#!/usr/bin/env bash
set -euo pipefail
OBSIDIAN_SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$OBSIDIAN_SOURCE_DIR/tools/install.py" "$@"
