#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/.."

WORKTREE="${GH_PAGES_WORKTREE:-/tmp/come-clean-gh-pages}"

if ! git rev-parse --verify gh-pages >/dev/null 2>&1; then
    echo "No gh-pages branch. Create one once with:"
    echo "  git switch --orphan gh-pages && git commit --allow-empty -m init"
    echo "  git push -u origin gh-pages && git switch main"
    exit 1
fi

if [[ ! -f public/index.html ]]; then
    echo "No public/index.html. Build it first with: make page"
    exit 1
fi

git worktree remove --force "$WORKTREE" >/dev/null 2>&1 || true
git worktree prune
trap 'git worktree remove --force "$WORKTREE" >/dev/null 2>&1 || true' EXIT

git worktree add "$WORKTREE" gh-pages
cp public/index.html "$WORKTREE/index.html"
git -C "$WORKTREE" add index.html
if git -C "$WORKTREE" diff --cached --quiet; then
    echo "Page unchanged since last deploy."
else
    git -C "$WORKTREE" commit -m "deploy: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    git -C "$WORKTREE" push
fi
