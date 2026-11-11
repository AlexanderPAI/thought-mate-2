import logging
from collections.abc import Callable

from openrouter import OpenRouter

from src.main_agent.config.config import agent_config, env_config
from src.main_agent.prompts.base import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class LLM:
    """LLM Contract class"""

    def __init__(self, llm_config, api_key) -> None:
        self.llm_config = llm_config.copy()
        self.model = OpenRouter(api_key=api_key)

        # todo валидацию всех полей llm_config

    async def invoke(self, messages):
        return self.model.chat.send(
            model=self.llm_config.model,
            messages=messages,
            tools=[],
            tool_choice="auto",
            temperature=self.llm_config.temperature,
            max_tokens=self.llm_config.max_tokens,
            stream=self.llm_config.stream,
        )


class AgentCore:
    """Agent core class"""

    def __init__(self, llm: LLM | None = None) -> None:
        self.llm = (
            llm
            if llm is not None
            else LLM(
                llm_config=agent_config.llm_config, api_key=env_config.provider_api_key
            )
        )
        self.tools: dict[str, Callable[..., str]] | None = None

    async def call_llm(self, messages: list[dict[str, str]]):
        """Call llm function"""
        response = await self.llm.invoke(messages=messages)
        return response

    async def invoke(self, user_message: str):
        """Invoke agent"""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        for turn in range(agent_config.agent_max_steps):
            logger.info(f"\n{'=' * 60}\n🔄 Turn {turn}\n{'=' * 60}")
            response = await self.call_llm(messages=messages)
            content = response.choices[0].message.content
            if content:
                logger.info(f"\n🤖 {content}")

            tool_calls = []

            if not tool_calls:
                print("(no text output)" if not content else "")
                print("✅ Agent finished")
                return

            # prefix = "\n" if content else ""

            messages.append(
                {
                    "role": "assistant",
                    "content": content or None,
                    # "tool_calls": [tool_call.model_dump() for tool_call in tool_calls],
                }
            )

            logger.info(
                f"\n⚠️  Max turns ({agent_config.agent_max_steps}) reached. Stopping."
            )
