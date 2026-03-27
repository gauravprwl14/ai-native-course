# AI-Native Development Course — Design Spec
**Date:** 2026-03-27
**Status:** Approved
**Author:** Brainstorming session with Gaurav Porwal

---

## 1. Overview

A comprehensive, practical AI-native development course published as a GitHub repository with a Docusaurus-rendered website. Targets junior-to-mid developers who know Python or Node.js and want to become AI engineers — capable of building agents, RAG pipelines, LLM integrations, and passing AI engineering interviews.

**Goals:**
- Zero-to-depth on 100 AI-native concepts
- Practical labs with runnable Python code (Node.js in iteration 2)
- Heavy visualization: diagrams, sequence flows, concept maps — not just text
- Structured MCQ quizzes with localStorage progress tracking
- Elite problem bank (the 1% problems)
- Deployable site: GitHub Pages + Docker for bare metal

---

## 2. Technology Stack

| Layer | Choice | Reason |
|---|---|---|
| Site framework | Docusaurus v3 | React-powered, MDX, great docs UX, plugin ecosystem |
| Language (iter 1) | Python | Broader AI/ML ecosystem, most AI tutorials use it |
| Language (iter 2) | Node.js / TypeScript | Streaming UIs, Vercel AI SDK, SSE |
| Diagrams | Mermaid (embedded in MDX) | Native Docusaurus support, version-controlled |
| Visual components | React components in MDX | Interactive diagrams, concept maps, flow visualizations |
| Quiz | Custom React component | localStorage scoring, per-chapter progress badges |
| Deployment | Docker + Nginx | Bare metal support; GitHub Actions for GH Pages |
| CI/CD | GitHub Actions | 3 workflows: CI, GH Pages deploy, Docker deploy |

---

## 3. Repo Structure (Approach C — Monorepo with Clear Separation)

```
ai-native-course/
│
├── CLAUDE.md                              ← AI assistant context for this repo
├── README.md                              ← Quick start, course overview
├── .env.example                           ← API key templates
│
├── website/                               ← Docusaurus site
│   ├── docusaurus.config.ts
│   ├── sidebars.ts
│   ├── src/
│   │   ├── components/
│   │   │   ├── Quiz/                      ← Scored quiz, localStorage tracking
│   │   │   ├── ProgressTracker/           ← Chapter completion badges
│   │   │   ├── ConceptMap/                ← Visual concept relationship graph
│   │   │   ├── SequenceDiagram/           ← Mermaid wrapper with annotations
│   │   │   ├── ArchDiagram/               ← Architecture diagram component
│   │   │   └── ConceptLink/               ← Cross-chapter reference component
│   │   ├── css/
│   │   └── pages/
│   ├── docs/
│   │   ├── intro.mdx                      ← Course overview, learning path, how to use
│   │   ├── tier-1-foundations/
│   │   ├── tier-2-builder/
│   │   ├── tier-3-advanced/
│   │   └── tier-4-architect/
│   └── static/
│       └── diagrams/                      ← SVG exports, images
│
├── curriculum/                            ← All runnable code
│   ├── tier-1-foundations/
│   ├── tier-2-builder/
│   ├── tier-3-advanced/
│   ├── tier-4-architect/
│   ├── problem-bank/                      ← Elite 1% problems
│   └── shared/
│       ├── utils.py
│       ├── requirements.txt
│       └── .env.example
│
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── nginx.conf
│   └── scripts/
│       ├── build.sh
│       ├── deploy.sh
│       └── health-check.sh
│
└── .github/
    └── workflows/
        ├── ci.yml
        ├── deploy-gh-pages.yml
        └── deploy-docker.yml
```

---

## 4. 4-Tier Curriculum

### Tier 1 — Foundations (8 chapters)
Pre-req: Python basics. No AI knowledge needed.

| Ch | Topic | Lab |
|---|---|---|
| 01 | LLMs & How They Work | Call your first LLM API |
| 02 | Tokens & Tokenization | Tokenize text, count cost |
| 03 | Context Window | Build a context-aware Q&A |
| 04 | Temperature & Sampling | Compare outputs at different temps |
| 05 | Embeddings | Embed sentences, find nearest neighbor |
| 06 | Inference vs Training | Run inference via API |
| 07 | Foundation vs Fine-tuned Models | Prompt same task, compare outputs |
| 08 | Multimodal Models | Describe an image via API |

### Tier 2 — Builder (14 chapters)
Pre-req: Tier 1 complete.

| Ch | Topic | Lab |
|---|---|---|
| 09 | Zero/Few-shot Prompting | Classify text with 0 vs 5 shots |
| 10 | Chain-of-Thought | Solve math word problems with CoT |
| 11 | System Prompts | Build a customer service bot |
| 12 | Structured Output | Extract structured data from text |
| 13 | Role + Meta Prompting | Auto-generate prompt variants |
| 14 | RAG — Core Concept | Build a document Q&A with RAG |
| 15 | Vector Databases | Index docs in Chroma/pgvector |
| 16 | Chunking Strategies | Compare retrieval quality |
| 17 | Hybrid Search | Build hybrid search pipeline |
| 18 | Re-ranking | Improve RAG precision |
| 19 | Tool Use / Function Calling | Build a weather + calculator agent |
| 20 | Agentic Loop | ReAct agent from scratch |
| 21 | AI Agent (full) | Multi-tool agent |
| 22 | Streaming (SSE) | Stream responses to terminal + browser |

### Tier 3 — Advanced (16 chapters)
Pre-req: Tier 2 complete.

| Ch | Topic | Lab |
|---|---|---|
| 23 | Planning & Task Decomposition | Planner agent |
| 24 | Multi-Agent Systems | Two-agent pipeline |
| 25 | Agent Memory | Agent with persistent memory |
| 26 | Reflection & Self-critique | Self-improving summarizer |
| 27 | Agent Handoff | Router → specialist agents |
| 28 | Human-in-the-Loop (HITL) | Agent that asks before acting |
| 29 | Fine-tuning Basics | Prepare a fine-tuning dataset |
| 30 | LoRA / QLoRA | Fine-tune a small model (Llama) |
| 31 | RLHF & DPO | DPO dataset construction |
| 32 | Evals / LLM Evaluation | Eval a RAG pipeline |
| 33 | LLM-as-Judge | Auto-eval pipeline |
| 34 | Hallucination Detection | Detect hallucinations in RAG output |
| 35 | Tracing & Observability | Instrument an agent with tracing |
| 36 | Guardrails | Add safety layer to a chatbot |
| 37 | Prompt Injection (Security) | Red-team your own agent |
| 38 | PII Handling | Strip PII from prompts |

### Tier 4 — Architect (12 chapters)
Pre-req: Tier 3 complete.

| Ch | Topic | Lab |
|---|---|---|
| 39 | LLM APIs Deep-dive | Cost estimator CLI tool |
| 40 | Model Selection Trade-offs | Benchmark same task across models |
| 41 | MCP (Model Context Protocol) | Build an MCP server |
| 42 | A2A & ACP Protocols | Agent-to-agent delegation |
| 43 | LLM Hosting | Run Llama locally with Ollama |
| 44 | LLM Caching | Add caching to RAG pipeline |
| 45 | Latency Optimization | Benchmark + optimize an agent |
| 46 | AI Gateway / Proxy | Build a simple LLM gateway |
| 47 | Knowledge Graphs (GraphRAG) | GraphRAG vs flat RAG comparison |
| 48 | Agentic Workflows (Durable) | Durable workflow with checkpoints |
| 49 | Computer Use / UI Agents | Simple browser agent |
| 50 | Capstone — Build an AI System | Full agent system from scratch |

---

## 5. Chapter Template (5 Pages per Chapter)

```
tier-X/chapter-YY-topic/
├── index.mdx       ← Overview, what you'll learn, prereqs, time estimate
├── concepts.mdx    ← Core concept: problem → intuition → how it works → diagram
├── patterns.mdx    ← Real-world patterns, anti-patterns, sequence diagrams
├── lab.mdx         ← Lab brief, acceptance criteria, how to run
└── quiz.mdx        ← 5–10 scored MCQs with explanations
```

### Concept Page Flow (concepts.mdx)
1. **The Problem** — Real scenario that motivates the concept
2. **The Intuition** — Layman analogy + visual diagram
3. **How It Works** — Technical depth, step by step
4. **Sequence / Architecture Diagram** — Mermaid embedded in MDX
5. **Key Terms** — Inline glossary
6. **Interview Angle** — What interviewers actually ask
7. **Common Mistakes** — Anti-patterns to avoid
8. **Further Reading** — 2–3 curated links (docs, articles, YouTube)

### Lab Folder Structure
```
curriculum/tier-X/chapter-YY/lab/
├── problem.md          ← Problem statement, constraints, acceptance criteria
├── starter/
│   └── solution.py     ← Scaffold with TODO comments
├── solution/
│   └── solution.py     ← Complete working solution
└── tests/
    └── test_solution.py ← pytest tests to verify their work
```

### Quiz Structure
- 5–10 questions per chapter
- 3 difficulty tiers: Recall (1pt), Apply (2pt), Analyze (3pt)
- Pass threshold: 70%
- Wrong answers show explanation + link back to concept
- Progress stored in localStorage: `{ "tier2-ch14": { score: 18, max: 20, passed: true } }`

---

## 6. Visualization Strategy

Text alone is insufficient for AI concepts. Every chapter MUST include at least:

| Visual Type | Tool | When to Use |
|---|---|---|
| Sequence diagram | Mermaid `sequenceDiagram` | API flows, agent loops, RAG pipelines |
| Architecture diagram | Mermaid `graph TD` or custom SVG | System components, data flow |
| Concept map | Custom React `<ConceptMap>` component | How this concept links to others |
| Mental model analogy | Inline illustration or ASCII art | Intuition building for abstract ideas |
| Before/After comparison | Side-by-side code blocks | Anti-pattern vs pattern |
| Token visualization | Interactive React component | Chapters 02, 03 — tokenization |
| Embedding space | 2D scatter plot (Plotly or D3) | Chapter 05 — embeddings |
| Attention heatmap | Static SVG | Chapter 01 — how LLMs process text |

### Custom React Components (in website/src/components/)
- `<ConceptMap>` — D3-based graph showing chapter relationships
- `<TokenVisualizer>` — Colorizes tokens in a string, shows count + cost
- `<EmbeddingPlot>` — 2D PCA scatter of sentence embeddings
- `<AgentLoop>` — Animated step-through of the observe→think→act cycle
- `<ArchDiagram>` — Wrapper for complex Mermaid diagrams with zoom/pan
- `<Timeline>` — Visual learning path across all 4 tiers

---

## 7. Problem Bank Design

```
curriculum/problem-bank/
├── README.md               ← What makes a great AI problem
├── prompting/
├── agents/
├── rag/
└── system-design/
```

Each problem file contains:
1. **Problem Statement** — Clear, constrained, real-world scenario
2. **What Makes This Hard** — The non-obvious challenge
3. **Naive Approach** — Common wrong solution and why it fails
4. **Expert Approach** — With rationale and mental model
5. **Solution** — Collapsible `<details>` block
6. **Interview Version** — How to present this verbally in 2 minutes

---

## 8. Deployment Design

### Docker (Bare Metal)
```
Dockerfile: multi-stage
  Stage 1: node:20-alpine → npm run build (Docusaurus static build)
  Stage 2: nginx:alpine → copy /build → serve on port 80

docker-compose.yml: local preview on port 3000
nginx.conf: gzip, cache headers, SPA fallback (index.html)

scripts/deploy.sh:
  - SSH to server
  - docker pull ghcr.io/<org>/ai-native-course:latest
  - docker-compose up -d --force-recreate
```

### GitHub Actions Workflows
- **ci.yml** — PR checks: `docusaurus build`, `pytest curriculum/`
- **deploy-gh-pages.yml** — Push to `main` → `docusaurus build` → deploy to `gh-pages` branch
- **deploy-docker.yml** — Git tag `v*` → build image → push to GHCR

---

## 9. CLAUDE.md Content

The repo CLAUDE.md will document:
- Repo structure overview
- How to add a new chapter (file naming, frontmatter conventions)
- How to add a new lab (folder structure, test conventions)
- How to run the site locally
- How to run labs locally
- Docusaurus MDX conventions used in this repo
- Component API for `<Quiz>`, `<ConceptMap>`, `<AgentLoop>` etc.

---

## 10. Success Criteria

- [ ] Learner can go from zero to building a working RAG pipeline in Tier 2
- [ ] Learner can build a multi-agent system by end of Tier 3
- [ ] Every chapter has at least 1 runnable lab with passing tests
- [ ] Every chapter has at least 2 diagrams (concept + flow)
- [ ] Quiz pass rate ≥ 70% gates chapter "completion" badge
- [ ] Site deploys via `docker-compose up` in under 5 minutes
- [ ] Site deploys to GitHub Pages via single push to main
- [ ] Problem bank has ≥ 20 elite problems across 4 categories

---

## 11. Out of Scope (Iteration 1)

- Node.js / TypeScript implementations (planned for iteration 2)
- User accounts or server-side progress tracking
- Video content
- Paid tier or authentication
- Mobile app
