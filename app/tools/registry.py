"""
Minimal tool registry for Day8.

This layer keeps tool metadata, validates input arguments, and executes
registered handlers through one small, predictable entrypoint.
"""
from dataclasses import dataclass
from typing import Any, Callable


class ToolCallError(Exception):
    """Raised when a tool call cannot be executed safely."""


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[[dict[str, Any], dict[str, Any]], Any]
    risk_level: str = "read"

    def schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "risk_level": self.risk_level,
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ToolCallError(f"工具已存在: {tool.name}")
        self._tools[tool.name] = tool

    def list_schemas(self) -> list[dict[str, Any]]:
        return [tool.schema() for tool in self._tools.values()]

    def get(self, name: str) -> Tool:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolCallError(f"未知工具: {name}")
        return tool

    def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            tool = self.get(name)
            safe_arguments = validate_arguments(tool.parameters, arguments)

            data = tool.handler(safe_arguments, context or {})
            return {"success": True, "tool": name, "error": None, "data": data}
        except ToolCallError as exc:
            return {"success": False, "tool": name, "error": str(exc), "data": None}
        except Exception as exc:
            return {"success": False, "tool": name, "error": f"工具执行失败: {exc}", "data": None}


def validate_arguments(schema: dict[str, Any], arguments: dict[str, Any]) -> dict[str, Any]:
    if schema.get("type") != "object":
        raise ToolCallError("工具参数 schema 必须是 object")
    if not isinstance(arguments, dict):
        raise ToolCallError("工具参数必须是 dict")

    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    unknown_keys = set(arguments) - set(properties)

    if schema.get("additionalProperties") is False and unknown_keys:
        raise ToolCallError(f"不支持的参数: {', '.join(sorted(unknown_keys))}")

    missing_keys = required - set(arguments)
    if missing_keys:
        raise ToolCallError(f"缺少必填参数: {', '.join(sorted(missing_keys))}")

    safe_arguments = {}
    for key, value in arguments.items():
        if key not in properties:
            continue
        spec = properties[key]
        safe_arguments[key] = validate_value(key, value, spec)

    return safe_arguments


def validate_value(key: str, value: Any, spec: dict[str, Any]) -> Any:
    expected_type = spec.get("type")

    if expected_type == "string":
        if not isinstance(value, str):
            raise ToolCallError(f"{key} 必须是字符串")
        value = value.strip()
        min_length = spec.get("minLength")
        max_length = spec.get("maxLength")
        if min_length is not None and len(value) < min_length:
            raise ToolCallError(f"{key} 长度不能小于 {min_length}")
        if max_length is not None and len(value) > max_length:
            raise ToolCallError(f"{key} 长度不能大于 {max_length}")
        return value

    if expected_type == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ToolCallError(f"{key} 必须是整数")
        minimum = spec.get("minimum")
        maximum = spec.get("maximum")
        if minimum is not None and value < minimum:
            raise ToolCallError(f"{key} 不能小于 {minimum}")
        if maximum is not None and value > maximum:
            raise ToolCallError(f"{key} 不能大于 {maximum}")
        return value

    if expected_type == "boolean":
        if not isinstance(value, bool):
            raise ToolCallError(f"{key} 必须是布尔值")
        return value

    raise ToolCallError(f"{key} 使用了暂不支持的参数类型: {expected_type}")
