from src.runtime.agent_executor import AgentExecutor


class ReactAgent:
    """Backward-compatible wrapper. Delegates to AgentExecutor internally."""

    def __init__(self):
        self.executor = AgentExecutor()
        self.graph = self.executor.graph
        self.checkpointer = self.executor.checkpointer

    def execute_stream(self, query: str, thread_id: str = "default"):
        yield from self.executor.stream(query, thread_id)


if __name__ == '__main__':
    agent = ReactAgent()
    for chunk in agent.execute_stream("给我生成我的使用报告"):
        print(chunk, end="", flush=True)
