#!/usr/bin/env bash
#
# sync.sh — land a zip of files from Claude into the repo, commit, push.
#
# Usage:
#   ./sync.sh <path-to-zip> "commit message"
#   ./sync.sh <path-to-zip> "commit message" --dry-run
#
# Run from the repo root. Expects the zip's internal paths to already be
# relative to repo root (e.g. app/main.py), which is how Claude will build
# them.
#
# Commit message convention: "<phase>: <what changed>", present tense,
# lower case, no trailing full stop. E.g. "phase 1: add labour extraction"

set -euo pipefail

log() {
    printf '%s | %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1"
}

fail() {
    log "ERROR: $1"
    exit 1
}

usage() {
    echo "Usage: $0 <path-to-zip> \"commit message\" [--dry-run]"
    exit 1
}

# --- argument parsing ---

[ $# -lt 2 ] && usage

ZIP_PATH="$1"
COMMIT_MSG="$2"
DRY_RUN=false

if [ "${3:-}" = "--dry-run" ]; then
    DRY_RUN=true
fi

# --- preflight checks ---

[ -f "$ZIP_PATH" ] || fail "zip not found: $ZIP_PATH"

[ -d ".git" ] || fail "not at repo root (no .git found). cd into the repo first."

# Prefer unzip if present (Linux/macOS usually have it). Git for Windows does
# not bundle unzip by default, but does bundle bsdtar, which extracts .zip
# files fine via `tar -xf`. Pick whichever is available.
EXTRACT_CMD=""
if command -v unzip >/dev/null 2>&1; then
    EXTRACT_CMD="unzip"
elif command -v tar >/dev/null 2>&1; then
    EXTRACT_CMD="tar"
else
    fail "neither unzip nor tar found. Git Bash should have tar bundled — check your Git for Windows install."
fi

if [ -n "$(git status --porcelain)" ]; then
    log "WARNING: working tree is not clean before extraction. existing uncommitted changes:"
    git status --short
    read -r -p "Continue anyway? [y/N] " REPLY
    [[ "$REPLY" =~ ^[Yy]$ ]] || fail "aborted by user."
fi

# --- extract ---

log "extracting $ZIP_PATH into $(pwd) (using $EXTRACT_CMD)"
if [ "$EXTRACT_CMD" = "unzip" ]; then
    unzip -o "$ZIP_PATH" -d . > /tmp/sync_unzip.log 2>&1 \
        || fail "unzip failed, see /tmp/sync_unzip.log"
else
    tar -xf "$ZIP_PATH" -C . > /tmp/sync_unzip.log 2>&1 \
        || fail "tar extraction failed, see /tmp/sync_unzip.log"
fi
log "extraction done"

# --- show what changed ---

log "changes to be committed:"
git add -A
git status --short

if [ -z "$(git diff --cached --name-only)" ]; then
    fail "nothing changed after extraction — zip may already be applied, or paths didn't match repo layout."
fi

if [ "$DRY_RUN" = true ]; then
    log "dry run — stopping before commit. run without --dry-run to commit and push."
    git reset > /dev/null
    exit 0
fi

# --- confirm before push ---

read -r -p "Commit as \"$COMMIT_MSG\" and push to origin main? [y/N] " REPLY
if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
    log "aborted before commit. changes are staged but not committed — review with git status."
    exit 0
fi

git commit -m "$COMMIT_MSG" || fail "commit failed"
log "committed: $(git rev-parse --short HEAD)"

git push origin main || fail "push failed. commit is local — retry push manually with: git push origin main"
log "pushed to origin main"
log "done. Streamlit Community Cloud redeploys automatically from origin/main."
