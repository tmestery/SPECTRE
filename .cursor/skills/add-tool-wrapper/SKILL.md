---
name: add-tool-wrapper
description: >-
  Creates a sandboxed wrapper for a security tool (nmap, nuclei, sqlmap, etc.)
  with scope checks, timeouts, audit logging, and Finding output parsing.
  Use when integrating a new offensive or recon tool.
---

# Add Tool Wrapper

## Prerequisites

- Read [local-safety-lab-scope.md](../../../docs/local/local-safety-lab-scope.md)
- Issue + branch per **git-workflow**

## Steps

1. **Create wrapper** at `spectre/tools/<tool>.py` extending `spectre/tools/base.py`:
   - `async def run(target: str, **opts) -> ToolResult`
   - Call `safety.scope.check(target)` first
   - Async subprocess with timeout (default 120s)
   - Audit log via bus `tool_invocation` event
   - Parse stdout/stderr → structured dict

2. **Schema** — define Pydantic output model for parsed results

3. **Finding mapping** — helper to convert ToolResult → list[Finding]

4. **Register** — add to relevant agent's `tools.yaml`

5. **Fixture** — add mock output to `tests/fixtures/<tool>_*.xml|json|log`

6. **Tests** — 1+3 in `tests/unit/test_<tool>.py`:
   - Parse fixture → valid output
   - Out-of-scope rejected before subprocess
   - Timeout handled
   - Malformed output handled

7. **Document** — `docs/local/local-tool-<tool>.md`

## Base wrapper contract

```python
class ToolWrapper(ABC):
    name: str
    timeout_seconds: int = 120

    async def execute(self, target: str, scope: Scope, **kwargs) -> ToolResult:
        await scope.check(target)
        # audit log start
        # async subprocess
        # audit log end
        return self.parse(output)
```

## Checklist

- [ ] No shell injection — use list args, not shell=True with user input
- [ ] Scope check before execution
- [ ] Audit logged
- [ ] Tests use fixtures only (no real tool in unit tests)
