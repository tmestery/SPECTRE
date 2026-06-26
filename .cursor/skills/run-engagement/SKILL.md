---
name: run-engagement
description: >-
  Runs a full SPECTRE penetration test engagement against an authorized lab
  target. Use when demoing, testing the crew end-to-end, or validating handoffs.
---

# Run Engagement

**Lab targets only.** Verify scope before running.

## Prerequisites

- Lab target running (see **setup-lab-target**)
- `scope.yaml` exists for target
- LLM API key in `.env` (not committed)
- Python env installed (`pip install -e .` once scaffold exists)

## Steps

1. **Start target**
   ```bash
   docker compose -f targets/dvwa/docker-compose.yml up -d
   ./targets/dvwa/healthcheck.sh
   ```

2. **Configure DVWA** (first run)
   - Open http://127.0.0.1:4280
   - Login: admin / password
   - Set security level to **Low**

3. **Start orchestrator**
   ```bash
   python -m spectre.cli run \
     --target dvwa \
     --scope targets/dvwa/scope.yaml
   ```

4. **Start demo UI** (Phase 3)
   ```bash
   npm run dev
   # Open http://localhost:5173
   ```

5. **Watch** — agent chat, timeline, handoffs in UI or terminal stream

6. **Halt** if needed
   ```bash
   python -m spectre.cli halt --session <id>
   ```

7. **Export report**
   ```bash
   python -m spectre.cli report --session <id> --format markdown
   ```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Scope rejection | Check target URL matches `scope.yaml` |
| Tool not found | Install nmap/sqlmap or use Docker sidecar |
| LLM errors | Verify `.env` API key |
| DVWA not ready | Wait for compose health; check port 4280 |

## Checklist

- [ ] Only in-scope URLs in scope file
- [ ] Engagement halted when done
- [ ] Report exported for review
- [ ] No credentials committed from session
