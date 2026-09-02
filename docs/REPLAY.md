# Replay the race (ws11)

A concurrency bug is normally a war story: "it failed once under load,
never on my laptop." In this repo it is an ARTIFACT — a schedule you
can attach to a bug report and a maintainer can replay, byte for byte,
as many times as it takes. This page is the workflow, the pieces that
make it work, and — first, because everything else is bounded by it —
the exact line between what is replayable here and what is not.

## The honesty boundary (read this before trusting a replay)

The deterministic scheduler is **lupin's** (`--seed`, `--schedule`,
`conform-run --explore` — the book's ch17 is the reader's tour). It
owns every scheduling decision **of a program running under lupin**:
every channel send/receive, `select`, spawn and join is a decision it
can pin with a seed, replay from that seed, and exhaustively permute
under `--explore` (DPOR, with the frontier's open/closed status stated
in the verdict). Three kinds of nondeterminism are OUTSIDE that space,
and each bounds what lobo can promise:

- **Values.** A seed replays scheduling decisions, not data. Hash
  seeds, OS identifiers, timestamps, request payloads — exploring
  schedules never varies them. Fuzzing and the corpus own that axis.
- **Real time.** Under the seeded scheduler time is virtualized; a
  replay validates the HANDLING of a timeout, never its calibration.
  Wall-clock questions belong to a load test against a real peer.
- **The membrane.** Anything the interpreter cannot see into: the OS,
  real sockets' peers, a spawned NATIVE binary. lobo's e2e suites
  (`drain_watch`, the signal witness, the differential) drive the
  real `target/lobo-debug` over real loopback TCP — that execution is
  the machine's, **not seed-replayable**, and this repo does not
  pretend otherwise.

And the direct consequence for the server itself: **lobo is
spawn-free** (D7 — one poll loop, no tasks), so a running lobo makes
no lupin-scheduling decisions at all. Its "schedule" is the ARRIVAL
ORDER of outside events — accepts, closes, reloads, signals — at the
loop. lobo therefore **never prints a seed**: it never draws one, and
a seed in the run banner would promise a replay the server cannot
deliver (a replay that is "usually the same" is worse than none).
What lobo's own surfaces honestly carry instead:

- **The event stream, ordered and gap-visible.** Every vocabulary
  event (docs/DRAIN.md) carries `seq=N` — the loop's own emission
  ordinal. An attached log excerpt is thereby a total order over the
  events that decided the outcome, and a hole (a level-gated mirror,
  a counted drop) shows as a seq gap, never a silent absence.
- **The completeness anchor.** `lobo status` prints `events: N` (and
  the JSON stanza `"events":N`): the highest seq emitted. A report
  whose log tops out at `seq=N` with status saying `events: N` is a
  complete window.
- **No production flight recorder** — stated plainly, the ch17
  posture: recording a live service's real schedule for offline
  replay is a different mechanism with a different cost, and neither
  wolf nor lobo has it (the contract's Tier 2; deferral recorded,
  asks filed upstream). What a production incident hands you is the
  seq-ordered event log plus status — enough to RECONSTRUCT the
  decisive order in the rig's model, which is exactly what the
  workflow below automates for the drain shapes.

One sentence, both halves load-bearing: **exploration proves ordering
properties over the events it can see and permute — and the events it
can see are the rig's model programs' channel operations, selects,
spawns and joins, which is where lobo's ordering bugs live.**

## The two-command workflow

A schedule-dependent finding always arrives carrying its own
reproduction:

```console
$ .wolf-bin/lupin conform-run <case>.lu --explore=500
<case>.lu: explored 16 schedule(s) in 16 execution(s) (DPOR; ...), frontier closed
  outcomes: 3 distinct — SCHEDULE-DEPENDENT
    ...
    exit(0) ×6 stdout=... — replay: --seed=4611686018427387922
      decision stream: ev:0,0,0,0,1
$ .wolf-bin/lupin run <case>.lu --seed=4611686018427387922
```

Command one finds; command two replays, forever, on any machine at
the pinned toolchain. Hand somebody the SEED when they need a number;
hand them the DECISION STREAM (`--schedule=ev:0,0,0,0,1`, the same
run) when they need to READ the counterexample — the stream is the
schedule in diffable form, and comparing it against a passing one
says which decisions differ before you read a line of code.

## The rig surfaces

- **`//! explore: N`** (tests/replay/, the corpus runner): the file's
  whole schedule space explored on every gauntlet run. Green requires
  agreement AND a CLOSED frontier — an open frontier is red even when
  every explored schedule agrees, because a verdict conditional on
  its budget is not a verdict. A dependent outcome is red with the
  explorer's replay lines printed.
- **`LOBO_SEED=<seed> tools/lobo-corpus`**: every lupin-lane run adds
  `--seed=$LOBO_SEED` — rerun the suite under the seed a bug report
  names. A failure prints the exact replay command. (A debugging
  posture, not a gate: the FIFO-pinned directives are pinned for the
  unseeded default.)
- **`tools/lobo-replay`** (a gauntlet step): the end-to-end witness,
  every run. It explores the PLANTED race, requires the finding,
  captures the failing schedule as a `.loborace` artifact, replays it
  from the artifact — twice by seed, once by decision stream, all
  three byte-identical against the artifact's recorded bytes — and
  then explores the FIXED twin to a closed one-outcome frontier.

## The specimen pair (tests/replay/)

`drain_finish_race.lu` keeps the ws08 drain-finish hazard alive as a
model: generation 1 draining two held connections, and a collector
that decides "retired" by RACING the shutdown-timeout message against
the close events in one `select`. The composite "count every close,
then retire" was never atomic against the two message kinds that
decide it. Its stdout is the log excerpt a bug report would carry —
lobo's real vocabulary builders, seq-stamped:

```
lobo: [notice] generation-draining gen=1 held=2 seq=1
lobo: [notice] connection-retired gen=1 remaining=1 seq=2
lobo: [notice] generation-retired gen=1 drained=1 aborted=1 age-ms=0 seq=3
```

Read the seq stream and the bug is visible before the code is: the
retirement at `seq=3` arrived while `remaining=1` — a close was still
outstanding. Under strict FIFO (any unseeded run — a developer's
laptop) the drain is always clean; eight of sixteen inequivalent
schedules are clean too. The machine's own schedules cluster at the
FIFO end, which is why this class "never reproduces".

`drain_finish_fixed.lu` is the REAL serve loop's shape: retirement is
a STATE CHECK (live count reaching zero; the timeout consulted
against the clock, in the loop's own bookkeeping — `retire_zero` in
`src/main.lu`), never a message race. Same tasks, same channels, same
`select`; the explorer closes a 24-schedule frontier on ONE outcome.
Its `//! explore: 64` mark keeps that true on every gauntlet run —
the accounting stays schedule-independent by test, not by memory.

## The .loborace artifact (schema 1)

Written by `tools/lobo-replay` to `target/replay/`; the shape a bug
report attaches when the finding comes from the rig:

```json
{"schema":1,
 "case":"tests/replay/drain_finish_race.lu",
 "seed":"4611686018427387922",
 "schedule":"ev:0,0,0,0,1",
 "verdict":"exit(0)",
 "stdout_sha256":"23d04d87…",
 "stdout":"lobo: [notice] generation-draining gen=1 held=2 seq=1\n…",
 "lupin":"lupin 0.1.19 (wolf-interp, reference interpreter at pin 83f83bb)"}
```

`seed` and `schedule` are BOTH carried (the number you hand somebody;
the schedule you can read and diff), the stdout pair pins the
expected bytes, and `lupin` names the interpreter identity the replay
holds under — a seed is a fact about a scheduler version, so the
artifact says which.

## What a bug report should attach (the server side)

For a live-server incident (not seed-replayable — the boundary
above): the error-log/stderr window with its seq-stamped vocabulary
events, and a `lobo status` snapshot. The seq stream gives the
maintainer the decisive event ORDER; `events:` bounds the window's
completeness; the drain model in tests/replay/ is the template for
driving that order deterministically under the rig and exploring its
neighborhood for the counterexample the incident sampled.

## Tier 2, re-read at ws13 (what the language must provide, stated against s132)

ws11 filed the Tier-2 gate as **wolf-lang#197** with three shapes:
(1) a runtime opt-in to the seeded scheduler for a NON-test binary,
(2) schedule capture as a value mid-run, (3) the record/replay io
boundary stated by the language. ws13 re-reads them against the pin
that carries s132 — regions with caps, and D68's proc-boundary faults
— because ws13 also put the first **proc** into lobo's request path
(the cap adoption: the regioned body work of a budgeted request runs
inside a `spawn proc`, and its breach reaches the join as
`fault(alloc-contract)`). Four things follow, each a shape, none
built:

1. **A capture must be written on the JOIN side, never inside the
   failing proc.** `[conc.proc.kill]`: a contained trap runs no
   further user code in the proc — no defer, no handler, no writer.
   The 5xx that Tier 2 wants to attach a schedule to is DECIDED at the
   join (the loop maps the exit reason to the response), so the
   capture writer lives in the loop, keyed on the reason class. This
   is already how lobo's `budget-exceeded site=region` event is
   emitted; a capture would ride the same seam.
2. **The reason class is a stable key.** `[conc.proc.exit]` is a
   closed set and `fault(kind)` draws `kind` from `[conf.trap.set]`'s
   closed vocabulary. A capture-on-5xx policy can therefore be
   spelled as a set of reason classes (`fault(alloc-contract)`,
   `fault(*)`, `error(*)`) rather than a status code — and the same
   spelling works for a future per-connection proc. The ask to #197:
   the mid-run capture surface should be reachable from a monitor's
   `exit(reason)` arm, so the join that already holds the reason can
   ask "the schedule so far" in the same select.
3. **The record boundary now has a natural place: the proc argument
   record.** s87's `[abi.native.procenv]` copies a proc's arguments at
   spawn. For lobo's body proc those are `(sock, path, head, cap,
   pipe)` — scalars and strings, no sockets read INSIDE the proc except
   the file and the write to the client. A Tier-2 recorder that
   captures proc argument records at spawn (plus the seed) has
   recorded everything the proc's schedule depended on; the io that
   crosses the membrane (the socket write) is replayed against a sink.
   That is #197's third shape made concrete: **record at the proc
   boundary, replay the proc**, not the process.
4. **What a proc can say back is the limit on what a capture can
   carry.** At this pin a proc's `normal(value)` is unreadable at the
   join and a channel cannot be a proc argument on wolfc (filed from
   ws13; the cap adoption carries its one number out through a
   loopback self-pipe). A capture token or a schedule handle produced
   INSIDE a proc could not leave it either. So shape (2)'s "capture
   as a value" must be a value the JOIN side obtains — from the
   monitor, the supervisor, or a runtime query keyed by the proc id —
   not one the proc hands back.

None of this changes lobo's honesty boundary above: a running lobo
still prints no seed and promises no replay. It changes what the ask
looks like, and the four points are posted to #197 as the ws13
re-read.
