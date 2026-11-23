import logging

from openrouter import OpenRouter
from qdrant_client import AsyncQdrantClient

from src.main_agent.config.config import agent_config, env_config
from src.main_agent.knowledge.search import search_chunks

logger = logging.getLogger(__name__)


async def search_knowledge(query: str) -> list[dict] | str:
    """Search the global knowledge base."""
    config = agent_config.knowledge

    try:
        qdrant = AsyncQdrantClient(
            url=config.qdrant_url,
            timeout=60,
        )

        try:
            async with OpenRouter(
                api_key=env_config.provider_api_key,
            ) as embedding_client:
                return await search_chunks(
                    query,
                    embedding_client=embedding_client,
                    qdrant_client=qdrant,
                    collection_alias=config.collection_alias,
                    embedding_model=config.embedding_model,
                    top_k=config.top_k,
                )
        finally:
            await qdrant.close()

    except Exception:
        logger.exception("Knowledge search failed")
        return "Error: Knowledge search is temporarily unavailable."
