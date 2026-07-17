import pytest
from src.tools.base import ToolResult


class TestToolResult:
    def test_default_timestamp(self):
        r = ToolResult(success=True, data="test")
        assert r.retrieved_at != ""

    def test_error_result(self):
        r = ToolResult(success=False, error="Something broke")
        assert not r.success
        assert r.error == "Something broke"
