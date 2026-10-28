#!/usr/bin/env bash
# Copy changed regular files only; preview unless explicitly applied.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/transfer_common.sh"
transfer_usage() { echo 'Usage: push_to_vps.sh --host USER@HOST --remote-root /project [--port 22] [--apply]'; }
parse_transfer_options "$@"
cd "$(git rev-parse --show-toplevel)"
if [[ -n $(git diff --name-only --diff-filter=U) ]]; then
    echo 'Resolve Git conflicts before transferring files.' >&2; exit 1
fi
paths=$(mktemp)
trap 'rm -f "$paths"' EXIT
# NUL delimiters preserve spaces; --diff-filter excludes deleted paths.
git diff --name-only -z --diff-filter=ACMRT HEAD -- > "$paths"
git ls-files --others --exclude-standard -z >> "$paths"
count=0
# Preflight every path before making any connection.
while IFS= read -r -d '' file; do
    check_transfer_path "$file"
    [[ -f $file && ! -L $file ]] || { printf 'Refusing non-regular file: %s\n' "$file" >&2; exit 1; }
done < "$paths"
while IFS= read -r -d '' file; do
    if $apply; then
        printf 'Copying: %s\n' "$file"
        scp -B -P "$port" -- "./$file" "$host:$remote_root/$file"
    else
        printf 'Would copy: %s -> %s:%s/%s\n' "$file" "$host" "$remote_root" "$file"
    fi
    count=$((count + 1))
done < "$paths"
if $apply; then printf 'Transferred %s file(s).\n' "$count"; else printf 'Dry run: %s file(s); no connection made.\n' "$count"; fi
