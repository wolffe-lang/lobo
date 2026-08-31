# Architecture (ws00 — honest edition: mostly stubs)

lobo is a from-parts wolf program: zero dependencies, net/fs/process
via the language's builtin tiers, the pinned nginx under
`tests/differential/` being test infrastructure rather than a
dependency. One directory = one module (D32); every module's public
surface is a checked-in `.wolfi` snapshot beside it (the many-hands
rule: internals are yours, surfaces are contracts — see
`tools/lobo-interface` and CLAUDE.md).

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
             oracle-pinned escapers, JSON doors, bounded sinks);
             metrics land ws12            [real; wsc03]
```

Intended call direction once real (locked by the sprint contracts,
not by this page): `main → shell → {config, serve}`;
`serve → {http, proxy, obs}`; `proxy → {http, obs}`; `config` and
`http` call nobody above the builtin tiers. `obs` is called by
everyone and calls nobody. A dependency arrow not in this list is a
contract change — say so in the sprint file, not just the code.

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
