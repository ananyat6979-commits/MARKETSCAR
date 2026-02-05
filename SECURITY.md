MARKETSCAR SECURITY GUIDELINES
==============================

# Security Policy

Thank you for taking the time to report a security issue.

## Supported scope
- Vulnerabilities in code in this repository.

## Reporting a vulnerability
Preferred: use GitHub Security Advisories to report privately:
1. Go to the repository on GitHub -> **Security** -> **Advisories** -> **Draft a new advisory**.
2. Provide a clear description, steps to reproduce, impact, and suggested mitigation.

If GitHub Security Advisories are not possible, email: `ananyatiwari6979@gmail.com` with:
- affected component / path
- reproduction steps
- PoC if available
- severity & impact

Do *not* post exploit details publicly until a fix is available.

## Private key & secrets guidance
- Never commit private keys or credentials to the repository.
- For CI, store secrets with GitHub Secrets and use workflow steps to write ephemeral files (the CI workflow supports this).
- If you accidentally committed a secret, rotate it immediately and remove the secret from git history.

## Disclosure policy
We will acknowledge receipt within 3 business days and provide a timeline for remediation. If you prefer to remain anonymous, say so.


## Manifest integrity:
   - The baseline manifest (data/baselines/manifest.json) includes SHA256 hashes and must be verified at runtime.
   - Any change to the baseline requires creating a new manifest and signing it.

## Audit trail:
   - All gating decisions produce JSON receipts and are signed.
   - Receipts must be append-only; CI tests assert the audit log integrity.


