#!/usr/bin/env bash
# Preview local branches merged into an explicit base. Never force-delete.
set -euo pipefail
usage() {
    echo 'Usage: clean_branches.sh --base REF [--prefix feature/] [--apply]'
}
base= prefix=feature/ apply=false
while (($#)); do
    case "$1" in
        --base|--prefix)
            (($# >= 2)) || { usage >&2; exit 2; }
            if [[ $1 == --base ]]; then base=$2; else prefix=$2; fi
            shift 2 ;;
        --apply) apply=true; shift ;;
        --help|-h) usage; exit 0 ;;
        *) usage >&2; exit 2 ;;
    esac
done
[[ -n $base && -n $prefix && $prefix == */ ]] || { usage >&2; exit 2; }
git check-ref-format "refs/heads/${prefix}example" >/dev/null
base_oid=$(git rev-parse --verify --end-of-options "${base}^{commit}")
current=$(git symbolic-ref --quiet --short HEAD || true)
# Snapshot refs before acting, and check ancestry again immediately before deletion.
refs=$(git for-each-ref --format='%(refname:short)' refs/heads/)
while IFS= read -r branch; do
    [[ $branch == "$prefix"* && $branch != "$current" ]] || continue
    oid=$(git rev-parse --verify --end-of-options "refs/heads/${branch}")
    [[ $oid != "$base_oid" ]] || { printf 'Keep base/equivalent: %s\n' "$branch"; continue; }
    if git merge-base --is-ancestor "$oid" "$base_oid"; then
        if $apply; then
            # -d retains Git's own merge/upstream and linked-worktree safeguards.
            # If another actor advances a ref, -d still refuses unmerged work.
            git branch -d -- "$branch"
        else
            printf 'Would delete merged branch: %s\n' "$branch"
        fi
    else
        status=$?
        if ((status != 1)); then exit "$status"; fi
        printf 'Keep unmerged branch: %s\n' "$branch"
    fi
done <<< "$refs"
if $apply; then echo 'Merged-branch cleanup completed.'; else echo 'Dry run; no branches changed. Use --apply after review.'; fi
