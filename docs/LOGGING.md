# Logs that parse (ws09)

The charter lists "Structured logs" as a *finally* item, and the compat
contract says an nginx.conf's `log_format`/`access_log` directives
CARRY. lobo holds both doors open:

- The nginx-compat door: `log_format` (with `escape=default`,
  `escape=json`, `escape=none`), `access_log <path> [format]
  [buffer=] [flush=]` and `access_log off`, `error_log <path>
  [level]` all carry, and the LINES are the oracle's bytes.
  `tools/lobo-logdiff` (a gauntlet step) runs the pinned nginx and
  lobo with the SAME log directives and the SAME raw requests,
  including the escape probe set (`"`, `\`, ESC, TAB, BS, FF, DEL,
  raw UTF-8, a percent-encoded target, a garbage request line with a
  bare CR), and byte-compares the logs modulo timestamps. nginx's log
  tooling parses lobo's access log because it IS nginx's format.
- The structured door (lobo-native, linted as such):
  `access_log <path> format=json;` writes ONE JSON OBJECT PER LINE
  with a versioned schema and TYPED values: numbers are numbers,
  which `escape=json` inside a string format can never give you.
  `error_log <path> <level> format=json;` does the same for the event
  stream. `log_headers A B C;` opts request headers into a nested
  object. Adopting the native parameters is a one-way door out of
  nginx-carryable configs and lint LOBO-L006 says so at load; the
  walk-back is deleting them.

The LINTER referees the tension: LOBO-L007 names what a used
`log_format` loses against the structured door (which typed facts it
never records; what `escape=default`'s hex-escapes and `-` conflation
cost a parser). It is a note, never a refusal, and the format still
carries as configured.

## The variable table (class-C, generated)

`docs/log-variables.md` is generated from `obs.var_table`
(`tools/lobo-logvars`, a gauntlet step). Implemented = what the
serving tree can know at this pin. A `log_format` naming a variable
whose row is not implemented is a CONFIG-TIME named error, never an
empty string at runtime; a variable with no row mirrors the oracle's
`unknown "x" variable`. (Verified against the oracle: nginx also
refuses unknown variables at load; the class-C posture here is about
lobo's own not-yet rows.)

## The escape rules (probed, pinned, held)

Probed byte-for-byte against nginx/1.30.4 (2026-08-30), pinned in
`tests/obs/escape_rules.lu`, held live by `tools/lobo-logdiff`:

- `escape=default`: `"` and `\` and every byte outside 0x20..0x7E
  become `\xHH`, hex UPPERCASE (`\x22`, `\x5C`, `\x1B`, `\x7F`,
  `\xC3\xA9` for é). A missing or empty value renders `-`.
- `escape=json`: `\"` `\\` `\b` `\f` `\n` `\r` `\t`, other C0 bytes
  as `\u00HH` (uppercase); 0x7F and >= 0x80 stay raw (probed; the
  compat door does what the oracle does). Missing/empty renders
  as the empty string.
- `escape=none`: raw bytes, empty stays empty.
- `$request` is the RAW request line, pre-decode (`/%41` logs as
  `/%41`); a garbage line is cut at its first CR (`BOGUS\rGARBAGE`
  logs `BOGUS`); a connection that never sent a request logs nothing.
- Log injection: a header value carrying CRLF cannot split a line in
  either door: `\x0D\x0A` in default, `\r\n` in json, structural
  escaping in the native JSON line.

## The native JSON schemas (version 1)

Access line (`access_log ... format=json`):

```json
{"schema":1,"time_iso8601":"2026-01-01T00:00:00+00:00",
 "remote_addr":"127.0.0.1","request":"GET /%41 HTTP/1.1",
 "status":200,"body_bytes_sent":79,"request_time":0.003,
 "upstream_addr":"127.0.0.1:8181","upstream_status":502,
 "upstream_response_time":0.012,
 "headers":{"user-agent":"x","x-req-id":"rid"}}
```

One line per request. `status`, `body_bytes_sent`, `request_time`
and the upstream trio are NUMBERS. The upstream keys appear only for
proxied requests; `headers` only when `log_headers` opted headers in
and the request carried at least one. Key names are the variable
names without the `$`.

Error line (`error_log ... <level> format=json`): `schema`,
`time_iso8601`, `level`, then either the DECODED EVENT, a message
whose first word is a ws08 vocabulary name and whose `k=v` fields
become typed members (`{"schema":1,...,"level":"notice",
"event":"generation-retired","gen":1,"drained":2,"aborted":0,
"age-ms":1840,"seq":8}`, the FROZEN field keys, verbatim), or the
whole message as `"msg"` (the ACME prose lines ride that way).
`seq` (ws11) is the vocabulary event's emission ordinal, stamped at
the seam and typed by the same generic decode; docs/DRAIN.md's
vocabulary section covers it. `schema` bumps only on a breaking
shape change.

## The writer discipline (D7-shaped; the contract's delta)

The ws09 contract predates wsm-era D7 (ONE spawn-free poll loop: no
writer task, no channel). What lobo does instead:

- Emit never blocks and never touches the fs. A served request
  becomes a record; rendering + `sink_emit` append to a BOUNDED
  in-memory buffer (`buffer=` maps to the cap; default 64 KiB). Over
  the cap the line is DROPPED AND COUNTED, so a dropped log line
  never becomes a stalled request.
- Flush is one bounded append per output per poll pass (the fs
  append tier, `O_APPEND`). A pass is milliseconds, so lobo flushes
  MORE often than any nginx `flush=` interval; `flush=` is accepted
  and subsumed (`buffer=` still required first, as nginx). The
  append happens ON the loop, so a pathological disk stalls a PASS
  (bounded by one buffer per sink) while the emit keeps going, and
  the drop counter is the pressure valve. A dedicated writer task
  rides the post-D7 concurrency story as a named row.
- A drop is reported: a per-output warn through the event seam
  (stderr + error_log), naming the output, the window count and the
  running total. An UNWRITABLE path drops-and-counts the same way,
  bounded memory, serving unharmed (`tests/obs/log_e2e_json.lu`).
- `reopen` (the ws04 verb) flushes and closes every output's fd;
  the next flush reopens at the configured path, so external
  logrotate works as it does against nginx. No self-rotation
  (`max_size` is a named post-v1 row, as the contract rules).
- Flush-on-quit/stop: the shutdown path flushes and closes every
  sink before the pid file is removed, so the last request of a quit
  run is in the log (`tests/obs/log_e2e_*.lu` pin it).

## Event levels (the ws08 vocabulary's level column)

docs/DRAIN.md has the level column beside the frozen vocabulary:
every drain event and the serving/arming notices log at `notice`;
sink-drop reports at `warn`; ACME issuance at `notice` and ACME
failure, TLS-config-keep and cert-load failures at `error`; startup
refusals at `emerg` (stderr; they precede the sinks). `error_log`'s
ladder is nginx's (`debug info notice warn error crit alert emerg`,
default `error`); an event logs to the file when its level is at or
above the configured one. STDERR KEEPS EVERY LINE as before ws09:
the ws02 seam the rig and the signal witness read is unchanged, and
the error_log file is a level-gated mirror.

### At the limits (ws64, lobo#84)

Four lines a process writes at `worker_connections` and out of
descriptors. Each is nginx's, body and level, measured on the pinned
oracle (notes/ws64-contract.md §2) and held beside it in
`tools/lobo-shell`:

| level | line | when | how often |
|---|---|---|---|
| `warn` | `512 worker_connections are not enough, reusing connections` | idle connections were closed to make room for a new one | at most once a second |
| `alert` | `512 worker_connections are not enough` | a new connection was closed at once: the process is at `worker_connections` and none is idle | once a refused connection (nginx does not rate-limit it either: 187 lines for 187 refusals) |
| `crit` | `accept() failed (24: Too many open files)` | the host refused an accept; the process then stops accepting for half a second | about twice a second for as long as it lasts |
| `crit` | `open() "<path>" failed (24: Too many open files)` | a request's file could not be opened for want of a descriptor; the request is answered 500 | once a request |

and one at start and at `-t`:

| level | line | when |
|---|---|---|
| `warn` | `512 worker_connections exceed open file resource limit: 256` | the process may not have as many descriptors as `worker_connections` |

Three deltas from nginx's lines, each named:

- nginx writes `accept4()` where the host has that call and
  `accept()` elsewhere; lobo writes `accept()` everywhere (which call
  the runtime makes is the runtime's).
- nginx's `open()` line goes on to name the client, the server, the
  request and the host; lobo's stops at the reason.
- The number and its text are the host's (`os_error`,
  `os_error_text`). wolf sets that number for file calls only, so
  after a failed accept lobo asks the host for a descriptor the file
  way (an open of `/dev/null`) and reports what THAT answers. If the
  open succeeds because a descriptor came back in between, the line
  is `accept() failed` with no number rather than a guessed one.

What becomes of a connection whose accept failed is the host's and
is the same under either server: linux leaves it in the listener's
queue, macOS drops it (`tools/lobo-shell` prints both servers' client
lines there instead of comparing them digit for digit).

nginx prints the start warning only when `error_log`'s level admits
a `warn` (its default level is `error`, so a default configuration
prints nothing); lobo's stderr carries every line whatever the level,
as for every other line, and its `error_log` file is gated the same
way nginx's is.

## Named deltas (routed to the wsc03 closeout)

- Clocks are UTC (`+0000` / `+00:00`): wolf has no timezone
  surface, and a zone-independent log is the better door anyway.
  logdiff normalizes timestamps; the SHAPE matches the oracle.
- Error lines carry no `pid#tid:`. wolf has `os_pid` since 0.2.29
  (the pid file is written with it, ws63) and no thread id; half the
  pair is not printed, and lobo does not fake the other half.
- `$remote_addr` is 127.0.0.1: no peer-address builtin, and the
  loopback-only law makes it truthful today; the row lifts with the
  builtin.
- No `access_log` directive means NO access log (nginx defaults
  to `logs/access.log` combined). The directive table has the row.
- Resolution is http/server level at v0; a location/if-level
  `access_log` parses and is NAMED inert (lint LOBO-L005).
- TLS connections are not access-logged at v0: the blocking TLS
  path predates the step loop (the D24 rider); logging joins when TLS
  joins `conn_step`.
- Reload: lobo's one process logs through the LIVE generation's
  outputs (nginx's old workers keep old-config logs).
- `worker=N` (ws16): under `worker_processes N` every line a hand
  writes to the error log ends in that trailing field (a number
  member in the JSON door; the k=v decode is unchanged). nginx's
  error lines carry `pid#tid:` instead, which lobo does not print (a
  pid since wolf 0.2.29, no thread id).
  Access lines carry no worker id on either server.
- `$upstream_status`/`$upstream_response_time` report the final
  attempt (nginx lists every tried peer's); `$upstream_addr` does
  list every tried peer, comma-joined.
- Error-page `$body_bytes_sent` differs by the server-identity
  footer (the documented body delta); logdiff's error round omits
  the bytes field.
- `$request_time` is start-of-request to completion in ms
  precision, the three decimals nginx prints: from the clock read
  after the wait that brought the request's first bytes, to the
  response's end — for a proxied request, the clock its exchange read
  when it ended, the reply written or the client's close seen (ws69,
  lobo#105; through ws68 both ends were the loop's pass clock, read
  before its wait, so a request on an idle keepalive connection logged
  up to 0.250 where nginx logs 0.000).
- `access_log ... gzip=`/`if=` are named post-v1 refusals at -t.
