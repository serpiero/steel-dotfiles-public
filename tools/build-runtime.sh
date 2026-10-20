#!/usr/bin/env bash
set -euo pipefail
OBSIDIAN_SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
OBSIDIAN_BUILD_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/obsidian-build/quickshell"
OBSIDIAN_QS_REV="4f508be500dea6e5732cc3d50382a0048b17e7b1"
OBSIDIAN_DEST="${1:?Pass the output executable path}"
mkdir -p "$(dirname -- "$OBSIDIAN_BUILD_DIR")" "$(dirname -- "$OBSIDIAN_DEST")"
if [[ ! -d "$OBSIDIAN_BUILD_DIR/.git" ]]; then
 git clone https://github.com/quickshell-mirror/quickshell.git "$OBSIDIAN_BUILD_DIR"
fi
if [[ "$(git -C "$OBSIDIAN_BUILD_DIR" rev-parse HEAD)" != "$OBSIDIAN_QS_REV" ]]; then
 if [[ -n "$(git -C "$OBSIDIAN_BUILD_DIR" status --porcelain)" ]]; then
  printf '%s\n' 'Build checkout has changes; preserve it and use a fresh cache directory.' >&2; exit 1
 fi
 git -C "$OBSIDIAN_BUILD_DIR" checkout --detach "$OBSIDIAN_QS_REV"
fi
if git -C "$OBSIDIAN_BUILD_DIR" apply --check "$OBSIDIAN_SOURCE_DIR/web-runtime/source.patch"; then
 git -C "$OBSIDIAN_BUILD_DIR" apply "$OBSIDIAN_SOURCE_DIR/web-runtime/source.patch"
elif ! git -C "$OBSIDIAN_BUILD_DIR" apply --reverse --check "$OBSIDIAN_SOURCE_DIR/web-runtime/source.patch"; then
 printf '%s\n' 'Runtime patch does not match the pinned source.' >&2;exit 1
fi
cmake -S "$OBSIDIAN_BUILD_DIR" -B "$OBSIDIAN_BUILD_DIR/build-obsidian" -G Ninja \
 -DCMAKE_BUILD_TYPE=Release -DCRASH_HANDLER=OFF -DDISTRIBUTOR=Steel \
 -DCRASHREPORT_URL=https://github.com/serpiero/steel-dotfiles/issues
cmake --build "$OBSIDIAN_BUILD_DIR/build-obsidian" --parallel "${OBSIDIAN_BUILD_JOBS:-2}"
install -m755 "$OBSIDIAN_BUILD_DIR/build-obsidian/src/quickshell" "$OBSIDIAN_DEST"
