# SPECTRE

**S**elf-coordinating **P**enetration and **E**xploit **C**rew for **T**hreat **R**esearch and **E**xposure — a multi-agent system that collaboratively audits **authorized GitHub repositories** for secrets, vulnerable dependencies, and misconfigurations.

## Quick start

> Scaffold not yet implemented. See [docs/local/local-plan-roadmap.md](docs/local/local-plan-roadmap.md) for build phases.

```bash
# Phase 0 (planned)
cp .env.example .env          # GROQ_API_KEY + GITHUB_TOKEN
npm install && npm run dev    # demo UI
python -m spectre.cli run \
  --repo owner/repo \
  --scope scopes/my-repo.yaml
```

See [AGENTS.md](AGENTS.md) and [docs/local/](docs/local/) for architecture, agent design, and workflows.
