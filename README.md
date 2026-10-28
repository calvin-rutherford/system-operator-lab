# System Operator Lab

Small Bash exercises for local Git cleanup and explicit file transfers. These are
learning utilities, not a deployment system or a database migration runner.
Requires Bash, Git and OpenSSH; the checks use Python 3's standard library.

## Clean merged local branches

Run from the Git repository you intend to inspect. The base is required, and the
default is a preview:

```sh
/path/to/scripts/clean_branches.sh --base main
/path/to/scripts/clean_branches.sh --base main --prefix feature/ --apply
```

Only local branches beginning with the literal prefix are considered. The script
checks commit ancestry against the selected base, skips the current branch and
branches equal to that base, and uses `git branch -d`, never force deletion.
Git can additionally refuse a branch because its upstream differs or because it
is checked out in another worktree. Such failures return nonzero; inspect them
rather than adding `-D`. No remote fetch, remote deletion or age heuristic occurs.
The preview is a snapshot; review the repository and base again before applying.

## Transfer files explicitly

Both scripts require a host and absolute remote project directory. Run from the
local Git project; paths are resolved from its root. Preview does not connect.
These examples use a reserved example hostname; substitute your own configured
SSH host only after reviewing the preview.

```sh
/path/to/scripts/push_to_vps.sh --host user@example.invalid --remote-root /srv/project
/path/to/scripts/pull_migrations.sh --host user@example.invalid --remote-root /srv/project
# Add --port PORT if needed, and --apply only when ready to copy.
```

- `push_to_vps.sh` selects tracked changes relative to HEAD and non-ignored
  untracked files. NUL delimiters preserve spaces and renamed destinations.
  Deleted files are not transferred or deleted remotely. Conflicts, symlinks and
  unsupported paths are refused before connecting. A remote destination directory
  must already exist; the script does not create directories or deploy services.
- `pull_migrations.sh` copies `*.py` from the remote counterpart of each existing
  local `*/migrations` directory. It does not execute migrations or commit them.
- Apply can overwrite corresponding files. Inspect local changes and back up any
  files you need before copying; review the resulting diff before committing.
- Use modern OpenSSH with its default SFTP transport (OpenSSH 9+). Do not force
  legacy SCP mode. Paths support letters, numbers, spaces, `_`, `.`, `/` and `-`;
  shell metacharacters and `..` are refused. IPv6 literals are not supported.
- Batch mode prevents interactive password prompts. SCP errors remain visible and
  stop execution with nonzero status. A multi-file transfer is not atomic: earlier
  files may already have copied when a later file fails. No success summary is
  printed on failure. No personal username, port or home directory is embedded.

## Validate without real hosts

```sh
bash -n scripts/*.sh
python3 -m unittest discover -s tests -v
```

The tests create disposable temporary Git repositories, including unmerged
branches and linked worktrees. Transfers use a fake `scp` executable that records
arguments and simulates failures. They do not connect to hosts or touch branches
in a working project. Passing them establishes these bounded script behaviors,
not a live transfer or production deployment.
