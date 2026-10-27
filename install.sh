#!/usr/bin/env bash
# Installe les hooks token-diet dans un depot.
# Usage: ./install.sh [chemin]
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
target="${1:-$(pwd)}"
hooks="$target/.git/hooks"

[ -d "$target/.git" ] || { echo "pas un depot git : $target"; exit 1; }
mkdir -p "$hooks"

for h in pre-commit commit-msg; do
  chmod +x "$root/hooks/$h"
  ln -sf "$root/hooks/$h" "$hooks/$h"
  echo "hook installe : $h"
done

echo
echo "les hooks pointent vers $root/hooks/"
echo "controle : head -1 hooks/pre-commit  (doit afficher #!/usr/bin/env bash)"