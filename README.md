# Lobo

> Named 2026-08-29 (D64): **Lobo** — Seton's wolf no trap could take.
> The name landed at wsm03, under the gauntlet. The repo goes public
> under `wolffe-lang/lobo` at ws16, "the door opens".

A production web server, written in wolf. The charter: **nginx,
rewritten without their owned bugs, so that a 20-year nginx user
says "finally!"** — a drop-in replacement aside from the new
capabilities. Your `nginx.conf` carries. Your certificates and their
tooling keep working. That last part is a hard minimum, not a
stretch goal.

## What "without their owned bugs" means

- **The memory-corruption class is structural, not vigilant.** Wolf
  has checked arithmetic in every build profile, region-owned
  request memory, and no undefined behavior. The historical nginx
  CVE inputs live in this repo's test corpus; the acceptance is
  refuse-or-trap-clean, forever, in CI.
- **The config footguns are named at load.** The `if`-is-evil class,
  inheritance surprises, alias traversal — the config carries, and
  the linter tells you where nginx would have quietly hurt you.
- **The drop-in claim is falsifiable.** CI runs a pinned real nginx
  beside lobo with the same configs and diffs the responses. Claims
  ratchet; they don't hand-wave.

## What "finally!" means

Built-in ACME (certificates without the certbot dance — though the
certbot dance still works). A dry-run that exercises routing, not
just syntax. Reloads whose connection draining you can observe.
`-T` that tells you which file set every directive. Structured logs.
Per-vhost memory budgets that are enforced, not hoped. And — because
wolf's scheduler is deterministic under test — races you can replay
from a bug report.

## Status

ws18 (wsc07): **`worker_processes N` is N-ish at last.** The master
binds the listeners and hands them down (`os_spawn_with` +
`net_adopt_listener`); every hand accepts on ONE socket, free-for-all,
and the kernel distributes the work — measured at 36/29/26 over three
hands, with `accepted=` on every row of `lobo status` so an operator
can see it. The serving loop blocks on `net_wait` instead of
time-slicing with deadlines, which took one lobo process from **37 to
13,508 req/s** on a connection-per-request load. ws17 had to serialize
accepts behind nginx's own `accept_mutex` shape because `net_accept`
parked in a blocking syscall after its readiness wait (wolf-lang#242,
filed by that sprint); the fix landed upstream and **ws18 deleted the
workaround** — three hands go from 12,866 to **23,663 req/s** (1.84x)
and eighteen hands on a keepalive load from 9,554 to **38,961**
(4.1x), because the turn had been capping the SERVING path as well as
the accept path. The control endpoint takes orders over a
**unix-domain socket** where the host has one, so file permissions are
the boundary, and each hand gets its own. The whole table, both
distribution shapes measured, and the three gates in the order they
were found are in docs/WORKERS.md. See the track plan
(Track 6) in the planning repo; sprints are contracts. This is also, deliberately, a flagship
codebase for reading production wolf: many agents, frozen `.wolfi`
interfaces between modules, and every language pothole filed
upstream as an issue.
