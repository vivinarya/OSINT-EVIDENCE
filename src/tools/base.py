from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: str | None = None
    source_type: str = "unknown"
    source_url: str = ""
    title: str = ""
    snippet: str = ""
    raw_text: str = ""
    retrieved_at: str = ""

    def __post_init__(self):
        if not self.retrieved_at:
            self.retrieved_at = datetime.now(timezone.utc).isoformat()


class BaseTool(ABC):
    name: str = "base_tool"

    @abstractmethod
    async def run(self, params: dict) -> ToolResult:
        ...
