#!/usr/bin/env bash
# Shared argument validation; sourced by the two transfer scripts.
parse_transfer_options() {
    host= remote_root= port=22 apply=false
    while (($#)); do
        case "$1" in
            --host|--remote-root|--port)
                (($# >= 2)) || { transfer_usage >&2; return 2; }
                case "$1" in
                    --host) host=$2 ;; --remote-root) remote_root=$2 ;; --port) port=$2 ;;
                esac
                shift 2 ;;
            --apply) apply=true; shift ;;
            --help|-h) transfer_usage; exit 0 ;;
            *) transfer_usage >&2; return 2 ;;
        esac
    done
    [[ $host =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.@-]*$ && $host != *@*@* ]] || { echo 'An explicit hostname or user@hostname is required.' >&2; return 2; }
    [[ $remote_root == /* && $remote_root != / && $remote_root != *'..'* && $remote_root =~ ^[a-zA-Z0-9_./\ -]+$ ]] || { echo 'Use an absolute remote project path with letters, numbers, spaces, _, . or -; no .. components.' >&2; return 2; }
    [[ $port =~ ^[0-9]{1,5}$ ]] && ((10#$port >= 1 && 10#$port <= 65535)) || { echo 'Port must be 1..65535.' >&2; return 2; }
    remote_root=${remote_root%/}
}
check_transfer_path() {
    # Conservative remote-path alphabet also avoids legacy remote-shell metacharacters.
    [[ $1 =~ ^[a-zA-Z0-9_./\ -]+$ && $1 != *'..'* ]] || { printf 'Unsupported transfer path: %q\n' "$1" >&2; return 2; }
}
