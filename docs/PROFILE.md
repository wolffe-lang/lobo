# Where the time goes (ws22, measured 2026-09-08)

`docs/PARITY.md` sets the bar; this page is the profile that says
what stands between lobo and it. The tool is `sample(1)` (macOS's sampling
profiler, no root needed for one's own process): ten seconds at one
millisecond on ONE serving process while `ab -t 20 -c 32` drives it,
the same 1 KiB file, the same loopback, the same session for every
row. Numbers are the MAIN THREAD's. `sample` counts parked threads
too, and lobo has three (main, `wolf-reactor`, `wolf-signal`); the
two helpers sit 95–99% in `kevent` and `read` respectively and are
not where the time goes. Host: nomad-1, Apple M5 Pro (12P+6E),
macOS 26.4.1; lobo 0.1.0+dev at wolf 0.2.6 pin 398e5f5,
`WOLF_MIDEND=0`; nginx 1.30.4 (the pin). Taken twice: once at
load(1m) 6.3 → 16.8 while sibling lanes held the box, and again on
the box idle (load 2.55 at the set's start, with is39 the last lane
out, per the coordinator's quiet-rig call). Every proportion below
reproduced within two points between the two; the numbers quoted are
the QUIET run's. The loaded run shows that a one-thread profile's
shape survives a busy neighbour, while a req/s ratio does not.

Guesses about this have been wrong twice in this repo (ws17, ws18).

## One process, keepalive — lobo 15,822 req/s (63 µs/request) beside nginx 53,158 (19 µs)

lobo, main thread, 7,703 samples, leaves (top of stack):

| samples | share | leaf | what it is |
|---|---|---|---|
| 2,913 | **37.8%** | `__psynch_cvwait` | parked on a Condvar in `wolf_rt::reactor::wait_on`, waiting for the `wolf-reactor` thread to confirm a readiness the loop already had |
| 1,065 | 13.8% | `__open` | `fs_read_bytes` opening the file, every request |
| 718 | 9.3% | `stat` | THREE per request: `fs_is_file`, `fs_size`, `fs_modified_ms` |
| 650 | 8.4% | `__sendto` | TWO per response: the head, then the body |
| 616 | 8.0% | `kevent` | the caller's own: arm (`EV_ADD\|EV_ONESHOT`) + wake (`EVFILT_USER`), per socket op |
| 313 | 4.1% | `__recvfrom` | the request read |
| 144 | 1.9% | `read` | the file read |
| ~380 | ~5% | memmove, malloc/free, mutex, `mach_absolute_time` | runtime bookkeeping |
| 90 | 1.2% | `poll` | `net_wait` — the loop's own readiness ask, for ALL sockets at once |

Inclusive, by the shallowest runtime entry on each stack:

| samples | share | entry | the syscall inside it |
|---|---|---|---|
| 1,739 | 22.6% | `__wolf_rt_net_read` | `recvfrom` 4.1% |
| 1,498 | 19.4% | `__wolf_rt_net_write_bytes` | `sendto` ~4.2% |
| 1,508 | 19.6% | `__wolf_rt_net_write` | `sendto` ~4.2% |
| 1,311 | 17.0% | `__wolf_rt_fs_read_bytes` | `open` 13.8% + `read` + `close` |
| 425 | 5.5% | `__wolf_rt_fs_is` | `stat` |
| 297 | 3.9% | `__wolf_rt_fs_stat` | `stat` ×2 |
| 365 | 4.7% | `__wolf_rt_strbuf_*` | string building (the response head, the log line) |
| 96 | 1.2% | `__wolf_rt_net_wait` | `poll` |
| ~190 | ~2.5% | `list_new`/`str_case`/`str_find`/`signal::raise` | |
| rest | ~3% | lobo's own `_W*` frames, self time | the parser, the loop, the table |

nginx, one worker, same everything, 8,399 samples: `open` 47.3%,
`writev` 23.4%, `recvfrom` 8.8%, `pread` 4.6%, `close` 4.1%, `fstat`
3.2%, `kevent` 0.7%, everything nginx-named ~3%.

### Reading it

In microseconds of the 63 (lobo) and 19 (nginx):

| where | lobo | nginx | whose |
|---|---|---|---|
| **the reactor round-trip** — cvwait + the caller's kevent + submit's Arc/HashMap/heap/mutex, three times per request (read, write, write) | **~30** | 0.1 | **wolf's** — `NetTable::read/write/accept` park on the reactor BEFORE the syscall (wolf-lang#257) |
| `open(2)` | 8.7 | 8.9 | the kernel's — both pay it (nginx has `open_file_cache`; lobo has nothing yet) |
| `stat` ×3 vs `fstat` ×1 | 5.9 | 0.6 | **lobo's** shape: three path stats where one fd stat would do |
| socket syscalls: two `sendto` + `recvfrom` vs one `writev` + `recvfrom` | 7.9 | 6.1 | half lobo's (two writes), half the language's (no `writev`, no `TCP_NODELAY` — wolf-lang#254; on linux the pair stalls 40 ms — lobo#3) |
| file read + close | 1.7 | 1.7 | — |
| user space (wolf `strbuf`/list/malloc ~5; lobo's own code ~1.5) | ~7 | ~0.6 | mostly the runtime's string materialization (wolf-lang#191's seam); lobo's parser and loop are ~1.5 µs |
| `net_wait` | 0.8 | 0.1 | — |

Of lobo's 63 µs, ~35 are the language's (the reactor handoff ~30, the
string runtime ~5, and the missing writev/nodelay behind the second
write), ~12 are lobo's own choices (two extra stats ~4, the second
write and its reactor trip ~10 counted above, no open cache), and ~16
are what nginx pays too (one open, one stat, one receive, one send).
lobo's own code (the parser, the loop, the config table) is about
1.5 µs of 63. Nothing in lobo's user space is worth optimizing before
the two shapes above are.

## One process, close — lobo 11,667 (86 µs) beside nginx 32,700 (31 µs)

Same picture plus the accept: lobo main thread cvwait 39.7%,
`net_accept` 10.1% inclusive with `accept(2)` itself 1.1%, `net_wait`
6.3%, `net_close` 1.6%; `open` 11.1%, `stat` 7.7%, `sendto` 7.1%.
nginx: `open` ~35%, `kevent` ~31% (its idle wait; one worker is not
saturated at 32 connections of connect/close), `writev` ~10%,
`close` ~9%, `accept` ~5%.

## Eighteen hands — one hand sampled

close, 19,300 req/s across 18 hands: the sampled hand is 63.6% in
cvwait and `net_accept` is 58.5% inclusive with `accept(2)` at 2.4%.
Every hand wakes on the level-triggered listener (`net_wait` is a
`poll` over a shared fd; macOS distributes nothing, s137), every hand
calls `net_accept`, and N−1 park in the reactor against the 5 ms
accept budget for each connection. So the close shape burns 7–8 cores
for 20k req/s while nginx's
`accept_mutex`-free kqueue workers burn 3. The posture is lobo's
(free-for-all, ws18); the park's cost per loser is the runtime's
(#257); the missing `EPOLLEXCLUSIVE`/`reuse_port`-distribution is the
host's.

keepalive, 48,400 req/s across 18 hands: cvwait 38.7%, `poll` 18.6%
(idle, 32 connections over 18 hands), and `os_signal_wait` 7.2% +
`signal::raise` 3.0% ≈ 10%: the self-raise signal poll the loop runs
every pass (the header note in `src/main.lu`), cheap per pass and
expensive when a hand's passes are short. That one is lobo's.

## The mid-end: worth nothing here, measured

`WOLF_MIDEND=0` is the shipped posture (wolf-lang#146). Re-probed at
this pin (the THIRTEENTH measurement), still the dominance ICE in
`std.x.crypto.curve25519.sc_muladd` (`%19 is not dominated by its
definition`), reached from `config`'s `use std.x.crypto.curve25519`,
so no lobo module graph builds with the mid-end on. What it would be
worth was measured on a lobo-SHAPED loop instead: lobo's own
`http.parse_request` (the parse half of `src/http/http.lu`, verbatim)
on `ab`'s request head plus the nine-interpolation response head
`serve_file` builds, 300,000 iterations, no I/O, three interleaved
pairs, taken twice (load(1m) 2.9, and again in the quiet re-measure):

| build | ms per 300k (first) | ms per 300k (re-measure) |
|---|---|---|
| `WOLF_MIDEND=0` (shipped) | 534 · 527 · 534 | 563 · 555 · 558 |
| mid-end on | 546 · 542 · 536 | 570 · 571 · 555 |

~1.8 µs per request either way; the mid-end is within noise and
slightly negative on this path, both times. The profile says the same
thing from the other side: lobo's user-space work is ~1.5 µs of a
63 µs request, and no compiler pass moves the other 60.

## ws23's addendum — what the list bought, and what it corrected (2026-09-09)

The changes ws22 priced were taken in its order on branch `ws23`,
each predicted before it was measured and measured with
`tools/lobo-parity` on both hosts; the numbers are beside each
change in the CHANGELOG and in the parity ledger. Three corrections
to the profile above, measured rather than sampled:

- **Four stats, not three.** The router asked `fs_is_dir` and then
  `fs_is_file` before `serve_file` asked `fs_size` and
  `fs_modified_ms`; the `__wolf_rt_fs_is` row above (425 samples) is
  two calls. A path stat costs ~0.5 µs on this box (100k pairs in
  1.05 ms), so the four were ~2 µs, not the 5.9 the leaf count
  attributed under load. ws23 removed one (the router asks the file
  first); the last two need a runtime call (wolf-lang#261).
- **The read shape is not where a stat hides.** `fs_open` +
  `fs_read_chunk` + a confirming read + `fs_close`, with the size
  taken from the read, costs the same as `fs_read_bytes` within
  noise (830–1,091 ms vs 841–1,218 ms per 100k iterations of a
  1 KiB file on the loaded box), so the size stat cannot be folded into the
  read without an fstat.
- **The second write was the linux number, whole.** One buffer per
  small response took the linux keepalive cell from 781 to 26,189
  req/s (110.7x → 3.3x) and the close cell 2.27x → 1.97x; the copy
  it costs is ~1.8 ns per byte (2 µs at 1 KiB), which is why a
  `Connection: close` response over 4 KiB keeps two writes.

## What this does NOT say

- Nothing here was profiled on linux. `sample` is macOS's; the linux
  numbers in the parity ledger came from the CI runner, where lobo's
  keepalive is 780 req/s: the two-write response meeting Nagle
  and linux's 40 ms delayed ACK (lobo#3), a stall this profile
  cannot see because macOS acks differently. A `perf`/`strace -c` leg
  on the runner is ws23's first instrument.
- The reactor share is a share of WALL time on a thread that is
  either working or parked; it is not cpu. The cores-used column in
  the parity table is the cpu.
- `open(2)` at 9–12 µs is this filesystem (APFS) on this box.
