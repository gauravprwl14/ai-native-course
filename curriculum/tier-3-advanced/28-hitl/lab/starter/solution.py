"""Lab 28: Human-in-the-Loop (HITL)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))
from utils import get_anthropic_client

REQUIRES_APPROVAL = {"delete_file", "send_email", "make_payment", "modify_database"}
CONFIDENCE_THRESHOLD = 0.7


def should_escalate(action: str, confidence: float) -> bool:
    """
    Return True if the action requires human approval.

    Escalate if:
    - action is in REQUIRES_APPROVAL (high-risk allowlist), OR
    - confidence is below CONFIDENCE_THRESHOLD

    # TODO: return action in REQUIRES_APPROVAL or confidence < CONFIDENCE_THRESHOLD
    """
    raise NotImplementedError("Implement should_escalate")


def request_approval(action: str, context: str, get_input=input) -> bool:
    """
    Ask the human for approval. Returns True if approved.

    Steps:
    1. Print the action and context clearly
    2. Call get_input() to get the human's response (use get_input, not input directly)
    3. Return True if the response contains "y" (case-insensitive)

    # TODO: print action + context, call get_input(), return "y" in response.lower()
    """
    raise NotImplementedError("Implement request_approval")


class HITLAgent:
    def __init__(self, get_input=input):
        self.get_input = get_input
        self.action_log = []

    def execute_action(self, action: str, context: str, confidence: float = 1.0) -> dict:
        """
        Execute an action with HITL escalation check.

        Returns:
            {
                "action": str,
                "approved": bool,  # True if action was approved (or not escalated)
                "executed": bool,  # True if action was actually executed
            }

        Steps:
        1. Check should_escalate(action, confidence)
        2. If escalation needed: call request_approval(action, context, self.get_input)
           - If approved: mark executed=True, approved=True
           - If rejected: mark executed=False, approved=False
        3. If no escalation needed: mark executed=True, approved=True (auto-approved)
        4. Append the result dict to self.action_log
        5. Return the result dict

        # TODO: implement escalation check + approval + logging
        """
        raise NotImplementedError("Implement execute_action")
