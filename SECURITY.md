# Security and repository boundaries

This public repository contains integration documentation, public schemas and synthetic examples only. Do not submit wallet keys, seed phrases, exchange credentials, environment files, customer data, signed payment authorizations, private Idempotency-Keys or unredacted reports in issues, discussions or pull requests. The examples save purchase state under ignored `.local/` with private filesystem modes.

Report security issues privately to support@zhidun.ai with a redacted description. Never include a wallet secret or complete payment authorization. There is no promised response SLA or bug-bounty payment.

CI checks the explicit `.public-files.json` allowlist, private file paths, private-key markers and reachable Git history with a pinned, checksum-verified Gitleaks CLI. CI has read-only repository permissions and no wallet or production credentials. A clean scan is a bounded check, not proof that every possible secret or issue has been found.

The live API remains authoritative for current pricing and availability. Directory registration, tests and small usage volumes do not certify security, legal compliance or regulatory approval.
