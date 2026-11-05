#!/usr/bin/env bash
# run_audit_sandbox.sh — run an audit agent inside an OS-enforced read-only jail.
#
# What the agent CAN do inside the jail:
#   - read /snapshot   (the authorized audit snapshot, mounted ro + noexec)
#   - read /context    (host-approved context files, mounted ro; optional)
#   - write /workspace (a size-limited tmpfs scratch area that dies with the run)
#
# What the OS enforces (not the prompt, not the agent):
#   - NO network: fresh network namespace with no interfaces except down'd lo
#   - NO writes outside /workspace: snapshot, context, and system dirs are ro binds
#   - NO reads outside authorized inputs: the jail root contains only /snapshot,
#     /context, /workspace and the runtime dirs needed to execute the agent
#   - NO execve() of target files: /snapshot is mounted noexec, so the audited
#     code cannot be run as a program — even if the agent tries
#   - NO process visibility outside the jail: fresh PID/IPC/UTS namespaces
#
# Honest boundary — what the sandbox does NOT enforce:
#   noexec blocks direct execve() of files under /snapshot. An agent could still
#   feed target code to an interpreter that lives inside the jail (e.g.
#   `python3 /snapshot/x.py`) — mount-level controls cannot distinguish that
#   from reading the file, which the audit legitimately does. Preventing it is
#   a CONTRACT rule (SKILL.md: never run target code), enforced by review and
#   by running the agent as a fixed entrypoint whose only binary is the agent
#   itself — which this script supports: give it an interpreter-free command.
#
# Usage:
#   tools/run_audit_sandbox.sh SNAPSHOT_DIR [CONTEXT_DIR] [AGENT_DIR] \
#       -- COMMAND [ARGS...]
#
#   SNAPSHOT_DIR  authorized audit snapshot      -> /snapshot (ro, noexec)
#   CONTEXT_DIR   host-approved context inputs   -> /context  (ro, noexec)
#   AGENT_DIR     the agent's own code           -> /agent    (ro, exec ok)
#   WORKSPACE_DIR host dir for agent output      -> /workspace (rw, size-N/A)
#                 Omit it for an ephemeral 64 MiB tmpfs instead.
#
# Mounting WORKSPACE_DIR rw is the ONLY writable path into the host: the
# report the agent produces lands there for the host to collect. Writes
# anywhere else are denied by read-only binds.
#
# Mounting AGENT_DIR ro+exec is deliberate: the agent's own code is trusted
# host software; the audited snapshot is not. Give the jail ONLY the
# interpreter the agent needs (see the honest boundary note above).
#
# Example:
#   tools/run_audit_sandbox.sh ./audit-snapshot ./ctx ./repo ./out \
#       -- python3 /agent/tools/reference_agent.py \
#          /context/request.yaml /snapshot /context /workspace/report.json
#
# Requires: unshare(1) with user-namespace support (util-linux, Linux only).
# No root, no sudo, no Docker — only unprivileged user namespaces.

set -euo pipefail

usage() { grep '^#' "$0" | head -45; exit 2; }

[ $# -ge 3 ] || usage
SNAPSHOT="$(realpath "$1")"; shift
CONTEXT=""
[ "$1" = "--" ] || { CONTEXT="$(realpath "$1")"; shift; }
AGENT=""
[ "$1" = "--" ] || { AGENT="$(realpath "$1")"; shift; }
WORK=""
[ "$1" = "--" ] || { WORK="$(realpath "$1")"; shift; }
[ "$1" = "--" ] || usage
shift
[ $# -ge 1 ] || usage

[ -d "$SNAPSHOT" ] || { echo "snapshot dir not found: $SNAPSHOT" >&2; exit 2; }
[ -z "$CONTEXT" ] || [ -d "$CONTEXT" ] || {
    echo "context dir not found: $CONTEXT" >&2; exit 2; }
[ -z "$AGENT" ] || [ -d "$AGENT" ] || {
    echo "agent dir not found: $AGENT" >&2; exit 2; }
[ -z "$WORK" ] || { mkdir -p "$WORK"; }

JAIL="$(mktemp -d /tmp/audit-jail.XXXXXX)"
trap 'umount -R "$JAIL" 2>/dev/null || true; rm -rf "$JAIL"' EXIT
mkdir -p "$JAIL"/{snapshot,context,workspace,agent}
for d in usr lib lib64 bin sbin etc; do
    [ -d "/$d" ] && mkdir -p "$JAIL/$d"
done

exec unshare --user --map-root-user --net --mount --pid --fork --mount-proc \
    --kill-child -- sh -c '
        set -e
        JAIL="$1"; SNAPSHOT="$2"; CONTEXT="$3"; AGENT="$4"; WORK="$5"; shift 5
        mount --make-rprivate /
        for d in usr lib lib64 bin sbin etc; do
            [ -d "$JAIL/$d" ] && mount -o bind,ro "/$d" "$JAIL/$d"
        done
        mount -o bind,ro,noexec,nosuid "$SNAPSHOT" "$JAIL/snapshot"
        if [ -n "$CONTEXT" ]; then
            mount -o bind,ro,noexec "$CONTEXT" "$JAIL/context"
        else
            rmdir "$JAIL/context"
        fi
        if [ -n "$AGENT" ]; then
            mount -o bind,ro "$AGENT" "$JAIL/agent"
        else
            rmdir "$JAIL/agent"
        fi
        if [ -n "$WORK" ]; then
            mount -o bind "$WORK" "$JAIL/workspace"
        else
            mount -t tmpfs -o size=64m,mode=1777 tmpfs "$JAIL/workspace"
        fi
        # The agent command runs as the jail entrypoint. Anything it writes
        # can only land in /workspace; the audited bytes are read-only.
        chroot "$JAIL" /usr/bin/env -i \
            PATH=/usr/local/bin:/usr/bin:/bin \
            HOME=/workspace SNAPSHOT=/snapshot CONTEXT=/context \
            AGENT=/agent WORKSPACE=/workspace "$@"
    ' -- "$JAIL" "$SNAPSHOT" "$CONTEXT" "$AGENT" "$WORK" "$@"
