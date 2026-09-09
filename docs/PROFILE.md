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

## ws24's addendum — the herd at the syscall-first pin (2026-09-09)

The pin moved to wolf bd7caff (wolf-lang#257: the syscall goes
first, a park on WouldBlock only) and the question ws23 left was
whether the accept herd's cost moved with it. The probe is ws22's
own: lobo at eighteen hands, the close shape under four `ab -t 20
-c 8` generators (20,546 req/s summed; ws22 saw 19,300), `sample(1)`
ten seconds at one millisecond on ONE serving hand, main thread.
Taken at load(1m) 7.7 (the box carried other lanes' gauntlets; a
one-thread profile's proportions survive that — ws22 measured it),
lobo at `8859ac9` (the pin, lobo's source untouched):

| samples | share | where | ws22 (v0.2.6) |
|---|---|---|---|
| 5,508 | **69.4%** | `net_accept` inclusive | 58.5% |
| 5,074 | **64.0%** | … of which `__psynch_cvwait` under `reactor::submit` → `wait_on` — the park | 63.6% (cvwait, whole thread) |
| 206 | 2.6% | … `accept_ready`: the syscall itself (`accept(2)` leaf 192) | 2.4% |
| 201 | 2.5% | … the caller's own `kevent` (arm + wake) | — |
| 1,448 | 18.3% | `net_wait` (`poll`) | — |
| ~400 | ~5% | `serve_file`, `handle_request`, `conn_step` — serving | — |

**The herd is still 64% of a hand's time, to the tenth of a point.**
#257 removed the park a call made BEFORE its syscall; a losing hand
never had a use for that one — its syscall answers EAGAIN and it
parks AFTER, against the 5 ms accept budget, and that park is the
same reactor round-trip (a waiter cell, a `kevent` to arm, a
condvar, a `kevent` to wake) it always was. The `wolf-reactor`
thread, which the keepalive shape at N=1 no longer starts, is
running in every hand here: the losers start it. What #257 bought
this cell is the WINNER's path (the accepted stream's read and write
no longer park), which is why the close ratio moved 1.981x → 1.300x
on linux and the cores column fell 6.24 → 5.35 here, and not the
herd, which is the same seventeen parks per connection.

What would move it, named and not built (lobo#5, wolf-lang#267): a
lost race that answers WITHOUT parking. The listener's budget is
armed once (`arm_accept`, 5 ms) and `[os.net.accept]` says a
budgeted accept returns within it, but `net_deadline(fd, 0)` CLEARS
the budget (net.rs, `ms <= 0`), so nothing in the language today
asks for "try once, `timeout` on EAGAIN" — the shape a
level-triggered `net_wait` loop wants, since the loop is back in
`net_wait` within a pass and the next SYN wakes it there. That is
a runtime surface, filed upstream with this table; the other lever
is a wake the kernel distributes (`EPOLLEXCLUSIVE` on linux;
`reuse_port` distributes on linux and not here, s137). ws23's probe
shape (watch the listener every 2nd/4th pass, a 1 ms budget) is not
re-run: it priced the wake-fewer and shorter-budget knobs at a park
cost that has not changed, and its answer stands.

## ws25's addendum — the first linux profile: what one request costs the kernel, counted (2026-09-09)

The instrument is `tools/lobo-profile` (the profile leg lobo#6 asked
for): `worker_processes 1` — one process, the master serving alone —
the parity file, the close shape under four `ab -c 8` generators, and
on linux `perf record -F 997 -g` on that process for eight seconds in
the middle of the drive, then `strace -c -f` on a SEPARATE drive
(ptrace slows the process several-fold and the shares must not carry
that). Run 34355608599 on the CI runner (4 vcpus, load 1.9), both
trees of the lobo#6 read side by side — `gather` (trunk `7c99905`)
and `copy` (`ws25-copy-arm`, ws23's byte loop back on the small
arm). The drive under perf: **13,135 req/s** (gather) vs **13,064**
(copy), +0.5%, the same reading the parity leg gave. The syscalls per
request, `strace -c` over eight seconds (the calls column divided by
the requests the drive counted):

| syscall | gather, per request | copy, per request | what it is |
|---|---|---|---|
| `statx` | **4.0** | 4.0 | `fs_is_file` (the router) + `fs_size` + `fs_modified_ms` + **one inside the runtime's `fs_read_bytes`** (`std::fs::read` sizes its buffer with a metadata call) — ws22 counted three from the leaves; the runtime's own was invisible to `sample` |
| `read` | 2.0 | 2.0 | the file's bytes, then the read that answers 0 (`fs::read` reads to EOF) |
| `close` | 2.0 | 2.0 | the file, the socket |
| `openat` | 1.0 | 1.0 | the file |
| `writev` / `sendto` | **1.0 `writev`** | **1.0 `sendto`** | the response — the gather, or the copy; one call either way |
| `accept4`, `recvfrom`, `setsockopt`, `ioctl`, `poll` | 1.0 each (`poll` 1.06) | 1.0 each | the accept, the request, `TCP_NODELAY` (the runtime's default), non-blocking, `net_wait` |
| `futex`, `brk`, `write`/`kill`/`getpid`/`rt_sigreturn` | 0.04, 0.06, 0.02 each | same | the reactor is idle at N=1 (no park); the signal self-raise runs every ~50 requests |

Every count identical between the trees but the one syscall that
changed its name, which is what "the gather costs nothing on linux"
looks like from the kernel's side. `read` under the tracer is
131 µs/call and 68% of the traced time — that is ptrace's cost on a
call that blocks (the socket read shares the name), not the file's;
the counts are the number, the times are not. What the count says
for item 3: a file request pays FOUR `statx` and TWO `read` where
nginx pays one `fstat` and one `pread`; `fs_open` + `fs_fstat` +
`fs_read_chunk(fd, size)` + `fs_close` is 1 `statx` (the router's
guard) + 1 `fstat` + 1 `read` + the same `openat`/`close`, which the
fstat run below counts.

The `perf report` tables of that run are empty: the tool chowned the
data file to the caller and then read it as root, which perf refuses
(fixed the same day; the fstat run carries the shares).

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
