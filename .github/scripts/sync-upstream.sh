#!/usr/bin/env bash
# Mirror official ExifTool master while keeping this repository's CI controls.
# Upstream commit -> normal descendant mirror commit; never force-push.
set -euo pipefail

UPSTREAM_URL="https://github.com/exiftool/exiftool.git"
UPSTREAM_BRANCH="master"
STATUS_FILE=".github/sync/upstream-head.sha"
CONTROLS=(
  ".github/workflows/auto-sync-release.yml"
  ".github/scripts/sync-upstream.sh"
  ".github/scripts/package-portable.py"
  ".github/docs/BUILD.md"
)

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git remote add official "$UPSTREAM_URL" 2>/dev/null || git remote set-url official "$UPSTREAM_URL"
git -c http.version=HTTP/1.1 fetch --no-tags --depth=1 official "refs/heads/${UPSTREAM_BRANCH}"
new_sha="$(git rev-parse FETCH_HEAD)"
old_sha="$(cat "$STATUS_FILE" 2>/dev/null || true)"
echo "source_sha=$new_sha" >> "$GITHUB_OUTPUT"

if [[ "$new_sha" == "$old_sha" ]]; then
  echo "changed=false" >> "$GITHUB_OUTPUT"
  echo "mirror_sha=$(git rev-parse HEAD)" >> "$GITHUB_OUTPUT"
  echo "Upstream unchanged at $new_sha. No new build needed."
  exit 0
fi

overlay="$(mktemp -d)"
trap 'rm -rf "$overlay"' EXIT
for file in "${CONTROLS[@]}"; do
  test -f "$file" || { echo "Missing CI control: $file" >&2; exit 1; }
  mkdir -p "$overlay/$(dirname "$file")"
  cp "$file" "$overlay/$file"
done

# Preserve upstream code verbatim; local automation lives only under .github.
git read-tree --reset -u FETCH_HEAD
for file in "${CONTROLS[@]}"; do
  mkdir -p "$(dirname "$file")"
  cp "$overlay/$file" "$file"
done
# Avoid importing unreviewed upstream GitHub workflow definitions.
find .github/workflows -maxdepth 1 -type f ! -name auto-sync-release.yml -delete
mkdir -p "$(dirname "$STATUS_FILE")"
printf '%s\n' "$new_sha" > "$STATUS_FILE"

git add -A
if ! git diff --cached --quiet; then
  git commit -m "chore(mirror): synchronize ExifTool upstream (${new_sha:0:12})"
  git push origin HEAD:master
fi
echo "changed=true" >> "$GITHUB_OUTPUT"
echo "mirror_sha=$(git rev-parse HEAD)" >> "$GITHUB_OUTPUT"
echo "Mirrored official master $new_sha -> $(git rev-parse HEAD)"
