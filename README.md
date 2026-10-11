<p align="center">
  <img src="./docs/assets/logo.png" alt="SPECTRE logo" width="520">
</p>

<h1 align="center">SPECTRE</h1>

<p align="center">
  <strong>Self-coordinating Penetration and Exploit Crew for Threat Research and Exposure</strong>
</p>

<p align="center">
  Multi-agent GitHub repository security audits with a live dashboard — scope-controlled and observable end to end.
</p>

<p align="center">
  <img alt="Python 3.12+" src="https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white">
  <img alt="CI" src="https://img.shields.io/github/actions/workflow/status/tmestery/SPECTRE/ci.yml?branch=main&label=CI">
</p>

---

> [!IMPORTANT]
> SPECTRE audits only repositories you own or have explicit permission to test.
> Every engagement requires a scope allowlist (`scopes/*.yaml`). Do not scan
> arbitrary public repos without authorization.

## What it does

- **Four-agent crew** — Recon, VulnHunter, Exploiter, and Reporter coordinate through a shared Findings Bus
- **Live dashboard** — Watch findings, handoffs, and report sections stream in real time
- **Sandboxed tools** — GitHub API, gitleaks, osv-scanner, and workflow checks with timeouts and redaction
- **Safety by default** — Repo allowlists, audit logs, and an engagement kill switch

## Run with Docker

**Requirements:** Docker with Compose, a GitHub token, and an LLM API key (Groq by default).

```bash
cp .env.example .env
# Set GITHUB_TOKEN and GROQ_API_KEY in .env

docker compose up --build
```

Open [http://localhost:8080](http://localhost:8080) and choose **Start audit**.

| Port | Service |
|------|---------|
| `8080` | Demo dashboard |
| `8765` | WebSocket control plane |

Optional CLI helpers (reports, halt, sessions):

```bash
docker compose --profile cli run --rm cli sessions
```

Full details: [Docker guide](docs/local/local-dev-docker.md).

## Configure

| Variable | Purpose |
|----------|---------|
| `GITHUB_TOKEN` | Access to authorized target repos |
| `GROQ_API_KEY` | LLM provider key (when `LLM_PROVIDER=groq`) |
| `LLM_MODEL` | Model id (see `.env.example`) |

Add a scope file under `scopes/` listing `allowed_repos` before auditing a new target. Defaults ship for this repo (`scopes/spectre.yaml`) and a demo sample (`scopes/vuln-sample.yaml`).

## Local development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]" && npm install && cp .env.example .env

# Terminal 1
python -m spectre.cli serve

# Terminal 2
npm run dev   # http://localhost:5173
```

## Documentation

- [Agent guide](AGENTS.md) · [Docs index](docs/local/README.md)
- [Architecture](docs/local/local-arch-overview.md) · [Safety & scope](docs/local/local-safety-lab-scope.md)
- [Docker](docs/local/local-dev-docker.md) · [Demo UI](docs/local/local-ui-demo-dashboard.md)

## Security

Use SPECTRE only on authorized repositories. Keep tokens in `.env`; never commit secrets or unredacted findings. Report vulnerabilities in SPECTRE privately to the maintainers.
