# Security Policy

## Supported Versions

We actively maintain and provide security patches for the following versions of **ChessReview**:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0.0 | :x:                |

---

## Reporting a Vulnerability

The ChessReview team takes security seriously. If you discover a security vulnerability, **please do not open a public issue or discussion**.

Instead, please report vulnerabilities responsibly via:

* **Email:** [security@chessreview.dev](mailto:security@chessreview.dev)
* **GitHub Private Advisory:** Navigate to the **Security** tab of this repository and select **Report a vulnerability**.

### What to Include
To help us triage and resolve the issue quickly, please include:
1. Description of the vulnerability and potential impact.
2. Step-by-step reproduction instructions or a minimal Proof of Concept (PoC).
3. Affected components (Backend API, Stockfish subprocess invocation, Frontend, Docker setup).
4. Any potential mitigations or suggested fixes.

### Response Timeline
* **Initial Triage:** Within 48 hours.
* **Status Update & Remediation Plan:** Within 5 business days.
* **Public Disclosure:** Coordinated after a patched release is published.

---

## Security Practices in ChessReview

* **Container Isolation:** Backend containers run under a non-root `appuser` (UID 10001).
* **Process Security:** Stockfish subprocesses are launched with timeout bounds and sanitization.
* **CORS Hardening:** Configurable origins prevent unauthorized cross-domain API access in production.
* **Secret Hygiene:** Environment variables are strictly kept out of version control via `.env.example` templates and pre-commit checks.

