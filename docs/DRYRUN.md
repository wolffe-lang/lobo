# The dry-run that means something (ws07)

`nginx -t` checks syntax. `lobo -t --request ...` checks MEANING: what
would this config DO with this request. It reports the matched server,
the matched location with a WHY-IT-LOST trace for every candidate that
was considered, the effective directives with `-T` provenance, and the
terminal decision, all offline: no listener, no network, deterministic.
This page is the CONTRACT for the surface and its JSON schema; the
stanza snapshots live under `tests/dryrun/probes/` (one per
config-corpus entry, reviewed), and `tools/lobo-dryrun` is the gate.

## The surface

```
lobo -t [-p prefix] [-c file] \
    --request '<method> <scheme>://<host>/<path>[?query]' ... \
    [--sni <name>] [--client <addr>] [--stat] [--format json]
```

- `--request` is REPEATABLE: a batch of probes answers in one run,
  one stanza (or one JSON object) per probe, in order. The URL is
  absolute-form and is parsed by ws02's request parser (the one
  target parser this codebase has, the same code path a wire request
  takes, including percent-decode → control gate → dot-segment
  normalize, in serve/'s order). A request those gates would refuse
  is answered with the PREDICTED refusal (400/414/501).
- `--sni <name>` feeds the ws05 TLS selection logic (config.ssl_select)
  for an `https://` probe: the stanza names the certificate entry the
  live handshake would present. No TLS runs; the selection is a pure
  function of the resolved cert table.
- `--client <addr>` supplies the one decision input an offline run may
  take from the operator: the client address. Without it,
  `$remote_addr` renders UNRESOLVED.
- `--stat` is the fs OPT-IN: the default run reports the mapped path
  and says `(not checked)`; `--stat` stats it and reports what the
  live fs dispatch would then do (file → serve; directory without a
  trailing slash → 301; directory with one → index scan or 403;
  absent → 404). Readability is probed with a real open; the pin has
  no permission-bits builtin (a named gap).
- `--format json` emits the machine twin (below).
- Exit code is `-t`'s: a config that fails `-t` prints the same
  `[emerg]` lines and predicts NOTHING. The dry-run knobs require
  `-t`; anywhere else they are a named CLI error.

## The why-it-lost trace

The candidate list comes from the REAL matcher: `http.route_traced`
is `route` with a trace collector parameter (want=false on the serving
hot path leaves it empty and allocation-free). Each candidate carries
a STABLE code plus operator prose from ONE table (`dryrun.why_prose`,
pinned by `tests/dryrun/why_table.lu`; ws-docs reuse the wording from
there):

| code | meaning |
|---|---|
| `first-server` / `not-first-server` | the first server block wins — server_name/Host selection is parse-only at this pin (a named delta) |
| `exact-match` / `exact-miss` | `location =` beats everything / the path is not exactly the argument |
| `longest-prefix` / `shorter-prefix` | the longest matching prefix wins / matched but shorter |
| `lost-to-exact` | matched, but an exact location takes precedence |
| `prefix-miss` | the path does not start with this prefix |
| `regex-parse-only` | regex locations never win a route at this pin (a named delta) |
| `named-location` | `@` locations are unreachable by URL |
| `tie-first-wins` | equal-length prefix — the earlier block wins |

Precedence, in one line (nginx's real order, minus the regex tier this
pin does not match): `= exact > longest prefix (regex is parse-only at
this pin and never wins)`.

## Decision kinds

- `serve`: the mapped fs path (root append / alias replace), with the
  index candidates on a directory request. Reported, `(not checked)`,
  unless `--stat`.
- `proxy`: the outbound upstream URL through ws03's REAL rewrite
  arithmetic (`proxy.rewrite_target`), the pool and its peer set, and
  the proxy_set_header rows with variables resolved-or-UNRESOLVED
  (never guessed: `$proxy_add_x_forwarded_for` depends on the inbound
  request and is always UNRESOLVED offline).
- `refuse`: a NAMED refusal with its predicted status: parse-stage
  400/414/501, routing 404, static-method 405, empty-pool 502,
  proxy-over-TLS 502 (the ws05 residue, predicted as the live server
  answers it).
- `none`: no listener for the probe's scheme: no HTTP answer at all,
  with the reason (never a guessed status).

The winning chain's directives whose table rows are not `implemented`
are called out in one aggregated `note:` line; `return 301` above a
404 decision gets its explanation.

## The JSON twin (schema 1)

`--format json` is a public tooling surface from day one (the
ws08/ws12 convention), so it is versioned before anyone depends on it,
hand-built
like the ws08 status surface and validated by an INDEPENDENT reader
(std.x.json) in `tests/dryrun/json_valid.lu`.

```
{ "schema": 1, "tool": "lobo --request", "requests": [ {
    "request":  { "method", "scheme", "host", "target", "path", "query" },
    "listener": "<bind or ''>",
    "tls":      "<selection note or ''>",
    "server":   { "row", "file", "line", "server_name" } | null,
    "location": { "row", "matched", "file", "line" } | null,
    "considered": [ { "kind": "server"|"location", "row", "file",
                      "line", "modifier", "key", "outcome": "won"|"lost",
                      "why": "<code>", "detail", "prose" } ],
    "directives": [ { "raw", "file", "line", "via" } ],
    "notes":    "<aggregated not-implemented note or ''>",
    "headers":  [ { "name", "value", "resolved": bool,
                    "unresolved": "<reason, when resolved is false>" } ],
    "decision": { "kind": "serve"|"proxy"|"refuse"|"none", "status",
                  "path"?, "checked": false, "alias"?: true, "index"?,
                  "upstream"?, "pool"?, "peers"?, "note"? },
    "stat":     "<--stat note or ''>"
} ] }
```

Schema changes bump `"schema"` and this page in one commit.

## The anti-drift gate: predicted vs live

`tools/lobo-dryrun` (a gauntlet step) runs two cross checks on every
gate:

- static: predict `GET /index.html` over the differential's own
  config (decision kind, mapped path, `--stat` existence), then start
  the REAL server on the same rendered config, send the same request,
  and assert the live status matches and the live body is
  byte-identical to the file at the PREDICTED path; a missing path is
  predicted 404-under-`--stat` and must answer a live 404.
- proxy: predict the outbound upstream target for `GET /rewrite/a`
  over the proxy differential's config, then run the real proxy
  against a rig backend and assert the request line the backend
  RECORDED is the predicted target.

Purity is checked the same way: the whole offline pipeline runs on the
interpreter lane (`tests/dryrun/purity_offline.lu`), which has no
sockets and no fs, so any io on the called path turns the lane red.
The probe count is ratcheted
(`tests/dryrun/probe_ratchet.lu`): raising is routine, lowering needs
the commit message to say why.
