import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal
from uuid import uuid4

from openrouter.components.chatmessages import ChatMessagesTypedDict

from src.main_agent.agent import providers
from src.main_agent.agent.providers.llm_contract import TokenUsage
from src.main_agent.config.config import agent_config
from src.main_agent.prompts.base import SYSTEM_PROMPT
from src.main_agent.tools.registry import build_tools

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Agent Response dataclass."""

    run_id: uuid.UUID
    status: Literal["completed", "step_limit", "empty_response", "running"]
    provider: str
    model: str
    llm_calls: int
    duration: timedelta
    usage: TokenUsage
    cost: float | None = None
    history: list[dict] | None = None


class AgentCore:
    """Agent core class"""

    def __init__(self, provider: providers.Provider) -> None:
        self.provider = provider

    async def call_llm(self, messages: list[ChatMessagesTypedDict]):
        """Call llm function"""
        response = await self.provider.invoke(messages=messages)
        return response

    async def invoke(self, user_message: str):
        """Invoke agent"""
        run_id = uuid4()
        start_time = datetime.now()

        agent_response = AgentResponse(
            run_id=run_id,
            status="running",
            provider=self.provider.name,
            model=self.provider.llm_config.model,
            llm_calls=0,
            duration=timedelta(seconds=0),
            usage=TokenUsage(
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                reasoning_tokens=0,
            ),
            cost=0.0,
            history=[],
        )

        tools = build_tools(run_id)
        workspace_names = json.dumps(list(agent_config.workspaces), ensure_ascii=False)
        messages: list[ChatMessagesTypedDict] = [
            {
                "role": "system",
                "content": f"{SYSTEM_PROMPT}\nConfigured workspace names: {workspace_names}",
            },
            {"role": "user", "content": user_message},
        ]

        for turn in range(agent_config.agent_max_steps):
            logger.info("================= 🔄 Turn %d =================", turn)
            response = await self.call_llm(messages=messages)
            message = response.message

            if message.content:
                logger.info("🤖 %s", message.content)

            agent_response.llm_calls += 1
            agent_response.duration += datetime.now() - start_time
            agent_response.usage.input_tokens += response.usage.input_tokens
            agent_response.usage.output_tokens += response.usage.output_tokens
            agent_response.usage.total_tokens += response.usage.total_tokens
            agent_response.usage.reasoning_tokens += response.usage.reasoning_tokens
            agent_response.cost += response.cost

            tool_calls = message.tool_calls or []

            if not tool_calls:
                if not message.content:
                    agent_response.status = "empty_response"
                    logger.warning("Model returned no text or tool calls")
                else:
                    agent_response.status = "completed"
                    agent_response.history.append(message.content)
                print("✅ Agent finished")
                return agent_response

            messages.append(message.model_dump(mode="json", exclude_unset=True))
            agent_response.history.append(message.content)
            for tool_call in tool_calls:
                name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                    if not isinstance(arguments, dict):
                        raise TypeError("Tool arguments must be a JSON object")
                    tool = tools.get(name)
                    if tool is None:
                        raise ValueError(f"Unknown tool: {name!r}")
                    logged_arguments = {
                        key: value
                        for key, value in arguments.items()
                        if key != "content"
                    }
                    logger.info("Calling tool %s with %s", name, logged_arguments)
                    result = tool(**arguments)
                    output = (
                        result
                        if isinstance(result, str)
                        else json.dumps(result, ensure_ascii=False)
                    )
                    if name == "write_file":
                        logger.info(
                            "Saved file in workspace %s: %s",
                            arguments["workspace"],
                            output,
                        )
                    else:
                        logger.info("Tool %s completed", name)
                except (OSError, TypeError, ValueError) as exc:
                    output = f"Error: {exc}"
                    logger.warning("Tool %s failed: %s", name, exc)

                messages.append(
                    {"role": "tool", "tool_call_id": tool_call.id, "content": output}
                )
                agent_response.history.append(
                    {"role": "tool", "tool_call_id": tool_call.id, "content": output}
                )
        agent_response.status = "step_limit"
        logger.warning(
            "Max turns (%d) reached. Stopping.", agent_config.agent_max_steps
        )
        return agent_response
