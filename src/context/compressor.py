from dataclasses import dataclass
from typing import Optional
from langchain_core.messages import SystemMessage
from .budget import ContextBudget


@dataclass
class CompressorConfig:
    max_summary_tokens: int = 256
    summary_prompt: str = "请用中文简洁总结以下对话的核心内容："


class ContextCompressor:
    """Compress long conversations using LLM summarization or extractive fallback."""

    def __init__(self, llm=None, config: Optional[CompressorConfig] = None):
        self.llm = llm
        self.config = config or CompressorConfig()

    def compress(self, messages: list, budget: ContextBudget, target_tokens: int) -> list:
        if len(messages) <= 4:
            return messages

        recent = messages[-4:]
        history = messages[:-4]

        if not history:
            return messages

        summary = self.summarize_segment(history)
        summary_msg = SystemMessage(content=f"[对话历史摘要] {summary}")
        return [summary_msg] + list(recent)

    def summarize_segment(self, messages: list) -> str:
        if self.llm:
            prompt = self.config.summary_prompt + "\n" + "\n".join(
                f"{type(m).__name__}: {m.content[:200]}"
                for m in messages[-20:]
                if hasattr(m, "content") and m.content
            )
            try:
                response = self.llm.invoke(prompt)
                return response.content if hasattr(response, "content") else str(response)
            except Exception:
                pass

        combined = " | ".join(
            m.content[:100]
            for m in messages[-10:]
            if hasattr(m, "content") and m.content
        )
        return combined[:500]
