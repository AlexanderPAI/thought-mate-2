from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


class LLMConfig(BaseModel):
    provider: Literal["openrouter"] = Field(..., description="Provider")
    base_url: str = Field(..., description="Base provider URL")
    model: str = Field(..., description="Model name")
    temperature: float = Field(..., description="Temperature for LLM")
    max_tokens: int = Field(..., description="Maximum number of tokens")
    stream: bool = Field(..., description="Stream mode")


class EnvConfig(BaseSettings):
    provider_api_key: str = Field(..., description="The PROVIDER API key")

    model_config = SettingsConfigDict(
        env_file=".env",
    )


class AgentConfig(BaseSettings):
    llm_config: LLMConfig = Field(..., description="LLM Config")
    log_level: Literal["debug", "info", "warning", "error"] = "info"
    agent_max_steps: int = Field(..., description="Max number of steps")
    workspaces: dict[str, str] = Field(..., description="Workspace names and paths")

    model_config = SettingsConfigDict(
        yaml_file="src/main_agent/config/config.yaml",
        yaml_file_encoding="utf-8",
    )

    @classmethod
    def settings_customise_sources(cls, settings_cls, **_):
        return (YamlConfigSettingsSource(settings_cls),)


env_config = EnvConfig()
agent_config = AgentConfig()
