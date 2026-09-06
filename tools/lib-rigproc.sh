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
# checkout-scoped marker below cannot see them. They were killed by
# hand, once. Every helper started after this file exists carries the
# absolute form and is collectable.
#
# THE RULE is sc12's idempotency rule applied to processes: a run
# leaves nothing behind, AND a run finds nothing behind. Both halves
# are the same operation at two moments, so there is one reaper and the
# caller says which moment it is.
#
# THE MARKER is **argv[0], never the rest of the command line** — and
# that distinction was paid for: a first cut matched the whole cmdline
# and killed the interactive shell that had merely TYPED
# `target/lobo-release` in a command. A process is ours when the
# program it is RUNNING is one of the two things a step starts, and
# when this repo's root appears somewhere in its command line:
#   * a rig helper — `<root>/tests/rig/<name>/.lu-cache/bin/<name>`.
#     The launch sites pass an ABSOLUTE program path for exactly this
#     reason: `wolf run ./tests/rig/x.lu` leaves a RELATIVE cmdline
#     that matches every lobo tree on the host, and a reaper that kills
#     by a bare name is worse than the leak it collects.
#   * a lobo under test — `<root>/target/lobo-debug` or
#     `<root>/target/lobo-release`. Every tool that starts one names it
#     absolutely (`$rig_root/target/...`), which is a change this file
#     made rather than an assumption it relies on: a relative `LOBO=`
#     left a cmdline with no root in it, and a server leaked from a
#     killed step would then be invisible to the same reaper that
#     collects the helpers beside it.
# Nothing else is ever killed: not the operator's editor, not another
# checkout, not the pinned nginx (which the differential harness stops
# by name and whose cmdline names no lobo path).
#
# CONCURRENCY: one run per checkout. The gauntlet's steps are
# sequential and each step's helpers are its own, so a reap at a step
# boundary can only find the PREVIOUS step's leftovers — which is the
# thing being collected. Two runs in one tree would fight; they already
# fight over target/ and every scratch directory.
rig_root="$(pwd)"

rig_pids() { # rig_pids — pids of this checkout's helpers and servers
    ps -axo pid=,command= 2> /dev/null | awk -v root="$rig_root" '
        {
            a0 = $2
        }
        a0 !~ /\/\.lu-cache\/bin\/[^\/]+$/ && a0 !~ /(^|\/)target\/lobo-(debug|release)$/ { next }
        index($0, root) == 0 { next }
        { print $1 }
    '
}

rig_reap() { # rig_reap <moment> — kill them, and SAY SO
    _rp=$(rig_pids | tr '\n' ' ')
    _rp=${_rp% }
    [ -n "$_rp" ] || return 0
    echo "rigproc: $1 — reaping $(echo "$_rp" | wc -w | tr -d ' ') process(es): $_rp" >&2
    for _p in $_rp; do
        kill -TERM "$_p" 2> /dev/null
    done
    # a helper blocked in accept(2) never reaches its exit path: give
    # the TERM a tenth of a second, then insist
    sleep 0.1
    for _p in $(rig_pids); do
        kill -9 "$_p" 2> /dev/null
    done
}

rig_reap_stale() { # at START — whatever a PREVIOUS run left behind
    rig_reap "stale from an earlier run"
}

rig_reap_own() { # at EXIT — whatever THIS run started and did not stop
    rig_reap "own, at exit"
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
