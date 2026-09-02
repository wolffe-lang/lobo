# The name resolves in time (ws13)

nginx resolves a `proxy_pass http://name` **once, at load, and never
again** — a backend that moves is a 502 until someone reloads, which
is trac #1064's complaint and report 11 §2 item 9's evidence: "async
DNS for upstreams", STRONG demand, the last strong-evidence item
wsc03 left unshipped. lobo before ws13 was worse on one axis and
better on the other: the name reached `net_connect` as text and the
host resolver answered it **at every dial**, synchronously, on the
ONE poll loop's thread, with no deadline. Fresh addresses, but a slow
or dead nameserver stalled every connection behind it.

This page is the design that fixes both, the measurement that proves
it, the deltas from nginx's `resolver` named one by one, and the two
upstream asks the design had to route around.

## The measurement (tools/lobo-resolver, a gauntlet step)

A real lobo, a loopback DNS server that answers only after a scripted
delay (`tests/rig/dnssrv`, 800 ms), a loopback backend, and one
driver that sends a PROXIED request whose upstream is a name and — at
once, on a second connection — a STATIC request, timing both:

| | `static-ms` (the second connection) | `proxied-ms` | `cached-ms` (a second request for the name) |
|---|---|---|---|
| **before** — the name resolved inline on the loop thread (the pre-ws13 shape, measured by disabling the wait) | **805** | 805 | 1 |
| **after** — the request parks; the loop keeps serving | **1** | 836 | 0 |

Measured 2026-09-02 on macOS/arm64 at the ws13 pin trio. The before
row is the stall: the static request waited the resolver's whole
delay although it needed no name at all. The after row is the
sprint's point: one millisecond, while the resolver held its answer
for eight hundred. The proxied request itself waits for the answer —
as it must — and the second request for the same name makes no round
trip (the DNS server's record file holds exactly one query).
`tests/resolver/proxy_e2e.lu` pins the same story in the corpus on
both native tiers, with the test as the DNS server and the backend.

## The design: a DNS client the loop multiplexes

There is no blocking call to wrap. `net_connect` hands its address
string to the host, which resolves a NAME synchronously with no
deadline (`wolf_rt/src/net.rs`: `TcpStream::connect(addr)`; the
runtime's own `connect_timeout` resolves first and times only the
handshake — and it is not surfaced to wolf at all). std.net says in
its own header that `dns`/`resolve` is not a function it has. So the
only way to turn a name into an address without stalling the loop is
to **speak DNS over a socket the loop already knows how to wait on**,
and that is what the new `resolver` module does — the whole thing,
spawn-free, in three halves:

1. **The wire** (`resolver.build_query` / `parse_answer`, pure over
   `List[int]`): an A/IN query under RFC 1035 §4.2.2's two-byte TCP
   length prefix; the answer parsed with compression pointers, CNAME
   records skipped (the recursive resolver already flattened the
   chain into the answer section), every A record collected in
   answer order, the SMALLEST TTL kept. Every malformed shape and
   every RCODE is a named failure, never a trap.
2. **The cache**: host → address set + expiry + a round-robin cursor.
   `valid=` overrides the record TTL exactly as nginx's parameter
   does. A 0-TTL answer is held one second, and so is a failure (both
   named below).
3. **The pending table**: one TCP query socket per in-flight name.
   Each poll pass the loop calls `resolver.tick`, which gives every
   pending socket a 1 ms read deadline and one bounded read — a
   complete frame settles the name, a closed socket settles `io`, a
   deadline past `resolver_timeout` settles `timeout`. Nothing else
   waits.

**The park.** `serve` asks `proxy.resolve_need` BEFORE it reads a
byte past the request head: is this route's upstream a name the
resolver has not answered fresh? If so it returns a `ConnStep` that
served nothing and carries the WHOLE buffer back, naming the host.
The loop marks the connection parked on that name, calls
`resolver.start` (a no-op while a query is in flight or the cache is
fresh), and skips the row on every pass until the name settles. Then
the row is stepped again from the top: the head is still in its
carry, the cache is warm, and the dial gets an address. A parked
connection's idle clock does not run (waiting on the resolver is
work); `resolver_timeout` bounds the park.

**The dial.** `proxy.run` expands each peer through the cache: an IP
literal is itself; a name with no `resolver` in effect is itself and
the dial resolves it as before (L012 said so at load); a name under a
resolver becomes its cached addresses rotated round-robin (nginx's
"several addresses, used in a round-robin fashion"), tried in the
existing connect-failure order; a held failure expands to nothing —
the peer is skipped, or the request is a 502 naming the host. The
access line's `$upstream_addr` names the RESOLVED address, as
nginx's does.

**The blocking driver** (`serve.serve_conn`, which the rig and the
differential drive directly) has no loop to park on: a name it meets
resolves INLINE through the same client, bounded by
`resolver_timeout`. That inline path is what the before row above
measured on the loop thread.

## The directives

```nginx
http {
    resolver 127.0.0.53 valid=30s;   # http, server or location
    resolver_timeout 5s;             # default 30s, nginx's
    server {
        location /api/ { proxy_pass http://api.internal:9000/; }
    }
}
```

Both carry nginx's grammar and `-t` answers nginx's own wording for a
parameter nginx would refuse (`invalid parameter "x"`); the two
parameters nginx accepts but lobo cannot honour refuse BY NAME
(`ipv4=off` — A records only at this pin; `status_zone=` — no
resolver status zone, the counters are at `/metrics`). The full rows
are in `docs/directives.md`.

**Lints.** LOBO-L012 fires when a `proxy_pass` or an upstream
`server` names a hostname with no `resolver` in effect: that name is
resolved by the host resolver at every dial, synchronously, on the
loop — the stall this page measures. LOBO-L013 fires when a resolver
IS in effect for a static `proxy_pass` name, because that is the
delta below, in lobo's favour, and a load-visible delta is linted.

## Deltas from nginx's `resolver`, named

| nginx | lobo | why |
|---|---|---|
| a static `proxy_pass http://name` resolves ONCE at load via the system resolver; `resolver` applies only to the variable form and `server … resolve` | `resolver` applies to static names too: resolved at runtime, cached under the TTL / `valid=`, re-resolved when stale — no reload | the finally-list item itself (trac #1064); L013 says so at load |
| UDP first, TCP on truncation | TCP only | wolf has no UDP surface; every recursive resolver answers on 53/tcp (RFC 7766 §1) |
| `ipv6=on` by default: A and AAAA | A only; `ipv6=on` accepted and answers nothing, `ipv4=off` refused at -t | lobo binds and dials IPv4 on loopback; AAAA rides the next pin that needs it |
| several resolver addresses, round-robin | the FIRST address | one query socket per name at this pin |
| a failed name is re-asked on the next request | a failure is held **1 s** | a dead name would otherwise make a query storm of the loop; the hold is one second, not a cache |
| a 0-TTL answer is re-resolved per request | held **1 s** | a request parked on a name that is stale the instant it lands would park forever |
| `status_zone=` | refused by name | `/metrics` carries `lobo_upstream_resolutions_total{result}`; no zone |
| the resolver is dialled by nginx's event loop with a timeout | `net_connect` to the resolver address: instant on loopback, one handshake RTT in production, bounded only by the OS | the prelude surfaces no connect deadline — the filed half below |

Where nginx's semantics carry they carry byte for byte: the
directive grammar, `valid=` overriding the TTL, `resolver_timeout`'s
default and meaning, `$upstream_addr` naming the resolved address,
NXDOMAIN and a no-address answer as 502. The proxy differential's
conf.in pair carries a `resolver` line on both sides so the oracle
and lobo prove they PARSE the same directive; the cases dial
literals, so neither consults it — the runtime semantics are lobo's
own by design, and this table is where they are named.

## Observability

- **Events** (ws09 vocabulary, appended — nothing renamed; docs/
  DRAIN.md has the table): `upstream-resolved host=<h> addrs=<n>
  ttl-ms=<ms> took-ms=<ms>` at notice; `upstream-resolve-failed
  host=<h> reason=<nxdomain|servfail|refused|noaddr|malformed|rcode|
  timeout|io|dial> took-ms=<ms>` at error. Both `seq=`-stamped by the
  emission seam.
- **Metric**: `lobo_upstream_resolutions_total{result="ok"|"failed"}`
  — a fixed two-value label set, both series always present; the
  reason lives in the event, not a label (the ws12 cardinality
  fence).

## The asks, filed not absorbed

- **wolf-std** — a resolver surface in `std.net` (`resolve(name) ->
  List[str] ! {not_found, timeout, io}` or the like), so a program
  can turn a name into an address without either blocking in the
  dial or carrying its own DNS client. **wolf-std#4**, filed the day
  this shipped.
- **wolf-lang** — `net_connect` resolves a name synchronously on the
  calling thread with no deadline, and the runtime's `connect_timeout`
  (which exists in `wolf_rt`) reaches no lane; a `net_resolve`
  builtin with a deadline (reactor-routed where a reactor exists)
  and a surfaced connect deadline would let this module's dial to the
  resolver itself be bounded. **wolf-lang#217**, filed alongside.

When either lands, the wire half here shrinks to a call and the park
stays exactly as it is — the seam was drawn at the socket on purpose.
