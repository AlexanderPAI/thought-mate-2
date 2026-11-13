from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class TokenUsage:
    """DTO for token usage"""

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    reasoning_tokens: int | None = None


@dataclass(frozen=True)
class LLMResponse:
    """DTO for LLM response"""

    content: str | None = None
    duration: timedelta | None = None
    usage: TokenUsage | None = None
    cost: float | None = None


class LLMProvider(ABC):
    """Abstract class to implement a LLM provider"""

    @abstractmethod
    async def invoke(self, messages): ...
