# Streaming Agent UX: Solving Perceived Latency

**Category:** system-design
**Difficulty:** Medium
**Key Concepts:** streaming, progressive disclosure, agent state visibility, TTFT vs perceived latency
**Time:** 25–35 min

---

## Problem Statement

You built an agent for a project management tool. It responds to requests like:

> "Summarize all overdue tasks, find the three team members with the most blockers, and send each of them a Slack message with a prioritized action plan."

The agent takes 15–25 seconds to complete:
- Tool call 1: Query tasks API (3–5s)
- Tool call 2: Query team member data (2–3s)
- LLM reasoning step (2–4s)
- Tool call 3: Generate personalized Slack messages (3–4s)
- Tool call 4: Send Slack messages (1–2s)
- LLM final response (2–4s)

**User behavior data:**
- 62% of users click away or hit refresh after 10 seconds
- Only 38% see the final response
- NPS for the feature is -12

A product manager says: "Just add a loading spinner."

An engineer says: "Stream the final LLM response so text appears faster."

**Both suggestions are wrong for this use case. Why? Design the correct UX pattern.**

---

## What Makes This Hard

Both common suggestions address the wrong part of the problem:

**The spinner:** Users don't drop off because they're missing a visual indicator. They drop off because they have no idea if the system is working. A spinner that runs for 25 seconds with no change is indistinguishable from a frozen page. It communicates "something is happening" but not "what, how far along, or how long."

**Streaming the final response:** Streaming helps when the bottleneck is token generation — when you want to show text appearing word by word. But in this pipeline, the LLM generation is only 2–4 seconds of a 15–25 second total. Streaming the last response does nothing for the first 13–21 seconds of silence. Token-by-token streaming of the final response would only save the user from waiting for the last 2–4 seconds — the part they would have waited for anyway if they hadn't already left.

The deeper insight: **perceived latency is not the same as actual latency.** Users tolerate waiting when they understand what is happening and can see forward progress. The same 20-second task feels fast with progress feedback and interminable with a static spinner.

This requires rethinking what information the agent emits during execution, not just at the end.

---

## Naive Approach

**Option A: Better spinner**
Add an animated spinner with text "Processing your request..." and a vague "This may take a moment."

**Why it fails:** Users still have no information about progress. The drop-off at 10 seconds continues because nothing changed about what they see during the 10-second window. The only thing a spinner communicates is "we know you're waiting." It does not communicate progress, stage, or time remaining.

**Option B: Stream the final LLM response**

```python
async def agent_handler(request):
    # ... 18 seconds of silent tool calls ...

    # Stream only the final response
    async for chunk in final_llm_response.stream():
        yield chunk
```

**Why it fails:** 18 seconds of silence followed by streaming text. The user already left at second 10. Streaming the last 4 seconds of a 22-second task is rearranging furniture while the house burns down. Time-to-first-token (TTFT) is still 18 seconds — the metric that drives drop-off.

**The shared failure mode:** Both approaches treat the agent as a black box with a visible output at the end. The fix requires making the agent a **transparent process** with observable intermediate states.

---

## Expert Approach

### Core Principle: Make the Agent Observable

Design the agent to emit structured events at every stage. The frontend subscribes to these events and renders them progressively. Users see the agent working in real time.

**Target experience:**
```
T+0.0s  ✓ Request received
T+0.5s  ⟳ Reading task database...
T+3.2s  ✓ Found 47 overdue tasks across 12 team members
T+3.5s  ⟳ Analyzing team workload distribution...
T+6.1s  ✓ Identified top 3 blocked team members: Sarah, Marcus, Priya
T+6.3s  ⟳ Drafting personalized action plans...
T+9.8s  ✓ Action plans ready — preparing Slack messages
T+10.0s ⟳ Sending messages...
T+11.4s ✓ All 3 messages sent
T+11.5s Generating summary...
T+13.2s [Full response streams in here, word by word]
```

The user sees forward progress at every step. They are never more than 3 seconds without new information. Drop-off rate plummets because users understand what is happening and when it will finish.

### Implementation

#### Step 1: Structured Agent Event Schema

```typescript
// Frontend receives these events via SSE
type AgentEvent =
  | { type: "tool_start"; tool_name: string; description: string; timestamp: number }
  | { type: "tool_result"; tool_name: string; summary: string; timestamp: number }
  | { type: "thinking"; content: string; timestamp: number }
  | { type: "output_start"; timestamp: number }
  | { type: "output_chunk"; content: string; timestamp: number }
  | { type: "output_end"; timestamp: number }
  | { type: "error"; message: string; recoverable: boolean; timestamp: number };
```

#### Step 2: Agent That Emits Events

```python
import asyncio
import json
from typing import AsyncGenerator
from datetime import datetime

class ObservableAgent:
    def __init__(self, llm_client, tools):
        self.llm = llm_client
        self.tools = {t.name: t for t in tools}

    async def run(self, user_query: str) -> AsyncGenerator[dict, None]:
        """Yield structured events throughout execution."""

        yield self._event("thinking", "Analyzing your request...")

        # Planning step
        plan = await self.llm.plan(user_query)

        for step in plan.steps:
            tool = self.tools[step.tool_name]

            # Emit: tool is starting
            yield self._event("tool_start",
                tool_name=step.tool_name,
                description=step.human_description,  # "Reading task database..."
            )

            # Execute the tool
            result = await tool.execute(step.parameters)

            # Emit: tool completed with a human-readable summary
            yield self._event("tool_result",
                tool_name=step.tool_name,
                summary=step.summarize_result(result),  # "Found 47 overdue tasks"
            )

            # If the result is interesting enough to show immediately, emit it
            if result.is_immediately_useful():
                yield self._event("thinking",
                    content=f"Key finding: {result.key_insight()}"
                )

        # Final LLM generation — stream token by token
        yield self._event("output_start")
        async for token in self.llm.stream_final_response(plan, results):
            yield self._event("output_chunk", content=token)
        yield self._event("output_end")

    def _event(self, event_type: str, **kwargs) -> dict:
        return {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
```

#### Step 3: SSE Endpoint (Server-Sent Events)

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.post("/agent/run")
async def run_agent(request: AgentRequest):
    agent = ObservableAgent(llm_client, tools)

    async def event_stream():
        async for event in agent.run(request.query):
            # SSE format: "data: {json}\n\n"
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
```

#### Step 4: Frontend Rendering

```typescript
// React component that renders agent events progressively
function AgentOutput({ query }: { query: string }) {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [outputText, setOutputText] = useState("");

  useEffect(() => {
    const source = new EventSource(`/agent/run?q=${encodeURIComponent(query)}`);

    source.onmessage = (e) => {
      const event: AgentEvent = JSON.parse(e.data);

      if (event.type === "output_chunk") {
        setOutputText(prev => prev + event.content);
      } else {
        setEvents(prev => [...prev, event]);
      }
    };

    return () => source.close();
  }, [query]);

  return (
    <div className="agent-output">
      {/* Progress timeline — visible during execution */}
      <div className="progress-timeline">
        {events.map((event, i) => (
          <AgentEventRow key={i} event={event} />
        ))}
      </div>

      {/* Streaming final output */}
      {outputText && (
        <div className="final-output">
          <TypewriterText text={outputText} />
        </div>
      )}
    </div>
  );
}

function AgentEventRow({ event }: { event: AgentEvent }) {
  const icons = {
    tool_start: "⟳",
    tool_result: "✓",
    thinking: "💭",
    output_start: "✍️",
  };

  if (event.type === "tool_start") {
    return (
      <div className="event-row running">
        <span className="icon spinning">⟳</span>
        <span>{event.description}</span>
      </div>
    );
  }

  if (event.type === "tool_result") {
    return (
      <div className="event-row complete">
        <span className="icon">✓</span>
        <span>{event.summary}</span>
      </div>
    );
  }

  return null;
}
```

#### Step 5: Show Partial Results Immediately

If an early tool result is independently useful, surface it before the full pipeline completes.

```python
# In the agent, after the task query returns
result = await tasks_tool.execute(parameters)

# If we found critical information, yield it immediately
# Don't wait for the full pipeline
if result.has_critical_blockers():
    yield self._event("thinking",
        content=f"Urgent: {result.critical_count} tasks are past deadline by > 2 weeks. "
                f"Flagging for priority action."
    )

# Continue running next tool in background while user reads this
```

### Design Principles for Agent UX

1. **TTFT is the primary latency metric, not total latency.** Time-to-first-token in the UI — the first moment anything meaningful appears — should be < 500ms. Every second of improvement here directly reduces drop-off.

2. **Communicate what, not just that.** "Loading..." conveys nothing. "Found 47 overdue tasks across 12 team members" is informative and builds confidence that the system is doing real work.

3. **Intermediate results reduce perceived wait.** Showing `"✓ Found top 3 blocked team members: Sarah, Marcus, Priya"` at T+6s gives the user something to think about while the agent finishes. This collapses the subjective wait time.

4. **Error transparency matters.** If a tool fails, emit an error event immediately and explain recovery. "Slack API rate limited — retrying in 3 seconds" is infinitely better than a 3-second black hole.

5. **Allow cancellation at any step.** Since the user can see exactly what step is running, they can meaningfully cancel mid-execution.

---

## Solution

<details>
<summary>Show Solution</summary>

### Full Architecture Diagram

```
User submits query
       |
       v
POST /agent/run
       |
       v
SSE connection established immediately  ← TTFT: < 100ms
       |
Agent begins execution
       |
       +-- tool_start event ─────────────→ Frontend: "⟳ Reading task database..."
       |
       +-- (DB query runs: 3–5s)
       |
       +-- tool_result event ────────────→ Frontend: "✓ Found 47 overdue tasks"
       |
       +-- tool_start event ─────────────→ Frontend: "⟳ Analyzing workload..."
       |
       +-- (LLM reasoning: 2–4s)
       |
       +-- tool_result event ────────────→ Frontend: "✓ Identified: Sarah, Marcus, Priya"
       |
       +-- tool_start event ─────────────→ Frontend: "⟳ Drafting action plans..."
       |
       +-- (message generation: 3–4s)
       |
       +-- tool_start event ─────────────→ Frontend: "⟳ Sending Slack messages..."
       |
       +-- (Slack API: 1–2s)
       |
       +-- tool_result event ────────────→ Frontend: "✓ 3 messages sent"
       |
       +-- output_start ─────────────────→ Frontend: typing indicator
       |
       +-- output_chunk (streaming) ─────→ Frontend: text appears word by word
       |
       +-- output_end ───────────────────→ Frontend: done
```

### Measuring Impact

Before/after metrics to track:

| Metric | Before (spinner) | Target (observable agent) |
|---|---|---|
| Drop-off at 10s | 62% | < 20% |
| Task completion rate | 38% | > 80% |
| NPS | -12 | > +20 |
| "Something went wrong?" support tickets | High | Near zero |

Track TTFT (time to first meaningful UI update) as a standalone SLO. Target: < 500ms.

</details>

---

## Interview Version

"You have an agent that takes 20 seconds. Users drop off after 10 seconds. The PM says add a spinner, the engineer says stream the response. Why are both wrong, and what's the right answer?"

**Diagnose first:**
"The spinner fails because it communicates existence, not progress. Streaming the final response fails because it only helps with the last 2–4 seconds of a 20-second pipeline. The drop-off happens in seconds 10–15, not in seconds 18–20."

**State the root cause:**
"Users don't have a latency problem — they have an uncertainty problem. They don't know if the system is working, what it's doing, or when it will finish."

**Draw the solution:**
```
T+0s  ✓ Request received
T+0.5 ⟳ Reading task database...    ← user sees this
T+3s  ✓ Found 47 overdue tasks      ← user reads this, learns something
T+3s  ⟳ Analyzing workload...       ← user stays engaged
...
T+13s [text streams in word by word]
```

**Implement with SSE:**
"Server-Sent Events from the agent, structured event schema, frontend renders each event type differently. Streaming happens at every step, not just the last response."

---

## Follow-up Questions

1. Your agent sometimes encounters tool failures mid-execution — the Slack API times out, or a database query returns an error. The agent retries internally, which adds 3–5 seconds. How do you communicate this to the user in a way that maintains trust rather than creating anxiety? What is the right level of detail to expose?
2. You implement the progressive disclosure pattern and drop-off falls to 18%. But you notice that users are now reading the intermediate steps and making decisions before the agent finishes — for example, seeing "Found 3 blocked team members" and immediately messaging them manually, then the agent sends duplicate messages. How do you handle user interactivity during agent execution?
3. The agent timeline events contain business logic details: team member names, task counts, internal project names. A user shares a screenshot of the progress UI on Twitter, inadvertently leaking organizational data. How do you redesign the event schema and frontend rendering to allow transparency without exposing sensitive intermediate data?
