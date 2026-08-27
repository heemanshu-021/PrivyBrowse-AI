from typing import Dict, Any, Tuple

class ActionValidator:
    def __init__(self):
        self.valid_actions = {
            "CLICK", "TYPE", "SCROLL", "PRESS_KEY", 
            "NAVIGATE", "WAIT", "GO_BACK", "GO_FORWARD", "FINISH"
        }

    def validate_action(self, action_json: Dict[str, Any], screen_width: int = 1920, screen_height: int = 1080) -> Tuple[bool, str]:
        """
        Validates that an action conforms to the expected schemas and bounds.
        Returns (is_valid, error_message).
        """
        if not isinstance(action_json, dict):
            return False, "Action must be a JSON object"

        action_name = action_json.get("action")
        if not action_name or action_name not in self.valid_actions:
            return False, f"Invalid or missing action name: {action_name}. Must be one of {self.valid_actions}"

        # Coordinate-based validation for CLICK, TYPE
        if action_name in ["CLICK", "TYPE"]:
            target = action_json.get("target")
            if not target or not isinstance(target, dict):
                return False, f"Action {action_name} requires a target coordinate object"
            
            x = target.get("x")
            y = target.get("y")
            
            if x is None or y is None:
                return False, f"Target coordinates x and y are required for {action_name}"
                
            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                return False, "Target coordinates must be numbers"
                
            if x < 0 or y < 0:
                return False, "Coordinates cannot be negative"
                
            if x > screen_width or y > screen_height:
                return False, f"Coordinates ({x}, {y}) are out of boundary of screen dimensions ({screen_width}x{screen_height})"

        # Check TYPE specific parameters
        if action_name == "TYPE":
            text = action_json.get("text")
            if text is None:
                return False, "Action TYPE requires a 'text' parameter"

        # Check navigation parameters
        if action_name == "NAVIGATE":
            url = action_json.get("url")
            if not url:
                return False, "Action NAVIGATE requires a 'url' parameter"

        return True, "Valid"
