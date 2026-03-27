# Multi-Model Agent System Design

**Category:** system-design
**Difficulty:** Hard
**Key Concepts:** model cascade, task routing, parallel execution, cost optimization
**Time:** 35–45 min

---

## Problem Statement

You are designing an AI agent system for a data analysis platform. Users can ask questions like:

> "Analyze our Q3 sales data and identify the top 3 underperforming regions. Create a chart comparing them to Q2."

The system must:
1. Understand and decompose the request into subtasks
2. Query a PostgreSQL database containing 3 years of sales data
3. Execute Python code to calculate statistics and generate a chart
4. Return the chart, a written analysis, and 3 recommended actions

**Constraints:**
- Latency target: p50 < 8 seconds, p95 < 15 seconds
- Cost target: < $0.05 per query
- The platform has 5,000 active users, 2,000 queries/day
- Database contains 200 tables, schema changes weekly
- Quality bar: the SQL must be correct on the first try > 90% of the time

**Design the agent architecture. Focus on model selection and routing. Show the cost math.**

---

## What Makes This Hard

The hard part is not "which models exist" — it is understanding that **different steps in an agent pipeline have radically different cognitive requirements**, and pricing LLM calls accordingly.

Using one model for everything is not just expensive — it is also slower, because more capable models have higher latency. Using a cheap model for everything sacrifices the quality steps that actually need reasoning.

The second challenge: many engineers default to sequential execution because it feels safer. But in a pipeline with 4+ steps, there are almost always steps that can run in parallel — and parallelism is the primary lever for hitting 8-second p50 latency.

The non-obvious trap: the SQL generation step looks like it needs a smart model ("databases are complex") but actually benefits more from **good prompting + schema context** than raw model intelligence. A well-constructed few-shot SQL prompt on Haiku outperforms a lazy GPT-4o call in both cost and speed.

---

## Naive Approach

**Use GPT-4o (or Claude Sonnet) for every step in the pipeline.**

```python
async def analyze_query(user_query: str) -> dict:
    # Step 1: Plan
    plan = await sonnet.chat("Decompose this task: " + user_query)

    # Step 2: SQL
    sql = await sonnet.chat("Write SQL for: " + user_query)

    # Step 3: Execute and get data
    data = execute_sql(sql)

    # Step 4: Python code for chart
    code = await sonnet.chat("Write Python chart code for: " + str(data))

    # Step 5: Written analysis
    analysis = await sonnet.chat("Analyze this data: " + str(data))

    return {"chart": run_code(code), "analysis": analysis}
```

**Why it fails:**

1. **Cost:** 5 Sonnet calls at ~$0.01/call = $0.05/query. At 2,000 queries/day, this is $100/day = $3,000/month just in LLM API costs. Some queries will easily exceed $0.05 with long contexts.
2. **Latency:** Each Sonnet call takes 1–3 seconds. Five sequential calls = 5–15 seconds. You've already blown the p95 budget before adding DB query time.
3. **Overcapability:** SQL generation is a structured, deterministic task given a clear schema. Haiku with a good prompt is equivalent to Sonnet for SQL. Using Sonnet here is money spent on intelligence you don't need.
4. **No parallelism:** The SQL query result and the chart visualization plan are independent. Both can start simultaneously, but sequential design forces them to wait for each other.

---

## Expert Approach

### Mental Model: Map Cognitive Load to Model Tier

Not all steps require the same intelligence. Match the model to the minimum necessary capability for each step.

| Step | Cognitive Requirement | Correct Model | Rationale |
|---|---|---|---|
| Task decomposition / planning | High — ambiguous intent, multi-step reasoning | Sonnet | This is the highest-value use of a capable model. Planning errors cascade. |
| SQL generation | Medium — structured, rule-bound, schema-dependent | Haiku + few-shot | SQL is mechanical given schema. Few-shot examples dominate model intelligence. |
| Data analysis | Medium-High — interpret numbers, identify patterns | Sonnet | Requires genuine reasoning over results. |
| Chart description / labels | Low — templated output | Haiku | Filling a template; minimal reasoning needed. |
| Recommendation generation | High — synthesis + strategic thinking | Sonnet | This is what the user cares most about. |

### Execution Timeline: Identify Parallelism

```
Sequential (naive):
[Plan] → [SQL] → [DB Query] → [Code Gen] → [Execute Code] → [Analysis] → [Recommend]
  2s       2s        3s           2s              1s             2s           2s   = 14s

Parallel (optimized):
[Plan]
   ├─→ [SQL Gen (Haiku)] → [DB Query] → [Analysis (Sonnet)] → [Recommend (Sonnet)]
   └─→ [Viz Plan (Haiku)]                    ↗
                           [Data] ──────────
                                            ↘
                           [Code Gen (Haiku)] → [Execute Code]
                                                              ↘
                                                    [Final Assembly + Recommend]
  ~1s      ~0.5s            ~3s                  ~2s               ~2s   = ~8.5s
```

SQL generation and visualization planning start simultaneously after the initial plan. Code generation runs on the retrieved data in parallel with the analysis.

### Implementation

```python
import asyncio
from anthropic import AsyncAnthropic

client = AsyncAnthropic()

async def plan_task(user_query: str, schema_summary: str) -> dict:
    """Use Sonnet for planning — highest value use of expensive model."""
    response = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"""Decompose this data analysis request into a structured plan.
Return JSON with: sql_goal, viz_goal, analysis_focus, output_format.

Database schema summary: {schema_summary}
Request: {user_query}"""
        }]
    )
    return parse_json(response.content[0].text)

async def generate_sql(plan: dict, schema_detail: str) -> str:
    """Use Haiku for SQL — structured task with good prompting dominates."""
    response = await client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=400,
        system="""You are a SQL expert. Generate PostgreSQL queries.
Rules:
- Always use explicit column names (no SELECT *)
- Use CTEs for complex queries
- Add LIMIT 1000 unless aggregating
- Return only the SQL, no explanation""",
        messages=[{
            "role": "user",
            "content": f"""Schema: {schema_detail}

Goal: {plan['sql_goal']}

Few-shot examples:
[User: Get top 5 regions by revenue Q3 2024]
[SQL: WITH q3 AS (SELECT region, SUM(revenue) as total FROM sales WHERE quarter='Q3' AND year=2024 GROUP BY region) SELECT region, total FROM q3 ORDER BY total DESC LIMIT 5;]

Generate SQL for the goal above."""
        }]
    )
    return extract_sql(response.content[0].text)

async def plan_visualization(plan: dict) -> dict:
    """Use Haiku for viz planning — templated, low reasoning requirement."""
    response = await client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": f"""Given this visualization goal: {plan['viz_goal']}
Return JSON: {{"chart_type": "...", "x_axis": "...", "y_axis": "...", "title": "...", "color_scheme": "..."}}"""
        }]
    )
    return parse_json(response.content[0].text)

async def generate_code(data_sample: dict, viz_plan: dict) -> str:
    """Use Haiku for code gen — structured task, data is explicit."""
    response = await client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=600,
        messages=[{
            "role": "user",
            "content": f"""Write Python using matplotlib/seaborn to generate this chart.
Data columns available: {list(data_sample.keys())}
Viz plan: {viz_plan}
Return only runnable Python code."""
        }]
    )
    return extract_code(response.content[0].text)

async def analyze_and_recommend(data: dict, analysis_focus: str) -> dict:
    """Use Sonnet for analysis + recommendations — requires genuine reasoning."""
    response = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=800,
        messages=[{
            "role": "user",
            "content": f"""Analyze this sales data and provide:
1. Key findings (3–5 bullet points)
2. Top 3 recommended actions with expected impact
3. Risk factors to watch

Analysis focus: {analysis_focus}
Data: {format_data_for_analysis(data)}"""
        }]
    )
    return parse_analysis(response.content[0].text)

async def full_pipeline(user_query: str, db_connection) -> dict:
    """Orchestrate the pipeline with maximum parallelism."""

    # Step 1: Plan (Sonnet) — must complete first
    schema_summary = get_schema_summary(db_connection)  # pre-cached, fast
    plan = await plan_task(user_query, schema_summary)

    # Step 2: SQL generation and viz planning run IN PARALLEL (both need only the plan)
    schema_detail = get_schema_detail(plan["sql_goal"], db_connection)
    sql_task = asyncio.create_task(generate_sql(plan, schema_detail))
    viz_task = asyncio.create_task(plan_visualization(plan))

    sql_query, viz_plan = await asyncio.gather(sql_task, viz_task)

    # Step 3: Execute SQL (not an LLM call — deterministic)
    data = execute_sql(sql_query, db_connection)

    # Step 4: Code generation and analysis run IN PARALLEL (both need data)
    code_task = asyncio.create_task(generate_code(data, viz_plan))
    analysis_task = asyncio.create_task(analyze_and_recommend(data, plan["analysis_focus"]))

    code, analysis_result = await asyncio.gather(code_task, analysis_task)

    # Step 5: Execute code (deterministic, sandboxed)
    chart = execute_in_sandbox(code, data)

    return {
        "chart": chart,
        "analysis": analysis_result["findings"],
        "recommendations": analysis_result["recommendations"],
        "sql_used": sql_query,  # transparency: show what was queried
    }
```

### Cost Comparison

**Naive (all-Sonnet):**

| Step | Model | Input Tokens | Output Tokens | Cost |
|---|---|---|---|---|
| Plan | Sonnet | 500 | 200 | $0.0045 |
| SQL | Sonnet | 1,000 | 300 | $0.0075 |
| Analysis | Sonnet | 2,000 | 500 | $0.0135 |
| Code gen | Sonnet | 1,500 | 400 | $0.0105 |
| Recommend | Sonnet | 2,500 | 400 | $0.0165 |
| **Total** | | | | **$0.0525/query** |

At 2,000 queries/day: **$105/day = $3,150/month**

**Cascade (mixed models):**

| Step | Model | Input Tokens | Output Tokens | Cost |
|---|---|---|---|---|
| Plan | Sonnet | 500 | 200 | $0.0045 |
| SQL | Haiku | 1,000 | 300 | $0.00044 |
| Viz plan | Haiku | 500 | 100 | $0.00015 |
| Code gen | Haiku | 1,500 | 400 | $0.00053 |
| Analysis+Rec | Sonnet | 4,500 | 900 | $0.0270 |
| **Total** | | | | **$0.0326/query** |

At 2,000 queries/day: **$65/day = $1,953/month**

**Savings: 38% cost reduction with equal or better quality on the high-value steps.**

*Pricing: Sonnet at $3/M input + $15/M output, Haiku at $0.25/M input + $1.25/M output*

### Latency Optimization: SQL Retry Budget

SQL generation is the quality-critical step. If Haiku generates wrong SQL (10% of the time), you need a retry strategy that does not blow the latency budget.

```python
async def generate_sql_with_retry(plan: dict, schema_detail: str, db_connection) -> str:
    """Generate SQL, validate against schema, retry once if invalid."""
    sql = await generate_sql(plan, schema_detail)

    # Validate SQL before executing (EXPLAIN only, no data fetched)
    is_valid, error = validate_sql(sql, db_connection)

    if not is_valid:
        # Retry with error context — include what went wrong
        sql = await client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": f"""The following SQL had an error: {error}

Original SQL: {sql}

Fix the SQL. Return only the corrected SQL."""
            }]
        )
        sql = extract_sql(sql.content[0].text)

    return sql
```

First-try success rate target: > 90%. With retry: > 98%. The retry adds ~500ms (Haiku is fast) and only triggers 10% of the time.

---

## Solution

<details>
<summary>Show Solution</summary>

### Decision Framework for Model Selection in Agent Pipelines

Ask these questions for each step:

1. **Is this step ambiguous or creative?** If yes, use a capable model (Sonnet/Opus).
2. **Is this step structured and rule-bound?** If yes, use a fast/cheap model (Haiku) with strong few-shot examples.
3. **Is this step deterministic?** If yes, do not use an LLM at all — run deterministic code.
4. **Is the quality of this step's output visible to the user?** If yes, do not cut corners.
5. **Can this step's failure be recovered cheaply?** If yes (retry is cheap), use a smaller model and retry on failure.

### Sandboxed Code Execution

Never run LLM-generated code in the production environment. Use a container-based sandbox.

```python
import docker
import json

def execute_in_sandbox(code: str, data: dict) -> bytes:
    """Execute LLM-generated Python in an isolated container."""
    client = docker.from_env()

    container_code = f"""
import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import io
import base64

data = {json.dumps(data)}
df = pd.DataFrame(data)

{code}

buf = io.BytesIO()
plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
buf.seek(0)
print(base64.b64encode(buf.read()).decode())
"""

    result = client.containers.run(
        "python:3.11-slim",
        command=["python", "-c", container_code],
        mem_limit="256m",
        cpu_quota=50000,  # 50% of one CPU
        timeout=10,  # 10-second max execution
        remove=True,  # Auto-remove after run
        network_disabled=True,  # No network access from generated code
    )

    return base64.b64decode(result)
```

### Monitoring Metrics

- SQL first-try success rate (target: > 90%)
- p50 and p95 end-to-end latency
- Cost per query (track by model tier)
- Haiku vs. Sonnet routing distribution
- User satisfaction by step (which outputs get thumbs down?)

</details>

---

## Interview Version

"Design an agent that takes a natural language data analysis request and produces a chart, analysis, and recommendations. Latency < 8 seconds, cost < $0.05/query."

**Open with the key insight:**
"The first thing I want to do is map each step to its cognitive requirement. Not every step needs the same model — and that's both a cost and latency optimization."

**Draw the step-model mapping:**
```
Plan:            Sonnet  (ambiguous intent → expensive model justified)
SQL Gen:         Haiku   (structured + few-shot examples = cheap + fast)
Viz Plan:        Haiku   (templated output)
Code Gen:        Haiku   (structured, deterministic)
Code Execution:  No LLM  (just run the Python)
Analysis:        Sonnet  (genuine reasoning over results)
```

**Show the parallel execution timeline:**
"After planning, SQL gen and viz planning are independent — I run them in parallel. After the DB query, code gen and analysis are independent — I run them in parallel. This cuts ~6 seconds off a naive sequential design."

**Close with the number:**
"Cascade approach costs $0.033/query vs $0.053 for all-Sonnet. At 2,000 queries/day, that's $1,953 vs $3,150/month — 38% savings with no quality loss on the steps users actually evaluate."

---

## Follow-up Questions

1. Your SQL generation step has a 90% first-try success rate. For the 10% of failures, you retry with error context. But some queries fail because the user asked for data that does not exist in the database ("show revenue by country" when you only have region-level data). How do you distinguish a fixable SQL error from a semantic mismatch, and how do you handle each case?
2. A user asks a question that requires joining 8 tables with complex business logic. Haiku fails on the first attempt and the retry also fails. Your system falls back to Sonnet for a third attempt. This adds 4 seconds of latency. How do you design the fallback strategy so users do not experience a noticeably slow query without knowing why?
3. The visualization code generated by Haiku runs successfully but produces a chart that is technically correct but visually ugly (wrong colors, overlapping labels, inappropriate chart type for the data). How do you add a quality gate for generated visualizations without adding significant latency?
