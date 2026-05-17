import inspect
import importlib
import pkgutil
from typing import Any, Optional

from src.tools.base import ToolSpec, ToolCategory


from pydantic import BaseModel, Field


class RagInput(BaseModel):
    query: str = Field(..., description="Search query for RAG retrieval")


class WeatherInput(BaseModel):
    city: str = Field(..., description="City name for weather lookup")


class FetchExternalInput(BaseModel):
    user_id: str = Field(..., description="User ID string")
    month: str = Field(..., description="Month in YYYY-MM format")


INPUT_VALIDATORS: dict[str, type] = {
    "rag_summarize": RagInput,
    "get_weather": WeatherInput,
    "fetch_external_data": FetchExternalInput,
}


class ToolRegistry:
    """Global tool registry. Module-level singleton matching existing pattern."""

    def __init__(self):
        self._specs: dict[str, ToolSpec] = {}
        self._by_category: dict[ToolCategory, list[str]] = {c: [] for c in ToolCategory}

    def register(self, spec: ToolSpec) -> None:
        self._specs[spec.name] = spec
        self._by_category[spec.category].append(spec.name)

    def register_from_module(self, module, prefix: str = "") -> int:
        count = 0
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if hasattr(obj, "_tool_spec"):
                spec = obj._tool_spec
                spec.fn = obj
                if prefix:
                    spec.name = f"{prefix}.{spec.name}"
                self.register(spec)
                count += 1
        return count

    def discover(self, package_path: str) -> int:
        total = 0
        package = importlib.import_module(package_path)
        for _, module_name, is_pkg in pkgutil.walk_packages(
            package.__path__, package.__name__ + "."
        ):
            if not is_pkg:
                module = importlib.import_module(module_name)
                total += self.register_from_module(module)
        return total

    def get(self, name: str) -> Optional[ToolSpec]:
        return self._specs.get(name)

    def get_by_category(self, category: ToolCategory | str) -> list[ToolSpec]:
        if isinstance(category, str):
            category = ToolCategory(category)
        return [self._specs[n] for n in self._by_category.get(category, [])]

    def get_schema(self) -> list[dict]:
        return [spec.to_openai_schema() for spec in self._specs.values()]

    def get_all(self) -> list[ToolSpec]:
        return list(self._specs.values())

    def get_all_fns(self) -> list:
        return [spec.fn for spec in self._specs.values() if spec.fn]

    def invoke(self, name: str, args: dict) -> Any:
        spec = self.get(name)
        if spec is None:
            return f"Error: Unknown tool '{name}'"
        if spec.fn is None:
            return f"Error: Tool '{name}' has no implementation"

        validator = INPUT_VALIDATORS.get(name)
        if validator is not None:
            try:
                validated = validator(**args)
                args = validated.model_dump()
            except Exception as e:
                return f"Error: Invalid arguments for '{name}': {e}"

        try:
            return spec.fn(**args)
        except Exception as e:
            return f"Error: {e}"

    def clear(self) -> None:
        self._specs.clear()
        for c in self._by_category:
            self._by_category[c].clear()


tool_registry = ToolRegistry()
