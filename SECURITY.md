# Security Policy

## Overview

The NGINX Declarative API project takes security seriously. This document outlines how to report vulnerabilities, which releases receive security fixes, and what you can expect after submitting a report.

> **Note:** This is a community-supported project maintained under the [f5devcentral](https://github.com/f5devcentral) organization. It is not an official F5 product and does not carry a commercial support SLA. However, security disclosures are treated with high priority.

---

## Supported Versions

Security fixes are applied to the **latest stable release** only. We strongly encourage all users to stay on the most recent version.

| Version | Supported          |
|---------|--------------------|
| 5.5.x   | ✅ Yes (latest)    |
| 5.4.x   | ⚠️ Critical fixes only |
| < 5.4   | ❌ No              |

---

## Reporting a Vulnerability

**Please do not open a public GitHub issue to report a security vulnerability.**

If you believe you have found a security vulnerability in this project, please disclose it responsibly using one of the following channels:

### Option 1 — GitHub Private Security Advisory (Preferred)

Use GitHub's built-in private disclosure mechanism:

1. Navigate to the [Security tab](https://github.com/f5devcentral/NGINX-Declarative-API/security) of this repository.
2. Click **"Report a vulnerability"**.
3. Fill in the details of the issue, including steps to reproduce, potential impact, and any suggested mitigations.

This keeps the disclosure private until a fix is ready.

### Option 2 — F5 Security Incident Response Team (SIRT)

For vulnerabilities that may have broader impact on F5 or NGINX products used in conjunction with this project (e.g., NGINX Instance Manager, NGINX One Console, NGINX Plus, or F5 WAF for NGINX), please contact the F5 Security Incident Response Team directly:

- **Web**: [https://www.f5.com/support/report-a-vulnerability](https://www.f5.com/support/report-a-vulnerability)
- **Email**: F5SIRT@f5.com (encrypted submissions accepted via the [F5 SIRT public PGP key](https://www.f5.com/support/report-a-vulnerability))

---

## What to Include in Your Report

To help us triage and respond quickly, please include as much of the following as possible:

- A clear description of the vulnerability and its potential impact
- The affected component(s) (e.g., API endpoint, GitOps sync logic, Docker image, configuration parser)
- Steps to reproduce the issue or a proof-of-concept (PoC)
- The version(s) of NGINX Declarative API affected
- Your suggested severity rating (e.g., CVSS score if applicable)
- Any proposed mitigations or patches

---

## Scope

This security policy covers the **NGINX Declarative API application code** in this repository, including:

- The Python-based REST API service
- GitOps autosync and queue management logic
- Docker and Kubernetes deployment manifests (`contrib/`)
- Go templates used for NGINX configuration rendering (`templates/`)
- Configuration handling for NGINX Instance Manager and NGINX One Console integrations

### Out of Scope

The following are **not** in scope for this project's security policy and should be reported to their respective vendors:

- [F5 NGINX Instance Manager](https://docs.nginx.com/nginx-instance-manager/) vulnerabilities → report to [F5 SIRT](https://www.f5.com/support/report-a-vulnerability)
- [F5 NGINX One Console](https://docs.nginx.com/nginx-one/) vulnerabilities → report to [F5 SIRT](https://www.f5.com/support/report-a-vulnerability)
- [F5 NGINX Plus](https://docs.nginx.com/nginx/) vulnerabilities → report to [F5 SIRT](https://www.f5.com/support/report-a-vulnerability)
- [F5 WAF for NGINX](https://docs.nginx.com/waf/) vulnerabilities → report to [F5 SIRT](https://www.f5.com/support/report-a-vulnerability)
- Third-party dependencies (Redis, Moesif, Redocly, Backstage) → report to respective maintainers

---

## Security Best Practices for Deployers

When deploying NGINX Declarative API, we recommend the following:

- **Network exposure**: Do not expose the NGINX Declarative API directly to the public internet. Place it behind a network boundary or API gateway with appropriate access controls.
- **Authentication**: Ensure that access to the REST API is protected with strong authentication. The API has privileged access to your NGINX infrastructure.
- **TLS**: Always use TLS for communication between clients and the NGINX Declarative API service, as well as between the service and NGINX Instance Manager / NGINX One Console.
- **Secrets management**: Do not store credentials, API keys, or TLS private keys in plaintext configuration files or environment variables. Use a secrets manager appropriate to your environment (e.g., Kubernetes Secrets with encryption at rest, HashiCorp Vault).
- **Container images**: Always use official or internally verified Docker images. Regularly scan images for known CVEs using tools such as Trivy, Grype, or Docker Scout.
- **Source of Truth security**: When using GitOps autosync, ensure that your source-of-truth repository (containing WAF policies, TLS certificates, and NGINX snippets) has appropriate access controls and audit logging.
- **Least privilege**: Run the API service container with a non-root user and minimal Linux capabilities.
- **Keep dependencies updated**: Regularly update Python dependencies (`requirements.txt`) and base Docker images to pull in upstream security patches.

---

## Disclosure Policy

We follow a **coordinated disclosure** model. We ask that reporters:

1. Give us reasonable time to investigate and patch before public disclosure.
2. Avoid exploiting the vulnerability beyond what is necessary to demonstrate the issue.
3. Do not access, modify, or delete data belonging to others.

In return, we commit to:

1. Acknowledging your report promptly.
2. Keeping you informed throughout the remediation process.
3. Crediting you in the release notes (unless you prefer to remain anonymous).

---

## License

This project is licensed under the [Apache License, Version 2.0](LICENSE.md). Security contributions and disclosures are welcomed under the same spirit of open collaboration.
