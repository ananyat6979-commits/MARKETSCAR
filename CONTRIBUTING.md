Thanks for helping improve MARKETSCAR. This document explains how to run tests, format code, commit, and update dependencies.

## Quickstart (local dev)
1. Create virtualenv:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # bash / macOS
   .venv\Scripts\Activate.ps1  # PowerShell (Windows)
   ```

2. Install pinned runtime deps:
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   ```

3. Install developer tools:
   ```bash
   pip install pre-commit pytest
   pre-commit install
   ```

4. Run tests:
   ```bash
   pytest -q
   ```

5. Run pre-commit checks locally:
   ```bash
   pre-commit run --all-files
   ```

## Formatting & Linting
- Project enforces `black` (line-length: 79), `isort` (profile=black), and `flake8`.
- Use `pre-commit run --all-files` to auto-format/lint before committing.
- If `pre-commit` modifies files during commit, add and re-commit the changes.

## Branches & commits
- Branches: `feature/<short-desc>`, `fix/<short-desc>`, `chore/<short-desc>`.
- Commit message style: `type(scope): short summary` example:
  - `fix(diagnostic): fallback for degenerate KDE samples`
  - `ci: pin workflow + run calibrate in CI`

## Updating dependencies
- Update dependencies locally, run your full test suite, then commit updated `requirements.txt`.
- **Do not** run `pip-compile` in CI. Compile locally (if needed) and commit the pinned `requirements.txt`.

## CI
- CI expects a committed `requirements.txt` file. If tests require secrets (dev RSA keys), add them as GitHub Secrets and the workflow restores them into `/tmp`.

If anything in the process is confusing or breaks, open a draft PR and tag `@ananyat6979-commits` (or leave a comment) — we'll help.

Thank you!
