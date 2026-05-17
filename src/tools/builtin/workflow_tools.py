from src.tools.base import ToolCategory
from src.tools import register_tool


@register_tool(
    name="set_workflow_context",
    description="切换当前工作流模式: listing(新品上架)/review(评价管理)/campaign(大促策划)/daily_report(日报生成)。调用后Agent将自动加载对应工作流的System Prompt和输出模板",
    input_schema={
        "type": "object",
        "properties": {
            "mode": {
                "type": "string",
                "description": "工作流模式: listing|review|campaign|daily_report",
                "enum": ["listing", "review", "campaign", "daily_report"],
            },
        },
        "required": ["mode"],
    },
    output_type="void",
    category=ToolCategory.CONTEXT_SIGNAL,
)
def set_workflow_context(mode: str) -> str:
    valid_modes = {"listing": "新品上架优化", "review": "评价危机管理", "campaign": "大促活动策划", "daily_report": "运营日报生成"}
    name = valid_modes.get(mode, mode)
    return f"workflow_context_set:{mode}:{name}"
