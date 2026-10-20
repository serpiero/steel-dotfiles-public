#!/usr/bin/env bash
set -euo pipefail
STEEL_SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$STEEL_SOURCE_DIR"
python3 tools/audit-export.py
if ! command -v gh >/dev/null; then printf '%s\n' 'Install github-cli and run gh auth login.' >&2; exit 1; fi
gh auth status
STEEL_REPO='serpiero/steel-dotfiles-public'
STEEL_VISIBILITY="$(gh repo view "$STEEL_REPO" --json visibility --jq .visibility)"
if [[ "$STEEL_VISIBILITY" != PUBLIC ]]; then printf '%s\n' 'Expected the separate PUBLIC repository; stopped.' >&2; exit 1; fi
if [[ -n "$(git status --porcelain)" ]]; then printf '%s\n' 'Commit reviewed source changes before publishing.' >&2; exit 1; fi
git push "https://github.com/$STEEL_REPO.git" HEAD:refs/heads/main
