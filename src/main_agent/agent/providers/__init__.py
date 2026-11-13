from src.main_agent.agent.providers.llm_contract import LLMProvider
from src.main_agent.agent.providers.openrouter import OpenRouterProvider

Provider = LLMProvider | OpenRouterProvider
