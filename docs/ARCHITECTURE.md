# Architecture (ws00 — honest edition: mostly stubs)

lobo is a from-parts wolf program: zero dependencies, net/fs/process
via the language's builtin tiers. The pinned nginx under
`tests/differential/` is test infrastructure. One directory = one
module (D32); every module's public surface is a checked-in `.wolfi`
snapshot beside it (the many-hands rule: internals are yours,
surfaces are contracts; see `tools/lobo-interface` and CLAUDE.md).

## The module map, and who calls whom

```
src/
  main.lu    entry — version print + arg dispatch ONLY, forever thin;
             calls: every module's version() (banner), shell/ (ws04+)
  config/    nginx.conf loading: lexer, parser, include graph,
             directive tables            [stub; ws01]
  http/      request/response types, HTTP/1.1 parsing (RFC 9112 MUST
             checklist)                  [stub; ws02]
  serve/     listeners, connection lifecycle, static serving
             (thread/task-per-connection — the honest v0; the s35
             reactor is the C10k phase)  [stub; ws02]
  proxy/     upstream pools, proxy_pass  [stub; ws03]
  shell/     CLI verbs, signals, reload (split on the upstream
             signal-reception ask)       [stub; ws04]
  obs/       logging (ws09: format compiler, variable table,
             oracle-pinned escapers, JSON doors, bounded sinks)
                                          [real; wsc03]
  resolver/  async upstream DNS (ws13): the DNS-over-TCP wire half
             (pure), the TTL cache, and the pending-query table the
             poll loop ticks like any other socket — a leaf that calls
             nobody; docs/RESOLVER.md   [real; wsc05]
  metrics/   the counter registry and the Prometheus text exposition
             (ws12: names/types/help/label shapes in ONE table, the
             cardinality fence in `sample`, the fixed histogram
             ladder). PURE — the counters themselves live in main's
             poll loop, because lobo is spawn-free and one mutator
             needs neither shards nor atomics
                                          [real; wsc03]
```

Intended call direction once real, as the sprint contracts lock it:
`main → shell → {config, serve}`;
`serve → {http, proxy, obs, resolver}`; `proxy → {http, obs,
resolver}`; `config` and `http` call nobody above the builtin tiers.
`resolver` (ws13) is the third leaf: `proxy` asks it which name a
request must wait for and what a cached name expands to, `serve`
carries its state through the step, and `main` owns that state and
ticks it once per pass. The arrows `main → resolver`, `serve →
resolver`, `proxy → resolver` come from ws13, declared in its
contract's closeout. `obs` is called by everyone and calls nobody.
`metrics` (ws12) is the second leaf beside `obs`: it calls nobody.
`main` calls it for the exposition; `serve` calls it only for the two
endpoint PATH constants, never for a number: the exposition cannot
reach into a serving module, and a serving module cannot render one.
The `/metrics` endpoint is TWO PHASE for that reason (`serve`
recognises the request, `main` renders it); and
`src/metrics/metrics.lu`'s header and the seam in `serve` both say
so. A dependency arrow not in this list is a contract change: record
it in the sprint file as well as in the code.

## Test infrastructure (not part of the server)

```
tests/rig/           the loopback HTTP client harness, in wolf:
  httpc/             client module (exchange, exchange_once,
                     split_reply, has_header)
  echosrv/           rig-private one-exchange server (NOT serve/'s
                     territory)
  *.lu               directive tests + drivers (freeport, diffsend)
tests/differential/  the pinned-nginx differential (docs/DIFFERENTIAL.md)
tools/               lobo-gauntlet and its steps (sh + jq; the tests
                     themselves are wolf — .docs/STYLE.md records why)
```

Every test is loopback-only, port 0 (or OS-chosen), deadline on every
read. The gauntlet (`tools/lobo-gauntlet`) is green before any commit.
