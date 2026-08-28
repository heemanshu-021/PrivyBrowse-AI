"""
PrivyBrowse AI — Agent State Machine
Enforces valid state transitions across the browser agent perception-action loop:
  OBSERVE → PERCEIVE → UNDERSTAND → PLAN → VALIDATE → ACT → VERIFY → (RE-OBSERVE / COMPLETE)
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set
from backend.agent.schemas import AgentState


class InvalidStateTransitionError(Exception):
    """Raised when an illegal state transition is attempted."""
    pass


# Map of valid state transitions
VALID_TRANSITIONS: Dict[AgentState, Set[AgentState]] = {
    AgentState.IDLE: {
        AgentState.OBSERVING,
        AgentState.PLANNING,
        AgentState.PAUSED
    },
    AgentState.OBSERVING: {
        AgentState.PERCEIVING,
        AgentState.FAILED,
        AgentState.PAUSED,
        AgentState.BLOCKED,
        AgentState.IDLE
    },
    AgentState.PERCEIVING: {
        AgentState.UNDERSTANDING,
        AgentState.FAILED,
        AgentState.PAUSED,
        AgentState.BLOCKED,
        AgentState.IDLE
    },
    AgentState.UNDERSTANDING: {
        AgentState.PLANNING,
        AgentState.FAILED,
        AgentState.PAUSED,
        AgentState.BLOCKED,
        AgentState.IDLE
    },
    AgentState.PLANNING: {
        AgentState.VALIDATING,
        AgentState.COMPLETED,
        AgentState.FAILED,
        AgentState.PAUSED,
        AgentState.BLOCKED,
        AgentState.IDLE
    },
    AgentState.VALIDATING: {
        AgentState.ACTING,
        AgentState.BLOCKED,
        AgentState.PLANNING,
        AgentState.FAILED,
        AgentState.PAUSED,
        AgentState.IDLE
    },
    AgentState.ACTING: {
        AgentState.VERIFYING,
        AgentState.FAILED,
        AgentState.PAUSED,
        AgentState.IDLE
    },
    AgentState.VERIFYING: {
        AgentState.OBSERVING,
        AgentState.PLANNING,
        AgentState.COMPLETED,
        AgentState.FAILED,
        AgentState.PAUSED,
        AgentState.BLOCKED,
        AgentState.IDLE
    },
    AgentState.PAUSED: {
        AgentState.OBSERVING,
        AgentState.PERCEIVING,
        AgentState.PLANNING,
        AgentState.IDLE,
        AgentState.FAILED
    },
    AgentState.BLOCKED: {
        AgentState.IDLE,
        AgentState.PLANNING,
        AgentState.ACTING,
        AgentState.FAILED
    },
    AgentState.COMPLETED: {
        AgentState.IDLE,
        AgentState.OBSERVING
    },
    AgentState.FAILED: {
        AgentState.IDLE,
        AgentState.OBSERVING
    },
}


class AgentStateMachine:
    """Explicit state machine managing agent execution lifecycle."""

    def __init__(self, initial_state: AgentState = AgentState.IDLE):
        self._current_state = initial_state
        self._history: List[Dict[str, Any]] = [
            {
                "state": initial_state.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reason": "INITIALIZATION"
            }
        ]

    @property
    def current_state(self) -> AgentState:
        return self._current_state

    def can_transition_to(self, target_state: AgentState) -> bool:
        """Returns True if transition to target_state is allowed from current state."""
        allowed = VALID_TRANSITIONS.get(self._current_state, set())
        return target_state in allowed

    def transition_to(self, target_state: AgentState, reason: str = "") -> AgentState:
        """
        Transitions to target_state if valid.
        Raises InvalidStateTransitionError on illegal transition.
        """
        if not self.can_transition_to(target_state):
            err_msg = (
                f"INVALID_STATE_TRANSITION: Cannot transition from {self._current_state.value} "
                f"to {target_state.value}. Allowed target states: {[s.value for s in VALID_TRANSITIONS.get(self._current_state, set())]}"
            )
            raise InvalidStateTransitionError(err_msg)

        old_state = self._current_state
        self._current_state = target_state
        self._history.append({
            "from": old_state.value,
            "to": target_state.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason
        })
        return self._current_state

    def reset(self) -> AgentState:
        """Resets the state machine back to IDLE."""
        self._current_state = AgentState.IDLE
        self._history.append({
            "state": AgentState.IDLE.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": "RESET"
        })
        return self._current_state

    def get_history(self) -> List[Dict[str, Any]]:
        """Returns the full state transition audit history."""
        return list(self._history)
