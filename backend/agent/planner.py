from typing import List, Dict, Any

class AgentPlanner:
    def __init__(self):
        pass

    def plan_action(self, task: str, fused_elements: List[Dict[str, Any]], history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Receives a user task and sanitized layout context, and decides the next action.
        This local decision-maker acts on the elements to advance the browser task.
        """
        task_lower = task.lower()
        
        # Helper to find elements by matching descriptors/attributes
        def find_element(el_type: str, keywords: List[str]) -> Dict[str, Any]:
            for el in fused_elements:
                if el["type"] == el_type:
                    # Check text, placeholder, or attributes
                    attrs = el.get("attributes", {})
                    combined_str = f"{el.get('text', '')} {attrs.get('placeholder', '')} {attrs.get('id', '')} {attrs.get('class', '')} {attrs.get('type', '')}".lower()
                    if any(k in combined_str for k in keywords):
                        return el
            # Fallback to first element of type if no keyword matches
            for el in fused_elements:
                if el["type"] == el_type:
                    return el
            return None

        # --- SCENARIO A: LOGIN TASK ---
        if "login" in task_lower or "signin" in task_lower or "sign in" in task_lower:
            username_field = find_element("INPUT", ["username", "email", "login", "user"])
            password_field = find_element("INPUT", ["password", "pass", "pwd"])
            login_btn = find_element("BUTTON", ["login", "submit", "sign", "enter"])

            # Detect if fields already have values (redacted or not)
            username_filled = False
            password_filled = False
            
            if username_field and (username_field.get("value") or "[EMAIL REDACTED]" in username_field.get("text", "") or "[NAME REDACTED]" in username_field.get("text", "")):
                username_filled = True
            if password_field and (password_field.get("value") or "[PASSWORD REDACTED]" in password_field.get("text", "")):
                password_filled = True

            # If username is not filled, type username
            if username_field and not username_filled:
                bbox = username_field["bbox"]
                x = (bbox[0] + bbox[2]) // 2
                y = (bbox[1] + bbox[3]) // 2
                return {
                    "action": "TYPE",
                    "target": {"x": x, "y": y},
                    "target_description": f"Username field ({username_field['id']})",
                    "text": "user@sih2026.gov.in",
                    "confidence": 0.95,
                    "element_id": username_field["id"]
                }
            
            # If password is not filled, type password
            if password_field and not password_filled:
                bbox = password_field["bbox"]
                x = (bbox[0] + bbox[2]) // 2
                y = (bbox[1] + bbox[3]) // 2
                return {
                    "action": "TYPE",
                    "target": {"x": x, "y": y},
                    "target_description": f"Password field ({password_field['id']})",
                    "text": "PrivySafePassword123!",
                    "confidence": 0.96,
                    "element_id": password_field["id"]
                }
            
            # Both filled, click login button
            if login_btn:
                bbox = login_btn["bbox"]
                x = (bbox[0] + bbox[2]) // 2
                y = (bbox[1] + bbox[3]) // 2
                return {
                    "action": "CLICK",
                    "target": {"x": x, "y": y},
                    "target_description": f"Login button ({login_btn['id']})",
                    "confidence": 0.92,
                    "element_id": login_btn["id"]
                }

        # --- SCENARIO B: SEARCH TASK ---
        elif "search" in task_lower or "find" in task_lower or "chandrayaan" in task_lower:
            search_field = find_element("INPUT", ["search", "query", "q", "input"])
            search_btn = find_element("BUTTON", ["search", "go", "submit"])
            result_link = find_element("LINK", ["chandrayaan", "result", "wiki", "about"])

            search_filled = False
            if search_field and search_field.get("value"):
                search_filled = True

            # If search input exists and is empty, type search query
            if search_field and not search_filled:
                bbox = search_field["bbox"]
                x = (bbox[0] + bbox[2]) // 2
                y = (bbox[1] + bbox[3]) // 2
                query = "Chandrayaan-3 Mission"
                if "chandrayaan" in task_lower:
                    query = "Chandrayaan-3"
                return {
                    "action": "TYPE",
                    "target": {"x": x, "y": y},
                    "target_description": f"Search input field ({search_field['id']})",
                    "text": query,
                    "confidence": 0.94,
                    "element_id": search_field["id"]
                }
            
            # Click search button if field is filled
            if search_btn and search_filled:
                bbox = search_btn["bbox"]
                x = (bbox[0] + bbox[2]) // 2
                y = (bbox[1] + bbox[3]) // 2
                return {
                    "action": "CLICK",
                    "target": {"x": x, "y": y},
                    "target_description": f"Search submit button ({search_btn['id']})",
                    "confidence": 0.90,
                    "element_id": search_btn["id"]
                }
                
            # Click first relevant link if we already performed the search
            if result_link:
                bbox = result_link["bbox"]
                x = (bbox[0] + bbox[2]) // 2
                y = (bbox[1] + bbox[3]) // 2
                return {
                    "action": "CLICK",
                    "target": {"x": x, "y": y},
                    "target_description": f"Result link ({result_link['text']})",
                    "confidence": 0.88,
                    "element_id": result_link["id"]
                }

        # --- SCENARIO C: GENERAL SECURE FORM FILL (e.g. checkout form) ---
        elif "form" in task_lower or "fill" in task_lower or "checkout" in task_lower or "pay" in task_lower:
            card_field = find_element("INPUT", ["card", "number", "cc"])
            name_field = find_element("INPUT", ["name", "owner"])
            email_field = find_element("INPUT", ["email"])
            submit_btn = find_element("BUTTON", ["submit", "pay", "checkout", "confirm"])

            card_filled = card_field and (card_field.get("value") or "[CARD REDACTED]" in card_field.get("text", ""))
            name_filled = name_field and (name_field.get("value") or "[NAME REDACTED]" in name_field.get("text", ""))
            email_filled = email_field and (email_field.get("value") or "[EMAIL REDACTED]" in email_field.get("text", ""))

            if email_field and not email_filled:
                bbox = email_field["bbox"]
                x = (bbox[0] + bbox[2]) // 2
                y = (bbox[1] + bbox[3]) // 2
                return {
                    "action": "TYPE",
                    "target": {"x": x, "y": y},
                    "target_description": "Email checkout input",
                    "text": "judge_sih@gov.in",
                    "confidence": 0.95,
                    "element_id": email_field["id"]
                }
            if name_field and not name_filled:
                bbox = name_field["bbox"]
                x = (bbox[0] + bbox[2]) // 2
                y = (bbox[1] + bbox[3]) // 2
                return {
                    "action": "TYPE",
                    "target": {"x": x, "y": y},
                    "target_description": "Name checkout input",
                    "text": "Prof. Amit Verma",
                    "confidence": 0.93,
                    "element_id": name_field["id"]
                }
            if card_field and not card_filled:
                bbox = card_field["bbox"]
                x = (bbox[0] + bbox[2]) // 2
                y = (bbox[1] + bbox[3]) // 2
                return {
                    "action": "TYPE",
                    "target": {"x": x, "y": y},
                    "target_description": "Credit Card number input",
                    "text": "4111 2222 3333 4444",
                    "confidence": 0.98,
                    "element_id": card_field["id"]
                }
            if submit_btn:
                bbox = submit_btn["bbox"]
                x = (bbox[0] + bbox[2]) // 2
                y = (bbox[1] + bbox[3]) // 2
                return {
                    "action": "CLICK",
                    "target": {"x": x, "y": y},
                    "target_description": "Submit / Checkout payment button",
                    "confidence": 0.90,
                    "element_id": submit_btn["id"],
                    "requires_confirmation": True # Mark checkout as safety-critical
                }

        # --- DEFAULT / FALLBACK ACTIONS ---
        # Look for buttons or clickable objects to wait/finish
        if history and len(history) >= 4:
            return {
                "action": "FINISH",
                "target": {"x": 0, "y": 0},
                "target_description": "Task complete: Maximum actions reached",
                "confidence": 0.99
            }
            
        return {
            "action": "WAIT",
            "target": {"x": 0, "y": 0},
            "target_description": "Idle wait: Analyzing page changes",
            "confidence": 0.85
        }
