import argparse
import asyncio

from openrouter import OpenRouter
from qdrant_client import AsyncQdrantClient

from src.main_agent.config.config import agent_config, env_config
from src.main_agent.knowledge.documents import (
    read_markdown_documents,
    split_document_into_chunks,
)
from src.main_agent.knowledge.embeddings import build_embedding_text, get_embeddings
from src.main_agent.knowledge.storage import write_collection


async def main():
    parser = argparse.ArgumentParser(description="Knowledge Agent Index")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print chunks for inspection without generating embeddings.",
    )
    args = parser.parse_args()

    chunks: list[dict] = []
    document_count = 0

    for source in agent_config.knowledge.sources:
        documents = read_markdown_documents(source)

        for document in documents:
            document_chunks = split_document_into_chunks(document)

            document_count += 1

            chunks.extend(document_chunks)

    print(f"Всего документов: {document_count}")
    print(f"Всего фрагментов: {len(chunks)}")

    if args.dry_run:
        for chunk in chunks:
            section = " -> ".join(chunk["section"]) or "Введение"

            print(f"\n{'-' * 60}")
            print(f"Документ: {chunk['source']}")
            print(f"Название: {chunk['title']}")
            print(f"Фрагмент: {chunk['chunk_no']}")
            print(f"Раздел: {section}")
            print(f"Символов: {len(chunk['text'])}")
            print()
            print(chunk["text"])

        return

    if not chunks:
        raise ValueError("No document chunks found")

    texts = [build_embedding_text(chunk) for chunk in chunks]

    async with OpenRouter(api_key=env_config.provider_api_key) as client:
        embeddings = await get_embeddings(
            client,
            texts,
            embedding_model=agent_config.knowledge.embedding_model,
        )

        print(f"\nВсего эмбеддингов: {len(embeddings)}")
        print(f"Размерность: {len(embeddings[0])}")

        for chunk, vector in zip(chunks, embeddings, strict=True):
            print(
                f"{chunk['source']} | "
                f"фрагмент {chunk['chunk_no']} | "
                f"начало вектора: {vector[:3]}"
            )

    qdrant_client = AsyncQdrantClient(
        url=agent_config.knowledge.qdrant_url,
        timeout=60,
    )

    try:
        collection_name = await write_collection(
            qdrant_client,
            chunks,
            embeddings,
            collection_prefix=agent_config.knowledge.collection_alias,
            embedding_model=agent_config.knowledge.embedding_model,
        )
    finally:
        await qdrant_client.close()

    print(f"Данные записаны в коллекцию: {collection_name}")


if __name__ == "__main__":
    asyncio.run(main())
