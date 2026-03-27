# AI-Native Course — Context for AI Assistants

## Repo Purpose

This is an AI-native development course. It has two main parts:
1. `website/` — Docusaurus v3 site (the course content as MDX)
2. `curriculum/` — Runnable Python labs (one per chapter)

## Repo Structure

```
ai-native-course/
├── website/docs/          ← MDX course content
│   ├── tier-1-foundations/
│   ├── tier-2-builder/
│   ├── tier-3-advanced/
│   └── tier-4-architect/
├── curriculum/            ← Python lab code
│   ├── tier-1-foundations/
│   ├── tier-2-builder/
│   ├── tier-3-advanced/
│   ├── tier-4-architect/
│   └── problem-bank/
├── docker/                ← Dockerfile, nginx, deploy scripts
└── .github/workflows/     ← CI/CD
```

## How to Add a New Chapter

1. Create the docs folder: `website/docs/tier-X/chapter-YY-topic/`
2. Create 5 MDX files: `index.mdx`, `concepts.mdx`, `patterns.mdx`, `lab.mdx`, `quiz.mdx`
3. Create the lab folder: `curriculum/tier-X/chapter-YY-topic/lab/`
4. Create lab structure: `problem.md`, `starter/solution.py`, `solution/solution.py`, `tests/test_solution.py`
5. Add chapter entry to `website/sidebars.ts`

## Chapter MDX Frontmatter Convention

Every MDX file in `website/docs/` must start with:

```yaml
---
title: "Chapter Title"
sidebar_position: 1
description: "One-line description for SEO and sidebar"
---
```

## Lab File Convention

- `starter/solution.py` must contain `# TODO:` comments for every step the learner needs to complete.
- `solution/solution.py` must be fully working with no TODOs.
- `tests/test_solution.py` must import from `starter.solution` (not solution/) so tests run against learner's work.

## Running the Site Locally

```bash
cd website
npm install
npm run start
```

## Running Labs Locally

```bash
cd curriculum/shared
pip install -r requirements.txt
cp .env.example .env
# Add API keys to .env
```

## Running Lab Tests

```bash
cd curriculum/tier-X/chapter-YY/lab
pytest tests/ -v
```

## Component API

### `<Quiz>` component

```mdx
import Quiz from '@site/src/components/Quiz';

<Quiz
  questions={[
    {
      id: "q1",
      text: "What does RAG stand for?",
      options: ["A) ...", "B) ...", "C) ...", "D) ..."],
      correct: 1,
      explanation: "RAG stands for..."
    }
  ]}
  chapterId="tier2-ch14"
  passMark={70}
/>
```

### `<ConceptMap>` component

```mdx
import ConceptMap from '@site/src/components/ConceptMap';

<ConceptMap
  current="embeddings"
  related={["tokens", "semantic-search", "rag", "vector-databases"]}
/>
```

### `<TokenVisualizer>` component

```mdx
import TokenVisualizer from '@site/src/components/TokenVisualizer';

<TokenVisualizer text="Hello world, this is a test sentence." model="cl100k_base" />
```

### `<AgentLoop>` component

```mdx
import AgentLoop from '@site/src/components/AgentLoop';

<AgentLoop steps={["Observe", "Think", "Act"]} animated={true} />
```

## Docusaurus Config Notes

- Custom components live in `website/src/components/`
- Global CSS is `website/src/css/custom.css`
- Sidebar is auto-generated from folder structure via `sidebars.ts`
- MDX plugins enabled: mermaid, math (katex)

## Docker Notes

- `docker/Dockerfile` is multi-stage: build stage uses node:20-alpine, serve stage uses nginx:alpine
- `docker/nginx.conf` serves the Docusaurus build with SPA fallback
- `docker/scripts/deploy.sh` SSHs to the target server and restarts the container

## Naming Conventions

- Chapter folders: `NN-kebab-case-topic/` (e.g., `01-llms/`, `14-rag-core/`)
- MDX files: lowercase, kebab-case (e.g., `concepts.mdx`)
- Python files: `snake_case.py`
- Test files: `test_snake_case.py`
- React components: `PascalCase/` folder with `index.tsx`
