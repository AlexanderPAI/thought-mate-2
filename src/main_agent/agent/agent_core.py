from collections.abc import Callable

from openrouter import OpenRouter

from src.main_agent.config.config import agent_config, env_config


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

    def __init__(self, llm: LLM | None) -> None:
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
