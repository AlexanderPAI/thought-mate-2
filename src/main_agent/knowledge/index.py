import argparse

from src.main_agent.config.config import agent_config
from src.main_agent.knowledge.documents import (
    read_markdown_documents,
    split_document_into_chunks,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Index knowkedge documents")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print document chunks for inspection"
    )
    args = parser.parse_args()

    if not args.dry_run:
        parser.error("Indexing is not implemented yet. Use --dry-run")

    document_count = 0
    chunk_count = 0

    for source in agent_config.knowledge.sources:
        documents = read_markdown_documents(source)

        for document in documents:
            chunks = split_document_into_chunks(document)
            document_count += 1
            chunk_count += len(chunks)

            print(f"\nДокумент: {document['source']}")
            print(f"Название: {document['title']}")
            print(f"Фрагментов: {len(chunks)}")

            for chunk in chunks:
                section = " → ".join(chunk["section"]) or "Введение"
                text = chunk["text"]

                print(f"\n{'-' * 60}")
                print(f"Фрагмент: {chunk['chunk_no']}")
                print(f"Раздел: {section}")
                print(f"Символов: {len(text)}")
                print()
                print(text)

        print(f"\nВсего документов: {document_count}")
        print(f"Всего фрагментов: {chunk_count}")


if __name__ == "__main__":
    main()
