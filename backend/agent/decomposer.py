"""
PrivyBrowse AI — Goal Decomposition Engine
Transforms natural-language user tasks into structured, ordered sub-objectives with concrete success criteria.
"""

import re
from typing import List
from backend.agent.schemas import Objective, ObjectiveStatus


class GoalDecomposer:
    """
    Decomposes high-level natural language browser goals into structured sequences of sub-objectives.
    """

    def __init__(self):
        pass

    def decompose(self, goal_text: str) -> List[Objective]:
        """
        Decomposes goal_text into an ordered list of Objectives.
        """
        goal_lower = goal_text.strip().lower()
        objectives: List[Objective] = []

        # -------------------------------------------------------------
        # 1. SEARCH & NAVIGATION TASKS
        # E.g. "Search for Chandrayaan-3 and open the first relevant result"
        # -------------------------------------------------------------
        if any(w in goal_lower for w in ["search", "find result", "lookup", "google", "wiki"]):
            # Extract query text if present (e.g., "Search for Chandrayaan-3")
            query = "Chandrayaan-3"
            query_match = re.search(r'(?:search\s+for|lookup|find)\s+([a-zA-Z0-9_\-\s]+?)(?:\s+and|\s+on|\.|$)', goal_lower)
            if query_match:
                query = query_match.group(1).strip()

            objectives.append(Objective(
                id="obj-001",
                description=f"Locate and focus search input for query '{query}'",
                target_type="INPUT",
                semantic_intent="search_input",
                target_keywords=["search", "query", "q", "input", "find"],
                success_criteria="search input element focused or text entered"
            ))
            objectives.append(Objective(
                id="obj-002",
                description=f"Submit search query '{query}'",
                target_type="BUTTON",
                semantic_intent="submit_search",
                target_keywords=["search", "submit", "go", "find", "enter"],
                success_criteria="search results or updated destination page appears"
            ))
            objectives.append(Objective(
                id="obj-003",
                description=f"Identify and select relevant destination link for '{query}'",
                target_type="LINK",
                semantic_intent="select_result",
                target_keywords=[query.lower(), "result", "wiki", "link", "destination"],
                success_criteria="navigation to destination article / page occurs"
            ))
            objectives.append(Objective(
                id="obj-004",
                description="Verify destination page content has loaded",
                target_type=None,
                semantic_intent="verify_navigation",
                target_keywords=[],
                success_criteria="destination URL or heading visible"
            ))

        # -------------------------------------------------------------
        # 2. LOGIN & AUTHENTICATION TASKS
        # E.g. "Login with user@sih2026.gov.in and password"
        # -------------------------------------------------------------
        elif any(w in goal_lower for w in ["login", "sign in", "signin", "auth"]):
            objectives.append(Objective(
                id="obj-001",
                description="Enter account username or email address",
                target_type="INPUT",
                semantic_intent="input_username",
                target_keywords=["username", "email", "login", "user", "account"],
                success_criteria="username field populated"
            ))
            objectives.append(Objective(
                id="obj-002",
                description="Enter account password securely",
                target_type="INPUT",
                semantic_intent="input_password",
                target_keywords=["password", "pass", "pwd", "secret"],
                success_criteria="password field sanitized and filled"
            ))
            objectives.append(Objective(
                id="obj-003",
                description="Click Sign In button to authenticate",
                target_type="BUTTON",
                semantic_intent="submit_login",
                target_keywords=["sign in", "login", "submit", "enter", "continue"],
                success_criteria="dashboard or authenticated area reached"
            ))
            objectives.append(Objective(
                id="obj-004",
                description="Verify successful authentication state",
                target_type=None,
                semantic_intent="verify_auth",
                target_keywords=["dashboard", "welcome", "logout", "profile"],
                success_criteria="authenticated session active"
            ))

        # -------------------------------------------------------------
        # 3. CHECKOUT & PAYMENT FORMS
        # E.g. "Fill out checkout form and confirm order"
        # -------------------------------------------------------------
        elif any(w in goal_lower for w in ["checkout", "billing", "payment", "card", "order", "buy"]):
            objectives.append(Objective(
                id="obj-001",
                description="Fill customer name and contact details",
                target_type="INPUT",
                semantic_intent="input_contact",
                target_keywords=["name", "first name", "email", "phone", "contact"],
                success_criteria="contact fields filled"
            ))
            objectives.append(Objective(
                id="obj-002",
                description="Enter shipping / billing address",
                target_type="INPUT",
                semantic_intent="input_address",
                target_keywords=["address", "street", "city", "zip", "pincode"],
                success_criteria="address fields populated"
            ))
            objectives.append(Objective(
                id="obj-003",
                description="Enter payment card details",
                target_type="INPUT",
                semantic_intent="input_card",
                target_keywords=["card", "card number", "cc", "cvv", "expiry"],
                success_criteria="card details sanitized and populated"
            ))
            objectives.append(Objective(
                id="obj-004",
                description="Submit payment order after confirmation verification",
                target_type="BUTTON",
                semantic_intent="submit_payment",
                target_keywords=["pay", "confirm", "place order", "submit payment", "buy"],
                success_criteria="payment confirmation receipt displayed"
            ))

        # -------------------------------------------------------------
        # 4. SCROLL & INSPECTION TASKS
        # E.g. "Scroll down and find specifications"
        # -------------------------------------------------------------
        elif any(w in goal_lower for w in ["scroll", "specs", "specifications", "footer", "bottom"]):
            objectives.append(Objective(
                id="obj-001",
                description="Scroll down the webpage to reveal offscreen sections",
                target_type=None,
                semantic_intent="scroll_page",
                target_keywords=["scroll", "down", "specifications", "footer"],
                success_criteria="viewport scroll offset increases"
            ))
            objectives.append(Objective(
                id="obj-002",
                description="Locate target information section",
                target_type=None,
                semantic_intent="locate_section",
                target_keywords=["specifications", "features", "details", "contact"],
                success_criteria="target section visible in viewport"
            ))

        # -------------------------------------------------------------
        # 5. GENERIC / PRIVACY INSPECTION TASK
        # -------------------------------------------------------------
        else:
            objectives.append(Objective(
                id="obj-001",
                description=f"Inspect page elements and identify primary action for '{goal_text}'",
                target_type="BUTTON",
                semantic_intent="general_action",
                target_keywords=goal_lower.split()[:4],
                success_criteria="appropriate interactive element identified"
            ))
            objectives.append(Objective(
                id="obj-002",
                description="Execute verified action and check page response",
                target_type="BUTTON",
                semantic_intent="execute_general",
                target_keywords=goal_lower.split()[:4],
                success_criteria="page responds to executed action"
            ))

        return objectives
