# The budget is real (ws10)

nginx's answer to memory pressure is the OOM killer: the request that
blew the process's memory is answered by the kernel, with a SIGKILL,
for every connection at once. lobo's answer is a **503 with a name** —
a `memory_budget` a request can exceed, deterministically, observably,
and alone. This page is the model, the enforcement contract, the audit
that makes it honest, and the plainly-stated line between what is
structural today and what waits on upstream.

## The model: regions are the substrate

Wolf's memory is region-owned: allocations live in arenas that die
wholesale, and the ws02 design put each request's and each connection's
working set in the serving tree's own frames. The budget's whole
premise is that per-request memory is *attributable* — you can only
refuse a request for its memory if its memory is its own.

ws10's **structure audit** (target 1, the sprint's soul) tested that
premise and found it half-true at the current pin:

- **Response bodies** (the largest per-request allocation) now live in
  per-response `region` blocks in `serve/` and die with their response
  — before the audit every served body was charged to the process
  ROOT region for the process's whole life (`[mem.region.create.3]`:
  the ambient region is the caller's, and nothing up the serve tree
  had scoped one — lobo had ZERO `region` blocks before ws10).
  Measured: ~290 KB retained per request before, ~24-26 KB after; a
  16 KiB-body drive now costs the same memory as a 16-byte-body
  drive (the `tools/lobo-membudget` differential witness, a gauntlet
  step).
- **String work** (request heads, parse results, response heads) still
  cannot join a region: the native tier realizes str materializations
  in a process-lifetime root arena — a documented v0 seam in wolf's
  own runtime (`wolf_rt/src/str.rs`), now filed with lobo's numbers as
  **wolf-lang#191**. Until that pin lands, a long-running lobo retains
  each request's string work; the audit witness names the gap loudly
  on every run and flips to a hard O(1) gate at the fix's pin bump.

### The audit method (a deliverable)

No in-language region accounting exists at this pin (`region_bytes` /
`live_region_bytes` live in `wolf_rt` but reach no lane — the query +
creation-time-cap ask is filed as **wolf-lang#187**, with this page's
use case as the customer). So the audit observes from OUTSIDE:

1. `tests/rig/memdrive.lu` drives N keepalive requests over **one**
   connection (a close before N is a named failure — the keepalive
   half of the witness);
2. `tools/lobo-membudget` samples the server's RSS via `ps(1)` around
   two same-shape drives whose only difference is body size (16 B vs
   16 KiB), and asserts the difference is allocator noise, not bodies;
3. a per-request retention ratchet (< 64 KB/req under a padded-head
   shape) catches lobo-side structural regressions while #191 heals.

Probes behind the fix (recorded 2026-08-31, pin addcd7f, macOS/arm64):
a 20k-iteration `region`-wrapped List loop holds 1.5 MB where the bare
loop holds 84 MB (regions work, cross-call included — despite a
misleading W1001, filed as **wolf-lang#192**); the same loop over str
interpolation holds 666 MB with or without the region (#191).

## The fence and the budget

Two different instruments, deliberately:

- **The fence** bounds *inputs* before they are read: header sizes,
  body sizes. It answers with the input-shaped statuses nginx answers
  (400/413/414). The fence is nginx-compatible directive by directive.
- **The budget** bounds *admitted memory* per request: what lobo has
  actually taken in (head bytes, body bytes) plus what it is about to
  materialize to respond (the response body's bytes). It answers 503
  and closes the connection — shedding, not scolding.

### The fence directives (perimeter, nginx-named)

| directive | contexts | semantics |
|---|---|---|
| `client_max_body_size <size>` | http, server, location† | request body cap → 413. `0` = unlimited (nginx's rule). Default 1m. |
| `large_client_header_buffers <n> <size>` | http, server | `<size>` bounds the request line (→ 414) and each header line (→ 400 "Request Header Or Cookie Too Large"); `n × size` bounds the whole header block (→ 400, same body). Default 4 8k. |
| `client_header_buffer_size <size>` | http, server | parse-clean, `planned(ws15)`: a read-buffer *tuning* knob, not a fence — the hard bounds above are what lobo enforces; ws15 (perf) decides whether the small-buffer fast path earns its place. |

† location-level `client_max_body_size` parses and is NAMED inert at
v0 (lint LOBO-L009): limits resolve at http/server level while server
selection is host-blind — the L005 pattern, lifted by the routing
sprint. Bad values are the oracle's own spelling:
`"client_max_body_size" directive invalid value` (probed).

`client_max_uri_length`-class rows: none — nginx has no such
directive; the request line is bounded through
`large_client_header_buffers`, and lobo matches nginx name-for-name
rather than inventing a fence nginx spells differently.

### The budget directive (lobo-native)

```
memory_budget <size>;    # http or server context; lobo-native (L008)
```

Per-REQUEST admitted-bytes budget under the vhost that serves it.
`0` (or absent) = off. nginx `-t` rejects the directive — adopting it
is the same one-way door as `cert auto`/`log_headers`, linted at load
(the WWS-L-native class). The effective Limits (fence + budget)
FREEZE per generation beside the model: a reload re-resolves them,
and a draining generation keeps serving under its own numbers — the
frozen-model discipline, applied to the budget.

**What counts against a request:** its header-block bytes, its body
bytes (declared or chunk-accumulated), and the response body bytes it
is about to materialize (a whole small file, or one 64 KiB stream
chunk). **What does not:** the frozen config, listeners, the sinks,
the runtime itself, error-response builds (O(1) small), and the
proxied *upstream response* leg at this pin (named residue below).

## Enforcement: deterministic per exceed-site

The rule, written before the code: **the fence fires first, the budget
second, at every site.** A request over both `client_max_body_size`
and the budget is a 413 — the more specific error wins. Then, per
site:

| site | when it checks | over → | notes |
|---|---|---|---|
| `head` | after the head is framed and parses clean | 503, close | fences (414/400) precede it; the head was necessarily read to be measured — the fence bounds that over-admission at `n × size` |
| `body` | BEFORE reading a declared (Content-Length) body | 503, half-close drain, close | the budget's strongest moment: refused pre-admission, zero body bytes read; `would` = head + declared length |
| `body-chunked` | while chunks accumulate | 503, half-close drain, close | fence (413) checked against the same running total first; `would` reports `budget+1` — the crossing point (an unread chunked body's true total is unknowable) |
| `file` | before any response byte is written, from `stat` size | 503, close | whole file ≤ 64 KiB charges its size; a streamed file charges one 64 KiB chunk; HEAD charges nothing; a conditional GET's 304 wins first (it materializes no body) |

A budget 503 always closes the connection (shedding memory is the
point; a keepalive would keep the conn's buffers). The 503 is nginx's
own shape: `503 Service Temporarily Unavailable`, default error body,
`Connection: close`.

**Routing** is not a charge site: it allocates O(config), not
O(request) (stated, per the contract's site enumeration).

**Proxy**: the request body is charged at the `body` site before the
upstream leg runs; the upstream *response* buffering is unmetered at
this pin — a named residue that rides the proxy-buffering sprint
(`proxy_buffering` is still `planned(ws03)`).

**TLS**: budgets enforce on TLS connections identically (the checks
live in the shared lifecycle), but the refusal is not *reported* —
the blocking TLS path predates the step loop and carries no access
record or event channel (the D24/D27 rider; the counters and events
below are the plaintext step path's until TLS joins it).

### Which half is structural today (the honest line)

Enforcement today is **admission metering above the regions**: lobo
counts the bytes it admits into the request's working set — it makes
every admission decision, so the meter is deterministic and refusals
are real. It is not yet the region runtime's own ledger: runtime
overhead, parse expansion, and str materializations are not in the
number. The gated half — `memory_budget` as a region CAP at
request/conn-region creation, exceed as a catchable fault row — is
exactly wolf-lang#187's cap half; when it lands, the meter becomes the
backstop and the cap becomes the enforcement. Per-CONNECTION budgets
(a cap on the conn's region at accept, exceed → conn close) are the
same gated half; today the conn's cross-request holdings are bounded
by the fence (`n × size` of carry) and the per-request budget.
Recorded as the campaign's named deferral with #187 as owner.

## Observability

- **Log event** (ws09 vocabulary, appended — nothing renamed):
  `budget-exceeded gen=<g> site=<head|body|body-chunked|file>
  budget=<bytes> would=<bytes>` at level `error`, through the same
  seam as every generation event (stderr always; the configured
  `error_log` level-gated, text or JSON door). The refused request
  also writes an ordinary access line with `status` 503.
- **Status stanza** (ws08 surface, additive — schema stays 1): each
  generation's line gains `mem-hw=<bytes>` (the high-water admitted
  bytes of any single request served under that generation) and
  `budget-503s=<n>` (refusals). JSON: `"mem_high_water"`,
  `"budget_503s"`. ws12's metrics endpoint serves the same object.

## Witnesses

- `tools/lobo-membudget` — the audit witness (gauntlet step): bodies
  die per-response (differential drive), the retention ratchet, and
  the loud #191 named gate.
- `tests/serve/budget_shapes.lu` — pure: limit resolution from config
  (defaults, overrides, `0` semantics, buffer math), the 503 shape.
- `tests/serve/budget_refusals.lu` — in-process round-trips: every
  exceed-site's status, the fence-first interplay both ways, HEAD's
  zero file charge.
- `tests/serve/budget_e2e.lu` — the corpus config with a deliberately
  tiny budget + a large-header request pins the 503-with-a-name end
  to end: the wire status, the access-log 503, the `budget-exceeded`
  event fields, and the status stanza's counters.
