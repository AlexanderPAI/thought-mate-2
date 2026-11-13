from datetime import datetime

from openrouter import OpenRouter

from src.main_agent.agent.providers.llm_contract import (
    LLMProvider,
    LLMResponse,
    TokenUsage,
)
from src.main_agent.prompts.base import LLM_TOOLS


class OpenRouterProvider(LLMProvider):
    """OpenRouterProvider"""

    def __init__(self, llm_config, api_key) -> None:
        self.name = "OpenRouterProvider"
        self.llm_config = llm_config.copy()
        self.client = OpenRouter(api_key=api_key)

    async def invoke(self, messages):
        start_time = datetime.now()

        response = await self.client.chat.send_async(
            model=self.llm_config.model,
            messages=messages,
            tools=LLM_TOOLS,
            tool_choice="auto",
            temperature=self.llm_config.temperature,
            max_tokens=self.llm_config.max_tokens,
            stream=self.llm_config.stream,
        )

        duration = datetime.now() - start_time

        message = response.choices[0].message
        usage = (
            response.usage.model_dump(mode="json") if response.usage is not None else {}
        )
        completion_details = usage.get("completion_tokens_details") or {}

        return LLMResponse(
            message=message,
            duration=duration,
            usage=TokenUsage(
                input_tokens=usage.get("prompt_tokens"),
                output_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
                reasoning_tokens=completion_details.get("reasoning_tokens"),
            ),
            cost=usage.get("cost"),
        )
