#!/usr/bin/env bash
# Installe les hooks token-diet dans le depot courant.
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
target="${1:-$(pwd)}"
hooks="$target/.git/hooks"

[ -d "$target/.git" ] || { echo "pas un depot git : $target"; exit 1; }
mkdir -p "$hooks"

for h in pre-commit commit-msg; do
  ln -sf "$root/hooks/$h" "$hooks/$h"
  chmod +x "$root/hooks/$h"
  echo "hook installe : $h"
done

echo "hooks token-diet actifs dans $target"