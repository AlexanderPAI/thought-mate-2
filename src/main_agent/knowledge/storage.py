import uuid

from qdrant_client import AsyncQdrantClient, models


async def write_collection(
    client: AsyncQdrantClient,
    chunks: list[dict],
    embeddings: list[list[float]],
    *,
    collection_prefix: str,
    embedding_model: str,
    batch_size: int = 64,
) -> str:
    """Write chunks to a collection"""
    if batch_size <= 0:
        raise ValueError("Batch size must be positive")

    if not chunks:
        raise ValueError("No chunks to write")

    if len(chunks) != len(embeddings):
        raise ValueError("Number of embeddings must match number of chunks")

    dimension = len(embeddings[0])

    if dimension == 0:
        raise ValueError("Embedding dimension must be greater than 0")

    points = []

    for chunk, vector in zip(chunks, embeddings, strict=True):
        if len(vector) != dimension:
            raise ValueError("Embedding dimensions do not match")

        points.append(
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "source": chunk["source"],
                    "title": chunk["title"],
                    "section": chunk["section"],
                    "chunk_no": chunk["chunk_no"],
                    "text": chunk["text"],
                    "embedding_model": embedding_model,
                },
            )
        )

        collection_name = f"{collection_prefix}_{uuid.uuid4().hex}"

        await client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=dimension,
                distance=models.Distance.COSINE,
            ),
        )

        print(f"Создана коллекция: {collection_name}")

        for start in range(0, len(points), batch_size):
            batch = points[start : start + batch_size]

            await client.upsert(
                collection_name=collection_name,
                points=batch,
                wait=True,
            )

            print(f"Записано фрагментов: {start + len(batch)}/{len(points)}")

        result = await client.count(
            collection_name=collection_name,
            exact=True,
        )

        if result.count != len(points):
            raise ValueError(
                f"Point count mismatch: expected {len(points)}, got {result.count}"
            )

    return collection_name


async def publish_collection(
    client: AsyncQdrantClient,
    *,
    collection_name: str,
    alias_name: str,
) -> None:
    """Publish a collection"""
    if not await client.collection_exists(collection_name):
        raise ValueError(f"Collection {collection_name} does not exist")

    aliases = await client.get_aliases()

    current_collection = next(
        (
            alias.collection_name
            for alias in aliases.aliases
            if alias.alias_name == alias_name
        ),
        None,
    )

    if current_collection == collection_name:
        return

    operations = []

    if current_collection is not None:
        operations.append(
            models.DeleteAliasOperation(
                delete_alias=models.DeleteAlias(
                    alias_name=alias_name,
                )
            )
        )

    operations.append(
        models.CreateAliasOperation(
            create_alias=models.CreateAlias(
                collection_name=collection_name,
                alias_name=alias_name,
            )
        )
    )

    await client.update_collection_aliases(
        change_aliases_operations=operations,
    )
