# Architecture — the module map, measured against the tree

lobo is a from-parts wolf program: zero dependencies, net/fs/process
via the language's builtin tiers. The pinned nginx under
`tests/differential/` is test infrastructure. One directory = one
module (D32); every module's public surface is a checked-in `.wolfi`
snapshot beside it (the many-hands rule: internals are yours,
surfaces are contracts; see `tools/lobo-interface` and CLAUDE.md).

Everything below is read off the tree, not intended for it: the
modules are `find src -name '*.lu'`, the arrows are the `use` lines,
and no arrow here is a plan. Re-read at **ws29** (lobo#4's second
item, whose first pass wrote this page at ws22 against v0.1.0); the
sprint that moves a module or an arrow re-reads it again.

## The modules

Thirteen, plus `src/main.lu`. `src/root.wolfi` names the twelve `main`
imports; `budget` is the thirteenth and is reached through `serve`.

| module | what it owns | landed |
| --- | --- | --- |
| `config/` | nginx.conf: lexer, parser, include graph, directive tables, the load-time lints, and `-T`'s provenance | ws01 |
| `http/` | request/response types and the RFC 9112 MUST-checklist HTTP/1.1 parser | ws02 |
| `serve/` | listeners, connection lifecycle, static serving, the per-connection step the poll loop drives | ws02 |
| `proxy/` | upstream pools, `proxy_pass`, hop-by-hop header discipline | ws03 |
| `shell/` | the CLI grammar, the text builders, the pid lifecycle, the control channel and the reload verbs | ws04 |
| `tls/` | what travels on the fd: TLS records off a socket, ClientHello parse, the server flight (`std.x.tls` owns the schedule) | ws05 |
| `conn/` | THE SEAM — a connection read/written/deadlined/closed without knowing whether bytes are in the clear or inside TLS 1.3 records | ws05 |
| `acme/` | the RFC 8555 client: DER writers, Ed25519 keys, PEM both ways, the atomic store, and the issuance flow | ws06 |
| `dryrun/` | what a config would DO with a request — matched server, matched location with a why-it-lost trace, effective directives with provenance. Offline, no sockets, no fs | ws07 |
| `obs/` | logging: the format compiler, the variable table, the oracle-pinned escapers, the JSON doors, bounded sinks | ws09 |
| `metrics/` | the counter registry, the cardinality fence, the Prometheus text exposition. PURE: no io, fs, net or clock | ws12 |
| `resolver/` | async upstream DNS: a stub client over TCP the one poll loop multiplexes, plus the TTL cache `resolver … valid=` names | ws13 |
| `budget/` | the proc boundary D68's region cap needs — a budgeted request's regioned work runs inside `spawn proc` here, and the join maps the exit reason for `serve` | ws13 |

`src/main.lu` is not thin. It is the largest single file in the tree
(~3,700 lines, against `serve/serve.lu`'s ~2,650 and
`proxy/proxy.lu`'s ~2,000) because it owns the things that cannot
live in a module: the ONE poll loop that multiplexes the http
listener, the control channel, the signal forwarder's pipe and every
open connection; the per-generation drain bookkeeping ws08 made
watchable; the prefork master and its per-worker control endpoints
(ws16/ws17, D73 — D7 kept inside every process); and the two-phase
`/metrics` render. The CLI grammar it dispatches over is `shell/`'s.

D7 in one sentence, as ws29 (lobo#8) left it: the serving loop is
spawn-free, and the ONE proc beside it is `sig_forwarder`, parked in
`os_signal_wait` for the process's life so that a signal is
READINESS on a socket the loop already waits on rather than something
the loop has to go and ask about. It holds two ints and a socket and
touches no server state.

## Who calls whom

Read from the `use` lines, both directions:

```
main    → acme config conn dryrun http metrics obs proxy resolver
          serve shell tls          (everything but budget)
serve   → budget config conn http metrics obs proxy resolver
proxy   → config http resolver
dryrun  → config http proxy
conn    → tls
http    → config
shell   → config
tls     → config
acme budget config metrics obs resolver → nobody in lobo
```

Six modules call no other lobo module: `acme`, `budget`, `config`,
`metrics`, `obs` and `resolver`. `config` is the one of those every
layer above reads.

Two arrows the ws00 map predicted and the tree does not have. `proxy`
does not call `obs`: it is not "called by everyone", it is called by
`main` and `serve`. And `serve` does not call `tls`; it calls `conn`,
which is the seam holding. `serve → {http, proxy, obs, resolver}` from
the old page is right as far as it goes and short by `budget`, `config`,
`conn` and `metrics`.

`metrics` stays two-phase for the reason the ws00 page gave, and that
reason survives the re-read: `serve` calls `metrics` only for the two
endpoint PATH constants, never for a number — the exposition cannot
reach into a serving module and a serving module cannot render one.
`src/metrics/metrics.lu`'s header and the seam in `serve` both say so.

A dependency arrow not in this list is a contract change: record it in
the sprint file as well as in the code, and re-read this page when you
do.

## Where the detail lives

| page | for |
| --- | --- |
| [CONTROL.md](CONTROL.md) | the control channel: transports, verbs, auth |
| [DRAIN.md](DRAIN.md) | reload, drain and the signal/verb split |
| [WORKERS.md](WORKERS.md) | prefork, the master, accept distribution |
| [RESOLVER.md](RESOLVER.md) | the DNS stub client and its cache |
| [BUDGET.md](BUDGET.md) | the region cap and its proc boundary |
| [LOGGING.md](LOGGING.md) · [log-variables.md](log-variables.md) | `obs` |
| [metrics.md](metrics.md) | the registry, generated |
| [directives.md](directives.md) | the config surface, generated |
| [DRYRUN.md](DRYRUN.md) · [DIFFERENTIAL.md](DIFFERENTIAL.md) | what lobo promises against nginx |
| [PARITY.md](PARITY.md) · [PROFILE.md](PROFILE.md) | the performance pair: PARITY sets the bar, PROFILE says what stands in the way |
| [REPLAY.md](REPLAY.md) | a concurrency schedule replayed from an artifact (ws11) |
| [GETTING-STARTED.md](GETTING-STARTED.md) | the learner path against an unpacked release archive |

Three of those pages are GENERATED and are never hand-edited —
`directives.md` from `src/config/table.lu` (`tools/lobo-directives`),
`metrics.md` from `metrics.registry` (`tools/lobo-metricsdoc`), and
`log-variables.md` from `obs.var_table` (`tools/lobo-logvars`).

## Test infrastructure (not part of the server)

`tests/` mirrors `src/` — one directory per module (`acme config
dryrun http metrics obs proxy replay resolver serve shell tls`) — plus
four that belong to nobody's module:

```
tests/rig/           the harness, in wolf, all of it loopback:
  httpc/             client module (exchange, exchange_once,
                     split_reply, has_header)
  echosrv/           rig-private one-exchange server (NOT serve/'s
                     territory)
  acmeca/            a test CA the ACME flow issues against
  dnssrv/            a stub DNS server the resolver resolves against
  rigback/           a backend the proxy proxies to
  *.lu               drivers: freeport, diffsend, holdconn, memdrive,
                     nowms, reloadhold, resolvedrive, …
tests/differential/  the pinned-nginx differential (docs/DIFFERENTIAL.md)
tests/config-corpus/ eight real-world nginx.conf fixtures (certbot
                     vhost, distro default, php-fpm, openresty, …)
tests/cve-corpus/    the historical-CVE corpus ws02 declared
tools/               the gauntlet and thirty-odd single-purpose tools
                     beside it (sh + jq; the tests themselves are wolf)
```

Every test is loopback-only, port 0 (or OS-chosen), deadline on every
read, and writes its scratch under `target/` — the repo root is not a
scratch directory, and since ws29 (lobo#2) the gauntlet's census step
fails RED, by name, on a run that leaves a file in the tree.
The gauntlet (`tools/lobo-gauntlet`) is green before any commit.
