# SPECTRE

**S**elf-coordinating **P**enetration and **E**xploit **C**rew for **T**hreat **R**esearch and **E**xposure — multi-agent GitHub repository security auditing.

## Quick start

### Docker (recommended)

```bash
cp .env.example .env
# Set GITHUB_TOKEN in .env

docker compose up --build
```

Open http://localhost:8080. Paste the `session_id` from the container logs, or use `?session=<id>` in the URL. See [docs/local/local-dev-docker.md](docs/local/local-dev-docker.md).

### Local development

```bash
# Python
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# UI (optional)
npm install

# Configure
cp .env.example .env
# Set GITHUB_TOKEN (optional for public repos) and GROQ_API_KEY (Phase 2+)

# Run Phase 1 audit
python -m spectre.cli run \
  --repo tmestery/SPECTRE \
  --scope scopes/spectre.yaml \
  --branch chore/1-phase-0-docs-scaffold

# Tests
pytest
npm test
npm run dev
```

See [AGENTS.md](AGENTS.md) and [docs/local/](docs/local/) for architecture and workflows.
