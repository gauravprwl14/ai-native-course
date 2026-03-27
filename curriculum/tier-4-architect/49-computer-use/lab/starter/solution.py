"""Lab 49: Browser Agent (Computer Use Stub) — Starter File

Implement a simplified browser agent that runs the screenshot-action loop
using text descriptions instead of real screenshots (for testability).
"""

from dataclasses import dataclass
from typing import Optional, Callable


@dataclass
class BrowserState:
    """Simplified browser state — text stands in for a real screenshot."""
    url: str
    title: str
    visible_text: str  # simplified "screenshot" as text


@dataclass
class AgentAction:
    """An action the agent wants to execute."""
    action_type: str  # "click", "type", "navigate", "done", "error"
    target: Optional[str] = None  # element description or URL
    text: Optional[str] = None    # for type actions
    reasoning: str = ""


@dataclass
class AgentStep:
    """One step in the agent's execution history."""
    state: BrowserState
    action: AgentAction
    step_number: int


def parse_action_from_llm_response(response: str) -> AgentAction:
    """Parse an LLM response string into an AgentAction.

    Expected format:
        ACTION: click|type|navigate|done|error
        TARGET: <element description or URL>
        TEXT: <text to type (for type action, empty otherwise)>
        REASONING: <why this action>

    Steps:
    1. Split the response into lines
    2. For each line, split on ': ' (first occurrence only) to get key and value
    3. Collect ACTION, TARGET, TEXT, REASONING into a dict
    4. Build and return AgentAction from the collected values
    5. If ACTION is missing or parsing throws an exception,
       return AgentAction(action_type="error", reasoning="parse failed")
    """
    # TODO: Parse ACTION, TARGET, TEXT, REASONING from response lines
    # TODO: Return AgentAction with parsed values
    # TODO: Default to error action if parsing fails or ACTION is missing
    pass


def format_prompt(goal: str, state: BrowserState, history: list) -> str:
    """Format the agent prompt with goal, current state, and recent history.

    The prompt must include:
    1. A 'Goal: {goal}' line
    2. Current URL: {state.url}
    3. Page title: {state.title}
    4. Visible text (first 500 characters of state.visible_text)
    5. Last 3 action types from history
       (if history is empty, write 'none')
    6. Instructions to respond in ACTION/TARGET/TEXT/REASONING format,
       listing valid action types: click, type, navigate, done, error

    Steps:
    1. Build a list of prompt lines
    2. For history, extract the last 3 AgentStep items (or fewer if history is shorter)
       and get each step's action.action_type
    3. Join everything into a single string and return it
    """
    # TODO: Build prompt with goal, state, recent history, and format instructions
    pass


def run_agent(
    goal: str,
    initial_state: BrowserState,
    llm_caller: Callable[[str], str],
    action_executor: Callable[["BrowserState", AgentAction], "BrowserState"],
    max_steps: int = 10,
) -> list:
    """Run the browser agent loop until goal achieved or max_steps reached.

    Args:
        goal: The natural-language goal for the agent
        initial_state: Starting BrowserState
        llm_caller: callable(prompt: str) -> str
            Called with the formatted prompt; returns the LLM response string
        action_executor: callable(state: BrowserState, action: AgentAction) -> BrowserState
            Executes the action and returns the new browser state
        max_steps: Maximum number of steps before stopping

    Returns:
        list of AgentStep objects in execution order

    Steps:
    1. history = []
    2. current_state = initial_state
    3. Loop up to max_steps:
       a. prompt = format_prompt(goal, current_state, history)
       b. response = llm_caller(prompt)
       c. action = parse_action_from_llm_response(response)
       d. step = AgentStep(state=current_state, action=action, step_number=<loop index>)
       e. history.append(step)
       f. If action.action_type in ("done", "error"): break
       g. current_state = action_executor(current_state, action)
    4. Return history
    """
    # TODO: Initialize history and current_state
    # TODO: Loop up to max_steps:
    #   a. format prompt
    #   b. call llm_caller
    #   c. parse action
    #   d. create and append AgentStep
    #   e. break if done or error
    #   f. execute action to get new state
    # TODO: Return history
    pass
