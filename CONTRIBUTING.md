# Contributing to Personal AI Infrastructure

## Core Principles

1. **Safety First**:
   Never alter working deployments on edge nodes without dry-run testing and rollback procedures.
2. **Zero Secret Policy**:
   Never commit `.env` files, API keys, passwords, database dumps, chat archives, or private tokens. All secrets must use environment variable interpolation or secure secret managers.
3. **Idempotency**:
   All provisioning, deployment, and configuration scripts must be strictly idempotent. Running them multiple times must produce the same desired state without data destruction or downtime.
4. **Upstream Pinned Dependencies**:
   Never blindly merge or copy upstream projects into this repository. Track dependencies in `upstreams/manifest.yaml` with pinned tags or commit hashes.

---

## Development Workflow

1. **Format & Lint**:
   Ensure all Python files adhere to PEP 8 and pass unit tests.
   Validate shell scripts with `shellcheck` syntax checking.
2. **Secret Scan Verification**:
   Run the local secret scanning test before creating any commit:
   ```bash
   python3 -m unittest tests/security/test_secret_leakage.py
   ```
3. **Review Architecture Boundaries**:
   Ensure that no proposed changes violate the Layer 1 (Inference) vs Layer 2 (Personal Infrastructure) isolation guarantee.
