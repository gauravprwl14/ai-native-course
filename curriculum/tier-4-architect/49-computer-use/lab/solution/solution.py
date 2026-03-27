"""Lab 49: Browser Agent (Computer Use Stub) — Reference Solution"""

from dataclasses import dataclass
from typing import Optional, Callable


@dataclass
class BrowserState:
    """Simplified browser state — text stands in for a real screenshot."""
    url: str
    title: str
    visible_text: str


@dataclass
class AgentAction:
    """An action the agent wants to execute."""
    action_type: str  # "click", "type", "navigate", "done", "error"
    target: Optional[str] = None
    text: Optional[str] = None
    reasoning: str = ""


@dataclass
class AgentStep:
    """One step in the agent's execution history."""
    state: BrowserState
    action: AgentAction
    step_number: int


def parse_action_from_llm_response(response: str) -> AgentAction:
    """Parse an LLM response string into an AgentAction."""
    try:
        parsed: dict[str, str] = {}
        for line in response.strip().split("\n"):
            if ": " in line:
                key, value = line.split(": ", 1)
                parsed[key.strip().upper()] = value.strip()

        action_type = parsed.get("ACTION", "").lower()
        if not action_type:
            return AgentAction(action_type="error", reasoning="parse failed: no ACTION field")

        return AgentAction(
            action_type=action_type,
            target=parsed.get("TARGET") or None,
            text=parsed.get("TEXT") or None,
            reasoning=parsed.get("REASONING", ""),
        )
    except Exception:
        return AgentAction(action_type="error", reasoning="parse failed")


def format_prompt(goal: str, state: BrowserState, history: list) -> str:
    """Format the agent prompt with goal, current state, and recent history."""
    recent_actions = [step.action.action_type for step in history[-3:]] if history else []
    history_str = ", ".join(recent_actions) if recent_actions else "none"

    return (
        f"Goal: {goal}\n\n"
        f"Current URL: {state.url}\n"
        f"Page title: {state.title}\n"
        f"Visible text (first 500 chars):\n{state.visible_text[:500]}\n\n"
        f"Recent actions (last 3): {history_str}\n\n"
        "Respond with the next action in this exact format:\n"
        "ACTION: click|type|navigate|done|error\n"
        "TARGET: <element description or URL>\n"
        "TEXT: <text to type, empty for non-type actions>\n"
        "REASONING: <why this action moves you toward the goal>"
    )


def run_agent(
    goal: str,
    initial_state: BrowserState,
    llm_caller: Callable[[str], str],
    action_executor: Callable[["BrowserState", AgentAction], "BrowserState"],
    max_steps: int = 10,
) -> list:
    """Run the browser agent loop until goal achieved or max_steps reached."""
    history: list[AgentStep] = []
    current_state = initial_state

    for step_number in range(max_steps):
        prompt = format_prompt(goal, current_state, history)
        response = llm_caller(prompt)
        action = parse_action_from_llm_response(response)

        step = AgentStep(
            state=current_state,
            action=action,
            step_number=step_number,
        )
        history.append(step)

        if action.action_type in ("done", "error"):
            break

        current_state = action_executor(current_state, action)

    return history


# ── Demo ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Simulate a 3-step agent run: navigate → click login → done
    step_responses = [
        "ACTION: navigate\nTARGET: http://example.com/login\nTEXT: \nREASONING: Go to login page",
        "ACTION: click\nTARGET: the Login button\nTEXT: \nREASONING: Submit credentials",
        "ACTION: done\nTARGET: \nTEXT: \nREASONING: Successfully logged in",
    ]
    response_iter = iter(step_responses)

    def mock_llm(prompt: str) -> str:
        return next(response_iter, "ACTION: error\nTARGET: \nTEXT: \nREASONING: no more responses")

    state_sequence = [
        BrowserState(url="http://example.com", title="Home", visible_text="Welcome to Example"),
        BrowserState(url="http://example.com/login", title="Login", visible_text="Username Password Login button"),
        BrowserState(url="http://example.com/dashboard", title="Dashboard", visible_text="Welcome, user!"),
    ]
    state_iter = iter(state_sequence[1:])

    def mock_executor(state: BrowserState, action: AgentAction) -> BrowserState:
        return next(state_iter, state)

    initial = state_sequence[0]
    steps = run_agent("Log into the website", initial, mock_llm, mock_executor, max_steps=10)

    for s in steps:
        print(f"Step {s.step_number}: [{s.action.action_type}] {s.action.target or ''} — {s.action.reasoning}")
