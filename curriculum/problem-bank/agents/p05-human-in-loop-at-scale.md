# Human-in-the-Loop at Scale

**Category:** agents
**Difficulty:** Expert
**Key Concepts:** HITL architecture, work queue, escalation, SLA, async workflows
**Time:** 40–45 min

---

## Problem Statement

Your agent handles 500 requests/day and performs "high-stakes" actions: sending emails, making purchases, initiating refunds. You added a human review step — a reviewer must approve or reject within 5 minutes before the agent proceeds.

Current setup: one reviewer watches a shared inbox. The approval time is meeting SLA on slow days. On busy days:

- Reviewer is overwhelmed (10 approvals/hour during peaks)
- Requests wait 8–15 minutes (SLA breach)
- Reviewer makes rushed decisions with incomplete context

Your team has 3 reviewers available. Redesign the HITL system to:
- Handle 500 requests/day with 3 reviewers
- Guarantee no request waits longer than 10 minutes
- Prevent duplicate approvals (two reviewers approving the same request)
- Provide enough context for reviewers to make decisions confidently in < 60 seconds

---

## What Makes This Hard

The naive mental model — "more reviewers = more capacity" — is correct but insufficient. The hard part is that **synchronous HITL doesn't scale**:

- Agent blocks a thread/process waiting for approval
- At 500 requests/day (≈21/hour average, up to 60/hour peak), blocking threads exhaust your connection pool
- A shared inbox creates race conditions: two reviewers click "approve" on the same request

The deeper architectural challenge: you need to design three separate systems that work together:

1. **Queue** — receives approval requests, prevents duplicates, tracks SLA timers
2. **Router** — assigns requests to reviewers based on type and workload
3. **Escalation engine** — monitors SLA timers and escalates before breach

And a non-obvious design choice: **what happens when no human approves in time?** You need a principled auto-resolution policy that isn't just "always reject" (too conservative) or "always approve" (no point having HITL). The answer depends on risk level — you need to classify action risk and apply different default policies.

---

## Naive Approach

**Three reviewers each monitor a shared inbox. First one to reply wins.**

```python
# Agent side: synchronous, blocking
async def agent_action_with_review(action: AgentAction) -> bool:
    await send_email_to_reviewers(action)
    # Block until a reviewer replies
    approved = await wait_for_email_reply(timeout_seconds=300)
    return approved

# Reviewer side: email inbox
# No routing, no deduplication, no SLA tracking
```

**Why this fails:**

1. **Race conditions.** Two reviewers approve the same request. The action executes twice — double purchase, duplicate email sent.
2. **No SLA tracking.** No system knows which requests are approaching the 10-minute deadline. The first request submitted might be the last reviewed.
3. **No routing.** A finance-trained reviewer approves marketing emails; a comms-trained reviewer approves financial transactions. Wrong expertise applied.
4. **Agent threads blocked.** 60 concurrent approval-pending requests = 60 blocked threads. This exhausts your thread pool before you hit the reviewer capacity problem.
5. **Context collapse.** The email contains the action and nothing else. The reviewer has to remember or look up: what's this agent trying to do? Why? What's the risk? A rushed reviewer approves blindly.
6. **No audit trail.** You have no record of who approved what, how long it took, or whether the approval was within the SLA.

---

## Expert Approach

**Five components:**

**Component 1: Async task queue (agent side)**

The agent never blocks. It submits an approval request to a queue and gets a `job_id` back immediately. It then polls (or receives a webhook) for the decision.

```
Agent → POST /approvals → {job_id: "apr-8291"} → continue doing other work
Agent → GET /approvals/apr-8291 → {status: "pending"} | {status: "approved"} | {status: "rejected"}
```

The queue owns deduplication. If two reviewers try to claim the same request, the queue rejects the second claim.

**Component 2: Reviewer assignment with skill routing**

Each approval request has a `action_type`. Route by type:
- `financial` actions → finance-trained reviewer
- `email` / `communication` actions → comms reviewer
- `data_access` actions → any available reviewer

Use round-robin within a skill group. Track each reviewer's pending count — don't assign to a reviewer who already has 5 pending items.

**Component 3: SLA timer with escalation**

When a request enters the queue, start a timer:
- `T+0`: assigned to reviewer
- `T+8min`: not yet reviewed → escalate to senior reviewer + Slack alert
- `T+10min`: SLA breach → auto-resolve based on risk classification

The timer must be durable (survive service restarts). Use Redis sorted sets (score = expiry timestamp) or a DB with a background worker.

**Component 4: Risk-based auto-resolution**

When `T+10min` is hit and no human has reviewed:
```
LOW risk (amount < $100, email to known contact): auto-APPROVE
HIGH risk (amount > $100, new contact, irreversible action): auto-REJECT
ESCALATED (already sent to senior reviewer): extend by 5 minutes
```

Auto-resolution is not a failure state — it's a designed fallback. The policy is explicit, audited, and reviewed quarterly.

**Component 5: Reviewer dashboard with decisioning context**

The dashboard shows each reviewer their queue, prioritized by SLA urgency. Each item displays:
- The proposed action (what exactly will happen)
- The agent's reasoning (why it decided this action was appropriate)
- The risk classification and estimated impact
- A one-line risk summary
- Approve / Reject buttons (single click, deduplication enforced server-side)

Context collapses decision time from 2 minutes to 30 seconds per item.

---

## Solution

<details>
<summary>Show Solution</summary>

```python
import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import redis.asyncio as redis

# --- Data model ---

class ActionType(str, Enum):
    FINANCIAL = "financial"
    EMAIL = "email"
    DATA_ACCESS = "data_access"
    PURCHASE = "purchase"

class RiskLevel(str, Enum):
    LOW = "low"
    HIGH = "high"

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"
    AUTO_REJECTED = "auto_rejected"
    ESCALATED = "escalated"

@dataclass
class ApprovalRequest:
    job_id: str
    action_type: ActionType
    action_description: str   # "Send email to john@acme.com with subject: Q4 Report"
    agent_reasoning: str      # "User requested outreach to this contact based on..."
    risk_level: RiskLevel
    risk_summary: str         # "Low-risk: known contact, routine communication"
    estimated_impact: str     # "$0 / 1 email sent to 1 recipient"
    submitted_at: float       # Unix timestamp
    sla_deadline: float       # submitted_at + 600 (10 min)
    status: ApprovalStatus = ApprovalStatus.PENDING
    assigned_reviewer_id: Optional[str] = None
    decision_at: Optional[float] = None
    decision_by: Optional[str] = None
    auto_resolve_policy: str = ""  # "approve_if_low_risk" | "reject_if_high_risk"

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "action_type": self.action_type.value,
            "action_description": self.action_description,
            "agent_reasoning": self.agent_reasoning,
            "risk_level": self.risk_level.value,
            "risk_summary": self.risk_summary,
            "estimated_impact": self.estimated_impact,
            "submitted_at": self.submitted_at,
            "sla_deadline": self.sla_deadline,
            "status": self.status.value,
            "assigned_reviewer_id": self.assigned_reviewer_id,
            "decision_at": self.decision_at,
            "decision_by": self.decision_by,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ApprovalRequest":
        return cls(
            job_id=d["job_id"],
            action_type=ActionType(d["action_type"]),
            action_description=d["action_description"],
            agent_reasoning=d["agent_reasoning"],
            risk_level=RiskLevel(d["risk_level"]),
            risk_summary=d["risk_summary"],
            estimated_impact=d["estimated_impact"],
            submitted_at=d["submitted_at"],
            sla_deadline=d["sla_deadline"],
            status=ApprovalStatus(d["status"]),
            assigned_reviewer_id=d.get("assigned_reviewer_id"),
            decision_at=d.get("decision_at"),
            decision_by=d.get("decision_by"),
        )


# --- Reviewer registry ---

@dataclass
class Reviewer:
    reviewer_id: str
    name: str
    skills: list[ActionType]  # Which action types this reviewer handles
    max_concurrent: int = 5   # Max pending items at once


REVIEWERS = [
    Reviewer("rev-finance", "Alice", [ActionType.FINANCIAL, ActionType.PURCHASE]),
    Reviewer("rev-comms", "Bob", [ActionType.EMAIL]),
    Reviewer("rev-general", "Carol", [ActionType.FINANCIAL, ActionType.EMAIL,
                                       ActionType.DATA_ACCESS, ActionType.PURCHASE]),
]


# --- HITL Queue (Redis-backed) ---

class HITLQueue:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.SLA_SECONDS = 600      # 10 minutes
        self.ESCALATE_SECONDS = 480 # 8 minutes

    async def submit(self, request: ApprovalRequest) -> str:
        """Submit an approval request. Returns job_id."""
        # Store the request
        key = f"approval:{request.job_id}"
        await self.redis.setex(
            key,
            3600,  # Keep for 1 hour
            json.dumps(request.to_dict())
        )

        # Add to SLA timer sorted set (score = deadline timestamp)
        await self.redis.zadd("sla:timers", {request.job_id: request.sla_deadline})

        # Route to a reviewer
        reviewer = await self._route_to_reviewer(request)
        if reviewer:
            await self._assign(request.job_id, reviewer.reviewer_id)

        return request.job_id

    async def _route_to_reviewer(self, request: ApprovalRequest) -> Optional[Reviewer]:
        """Find the best available reviewer for this action type."""
        eligible = [r for r in REVIEWERS if request.action_type in r.skills]
        if not eligible:
            eligible = REVIEWERS  # Fallback to any reviewer

        # Pick the reviewer with the fewest pending items
        best_reviewer = None
        min_pending = float("inf")

        for reviewer in eligible:
            pending_count = await self.redis.llen(f"reviewer:{reviewer.reviewer_id}:queue")
            if pending_count < reviewer.max_concurrent and pending_count < min_pending:
                min_pending = pending_count
                best_reviewer = reviewer

        return best_reviewer

    async def _assign(self, job_id: str, reviewer_id: str):
        """Assign a job to a reviewer (deduplication enforced)."""
        # Use SET NX (set if not exists) to prevent duplicate assignments
        assigned = await self.redis.set(
            f"assignment:{job_id}",
            reviewer_id,
            nx=True,  # Only set if key doesn't exist
            ex=3600
        )
        if not assigned:
            return  # Already assigned — deduplication working

        # Add to reviewer's queue
        await self.redis.rpush(f"reviewer:{reviewer_id}:queue", job_id)

        # Update request status
        await self._update_status(job_id, ApprovalStatus.ASSIGNED, reviewer_id=reviewer_id)

    async def get_status(self, job_id: str) -> Optional[ApprovalRequest]:
        """Get the current status of an approval request."""
        key = f"approval:{job_id}"
        data = await self.redis.get(key)
        if not data:
            return None
        return ApprovalRequest.from_dict(json.loads(data))

    async def reviewer_decide(self, job_id: str, reviewer_id: str, approved: bool) -> bool:
        """
        Reviewer makes a decision. Returns True if decision was accepted.
        Returns False if request was already decided (prevents double-approvals).
        """
        # Atomic: only allow one decision per job_id
        decided = await self.redis.set(
            f"decision:{job_id}",
            "1",
            nx=True,  # Only set if not already decided
            ex=3600
        )
        if not decided:
            return False  # Already decided — second reviewer rejected

        status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        await self._update_status(
            job_id, status,
            decision_at=time.time(),
            decision_by=reviewer_id
        )

        # Remove from reviewer's queue
        await self.redis.lrem(f"reviewer:{reviewer_id}:queue", 1, job_id)
        # Remove from SLA timer
        await self.redis.zrem("sla:timers", job_id)

        return True

    async def _update_status(
        self,
        job_id: str,
        status: ApprovalStatus,
        reviewer_id: str = None,
        decision_at: float = None,
        decision_by: str = None,
    ):
        key = f"approval:{job_id}"
        data = await self.redis.get(key)
        if not data:
            return
        request = ApprovalRequest.from_dict(json.loads(data))
        request.status = status
        if reviewer_id:
            request.assigned_reviewer_id = reviewer_id
        if decision_at:
            request.decision_at = decision_at
        if decision_by:
            request.decision_by = decision_by
        await self.redis.setex(key, 3600, json.dumps(request.to_dict()))

    async def get_reviewer_queue(self, reviewer_id: str) -> list[ApprovalRequest]:
        """Get all pending items for a reviewer, sorted by SLA urgency."""
        job_ids = await self.redis.lrange(f"reviewer:{reviewer_id}:queue", 0, -1)
        requests = []
        for job_id_bytes in job_ids:
            job_id = job_id_bytes.decode() if isinstance(job_id_bytes, bytes) else job_id_bytes
            req = await self.get_status(job_id)
            if req and req.status in (ApprovalStatus.ASSIGNED, ApprovalStatus.ESCALATED):
                requests.append(req)
        # Sort by SLA deadline (most urgent first)
        return sorted(requests, key=lambda r: r.sla_deadline)


# --- SLA monitor (background worker) ---

class SLAMonitor:
    def __init__(self, queue: HITLQueue):
        self.queue = queue
        self.running = False

    async def run(self):
        """Background loop: check SLA timers every 30 seconds."""
        self.running = True
        while self.running:
            await self._check_timers()
            await asyncio.sleep(30)

    async def _check_timers(self):
        now = time.time()
        escalate_before = now + (self.queue.SLA_SECONDS - self.queue.ESCALATE_SECONDS)

        # Find requests approaching escalation threshold
        approaching = await self.queue.redis.zrangebyscore(
            "sla:timers",
            "-inf",
            now + 120  # Requests expiring in next 2 minutes
        )

        for job_id_bytes in approaching:
            job_id = job_id_bytes.decode() if isinstance(job_id_bytes, bytes) else job_id_bytes
            req = await self.queue.get_status(job_id)
            if not req:
                continue

            time_remaining = req.sla_deadline - now

            if time_remaining <= 0:
                # SLA breached — auto-resolve
                await self._auto_resolve(req)
            elif time_remaining <= 120 and req.status == ApprovalStatus.ASSIGNED:
                # 2 minutes remaining — escalate
                await self._escalate(req)

    async def _escalate(self, request: ApprovalRequest):
        """Escalate to senior reviewer + alert."""
        await self.queue._update_status(request.job_id, ApprovalStatus.ESCALATED)
        # In production: send Slack alert, assign to senior reviewer
        print(
            f"[ESCALATION] job_id={request.job_id} "
            f"action={request.action_description[:50]} "
            f"time_remaining={int(request.sla_deadline - time.time())}s"
        )

    async def _auto_resolve(self, request: ApprovalRequest):
        """Auto-resolve based on risk level."""
        if request.risk_level == RiskLevel.LOW:
            status = ApprovalStatus.AUTO_APPROVED
            outcome = "AUTO-APPROVED (low risk, SLA expired)"
        else:
            status = ApprovalStatus.AUTO_REJECTED
            outcome = "AUTO-REJECTED (high risk, SLA expired)"

        # Use the decision lock to prevent race with a human decision
        decided = await self.queue.redis.set(
            f"decision:{request.job_id}",
            "auto",
            nx=True,
            ex=3600
        )
        if not decided:
            return  # A human already decided — don't override

        await self.queue._update_status(
            request.job_id,
            status,
            decision_at=time.time(),
            decision_by="auto_resolver"
        )
        await self.queue.redis.zrem("sla:timers", request.job_id)

        # In production: write to audit log
        print(f"[AUTO-RESOLVE] job_id={request.job_id} outcome={outcome}")


# --- Agent side: async approval request ---

async def request_approval_async(
    queue: HITLQueue,
    action_type: ActionType,
    action_description: str,
    agent_reasoning: str,
    risk_level: RiskLevel,
    risk_summary: str,
    estimated_impact: str,
    poll_interval: float = 5.0,
    max_wait: float = 660.0,  # Slightly beyond SLA — auto-resolve will have fired
) -> tuple[bool, str]:
    """
    Submit an approval request and poll for the decision.
    The agent does NOT block a thread — it awaits asynchronously.
    Returns (approved: bool, decision_reason: str).
    """
    now = time.time()
    request = ApprovalRequest(
        job_id=f"apr-{uuid.uuid4().hex[:8]}",
        action_type=action_type,
        action_description=action_description,
        agent_reasoning=agent_reasoning,
        risk_level=risk_level,
        risk_summary=risk_summary,
        estimated_impact=estimated_impact,
        submitted_at=now,
        sla_deadline=now + queue.SLA_SECONDS,
    )

    job_id = await queue.submit(request)
    start_time = time.time()

    while time.time() - start_time < max_wait:
        await asyncio.sleep(poll_interval)
        status_req = await queue.get_status(job_id)

        if status_req is None:
            return False, "Request not found"

        if status_req.status == ApprovalStatus.APPROVED:
            return True, f"Approved by {status_req.decision_by}"
        elif status_req.status == ApprovalStatus.AUTO_APPROVED:
            return True, "Auto-approved (low risk, SLA expired)"
        elif status_req.status in (ApprovalStatus.REJECTED, ApprovalStatus.AUTO_REJECTED):
            return False, f"Rejected by {status_req.decision_by or 'auto_resolver'}"

    return False, "Timed out waiting for approval decision"


if __name__ == "__main__":
    async def demo():
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        queue = HITLQueue(r)

        # Start SLA monitor in background
        monitor = SLAMonitor(queue)
        monitor_task = asyncio.create_task(monitor.run())

        # Simulate an agent requesting approval
        approved, reason = await request_approval_async(
            queue=queue,
            action_type=ActionType.EMAIL,
            action_description="Send email to john@acme.com with subject: Q4 Report Summary",
            agent_reasoning="User requested to follow up with John on the Q4 analysis we completed.",
            risk_level=RiskLevel.LOW,
            risk_summary="Low-risk: known contact, no sensitive data, routine follow-up",
            estimated_impact="1 email sent to 1 recipient",
        )
        print(f"Approval result: {'APPROVED' if approved else 'REJECTED'} — {reason}")

        monitor.running = False
        monitor_task.cancel()
        await r.aclose()

    asyncio.run(demo())
```

</details>

---

## Interview Version

**Opening (20 seconds):** "The problem has two parts: throughput (3 reviewers, 500 requests/day) and correctness (no duplicate approvals, guaranteed SLA). A shared inbox solves neither. You need an async task queue with routing, SLA timers, and deduplication — all separate concerns."

**Draw the architecture:**
```
Agent
  └─ POST /approvals → {job_id} (non-blocking)
  └─ poll GET /approvals/{job_id} every 5s

Queue (Redis)
  ├─ Store request (key: approval:{job_id})
  ├─ Route to reviewer (skill match + min-load)
  ├─ SLA timer (sorted set, score = deadline)
  └─ Decision lock (SET NX prevents duplicate approvals)

SLA Monitor (background worker, every 30s)
  ├─ T+8min: escalate + Slack alert
  └─ T+10min: auto-resolve by risk level

Reviewer Dashboard
  └─ Queue sorted by SLA urgency
  └─ Context: action + reasoning + risk + impact
  └─ One-click approve/reject
```

**The non-obvious detail:** "The `SET NX` (set if not exists) on the decision key is what prevents race conditions. Two reviewers can both click Approve simultaneously — only the first write wins, the second gets a rejection from the database. No application-level locking needed."

**Risk-based auto-resolution:** "Defaulting to 'always reject on timeout' sounds safe but causes agent failure modes at scale. A principled risk classification (low = auto-approve, high = auto-reject) lets you define explicit failure modes. Every auto-resolution goes to the audit log and is reviewed in weekly ops review."

---

## Follow-up Questions

1. Your SLA monitor runs every 30 seconds. A request submitted at T=0 might not be checked until T=29. For a 10-minute SLA, that's a 5% margin. How would you design a more precise timer that fires within 5 seconds of the SLA deadline without polling every second?
2. A reviewer approves a request, then 30 seconds later says "wait, I made an error — please reverse that decision." The action has already executed. How would you build a "decision undo" window into the architecture, and what is the maximum safe undo window for each action type?
3. Your routing sends `financial` actions to Alice. Alice goes on vacation for a week. How does the routing system detect and adapt to reviewer unavailability, and what SLA guarantees can you make during reduced staffing?
