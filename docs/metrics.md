# Metrics (generated)

Generated from `src/metrics/metrics.lu` (`metrics.registry`) by
`tools/lobo-metricsdoc` — NEVER hand-edited. Every row
below is the same string the `# HELP` line carries at
`/metrics`, so a Grafana panel built from this page and a live
scrape can never disagree.

The memory rows are explained in `docs/BUDGET.md`; the endpoint
itself is below.

| metric | type | labels | help |
|--------|------|--------|------|
| `lobo_build_info` | gauge | `version` | Build identity of the running lobo; always 1 (the info-metric idiom). |
| `lobo_config_generation_info` | gauge | `gen id state` | One series per live configuration generation, labelled with its content-hash id and state; always 1 (the info-metric idiom). |
| `lobo_config_generation_current` | gauge | — | The generation number currently accepting new connections. |
| `lobo_config_generations` | gauge | `state` | Live configuration generations by state (current or draining). |
| `lobo_connections_accepted_total` | counter | — | Connections accepted since start. |
| `lobo_connections_active` | gauge | `gen` | Connections currently held, by the generation that accepted them. |
| `lobo_connections_retired_total` | counter | `gen outcome` | Connections retired from a draining generation: outcome drained (finished) or aborted (worker_shutdown_timeout forced the close). |
| `lobo_requests_total` | counter | `class` | Requests served, by response status class (2xx/3xx/4xx/5xx). Deliberately NOT by URI or by client: see the cardinality fence. |
| `lobo_request_duration_seconds` | histogram | — | Request service time in seconds, over a fixed 5ms..10s ladder. |
| `lobo_request_bytes_total` | counter | — | Request header and body bytes admitted. |
| `lobo_response_bytes_total` | counter | — | Response body bytes written. |
| `lobo_upstream_requests_total` | counter | `class` | Proxied requests by upstream status class; class "error" counts legs that produced no upstream status (dial, TLS or read failure). |
| `lobo_upstream_duration_seconds` | histogram | — | Upstream leg time in seconds, over the same 5ms..10s ladder as the client-facing histogram. |
| `lobo_tls_handshakes_total` | counter | — | TLS handshakes that completed and served a connection. |
| `lobo_tls_handshake_failures_total` | counter | `reason` | TLS handshakes lobo refused or lost, by reason (refused, timeout, io). |
| `lobo_budget_refusals_total` | counter | `gen` | Requests refused with 503 by memory_budget, by generation. |
| `lobo_request_admitted_bytes_high_water` | gauge | `gen` | Highest admitted-bytes total of any single request served under the generation — lobo's own ADMISSION METER, the number the budget rules on. |
| `lobo_request_region_bytes_high_water` | gauge | `gen` | Highest MEASURED response-region charge of any single request served under the generation, read from the runtime's own ledger. A different unit from the admitted-bytes gauge and never to be subtracted from it. |
| `lobo_live_region_bytes` | gauge | — | Process-wide bytes the runtime holds for live regions at scrape time. NOT an RSS proxy: the process-root arena, where every string materialization still lands, is not counted. |
| `lobo_upstream_resolutions_total` | counter | `result` | Upstream names the resolver settled, by result (ok, failed). The failure reason is in the upstream-resolve-failed log event, not a label. |
| `lobo_log_lines_dropped_total` | counter | — | Access-log lines dropped because a sink's bounded buffer was full (emit never blocks). |
| `lobo_events_total` | counter | — | Vocabulary events emitted — the highest seq stamped. A log stream whose top seq matches this has no trailing hole. |
| `lobo_worker_id` | gauge | — | Which process answered this scrape: 0 for a single-process lobo, the worker's ordinal under a master. A scrape reaches ONE worker; the master's status is the sum across workers. |

## The endpoint

```
http {{
  server {{
    listen 127.0.0.1:9113;   # see the posture below
    metrics on;              # lobo-native; nginx -t rejects it (L010)
  }}
}}
```

`metrics on` publishes two paths on that server's listener:

| path | content type | body |
|------|--------------|------|
| `/metrics` | `text/plain; version=0.0.4; charset=utf-8` | the exposition above |
| `/status.json` | `application/json` | the SAME schema-1 object `lobo status --format json` serves over the control channel (ws08 designed it once; ws12 serves it twice) |

**The v0 access posture, plainly.** There is no authentication
on the endpoint beyond WHERE IT IS BOUND. The exposition names
your generations, your upstream error rates and your memory
high waters; bind the server to loopback or an admin network.
`LOBO-L011` says so at load time when it is not, as a warning
rather than a refusal — a private-network bind is a legitimate
posture lobo cannot tell from a public one by reading an
address. Authentication is ws14's; this line is the whole of
v0's story and it is deliberately short.

**Named limits at this pin**, so nobody has to discover them:

* the endpoint's own admin `listen` — the recommended shape —
  waits on multi-listener support: lobo binds ONE plaintext and
  ONE ssl listener, so `metrics` is a switch on the server it is
  written in, not a listener of its own;
* the endpoint answers on the PLAINTEXT step path only. Over
  TLS these two paths route to the filesystem like any other
  URI — the same D24 rider the ws10 counters carry;
* the switch is resolved at START. A reload that flips it takes
  effect at the next restart (`ServerOpts` is process-wide, not
  per-generation);
* the scrape is an ORDINARY request. It appears in these
  counters and in the access log, one scrape behind (a counter
  that included its own scrape would have to lie), and it obeys
  `memory_budget`: under a budget smaller than the exposition,
  the scrape is a 503 with a name. That is correct.

## The cardinality fence

The registry above is the ONLY place a label may be invented.
`metrics.sample` asserts that the label keys it was handed are
exactly the keys the family declared, so a per-URI or
per-client series is not expressible in lobo — not discouraged,
not linted: unwriteable. `tools/lobo-metrics` measures the
consequence on a live server, asserting that driving four more
distinct URIs adds exactly zero series. Metrics that explode
cardinality are how monitoring kills servers; the footgun gets
a fence, not a hope.


## The duration ladder

Both histograms use one FIXED ladder of upper bounds, in
seconds:

`0.005`, `0.010`, `0.025`, `0.050`, `0.100`, `0.250`, `0.500`, `1.000`, `2.500`, `5.000`, `10.000`, `+Inf`

It is fixed on purpose: a per-deployment ladder is a
configuration surface with a cardinality cost, and native
histograms are named post-v1.
