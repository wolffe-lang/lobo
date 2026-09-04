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

ws17 (wsc06, closed): **`worker_processes N` uses the cores.** The
master binds the listeners and hands them down (`os_spawn_with` +
`net_adopt_listener`); every hand accepts on ONE socket and the kernel
distributes the work — measured at 28/32/31 over three hands, with
`accepted=` on every row of `lobo status` so an operator can see it.
The serving loop blocks on `net_wait` instead of time-slicing with
deadlines, which took one lobo process from **37 to 11,278 req/s** on
a connection-per-request load — within 2x of nginx at one worker. The
control endpoint takes orders over a **unix-domain socket** where the
host has one, so file permissions are the boundary, and each hand gets
its own. What N is not yet is N times: `net_accept` parks in a
blocking syscall after its readiness wait (wolf-lang#242, filed by
this sprint), so lobo serializes accepts behind nginx's own
`accept_mutex` shape to stay correct on a quiet server. The whole
table, both distribution shapes measured, and the three gates in the
order they were found are in docs/WORKERS.md. See the track plan
(Track 6) in the planning repo; sprints are contracts. This is also, deliberately, a flagship
codebase for reading production wolf: many agents, frozen `.wolfi`
interfaces between modules, and every language pothole filed
upstream as an issue.
