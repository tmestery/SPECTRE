# SPECTRE

**S**elf-coordinating **P**enetration and **E**xploit **C**rew for **T**hreat **R**esearch and **E**xposure — a multi-agent penetration testing system where specialized agents collaborate on authorized lab targets.

## Quick start

> Scaffold not yet implemented. See [docs/local/local-plan-roadmap.md](docs/local/local-plan-roadmap.md) for build phases.

```bash
# Phase 0 (planned)
docker compose -f targets/dvwa/docker-compose.yml up -d
npm install && npm run dev          # demo UI
python -m spectre.cli run --target dvwa --scope lab
```

See [AGENTS.md](AGENTS.md) and [docs/local/](docs/local/) for architecture, agent design, and workflows.
