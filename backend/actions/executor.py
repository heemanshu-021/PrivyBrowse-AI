from typing import Dict, Any, Tuple
from backend.agent.validator import ActionValidator

class ActionExecutor:
    def __init__(self):
        self.validator = ActionValidator()

    def execute_action(self, action_json: Dict[str, Any], screen_w: int = 1920, screen_h: int = 1080) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validates and routes the action for execution.
        Returns (success, message, result_metadata).
        """
        # Validate action schema and limits
        is_valid, err_msg = self.validator.validate_action(action_json, screen_w, screen_h)
        if not is_valid:
            return False, f"Safety block / validation error: {err_msg}", {}

        action_name = action_json["action"]
        target = action_json.get("target", {"x": 0, "y": 0})
        text = action_json.get("text", "")
        
        # Check safety restrictions (Problem Statement: require user confirmation for dangerous tasks)
        requires_confirm = action_json.get("requires_confirmation", False)
        # If it's a click on submit/payment without user-confirmation flag active
        if action_name == "CLICK" and "pay" in action_json.get("target_description", "").lower():
            requires_confirm = True

        if requires_confirm:
            return False, "CONFIRMATION_REQUIRED", {
                "message": f"Agent wants to perform a potentially irreversible action: {action_json.get('target_description', 'Action')}. Please confirm.",
                "action": action_json
            }

        # Simulated execution details
        result_meta = {
            "action": action_name,
            "target": target,
            "text_sent": text,
            "latency_ms": 12.0, # execution trigger time
            "status": "SUCCESS"
        }

        return True, f"Successfully simulated action: {action_name} at ({target.get('x')}, {target.get('y')})", result_meta
