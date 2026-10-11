# ws60 — the split scalar

Wave 53, lane ws60 (Opus). Written on lobo trunk `20a952b` (ws59). The
planning contract is `sprints/wws/29-the-split-scalar/` in the private
`wolffe-lang/wolf`; rules `sprints/wave-53.md` down to `wave-45.md`.
Toolchain is the pin: wolf 0.2.27 / lupin 0.1.50 from the release
archives by digest, lobo's std `14f0ab2`. Oracle: the pinned nginx
1.30.4 (`65595ac2…`), run, never read.

One deliverable: no byte sequence a client can send makes a lobo worker
trap; every malformed shape is answered with the right 4xx (or a clean
close) on all four machines; a byte-level fuzz over the request path
holds the property.

## 1. Forbidden, absolutely

Verbatim from the contract and `wave-53.md`: no `rm` outside
`~/lanes/ws60/` and this lane's own clones (`/tmp` included, no scratch
in `/tmp`); no `git add -A`; nothing under `~/.claude`; no package
installs; no merge, tag or release; close no issue; no commit or PR
attribution trailers; checksums carry a trailing `…`; no "seen red"
without a run id, sha, path or digest. Strict evidence (wolf-lang#571):
`WOLF_PAIRING_REQUIRE_SIBLING=1`, stdout+stderr together, SKIP counted;
a `wolf build` exit 2 is a compile error, never a skip. No correctness
trade: the differential corpus and the equivalence rows stay green and
a request refused before is refused after, same status. No new `spawn
proc`, no channel send, nothing moved across a region block
(wolf-lang#660/#665/#678). Crafted requests go only to a lobo this lane
started on a lane-private loopback port (18660/18661 on kasumi); never
the live site, 8080, 8088 or a tunnel. kasumi: `bash -c`, kill by
recorded pid, prune as you go; no build on nomad-1. Until the fix is
merged, no public text gives a working recipe for the fault; the tests
carry the inputs, which is accepted.

## 2. Inputs, verified (re-derived 2026-10-11)

| input | found |
|---|---|
| lobo trunk | `origin/trunk` = `20a952b` (ws59); pins wolf 0.2.27, lupin 0.1.50, std `14f0ab2` |
| toolchain | wolf `6f5713a2…`, libwolf_rt.a `ab575b27…`, lupin `3a47644…` (re-checked from ws59's archives by digest; `toolchain-tc-0227.txt`) |
| trunk build | both tiers exit 0 at `--error-limit=0`; release `12fec915…`, debug `9a3f2d67…` (`build-wt-trunk.log`) |
| the fault | reproduced on the debug and release tiers at trunk, each on a fresh lane-private server; a crafted request kills the worker process with `wolf-trap: bounds` and the client gets no reply (`probe1-trunk.log`, `probe2-trunk.log`) |

## 3. The root cause, and the prediction (committed before the fix)

**Root.** lobo reads client bytes off the socket and holds them as a
`str` (`conn.sock_read` → `net_read_bytes` → `str_from_utf8`), so the
buffer is always valid UTF-8. The request path then computes **byte
offsets** while walking that `str` and slices it with `s[a..b]`. By
`[mem.str.get]` a checked slice faults `bounds` when an endpoint is not
a code-point boundary. When a computed offset lands inside a multi-byte
scalar, the slice traps and the worker dies. This is **not** a wolf bug:
`str` slicing is defined to fault on a non-boundary — that is why
`s.get(a..b) -> str ! {none}` exists as its recoverable twin. The bug is
lobo's alone: it treats a `str` as a byte buffer. No wolf-lang witness
is owed.

**Every site on the request path with this shape** (listed before the
fuzz, the census):

| file / fn | the slice | grammar | right answer |
|---|---|---|---|
| `http.starts_with_fold` | fixed-offset prefix of the request target (absolute-form `http://`/`https://` probe) | a split means a non-ASCII byte in the prefix, which can never equal the ASCII literal | not-equal (origin-form routing), request parses |
| `http.contains_fold` | a fixed window of a value scanned for an ASCII token | callers gate on `is_ascii`; a non-boundary window holds non-ASCII | skip the window (defence in depth) |
| `http.percent_decode` | per-character and hex slices of the target | a raw non-ASCII octet before a `%`-escape | decode over bytes; result validated once; bad escape still 400 |
| `http.decode_chunked` | the chunk-data and framing slices | a chunk whose size splits a scalar | framing error → 400 |
| `serve.take_length` | the fixed-length body split at Content-Length | the body boundary falls inside a scalar | clean close (str-only body at this pin) |
| `proxy.read_up_length`, `proxy.tls_read_len` | the upstream body split at its Content-Length | same, on the upstream response path | clean close → 502 at the caller |

Sites that are **already safe** and stay so: `end_request_line` /
`end_header_line` slice the method, target, version, name and value at
ASCII delimiters (SP, `?`, `:`, CR, the OWS edges), which are always
code-point boundaries; `eq_fold` and `parse_length` iterate `s.bytes()`
and never slice; `eq_ci`/`ci_contains` gate on `is_ascii` before any
byte-window compare; `normalize_path`/`is_canonical` slice the decoded
path at `/` (ASCII); `raw_line`/`head_cut` cut at CR/LF. ws59's one-walk
rewrite had already moved header-value slicing onto ASCII-delimited
boundaries, so the header-value shape the finding named **no longer
reproduces at `20a952b`** (it did at the finding's head); its live
analogue is the target absolute-form probe, covered above.

**Prediction.** Routing every one of these slices through `.get` (or,
for `percent_decode`, walking the bytes directly) turns the fault into
the status the grammar already assigns at that point and leaves every
legal request byte-identical. The equivalence rows (`parse_walk_equiv`,
`parse_walk_rows`) stay green because the only `parse_request` change is
`starts_with_fold`, whose split inputs the old `ref_*` parser trapped on
too (the corpus seeds carry no such input). The differential corpus and
the membudget gate are unchanged. The fuzz gate completes with no trap
and a well-formed row for every mutation.

## 4. The severity, plainly

Before: a single crafted request — a few dozen bytes, no authentication,
one TCP connection — makes a lobo worker process trap and exit. The
master logs `worker-exited` and respawns it, so the server as a whole
survives, but: the worker's other in-flight connections die with it
(any keepalive client mid-request on that worker gets a dropped
connection and no reply; a TLS session is torn down); and a client that
opens a connection per crafted request can keep one worker in a
respawn loop. With `worker_processes 1` the whole server is down between
the trap and the respawn. It is a remote, unauthenticated
denial-of-service against availability. After: the same bytes get a
well-formed 4xx or a clean connection close, the worker pid is
unchanged, and its other connections are untouched.

## 5. Done-when / evidence

Branch `ws60`; one commit per site plus this note and the tests; the
gauntlet green on kasumi and CI green at head on both hosts; the
equivalence rows green; the fuzz gate green; the e2e asserts the worker
pid is unchanged after each shape. Evidence under `~/lanes/ws60/` on
kasumi (not public before merge): the reproductions with digests, the
fuzz counts, the before/after severity. Close nothing.
