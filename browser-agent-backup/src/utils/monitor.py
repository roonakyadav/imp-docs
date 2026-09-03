import json
import time
from datetime import datetime
from src.config import logger

class AgentMonitor:
    def __init__(self, session_id=None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.audit_log_path = f"logs/audit_{self.session_id}.json"
        self.metrics_path = f"logs/metrics_{self.session_id}.json"
        self.actions = []
        self.start_time = time.time()
        self.metrics = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "total_steps": 0,
            "errors": 0,
            "retries": 0,
            "success": False,
            "duration_seconds": 0,
            "cost_estimate": 0.0  # Placeholder for cost tracking
        }

    def record_action(self, step, state, output, error=None):
        action_entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "goal": output.current_state.next_goal if output and hasattr(output, 'current_state') else "Unknown",
            "thought": output.current_state.thinking if output and hasattr(output, 'current_state') else "Processing",
            "action": output.current_state.next_goal if output and hasattr(output, 'current_state') else "Processing",
            "status": "success" if not error else "failed",
            "error": str(error) if error else None
        }
        self.actions.append(action_entry)
        self.metrics["total_steps"] += 1
        if error:
            self.metrics["errors"] += 1
            logger.warning(f"⚠️ Step {step} failed: {error}. Attempting recovery...")
        
        # Save audit log incrementally
        with open(self.audit_log_path, 'w') as f:
            json.dump(self.actions, f, indent=2)
        
        logger.info(f"Audit: {action_entry['timestamp']} -> Step {step}: {action_entry['goal']} [{action_entry['status']}]")

    def finalize(self, success=True):
        self.metrics["success"] = success
        self.metrics["duration_seconds"] = time.time() - self.start_time
        self.metrics["end_time"] = datetime.now().isoformat()
        
        with open(self.metrics_path, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        logger.info(f"Session finalized. Success: {success}. Duration: {self.metrics['duration_seconds']:.2f}s")

    def get_summary(self):
        return (
            f"📊 Session Summary:\n"
            f"- Steps: {self.metrics['total_steps']}\n"
            f"- Errors: {self.metrics['errors']}\n"
            f"- Duration: {self.metrics['duration_seconds']:.1f}s\n"
            f"- Status: {'✅ Success' if self.metrics['success'] else '❌ Failed'}"
        )
