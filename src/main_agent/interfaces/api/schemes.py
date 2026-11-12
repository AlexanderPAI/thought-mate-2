import uuid
from typing import Literal

from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """Token Usage Response Model"""

    input_tokens: int | None = Field(None, description="Input tokens")
    output_tokens: int | None = Field(None, description="Output tokens")
    total_tokens: int | None = Field(None, description="Total tokens")
    reasoning_tokens: int | None = Field(None, description="Reasoning tokens")


class AgentResponse(BaseModel):
    """Agent Response Model"""

    run_id: uuid.UUID = Field(..., description="Run ID")
    status: Literal["completed", "step_limit", "empty_response"] = Field(
        ..., description="Status"
    )
    content: str | None = Field(None, description="Content of the response")
    reasoning: str | None = Field(None, description="Reasoning")
    provider: str = Field(..., description="Provider")
    model: str = Field(..., description="Model")
    llm_calls: int = Field(..., description="LLM Calls")
    duration_ms: int = Field(..., description="Duration")
    usage: TokenUsage = Field(..., description="Usage")
