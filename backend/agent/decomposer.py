"""
PrivyBrowse AI — Goal Decomposition & Dynamic Replanning Engine
Transforms natural-language user tasks into structured, ordered multi-step task plans with
concrete success criteria, step dependencies, and dynamic replanning capabilities.
"""

import re
import time
from typing import List, Dict, Any, Optional
from backend.agent.schemas import TaskStep, ObjectiveStatus, AgentTask, TaskState


from collections import OrderedDict

class GoalDecomposer:
    """
    Decomposes high-level natural language browser goals into structured sequences of TaskSteps
    and dynamically replans remaining sub-goals with LRU memoization.
    """

    def __init__(self, max_cache: int = 50):
        self._decompose_cache: OrderedDict[str, List[TaskStep]] = OrderedDict()
        self._max_cache = max_cache

    def clear_cache(self):
        """Flushes the goal decomposition cache."""
        self._decompose_cache.clear()

    def _extract_search_query(self, goal_text: str) -> str:
        """Extracts the primary search term from natural language query goals."""
        goal_clean = goal_text.strip()

        # Match "search for <query>", "find information about <query>", "lookup <query>", etc.
        patterns = [
            r'(?:search\s+for|search)\s+["\']?([^"\',.;\n]+?)["\']?(?:\s+on\s+\w+|\s+and\s+|\s+in\s+|$|\.)',
            r'(?:find\s+(?:the\s+)?(?:latest\s+)?(?:information\s+(?:about|on)\s+)?|lookup\s+)["\']?([^"\',.;\n]+?)["\']?(?:\s+on\s+\w+|\s+and\s+|\s+in\s+|$|\.)',
            r'(?:open\s+.*?and\s+(?:search\s+for|find)\s+)["\']?([^"\',.;\n]+?)["\']?(?:\s+on\s+\w+|\s+and\s+|\s+in\s+|$|\.)',
            r'(?:find\s+(?:a\s+|an\s+)?)([^"\',.;\n]+?)(?:\s+under\s+.*|\s+and\s+|\s+on\s+|$|\.)',
        ]

        for pat in patterns:
            m = re.search(pat, goal_clean, re.IGNORECASE)
            if m and m.group(1).strip():
                extracted = m.group(1).strip()
                # Remove common leading articles/prepositions
                extracted = re.sub(r'^(?:a|an|the|about|for)\s+', '', extracted, flags=re.IGNORECASE).strip()
                if extracted:
                    return extracted

        # Fallback: remove intent words and take remaining content
        stop_words = {"search", "for", "find", "the", "latest", "information", "about", "lookup", "open", "please", "and", "on"}
        words = [w for w in re.split(r'\s+', goal_clean) if w.lower() not in stop_words and len(w) > 1]
        return " ".join(words[:4]) if words else goal_clean

    def _extract_domain_target(self, goal_text: str) -> Optional[str]:
        """Extracts destination domain/website if specified (e.g. 'on Wikipedia', 'on ISRO portal')."""
        m = re.search(r'\bon\s+([A-Za-z0-9_\-\.]+?)(?:\s+and|\s+for|$|\.|\,)', goal_text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        return None

    def decompose(self, goal_text: str) -> List[TaskStep]:
        """
        Decomposes goal_text into an ordered list of TaskSteps with step dependencies.
        """
        if not goal_text:
            return []

        clean_key = goal_text.strip()
        if clean_key in self._decompose_cache:
            self._decompose_cache.move_to_end(clean_key)
            return [TaskStep(**s.model_dump()) for s in self._decompose_cache[clean_key]]

        goal_lower = clean_key.lower()
        steps: List[TaskStep] = []

        # -------------------------------------------------------------
        # 1. SEARCH & LOOKUP TASKS
        # E.g. "Search for Aditya-L1 Mission", "Find the latest information about ISRO"
        # -------------------------------------------------------------
        if any(w in goal_lower for w in ["search", "find", "lookup", "google", "wiki", "query", "explore"]):
            query = self._extract_search_query(goal_text)
            domain = self._extract_domain_target(goal_text)

            query_tokens = [t.lower() for t in re.split(r'\W+', query) if len(t) > 1]
            search_keywords = ["search", "query", "q", "input", "find", "search-box", "search_input"] + query_tokens

            # Step 1: Locate & Type Search Query
            steps.append(TaskStep(
                id="step-001",
                description=f"Locate and enter search query '{query}' into the search field",
                target_type="INPUT",
                semantic_intent="search_input",
                target_keywords=search_keywords,
                success_criteria=f"search input populated with '{query}'",
                expected_result=f"Input populated with '{query}'",
                dependencies=[]
            ))

            # Step 2: Submit Search
            steps.append(TaskStep(
                id="step-002",
                description=f"Submit search for '{query}'",
                target_type="BUTTON",
                semantic_intent="submit_search",
                target_keywords=["search", "submit", "go", "find", "btn-search", "search_btn", "enter"],
                success_criteria="search results page appears or DOM updates with results",
                expected_result="Search results rendered in DOM",
                dependencies=["step-001"]
            ))

            # Step 3: Select Result / Verify Target
            result_keywords = query_tokens + ["result", "wiki", "link", "destination", "title", "heading"]
            if domain:
                result_keywords.append(domain.lower())

            steps.append(TaskStep(
                id="step-003",
                description=f"Identify and select relevant result for '{query}'",
                target_type="LINK",
                semantic_intent="select_result",
                target_keywords=result_keywords,
                success_criteria=f"navigation or display of content relevant to '{query}' occurs",
                expected_result="Article or destination page navigated",
                dependencies=["step-002"]
            ))

            # Step 4: Verify Content Loaded
            steps.append(TaskStep(
                id="step-004",
                description=f"Verify target content for '{query}' is visible",
                target_type=None,
                semantic_intent="verify_completion",
                target_keywords=query_tokens,
                success_criteria="target heading or information visible in viewport",
                expected_result="Target section verified",
                dependencies=["step-003"]
            ))

        # -------------------------------------------------------------
        # 2. LOGIN & AUTHENTICATION TASKS
        # E.g. "Login to the portal with user credentials"
        # -------------------------------------------------------------
        elif any(w in goal_lower for w in ["login", "sign in", "signin", "auth", "authenticate"]):
            steps.append(TaskStep(
                id="step-001",
                description="Enter account username or email address",
                target_type="INPUT",
                semantic_intent="input_username",
                target_keywords=["username", "email", "login", "user", "account", "user_email"],
                success_criteria="username field populated",
                dependencies=[]
            ))
            steps.append(TaskStep(
                id="step-002",
                description="Enter account password securely",
                target_type="INPUT",
                semantic_intent="input_password",
                target_keywords=["password", "pass", "pwd", "secret", "credentials"],
                success_criteria="password field sanitized and filled",
                dependencies=["step-001"]
            ))
            steps.append(TaskStep(
                id="step-003",
                description="Click Sign In button to authenticate",
                target_type="BUTTON",
                semantic_intent="submit_login",
                target_keywords=["sign in", "login", "submit", "enter", "continue", "auth-btn"],
                success_criteria="dashboard or authenticated area reached",
                dependencies=["step-002"]
            ))
            steps.append(TaskStep(
                id="step-004",
                description="Verify successful authentication state",
                target_type=None,
                semantic_intent="verify_auth",
                target_keywords=["dashboard", "welcome", "logout", "profile", "account"],
                success_criteria="authenticated session active",
                dependencies=["step-003"]
            ))

        # -------------------------------------------------------------
        # 3. CHECKOUT, ORDER & PAYMENT FORMS
        # E.g. "Fill out checkout form and confirm order"
        # -------------------------------------------------------------
        elif any(w in goal_lower for w in ["checkout", "billing", "payment", "card", "order", "buy", "purchase"]):
            steps.append(TaskStep(
                id="step-001",
                description="Fill customer name and contact details",
                target_type="INPUT",
                semantic_intent="input_contact",
                target_keywords=["name", "first name", "email", "phone", "contact", "customer"],
                success_criteria="contact fields filled",
                dependencies=[]
            ))
            steps.append(TaskStep(
                id="step-002",
                description="Enter shipping / billing address",
                target_type="INPUT",
                semantic_intent="input_address",
                target_keywords=["address", "street", "city", "zip", "pincode", "postal"],
                success_criteria="address fields populated",
                dependencies=["step-001"]
            ))
            steps.append(TaskStep(
                id="step-003",
                description="Enter payment card details",
                target_type="INPUT",
                semantic_intent="input_card",
                target_keywords=["card", "card number", "cc", "cvv", "expiry", "cardholder"],
                success_criteria="card details sanitized and populated",
                dependencies=["step-002"]
            ))
            steps.append(TaskStep(
                id="step-004",
                description="Submit payment order after human confirmation",
                target_type="BUTTON",
                semantic_intent="submit_payment",
                target_keywords=["pay", "confirm", "place order", "submit payment", "buy", "charge"],
                success_criteria="payment confirmation receipt displayed",
                dependencies=["step-003"]
            ))

        # -------------------------------------------------------------
        # 4. SCROLL & INSPECTION TASKS
        # -------------------------------------------------------------
        elif any(w in goal_lower for w in ["scroll", "specs", "specifications", "footer", "bottom", "down"]):
            target_topic = self._extract_search_query(goal_text)
            topic_tokens = [t.lower() for t in re.split(r'\W+', target_topic) if len(t) > 1]

            steps.append(TaskStep(
                id="step-001",
                description="Scroll down the webpage to reveal offscreen sections",
                target_type=None,
                semantic_intent="scroll_page",
                target_keywords=["scroll", "down", "specifications", "footer"] + topic_tokens,
                success_criteria="viewport scroll offset increases",
                dependencies=[]
            ))
            steps.append(TaskStep(
                id="step-002",
                description=f"Locate and inspect target section for '{target_topic}'",
                target_type=None,
                semantic_intent="locate_section",
                target_keywords=topic_tokens + ["specifications", "features", "details", "contact"],
                success_criteria="target section visible in viewport",
                dependencies=["step-001"]
            ))

        # -------------------------------------------------------------
        # 5. GENERAL BROWSER INTERACTION
        # -------------------------------------------------------------
        else:
            action_terms = [w for w in re.split(r'\W+', goal_lower) if len(w) > 2]
            steps.append(TaskStep(
                id="step-001",
                description=f"Inspect page elements and identify primary interaction for '{goal_text}'",
                target_type="BUTTON",
                semantic_intent="general_action",
                target_keywords=action_terms[:5],
                success_criteria="appropriate interactive element identified",
                dependencies=[]
            ))
            steps.append(TaskStep(
                id="step-002",
                description="Execute verified action and check page response",
                target_type="BUTTON",
                semantic_intent="execute_general",
                target_keywords=action_terms[:5],
                success_criteria="page responds to executed action",
                dependencies=["step-001"]
            ))

        self._decompose_cache[clean_key] = steps
        if len(self._decompose_cache) > self._max_cache:
            self._decompose_cache.popitem(last=False)

        return steps

    def decompose_with_context(
        self,
        goal_text: str,
        current_url: str = "",
        current_elements: List[Dict[str, Any]] = None
    ) -> List[TaskStep]:
        """
        Context-aware decomposition: inspects the initial page layout to optimize
        the initial step plan (e.g. skip typing if results are already visible).
        """
        base_steps = self.decompose(goal_text)
        elements = current_elements or []
        if not elements:
            return base_steps

        page_text = " ".join([
            str(e.get("text", "")) + " " + str(e.get("label", "")) + " " + str(e.get("attributes", {}).get("placeholder", ""))
            for e in elements
        ]).lower()

        query = self._extract_search_query(goal_text).lower()

        # If search query results already visible on page, adjust steps to focus directly on selecting result
        if query and query in page_text and any(w in page_text for w in ["result", "results", "article", "match"]):
            optimized_steps = [s for s in base_steps if s.semantic_intent in ("select_result", "verify_completion")]
            if optimized_steps:
                optimized_steps[0].dependencies = []
                return optimized_steps

        return base_steps

    def replan_remaining_steps(
        self,
        task: AgentTask,
        failed_step_index: int,
        current_elements: List[Dict[str, Any]],
        current_url: str = "",
        failure_reason: str = ""
    ) -> List[TaskStep]:
        """
        Dynamically replans remaining sub-goals when navigation occurs or a step fails.
        Preserves previously completed steps and regenerates steps from current_step_index onwards.
        """
        if failed_step_index >= len(task.steps):
            return task.steps

        completed_steps = task.steps[:failed_step_index]
        remaining_goal = task.goal

        # Generate fresh steps from current context
        fresh_steps = self.decompose_with_context(
            goal_text=remaining_goal,
            current_url=current_url,
            current_elements=current_elements
        )

        # Re-index and link dependencies
        reindexed_fresh = []
        for idx, s in enumerate(fresh_steps):
            new_id = f"step-{failed_step_index + idx + 1:03d}"
            prev_id = completed_steps[-1].id if (idx == 0 and completed_steps) else (reindexed_fresh[-1].id if reindexed_fresh else None)
            deps = [prev_id] if prev_id else []
            s_copy = s.model_copy(update={"id": new_id, "dependencies": deps})
            reindexed_fresh.append(s_copy)

        updated_plan = completed_steps + reindexed_fresh
        task.steps = updated_plan
        task.replan_count += 1
        return updated_plan
