# lib-rigproc.sh — the rig's process hygiene (lobo#1). Sourced by every
# tool that leaves a helper or a server RUNNING in the background; not
# executable on its own. Source it AFTER lib-toolchain.sh, from the
# repo root (every tool cds there first).
#
# THE LEAK, and it is not the trap you would guess. A tool starts a
# helper with `"$WOLF" run tests/rig/dnssrv/dnssrv.lu … &` and keeps
# `$!`. But `wolf run` COMPILES the program and executes the cache
# binary beside its source, so `$!` is the DRIVER and the listener is
# its child: `kill "$dnspid"` reaps the wrapper and orphans the helper,
# which then holds its loopback port for as long as the box is up.
# Filed as lobo#1 after nineteen orphans up to 21 h old were found by
# hand. Three more were alive when ws18 opened — one 45 h old, and one
# from each of the two gauntlet runs the sprint began with, so the rate
# is EXACTLY ONE LEAK PER RUN. Those three could not be reaped by the
# fix that found them: they were launched the old way, with a relative
# `./tests/rig/...`, so their command lines carry no repo root and the
# checkout-scoped marker below could not see them.
#
# THE SECOND LEAK (ws25, the one ws18's marker could not see): the
# corpus TESTS spawn a master themselves — `os_spawn(["target/
# lobo-debug", "serve", …])`, a RELATIVE argv[0] with no root in the
# command line — and `os_kill` is SIGKILL (the runtime's `Child::
# kill`), so a test that dies at the runner's ceiling, or kills its
# master on a failure path, leaves a master the reaper is blind to and
# hands the master RESPAWNS when the reaper kills them first. Three
# lanes killed such masters by hand in one wave; one was found alive
# at this sprint's open, 5 h 30 m old, its worktree already deleted,
# two loopback listeners still held. So the rule is now two-sided:
#   * argv[0] ABSOLUTE under this root (`<root>/tests/rig/x/.lu-cache/
#     bin/x`, `<root>/target/lobo-release`, a hand's `<root>/target/
#     lobo-debug --worker N …` — the master names its hands through
#     `os_exe`, absolutely), or
#   * argv[0] RELATIVE WITH A SLASH (`target/lobo-debug`, `./lobo`)
#     and the process's WORKING DIRECTORY under this root — read off
#     /proc on linux and lsof(8) on macOS, for those candidates only.
# The tests spawn absolutely now (ws25) so the first arm sees them;
# the second arm is for the run that predates the fix, and for the
# next test that forgets. A bare name (`awk`, `ps`) is never a
# candidate, and neither is the pinned toolchain (`.wolf-bin/…`): the
# compiler is not the rig's to kill.
#
# THE RULE is sc12's idempotency rule applied to processes: a run
# leaves nothing behind, AND a run finds nothing behind. Both halves
# are the same operation at two moments, so there is one reaper and the
# caller says which moment it is. ws25 adds the ASSERTION: `rig_census`
# names what is left and fails, so a gauntlet whose last step is the
# census is RED when any step leaked — the reaper on the way out then
# cleans up, but the run was red first.
#
# THE MARKER is **argv[0], never the rest of the command line** — and
# that distinction was paid for: a first cut matched the whole cmdline
# and killed the interactive shell that had merely TYPED
# `target/lobo-release` in a command. Nothing else is ever killed: not
# the operator's editor, not another checkout, not the pinned nginx
# (which the differential harness stops by name and whose cmdline
# names no lobo path).
#
# THE ORDER (ws25): masters before hands. A master whose hand dies
# replaces it (`restarts=1` is a feature the prefork witness asserts),
# so a reaper that TERMs a hand under a live master is racing the
# supervisor it is trying to stop. The reaper TERMs the masters, waits
# for them to go (a master's TERM is `stop`: it fans out and exits),
# then TERMs what is left, then KILLs what is still there, and scans
# once more by name.
#
# PROCESS GROUPS (ws25): a runner that puts a lane in its own process
# group registers the group here (`rig_group_add`), and the exit trap
# takes the WHOLE group down — TERM, then KILL — before it reaps by
# name. That is the "kills its process group on exit and on timeout"
# half of lobo#1: the ceiling is `timeout -k` (which signals the
# group it leads), and a signal to the runner reaches the same group
# through the trap.
#
# CONCURRENCY: one run per checkout. The gauntlet's steps are
# sequential and each step's helpers are its own, so a reap at a step
# boundary can only find the PREVIOUS step's leftovers — which is the
# thing being collected. Two runs in one tree would fight; they already
# fight over target/ and every scratch directory.
rig_root="$(pwd)"
rig_groups=""

# rig_cwds <pids...> — "pid cwd" per pid, the host's way (linux: /proc;
# macOS: one lsof over the whole list). A pid that is gone prints
# nothing.
rig_cwds() {
    [ $# -gt 0 ] || return 0
    if [ -d /proc/self ]; then
        for _p in "$@"; do
            _c=$(readlink "/proc/$_p/cwd" 2> /dev/null) && echo "$_p $_c"
        done
    else
        lsof -a -d cwd -p "$(echo "$@" | tr ' ' ',')" -Fpn 2> /dev/null |
            awk '/^p/ { p = substr($0, 2) } /^n/ { print p, substr($0, 2) }'
    fi
}

# rig_table — one line per process of ours: "pid kind" where kind is
# master (a lobo without --worker), hand (a lobo with it) or helper
# (a rig program). The two arms of the marker are applied here and
# nowhere else.
rig_table() {
    _self="$$ $PPID"
    ps -axo pid=,command= 2> /dev/null | awk -v root="$rig_root" -v self="$_self" '
        BEGIN { n = split(self, s, " "); for (i = 1; i <= n; i++) mine[s[i]] = 1 }
        {
            pid = $1
            a0 = $2
            if (pid in mine) next
            if (a0 ~ /\.wolf-bin\//) next
            kind = "helper"
            if (a0 ~ /(^|\/)lobo(-debug|-release)?$/) kind = ($0 ~ / --worker /) ? "hand" : "master"
            if (index(a0, root "/") == 1) { print pid, kind; next }
            if (a0 ~ /^\// || a0 !~ /\//) next
            print pid, kind, "cwd?"
        }
    ' | {
        # the relative arm: settle the cwd question for those candidates
        _ask=""
        while read -r _pid _kind _q; do
            if [ -z "$_q" ]; then
                echo "$_pid $_kind"
            else
                _ask="$_ask $_pid"
                eval "_kind_$_pid=\$_kind"
            fi
        done
        # shellcheck disable=SC2086
        rig_cwds $_ask | while read -r _pid _cwd; do
            case "$_cwd" in
            "$rig_root" | "$rig_root"/*) eval "echo \"$_pid \$_kind_$_pid\"" ;;
            esac
        done
    }
}

rig_pids() { # rig_pids [kind] — pids of this checkout's processes (all, or one kind)
    if [ $# -gt 0 ]; then
        rig_table | awk -v k="$1" '$2 == k { print $1 }'
    else
        rig_table | awk '{ print $1 }'
    fi
}

rig_gone() { # rig_gone <tenths> [kind] — wait up to N tenths for the set to empty; 0 if it did
    _i=0
    while [ "$_i" -lt "$1" ]; do
        [ -z "$(rig_pids ${2:-})" ] && return 0
        sleep 0.1
        _i=$((_i + 1))
    done
    [ -z "$(rig_pids ${2:-})" ]
}

rig_reap() { # rig_reap <moment> — kill them, in order, and SAY SO
    _rp=$(rig_pids | tr '\n' ' ')
    _rp=${_rp% }
    [ -n "$_rp" ] || return 0
    echo "rigproc: $1 — reaping $(echo "$_rp" | wc -w | tr -d ' ') process(es): $_rp" >&2
    # masters first, and wait for them: a hand killed under a live
    # master is replaced, and the replacement is not in the list
    for _p in $(rig_pids master); do
        kill -s TERM "$_p" 2> /dev/null
    done
    rig_gone 20 master
    for _p in $(rig_pids); do
        kill -s TERM "$_p" 2> /dev/null
    done
    # a helper blocked in accept(2) never reaches its exit path: give
    # the TERM a moment, then insist
    rig_gone 10
    for _p in $(rig_pids); do
        kill -s KILL "$_p" 2> /dev/null
    done
    rig_gone 5 && return 0
    _left=$(rig_pids | tr '\n' ' ')
    echo "rigproc: $1 — still alive after TERM and KILL: $_left" >&2
    for _p in $_left; do
        kill -s KILL "$_p" 2> /dev/null
    done
}

rig_reap_stale() { # at START — whatever a PREVIOUS run left behind
    rig_reap "stale from an earlier run"
}

# rig_group_add <pgid> / rig_group_del <pgid> — the process groups of
# this tool's in-flight lanes. `timeout` leads the group it starts
# (setpgid(0, 0) unless --foreground), so a lane run as
# `timeout -k G N cmd & ; rig_group_add $!` is one group, and the
# ceiling and the trap both reach all of it.
rig_group_add() {
    rig_groups="$rig_groups $1"
}
rig_group_del() {
    rig_groups=$(printf ' %s ' "$rig_groups" | sed "s/ $1 / /" | sed 's/^ *//; s/ *$//')
}
rig_reap_groups() { # kill every registered group: TERM, a moment, KILL
    [ -n "$rig_groups" ] || return 0
    echo "rigproc: $1 — killing $(echo "$rig_groups" | wc -w | tr -d ' ') in-flight process group(s):$rig_groups" >&2
    for _g in $rig_groups; do
        kill -s TERM -- "-$_g" 2> /dev/null
    done
    sleep 0.5
    for _g in $rig_groups; do
        kill -s KILL -- "-$_g" 2> /dev/null
    done
    rig_groups=""
}

rig_reap_own() { # at EXIT — whatever THIS run started and did not stop
    rig_reap_groups "own, at exit"
    rig_reap "own, at exit"
}

# rig_census <moment> — the ASSERTION (ws25): print whatever of ours
# is still running, by name, and fail. It kills nothing; the caller
# decides (a gauntlet's last step reds, then its exit trap reaps).
rig_census() {
    _c=$(rig_pids | tr '\n' ' ')
    _c=${_c% }
    [ -n "$_c" ] || return 0
    echo "rigproc: $1 — $(echo "$_c" | wc -w | tr -d ' ') process(es) LEFT BEHIND (lobo#1):" >&2
    ps -o pid=,pgid=,etime=,command= -p "$(echo "$_c" | tr ' ' ',')" 2> /dev/null | sed 's/^/rigproc:   /' >&2
    return 1
}

# The trap every caller wants: reap on the way out, however it goes —
# a green return, a red `exit 1`, an interrupt, or the 600 s ceiling
# that killed the runs lobo#1 was filed about.
rig_arm() { # rig_arm — reap now, and again on the way out
    rig_reap_stale
    trap 'rig_reap_own' EXIT
    trap 'rig_reap_own; exit 130' INT
    trap 'rig_reap_own; exit 143' TERM
}
