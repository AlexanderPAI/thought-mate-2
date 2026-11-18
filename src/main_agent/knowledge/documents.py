from pathlib import Path


def read_markdown_documents(dir: str | Path) -> list[dict[str, str]]:
    """Read markdown documents from a directory."""
    root = Path(dir).resolve()

    if not root.is_dir():
        raise ValueError(f"Directory {root} does not exist")

    documents: list[dict[str, str]] = []

    for path in root.glob("**/*.md"):
        if not path.is_file():
            continue

        text = path.read_text(encoding="utf-8")

        if not text.strip():
            continue

        documents.append(
            {
                "source": path.relative_to(root).as_posix(),
                "title": path.stem,
                "text": text,
            }
        )

    return documents
