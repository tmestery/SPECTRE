---
name: setup-lab-target
description: >-
  Sets up a Docker Compose lab target for SPECTRE (DVWA v1). Use when adding
  a new target or preparing the demo environment.
---

# Setup Lab Target

## DVWA (v1 primary)

### Steps

1. **Create compose file** at `targets/dvwa/docker-compose.yml` (see [local-target-dvwa.md](../../../docs/local/local-target-dvwa.md))

2. **Create scope file** at `targets/dvwa/scope.yaml` with explicit allowlist

3. **Health check** — `targets/dvwa/healthcheck.sh`:
   ```bash
   #!/usr/bin/env bash
   curl -sf http://127.0.0.1:4280 >/dev/null || exit 1
   ```

4. **README** — `targets/dvwa/README.md` with login, security level, ports

5. **Start**
   ```bash
   docker compose -f targets/dvwa/docker-compose.yml up -d
   ```

6. **Verify scope enforcement** — orchestrator rejects `http://192.168.1.1` when not in allowlist

7. **Document** — update [local-target-dvwa.md](../../../docs/local/local-target-dvwa.md)

## Adding a new target (e.g. Juice Shop)

1. `targets/<name>/docker-compose.yml`
2. `targets/<name>/scope.yaml` — **required**
3. `targets/<name>/healthcheck.sh`
4. `docs/local/local-target-<name>.md`
5. Demo path table (which vulns for agent crew)
6. Issue + PR per **git-workflow**

## Checklist

- [ ] scope.yaml allowlist is minimal (not 0.0.0.0/0)
- [ ] Port documented and matches compose
- [ ] Health check script exits 0 when ready
- [ ] Safety doc cross-linked
