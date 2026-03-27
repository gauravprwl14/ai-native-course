# AI-Native Development Course

A practical, depth-first course for developers who want to build with AI.
Covers 50 chapters across 4 tiers — from LLM fundamentals to production
multi-agent systems.

## Who Is This For?

Developers who know Python (or Node.js) and want to become AI engineers.
No prior AI/ML knowledge required.

## Repository Setup

> **Fork this repo** before cloning. Replace `your-org` with your GitHub username or organization name throughout this file.

## Course Structure

| Tier | Name | Chapters | What You Build |
|------|------|----------|----------------|
| 1 | Foundations | 8 | First LLM API call → embeddings |
| 2 | Builder | 14 | RAG pipelines → agents |
| 3 | Advanced | 16 | Multi-agent systems → fine-tuning |
| 4 | Architect | 12 | Production systems → capstone |

## Quick Start

### Browse the course
Visit: https://<your-org>.github.io/ai-native-course

### Run labs locally

```bash
# Clone the repo
git clone https://github.com/<your-org>/ai-native-course
cd ai-native-course

# Set up Python environment
cd curriculum/shared
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Copy environment variables from template
# curriculum/shared/.env.example contains all required API key names
cp .env.example .env
# Edit .env and add your API keys (minimum: ANTHROPIC_API_KEY for Tier 1–3 labs)

# Run a lab example (start here after completing setup)
cd ../tier-1-foundations/01-llms/lab/starter
python solution.py   # fill in the TODOs first, then run
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
# Build + run locally
cd docker
./scripts/build.sh
docker-compose up

# Deploy to server
./scripts/deploy.sh user@your-server.com
```

## Contributing

See [CLAUDE.md](./CLAUDE.md) for how to add chapters and labs.
