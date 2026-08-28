# Goal Decomposition, Candidate Generation & Action Scoring

## 1. Goal Decomposition Engine
High-level user tasks are decomposed into discrete, ordered sub-objectives (`Objective`). Each sub-objective specifies target control types, semantic intents, and concrete verification criteria:

### Example: Search Task
```json
[
  {
    "id": "obj-001",
    "description": "Locate and focus search input for query 'Chandrayaan-3'",
    "target_type": "INPUT",
    "semantic_intent": "search_input",
    "success_criteria": "search input element focused or text entered"
  },
  {
    "id": "obj-002",
    "description": "Submit search query 'Chandrayaan-3'",
    "target_type": "BUTTON",
    "semantic_intent": "submit_search",
    "success_criteria": "search results or updated destination page appears"
  },
  {
    "id": "obj-003",
    "description": "Identify and select relevant destination link for 'Chandrayaan-3'",
    "target_type": "LINK",
    "semantic_intent": "select_result",
    "success_criteria": "navigation to destination article / page occurs"
  },
  {
    "id": "obj-004",
    "description": "Verify destination page content has loaded",
    "target_type": null,
    "semantic_intent": "verify_navigation",
    "success_criteria": "destination URL or heading visible"
  }
]
```

---

## 2. Transparent Multi-Factor Action Scoring
Every candidate action is ranked using an explainable mathematical formula:

$$\text{Composite Score} = 0.40 \cdot S_{\text{semantic}} + 0.25 \cdot S_{\text{confidence}} + 0.20 \cdot S_{\text{type}} + 0.15 \cdot S_{\text{visibility}} - P_{\text{history}} - P_{\text{risk}}$$

### Factor Definitions:
1. **$S_{\text{semantic}}$ (Semantic Keyword Match, Weight = 0.40)**: Overlap between element text, placeholder, ID, class, and objective target keywords.
2. **$S_{\text{confidence}}$ (Perception Confidence, Weight = 0.25)**: Fused multi-source confidence (DOM + OCR + Contour).
3. **$S_{\text{type}}$ (Target Type Alignment, Weight = 0.20)**: $1.0$ if element matches target type (`INPUT`, `BUTTON`, `LINK`), $0.4$ otherwise.
4. **$S_{\text{visibility}}$ (Viewport Visibility, Weight = 0.15)**: $1.0$ for `VISIBLE`, $0.6$ for `PARTIALLY_VISIBLE`, $0.1$ for `OFFSCREEN`.
5. **$P_{\text{history}}$ (Repeat Attempt Penalty)**: $-0.15$ for each recent failure on the same target to prevent looping.
6. **$P_{\text{risk}}$ (Unconfirmed Risk Penalty)**: $-0.10$ for unconfirmed high-risk actions.
