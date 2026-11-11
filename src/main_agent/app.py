import asyncio
import logging

from src.main_agent.agent.agent_core import AgentCore
from src.main_agent.prompts.base import SYSTEM_PROMPT

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting app")
    logger.info("This is main agent ThoughtMate")
    agent = AgentCore()
    system_prompt = {"role": "system", "content": SYSTEM_PROMPT}
    user_prompt = {"role": "user", "content": input("Enter your question: ")}
    logger.info("Asking agent...")
    result = await agent.call_llm([system_prompt, user_prompt])
    logger.info("Answer:")
    logger.info(result.choices[0].message.content)


if __name__ == "__main__":
    asyncio.run(main())
