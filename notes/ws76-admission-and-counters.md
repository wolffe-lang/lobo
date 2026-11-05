# ws76 — admission across hands and connection counters

## 1. Forbidden

No nginx or other web-server source. The pinned nginx binary is a
black-box oracle. Tests bind loopback only, on their own ports.
No labels, merges, tags, releases or issue closures from this lane;
no attribution trailers. Builds use committed, isolated trees and
bounded containers on assigned CPUs.

## 2. Inputs, verified

- Base: trunk `6b8b9ee`, branch `ws76`.
- Pins: wolf 0.2.36, lupin 0.1.58, std `78b9d3cb`;
  nginx 1.30.4, as recorded in the toolchain and differential pins.
- The ignored reference directory was copied into this fresh clone.
  Its API conventions differed from the canonical standard-library
  trunk; the canonical copy replaced it before implementation.
- The required entry gauntlet is queued against the unmodified base.

## 3. Prediction (committed before any source change)

With two workers sharing an inherited listener, a full worker with
no idle connection currently competes with a sibling that still has
room. A directed two-worker drive at `worker_connections 16` should
show a refusal among the first 28 connections on the base, while the
same-host pinned oracle admits those 28. The row will first measure
the oracle instead of assuming its capacity, then be run at least
20 times without added load and 20 times with CPU load.

A short listener-only pause should let the sibling take the pending
connection. The pause must expire once, permitting refusal when all
workers are full; control, signals and established connections must
remain serviceable. Single-process and reuseport admission should
stay unchanged, with explicit scope rows. A starting value of 20 ms
will be measured before it is retained. Elapsed-time observations
will not become scheduling-sensitive upper-bound gates.

The process counter block should retain refused and idle-evicted
connection totals and accept-failure totals for emfile, enfile and
other reasons. Only an actual refusal, idle eviction or failed
accept increments its corresponding counter. Timeout from an accept
race is not a failure. Failed recovery accepts must be counted too.
The metrics registry must declare bounded reason labels, generated
metric docs must match it, and worker stamping must remain intact.

A refusal, an idle eviction and a low-descriptor accept failure will
each have a red-first row. The existing exposition checker will see
the added series, and exact assertions will catch missing counters.
The final gate runs at the final head, with one off-line pause-removal
plant required to fail the admission row by name.

## 4. Evidence index

Pending the red-first drives and final-head gate.

## 5. Limits and follow-ups

No new policy is chosen here: the shared-listener pause and the
three counter families implement the specified follow-up scope.
Host-wide ENFILE is not safe to induce on a shared host; its reason
mapping needs a pure row in addition to the live EMFILE witness.

Footprint: module
