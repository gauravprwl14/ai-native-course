# AI-Native Development Course

A practical, depth-first course for developers who want to build with AI.
Covers 50 chapters across 4 tiers — from LLM fundamentals to production
multi-agent systems.

**Live site:** https://gauravprwl14.github.io/ai-native-course/

## Who Is This For?

Developers who know Python (or Node.js) and want to become AI engineers.
No prior AI/ML knowledge required.

## Course Structure

| Tier | Name | Chapters | What You Build |
|------|------|----------|----------------|
| 1 | Foundations | 8 | First LLM API call → embeddings |
| 2 | Builder | 14 | RAG pipelines → agents |
| 3 | Advanced | 16 | Multi-agent systems → fine-tuning |
| 4 | Architect | 12 | Production systems → capstone |

Each chapter includes:
- **5 MDX pages**: overview, concepts, patterns, lab brief, quiz
- **Python lab**: starter with TODOs, complete solution, mocked pytest tests
- **Diagrams**: Mermaid sequence diagrams, architecture diagrams, concept maps

**Problem bank**: 20 elite problems across prompting, agents, RAG, and system design.

## Quick Start

### Browse the course

Visit: https://gauravprwl14.github.io/ai-native-course/

### Run labs locally

```bash
# Clone the repo
git clone https://github.com/gauravprwl14/ai-native-course
cd ai-native-course

# Set up Python environment
cd curriculum/shared
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env and add your API keys (minimum: ANTHROPIC_API_KEY for Tier 1–3 labs)

# Run a lab (fill in the TODOs first, then run)
cd ../tier-1-foundations/01-llms/lab/starter
python solution.py
```

### Run the site locally

```bash
cd website
npm install
npm run start
# Open http://localhost:3000
```

### Deploy with Docker

```bash
cd docker
./scripts/build.sh
docker-compose up

# Deploy to server
./scripts/deploy.sh user@your-server.com
```

## Repository Structure

```
ai-native-course/
├── website/docs/          ← MDX course content (50 chapters)
│   ├── tier-1-foundations/
│   ├── tier-2-builder/
│   ├── tier-3-advanced/
│   └── tier-4-architect/
├── curriculum/            ← Runnable Python labs
│   ├── tier-1-foundations/
│   ├── tier-2-builder/
│   ├── tier-3-advanced/
│   ├── tier-4-architect/
│   ├── problem-bank/      ← 20 elite problems
│   └── shared/            ← requirements.txt, utils, .env.example
├── docker/                ← Dockerfile, nginx, deploy scripts
└── .github/workflows/     ← CI (PRs) + deploy (main)
```

## Contributing

See [CLAUDE.md](./CLAUDE.md) for how to add chapters and labs.
