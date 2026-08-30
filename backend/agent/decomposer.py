"""
PrivyBrowse AI — Goal Decomposition Engine
Transforms natural-language user tasks into structured, ordered sub-objectives with concrete success criteria.
Dynamically extracts intents, query strings, domain targets, and attribute keywords.
"""

import re
from typing import List, Dict, Any, Optional
from backend.agent.schemas import Objective, ObjectiveStatus


class GoalDecomposer:
    """
    Decomposes high-level natural language browser goals into structured sequences of sub-objectives.
    """

    def __init__(self):
        pass

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

    def decompose(self, goal_text: str) -> List[Objective]:
        """
        Decomposes goal_text into an ordered list of Objectives.
        """
        goal_lower = goal_text.strip().lower()
        objectives: List[Objective] = []

        # -------------------------------------------------------------
        # 1. SEARCH & LOOKUP TASKS
        # E.g. "Search for Aditya-L1 Mission", "Find the latest information about ISRO"
        # -------------------------------------------------------------
        if any(w in goal_lower for w in ["search", "find", "lookup", "google", "wiki", "query", "explore"]):
            query = self._extract_search_query(goal_text)
            domain = self._extract_domain_target(goal_text)

            query_tokens = [t.lower() for t in re.split(r'\W+', query) if len(t) > 1]
            search_keywords = ["search", "query", "q", "input", "find", "search-box", "search_input"] + query_tokens

            # Objective 1: Locate & Type Search Query
            objectives.append(Objective(
                id="obj-001",
                description=f"Locate and enter search query '{query}' into the search field",
                target_type="INPUT",
                semantic_intent="search_input",
                target_keywords=search_keywords,
                success_criteria=f"search input populated with '{query}'"
            ))

            # Objective 2: Submit Search
            objectives.append(Objective(
                id="obj-002",
                description=f"Submit search for '{query}'",
                target_type="BUTTON",
                semantic_intent="submit_search",
                target_keywords=["search", "submit", "go", "find", "btn-search", "search_btn", "enter"],
                success_criteria="search results page appears or DOM updates with results"
            ))

            # Objective 3: Select Result / Verify Target
            result_keywords = query_tokens + ["result", "wiki", "link", "destination", "title", "heading"]
            if domain:
                result_keywords.append(domain.lower())

            objectives.append(Objective(
                id="obj-003",
                description=f"Identify and select relevant result for '{query}'",
                target_type="LINK",
                semantic_intent="select_result",
                target_keywords=result_keywords,
                success_criteria=f"navigation or display of content relevant to '{query}' occurs"
            ))

            # Objective 4: Verify Content Loaded
            objectives.append(Objective(
                id="obj-004",
                description=f"Verify target content for '{query}' is visible",
                target_type=None,
                semantic_intent="verify_completion",
                target_keywords=query_tokens,
                success_criteria="target heading or information visible in viewport"
            ))

        # -------------------------------------------------------------
        # 2. LOGIN & AUTHENTICATION TASKS
        # E.g. "Login to the portal with user credentials"
        # -------------------------------------------------------------
        elif any(w in goal_lower for w in ["login", "sign in", "signin", "auth", "authenticate"]):
            objectives.append(Objective(
                id="obj-001",
                description="Enter account username or email address",
                target_type="INPUT",
                semantic_intent="input_username",
                target_keywords=["username", "email", "login", "user", "account", "user_email"],
                success_criteria="username field populated"
            ))
            objectives.append(Objective(
                id="obj-002",
                description="Enter account password securely",
                target_type="INPUT",
                semantic_intent="input_password",
                target_keywords=["password", "pass", "pwd", "secret", "credentials"],
                success_criteria="password field sanitized and filled"
            ))
            objectives.append(Objective(
                id="obj-003",
                description="Click Sign In button to authenticate",
                target_type="BUTTON",
                semantic_intent="submit_login",
                target_keywords=["sign in", "login", "submit", "enter", "continue", "auth-btn"],
                success_criteria="dashboard or authenticated area reached"
            ))
            objectives.append(Objective(
                id="obj-004",
                description="Verify successful authentication state",
                target_type=None,
                semantic_intent="verify_auth",
                target_keywords=["dashboard", "welcome", "logout", "profile", "account"],
                success_criteria="authenticated session active"
            ))

        # -------------------------------------------------------------
        # 3. CHECKOUT, ORDER & PAYMENT FORMS
        # E.g. "Fill out checkout form and confirm order"
        # -------------------------------------------------------------
        elif any(w in goal_lower for w in ["checkout", "billing", "payment", "card", "order", "buy", "purchase"]):
            objectives.append(Objective(
                id="obj-001",
                description="Fill customer name and contact details",
                target_type="INPUT",
                semantic_intent="input_contact",
                target_keywords=["name", "first name", "email", "phone", "contact", "customer"],
                success_criteria="contact fields filled"
            ))
            objectives.append(Objective(
                id="obj-002",
                description="Enter shipping / billing address",
                target_type="INPUT",
                semantic_intent="input_address",
                target_keywords=["address", "street", "city", "zip", "pincode", "postal"],
                success_criteria="address fields populated"
            ))
            objectives.append(Objective(
                id="obj-003",
                description="Enter payment card details",
                target_type="INPUT",
                semantic_intent="input_card",
                target_keywords=["card", "card number", "cc", "cvv", "expiry", "cardholder"],
                success_criteria="card details sanitized and populated"
            ))
            objectives.append(Objective(
                id="obj-004",
                description="Submit payment order after human confirmation",
                target_type="BUTTON",
                semantic_intent="submit_payment",
                target_keywords=["pay", "confirm", "place order", "submit payment", "buy", "charge"],
                success_criteria="payment confirmation receipt displayed"
            ))

        # -------------------------------------------------------------
        # 4. SCROLL & INSPECTION TASKS
        # E.g. "Scroll down and find specifications"
        # -------------------------------------------------------------
        elif any(w in goal_lower for w in ["scroll", "specs", "specifications", "footer", "bottom", "down"]):
            target_topic = self._extract_search_query(goal_text)
            topic_tokens = [t.lower() for t in re.split(r'\W+', target_topic) if len(t) > 1]

            objectives.append(Objective(
                id="obj-001",
                description="Scroll down the webpage to reveal offscreen sections",
                target_type=None,
                semantic_intent="scroll_page",
                target_keywords=["scroll", "down", "specifications", "footer"] + topic_tokens,
                success_criteria="viewport scroll offset increases"
            ))
            objectives.append(Objective(
                id="obj-002",
                description=f"Locate and inspect target section for '{target_topic}'",
                target_type=None,
                semantic_intent="locate_section",
                target_keywords=topic_tokens + ["specifications", "features", "details", "contact"],
                success_criteria="target section visible in viewport"
            ))

        # -------------------------------------------------------------
        # 5. GENERAL BROWSER INTERACTION
        # E.g. "Click the submit button and validate form"
        # -------------------------------------------------------------
        else:
            action_terms = [w for w in re.split(r'\W+', goal_lower) if len(w) > 2]
            objectives.append(Objective(
                id="obj-001",
                description=f"Inspect page elements and identify primary interaction for '{goal_text}'",
                target_type="BUTTON",
                semantic_intent="general_action",
                target_keywords=action_terms[:5],
                success_criteria="appropriate interactive element identified"
            ))
            objectives.append(Objective(
                id="obj-002",
                description="Execute verified action and check page response",
                target_type="BUTTON",
                semantic_intent="execute_general",
                target_keywords=action_terms[:5],
                success_criteria="page responds to executed action"
            ))

        return objectives
