import asyncio
import logging
import sys

from src.main_agent.agent.agent_core import AgentCore
from src.main_agent.config.config import agent_config

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("src.main_agent").setLevel(agent_config.log_level.upper())
logger = logging.getLogger(__name__)


async def main(args):
    logger.info("Starting app")
    logger.info("This is main agent ThoughtMate")
    agent = AgentCore()
    prompt = " ".join(args[1:]) if len(args) > 1 else ""
    if not prompt.strip():
        print("No task provided. Exiting.")
        sys.exit(1)
    await agent.invoke(prompt)


if __name__ == "__main__":
    asyncio.run(main(sys.argv))
