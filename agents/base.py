from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Any, Optional, Dict, List
from pydantic import BaseModel, Field

# Define TypeVars for generic agent inputs/outputs
InputType = TypeVar('InputType', bound=BaseModel)
OutputType = TypeVar('OutputType', bound=BaseModel)

class AgentRequest(BaseModel):
    """
    Standard request wrapper received by all sub-agents.
    Ensures consistent data format across the orchestrator boundary.
    """
    session_id: str = Field(..., description="Unique session identifier for state tracking")
    payload: Dict[str, Any] = Field(..., description="Agent-specific input arguments")
    context: Dict[str, Any] = Field(default_factory=dict, description="Shared global context, e.g. user profile data")

class AgentResponse(BaseModel):
    """
    Standard response wrapper returned by all sub-agents.
    Ensures the orchestrator can consistently read logs, status, and outputs.
    """
    agent_name: str = Field(..., description="Name of the agent that executed the task")
    success: bool = Field(..., description="Flag indicating if the task completed successfully")
    output: Dict[str, Any] = Field(..., description="Agent-specific output payload")
    reasoning_steps: List[str] = Field(default_factory=list, description="Audit log of agent thoughts/actions")
    error_message: Optional[str] = Field(None, description="Detailed error message if execution failed")

class BaseAgent(ABC, Generic[InputType, OutputType]):
    """
    Abstract Base Class for all specialist agents.
    Enforces a strict input/output signature on the orchestrator-worker boundary.
    """
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Processes the request and returns a standardized AgentResponse.
        Each specialist agent overrides this method.
        """
        pass
