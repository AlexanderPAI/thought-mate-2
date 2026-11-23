import argparse
import asyncio

from openrouter import OpenRouter
from qdrant_client import AsyncQdrantClient

from src.main_agent.config.config import agent_config, env_config
from src.main_agent.knowledge.embeddings import get_embeddings


async def search_knowledge(
    query: str,
    *,
    embedding_client: OpenRouter,
    qdrant_client: AsyncQdrantClient,
    collection_alias: str,
    embedding_model: str,
    top_k: int = 5,
) -> list[dict]:
    """Return knowledge chunks ranked by similarity to the query."""

    if not query.strip():
        raise ValueError("Query cannot be empty")

    if top_k <= 0:
        raise ValueError("Top K cannot be less than 0")

    embeddings = await get_embeddings(
        embedding_client,
        [query],
        embedding_model=embedding_model,
    )

    response = await qdrant_client.query_points(
        collection_name=collection_alias,
        query=embeddings[0],
        limit=top_k,
        with_payload=True,
        with_vectors=True,
    )

    results = []

    for point in response.points:
        payload = point.payload or {}

        results.append(
            {
                "score": point.score,
                "source": payload["source"],
                "title": payload["title"],
                "section": payload["section"],
                "chunk_no": payload["chunk_no"],
                "text": payload["text"],
            }
        )

    return results


async def main() -> None:
    parser = argparse.ArgumentParser(description="Search knowledge")
    parser.add_argument("query", help="Query to search for")
    args = parser.parse_args()

    qdrant = AsyncQdrantClient(
        url=agent_config.knowledge.qdrant_url,
        timeout=60,
    )

    try:
        count = await qdrant.count(
            collection_name=agent_config.knowledge.collection_alias,
            exact=True,
        )

        print(f"Фрагментов в опубликованной коллекции: {count.count}")

        async with OpenRouter(api_key=env_config.provider_api_key) as embedding_client:
            results = await search_knowledge(
                query=args.query,
                embedding_client=embedding_client,
                qdrant_client=qdrant,
                collection_alias=agent_config.knowledge.collection_alias,
                embedding_model=agent_config.knowledge.embedding_model,
                top_k=agent_config.knowledge.top_k,
            )
    finally:
        await qdrant.close()

    print(f"Найдено: {len(results)}")

    for rank, result in enumerate(results, start=1):
        section = " → ".join(result["section"]) or "Введение"

        print(f"\n{'-' * 60}")
        print(f"Позиция: {rank}")
        print(f"Сходство: {result['score']:.4f}")
        print(f"Источник: {result['source']}")
        print(f"Раздел: {section}")
        print(f"Фрагмент: {result['chunk_no']}")
        print()
        print(result["text"])


if __name__ == "__main__":
    asyncio.run(main())
