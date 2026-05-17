from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """Extended agent state with workflow mode and report flag."""
    report: bool
    workflow: str       # listing | review | campaign | daily_report
    metadata: dict
    turn_count: int
