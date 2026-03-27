"""Lab 28: Human-in-the-Loop (HITL) — Solution"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))
from utils import get_anthropic_client

REQUIRES_APPROVAL = {"delete_file", "send_email", "make_payment", "modify_database"}
CONFIDENCE_THRESHOLD = 0.7


def should_escalate(action: str, confidence: float) -> bool:
    """Return True if the action requires human approval."""
    return action in REQUIRES_APPROVAL or confidence < CONFIDENCE_THRESHOLD


def request_approval(action: str, context: str, get_input=input) -> bool:
    """Ask the human for approval. Returns True if approved."""
    print(f"\n[APPROVAL REQUIRED]")
    print(f"  Action:  {action}")
    print(f"  Context: {context}")
    response = get_input("  Approve? (y/n): ").strip().lower()
    return "y" in response


class HITLAgent:
    def __init__(self, get_input=input):
        self.get_input = get_input
        self.action_log = []

    def execute_action(self, action: str, context: str, confidence: float = 1.0) -> dict:
        """
        Execute an action with HITL escalation check.

        Returns {"action": str, "approved": bool, "executed": bool}
        """
        if should_escalate(action, confidence):
            approved = request_approval(action, context, self.get_input)
            executed = approved
        else:
            approved = True
            executed = True

        result = {
            "action": action,
            "approved": approved,
            "executed": executed,
        }
        self.action_log.append(result)
        return result
