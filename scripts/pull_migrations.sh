#!/usr/bin/env bash
# Pull Python migration files into existing local app migration directories.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/transfer_common.sh"
transfer_usage() { echo 'Usage: pull_migrations.sh --host USER@HOST --remote-root /project [--port 22] [--apply]'; }
parse_transfer_options "$@"
cd "$(git rev-parse --show-toplevel)"
shopt -s nullglob
folders=(*/migrations)
for folder in "${folders[@]}"; do
    check_transfer_path "$folder"
    [[ ! -L $folder && ! -L ${folder%/migrations} ]] || { echo 'Refusing symlinked migration directory.' >&2; exit 1; }
done
count=0
for folder in "${folders[@]}"; do
    if $apply; then
        printf 'Pulling: %s\n' "$folder"
        scp -B -P "$port" -- "$host:$remote_root/$folder/*.py" "./$folder/"
    else
        printf 'Would pull: %s:%s/%s/*.py -> ./%s/\n' "$host" "$remote_root" "$folder" "$folder"
    fi
    count=$((count + 1))
done
if $apply; then printf 'Transferred migrations for %s app(s).\n' "$count"; else printf 'Dry run: %s app(s); no connection made.\n' "$count"; fi
