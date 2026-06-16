#!/bin/bash
# This script automatically removes the old feature/ branches from the git workspace


echo "Removing old feature branches from workspace..."

for branch in $(git branch | grep "feature/") ; do
    echo "Deleting branch: $branch"
    git branch -D "$branch"
done

echo "Workspace is Clean!"
