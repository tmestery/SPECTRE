# local-target-dvwa

**Status:** draft  
**Updated:** 2026-06-25  
**Related:** [local-safety-lab-scope.md](local-safety-lab-scope.md), `.cursor/skills/setup-lab-target/`

## Summary

DVWA (Damn Vulnerable Web Application) is SPECTRE's primary v1 lab target — a deliberately vulnerable PHP web app ideal for demonstrating the full agent crew from recon through SQLi exploitation.

## Context

DVWA is well-documented, fast to deploy via Docker, and has graded vulnerability difficulty. Security level "low" for demo ensures agents can achieve visible wins without advanced bypass techniques.

## Implementation

### Docker Compose (planned)

```yaml
# targets/dvwa/docker-compose.yml
services:
  dvwa:
    image: vulnerables/web-dvwa
    ports:
      - "4280:80"
    environment:
      - MYSQL_HOSTNAME=db
    depends_on:
      - db
  db:
    image: mariadb:10
    environment:
      - MYSQL_ROOT_PASSWORD=dvwa
      - MYSQL_DATABASE=dvwa
```

### Scope file

```yaml
# targets/dvwa/scope.yaml
name: dvwa-lab
allowed_hosts: [127.0.0.1, localhost]
allowed_urls:
  - http://127.0.0.1:4280
  - http://localhost:4280
allowed_ports: [4280]
max_duration_minutes: 30
authorization: lab-local-only
```

### Setup steps

```bash
docker compose -f targets/dvwa/docker-compose.yml up -d
# Wait for health check
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:4280  # expect 200 or 302
# Default login: admin / password (document in target README)
# Set DVWA security to "low" via web UI for demo
```

### Demo exploit path

| Step | Agent | Action | Expected finding |
|------|-------|--------|------------------|
| 1 | Recon | nmap + httpx | Port 4280, Apache, DVWA |
| 2 | VulnHunter | nuclei + sqli probe | SQLi on `/vulnerabilities/sqli/` |
| 3 | Exploiter | sqlmap | Database enumeration PoC |
| 4 | Reporter | synthesize | Full report with evidence |

### DVWA vulnerabilities (reference for agents)

| Vuln | Path | Demo priority |
|------|------|---------------|
| SQL Injection | `/vulnerabilities/sqli/` | **Primary** |
| XSS | `/vulnerabilities/xss_r/` | Secondary |
| CSRF | `/vulnerabilities/csrf/` | Phase 2 |
| File Upload | `/vulnerabilities/upload/` | Phase 2 |

### Health check script (planned)

`targets/dvwa/healthcheck.sh` — exits 0 when DVWA responds on 4280.

## Tests

| Case | Type |
|------|------|
| scope.yaml validates against running DVWA URL | Positive |
| compose brings up service on 4280 | Integration (manual CI optional) |
| scope rejects 192.168.x.x when only 127.0.0.1 allowed | Negative |

## Changelog

- 2026-06-25 — Initial DVWA target doc
