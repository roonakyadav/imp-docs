import json
import os
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from src.core.models import AgentStatus, AgentState, ExecutionStep, TaskStatus, SessionMetrics, ExecutionNode, ExecutionGraph
from src.config import logger
import uuid

class ObservabilityManager:
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = time.time()
        self.status = AgentStatus(
            start_time=datetime.now().isoformat(),
            current_state=AgentState.INITIALIZING
        )
        self.steps: List[ExecutionStep] = []
        self.audit_log_path = f"logs/audit_{self.session_id}.json"
        self.metrics_path = f"logs/metrics_{self.session_id}.json"
        self.session_manifest_path = f"sessions/manifest_{self.session_id}.json"
        
        # Initialize Graph
        self.status.execution_graph.root_id = "root"
        self.status.execution_graph.nodes["root"] = ExecutionNode(
            id="root", label="Start", type="goal"
        )
        self.current_parent_id = "root"
        
        # Ensure directories exist
        os.makedirs("logs", exist_ok=True)
        os.makedirs("screenshots", exist_ok=True)
        os.makedirs("sessions", exist_ok=True)

    def update_state(self, state: AgentState, **kwargs):
        """Resilient state update with schema-safe extraction."""
        self.status.current_state = state
        for key, value in kwargs.items():
            if hasattr(self.status, key):
                setattr(self.status, key, value)
        
        # Update runtime
        elapsed = time.time() - self.start_time
        hours, rem = divmod(elapsed, 3600)
        minutes, seconds = divmod(rem, 60)
        self.status.runtime = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        
        # Log to recent logs
        if 'last_action' in kwargs:
            log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] {state}: {kwargs['last_action']}"
            self.status.recent_logs.insert(0, log_entry)
            self.status.recent_logs = self.status.recent_logs[:50] # Keep last 50

    def record_step(self, step_number: int, state: Any, output: Any, error: Optional[str] = None):
        """Safe extraction of step data from browser-use objects."""
        # Safe extraction layer
        goal = self._safe_extract(output, 'next_goal', self._safe_extract(output, 'current_state.next_goal', "Processing..."))
        thought = self._safe_extract(output, 'thinking', self._safe_extract(output, 'current_state.thinking', "Thinking..."))
        action = self._safe_extract(output, 'next_goal', self._safe_extract(output, 'current_state.next_goal', "Acting..."))
        url = self._safe_extract(state, 'url', "Unknown")
        
        # Calculate real confidence heuristics
        confidence = self._calculate_confidence(step_number, error)
        
        step_entry = ExecutionStep(
            timestamp=datetime.now().isoformat(),
            step=step_number,
            state=self.status.current_state,
            goal=goal,
            thought=thought,
            action=action,
            status="failed" if error else "success",
            url=url,
            retry_count=self.status.retry_count,
            error=error,
            confidence=confidence,
            latency_ms=(time.time() - self.start_time) * 1000
        )
        
        self.steps.append(step_entry)
        self.status.step_count = len(self.steps)
        self.status.last_thought = thought
        self.status.last_action = action
        self.status.current_url = url
        self.status.confidence_score = confidence
        
        if error:
            self.status.retry_count += 1
            
        # Update Graph
        self._update_graph(step_entry)
            
        # Incremental save
        self._save_audit_log()

    def _calculate_confidence(self, step: int, error: Optional[str]) -> float:
        """Heuristic-based confidence scoring."""
        base = 1.0
        # Penalty for retries
        base -= (self.status.retry_count * 0.15)
        # Penalty for errors
        if error: base -= 0.3
        # Penalty for long duration/many steps (complexity)
        base -= (step * 0.02)
        return max(0.05, min(1.0, base))

    def _update_graph(self, step: ExecutionStep):
        """Build a deterministic execution graph."""
        node_id = f"step_{step.step}"
        label = step.goal[:30] + "..." if len(step.goal) > 30 else step.goal
        
        node = ExecutionNode(
            id=node_id,
            label=label,
            type="error" if step.error else "action",
            metadata={"thought": step.thought, "action": step.action}
        )
        
        self.status.execution_graph.nodes[node_id] = node
        if self.current_parent_id in self.status.execution_graph.nodes:
            self.status.execution_graph.nodes[self.current_parent_id].children.append(node_id)
        
        self.current_parent_id = node_id

    def _safe_extract(self, obj: Any, path: str, default: Any) -> Any:
        """Resiliently extract nested attributes."""
        try:
            parts = path.split('.')
            current = obj
            for part in parts:
                if hasattr(current, part):
                    current = getattr(current, part)
                elif isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default
            return current if current is not None else default
        except Exception:
            return default

    def _save_audit_log(self):
        try:
            with open(self.audit_log_path, 'w') as f:
                json.dump([s.model_dump() for s in self.steps], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save audit log: {e}")

    def finalize(self, task_status: TaskStatus, error_message: Optional[str] = None):
        self.status.task_status = task_status
        self.status.error_message = error_message
        self.status.current_state = AgentState.COMPLETED if task_status != TaskStatus.FAILED else AgentState.FAILED
        
        # Calculate metrics
        metrics = SessionMetrics(
            session_id=self.session_id,
            start_time=datetime.fromisoformat(self.status.start_time),
            end_time=datetime.now(),
            total_steps=self.status.step_count,
            total_errors=1 if task_status == TaskStatus.FAILED else 0,
            total_retries=self.status.retry_count,
            duration_seconds=time.time() - self.start_time,
            success_rate=1.0 if task_status == TaskStatus.SUCCESS else 0.0
        )
        
        try:
            with open(self.metrics_path, 'w') as f:
                json.dump(metrics.model_dump(), f, indent=2, default=str)
                
            # Create session manifest for replayability
            manifest = {
                "session_id": self.session_id,
                "status": self.status.model_dump(),
                "steps": [s.model_dump() for s in self.steps],
                "metrics": metrics.model_dump()
            }
            with open(self.session_manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to finalize observability: {e}")

    def get_dashboard_data(self) -> Dict[str, Any]:
        return self.status.model_dump()
