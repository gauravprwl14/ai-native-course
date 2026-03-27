# Lab 49 — Browser Agent (Computer Use Stub)

## Goal

Build a simplified browser agent that runs the screenshot-action loop. Because real computer use requires the Anthropic API and a sandbox, this lab uses text descriptions as the "screenshot" and mock callables for the LLM and action executor. The agent logic is real and fully testable.

## Background

Computer use agents follow the loop:
1. Observe current state (screenshot / page text)
2. Ask LLM: "Given goal X and current state Y, what should I do next?"
3. Parse the LLM's structured action response
4. Execute the action
5. Repeat until done or max steps reached

## What to Implement

### Data classes

**`BrowserState`**: url, title, visible_text (the simplified "screenshot")

**`AgentAction`**: action_type (click/type/navigate/done/error), target, text, reasoning

**`AgentStep`**: state (BrowserState), action (AgentAction), step_number

### `parse_action_from_llm_response(response: str) -> AgentAction`

Parse the LLM response in this format:
```
ACTION: click
TARGET: the Login button
TEXT: (empty for click)
REASONING: Login button visible top-right
```

- Extract ACTION, TARGET, TEXT, REASONING by splitting each line on `": "` (first occurrence)
- Return `AgentAction` with parsed values
- On any parse failure: return `AgentAction(action_type="error", reasoning="parse failed")`

### `format_prompt(goal, state, history) -> str`

Build the agent prompt containing:
- The goal
- Current URL, title, and first 500 chars of visible_text
- Last 3 action types from history (or "none")
- Instructions: respond with ACTION/TARGET/TEXT/REASONING; valid action_types: click, type, navigate, done, error

### `run_agent(goal, initial_state, llm_caller, action_executor, max_steps=10) -> list[AgentStep]`

The main agent loop:
1. history = [], current_state = initial_state
2. For up to max_steps:
   - format_prompt → llm_caller → parse_action
   - Append AgentStep to history
   - If action_type == "done" or "error": break
   - action_executor(current_state, action) → new current_state
3. Return history

## Test

```bash
cd curriculum/tier-4-architect/49-computer-use/lab
pytest tests/ -v
```

## No Real API Calls

All tests use `unittest.mock` — `llm_caller` and `action_executor` are mock functions. The tests verify the loop logic, prompt content, and action parsing without any network calls.
