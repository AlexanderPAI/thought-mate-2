import json
import logging
from uuid import uuid4

from openrouter import OpenRouter
from openrouter.components.chatmessages import ChatMessagesTypedDict
from openrouter.components.reasoningdetailsummary import ReasoningDetailSummary
from openrouter.components.reasoningdetailtext import ReasoningDetailText

from src.main_agent.config.config import agent_config, env_config
from src.main_agent.prompts.base import LLM_TOOLS, SYSTEM_PROMPT
from src.main_agent.tools.registry import build_tools

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
            tools=LLM_TOOLS,
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

    async def call_llm(self, messages: list[ChatMessagesTypedDict]):
        """Call llm function"""
        response = await self.llm.invoke(messages=messages)
        return response

    async def invoke(self, user_message: str):
        """Invoke agent"""
        tools = build_tools(f"run-{uuid4().hex}")
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
            message = response.choices[0].message
            if logger.isEnabledFor(logging.DEBUG):
                reasoning = message.reasoning
                if isinstance(reasoning, str) and reasoning.strip():
                    logger.debug("Model reasoning:\n%s", reasoning.strip())
                else:
                    for detail in message.reasoning_details or []:
                        if isinstance(detail, ReasoningDetailSummary):
                            logger.debug("Model reasoning summary:\n%s", detail.summary)
                        elif isinstance(detail, ReasoningDetailText):
                            text = detail.text
                            if isinstance(text, str) and text.strip():
                                logger.debug("Model reasoning:\n%s", text.strip())
            content = message.content
            if isinstance(content, str):
                content = content.strip()
            if content:
                logger.info("🤖 %s", content)

            tool_calls = message.tool_calls or []

            if not tool_calls:
                if not content:
                    logger.warning("Model returned no text or tool calls")
                print("✅ Agent finished")
                return

            messages.append(message.model_dump(mode="json", exclude_unset=True))
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

        logger.warning(
            "Max turns (%d) reached. Stopping.", agent_config.agent_max_steps
        )
