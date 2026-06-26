# SPECTRE

**S**elf-coordinating **P**enetration and **E**xploit **C**rew for **T**hreat **R**esearch and **E**xposure — multi-agent GitHub repository security auditing.

## Quick start

### Docker (recommended)

```bash
cp .env.example .env
# Set GITHUB_TOKEN in .env

docker compose up --build
```

Open http://localhost:8080 and click **Start audit**. See [docs/local/local-dev-docker.md](docs/local/local-dev-docker.md).

### Local development

```bash
# Terminal 1 — control server
python -m spectre.cli serve

# Terminal 2 — UI
npm install
npm run dev
```

Open http://localhost:5173 and click **Start audit**.

```bash
# Python setup
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Set GITHUB_TOKEN and GROQ_API_KEY

# Tests
pytest
npm test
```

See [AGENTS.md](AGENTS.md) and [docs/local/](docs/local/) for architecture and workflows.
