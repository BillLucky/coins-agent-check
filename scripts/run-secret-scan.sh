#!/usr/bin/env bash
set -euo pipefail
umask 077
revision=8.30.1
repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"
if [[ -n "${GITLEAKS_BIN:-}" ]]; then
  scan_bin="$GITLEAKS_BIN"
else
  cache_dir="$repo_root/.local/security-tools/gitleaks-$revision"
  mkdir -p "$cache_dir"
  case "$(uname -s):$(uname -m)" in
    Linux:x86_64) artifact="gitleaks_${revision}_linux_x64.tar.gz"; digest=551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb ;;
    Darwin:arm64) artifact="gitleaks_${revision}_darwin_arm64.tar.gz"; digest=b40ab0ae55c505963e365f271a8d3846efbc170aa17f2607f13df610a9aeb6a5 ;;
    *) echo 'Unsupported platform; supply the verified pinned GITLEAKS_BIN.' >&2; exit 2 ;;
  esac
  scan_bin="$cache_dir/gitleaks"
  if [[ ! -x "$scan_bin" ]]; then
    curl --fail --silent --show-error --location --connect-timeout 15 --max-time 90       "https://github.com/gitleaks/gitleaks/releases/download/v$revision/$artifact" -o "$cache_dir/$artifact"
    python3 - "$cache_dir/$artifact" "$digest" "$scan_bin" <<'CHECK'
import hashlib, pathlib, shutil, sys, tarfile
archive, expected, target = pathlib.Path(sys.argv[1]), sys.argv[2], pathlib.Path(sys.argv[3])
if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
    raise SystemExit('Pinned scanner archive checksum mismatch')
with tarfile.open(archive) as package:
    member = package.getmember('gitleaks')
    if not member.isfile():
        raise SystemExit('Invalid scanner archive')
    with package.extractfile(member) as source, target.open('wb') as output:
        shutil.copyfileobj(source, output)
target.chmod(0o700)
CHECK
  fi
fi
[[ "$("$scan_bin" version)" == "$revision" ]] || { echo 'Unexpected scanner version' >&2; exit 2; }
unset GITLEAKS_CONFIG GITLEAKS_CONFIG_TOML
config=()
[[ ! -f .gitleaks.toml ]] || config=(--config "$repo_root/.gitleaks.toml")
exec "$scan_bin" git --log-opts='--all --full-history' --no-banner --redact=100   --ignore-gitleaks-allow "${config[@]}" "$repo_root"
