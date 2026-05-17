from functools import wraps
from .base import ToolSpec, ToolCategory


def register_tool(
    name: str,
    description: str,
    input_schema: dict,
    output_type: str = "string",
    category: ToolCategory = ToolCategory.KNOWLEDGE,
    version: str = "1.0.0",
    examples: list | None = None,
):
    """Decorator: tag a function with a ToolSpec for auto-discovery by ToolRegistry."""
    def decorator(fn):
        spec = ToolSpec(
            name=name,
            description=description,
            input_schema=input_schema,
            output_type=output_type,
            category=category,
            version=version,
            examples=examples or [],
            fn=fn,
        )
        fn._tool_spec = spec

        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        wrapper._tool_spec = spec
        return wrapper
    return decorator
