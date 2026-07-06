"""Project-specific tools for PHP-Sage."""
from app.tools.registry import Tool, ToolCallError, ToolRegistry


def build_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()


    registry.register(
        Tool(
            name="search_knowledge_base",
            description="Search PHP production issue documents and return relevant chunks.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "PHP production issue or error message.",
                        "minLength": 1,
                        "maxLength": 300,
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Maximum number of chunks to return.",
                        "minimum": 1,
                        "maximum": 3,
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            handler=search_knowledge_base,
            risk_level="read",
        )
    )

    registry.register(
        Tool(
            name="get_service_status",
            description="Return current PHP-Sage service readiness and knowledge base statistics.",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            handler=get_service_status,
            risk_level="read",
        )
    )

    return registry


def search_knowledge_base(arguments: dict, context: dict) -> dict:
    searcher = context.get("searcher")
    if searcher is None:
        raise ToolCallError("知识库尚未初始化完成")

    query = arguments["query"]
    top_k = arguments.get("top_k", 3)
    results = searcher.search(query)[:top_k]

    return {
        "query": query,
        "results": results,
        "sources": list(dict.fromkeys(result["source"] for result in results)),
    }


def get_service_status(arguments: dict, context: dict) -> dict:
    return {
        "ready": bool(context.get("ready")),
        "chunk_count": context.get("chunk_count", 0),
        "tool_count": context.get("tool_count", 0),
    }

