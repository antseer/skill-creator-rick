#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/antseer/antseer-components.git"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE_ROOT="${ANTSEER_COMPONENTS_CACHE_ROOT:-${XDG_CACHE_HOME:-$HOME/.cache}/skill-creator-rick}"
CACHE_DIR="${ANTSEER_COMPONENTS_CACHE_DIR:-$CACHE_ROOT/antseer-components}"
LEGACY_CACHE_DIR="$SKILL_DIR/frontend-components/antseer-components"
BRANCH="${ANTSEER_COMPONENTS_BRANCH:-main}"

# Older local installs cached a full git checkout inside the skill package.
# That pollutes validation/release with .git and node_modules, so remove only
# the known generated checkout when this script runs.
if [ "$CACHE_DIR" != "$LEGACY_CACHE_DIR" ] && [ -d "$LEGACY_CACHE_DIR/.git" ]; then
  printf 'Removing legacy in-skill antseer-components cache: %s
' "$LEGACY_CACHE_DIR" >&2
  rm -rf "$LEGACY_CACHE_DIR"
  rmdir "$SKILL_DIR/frontend-components" 2>/dev/null || true
fi

mkdir -p "$(dirname "$CACHE_DIR")"

print_cache() {
  printf 'antseer-components cache: %s
' "$CACHE_DIR"
  printf 'remote: %s
' "$REPO_URL"
  if [ -d "$CACHE_DIR/.git" ]; then
    printf 'commit: '
    git -C "$CACHE_DIR" log -1 --format='%h %s (%ci)%n' --abbrev=12
  else
    printf 'commit: unavailable; cache is not a git checkout
'
  fi
}

if [ -d "$CACHE_DIR/.git" ]; then
  git -C "$CACHE_DIR" remote set-url origin "$REPO_URL"
  if git -C "$CACHE_DIR" fetch --prune origin "$BRANCH"; then
    LOCAL="$(git -C "$CACHE_DIR" rev-parse HEAD)"
    REMOTE="$(git -C "$CACHE_DIR" rev-parse "origin/$BRANCH")"
    if [ "$LOCAL" != "$REMOTE" ]; then
      git -C "$CACHE_DIR" checkout "$BRANCH" >/dev/null 2>&1 || git -C "$CACHE_DIR" checkout -B "$BRANCH" "origin/$BRANCH"
      git -C "$CACHE_DIR" pull --ff-only origin "$BRANCH"
    fi
    print_cache
  else
    printf 'WARNING: could not reach %s; using existing local cache.
' "$REPO_URL" >&2
    print_cache
  fi
else
  rm -rf "$CACHE_DIR"
  if git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$CACHE_DIR"; then
    print_cache
  else
    printf 'ERROR: cannot clone %s and no local cache exists.
' "$REPO_URL" >&2
    exit 1
  fi
fi
