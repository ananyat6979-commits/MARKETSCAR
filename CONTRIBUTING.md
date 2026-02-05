CONTRIBUTING to MARKETSCAR
=========================

1. Code style
   - Run `black .` before committing.
   - Run `isort .` for import ordering.

2. Tests
   - Add tests for new features under tests/
   - Run `pytest -q` locally before pushing.

3. Pre-commit
   - Install pre-commit: `pip install pre-commit`
   - Run once to install hooks: `pre-commit install`

4. Secrets and keys
   - Never commit private keys (.pem) to the repo.
   - Use `.secrets/` for local dev keys and add `.secrets` to `.gitignore`.
   - Use `src/infra/keys.py` helpers to generate ephemeral keys for tests and CI.

5. Workflow
   - Create a feature branch and open a PR against main.
   - PR must pass CI (unit tests + calibration + replay checks) and be reviewed.

Thank you.
