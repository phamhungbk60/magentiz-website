#!/usr/bin/env bash
# Publish a preview build to the gh-pages branch (GitHub Pages).
# Served at https://<user>.github.io/<repo>/ with all pages set to noindex.
# Usage: ./deploy-preview.sh   (run from the repo root, after committing)
set -euo pipefail

repo_name=$(basename -s .git "$(git remote get-url origin)")
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

git worktree add -q --detach "$tmp" HEAD
(cd "$tmp" && BASE_PATH="/$repo_name" PREVIEW=1 python3 build.py >/dev/null)
touch "$tmp/public/.nojekyll"

cd "$tmp/public"
git init -q
git checkout -q -b gh-pages
git add -A
git commit -q -m "Preview build of $(git -C "$OLDPWD" rev-parse --short HEAD 2>/dev/null || echo main)"
git push -q -f "$(git -C "$OLDPWD" remote get-url origin)" gh-pages
cd - >/dev/null
git worktree remove --force "$tmp"
echo "Preview pushed to gh-pages."
