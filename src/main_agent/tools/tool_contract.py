import uuid
from typing import Any, Literal

from pydantic import BaseModel


class ToolCall(BaseModel):
    """ToolCall model"""

    id: uuid.UUID
    name: str
    args: dict[str, Any]


class ToolResult(BaseModel):
    """ToolResult model"""

    call_id: uuid.UUID
    status: Literal["success", "failure"]
    data: dict[str, Any] | None = None
    error: str | None = None
