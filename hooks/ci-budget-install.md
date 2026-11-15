# Install the check budget on session start

`~/.claude/hooks/valentin-mode-load.py` already runs when a session starts. This change does not edit that file. After this lands on main and house-rules sync pulls it, add the call below just before the final `print` in that hook.

```python
import importlib.util
import os

hook = Path.home() / ".local/share/house-rules/hooks/ci-budget-session.py"
if hook.is_file():
    spec = importlib.util.spec_from_file_location("ci_budget_session", hook)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    extra = mod.budget_line(os.getcwd())
    if extra:
        text += "\n\n" + extra
```

`budget_line` does nothing when the working directory is not a git checkout, when `origin` is not a `valentinyeo` GitHub repo, or when the repo name matches the out-of-bounds pattern (`inne` or `vwo` as a whole word). Otherwise it runs `bin/ci-budget` with a 20 second timeout. The result is cached for 6 hours under `~/.local/state/ci-budget/`. When the repo is over budget, the session context gains one line:

`CHECKS OVER BUDGET: <items>. You own this repo's checks: fix them first (SOFT-2470).`

A timeout or a missing `ci-budget` adds no line and is not cached, so the next session tries again.
