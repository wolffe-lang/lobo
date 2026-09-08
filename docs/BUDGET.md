# The budget is real (ws10)

nginx's answer to memory pressure is the OOM killer: the request that
blew the process's memory is answered by the kernel, with a SIGKILL,
for every connection at once. lobo's answer is a 503 with a name: a
`memory_budget` a request can exceed, deterministically, observably,
and alone. This page is the model, the enforcement contract, the audit
behind it, and the line between what is structural today and what
waits on upstream.

## The model: regions are the substrate

Wolf's memory is region-owned: allocations live in arenas that die
wholesale, and the ws02 design put each request's and each connection's
working set in the serving tree's own frames. The budget's premise is
that per-request memory is *attributable*: you can only refuse a
request for its memory if its memory is its own.

ws10's structure audit (target 1) tested that premise and found it
half-true at the current pin:

- Response bodies (the largest per-request allocation) now live in
  per-response `region` blocks in `serve/` and die with their
  response. Before the audit every served body was charged to the
  process ROOT region for the process's whole life
  (`[mem.region.create.3]`: the ambient region is the caller's, and
  nothing up the serve tree had scoped one; lobo had ZERO `region`
  blocks before ws10).
  Measured: ~290 KB retained per request before, ~24-26 KB after; a
  16 KiB-body drive now costs the same memory as a 16-byte-body
  drive (the `tools/lobo-membudget` differential witness, a gauntlet
  step).
- String work (request heads, parse results, response heads) still
  cannot join a region: the native tier realizes str materializations
  in a process-lifetime root arena, a documented v0 seam in wolf's
  own runtime (`wolf_rt/src/str.rs`), now filed with lobo's numbers as
  wolf-lang#191. Until that pin lands, a long-running lobo retains
  each request's string work; the audit witness names the gap
  on every run and flips to a hard O(1) gate at the fix's pin bump.

### The audit method (a deliverable)

ws12 update: the audit no longer has to observe from outside.
wolf-lang s131 landed `region_bytes(r)` and `live_region_bytes()`
([mem.region.account.1/.2]) at pin `0.2.1+dev.e6cf24e`, and lobo reads
them, so the numbers below stopped being estimates. What follows is kept
in full because it is still the *shape* of the audit, and because the
`ps(1)` witness still guards the half the ledger cannot see (#191's
string work, which lands in no named region at all). The OUTSIDE
method:

1. `tests/rig/memdrive.lu` drives N keepalive requests over one
   connection (a close before N is a named failure, the keepalive
   half of the witness);
2. `tools/lobo-membudget` samples the server's RSS via `ps(1)` around
   two same-shape drives whose only difference is body size (16 B vs
   16 KiB), and asserts the difference is allocator noise, not bodies;
3. a per-request retention ratchet (< 64 KB/req under a padded-head
   shape) catches lobo-side structural regressions while #191 heals.

Probes behind the fix (recorded 2026-08-31, pin addcd7f, macOS/arm64):
a 20k-iteration `region`-wrapped List loop holds 1.5 MB where the bare
loop holds 84 MB (regions work, cross-call included, despite a
misleading W1001, filed as wolf-lang#192); the same loop over str
interpolation holds 666 MB with or without the region (#191).
#192 healed at the ws12 pin: r04 fixed both halves (W1001 gains its
call test, E1010 reads through the error row), so the misleading
diagnostic that made the ws10 probe hard to read is gone.

## The measured numbers (ws12)

`serve` now reads `region_bytes` inside the per-response and per-chunk
regions the ws10 audit put there, and carries the reading out as
`ReqOut.mem_rt`. The entry high-waters it per generation beside ws10's
metered figure. Both are published: `mem-rt-hw` in `lobo status`,
`mem_rt_high_water` in the JSON, `lobo_request_region_bytes_high_water`
at `/metrics`, and the process-wide `live_region_bytes()` as
`live-region-bytes:` / `lobo_live_region_bytes`.

Two numbers, two questions, never subtracted from each other:

| | `mem-hw` (ws10) | `mem-rt-hw` (ws12) |
|---|---|---|
| what it counts | bytes lobo DECIDED to admit | bytes the RUNTIME charged the response region |
| who computes it | lobo's admission meter | the region ledger, `[mem.region.account.1]` |
| when it is knowable | BEFORE the bytes are read — which is what makes a pre-admission 503 possible | only after |
| what it rules | the budget | nothing; it reports |
| units | request bytes | implementation-measured per tier |

What the ledger says, measured 2026-09-01, pin `0.2.1+dev.e6cf24e`,
macOS/arm64 (`tests/serve/region_measured.lu` pins the relations;
these are the raw readings behind it):

| response | budget charges | region ledger reads |
|---|---|---|
| an 18-byte file | 18 | **496** native / 288 checked |
| one 64 KiB stream chunk | 65,536 | **1,048,560** native / 1,048,576 checked |
| a HEAD | 0 | **0** |
| a 128 KiB file, streamed | 65,536 (one chunk) | 1,048,560 |
| a 256 KiB file, streamed | 65,536 (one chunk) | 1,048,560 — *the same number* |

Read the last two rows first: doubling the file does not move the
number. That is the O(1)-in-file-size claim ws10 could only argue
from RSS noise, now stated by the runtime as an equality, and it is the
property that makes a long-running lobo's body memory bounded. The
per-chunk region works as designed.

The other side of it: a 64 KiB chunk charges 1 MiB, 16x. Two
multipliers, neither of them a lobo bug:

1. 8x, because a byte buffer is a `List[int]`. `fs_read_chunk`,
   `fs_read_bytes` and `net_read_bytes` all return one machine int (8
   bytes) per byte. 64 KiB of file is 512 KiB of storage.
2. 2x, because the ledger is cumulative by contract.
   `[mem.region.account.1]`: "a reallocation's abandoned buffer stays
   charged; nothing is ever subtracted while the region lives". A list
   grown to 65,536 elements by doubling therefore charges the sum of
   every buffer it ever had: 8+16+…+524,288 ≈ 1,048,568, which is what
   we measure, to the byte.

Filed, not absorbed: wolf-lang#203 (the byte-buffer representation,
with these numbers), and a comment on #187 because the gap bears on
the cap half's units. Until one of them lands, read `memory_budget` as
a POLICY instrument in admitted-request bytes, bounding
what lobo lets in, deterministically, before it is read. It is not a
prediction of RSS, and on the streaming path an operator who reads
`memory_budget 1m` as "about a megabyte of memory per request" is out
by 16x.

`live_region_bytes()` is the process-wide companion, with its own
caveat from the clause: it is not an RSS proxy. The
process-root arena, where at this pin every string materialization
still lands (#191), is never counted. On an idle lobo it reads 0,
because every response region has died; that is `[mem.region.account.2]`
working, not a broken gauge.

## The fence and the budget

Two different instruments:

- The fence bounds *inputs* before they are read: header sizes,
  body sizes. It answers with the input-shaped statuses nginx answers
  (400/413/414). The fence is nginx-compatible directive by directive.
- The budget bounds *admitted memory* per request: what lobo has
  actually taken in (head bytes, body bytes) plus what it is about to
  materialize to respond (the response body's bytes). It answers 503
  and closes the connection, shedding the memory.

### The fence directives (perimeter, nginx-named)

| directive | contexts | semantics |
|---|---|---|
| `client_max_body_size <size>` | http, server, location† | request body cap → 413. `0` = unlimited (nginx's rule). Default 1m. |
| `large_client_header_buffers <n> <size>` | http, server | `<size>` bounds the request line (→ 414) and each header line (→ 400 "Request Header Or Cookie Too Large"); `n × size` bounds the whole header block (→ 400, same body). Default 4 8k. |
| `client_header_buffer_size <size>` | http, server | parse-clean, `planned(ws15)`: a read-buffer *tuning* knob, not a fence — the hard bounds above are what lobo enforces; ws15 (perf) decides whether the small-buffer fast path earns its place. |

† location-level `client_max_body_size` parses and is NAMED inert at
v0 (lint LOBO-L009): limits resolve at http/server level while server
selection is host-blind, the L005 pattern, lifted by the routing
sprint. Bad values are the oracle's own spelling:
`"client_max_body_size" directive invalid value` (probed).

`client_max_uri_length`-class rows: none, because nginx has no such
directive; the request line is bounded through
`large_client_header_buffers`, and lobo matches nginx name-for-name
instead of inventing a fence nginx spells differently.

### The budget directive (lobo-native)

```
memory_budget <size>;    # http or server context; lobo-native (L008)
```

Per-REQUEST admitted-bytes budget under the vhost that serves it.
`0` (or absent) = off. nginx `-t` rejects the directive; adopting it
is the same one-way door as `cert auto`/`log_headers`, linted at load
(the WWS-L-native class). The effective Limits (fence + budget)
FREEZE per generation beside the model: a reload re-resolves them,
and a draining generation keeps serving under its own numbers, the
frozen-model discipline applied to the budget.

What counts against a request: its header-block bytes, its body
bytes (declared or chunk-accumulated), and the response body bytes it
is about to materialize (a whole small file, or one 64 KiB stream
chunk). What does not: the frozen config, listeners, the sinks,
the runtime itself, error-response builds (O(1) small), and the
proxied *upstream response* leg at this pin (named residue below).

## Enforcement: deterministic per exceed-site

The rule, written before the code: the fence fires first, the budget
second, at every site. A request over both `client_max_body_size`
and the budget is a 413; the more specific error wins. Then, per
site:

| site | when it checks | over → | notes |
|---|---|---|---|
| `admin` | on the ws12 `/metrics` and `/status.json` endpoint, before the rendered body is written | 503, close | the fifth site, appended (the frozen field keeps its key; the VALUE set widens). The exposition is a response body lobo materializes, so it is charged like one — a scrape that sheds under a tiny budget is CORRECT, and a rig case |
| `region` | ws14 (built at ws13): at the runtime's own region cap — `16 × pow2ceil(budget)` ledger units, ws15's D40 envelope — inside the body proc: the read for a small file, the first chunk for a streamed one | 503, close (small path); close (stream path — the head is on the wire) | the sixth site: the RUNTIME refused, not the meter ([mem.region.cap.3], D68: the breach is contained at the proc boundary and reaches the join as `fault(alloc-contract)`). `would` reports `budget+1` (a killed proc's charge is unobservable at the join) and the event gains a trailing `cap=<ledger units>` field. **Not reachable from a config since D40** — the envelope follows the growth law, so no body the meter admits can cross the cap (the theorem below, asserted over the whole admissible shape space). It is the backstop for a runtime charge the meter does not model, and its witness is the join driven directly in `tests/serve/budget_cap.lu` |
| `head` | after the head is framed and parses clean | 503, close | fences (414/400) precede it; the head was necessarily read to be measured — the fence bounds that over-admission at `n × size` |
| `body` | BEFORE reading a declared (Content-Length) body | 503, half-close drain, close | the budget's strongest moment: refused pre-admission, zero body bytes read; `would` = head + declared length |
| `body-chunked` | while chunks accumulate | 503, half-close drain, close | fence (413) checked against the same running total first; `would` reports `budget+1` — the crossing point (an unread chunked body's true total is unknowable) |
| `file` | before any response byte is written, from `stat` size | 503, close | whole file ≤ 64 KiB charges its size; a streamed file charges one 64 KiB chunk; HEAD charges nothing; a conditional GET's 304 wins first (it materializes no body) |

A budget 503 always closes the connection (a keepalive would keep the
conn's buffers). The 503 is nginx's
own shape: `503 Service Temporarily Unavailable`, default error body,
`Connection: close`.

Routing is not a charge site: it allocates O(config), not
O(request) (per the contract's site enumeration).

Proxy: the request body is charged at the `body` site before the
upstream leg runs; the upstream *response* buffering is unmetered at
this pin, a named residue that rides the proxy-buffering sprint
(`proxy_buffering` is still `planned(ws03)`).

TLS: budgets enforce on TLS connections identically (the checks
live in the shared lifecycle), but the refusal is not *reported*:
the blocking TLS path predates the step loop and carries no access
record or event channel (the D24/D27 rider; the counters and events
below are the plaintext step path's until TLS joins it).

### Which half is structural today — BOTH (ws14 edition)

The meter admits; the runtime enforces. s132 shipped `region
r(cap: n)` ([mem.region.cap.1-3]) and D68 ruled a breach inside a
proc contained at the proc boundary, reaching the join as
`fault(alloc-contract)`. ws13 consumed them: a budgeted request's
regioned body work runs inside a `spawn proc` (`src/budget`, the
first proc in lobo's request path) under `cap: ledger_cap(memory_budget)`,
and the join maps the reason: normal → the response went out, error
→ the socket broke, `fault(alloc-contract)` → 503 with a name,
`site=region`, any other fault → 500 (a trap contained, where
before it was the process). The measured `region_bytes` reading ws12
publishes comes back out of the proc through a loopback self-pipe
the entry opens once, because a proc's `normal(value)` is unreadable
at the join and a channel cannot be a proc argument on wolfc
(wolf-lang#219 records the gap; D38 in the ledger).

ws13 built it and the release tier refused to emit it: a `spawn
proc` whose spawner lives in any module but the entry landed its
entry shim outside its object (`func.addr of
@budget.run_small.task0.entry outside this object's subset`, the
#136 shape for a PROC). Filed as wolf-lang#219; s134 fixed it
(the LLVM emitter now declares an out-of-subset `func.addr` referee
by its mangled symbol and lets the linker resolve it, under every
partition, `WOLF_MIDEND=0` included, which is the mode lobo's
gauntlet builds in while #146 is open), and the adoption merged at
the 5f99b9f pin (ws14). The proof is the gauntlet's own
release step: `WOLF_MIDEND=0 wolf build --release src/main.lu` links
`src/budget`'s proc, and every release-binary witness (`lobo-
membudget`, `lobo-signal`, `lobo-resolver`, the differentials) runs
that binary.

Per lane:

| lane | the cap adoption | how it is known |
|---|---|---|
| native (debug tier) | runs | `tests/serve/budget_cap.lu` (the four relations, the join driven directly), `budget_cap_e2e.lu` (the real server, 200 through the proc, `mem-rt-hw` back through the pipe), `cap_shape.lu` |
| release (`WOLF_MIDEND=0`) | runs — #219's fix | the gauntlet's tiers step builds it; `tools/lobo-membudget`'s cap rounds drive the whole budgeted path through a real socket against `target/lobo-release` — since ws15 that includes D40's closure measurement (the ws14 breach serving 200, the meter's 503 beside it) |
| checked — `wolf conform-run --checked` (the s23 UB machine, the corpus runner's lane) | **refuses, by name**: `unsupported` at `mem`, `x-unsupported-construct: "structured concurrency in checked execution (C1 deferred)"` — the machine runs no `spawn`/scope/`select` at all; a proc is refused where every spawn is (the C1 sprint, not a fix) | `//! checked-refuses:` on `budget_cap.lu` and `cap_shape.lu` — the runner ASSERTS the named record, never skips the lane (at v0.2.2 the record was empty: #219's second observation, fixed by s134). Every witness that fires a refusal BEFORE the proc keeps its checked lane (`budget_refusals.lu`, `budget_e2e.lu`, `region_measured.lu`) |
| checked — `wolf run --checked` | runs (it is the NATIVE build under the checked profile, a different machine) | not a corpus lane; stated so nobody bisects it again |
| lupin | runs the shape (`cap_shape.lu`); the serve suite cannot run there (lupin has no fs) | the corpus lane |

The arithmetic (the directive documents it). The cap bounds the
region's LEDGER, which `[mem.region.account.1]` keeps in the tier's
own units, cumulative and high-water. Two factors set it:

- 16×, the per-byte factor. #203 measured lobo's streaming shape
  at sixteen times the payload: 8× because a byte buffer is a
  `List[int]`, 2× because growth's abandoned buffers stay charged.
- `pow2ceil`, the growth factor. The buffer grows by DOUBLING and
  the ledger keeps every abandoned buffer, so a body's charge is set
  by the smallest power of two at or above it, not by the body.

So `ledger_cap(budget) = 16 × pow2ceil(budget)`, which is D40 (ws15).
ws13 wrote `budget × 16` from a single measurement; ws14 measured the whole
curve, found the flat envelope false, and routed the decision; this is
its resolution. The spec's own advice is to derive caps from measured
readings rather than payload constants, and lobo publishes the reading
(`mem-rt-hw`) the arithmetic is checked against; when #203 changes the
growth law the exponent changes with the pin, in one place.

The growth law (ws14's measurement, unchanged). Measured at the
5f99b9f bump, native tier, `fs_read_bytes` into a fresh capped region
(`tests/serve/budget_cap.lu` pins the relations; these are the raw
readings):

| body bytes N | ledger charge | ÷ N |
|---|---|---|
| 18 | 496 | 27.6 |
| 1,000 | 16,368 | 16.4 |
| **1,024** | 16,368 | 16.0 |
| **1,025** | **32,752** | **32.0** |
| 4,096 | 65,520 | 16.0 |
| 4,097 | 131,056 | 32.0 |
| 40,000 | 1,048,560 | 26.2 |
| 65,535 / 65,536 | 1,048,560 | 16.0 |

The law is `charge(N) = 16 × pow2ceil(N) − 16`: 16× the payload
exactly AT a power of two (where #203 measured, and where the 64 KiB
chunk sits), and up to 32× just past one.

What D40 changed, and why. Under ws13's flat `budget × 16`
envelope the law opened a BAND in which the runtime refused a request
the meter had ADMITTED: a 33,000-byte file under `memory_budget 40k`
was admitted (head + 33,000 < 40,960) and then charged 1,048,560
against a cap of 655,360, dying at the join. That is the cap acting as
a SECOND METER with different arithmetic from the first: two numbers
an operator must reconcile, one of them undocumented in their config.
ws14 left the envelope alone and routed the decision, because "what is
the cap FOR" is a campaign question, not a lane's. The answer is
backstop: the meter is the surface an operator configures and
reasons about; the cap exists to contain a runtime charge the meter
does not model, and it should never fire on a shape the meter has
already ruled on.

Making the envelope follow the law delivers that, and the theorem
now holds:

> No body the meter admits can cross the cap. Small path: the
> meter admits only `N ≤ budget`, so `pow2ceil(N) ≤ pow2ceil(budget)`
> and the charge `16 × pow2ceil(N) − 16` is strictly under
> `16 × pow2ceil(budget)`. Stream path: a streamed body is admitted
> only when the meter can charge one 64 KiB chunk, so
> `budget ≥ 65,536`, so the cap is at least 2,097,152, over the
> 1,048,560 a chunk region charges.

It is ASSERTED: `tests/serve/budget_cap.lu` walks
every budget from 1 byte up past the stream threshold and checks the
worst admissible body against the cap at each. And it is MEASURED end
to end: `tools/lobo-membudget` serves the file ws14 measured as
a breach (33,000 bytes under `memory_budget 40k`) and reads back
`mem-rt-hw=1048560` against a cap of 1,048,576, a 200 in full with a
sixteen-unit margin, with NO `site=region` event anywhere in the run.
The 50,000-byte file beside it is still a 503 `site=file`: the meter
refuses it, before any proc is spawned.

Operator rule. Set `memory_budget` to the bytes you are willing to
admit. There is no second arithmetic to reconcile and no
power-of-two footnote. (ws14's rule, "set it to at
least the power of two above the largest small file you serve", is
RETIRED by D40; a config written to it is still correct, just no
longer necessary.) What the cap costs you is address space the region
may reserve, not bytes it will use: a budget of 40k caps its regions
at 1,048,576 ledger units rather than 655,360, and the ledger is a
count, not an allocation.

Per-CONNECTION budgets (a cap on the conn's carry at accept)
stay the second door: they need the proc boundary to be a
per-connection unit, which is the D24 stepper's rework, not this
sprint's. Recorded in the ledger (D24 owns the stepper; the cap arm
is no longer gated on anything upstream).

## Observability

- Log event (ws09 vocabulary, appended, nothing renamed):
  `budget-exceeded gen=<g> site=<head|body|body-chunked|file|admin>
  budget=<bytes> would=<bytes>` at level `error`, through the same
  seam as every generation event (stderr always; the configured
  `error_log` level-gated, text or JSON door). The refused request
  also writes an ordinary access line with `status` 503.
- Status stanza (ws08 surface, additive; schema stays 1): each
  generation's line gains `mem-hw=<bytes>` (the high-water admitted
  bytes of any single request served under that generation),
  `budget-503s=<n>` (refusals) and, from ws12, `mem-rt-hw=<bytes>` (the
  MEASURED high water). The stanza head gains
  `live-region-bytes: <bytes>`. JSON: `"mem_high_water"`,
  `"budget_503s"`, `"mem_rt_high_water"`, `"live_region_bytes"`.
  ws12's metrics endpoint serves this same object at `/status.json`,
  and the exposition's `lobo_request_admitted_bytes_high_water` /
  `lobo_request_region_bytes_high_water` / `lobo_live_region_bytes`
  carry the same three numbers for a scraper (docs/metrics.md).
- Per hand under `worker_processes N` (ws16, docs/WORKERS.md):
  the meter, the cap, `live_region_bytes()` and every number above
  live inside the process that served the request, so a
  `memory_budget` of 64k is 64k in EACH of N hands, never 64k across
  them. The master's `lobo status` sums `live-region-bytes` over the
  hands and shows each hand's `budget-503s`; a `/metrics` scrape is
  ONE hand's numbers (`lobo_worker_id` names which).

## Witnesses

- `tools/lobo-membudget`, the audit witness (gauntlet step): bodies
  die per-response (differential drive), the retention ratchet, and
  the #191 named gate.
- `tests/serve/budget_shapes.lu`, pure: limit resolution from config
  (defaults, overrides, `0` semantics, buffer math), the 503 shape.
- `tests/serve/budget_refusals.lu`, in-process round-trips: every
  exceed-site's status, the fence-first interplay both ways, HEAD's
  zero file charge.
- `tests/serve/region_measured.lu`, THE MEASURED witness (ws12): a
  small file charges a bounded region, a HEAD charges nothing, two
  stream files of different lengths charge the SAME high water (the
  O(1) claim as an equality), and `live_region_bytes()` returns to its
  entry reading after every response; `[mem.region.account.1/.2]`'s
  relations, never their units.
- `tests/serve/budget_e2e.lu`: the corpus config with a tiny
  budget + a large-header request pins the 503-with-a-name end
  to end: the wire status, the access-log 503, the `budget-exceeded`
  event fields, and the status stanza's counters.
- `tests/serve/budget_cap.lu`, THE CAP witness (ws13/ws14): the
  budget-off path unchanged, the envelope holding through the proc
  with `mem_rt` back through the self-pipe, the stream path chunk by
  chunk, and the join driven directly to a contained
  `fault(alloc-contract)` with `live_region_bytes()` at baseline.
- `tests/serve/budget_cap_e2e.lu`: the real server under
  `memory_budget 4k`: 200 through the capped proc, `mem-rt-hw`
  non-zero in the status stanza.
- `tests/serve/cap_shape.lu`: the one-module shape on native AND
  lupin (200 rounds, a breach, the next round clean); the checked
  lane's named refusal asserted.
- `tools/lobo-membudget`'s cap rounds (ws14, re-baselined at ws15):
  the release binary under `memory_budget 40k`, with rounds A'/B'
  re-baselined THROUGH the proc (the same two gates), then D40's
  closure through a real socket, where the 33,000-byte file ws14
  measured as a `site=region` breach now serves 200 in full
  (`mem-rt-hw=1048560` against a cap of 1,048,576), the power-of-two
  neighbour beside it serves 200, a 50,000-byte file is refused by
  the METER (503 `site=file`) and NO `site=region` event appears
  anywhere in the run, fifty keepalive requests after it,
  `budget-503s=1` and `mem-rt-hw` in `lobo status`.
