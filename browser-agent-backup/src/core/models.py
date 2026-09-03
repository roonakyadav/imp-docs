from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime

class AgentState(str, Enum):
    IDLE = "IDLE"
    INITIALIZING = "INITIALIZING"
    THINKING = "THINKING"
    NAVIGATING = "NAVIGATING"
    EXTRACTING = "EXTRACTING"
    RECOVERING = "RECOVERING"
    RETRYING = "RETRYING"
    HUMAN_INTERVENTION = "HUMAN_INTERVENTION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"

class ExecutionStep(BaseModel):
    timestamp: str
    step: int
    state: AgentState
    goal: str
    thought: str
    action: str
    status: str
    url: Optional[str] = None
    screenshot_path: Optional[str] = None
    latency_ms: float = 0.0
    confidence: float = 1.0
    retry_count: int = 0
    error: Optional[str] = None

class SessionMetrics(BaseModel):
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_steps: int = 0
    total_errors: int = 0
    total_retries: int = 0
    total_cost: float = 0.0
    duration_seconds: float = 0.0
    success_rate: float = 0.0

class ExecutionNode(BaseModel):
    id: str
    label: str
    type: str # 'goal', 'action', 'retry', 'error'
    children: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ExecutionGraph(BaseModel):
    nodes: Dict[str, ExecutionNode] = Field(default_factory=dict)
    root_id: Optional[str] = None

class AgentStatus(BaseModel):
    current_state: AgentState = AgentState.IDLE
    task_status: TaskStatus = TaskStatus.PENDING
    current_task: str = ""
    start_time: str = ""
    runtime: str = "00:00:00"
    step_count: int = 0
    retry_count: int = 0
    last_action: str = "Waiting for task..."
    last_thought: str = ""
    current_url: str = "None"
    error_message: Optional[str] = None
    confidence_score: float = 1.0
    human_intervention_needed: bool = False
    token_usage: Dict[str, int] = Field(default_factory=lambda: {"prompt": 0, "completion": 0, "total": 0})
    estimated_cost: float = 0.0
    recent_logs: List[str] = Field(default_factory=list)
    recent_screenshots: List[str] = Field(default_factory=list)
    execution_graph: ExecutionGraph = Field(default_factory=ExecutionGraph)
