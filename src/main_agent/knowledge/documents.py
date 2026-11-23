from pathlib import Path

from markdown_it import MarkdownIt


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


def split_document_into_chunks(document: dict[str, str], *, max_chars: int = 4000):
    """Split a Markdown document into chunks using headings and block boundaries."""
    if max_chars <= 0:
        raise ValueError("max_chars must be a positive integer")

    parser = MarkdownIt("commonmark").enable("table")
    tokens = parser.parse(document["text"])
    lines = document["text"].splitlines(keepends=True)

    chunks = []
    headings = []
    blocks = []
    current_size = 0

    def flush():
        nonlocal current_size

        if not blocks:
            return

        chunks.append(
            {
                "source": document["source"],
                "title": document["title"],
                "section": [title for _, title in headings],
                "chunk_no": len(chunks),
                "text": "\n\n".join(blocks),
            }
        )

        blocks.clear()
        current_size = 0

    for index, token in enumerate(tokens):
        if token.level != 0 or token.map is None:
            continue

        if token.type == "heading_open":
            flush()

            heading_level = int(token.tag[1:])
            heading_title = tokens[index + 1].content

            while headings and headings[-1][0] >= heading_level:
                headings.pop()

            headings.append((heading_level, heading_title))
            continue

        start_line, end_line = token.map
        block = "".join(lines[start_line:end_line]).strip()

        if not block:
            continue

        separator_size = 2 if blocks else 0

        if blocks and current_size + separator_size + len(block) > max_chars:
            flush()
            separator_size = 0

        blocks.append(block)
        current_size += separator_size + len(block)

    flush()

    return chunks
