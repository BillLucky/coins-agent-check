#!/usr/bin/env python3
"""Reject private material paths and unexpected files in the public export.

This complements Gitleaks; neither check is a proof that every secret is absent.
Only paths/rule names are reported, never matching values or file contents.
"""
import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess


def forbidden(name):
    p = PurePosixPath(name)
    if any(part in {".local", ".runtime", ".worktrees", ".ssh", ".aws", ".gnupg", "private", "data", "snapshots", "node_modules"} for part in p.parts):
        return True
    if (p.name.startswith(".env") or re.search(r"\.env(?:\.|$)", p.name)) and not p.name.endswith(".env.example"):
        return True
    if p.name in {"id_rsa", "id_ed25519", "id_ecdsa", ".netrc", ".pypirc"}:
        return True
    if re.search(r"\.(pem|key|keystore|p12|pfx|jks|sqlite(?:-wal|-shm)?|log)$", p.name, re.I):
        return True
    if re.fullmatch(r"(?:state|payment|authorization|buyer-preview|wallet-addresses)(?:[.-][^.]+)*\.(json|txt)", p.name, re.I):
        return True
    return False


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--include-untracked", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    flags = ["--cached", "--others", "--exclude-standard"] if args.include_untracked else ["--cached"]
    names = set(git(root, "ls-files", "-z", *flags).decode().split("\0")) - {""}
    errors = [{"path": name, "rule": "private_material_path"} for name in sorted(names) if forbidden(name)]
    for name in sorted(names):
        path = root / name
        if path.is_symlink():
            errors.append({"path": name, "rule": "symlink_requires_review"})
        if path.is_file() and path.stat().st_size < 2_000_000:
            data = path.read_bytes()
            if re.search(rb"(?m)^-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----\s*$", data):
                errors.append({"path": name, "rule": "private_key_material"})
            if re.search(rb"https://open\.feishu\.cn/open-apis/bot/v2/hook/[a-fA-F0-9-]{36}", data):
                errors.append({"path": name, "rule": "private_feishu_webhook"})
    required_ignores = [".env", ".env.local", "service.env", "compose.env", ".local/state.json", "docs/private/check.json", ".runtime/payments.sqlite", "example.key"]
    for name in required_ignores:
        if subprocess.run(["git", "check-ignore", "-q", name], cwd=root).returncode:
            errors.append({"path": name, "rule": "missing_ignore_rule"})
    manifest = root / ".public-files.json"
    if manifest.exists():
        allowed = set(json.loads(manifest.read_text())["files"])
        for name in sorted(names - allowed):
            errors.append({"path": name, "rule": "not_in_public_export_manifest"})
        for name in sorted(allowed - names):
            errors.append({"path": name, "rule": "missing_public_export_file"})
    print(json.dumps({"filesChecked": len(names), "publicManifestEnforced": manifest.exists(), "findings": errors}))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
