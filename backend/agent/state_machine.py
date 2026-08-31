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
    AgentState.CREATED: {
        AgentState.UNDERSTANDING,
        AgentState.PLANNING,
        AgentState.OBSERVING,
        AgentState.PERCEIVING,
        AgentState.IDLE,
        AgentState.CANCELLED,
        AgentState.FAILED
    },
    AgentState.IDLE: {
        AgentState.CREATED,
        AgentState.OBSERVING,
        AgentState.PERCEIVING,
        AgentState.UNDERSTANDING,
        AgentState.PLANNING,
        AgentState.PAUSED,
        AgentState.CANCELLED
    },
    AgentState.PLANNED: {
        AgentState.READY,
        AgentState.OBSERVING,
        AgentState.PLANNING,
        AgentState.EXECUTING,
        AgentState.ACTING,
        AgentState.CANCELLED,
        AgentState.FAILED
    },
    AgentState.READY: {
        AgentState.EXECUTING,
        AgentState.ACTING,
        AgentState.PLANNING,
        AgentState.OBSERVING,
        AgentState.NEEDS_CONFIRMATION,
        AgentState.AWAITING_CONFIRMATION,
        AgentState.CANCELLED,
        AgentState.FAILED
    },
    AgentState.OBSERVING: {
        AgentState.PERCEIVING,
        AgentState.UNDERSTANDING,
        AgentState.PLANNING,
        AgentState.FAILED,
        AgentState.PAUSED,
        AgentState.BLOCKED,
        AgentState.CANCELLED,
        AgentState.IDLE
    },
    AgentState.PERCEIVING: {
        AgentState.UNDERSTANDING,
        AgentState.PLANNING,
        AgentState.FAILED,
        AgentState.PAUSED,
        AgentState.BLOCKED,
        AgentState.CANCELLED,
        AgentState.IDLE
    },
    AgentState.UNDERSTANDING: {
        AgentState.PLANNING,
        AgentState.READY,
        AgentState.FAILED,
        AgentState.PAUSED,
        AgentState.BLOCKED,
        AgentState.CANCELLED,
        AgentState.IDLE
    },
    AgentState.PLANNING: {
        AgentState.READY,
        AgentState.VALIDATING,
        AgentState.EXECUTING,
        AgentState.ACTING,
        AgentState.NEEDS_CONFIRMATION,
        AgentState.AWAITING_CONFIRMATION,
        AgentState.COMPLETED,
        AgentState.FAILED,
        AgentState.PAUSED,
        AgentState.BLOCKED,
        AgentState.CANCELLED,
        AgentState.IDLE
    },
    AgentState.VALIDATING: {
        AgentState.READY,
        AgentState.ACTING,
        AgentState.EXECUTING,
        AgentState.NEEDS_CONFIRMATION,
        AgentState.AWAITING_CONFIRMATION,
        AgentState.BLOCKED,
        AgentState.PLANNING,
        AgentState.FAILED,
        AgentState.PAUSED,
        AgentState.CANCELLED,
        AgentState.IDLE
    },
    AgentState.ACTING: {
        AgentState.VERIFYING,
        AgentState.EXECUTING,
        AgentState.RECOVERING,
        AgentState.FAILED,
        AgentState.PAUSED,
        AgentState.CANCELLED,
        AgentState.IDLE
    },
    AgentState.EXECUTING: {
        AgentState.VERIFYING,
        AgentState.WAITING,
        AgentState.RECOVERING,
        AgentState.FAILED,
        AgentState.PAUSED,
        AgentState.CANCELLED,
        AgentState.IDLE
    },
    AgentState.WAITING: {
        AgentState.VERIFYING,
        AgentState.EXECUTING,
        AgentState.RECOVERING,
        AgentState.OBSERVING,
        AgentState.CANCELLED,
        AgentState.FAILED
    },
    AgentState.VERIFYING: {
        AgentState.OBSERVING,
        AgentState.PLANNING,
        AgentState.READY,
        AgentState.EXECUTING,
        AgentState.ACTING,
        AgentState.RECOVERING,
        AgentState.COMPLETED,
        AgentState.FAILED,
        AgentState.PAUSED,
        AgentState.BLOCKED,
        AgentState.CANCELLED,
        AgentState.IDLE
    },
    AgentState.RECOVERING: {
        AgentState.OBSERVING,
        AgentState.PERCEIVING,
        AgentState.PLANNING,
        AgentState.READY,
        AgentState.EXECUTING,
        AgentState.ACTING,
        AgentState.BLOCKED,
        AgentState.CANCELLED,
        AgentState.FAILED,
        AgentState.IDLE
    },
    AgentState.NEEDS_CONFIRMATION: {
        AgentState.READY,
        AgentState.EXECUTING,
        AgentState.ACTING,
        AgentState.PLANNING,
        AgentState.CANCELLED,
        AgentState.FAILED,
        AgentState.BLOCKED
    },
    AgentState.AWAITING_CONFIRMATION: {
        AgentState.READY,
        AgentState.EXECUTING,
        AgentState.ACTING,
        AgentState.PLANNING,
        AgentState.CANCELLED,
        AgentState.FAILED,
        AgentState.BLOCKED
    },
    AgentState.PAUSED: {
        AgentState.OBSERVING,
        AgentState.PERCEIVING,
        AgentState.PLANNING,
        AgentState.READY,
        AgentState.EXECUTING,
        AgentState.ACTING,
        AgentState.CANCELLED,
        AgentState.IDLE,
        AgentState.FAILED
    },
    AgentState.BLOCKED: {
        AgentState.IDLE,
        AgentState.PLANNING,
        AgentState.RECOVERING,
        AgentState.ACTING,
        AgentState.EXECUTING,
        AgentState.CANCELLED,
        AgentState.FAILED
    },
    AgentState.COMPLETED: {
        AgentState.IDLE,
        AgentState.CREATED
    },
    AgentState.FAILED: {
        AgentState.IDLE,
        AgentState.CREATED,
        AgentState.RECOVERING
    },
    AgentState.CANCELLED: {
        AgentState.IDLE,
        AgentState.CREATED
    }
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
