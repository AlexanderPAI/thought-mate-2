from openrouter import OpenRouter


def build_embedding_text(chunk: dict) -> str:
    """Combine the document title, section headings, and chunk text."""
    parts = [f"Документ: {chunk['title']}"]

    if chunk["section"]:
        section = " -> ".join(chunk["section"])
        parts.append(f"Раздел: {section}")

    parts.append(chunk["text"])

    return "\n\n".join(parts)


async def get_embeddings(
    client: OpenRouter,
    texts: list[str],
    *,
    embedding_model: str,
    batch_size: int = 16,
) -> list[list[float]]:
    """Return embeddings in the same order as the input texts."""
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    if any(not text.strip() for text in texts):
        raise ValueError("texts must be non-empty")

    embeddings = []
    dimension = None

    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]

        response = await client.embeddings.generate_async(
            model=embedding_model,
            input=batch,
            encoding_format="float",
        )

        items_by_index = {item.index: item for item in response.data}

        if len(response.data) != len(batch) or set(items_by_index) != set(
            range(len(batch))
        ):
            raise ValueError("embeddings must have the same dimension")

        for index in range(len(batch)):
            vector = items_by_index[index].embedding

            if not isinstance(vector, list) or not vector:
                raise ValueError("embeddings must have a list of vectors")

            if dimension is None:
                dimension = len(vector)

            if len(vector) != dimension:
                raise ValueError("embeddings must have the same dimension")

            embeddings.append(vector)
    return embeddings
