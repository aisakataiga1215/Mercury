import time
from typing import Generator, Optional

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from model.factory import chat_model
from utils.prompt_loader import (
    load_system_prompts, WORKFLOW_PROMPTS,
)
from utils.logger_handler import logger

from .agent_state import AgentState
from .agent_graph import AgentGraph
from src.tools.registry import tool_registry
from src.harness.lifecycle import LifecycleHooks, HookEvent, HookContext
from src.harness.trace import TraceCollector
from src.context.assembler import ContextAssembler
from src.context.budget import ContextBudget
from src.memory.manager import MemoryManager


class AgentExecutor:
    """Central integration hub. Wires together all 6 framework modules."""

    def __init__(
        self,
        llm=None,
        checkpointer=None,
        hooks: Optional[LifecycleHooks] = None,
        trace_collector: Optional[TraceCollector] = None,
        memory_manager: Optional[MemoryManager] = None,
        context_assembler: Optional[ContextAssembler] = None,
        context_budget: Optional[ContextBudget] = None,
    ):
        self.llm = llm or chat_model
        self.checkpointer = checkpointer or InMemorySaver()

        self.hooks = hooks or LifecycleHooks()
        self.trace = trace_collector or TraceCollector()
        self.memory = memory_manager or MemoryManager()
        self.assembler = context_assembler or ContextAssembler()
        self.budget = context_budget or ContextBudget()

        tool_registry.discover("src.tools.builtin")
        self.model = self.llm.bind_tools(list(tool_registry.get_all_fns()))

        self.graph = self._build_graph()
        self._wire_default_hooks()

    def _wire_default_hooks(self) -> None:
        def on_tool_start(ctx: HookContext):
            span = self.trace.start_span(
                ctx.thread_id, f"tool:{ctx.tool_name}",
                metadata={"args": ctx.tool_args or {}},
            )
            ctx.metadata["span_id"] = span.span_id

        def on_tool_end(ctx: HookContext):
            if "span_id" in ctx.metadata:
                status = "ok" if ctx.metadata.get("success", True) else "error"
                self.trace.end_span(ctx.thread_id, ctx.metadata["span_id"], status)

        self.hooks.on(HookEvent.TOOL_START, on_tool_start)
        self.hooks.on(HookEvent.TOOL_END, on_tool_end)

    def _select_prompt(self, workflow: str) -> str:
        """Select system prompt based on workflow mode."""
        if workflow and workflow in WORKFLOW_PROMPTS:
            return WORKFLOW_PROMPTS[workflow]()
        return load_system_prompts()

    def _build_graph(self):
        def call_model(state: AgentState):
            thread_id = state.get("metadata", {}).get("thread_id", "")
            self.hooks.emit(HookContext(thread_id=thread_id, event=HookEvent.NODE_ENTER, node_name="agent"))

            messages = state["messages"]
            workflow = state.get("workflow", "")
            system_prompt = self._select_prompt(workflow)

            memory_context = self.memory.get_context(
                self.memory.extract_user_id(state)
            )
            if memory_context:
                system_prompt += "\n\n" + memory_context

            assembled = self.assembler.assemble(
                system_prompt=system_prompt,
                messages=messages,
            )

            if not self.budget.within_budget(assembled):
                logger.info("[executor] Context over budget, truncating...")
                assembled = self.budget.truncate_messages(assembled)

            logger.info(f"[executor] LLM call | {len(assembled)} msgs | workflow={workflow or 'default'}")
            t0 = time.time()
            response = self.model.invoke(assembled)
            llm_ms = (time.time() - t0) * 1000

            self.hooks.emit(HookContext(thread_id=thread_id, event=HookEvent.NODE_EXIT, node_name="agent",
                                        duration_ms=llm_ms))
            return {"messages": [response], "turn_count": state.get("turn_count", 0) + 1}

        def execute_tools(state: AgentState):
            thread_id = state.get("metadata", {}).get("thread_id", "")
            self.hooks.emit(HookContext(thread_id=thread_id, event=HookEvent.NODE_ENTER, node_name="tools"))

            last_message = state["messages"][-1]
            tool_messages = []
            workflow = state.get("workflow", "")

            for tc in last_message.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]

                ctx = HookContext(thread_id=thread_id, event=HookEvent.TOOL_START,
                                  tool_name=tool_name, tool_args=tool_args)
                self.hooks.emit(ctx)
                t_start = time.time()

                try:
                    result = tool_registry.invoke(tool_name, tool_args)
                    success = not str(result).startswith("Error:")
                except Exception as e:
                    result = f"Error: {e}"
                    success = False

                latency = (time.time() - t_start) * 1000
                logger.info(f"[executor] tool={tool_name} | latency={latency:.0f}ms | {'OK' if success else 'FAIL'}")

                self.hooks.emit(HookContext(
                    thread_id=thread_id, event=HookEvent.TOOL_END,
                    tool_name=tool_name, tool_result=str(result),
                    duration_ms=latency, metadata={"success": success},
                ))

                # Detect workflow context switch
                if tool_name == "set_workflow_context" and success:
                    raw = str(result)
                    if raw.startswith("workflow_context_set:"):
                        workflow = raw.split(":")[1]
                        logger.info(f"[executor] Workflow switched to: {workflow}")

                tool_messages.append(
                    ToolMessage(content=str(result), tool_call_id=tc["id"], name=tool_name)
                )

            self.hooks.emit(HookContext(thread_id=thread_id, event=HookEvent.NODE_EXIT, node_name="tools"))
            return {"messages": tool_messages, "workflow": workflow}

        @staticmethod
        def _router(state: AgentState) -> str:
            last = state["messages"][-1]
            if hasattr(last, "tool_calls") and last.tool_calls:
                return "tools"
            return "__end__"

        return AgentGraph.create_default(
            agent_node=call_model,
            tools_node=execute_tools,
            router=_router,
            checkpointer=self.checkpointer,
        )

    # ---- Public API ----

    def stream(self, query: str, thread_id: str = "default") -> Generator[str, None, None]:
        config = {"configurable": {"thread_id": thread_id}}
        self.hooks.emit(HookContext(thread_id=thread_id, event=HookEvent.TURN_START))

        input_state = {
            "messages": [HumanMessage(content=query)],
            "report": False,
            "workflow": "",
            "metadata": {"thread_id": thread_id},
            "turn_count": 0,
        }

        t_start = time.time()
        phase = "start"       # start → tools → reply
        try:
            for chunk in self.graph.stream(input_state, config, stream_mode="values"):
                messages = chunk.get("messages", [])
                if messages:
                    latest = messages[-1]
                    if hasattr(latest, "tool_calls") and latest.tool_calls:
                        if phase == "start":
                            yield "[think]分析输入...\n"
                            phase = "tools"
                        elif phase == "reply":
                            yield "[think]调用工具...\n"
                            phase = "tools"
                    elif isinstance(latest, ToolMessage):
                        pass  # 工具执行不单独输出
                    elif isinstance(latest, AIMessage) and latest.content:
                        if phase == "tools":
                            yield "[think]生成回复...\n"
                        yield f"[reply]{latest.content.strip()}\n"
                        phase = "reply"
            yield "[think]完成\n"
        except Exception as e:
            logger.error(f"[executor] Stream error: {e}")
            yield f"[reply]系统错误: {e}"
        finally:
            turn_ms = (time.time() - t_start) * 1000
            self.memory.on_turn_end()
            self.hooks.emit(HookContext(thread_id=thread_id, event=HookEvent.TURN_END, duration_ms=turn_ms))

    def invoke(self, query: str, thread_id: str = "default") -> str:
        return "".join(self.stream(query, thread_id))


    def get_trace(self, thread_id: str):
        return self.trace.to_dict(thread_id)
