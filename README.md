# wolf-wws

> Working name. The public name is undecided and this repo has no
> remote until it is chosen.

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
  beside wws with the same configs and diffs the responses. Claims
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

Pre-ws00: scaffolding. See the track plan (Track 6) in the planning
repo; sprints are contracts. This is also, deliberately, a flagship
codebase for reading production wolf: many agents, frozen `.wolfi`
interfaces between modules, and every language pothole filed
upstream as an issue.
