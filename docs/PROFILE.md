# Where the time goes (ws22, measured 2026-09-08)

The bar is `docs/PARITY.md`; this page is the profile that says what
stands between lobo and it. The tool is `sample(1)` (macOS's sampling
profiler, no root needed for one's own process): ten seconds at one
millisecond on ONE serving process while `ab -t 20 -c 32` drives it,
the same 1 KiB file, the same loopback, the same session for every
row. Numbers are the MAIN THREAD's — `sample` counts parked threads
too, and lobo has three (main, `wolf-reactor`, `wolf-signal`); the
two helpers sit 95–99% in `kevent` and `read` respectively and are
not where the time goes. Host: nomad-1, Apple M5 Pro (12P+6E),
macOS 26.4.1; lobo 0.1.0+dev at wolf 0.2.6 pin 398e5f5,
`WOLF_MIDEND=0`; nginx 1.30.4 (the pin). **Load(1m) 6.3 at the start
and 16.8 at the end** — a sibling lane's corpus loop held one core
throughout, so the PROPORTIONS are the claim here and the absolutes
are indicative; the parity ledger is where absolutes live.

The guess has been wrong twice in this repo (ws17, ws18). This is
not a guess.

## One process, keepalive — lobo 12,192 req/s (82 µs/request) beside nginx 58,482 (17 µs)

lobo, main thread, 7,512 samples, leaves (top of stack):

| samples | share | leaf | what it is |
|---|---|---|---|
| 2,981 | **39.7%** | `__psynch_cvwait` | parked on a Condvar in `wolf_rt::reactor::wait_on`, waiting for the `wolf-reactor` thread to confirm a readiness the loop already had |
| 1,082 | 14.4% | `__open` | `fs_read_bytes` opening the file, every request |
| 805 | 10.7% | `stat` | THREE per request: `fs_is_file`, `fs_size`, `fs_modified_ms` |
| 564 | 7.5% | `__sendto` | TWO per response: the head, then the body |
| 514 | 6.8% | `kevent` | the caller's own: arm (`EV_ADD\|EV_ONESHOT`) + wake (`EVFILT_USER`), per socket op |
| 294 | 3.9% | `__recvfrom` | the request read |
| 123 | 1.6% | `read` | the file read |
| ~420 | ~5.6% | memmove, malloc/free, mutex, `mach_absolute_time` | runtime bookkeeping |
| 55 | 0.7% | `poll` | `net_wait` — the loop's own readiness ask, for ALL sockets at once |

Inclusive, by the shallowest runtime entry on each stack:

| samples | share | entry | the syscall inside it |
|---|---|---|---|
| 1,663 | 22.1% | `__wolf_rt_net_read` | `recvfrom` 3.9% |
| 1,489 | 19.8% | `__wolf_rt_net_write_bytes` | `sendto` ~3.7% |
| 1,444 | 19.2% | `__wolf_rt_net_write` | `sendto` ~3.8% |
| 1,301 | 17.3% | `__wolf_rt_fs_read_bytes` | `open` 14.4% + `read` + `close` |
| 524 | 7.0% | `__wolf_rt_fs_is` | `stat` |
| 288 | 3.8% | `__wolf_rt_fs_stat` | `stat` ×2 |
| 368 | 4.9% | `__wolf_rt_strbuf_*` | string building (the response head, the log line) |
| 67 | 0.9% | `__wolf_rt_net_wait` | `poll` |
| ~100 | ~1.3% | `list_new`/`list_push`/`str_find` | |
| rest | ~3% | lobo's own `_W*` frames, self time | the parser, the loop, the table |

nginx, one worker, same everything, 7,708 samples: `open` 51.8%,
`writev` 20.6%, `recvfrom` 9.0%, `pread` 4.2%, `close` 3.8%, `fstat`
2.8%, `kevent` 1.2%, everything nginx-named ~3%.

### Reading it

In microseconds of the 82 (lobo) and 17 (nginx):

| where | lobo | nginx | whose |
|---|---|---|---|
| **the reactor round-trip** — cvwait + the caller's kevent + submit's Arc/HashMap/heap/mutex, three times per request (read, write, write) | **~38** | 0.2 | **wolf's** — `NetTable::read/write/accept` park on the reactor BEFORE the syscall (wolf-lang#257) |
| `open(2)` | 11.8 | 8.9 | the kernel's — both pay it (nginx has `open_file_cache`; lobo has nothing yet) |
| `stat` ×3 vs `fstat` ×1 | 8.8 | 0.5 | **lobo's** shape: three path stats where one fd stat would do |
| socket syscalls: two `sendto` + `recvfrom` vs one `writev` + `recvfrom` | 9.4 | 5.0 | half lobo's (two writes), half the language's (no `writev`, no `TCP_NODELAY` — wolf-lang#254; on linux the pair stalls 40 ms — lobo#3) |
| file read + close | 2 | 1.4 | — |
| user space (wolf `strbuf`/list/malloc ~7; lobo's own code ~2) | ~9 | ~0.5 | mostly the runtime's string materialization (wolf-lang#191's seam); lobo's parser and loop are ~2 µs |
| `net_wait` | 0.6 | 0.2 | — |

**The split: of lobo's 82 µs, ~45 are the language's (the reactor
handoff, the string runtime, the missing writev), ~20 are lobo's own
choices (three stats, two writes, per-request open with no cache),
and ~15 are what nginx pays too.** lobo's own code — the parser, the
loop, the config table — is about 2 µs of 82. Nothing in lobo's user
space is worth optimizing before the two shapes above are.

## One process, close — lobo 8,526 (117 µs) beside nginx 28,376 (35 µs)

Same picture plus the accept: lobo main thread cvwait **42.9%**,
`net_accept` 9.5% inclusive with `accept(2)` itself 1.2%, `net_wait`
4.6%, `net_close` 1.6%; `open` 11.6%, `stat` 9.0%, `sendto` 6.9%.
nginx: `open` 35.4%, `kevent` 31.2% (its idle wait — one worker was
not saturated at 32 connections of connect/close), `writev` 9.8%,
`close` 9.0%, `accept` 4.7%.

## Eighteen hands — one hand sampled

**close, 19,600 req/s across 18 hands:** the sampled hand is
**60.4% in cvwait and `net_accept` is 52.6% inclusive with
`accept(2)` at 2.0%.** Every hand wakes on the level-triggered
listener (`net_wait` is a `poll` over a shared fd; macOS distributes
nothing — s137), every hand calls `net_accept`, and N−1 park in the
reactor against the 5 ms accept budget for each connection. That is
why the close shape burns 7–8 cores for 20k req/s while nginx's
`accept_mutex`-free kqueue workers burn 3. The posture is lobo's
(free-for-all, ws18); the park's cost per loser is the runtime's
(#257); the missing `EPOLLEXCLUSIVE`/`reuse_port`-distribution is the
host's.

**keepalive, 45,000 req/s across 18 hands:** cvwait 42.5%, `poll`
17.0% (idle — 32 connections over 18 hands), and **`os_signal_wait`
7.1% + `signal::raise` 2.5% ≈ 10%**: the self-raise signal poll the
loop runs every pass (the header note in `src/main.lu`), which is
cheap per pass and not cheap when a hand's passes are short. lobo's.

## The mid-end: worth nothing here, measured

`WOLF_MIDEND=0` is the shipped posture (wolf-lang#146). Re-probed at
this pin — the THIRTEENTH measurement — still the dominance ICE in
`std.x.crypto.curve25519.sc_muladd` (`%19 is not dominated by its
definition`), reached from `config`'s `use std.x.crypto.curve25519`,
so no lobo module graph builds with the mid-end on. What it would be
worth was measured on a lobo-SHAPED loop instead: lobo's own
`http.parse_request` (the parse half of `src/http/http.lu`, verbatim)
on `ab`'s request head plus the nine-interpolation response head
`serve_file` builds, 300,000 iterations, no I/O, three interleaved
pairs, load(1m) 2.9:

| build | ms per 300k |
|---|---|
| `WOLF_MIDEND=0` (shipped) | 534 · 527 · 534 |
| mid-end on | 546 · 542 · 536 |

**1.8 µs per request either way; the mid-end is within noise and
slightly negative on this path.** Which is the same finding as the
profile from the other side: lobo's user-space work is ~2 µs of an
82 µs request, and no compiler pass moves the 80.

## What this does NOT say

- Nothing here was profiled on linux. `sample` is macOS's; the linux
  numbers in the parity ledger came from the CI runner, where lobo's
  keepalive is **780 req/s** — the two-write response meeting Nagle
  and linux's 40 ms delayed ACK (lobo#3), a stall this profile
  cannot see because macOS acks differently. A `perf`/`strace -c` leg
  on the runner is ws23's first instrument.
- The reactor share is a share of WALL time on a thread that is
  either working or parked; it is not cpu. The cores-used column in
  the parity table is the cpu.
- `open(2)` at 9–12 µs is this filesystem (APFS) on this box.
