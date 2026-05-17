from dataclasses import dataclass
from typing import Optional
from langchain_core.messages import SystemMessage


@dataclass
class ContextConfig:
    include_system_prompt: bool = True
    include_conversation_history: bool = True
    include_rag_context: bool = True
    include_user_profile: bool = False
    include_working_memory: bool = True
    max_tokens: int = 8192


class ContextAssembler:
    """Composable context assembly pipeline. Layers components in order:
    SystemPrompt -> RAG -> UserProfile -> WorkingMemory -> ConversationHistory"""

    def __init__(self, config: Optional[ContextConfig] = None):
        self.config = config or ContextConfig()

    def assemble(
        self,
        system_prompt: str,
        messages: list,
        rag_results: Optional[list[str]] = None,
        user_profile: Optional[dict] = None,
        working_memory: Optional[dict] = None,
    ) -> list:
        assembled = []

        if self.config.include_system_prompt and system_prompt:
            system_content = system_prompt

            if self.config.include_rag_context and rag_results:
                rag_section = "\n\n### 参考资料\n" + "\n".join(
                    f"[{i+1}] {r}" for i, r in enumerate(rag_results)
                )
                system_content += rag_section

            if self.config.include_user_profile and user_profile:
                system_content += "\n\n### 用户画像\n" + str(user_profile)

            if self.config.include_working_memory and working_memory:
                system_content += "\n\n### 当前任务上下文\n" + str(working_memory)

            assembled.append(SystemMessage(content=system_content))

        if self.config.include_conversation_history and messages:
            assembled.extend(messages)

        return assembled
