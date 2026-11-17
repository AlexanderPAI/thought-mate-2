from typing import Literal

from pydantic import BaseModel, Field, model_validator
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


class KnowledgeConfig(BaseModel):
    qdrant: str = Field(..., description="Qrant URL")
    collection_alias: str = Field(..., description="Collection alias")
    source: list[str] = Field(..., description="Source")


class EnvConfig(BaseSettings):
    provider_api_key: str = Field(..., description="The PROVIDER API key")

    model_config = SettingsConfigDict(
        env_file=".env",
    )


class AgentConfig(BaseSettings):
    llm_config: LLMConfig = Field(..., description="LLM Config")
    knowledge_config: KnowledgeConfig = Field(..., description="Knowledge Config")
    log_level: Literal["debug", "info", "warning", "error"] = "info"
    agent_max_steps: int = Field(..., description="Max number of steps")
    workspaces: dict[str, str] = Field(..., description="Workspace names and paths")
    default_workspace: str | None = None

    model_config = SettingsConfigDict(
        yaml_file="src/main_agent/config/config.yaml",
        yaml_file_encoding="utf-8",
    )

    @classmethod
    def settings_customise_sources(cls, settings_cls, **_):
        return (YamlConfigSettingsSource(settings_cls),)

    @model_validator(mode="after")
    def validate_default_workspace(self) -> AgentConfig:
        if (
            self.default_workspace is not None
            and self.default_workspace not in self.workspaces
        ):
            raise ValueError("default_workspace must be a name from workspaces")
        return self


env_config = EnvConfig()
agent_config = AgentConfig()
