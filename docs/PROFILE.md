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
(fixed the same day; the next run carries the shares).

### The fstat arm beside the gather (run 34362397588, the same VM class)

`fstat` = ws25 `0f2aa93`, `gather` = trunk `7c99905`; one process,
the close shape, `perf record -F 997 -g` over eight seconds while the
drive answered **13,896 req/s** (fstat) vs **13,143** (gather), +5.7%
— and `tools/lobo-parity` on the same VM read +3.8% on the N=4 close
cell and +10.5% on keepalive (docs/PARITY.md). The kernel's count
per request, `strace -c` on a separate drive:

| syscall | fstat | gather | what moved |
|---|---|---|---|
| `statx` | **2.0** | 4.0 | the router's `fs_is_file` and `fs_fstat` — `fs_size`, `fs_modified_ms` and the runtime's own inside `fs_read_bytes` are gone |
| `read` | **1.0** | 2.0 | `read_exact(fd, size)` reads the size the fstat named; `fs::read`'s read-to-EOF is gone |
| `openat`, `close` ×2, `writev`, `accept4`, `recvfrom`, `poll`, `setsockopt`, `ioctl` | 1 each (`close` 2) | the same | — |
| **calls per request** | **~12.2** | ~15.3 | three fewer |

Where the process's time goes on this host (`perf`, the whole
process, leaves and inclusive), the first linux profile lobo has:

| | fstat | gather |
|---|---|---|
| kernel / lobo-release / libc (by dso) | 76.3% / 14.5% / 9.0% | 77.1% / 13.6% / 9.1% |
| in a syscall, inclusive (`entry_SYSCALL_64`) | 66.8% | 68.3% |
| `writev` inclusive — the response's whole transmit path (`tcp_sendmsg` → `ip_output` → the loopback's receive softirq, ~20 points of it) | 24.9% | 22.2% |
| `close(2)` inclusive — the socket's teardown (`__fput`, the FIN) | 17.7% | 15.2% |
| `link_path_walk` leaf — the path stats' walks | 0.67% | 1.50% |
| top leaf: `_raw_spin_unlock_irqrestore` (the loopback's softirq handoff) | 9.0% | 7.1% |
| lobo's own frames (`_Wserve_main`, leaf) | 0.70% | 0.82% |

Two thirds of one process on this host is the kernel serving the
socket, a quarter of it the response's transmit and a sixth the
close — the close SHAPE's own cost, which nginx pays too (its N=1
close on this VM is 19.2k against lobo's 14.3k, 1.35x). The path
walks halved with the fstat and were never large; what the fstat
bought is three kernel entries at ~1 µs each on a ~70 µs request at
N=1 close and a ~17 µs one at N=4 keepalive, which is why the
keepalive cell moved most. lobo's user space is under 15% of the
process here, of which lobo's own code is under 1%: the ws22 reading
holds on linux.

## ws27's addendum — both servers counted, and the keepalive shape profiled (2026-09-10)

Two instruments this sprint added, both on the CI runner (ubuntu-
latest, 4 vcpus), one job (run 34504504973), lobo `9a24fde` at wolf
0.2.9 (pin 4c60946), nginx 1.30.4, the parity file. The first is
`tools/lobo-syscalls`: `strace -c -f` attached to EVERY serving
process of one server before an `ab -t 8 -c 32` drive (four
generators) and detached after it, calls ÷ the requests the
generators completed, lobo then nginx, `worker_processes 4` both — so
the number below is exact per request and the same on every VM class
(ws25: counts held across runs whose req/s spread 13%). The second is
`tools/lobo-profile` with its new shape argument: `perf record -F 997
-g` on ONE hand under `ab -k` (the read/serve path alone; every prior
profile in this file is the close shape).

### The count, N=4 c=32, per request — the two shapes

| syscall | lobo, keepalive | nginx, keepalive | lobo, close | nginx, close | what it is |
|---|---|---|---|---|---|
| `recvfrom` | 1.00 | 1.00 | 1.01 | 1.00 | the request; one read answers the whole head on both |
| `statx` | **2.00** | — | **2.00** | — | lobo: the router's PATH stat (`fs_is_file`, the fifo guard) + `fs_fstat` on the handle |
| `fstat` | — | **1.00** | — | **1.00** | nginx: on the fd it opened — no path stat, its open is `O_NONBLOCK` |
| `openat` | 1.00 | 1.00 | 1.00 | 1.00 | the file, both |
| `read` / `pread64` | 1.02 / — | — / 1.00 | 1.11 / — | — / 1.00 | the body; lobo's extra 0.02 / 0.11 is the reactor's eventfd (below) |
| `writev` | 1.00 | 1.00 | 1.00 | 1.00 | the response, one gather each |
| `close` | 1.00 | 1.00 | 2.01 | 2.00 | the file; on close, the socket too |
| `poll` / `epoll_wait` | 0.15 / — | — / 0.13 | 1.28 / 0.13 | — / 1.00 | the pass's wait: ~7 requests per pass on BOTH on keepalive (the loop shape is nginx's); on close, one per connection plus lobo's zero-budget probe before every accept after a burst's first (0.28); lobo's `epoll_wait` is the reactor thread's |
| `accept4` | 0.01 | 0.00 | **1.08** | 1.00 | the accept; lobo's 0.08 are lost races answering EAGAIN (#267) |
| `ioctl` (FIONBIO) | 0.01 | — | **1.01** | — | the runtime's non-blocking posture, a second call after std's `accept4(SOCK_CLOEXEC)` (wolf-lang#290) |
| `setsockopt` (TCP_NODELAY) | 0.01 | 0.00 | **1.01** | 0.00 | #254's default, at accept; nginx sets it only when a connection goes keepalive (wolf-lang#290) |
| `epoll_ctl` | — | 0.00 | 0.14 | 1.13 | nginx's per-connection registration; lobo's is the reactor's arm for a park |
| `futex` | 0.06 | — | 0.27 | — | the reactor handoff (a park) and malloc's arena |
| `write` + `read` (eventfd) | 0.03 + ~0.02 | — | 0.11 + 0.11 | — | the reactor's wake per park |
| `kill` + `getpid` + `rt_sigreturn` | 0.03 each | — | 0.04 each | — | the signal self-raise probe, every `sig_poll_ms` (25 ms): ~1 in 33 requests at this rate |
| `brk` | 0.04 | — | 0.07 | — | the heap growing — the runtime's |
| **calls per request** | **7.41** | **6.14** | **13.36** | **10.13** | **+1.27 keepalive, +3.22 close** |

Read on the keepalive shape: lobo makes ONE call nginx does not —
the router's path stat, +1.00 — and a quarter-call of small change
(the probe 0.12, `futex` 0.06, `brk` 0.04, the accept side 0.03).
7.41 against 6.14 is 1.21x in calls where the cell reads 1.72x in
req/s; **the keepalive gap is not in the count.** Read on the close
shape: the path stat, then the accept posture (`ioctl` + `setsockopt`,
+2.02 per connection against nginx's one `epoll_ctl`), then the
herd's residue at four hands — 0.08 lost races per connection, each a
park (~0.9 syscalls across the reactor's rows), a tenth of the
eighteen-hand macOS herd and still the one cost no lobo-side change
reaches. Each extra, what removes it and whose it is: the path stat —
an `fs_open` that carries `O_NONBLOCK` so `fs_fstat` classifies after
the open (wolf-lang#289; ws27 built the no-surface half, a one-second
kind table in the router, and its delta is in the parity ledger); the
`ioctl` — `accept4(SOCK_NONBLOCK)` in `push_stream` (wolf-lang#290);
the `setsockopt` — `TCP_NODELAY` set lazily, nginx's shape
(wolf-lang#290); the probe — a signal poll that does not park
(wolf-lang#126's family, commented there with the count); the probe
`poll` and the parks — a park-free lost race (wolf-lang#267).

### The count after the warm kind table (run 34506393898, the same instrument)

`statx` **1.00** on both shapes, every other row unchanged: keepalive
**6.31** against nginx's 6.13 (+0.18 — the probe 0.12, `futex`,
`brk`), close **12.41** against 10.13 (+2.28 — the accept posture's
`ioctl` + `setsockopt`, the herd's parks, the probe `poll`). The
delta it read in req/s on the same VM is in the parity ledger:
+2.7% keepalive, +2.1% close at N=4.

### Where a keepalive request's time goes on linux — one hand, `perf`, 18,133 req/s under the drive

| | keepalive (ws27) | close (ws25, the fstat tree) |
|---|---|---|
| kernel / lobo-release / libc (by dso) | **64.2% / 22.0% / 13.5%** | 76.3% / 14.5% / 9.0% |
| in a syscall, inclusive (`do_syscall_64`) | 55.6% | 66.8% |
| `writev` inclusive — the transmit path down to the loopback softirq | 31.0% | 24.9% |
| top leaf: `_raw_spin_unlock_irqrestore` (the softirq handoff) | 9.4% | 9.0% |
| `malloc` + `cfree` + `realloc` + `finish_grow` + `reserve` (libc and the runtime's Vec growth) | ~4.7% | — |
| `wolf_rt::str::ambient_alloc` + `__wolf_rt_strbuf_str` | 3.2% | — |
| `StrSearcher::new` + `TwoWaySearcher::next` (`str.find`) + `to_lowercase` | 2.2% | — |
| `link_path_walk` + `__d_lookup_rcu` + `inode_permission` (the path stats' walks) | 2.2% | 0.7% (leaf) |
| `do_user_addr_fault` + `do_anonymous_page` + `clear_page_erms` + `__handle_mm_fault` (fresh pages — the heap growing) | 3.1% | — |
| lobo's own frames, leaves: `serve_request` 0.94, `serve_main` 0.92, `parse_request` 0.53, `conn_step` 0.50, `serve_file` 0.45, `http_date` 0.43, `split_lines_strict` 0.41, `hline` 0.40 | ~4.6% | 0.7% |

With the accept and the teardown out of the request, a third of a
keepalive request on this host is user space, and most of that is the
runtime materializing and searching strings — the allocator (~5%),
`ambient_alloc`/`strbuf` (3%), `find`/`to_lowercase` (2%), and the
page faults that a heap growing under those allocations costs (3%;
the `brk` in the count is the same fact) — with lobo's own frames
under 5%. The kernel's share is the response's transmit (31%, which
nginx pays too on this loopback) and the file's open/stat/read/close.
So the linux keepalive cell, after the count: ~1 call in 7 is the
router's (built around, filed); ~1/3 of the request is the string
runtime's (wolf-lang#191's seam, the same reading ws22 took on macOS
at 5 of 63 µs and a larger share now that the reactor trips are
gone); and the remainder is the kernel serving a socket, which is the
same on both sides of the bar.

### What this does NOT say

- The count is the request's; the herd's cost per park is not a
  count but a wait, and this table only shows its syscalls.
- `perf` here is one hand at N=1; the N=4 cell's shares were not
  taken (the count was). The dso split at N=1 keepalive is the
  per-request reading with no distribution in the way, which is the
  cell the profile leg was asked for.
- nginx was COUNTED and not profiled; its user-space share is ws22's
  macOS reading (~3%), not a linux measurement.

## ws28's addendum — the strings on the serving path, counted, and the head taken out of the request (2026-09-10)

ws27 left the linux keepalive cell with the count settled and a
third of the request in user space, most of it the runtime
materializing strings. ws28 counted those strings by source line —
the CHANGELOG's ws28 entry carries the predicted table, sixteen rows,
one per operation, with arena allocations, libc calls and bytes
beside each — and then took out the rows a program can. Two
instruments, one new:

- **`tools/lobo-strings`** (the BYTES leg): the ambient arena never
  frees (wolf-lang#191), so a serving hand's RSS growth over a drive
  ÷ the requests it completed IS what one request materializes and
  keeps — on either host, on any VM class, a count and not a sample.
  One process, the parity file, `ab -k -n 20000 -c 8` after a
  2,000-request warm-up, `LOBO_REF` for a second tree, nginx for the
  contrast.
- `tools/lobo-profile … keepalive` on macOS (`sample`, the main
  thread), read as INCLUSIVE counts per function (every stack line
  naming the function, summed) rather than the tool's top-of-stack
  table, so a runtime entry's whole cost — the `String` growth, the
  arena bump, the frees under it — lands on one row.

### Bytes per request, counted (macOS arm64, the count is host-independent)

| tree | RSS before | RSS after (20,000 requests) | **bytes retained per request** |
|---|---|---|---|
| pin (trunk c58b4f1) | 15,680 KiB | 139,488 KiB | **6,339** |
| ws28 | 7,872 KiB | 56,896 KiB | **2,510** (before the histogram row below; re-read after it in the CHANGELOG) |
| nginx 1.30.4 | 2,320 KiB | 2,320 KiB | **0** |

The prediction was ~5.3 KB before and ~0.4 KB after. Before: the
16-byte rounding and the list buffers the table under-counted (a
`List[str]` header is 48 bytes and its first buffer 128) make up the
difference. After: the prediction missed by 2 KB, and the miss is
LISTS, not strings — every string row the table named is gone (the
profile below says so), and what remains is list headers and
eight-slot buffers: `tls.no_sess()`'s six (the conn seam the request
writes through), the parser's four, the access record's two,
`fs_fstat`'s `List[int]`, the route's three, the loop's per-pass
lists, the metrics histogram's eleven-element bucket ladder built
per observation (found by this count, removed in the same sprint),
and the read's 117-byte arena copy.

### One hand, keepalive, macOS `sample` — before and after (INDICATIVE: load 3.3 before, 5.4 after; proportions, not rates)

Main thread, one hand under four `ab -k -c 8`, an 8 s window at 1 ms:
6,804 samples at trunk (58,771 req/s under the drive), 6,766 at ws28
(71,908 req/s under a heavier load — the rate is not the number here,
the shares are):

| inclusive, main thread | trunk c58b4f1 | ws28 | what it is |
|---|---|---|---|
| `open(2)` | 2,245 (33.0%) | 3,140 (46.4%) | the file, APFS — the same per request, a larger share of a shorter one |
| `writev` | 878 (12.9%) | 1,166 (17.2%) | the response |
| `recvfrom` | 433 (6.4%) | 587 (8.7%) | the request |
| `read` (the file) + `fstat` + `close` + `poll` | ~805 (11.8%) | ~1,033 (15.3%) | the file's read and stat, the pass's wait |
| **in a syscall** | **~4,361 (64.1%)** | **~5,926 (87.6%)** | |
| **user space** | **~2,443 (35.9%)** | **~840 (12.4%)** | |
| `__wolf_rt_strbuf_str` | 669 (9.8%) | 45 (0.7%) | interpolation segments (the `String` growing: `reserve` 511, `finish_grow` 482, `realloc` 319 under it) |
| `__wolf_rt_strbuf_finish` + `_new` + `_i64` | 658 (9.7%) | <5 | the arena copy of every interpolation, the box, the int holes |
| `__wolf_rt_str_case` (`lower()`) | 116 (1.7%) | 0 | eight per request → none on an ASCII request |
| `__wolf_rt_str_find` + `StrSearcher::new` | 103 + 64 | 45 + 20 | `head_cut`'s searches, halved |
| `__wolf_rt_list_new` + `list_push` | 162 + 87 (3.7%) | 92 + 69 (2.4%) | the lists that remain |
| `ambient_alloc` (inclusive: the mutex) | 252 (3.7%) | 79 (1.2%) | arena bumps |
| `memmove` + `xzm_free` + `malloc` family, leaves | ~1,100 (16%) | ~170 (2.5%) | the copies and the `String` frees |
| **the string runtime** (`strbuf_*` + `str_case` + `str_find` + `list_*`) | **~1,795 (26.4%)** | **~251 (3.7%)** | |
| `serve.hline` / `http_date` / `to_hex` | 375 / 355 / 248 | 0 / 0 / 0 | the head's builders — memoized |
| `http.parse_request` | 163 | 92 | names interned, tokens folded |
| `serve.conn_step` less `net_read` | 54 | 7 | the read adopted, the seam lazy |
| `http.normalize_path` + `percent_decode` | 79 + 41 | 15 + <5 | the views |
| `http.route` + `join_path` | 32 + 30 | ~10 + 63 | no trace; the fs path's join stays |
| `serve.is_file_warm` + `head_warm` + `head_cut` | 30 + — + — | 52 + 32 + 25 | the tables and the cut — what the memo costs |
| `tls.no_sess` | 59 | 42 | once per request now, not twice |

Read: on this host a keepalive request's user space fell from ~36%
of the thread to ~12%, and the string runtime's share from ~26% to
under 4%. What is left in user space is the runtime's list headers,
the read's copy, and lobo's own frames (the parser, the tables, the
loop — ~4%). The kernel's share is the same work it always was —
`open`, `writev`, `recvfrom`, the file's read and stat — now most of
the request.

### One hand, keepalive, linux `perf` — both trees, one VM (run 34536710553)

The same instrument as ws27's keepalive profile, both trees in one
job (`ws28` = 8a14d2a, `pin` = c58b4f1, wolf 0.2.9), `perf record -F
997 -g` on ONE hand under four `ab -k -c 8` for eight seconds, load
1.3–1.8:

| | pin | ws28 |
|---|---|---|
| req/s under the perf drive | 18,625 | **31,047** |
| kernel / lobo-release / libc (by dso) | 64.1% / 22.6% / 13.1% | **74.4% / 18.2% / 6.9%** |
| in a syscall, inclusive (`do_syscall_64`) | 55.2% | 68.9% |
| `writev` inclusive — the transmit path | 32.2% | 39.5% |
| `malloc` / `cfree` / `realloc` / `reserve` / `finish_grow` (leaves) | 1.87 / 0.75 / 0.69 / 0.63 / 0.58 | all under 0.4% |
| `wolf_rt::str::ambient_alloc` / `__wolf_rt_strbuf_str` / `strbuf_finish` | 1.71 / 1.53 / 0.48 | 0.85 / — / — |
| `to_lowercase` | 0.40 | — |
| `TwoWaySearcher::next` + `StrSearcher::new` (`find`) | 1.10 + 0.79 | 0.67 + 0.77 |
| `__wolf_rt_list_new` | 0.48 | 0.41 |
| `do_user_addr_fault` + `clear_page_erms` (the arena's fresh pages) | (ws27: 1.71 + 0.49) | 0.72 + 0.63 |
| lobo's own leaves: `serve_main` / `serve_request` / `parse_request` / `serve_file` / `split_lines_strict` | 1.14 / 0.65 / 0.70 / 0.53 / 0.49 | 1.05 / 0.97 / 0.89 / 0.54 / 0.55 |
| the memo's cost: `head_warm` / `is_file_warm` / `lower_token` | — / 0.43 / — | 0.70 / 0.67 / 0.40 |
| syscalls per request (the count leg, N=4): keepalive / close | 6.31 / 12.41 (ws27) | **6.37 / 12.38** — unchanged; `brk` 0.04 → 0.01 |

Read: with the strings out, a keepalive request on this host is
three quarters kernel, and the user-space quarter is lobo's own
frames (~5%), the runtime's list headers and arena bumps (~2%) and
the searchers (~1.5%). The two-tree parity set in the same job
(`docs/PARITY.md`) read the delta at +30.6% on the N=4 keepalive
cell and +55.1% at N=1 — well past the +7% and +8% the CHANGELOG
entry predicted from ws27's leaf shares, which is the lesson this
page records: a leaf table sums what a function does in its own
frame, and the cost of a retained allocation is paid elsewhere (the
fault path, the cache), under names that read as the kernel's. The
bytes count (`tools/lobo-strings`) is the number to predict from.

## ws29's addendum — the signal probe retired, PREDICTED then measured (2026-09-10)

lobo#8's count, taken at ws27 and re-taken on trunk `9a4a905` the day
this sprint opened (CI run 34539376264, ubuntu-latest 4 vcpus, wolf
v0.2.9): a serving hand raised a signal to ITSELF every 25 ms and
waited once, to learn whether an operator had sent one — `kill` +
`getpid` + `rt_sigreturn` + the runtime's self-pipe `write`, four
syscalls a probe. It was ws08's only option: [os.signal.wait]'s
intended parked forwarder was refused by the release tier under
wolf-lang#136, and `src/main.lu`'s header promised the flip "the
sprint after the fix enters the pin". #136 is closed and the pin is
v0.2.9.

**The disposition: FLIPPED, not retired.** Retiring the probe outright
would have meant a server that does not answer `kill -HUP`, and the
compat contract does not allow that — nginx's operator sends signals.
So `sig_forwarder` (`src/main.lu`) parks one proc in `os_signal_wait`
for the process's life and writes each meaning down a loopback
self-pipe whose READ END joins the loop's ordinary wait set. A signal
becomes readiness, like every other event the loop handles. The loop
asks nothing and pays nothing per pass; the only self-raise left in
lobo is the ONE that retires the forwarder at shutdown. Two
consequences beyond the count: `wait_budget`'s 25 ms signal floor is
gone (an armed loop now waits the same 250 ms an unarmed one does —
this page's own note called that floor "the honest limit on how much
of #127's win a server that must notice a SIGHUP can take"), and
signal latency IMPROVES, from within `sig_poll_ms` plus a pass to the
wait's own return.

D7 moves and is still one sentence: the serving loop is spawn-free and
`sig_forwarder` is the one proc beside it, holding two ints and a
socket and touching no server state.

### The prediction, written before the run

The probe's cost is a cost per unit TIME divided by requests, so its
per-request figure moves with the rate — which is why ws27 read 0.03
each and this sprint's own before-run, at a higher traced rate, read
0.01 each on the keepalive shape. What the flip removes is the whole
of it.

| row | before (trunk 9a4a905) | predicted after | why |
|---|---|---|---|
| `kill`, `getpid`, `rt_sigreturn` — keepalive | 0.01 each | **0.00 each** | four calls per PROCESS now, not per 25 ms; ~4 in 100,000 requests rounds to zero |
| `kill`, `getpid`, `rt_sigreturn` — close | 0.03 each | **0.00 each** | same |
| `write` — keepalive / close | 0.01 / 0.10 | **0.00 / ~0.07** | the handler's self-pipe write went with the probe; the rest of `write` is the log |
| `futex` — keepalive / close | 0.03 / 0.25 | **down, not to zero** | the raise→drain-thread→wait handoff goes; the arena mutex (#191) and the pool stay. Low confidence on the size |
| `poll` — keepalive / close | 0.15 / 1.28 | **unchanged, or slightly up** | this is the runtime's own drain/pool traffic, not the loop's. A permanently parked forwarder is a thread the runtime did not have; if compensation adds one, this is where it shows. LOW confidence, and the row to watch |
| `epoll_wait` — keepalive / close | 0.00 / 0.14 | **unchanged or down** | the wait budget lengthened 25 ms → 250 ms, so fewer returns on an idle pass; under load the loop was already never idle |
| **calls per request** — keepalive | **6.28** (nginx 6.14, +0.13) | **6.22–6.24**, gap **+0.08–0.10** | the four probe rows only |
| **calls per request** — close | **12.27** (nginx 10.13, +2.14) | **12.15–12.20** | the four probe rows only |

Named risk, priced now rather than after: the forwarder is a real
thread parked for the process's life ([os.signal.wait] parks with
blocking compensation). That is a per-PROCESS cost — one stack, and
whatever the pool does about a permanently blocked task — and a
per-request count cannot see it. It would show in RSS, not here. If
`poll` moves up, that is the row that saw it.

### The measurement

CI run **34540847393** on `ws29@ece69e7`, the same workflow input
(`syscalls=true`) and the same runner class as the before-run
(34540847393's box: ubuntu-latest, 4 vcpus, load(1m) 3.00).

**The acceptance criterion is MET.** `kill`, `getpid` and
`rt_sigreturn` do not appear in either shape's table any more — not
0.01, not 0.03: the rows are gone, because the calls are. `write`
leaves the keepalive table too and falls 0.10 → 0.08 on close, which
is the handler's self-pipe write going and the log's staying.

| row (per request) | keepalive before → after | close before → after | predicted |
|---|---|---|---|
| `kill` / `getpid` / `rt_sigreturn` | 0.01 → **0.00** each | 0.03 → **0.00** each | 0.00 — **right** |
| `write` | 0.01 → **0.00** | 0.10 → **0.08** | 0.00 / ~0.07 — **right** |
| `poll` | 0.15 → 0.14 | 1.28 → 1.28 | unchanged — right per request, **wrong in the raw**, and in lobo's favour |
| `futex` | 0.03 → **0.09** | 0.25 → **0.39** | down — **WRONG**, and against lobo |
| `epoll_wait` | 0.00 → 0.00 | 0.14 → 0.14 | unchanged or down — right |
| **calls per request** | 6.28 → **6.26** (nginx 6.14 → 6.15, gap +0.13 → **+0.11**) | 12.27 → **12.27** (gap +2.14 → **+2.14**) | 6.22–6.24 / 12.15–12.20 — **WRONG** |

### Why the totals barely moved, and why that is not the whole result

**Read the raw counts, not only the per-request ones.** Everything this
change touches is work per unit TIME, and the two drives did not serve
the same number of requests: the after-box was slower for BOTH servers
(nginx traced at 13,751 → 10,601 req/s keepalive and 7,312 → 5,774 on
close, a ~23% fall it had nothing to do with). Per-TIME work divided by
fewer requests reads higher per request. So the per-request totals are
the wrong instrument for exactly this change, and the raw column over
the same 8-second drive across the same four hands is the right one:

| raw calls per 8 s drive, 4 hands | keepalive before → after | close before → after |
|---|---|---|
| `kill` + `getpid` + `rt_sigreturn` | 4,113 → **0** | 4,053 → **0** |
| `poll` | 15,241 → **10,727** | 60,975 → **45,768** |
| `futex` (of which errors) | 3,205 (539) → **6,608 (6,593)** | 11,770 (1,283) → **13,861 (7,712)** |
| **net** | **−5,224** | **−17,169** |

Three findings, and two of them contradict the prediction:

1. **The probe is gone, exactly as predicted** — 4,113 and 4,053 calls
   a drive to zero, and one raise per process instead.
2. **`poll` fell, and by MORE than the probe did.** Predicted
   unchanged; wrong, and in lobo's favour. This is `wait_budget`'s
   floor lifting: the loop's wait went 25 ms → 250 ms, so an idle pass
   trips the reactor a tenth as often. That win was invisible per
   request and is 4,514 / 15,207 calls a drive.
3. **`futex` ROSE, and this is the named risk landing** — on `futex`,
   not on `poll` where the prediction put it. The error count is the
   tell: 539 → 6,593 on keepalive, 1,283 → 7,712 on close. That is a
   permanently parked task's blocking compensation ([os.signal.wait]
   parks a real thread), waking and re-waiting for the life of the
   process. It is a cost per unit TIME on an otherwise idle thread and
   it takes back about two thirds of the probe's calls on keepalive
   and half on close. **Filed upstream as wolf-lang#302** — it is the
   runtime's, not lobo's: the forwarder allocates nothing, touches no
   socket and never returns on a drive where no signal is sent, so
   every one of those calls is the pool's compensation for a thread
   that is doing nothing. lobo has no cheaper spelling available; the
   alternatives are the poll this replaced or no signal reception.

The net is still a win — 5,224 and 17,169 fewer calls a drive — and it
is a smaller win than "the probe is gone" suggests, which is the
sentence this page exists to make possible. The per-request table says
6.26 and 12.27 and would let a reader conclude nothing changed; the raw
column says what changed and in which direction.

**A caveat on ws25's rule.** ws25 established that the COUNT is the one
linux number a shared VM holds still — identical across runs whose
req/s spread 13%. That holds here for every per-REQUEST row: `read`,
`statx`, `openat`, `writev`, `close` and `recvfrom` read 1.00–1.01 in
both runs, before and after, unmoved. It does NOT hold for the per-TIME
rows (`poll`, `futex`, `epoll_wait`, and the probe while it existed),
and this sprint is the first to change one of those. The rule wants the
amendment: a per-request count is stable for work the request does, and
is a rate in disguise for work the clock does.

## ws30's addendum — the router takes the syscalls: the pin at fc07cc5, PREDICTED before the build (2026-09-11)

s149 landed on wolf-lang trunk as `fc07cc5` (wolf-lang#289 and #290
closed) with the two runtime changes ws27's count named as the two
biggest rows lobo could not reach from its own side: `fs_open_mode(p,
5)` — a read open carrying `O_NONBLOCK`, so a fifo answers a handle
instead of parking the hand and the router no longer needs a PATH stat
to be safe — and the accept posture, `accept4(SOCK_NONBLOCK|
SOCK_CLOEXEC)` where linux has it plus `TCP_NODELAY` paid at the first
write Nagle could hold back rather than at every accept. This sprint
pins it (a `+dev` stamp: `wolf 0.2.10+dev.fc07cc5 (wolfgang, pin
fc07cc5)`), moves the one router site, and measures. Everything below
this heading and above "The measurement" was written BEFORE the pin
was staged into `.wolf-bin`.

### The site count, read off the tree

s149's hand-off says "one site". Read against `src/`, it is one
serving-path site with two halves and one mirror:

- `serve.is_file_warm` (`fs_is_file` behind the ws27 one-second kind
  table) — the router's guard, called from `handle_request` for the
  direct path and again for each index candidate;
- `serve.serve_file`'s `fs_open(path)` + `fs_fstat(fd)` — the open the
  guard was protecting.

The two become ONE open: `fs_open_mode(path, 5)` first, `fs_fstat` on
the handle classifies (`kind` 0 serve, 1 a directory — the router's
directory arm, 2 refuse: close it and answer what a not-a-file answers
today). The kind table's kind half goes with the stat (its head cache
and date memo — ws28's — stay; they are per-request memos of pure
functions, not a window). The mirror is `dryrun.stat_note`
(`-t --request`'s "what would this config do"), which classifies the
same way and moves the same way so the prediction and the live
answer keep agreeing; it is not on the serving path and has no row
in the count. `budget.lu`'s `fs_open` (the capped proc's own open of
a path the router already classified) and `obs.lu`'s log open (mode
2) are not classification sites and do not move.

### The census, predicted

The gauntlet's suite counts at trunk `d04dd97` are the baseline (the
before-run of this sprint's own gauntlet prints them). Predicted to
move: the **corpus row, +1** — `tests/serve/file_kinds.lu` is
rewritten in place to pin the open-first classification (a regular
file, a directory, a missing path, the swap under a handle), and one
new witness drives a real lobo at a **fifo under the root** and asks
for it: the answer is 404 at once, where a `fs_open` without the flag
parks the hand until a writer appears — the hang the guard existed
for, now a test instead of a stat. Every other row identical:
differential, proxy, control, logdiff, signal (21), membudget,
resolver, prefork, replay, metrics, tls, acme, shell, confcheck,
dryrun. Two `.wolfi` motions, each its own `interface(…)` commit: the
toolchain stamp `0.2.9 → 0.2.10` in every header (MECHANICAL — the
stamp reads the version, not the dev suffix, as the ws24 and ws27
pins recorded), and `serve.wolfi` losing `is_file_warm` and the two
kind lists on `FileKinds` (a surface change).

### The count, predicted row by row — against TRUNK, not against ws27

s149 predicted **keepalive 7.41 → 6.41** and **close 13.36 → 10.34**
on this issue's table. Those are ws27's PRE-kind-table numbers. ws27's
warm kind table already collected the `statx` unit on both shapes
(6.31 / 12.41, run 34506393898), and ws28/ws29 took the rest of the
small change (6.26 / 12.27, run 34540847393 on `ws29@ece69e7`, which
is trunk `d04dd97` for every per-request row). So the prediction here
is against trunk, and it says something s149's could not: **the pin
buys the keepalive table nothing at two decimals, and buys the close
table exactly the accept side.**

| row (per request) | keepalive: trunk → predicted | close: trunk → predicted | why, and confidence |
|---|---|---|---|
| `statx` | 1.00 → **1.00** | 1.00 → **1.00** | this is `fs_fstat` on the handle. The path stat was already down to one per second per hand per path (ws27's table; ~0.0004 per request at this rate, invisible at two decimals). What the pin removes is the WINDOW — a second in which a swap for a fifo could park a hand — not a row. HIGH |
| `openat` | 1.00 → 1.00 | 1.00 → 1.00 | the flag rides the open that was already made. HIGH |
| `ioctl` (FIONBIO) | 0.00 → 0.00 (raw 231 → ~8: the listeners' own, once per hand) | **1.00 → 0.00** | `accept4(SOCK_NONBLOCK)`: the posture arrives with the fd. HIGH |
| `setsockopt` (TCP_NODELAY) | 0.00 → 0.00 (raw ~231 → ~231: paid at each keepalive connection's SECOND write, the first that finds bytes in flight — once per connection, as before, just later) | **1.00 → 0.00** | one gather then a close pays nothing; nginx pays nothing on this shape either. HIGH |
| `accept4` | 0.00 → 0.00 | 1.08 → 1.08 | the 0.08 are the herd's lost races (lobo#5, wolf-lang#267); the pin does not touch the race. HIGH per request; its raw count moves with the rate |
| `read`, `recvfrom`, `writev`, `close` | 1.00 / 1.00 / 1.00 / 1.00 | 1.08 / 1.00 / 1.00 / 2.01 | untouched; the 0.08 of `read` on close is the reactor's eventfd, a park's row. HIGH |
| `poll`, `futex`, `epoll_wait`, `epoll_ctl`, `write`, `brk` | 0.14 / 0.09 / 0.00 / 0.00 / 0.00 / 0.01 | 1.28 / 0.39 / 0.14 / 0.15 / 0.08 / 0.04 | the PER-TIME rows. The pin touches none of their mechanisms (the runtime's delta `4c60946..fc07cc5` is `fs.rs` and `net.rs`, nothing in `task/`), so they are predicted UNCHANGED as rates and are read raw over the 8 s drive, per ws29's amendment; their per-request figures will move with the box's rate and that motion is drift, not the pin. MEDIUM on any per-request figure, by construction |
| **calls per request** | **6.26 → 6.26** (nginx 6.15; gap **+0.11 → +0.11**, 1.02x) | **12.27 → 10.27** (nginx 10.13; gap **+2.14 → +0.14**, 1.21x → **1.01x** in calls) | the whole of the pin's per-request effect is −2.00 on the close shape and 0.00 on keepalive. HIGH |
| accept side per close-shape connection (`accept4` + `ioctl` + `setsockopt`) | — | **3.08 → 1.08** | s149 said 3.10 → 1.08 off ws27's 1.08 + 1.01 + 1.01. HIGH |

Restated against s149's own numbers: 10.34 was 13.36 − 1.00 (the
path stat) − 1.01 − 1.01; from trunk the path stat's unit is already
gone and the probe's 0.12 went at ws29, so 12.27 − 2.00 = 10.27. The
two predictions agree on what the pin removes; they start from
different tables.

**The per-time drift, named before it is measured.** The two boxes
will not run at the same rate under `ptrace`; the gauge is nginx's
own traced rate on each (10,601 req/s keepalive / 5,774 close on the
ws29 box), since nginx did not change. Every per-request row of
lobo's that is a rate in disguise moves by that ratio and no more; a
row that moves by more than the drift is the pin's or a finding.

### Item 3 predicted: the parked task's `futex`, at idle and under the drive

wolf-lang#302's number was DERIVED at ws29 from two drives — (6,608 −
3,205) ÷ 8 s ÷ 4 hands ≈ 106 futex/s per hand — which is a difference
of two rates in disguise. This sprint measures it directly with
`tools/lobo-syscalls idle` (new: the same processes, the same window,
no generator, calls ÷ SECONDS) and re-reads the drives' raw column.
Predicted:

| | lobo, per hand | nginx, per worker | why |
|---|---|---|---|
| `futex` / s at idle | **~100–110**, nearly all of them errors (the ETIMEDOUT shape of a timed wait that re-arms) | 0 | the forwarder's compensation is a clock, not a request: at idle it is the WHOLE of lobo's futex; under the drive the reactor's park handoffs add to it |
| `poll` / s at idle | **~4** | 0 | `wait_budget` is 250 ms with nothing armed (ws29 lifted the 25 ms floor) |
| `epoll_wait` / s at idle | ~0–4 | ~0 (its timer wheel) | the reactor thread has nothing to wait for |
| before → after the pin | **the same number** | — | the runtime between the pins changed `fs.rs` and `net.rs` only; #302 is still open and nothing addressed it, so the idle rate holds and the drives' raw `futex` moves only with the drift |

If idle `futex` reads far below ~100/s per hand, ws29's derivation
was wrong (the rise under the drive would then be the reactor's, not
the forwarder's) and #302 needs an amended number; if it reads ~100
it is the witness the runtime lane asked for.

### The measurement — the count (runs 34553773533 before, 34554207566 after)

Both runs are on branch `ws30`, one instrument, one day, one runner
class (ubuntu-latest, 4 vcpus): the BEFORE at `daf629b` (trunk
`d04dd97` plus this sprint's idle shape, wolf 0.2.9), the AFTER at
`3c064d2` (the pin and the router, wolf `0.2.10+dev.fc07cc5`).

| row (per request) | keepalive: before → after (predicted) | close: before → after (predicted) | verdict |
|---|---|---|---|
| `statx` | 1.00 → **1.00** (1.00) | 1.00 → **1.00** (1.00) | **right** — the fstat; the path stat's unit was already gone |
| `openat` | 1.00 → 1.00 | 1.00 → 1.00 | right |
| `ioctl` | 0.00 → **gone from the table** (raw 221 → 0) | **1.00 → gone** (raw 34,237 → 0) | **right** — `accept4(SOCK_NONBLOCK)`; the listeners' own FIONBIO is outside the traced window |
| `setsockopt` | 0.00 → 0.00 (raw 221 → **114**; predicted ~231) | **1.00 → gone** (raw 34,237 → 0) | right per request; **the raw is half the prediction, and the rule says why** (below) |
| `accept4` | 0.00 → 0.00 | 1.08 → **1.08** (1.08) | right — the herd's lost races, 7.0% → 6.9% of accepts, untouched |
| `read` / `recvfrom` / `writev` / `close` | 1.00 / 1.00 / 1.00 / 1.00, unmoved | 1.08 → 1.07 / 1.00 / 1.00 / 2.01 → 2.00 | right — per-request rows hold to a hundredth |
| `poll` | 0.15 → 0.16 | 1.28 → 1.28 | right; on close `poll` is per CONNECTION (the probe before an accept), and it holds |
| `futex` | 0.10 → 0.07 | 0.39 → 0.32 | per-time, read raw below: the row did not move, the box did |
| `epoll_wait` / `epoll_ctl` / `write` / `brk` | 0.00 / 0.00 / — / 0.01 | 0.14 / 0.15 / 0.07 / 0.04, unmoved | right |
| **calls per request** | **6.29 → 6.25** (nginx 6.14 → 6.15; gap +0.15 → **+0.10**) — predicted 6.26 → 6.26 | **12.27 → 10.16** (nginx 10.13 → 10.13; gap +2.13 → **+0.03**, 1.21x → **1.003x** in calls) — predicted 10.27 | keepalive **right** (the pin buys the table nothing at two decimals); close **right on the mechanism, 0.11 better than the figure**, and the 0.11 is drift |
| accept side per close connection | — | **3.08 → 1.08** (1.08) | **right** — the whole of s149's second syscall |

**Every row that moved**: `ioctl` and `setsockopt` on the close shape
(each 1.00 → absent), and nothing else at two decimals. **Every row
that did not**: `statx`, `openat`, `read`, `recvfrom`, `writev`,
`close`, `accept4`, `poll`, `epoll_wait`, `epoll_ctl`, `write`, `brk`
— on both shapes. The close-shape total lands at 10.16 against a
predicted 10.27 because three per-time rows read lower on a faster
box (`futex` −0.07, `read` −0.01, `close` −0.01), which is the
prediction's own caveat landing: MEDIUM on any per-request figure of a
per-time row, by construction.

**The per-time drift, measured.** nginx's traced rate — the gauge,
since nginx did not change — was **8,672 → 13,740 req/s** on
keepalive (+58%) and **5,210 → 7,320** on close (+40%) between the two
boxes; lobo's went 8,271 → 12,074 and 4,257 → 6,844. Read raw over
the same 8-second drive across the same four hands:

| raw calls per 8 s drive, 4 hands | keepalive before → after | close before → after |
|---|---|---|
| requests completed | 66,172 → 96,601 (+46%) | 34,061 → 54,767 (+61%) |
| `futex` (errors) | 6,846 (6,840) → **6,976 (6,960)** — flat | 13,334 (7,611) → **17,578 (8,227)** (+32%, under +61% more requests) |
| `poll` | 9,956 → 15,063 (+51%: scales with requests — the pass's wait) | 43,606 → 70,077 (+61%: scales with connections — the probe) |
| `ioctl` + `setsockopt` | 221 + 221 → **0 + 114** | 34,237 + 34,237 → **0 + 0** |
| `epoll_wait` (the reactor thread's) | 5 → 14 | 4,781 → 7,515 |

So `futex` on keepalive is a CLOCK: the same ~6,900 calls a drive
whether the drive served 66k or 97k requests, which is why its
per-request figure fell 0.10 → 0.07 with nothing changed — the drift
this addendum named before the run. On close it is a clock plus the
reactor's parks (which scale with the herd's lost races, +61%), and
the sum grew slower than the requests did.

**Why keepalive `setsockopt` read 114 and not ~231.** The runtime
pays `TCP_NODELAY` before the first write that finds bytes of the
stream still in flight — concretely, before a stream's SECOND write
(`wolf_rt::net::Nodelay`: `Fresh` → `InFlight` on the first write of
n > 0 bytes; `arm_nodelay` pays on the next). Of the ~254 connections
the four hands accepted in the window, ~128 were the master's 200 ms
liveness probes (`docs/WORKERS.md` §Supervision — a CONNECT the hand
answers with one `sendto` and closes: one write, never a second, so
never the option) and ~126 were `ab`'s (32 held open plus one
reconnect per 1,000 requests, `keepalive_requests`' default). 114 of
those paid it at their second write; the dozen that did not were the
connections `-t 8` cut off inside their first. The prediction counted
every accepted connection; the rule counts the ones that write twice.
Per request the row is 0.00 either way; the raw column is where the
rule is legible, and it says the deferral is doing exactly what #290
described.

### The measurement — item 3, the parked task's `futex`, idle and under the drive

`tools/lobo-syscalls idle`, the same four hands, no generator, 8 s:

| idle, 8 s, 4 hands | before (wolf 0.2.9) | after (fc07cc5) | predicted |
|---|---|---|---|
| `futex` calls (errors) | **6,266 (6,266)** | **6,262 (6,262)** | "the same number" — **right** |
| `futex` / s, per hand | **~196** | **~196** | ~100–110 — **WRONG, low by half** |
| `poll` / s, all hands | 16 | 23 | ~16 — right before, high after (the loop woke more often: the master's probes, below) |
| `epoll_wait` | 0 | 0 | ~0 — right |
| the master's probe on the hand: `accept4` + `recvfrom` + `sendto` + `close` (+ `ioctl` + `setsockopt` before) | 128 each = **24 calls/s per hand** | 128 each = **16 calls/s per hand** | not predicted: a row this addendum did not know was there |
| **calls / s, all hands** | **897** | **872** | — |
| nginx, four workers, same window | **0** | **0** | 0 — right |

**The number for wolf-lang#302 is ~196 `futex`/s per hand, all of
them error returns, and the pin did not move it** (6,266 → 6,262 in
8 s is the same clock read twice). ws29's ~106 was a subtraction of
two drives whose "before" column carried the old self-raise probe's
own handoffs; measured with nothing else on the thread the cost is
almost twice that, and under the keepalive drive it is ~90% of every
`futex` the hands make (6,976 a drive against 6,262 idle). Posted on
#302 the same day with both raw tables. nginx makes NO syscalls at
idle: four workers in `epoll_wait` with nothing armed.

**The row the prediction did not know: the master's probe.** At idle
each hand accepts a fresh loopback connection from its master every
~250 ms (`docs/WORKERS.md`: "a hand is probed at most every 200 ms",
paced by the loop's own wait) and answers it with one `sendto` and a
close. Before this pin that was six syscalls on the hand per probe
(`accept4`, `ioctl`, `setsockopt`, `recvfrom`, `sendto`, `close`);
now it is four, because the accept posture arrives with the fd and a
single write pays no option — s149's second syscall, read a second
way. It is 16 calls/s per hand for supervision without a channel
(nginx has a socketpair; wolf-lang#235's inherited descriptor is what
would give lobo one), and it is lobo's design, not a finding against
the runtime; it is named here because an idle count now exists to
show it.

### W8 restated, the count beside the timing (parity run 34554232695)

The parity leg on the same day (`docs/PARITY.md`, the ws30 entry):
nginx ÷ ws30 **close 1.161x**, **keepalive 1.286x** at N=4 (VALID, the
fast class), and ws30 ÷ the pin-only tree **1.005x / 1.004x** — the
router half is worth in time exactly what it is worth in calls,
nothing. Beside the count: close **10.16 vs 10.13**, keepalive **6.25
vs 6.15**. So the count answers its question — the remaining gap is
NOT syscalls, on either shape — and the timing answers its: W8 linux
is **NOT MET on both shapes**. The count does not claim the bar. The
close cell's 16% at three hundredths of a call excess is the herd's
parks (the rows with a wait behind them: `accept4` 1.08, `poll` 1.28,
`futex` 0.32, the reactor's `epoll_wait`) and 0.19 more cores; the
keepalive cell's 29% is ws28's reading, the string runtime and the
transmit path. The prediction (PR #12, before the set was read) had
close at ~1.08x, pricing the accept side's two syscalls at ws25's
per-call rate against a cross-class ledger row; that comparison
cannot be made across classes and was wrong to be priced that way.


## ws31's addendum — the gap closed: the release pair, PREDICTED before the pin is staged, then the profile that names what remains (2026-09-11)

wolf **v0.2.11** tagged at `c9237c1` (r16; release run 34596068449)
and lupin **0.1.33** tagged at `18de030` (is45) the same morning. This
sprint pins both — the release archives themselves, by digest, never a
build on this box — re-reads the count at the release pair, and then
does what ws30 left as the next question: with the count within 0.03
calls of nginx on close and 0.10 on keepalive, and the timing at
1.161x / 1.286x, **profile the request on linux and name, by row, what
the remaining time is** — the runtime's (#298's copies, #299's head
list, #302's parked proc) or lobo's own. Everything under this heading
and above "The measurement" was written BEFORE `.wolf-bin` held the
release pair.

### The pairing shape, stated honestly

At the tags the pairing is **one release each way, not closed**:
`wolf 0.2.11` declares `lupin 0.1.32` (pin `e0ce018`, s147's fold,
twenty-two commits inside v0.2.10 — the release was cut before 0.1.33
tagged), and `lupin 0.1.33` declares pin `662b14c`, **the v0.2.10
tag** (s149–s155 are past it). ws30's gap was two releases at a dev
sha (`[wolf]` fc07cc5 declaring 0.1.31 with 0.1.29 staged); this is
each side one release behind the other's tag. What CAN be measured
here is narrower than "closed": whether anything in lobo's corpus
diverges between the two machines at these tags — the 63 files that
declare a lupin lane, run by the gauntlet against their own headers on
both tiers. Predicted: **zero divergence** — none of the clauses on
either side of the gap (s150's fn values and channel payloads, s151's
`then`, s152's `Map`, s153's built-`str` site, s155's operator
dispatch on the wolf side; is45's E0409/E0416/E0206/#84/#89 on the
lupin side) is spelled anywhere in `src/` or `tests/` (grepped at the
bump: no `: fn(` type, no `Map`, no `trait`/`impl`, no bare `if …
then`, no `str` slice assignment, no generic `fn x[`), so the lobo
corpus cannot reach the code either machine moved. That is a sentence
about lobo's corpus, not about the pairing.

### What the pin carries that lobo could feel — the census, predicted

The runtime's delta `fc07cc5..v0.2.11` in `crates/wolf_rt/src/` is
five files: `lib.rs` (+3: `pub mod map`), `map.rs` (new, s152),
`list.rs` (+23: `alloc_in` made `pub(crate)` for the closure seam and
`list_from_bytes` for `pairs()` — nothing lobo's lists call),
`native.rs` (+18: `__wolf_rt_closure_alloc`, s150) and
`task/chan.rs` (+151: payload boxes). **Nothing in `fs.rs`, `net.rs`,
`str.rs`, `signal.rs`, `reactor.rs` or `poll.rs`** — the serving path
runs the same runtime code it ran at fc07cc5, and so does the parked
signal proc (item 3 below).

| what the bump brings | class | predicted effect on lobo |
|---|---|---|
| s150 — every fn value is a pointer to a callable record; channel payloads beyond a word cross in boxes | LOWERING (fn values), RUNTIME (chan) | **zero**: lobo has no fn-typed value anywhere (grepped: no `: fn(`, `= fn(`, `-> fn(`), no channel (ws30 grepped; still none). The `else \|e\|` handlers are row handlers, not closures, and the baseline WIR carries **zero** `closure` constructs. The WIR and the release-tier LLVM IR of `src/main.lu` are predicted **byte-identical modulo any stamp line** — 174,425 WIR lines / 1,191 fns and 349,020 LLVM lines / 1,192 defines at fc07cc5, measured below at the release |
| s151 — the one-line `if` with a contextual `then`; `[gram.fmt.if]` never converts | GRAMMAR-WIDENING | **zero**: no bare `if` in the tree; `then` appears in strings only. wolf-lang's own s151 entry measured `wolf fmt --check` over lobo `d792290` (this tree) with the new binary: zero motion. The gauntlet's fmt step is the measurement |
| s152 — `Map[K, V]` typed, `m[k]` is `V ! {none}`, `op=` E0417, a struct key E0418 | TYPING (new), RUNTIME (five seams, `RT_SYMBOLS` 138 → 143) | **zero**: lobo's kind table, head memo and connection table are parallel `List`s (ws27/ws28); there is no `Map` in `src/` or `tests/` |
| s153 — `[mem.region.escape]`: a `str` built by `+`, `+=` or a holed interpolation is an allocation site in the region of the building expression; leaving it is **E1010** | TIGHTENING — the one rule that could red the build | **zero, predicted by reading every region block.** lobo has four: `serve.serve_file`'s `region resp {…}` (the plaintext small arm) and `region chunkr {…}` (the stream), `budget.body_small`'s `region resp(cap:) {…}` and `body_stream`'s `region chunkr(cap:) {…}`. Each builds a `List[byte]` (the body, the chunk, `head.bytes()`, the gather's `parts`) and nothing else; every `str` they touch (`head`, `path`) is built OUTSIDE and lent in; each block's tail is a scalar on purpose (`wcode = wcode`, ws10) and the only values crossing out are `int`s. No `+`, no `+=`, no interpolation stands inside any of the four, so there is no built-`str` site to escape. The checked budget (`[exec.checked.budget]`) is the checked tier's: the corpus's checked lanes run short programs and none is predicted to exhaust bytes |
| s155 — operators dispatch through traits on a type parameter or a user type; `trait Num = …` | TYPING | **zero**: lobo defines no trait and no impl; every operator in the tree is on two primitives, which stay builtin |
| #282 — `wolf --version \| head -1` exits 0 | DRIVER | MECHANICAL; `lib-toolchain.sh` already reads the first line through `head -1` |
| r16 — the version sites, the pairing at 0.1.32 | MECHANICAL | the `.wolfi` toolchain stamp `0.2.10 → 0.2.11` in every header |

**The census, predicted**: the gauntlet's counts at trunk `d792290`
(the before-run of this sprint's own gauntlet, at the fc07cc5 pair)
are the baseline, and **every row is predicted identical at the
release pair** — corpus **272 lane-runs** (63 lupin-lane files
among them), differential 3/3, proxy 8/8, control 9/9, logdiff 4/4,
signal (macOS: the named skip), prefork 38/38, membudget 17/17,
resolver 9/9, replay 2/2, metrics, dryrun, shell, confcheck, tls,
acme, dist. Source motion for the pin's own sake: `wolf-toolchain.toml`
and the two `shell.lu` constants (`toolchain_version` "0.2.11",
`toolchain_pin` "c9237c1"). **The `.wolfi` motion is the first test of
s148's content-only rule (#292) at a pin bump**: ws30 re-derived every
hash once and recorded "the next pin moves only the header stamp";
predicted here as **fourteen files, one line each** — `toolchain
0.2.10 · edition v1` → `0.2.11` — and **every `export_hash`, `pkg_hash`
and dep hash unchanged**, ZERO item motion. `[lupin]` 0.1.29 → 0.1.33
(is42–is45): the mirrors it takes (a leading `else`, the range arm,
`then`, E0409 on either side of a row compare, E0416 on a `str` slice
assignment, one `T` per call, a keyword in type position E0206) are
all tightenings lobo's source does not spell (grepped at the bump), so
the **63 lupin-lane files are predicted to move by zero**.

### The count at the release pair, predicted

The serving path's runtime is fc07cc5's byte for byte (the delta above
touches no file it calls), so the count is ws30's, read again on
another VM of the same class: **keepalive 6.25 ± 0.02 against nginx
6.15**, every per-request row (`statx` 1.00, `openat` 1.00, `read`
1.00, `recvfrom` 1.00, `writev` 1.00, `close` 1.00) held to a
hundredth, `poll` and `futex` moving only with the box's rate; **close
10.16 ± 0.10 against 10.13**, `accept4` 1.08 (the herd, lobo#5,
untouched), `poll` 1.28 per connection, no `ioctl`, no `setsockopt`.
Any per-request row that moves by more than a hundredth is a finding
against this prediction and a filing.

### Item 3, said rather than re-measured

wolf-lang#302's parked proc: the runtime between fc07cc5 and v0.2.11
touched `task/chan.rs` alone under `task/` and nothing under
`signal.rs`, `reactor.rs` or `poll.rs` — the compensation clock that
costs an idle hand ~196 `futex`/s is the same code. The count leg's
idle shape runs regardless (it is one line of the CI step) and is
predicted to read **~196/s per hand, every one an error return**
(6,200–6,300 calls per 8 s over four hands), nginx 0, the master's
probe 4 calls a probe. If it reads otherwise the prediction is wrong
and the runtime changed something this reading of the diff missed.

### Item 2 — the profile, PREDICTED: what remains of W8 on linux, by row

The instrument is ws25/ws28's, `tools/lobo-profile` (`perf record -F
997 -g` on ONE serving process for eight seconds under four `ab -c 8`
generators, then `strace -c` on a separate drive), on the CI runner,
this sprint on BOTH shapes — and, new, at **N=4 as well as N=1**: the
tool gains a fifth argument (the worker count) and a by-thread report
(`--sort comm`), because the close cell's gap lives at four hands
(N=1 close is 1.065x, inside the bar; N=4 is 1.161x) and a profile at
one hand cannot see it. `perf` samples CPU, not wall: a parked hand
takes no samples, so what a park costs in cpu shows (its syscalls, the
switch), and what it costs in latency shows only in the parity table's
req/s.

**The arithmetic the pricing is read against** (ws30's parity run
34554232695, the fast class, cores ÷ req/s):

| cell | lobo µs cpu / request | nginx µs cpu / request | gap | timing |
|---|---|---|---|---|
| N=1 keepalive | 19.6 (1.00 core, 50,986 req/s) | 15.8 | **3.8 µs** | 1.248x |
| N=4 keepalive | 22.9 (2.67 / 116,787) | 16.3 | **6.6 µs** | 1.286x |
| N=1 close | 34.6 (0.99 / 28,640) | 32.5 | **2.1 µs** | 1.065x |
| N=4 close | 45.4 (1.81 / 39,860) | 34.9 | **10.5 µs** | 1.161x |

So the keepalive gap is ~4 µs of cpu a request at one hand and ~7 at
four; the close gap is ~2 µs at one hand and ~10 at four. A profile
row is priced as its share of lobo's per-request cpu on that cell.

**Predicted, keepalive, one hand** (ws28's linux table at 0.2.9 is
the base: 74.4 / 18.2 / 6.9 kernel / lobo+runtime / libc; the runtime
is statically linked, so `lobo-release` the dso is lobo's frames AND
`wolf_rt`'s):

| | predicted |
|---|---|
| kernel / lobo-release / libc | **73–76% / 17–19% / 6–8%** — nothing on the path changed since ws28 but ws29's park (a thread that takes ~no samples) and ws30's `classify` (a lookup fewer, a stat the same) |
| in a syscall, inclusive | 66–70% |
| `writev` inclusive (the transmit path down to the loopback softirq) | 38–42% — **not a gap row**: nginx pays the same path for the same bytes |
| `recvfrom` + the file's `openat`/`fstat`/`read`/`close` | 18–22% — not gap rows either (nginx without `open_file_cache` opens per request too) |
| **the runtime's allocations and their faults** — `ambient_alloc`, `__wolf_rt_list_new`/`list_push`, `do_user_addr_fault` + `clear_page_erms` + `__handle_mm_fault` (the 2,315 retained bytes a request, #191/#298) | **2.5–3.5%**, ~0.5–0.7 µs — **the runtime's** (#298 items 1–3 and #191) |
| **libc copies** — `memset` (`net_read`'s 4 KiB zeroing, #298 item 3), `memcpy`/`memmove` (the read's arena copy; `head.bytes()`'s 241 B, #299) | **2–3%**, ~0.4–0.6 µs — **the runtime's** (#298, #299) |
| **the parser and its searchers** — `parse_request`, `split_lines_strict`, `TwoWaySearcher::next` + `StrSearcher::new` under lobo's `find`s, `lower_token` | **3–4%**, ~0.6–0.8 µs — **lobo's own** (the searchers are the runtime's `str.find`, but lobo chooses the calls) |
| **the loop and the route** — `serve_main`, `conn_step`, `serve_request`, `handle_request`, `head_warm`, `classify`, `normalize_path`, `join_path` | **3.5–4.5%**, ~0.7–0.9 µs — **lobo's own** |
| #302's parked proc — `futex` wakes on the forwarder's thread | **under 0.2%**: ~196 wakes/s at a few µs each against ~50k req/s is ~0.006 calls and ~0.02 µs a request; visible in the by-thread report as a thread with a handful of samples, invisible in the leaf table |

Read together: of the ~4 µs a keepalive request costs more than
nginx's at one hand, the runtime's rows above are predicted at
**~1.0–1.3 µs** (#298/#299 — the copies and the retained bytes) and
lobo's own frames at **~1.3–1.7 µs**, with the remainder inside kernel
rows that read the same by name on both sides but cost lobo more
(the fault path under the arena's growth, `poll` at 0.16 a request
where nginx's `epoll_wait` is 1.00 — lobo makes FEWER wait calls and
each returns more). #302 is not a keepalive row at all.

**Predicted, close, one hand** (ws25's fstat-tree table is the base:
76.3 / 14.5 / 9.0; since then the accept posture took two syscalls per
connection and the gather/read arms are the same):

| | predicted |
|---|---|
| kernel / lobo-release / libc | **77–80% / 12–14% / 7–9%** |
| `writev` inclusive / `close(2)` inclusive (the FIN, `__fput`) / `accept4` inclusive | 22–26% / 15–18% / 6–9% — the close SHAPE's own cost; nginx pays all three |
| the runtime's allocations + faults (8,779 retained bytes a connection, ws28: the conn seam's six lists, the accept record, the parser's four) | **3–4%** — the runtime's (#298/#191), larger than on keepalive because a connection retains ~2 fresh pages |
| lobo's own frames (the loop, `arm_accept`, the connection table's push/remove, the route) | **3–4%** — lobo's own |
| the parser + searchers | 2–3% — lobo's own |
| libc copies | 1.5–2.5% — the runtime's |

**Predicted, close, FOUR hands, one hand sampled** — the cell the bar
gates: the same rows plus the herd's cpu — `accept4` returning
EAGAIN (0.08 a connection), the `poll` probe before every accept after
a burst's first (1.28 a connection, lobo's own design), the park's
mechanics on a lost race (`epoll_ctl`, the eventfd `write`/`read`,
`futex`, ~0.9 syscalls and two context switches per lost race — the
`wolf-reactor` thread's rows in the by-thread report) — predicted
**2–4% of the hand's cpu together**, i.e. ~1–2 µs of the 10.5 µs
N=4 gap. The remaining ~8 µs is predicted NOT to be a cpu row of one
hand at all but the herd's WALL — four hands waking on one listener
for every SYN (`net_wait` returns on all four; one wins), which
`perf` on cpu cannot price and the count shows as `poll` 1.28 — plus
whatever the fault path costs when four arenas grow at once. If the
N=4 one-hand table reads within 2 points of the N=1 table by dso, the
herd is wall and lobo#5 stands as written; if `lobo-release` or the
scheduler's rows (`schedule`, `__switch_to`, `try_to_wake_up`) grow
by more, the park's cpu is larger than lobo#5 priced it.

**Predicted, keepalive, four hands, one hand sampled**: within 2
points of the one-hand table by dso — this shape has no listener
race; the extra ~3 µs a request at N=4 over N=1 is predicted to be
the four generators and four hands sharing four vcpus with nginx's
own cell having the same shape, not a row.

**The top five, predicted, and whose they are** (keepalive, the cell
furthest from the bar; shares of one hand's cpu, priced in µs of a
~20 µs request):

| # | row | predicted share | µs | whose | what it would take |
|---|---|---|---|---|---|
| 1 | the transmit path (`writev` inclusive) | ~40% | ~8 | the kernel's, both sides | nothing — not a gap row |
| 2 | the loop + the route (`serve_main` … `classify`) | ~4% | ~0.8 | **lobo's** | a lobo-side row only if one function inside it is over ~1% by itself and under a day |
| 3 | the parser + the searchers | ~3.5% | ~0.7 | **lobo's** (ws28's views already took the copies out; what is left is the walk) | the same rule |
| 4 | the runtime's allocations + the fault path | ~3% | ~0.6 | **the runtime's** — #298 items 1–3, #191 | `net_read` into the arena / no zeroing (#298 item 3), the list headers (#191) |
| 5 | libc `memset`/`memcpy` | ~2.5% | ~0.5 | **the runtime's** — #298 item 3, #299 | `net_writev` taking a `str` part (#299), the un-zeroed read (#298) |
| — | #302 | <0.2% | <0.05 | the runtime's | nothing for W8 on this shape; the idle count is its witness |

If the measurement puts a lobo-own function over ~1% of the request
by itself and the fix is a morning, this sprint takes it and measures
it (a two-tree parity set on one VM, `ref_tree` = this branch before
the fix, which pins the same toolchain and so CAN be built beside it);
otherwise the profile is the deliverable and the rows are filed where
they belong.


### The measurement — the pin, the census, the IR (the gauntlet twice on macOS arm64, the IR diffed)

Both gauntlets GREEN, exit 0: the fc07cc5 pair on trunk `d792290`
(12:09–12:13Z) and the release pair on `92c373b` (12:15–12:21Z). The
75 summary rows of the two logs diffed: **identical** but for pids,
which hand a held connection landed on, and the stamp strings —
corpus **272/272** lane-runs (63 lupin), every other row as
predicted. E1010: **zero** (both tiers build). `.wolfi`: **14
insertions, 14 deletions, `toolchain 0.2.10 → 0.2.11` and nothing
else** — #292's content-only rule at its first pin bump, exactly as
ws30 wrote it. `wolf fmt --check`: zero. #146: an eighteenth ICE
(`sc_muladd`, `%19 is not dominated by its definition`).

**The IR — wrong by one site, not lobo's.** WIR of `src/main.lu`
174,425 → 174,426 lines, **9 diff lines**: the two stamp strings, one
length constant, and `std.str.each_word`'s callback call — `call.ind
%1(%137)` at fc07cc5, `%138 = load.ptr %1, %3; call.ind %138(%1,
%137)` at v0.2.11, s150's record-leading shape — the one `fn`-typed
parameter in the PINNED STD TREE this program links, which nothing in
lobo calls. Release LLVM IR 349,020 → 349,025 lines, 35 diff lines
with metadata numbers normalized (the same site and its `!noalias`
scopes). 1,191 WIR functions / 1,192 LLVM defines at both pins; zero
motion on the serving path. The prediction's lesson: "no fn values"
was a sentence about `src/`; the linked std tree carries one.

### The measurement — the count at the release pair (run 34598620069)

| row (per request) | keepalive: ws30 → ws31 (nginx) | close: ws30 → ws31 (nginx) |
|---|---|---|
| `statx` / `openat` / `read` / `recvfrom` / `writev` | 1.00 → **1.00** each | 1.00 → **1.00** each (`read` 1.07 → 1.07) |
| `close` | 1.00 → 1.00 | 2.00 → 2.00 |
| `accept4` | — | 1.08 → **1.08** (the herd, lobo#5) |
| `poll` | 0.16 → 0.15 | 1.28 → **1.28** |
| `futex` | 0.07 → 0.10 | 0.32 → 0.36 |
| `epoll_wait` / `epoll_ctl` / `write` / `brk` | 0.00 / 0.00 / — / 0.01 | 0.14 / 0.15 / 0.07 / 0.04 — unmoved |
| `ioctl` / `setsockopt` | absent | absent |
| **calls per request** | **6.25 → 6.27** (6.14; +0.13) — predicted 6.25 ± 0.02 | **10.16 → 10.20** (10.13; +0.06) — predicted 10.16 ± 0.10 |

**Right on every per-request row, to a hundredth.** The two
hundredths on keepalive and four on close are the `futex` clock read
on a SLOWER VM (nginx's traced rate 13,740 → 10,720 keepalive, 7,320
→ 5,663 close): raw `futex` 7,444 per 8 s keepalive (ws30: 6,976)
over 75,578 requests (ws30: 96,601) is 0.098 where ws30's was 0.072
— the per-time drift ws29's amendment names, and nothing else moved.
The release runtime's serving path is fc07cc5's, as the diff said.

### The measurement — item 3, the idle count (the same run)

`tools/lobo-syscalls idle`: **`futex` 6,269 calls in 8 s over four
hands, 6,269 errors — 783.6/s, ~196/s per hand**; `poll` 21.3/s; the
master's probe 16/s each of `accept4`/`recvfrom`/`sendto`/`close` (4
calls a probe, as ws30 measured after the posture); **870.5 calls/s
in all** (ws30: 872); nginx **0**. Predicted ~196/s and 6,200–6,300
calls — right. The runtime did not touch the parked proc between the
pins (the diff) and the number says the same thing (6,262 → 6,269).
wolf-lang#302 stands as posted at ws30; nothing to re-post.

### The measurement — the profile by dso, four cells (runs 34598623726 keepalive N=1, 34598625530 close N=1, 34598628016 close N=4, 34598629759 keepalive N=4; `92c373b`, one runner class, 12:25Z)

`perf record -F 997 -g` on ONE serving process for eight seconds
under four `ab -c 8` generators, loads 2.96–3.32 at the start (the
toolchain build's tail; a share, not a rate):

| cell | req/s under perf (summed) | kernel / lobo-release / libc / vdso | predicted | in a syscall (incl.) | `writev` incl. | reactor thread |
|---|---|---|---|---|---|---|
| keepalive N=1 | 47,043 | **79.7 / 14.3 / 5.7** / 0.4 | 73–76 / 17–19 / 6–8 | 75.2% | 41.3% | none started |
| keepalive N=4 (one hand of four) | 66,538 | **73.1 / 19.3 / 7.3** / 0.3 | within 2 points of N=1 | 66.9% | 38.3% | 0 samples (comm) |
| close N=1 | 15,337 | **81.3 / 13.5 / 4.9** / 0.3 | 77–80 / 12–14 / 7–9 | 74.0% | 31.2% | none started |
| close N=4 (one hand of four) | 21,728 | **77.4 / 15.5 / 6.8** / 0.3 | within 2 points of N=1 | 68.9% | 25.4% | **`wolf-reactor` 1.74%** |

Read: the dso split at one hand is MORE kernel than ws28's 74.4 /
18.2 / 6.9 (keepalive) — the user-space quarter shrank to a fifth
(14.3 + 5.7) with ws30's `classify` and a faster VM class (47k under
perf where ws28 saw 31k), and the shares landed outside the
prediction's brackets by 3–4 points on each side: the prediction
carried ws28's user share forward and it had already fallen. Close at
one hand is four fifths kernel, as ws25 read it. **At four hands the
user-space share GROWS on both shapes** (+5.1 points keepalive, +3.9
close), against the prediction of "within 2 points": with eight
connections per hand instead of thirty-two, a pass finds fewer ready
connections and the loop's own frames (`serve_main` 1.13 → 1.26,
`serve_request` 0.65 → 1.03) and a context switch (`finish_task_switch`
0.50) are paid per fewer requests; the `poll` count per request is
the same 0.15, so it is the pass's bookkeeping, not a syscall. The
reactor thread is 1.74% of a close-shape hand's cpu at four hands and
absent at one — the herd's park mechanics, in the bracket predicted
(2–4% with the main thread's own `futex`/`epoll_ctl`/eventfd rows);
the wolf-reactor row confirms the thread starts only when a hand
loses a race.

**The one-hand strace beside each profile** (a separate drive, the
hand alone, 8 s): keepalive N=1 `futex` **1,488 in 8 s = 186/s, all
errors** — wolf-lang#302's clock, read on the profiled hand itself;
close N=4, worker 1 alone: `accept4` 9,276 with **2,551 EAGAIN**
against 6,690 connections served — this hand lost 0.38 races per
connection it won, `futex` 1.38 / `epoll_wait` 0.68 / `epoll_ctl` 0.76
/ eventfd `write` 0.38 per connection on top, where the four-hand
average in the count leg is `accept4` 1.08 and `futex` 0.36: the
herd's losses fall unevenly and a ptraced hand loses more, which is
why the count leg (all four traced alike) is the number and this
column is the mechanism.

### The measurement — the profile BY FUNCTION (runs 34599274095 keepalive N=1, 34599275985 close N=1, 34599278195 close N=4, 34599280320 keepalive N=4; `f9f95e7`, the user-space leaves by dso down to 0.1%)

The whole-process leaf table cuts at 0.4% and a request's user-space
fifth is spread over rows smaller than that, so the tool grew two
tables per cell — the leaves inside `lobo-release` (lobo's frames AND
the statically linked runtime) and inside libc, down to 0.1% — and
the four cells were taken again. Two things first. **The dso split
is itself a VM-class number**: keepalive N=1 read 79.7 / 14.3 / 5.7 on
a VM serving 47k req/s under perf (the first set) and **74.9 / 18.5 /
6.0** on one serving 31k (this set); close N=4 read 77.4 / 15.5 / 6.8
at 21.7k and **74.0 / 17.2 / 8.2** at 52k. The user-space share is
larger on the slower VM class on the keepalive shape and on the
faster one on the close shape, so a share is compared within one run,
never across two, and each table below names its own req/s. And
**`--sort tid` is not a perf 6.17 key** — the by-thread report printed
nothing and said so (fixed to `pid`, the per-thread key; the runs at
`cf1141f` carry it; the `comm` report of the first set already named
`wolf-reactor` at 1.74% of the close N=4 hand).

**Keepalive, one hand (31,008 req/s under perf; 74.9 / 18.5 / 6.0):**
the per-request cell, priced against the parity VM's **34.2 µs of cpu
a request** (1% ≈ 0.34 µs) and its **5.2 µs gap** to nginx.

| row (leaf, self) | share | whose |
|---|---|---|
| `serve_main` (the pass: the wait set rebuilt, the seven per-pass lists, the walk) | **1.29** | lobo |
| `serve.serve_request` | **1.12** | lobo |
| `http.parse_request` | 0.84 | lobo |
| `TwoWaySearcher::next` + `StrSearcher::new` + `__wolf_rt_str_find` — the `find` family under lobo's `find`s | **0.90 + 0.69 + 0.30 = 1.89** | the runtime's shape, lobo's calls |
| `ambient_alloc` + `list_new` + `list_push` (the arena) | 0.73 + 0.31 + 0.19 = 1.23 | the runtime (#191, #298) |
| `serve.head_warm` | 0.61 | lobo (the memo's key: a byte fold and six compares) |
| `http.split_lines_strict` | 0.59 | lobo |
| `serve.serve_file` / `conn_step` / `step_serve` / `handle_request` | 0.44 / 0.35 / 0.31 / 0.29 | lobo |
| `http.lower_token` / `contains_fold` / `is_canonical` / `child_arg1` / `match_location` | 0.40 / 0.21 / 0.19 / 0.23 / 0.15 | lobo |
| **`proxy.first_http` + `proxy.plan` (+ `first_server`, `child_arg1`'s share)** — the route resolving by scanning the config's name table, per request, on a config with no `proxy_pass` | **0.31 + 0.28 ≈ 0.6–1.0** | lobo — a row nobody had named |
| `note_request` / `metrics.hist_observe` / `fill_req_acc` (the access record, the histogram) | 0.23 / 0.20 / 0.16 | lobo |
| the runtime's syscall wrappers: `net_writev` 0.31, `writev_ready` 0.16, `read_shim` 0.21, `fs_open` 0.18, `File::open_c` 0.16, `CStr::from_bytes_with_nul` 0.15 (the path copied to a C string per open), `ledger_on_free` 0.16 | 1.33 | the runtime |
| libc: `open64` 0.46, `writev` 0.43, `__close` 0.30, `statx` 0.28, `recv` 0.26, `read` 0.25, `clock_gettime` 0.26 | 2.24 | both sides pay these |
| libc: `malloc` 0.26 + `__libc_calloc` 0.21 + `cfree` 0.28 — `calloc` IS `net_read`'s zeroed 4 KiB `Vec` (#298 item 3), the rest the strbuf boxes | 0.75 | the runtime (#298) |
| the fault path, kernel-named (first set: `do_user_addr_fault` 1.24, `clear_page_erms` 0.74, `do_anonymous_page`, `__handle_mm_fault`) — the pages the retained 2,315 B/request fault in | ~2.5 | the runtime (#191) |
| `writev` inclusive — the transmit path | 41.3 | both sides; not a gap row |

**The top five, measured and priced** (keepalive, one hand; the
prediction's table had the loop and the parser at 2–3 and 3–4 and the
runtime's rows at 4–6 — the order came out the same and the sizes
close):

| # | row | share | µs of 34.2 | whose | against |
|---|---|---|---|---|---|
| 1 | the transmit path (`writev` inclusive) | ~41% | ~14 | the kernel's, both sides | not a gap row |
| 2 | **lobo's own frames** — the loop and the route (`serve_main`, `serve_request`, `conn_step`, `step_serve`, `handle_request`, `head_warm`, the config scan), the parser (`parse_request`, `split_lines_strict`, `lower_token`, `contains_fold`), the access record and the histogram | **~8.2%** over 0.1% (≈ 9–10 with the tail) | **~2.8–3.3** | **lobo's** | the biggest single function is the pass at 1.3%; no lobo function is over 1.5% by itself |
| 3 | **the runtime's allocations and the pages they fault in** — `ambient_alloc`/`list_new`/`list_push` 1.23, `malloc`/`calloc`/`cfree` 0.75, the fault path ~2.5 | **~4.5%** | **~1.5** | the runtime's | **#298** items 1–3 (`calloc` is the read's zeroing; the strbuf boxes), **#191** (the retained bytes: 2,315 B a request is 0.57 fresh pages a request, `clear_page_erms`) |
| 4 | **the `find` family** — a `TwoWaySearcher` built (`StrSearcher::new` 0.69) and run (`next` 0.90) for every `find`, needles of one to four bytes (`\r\n`, `:`, ` `, `/`) | **1.9%** | **~0.65** | the runtime's shape, under lobo's calls | not in #298: filed new — a searcher per call for a short needle where a `memchr`/`memmem` path is an order cheaper |
| 5 | the runtime's wrappers around the syscalls (`net_writev`, `writev_ready`, `read_shim`, `fs_open`, `open_c`, the `CString` per open, `ledger_on_free`) | 1.3% | ~0.45 | the runtime's | small; the `CString` is a path copy a request |
| — | **#299** (the head's `bytes()` copy, 241 B + a list) | under 0.1% — no row | <0.03 | the runtime's | the copy is ~20 ns; its list header is inside row 3 |
| — | **#302** (the parked proc's `futex`) | the hand's strace: **1,529 `futex` in 8 s = 191/s, all errors**; in cpu under 0.1% | <0.02 | the runtime's | a count, not a time; nothing for W8 |

Sum of the gap rows: lobo ~2.8–3.3 µs, the runtime ~2.6 µs (rows 3–5)
— **~5.5 µs against the measured 5.2 µs gap at one hand**. So on the
keepalive shape at one hand the gap is user space, split near evenly
between lobo's own frames and the runtime's, and the runtime's half
is three rows: the allocations and their pages (#298/#191), the
searcher-per-`find`, the wrappers.

**Close, one hand (16,118 req/s; 81.3 / 13.1 / 5.4)** — the cell that
is AT PARITY (0.994x, 65.1 µs both sides): the same rows at smaller
shares (`serve_main` 1.17, `parse_request` 0.63, `serve_request`
0.62, `ambient_alloc` 0.58, the `find` family 1.07, `head_warm` 0.40,
`list_new` 0.31, `net_writev` 0.28; libc `malloc`/`calloc`/`cfree`
0.85), under a kernel share that is the accept and the teardown. lobo
spends the same ~6 µs of user space here as on keepalive and nginx
spends its ~2 µs; the difference sits inside a 65 µs connection whose
other 59 µs is the kernel's on both sides, and the ratio reads 0.994x.

**Close, four hands, one sampled (52,075 req/s summed; 74.0 / 17.2 /
8.2)** — the bar's cell, +17.6 µs a connection over nginx where one
hand is +0.0: `ambient_alloc` **3.41%** (0.58 at one hand; **0.87** in
the first four-hand set at 21.7k req/s — a row that varies 4x between
two VMs of the same cell is reported, not filed), `serve_main` 1.12,
the `find` family 1.73, `head_warm` 0.71, **`__wolf_rt_net_wait` 0.59
+ the `Vec<i64>::from_iter` under `wait_ready` 0.21** (the pass's
pollfd array and ready list, built per pass — at 1.28 passes a
connection), `net_accept` 0.41, `split_lines_strict` 0.56,
`serve_request` 0.47, `list_new` 0.44; libc `__poll` 0.50, `accept4`
0.47, `malloc`/`realloc`/`cfree`/`calloc` 1.2; the fault path ~3.1
(`do_user_addr_fault` 1.58); the `wolf-reactor` thread 1.74% (first
set). The hand's own strace: `accept4` 28,779 with **7,012 EAGAIN**
against 21,726 connections — 0.32 lost races a connection won on
worker 1 under ptrace, `futex` 1.02, `epoll_wait` 0.57, `epoll_ctl`
0.65, `poll` 1.38 a connection. Priced: the herd's cpu on this hand
(the reactor thread, the losers' `accept4`, the park's `futex`/
`epoll_ctl`/eventfd, the `poll` probe) is **~3–5% of the hand ≈ 2–4
µs a connection**, in the bracket predicted (2–4%), and the other
~13 µs of the 17.6 is not a cpu row of one hand: it is the four hands'
WALL — every SYN wakes four `net_wait`s, one wins, three paid a pass
for nothing (`poll` 1.28 a connection is that pass) — and the four
arenas faulting at once. **lobo#5 stands as written**: the count's
`accept4` 1.08 / `poll` 1.28 / `futex` 0.36 are the rows, a kernel-
distributed wake (`EPOLLEXCLUSIVE`, wolf-lang#267) or a park-free
loser is what would move them, and nothing on lobo's side under a day
does.

**Keepalive, four hands, one sampled (65,670 req/s summed; 74.6 /
18.3 / 6.6)** — +11.1 µs a request over nginx where one hand is +5.2:
the one-hand table again with the loop's rows a little larger
(`serve_main` 1.54, `ambient_alloc` 1.08, `serve_request` 1.04,
`parse_request` 0.89, the `find` family 1.3, `head_warm` 0.62,
`classify` 0.17) and nothing new over 0.1%. The count says the pass
frequency is nginx's own (`poll` 0.15 a request beside `epoll_wait`
0.13), the profile says no row grew by more than half a point, and
the parity table says lobo's cpu a request rose 34 → 39 µs across the
cells while nginx's fell 29 → 28. **The ~6 µs a request that four
hands pay and one does not on this shape has no row in a one-hand
profile**: it is what four hands, four generators and the softirq
path cost each other on four vcpus, and nginx's four workers do not
pay it. Named, not explained; a per-cpu or cross-hand instrument
(`perf` over all four hands with `--sort cpu`, or `perf sched`) is the
next reading, and it is not this sprint's.

### The row that could be taken, and why it was not

The rule was: a lobo-side row, under a day, then take it and measure
it. The candidates the table names: **the pass** (`serve_main` 1.3–1.5%,
the seven per-pass lists rebuilt on every pass — a restructure of the
connection table the drain and the generations ride on: past a day);
**the route's config scan** (`proxy.plan` + `first_http` +
`first_server` + `child_arg1`, ~0.6–1.0%: a per-generation memo of the
plan keyed on the normalized path, with a reload-invalidation witness
— a morning to write, but 1% is under the parity instrument's floor
(ws30's "nothing" change read 1.005x [0.998, 1.006]) and the share
table is the only thing that would read it, on a two-tree profile);
**`head_warm`'s key** (0.6%, the same floor). None is both over the
floor and under a day, so none was taken blind; the config scan is
filed as lobo's (lobo#14) with the numbers, the `find` family upstream
(wolf-lang#335), and #298's rows carry the release-pin prices.

### The measurement — by thread (runs 34599620912 keepalive N=1, 34599622683 close N=4; `cf1141f`, `--sort pid`)

| cell | the serving thread | `wolf-reactor` | the signal forwarder's carrier (unnamed) |
|---|---|---|---|
| keepalive, one hand (29,079 req/s; 74.9 / 18.5 / 6.3) | **99.99%** | not started | **0.01%** — 1,528 `futex` in the same window's strace |
| close, four hands, one sampled (22,131 req/s summed; 76.8 / 16.6 / 6.3) | **98.33%** | **1.60%** | 0.06% |

**#302 priced to the hundredth: the parked proc's ~190 `futex`/s is
0.01% of a serving hand's cpu.** The reactor thread is 1.60% of a
four-hand close hand (1.74% in the `comm` set) and absent at one
hand: the herd's park mechanics, and the only thread row W8 has.

## ws32's addendum — the herd: two candidates, each alone, PREDICTED before either is built (2026-09-11)

lobo#5 at the release pair (ws31): N=1 close is AT parity (0.994x,
65.1 µs a connection on both servers) and N=4 close is 1.139x with
+17.6 µs a connection, of which one sampled hand's cpu accounts for
~2–4 µs (the reactor thread 1.6–1.7%, the losers' `accept4`, the
park's `futex`/`epoll_ctl`/eventfd) and the rest is four hands' wall:
every SYN wakes four `net_wait`s, one wins, three paid a pass for
nothing (`poll` 1.28 a connection). ws27 named two candidates and this
sprint measures each ALONE on the count leg and the parity leg, both
predicted here first, and takes the one that moves the N=4 close
number below the parity instrument's floor (~1%: ws30's no-op read
1.005x [0.998, 1.006]) — or says neither does. The parity leg is the
ws25 two-tree shape: the candidate ÷ trunk `d3dec23` on ONE VM against
that VM's own nginx; the count leg is ws27's `strace -c` over all four
hands. Everything under this heading and above "The measurement" was
written before a dispatch.

### What the runtime offers, read off v0.2.11's `net.rs` (the candidates as lobo can spell them)

`net.rs` did not move between v0.2.11 and trunk (the one commit past
the tag is the release commit). Two facts decide what each candidate
IS:

- **`net_deadline(fd, 0)` CLEARS the budget.** `set_deadline` maps
  `millis <= 0` to `deadline: None`, and `try_then_park` with `None`
  is `wait_raw(raw, Read, None)` — an unbounded park. ws27's
  correction on lobo#5 stands: there is no try-once accept in the
  runtime (wolf-lang#267 asks for one), so the only "zero accept
  budget" lobo can write is the ws17 shape — a loser parks in the
  reactor until the NEXT SYN wakes it, not for 5 ms.
- **`net_listen_with(addr, reuse_port, backlog)`** sets `SO_REUSEPORT`
  before the bind. Linux distributes the group by 4-tuple hash; macOS
  hands every SYN to the newest bound member (s137, and lobo's own
  `tests/serve/reuse_port_posture.lu`: 0/0/30); windows answers
  `unsupported` by name (the alias to `SO_REUSEADDR` would be a silent
  hijack — `docs/platforms.md`). A group member that never accepts
  swallows its hash share, so in this shape the MASTER must not hold a
  member: each hand binds its own socket, and the master binds nothing.

### Candidate (a) — `arm_accept` at 0: the unbudgeted accept

The change is one line (`net_deadline(l, 0)` in `arm_accept`), taken
on a side branch `ws32-a` off this one and never merged. Predicted:

| leg | prediction |
|---|---|
| count, close N=4 | **no row moves by design**: `accept4` 1.08 → 1.05–1.10 (the race is the same race; the loser parks longer, then re-races on the next SYN), `futex` 0.36 / `epoll_ctl` 0.15 / `epoll_wait` 0.14 / eventfd `write` 0.07 each within ±0.05, `poll` 1.28 → 1.2–1.3; total 10.20 → 10.1–10.3. Only the park's LENGTH changes, and a count cannot see length |
| parity, close N=4 | delta ws32-a ÷ trunk **1.00 [0.98, 1.02]** — under the floor |
| parity, keepalive N=4 | **at risk, and the risk is the ws17 bug**: 32 connections open at the start of a run and none after; a hand that loses a race at setup parks holding its keepalive connections until the next SYN, which may be the run's end. Predicted: delta **0.75–1.00 with a wide spread** (a mute hand in some pairs), or a refused set on failed requests |
| the gauntlet on ws32-a | **RED at `tools/lobo-prefork` check 1c** ("after 2 s of silence every hand still answers its own control endpoint — a #242 park leaves the losers mute"): the losers are parked in the reactor on the http listener and their control endpoints are not in that park. That check exists because ws18 fixed exactly this |

So (a) is predicted to move nothing on close and to be inadmissible on
its own witness regardless. It is measured anyway because the contract
says each alone, and because "a park until the next SYN costs the same
as a park for 5 ms" is a sentence the count can confirm or deny.

### Candidate (b) — `listen … reuseport`: the kernel-distributed wake

nginx spells this as an opt-in flag on `listen` (off by default; useful
on linux 3.9+ and DragonFly, honored elsewhere without distributing),
so lobo mirrors it: `listen ADDR reuseport;` — nginx's own grammar, a
config that carries. With the flag, at `worker_processes N`:

- the master binds NOTHING for that listener and spawns the hands with
  an empty inherit set (`os_spawn`, `--inherit 0`);
- each hand binds its own `net_listen_with(addr, true, 0)`, arms the
  same 5 ms budget (a member's queue is its own, so the budget is
  never spent), and serves;
- **on `unsupported` (windows) a hand falls back to `net_listen(addr)`
  — ws16's bind-and-stand-by shape: one hand serves, the rest retry
  each pass and take the port when its holder dies — and says so once,
  by name, in its log** (the runtime's refusal is a choice, not a gap,
  and lobo does not re-decide it); on `exists` (a foreign holder
  without the option) the hand stands by the same way;
- at `worker_processes 1` the one process binds a one-member group
  (a socket with a flag; nothing else changes);
- on macOS the flag is honored as nginx honors it, and the delivery is
  the newest member's — documented in `docs/WORKERS.md`, not detected:
  the operator who writes `reuseport` on macOS gets what nginx gives.

The trade the flag makes is nginx's too: a hand that dies takes the
connections queued on ITS socket with it (a shared queue loses none),
and a replacement binds a fresh member. The prefork witness's kill-9
window is therefore "the queue's depth" rather than "a request" in
this shape — reported, not gated.

Predicted, the candidate ÷ trunk on one VM (the tools grow
`LOBO_LISTEN_ARGS` / `LOBO_REF_LISTEN_ARGS` so the candidate's config
carries the flag and the ref's does not; trunk parses the flag and
ignores it, so one config could serve both — the knob is per binary to
keep the two trees' configs honest):

| leg | prediction |
|---|---|
| count, close N=4 | **`accept4` 1.08 → 1.00** (no lost races: one wake, one queue, one hand), **`epoll_ctl` 0.15 → 0.00, `epoll_wait` 0.14 → 0.00, eventfd `write` 0.07 → 0.00** (no hand ever parks, so the `wolf-reactor` thread never starts), `futex` 0.36 → ~0.10 (#302's clock alone, read through the rate), `poll` 1.28 → 1.00–1.15 (a SYN wakes one hand once; the probe after a burst's first accept persists); **total 10.20 → 9.5–9.7 against nginx's 10.13 — under nginx's count on close for the first time** |
| count, keepalive N=4 | unchanged, 6.27 ± 0.05: accepts happen at the start only |
| parity, close N=4 | lobo's cpu a connection 78.9 → **66–72 µs**; delta ws32 ÷ trunk **1.05–1.12x** req/s; nginx ÷ ws32 1.139x → **1.02–1.08x** — above the floor, and the number the sprint takes if it reads so |
| parity, keepalive N=4 | delta **0.95–1.01**: the hash spreads 32 connections unevenly over four members (a shared queue balances by whoever is free), and the busiest hand bounds the run |
| parity, N=1 both shapes | 1.00 ± 0.01 — a one-member group |
| the by-thread profile, close N=4 | `wolf-reactor` **absent** (1.60–1.74% at trunk); the serving thread 99.9% |

If close N=4 reads under 1.02x delta the prediction is wrong and the
herd's cost was not the wasted passes; if keepalive N=4 reads under
0.95x the flag costs more on the read/serve path than it buys on the
accept path and the posture stays opt-in with that number beside it.

### Item 2 — the ~6 µs a request that four hands pay and one does not: the cross-hand instrument, predicted

ws31's one-hand profile at keepalive N=4 found no row over half a point
larger than at N=1, and named the gap "what four hands, four generators
and the softirq path cost each other on four vcpus". `tools/lobo-profile`
grows a sixth argument, `hands` (`1`, the default — worker 1 sampled as
at ws31 — or `all`): with `all`, `perf record -p` takes every hand at
once and the report adds `--sort pid` over the four (each hand's threads
side by side), `--sort cpu` (which vcpus the four hands ran on), and the
same dso/leaf tables over the union; and, from `/proc` with no tracer
at all, a per-hand table for the window — cpu seconds (utime+stime),
write syscalls (`syscw`, one `writev` a request on this shape: the
request count per hand without ptrace), **µs cpu a request per hand**,
and voluntary / involuntary context switches per request. Predicted:

- the four hands' cpu a request are **within ±10% of each other** —
  the ~6 µs is paid by every hand, not by an unlucky one (imbalance
  would show as one hand at 30+ µs beside three at 34 — the shape the
  hash can produce in candidate (b), not the shared queue);
- involuntary switches a request **> 0.2 at four hands** where one hand
  on a quiet vcpu reads ~0: four hands and four generators on four
  vcpus preempt each other mid-request, and the scheduler's rows
  (`finish_task_switch`, `__schedule`, `switch_mm_irqs_off`) plus the
  softirq path (`__do_softirq`, `net_rx_action` charged to whichever
  hand's context the loopback delivery lands in) sum to **~8–12% of the
  union** where the one-hand cell reads ~3%;
- `--sort cpu` shows every hand on every vcpu (no affinity; migrations
  are the `switch_mm` row).

If that reads so, the row has a name — preemption and migration on a
fully subscribed VM, paid per request because a lobo pass at eight
connections a hand is a shorter run between switches than nginx's —
and it is priced, not fixed, this sprint. If the split is uneven, the
row is the shared queue's imbalance and candidate (b)'s keepalive
number is the fix's own measurement.

### Item 3 — wolf-lang#302 at the release pair, one leg

The runtime did not touch the parked proc between fc07cc5 and v0.2.11
(ws31 read the diff); this sprint re-measures the idle count once on
the new pair from THIS branch and predicts **6,200–6,300 `futex` in
8 s over four hands, ~196/s per hand, every one an error return; nginx
0** — ws31 read 6,269. It holds or the reading of the diff was wrong.

### The measurement — candidate (a), the unbudgeted accept (runs 34603229602 count, 34603232342 parity; `ws32-a` @ f4c9c30, never merged)

| leg | predicted | measured |
|---|---|---|
| count, close N=4 | no row moves; `accept4` 1.05–1.10, `poll` 1.2–1.3, `futex` ±0.05 | **`accept4` 1.07** (trunk 1.09), **`poll` 1.27** (1.27), **`futex` 0.32** (0.35), `epoll_wait` 0.07 (0.17), `epoll_ctl` 0.14 (0.18); the eventfd `write`/`read` gone (a loser that never times out never needs the wake) — total 9.93 vs trunk's 10.29 on the same day. **Right: no per-connection row moved**; only the park's LENGTH changed |
| count, IDLE | (not predicted) | **the master's probes answered by ONE hand of four** — `accept4`/`recvfrom`/`sendto`/`close` 4.00/s where four hands answer 16.00/s — and **`futex` 1,373/s** against 784: three hands parked mute in the reactor, each costing its own ~196/s compensation clock (wolf-lang#302, the per-park reading) |
| parity, close N=4 | delta 1.00 [0.98, 1.02] | **1.020x [0.988, 1.029]** — under the floor, as predicted |
| parity, keepalive N=4 | at risk: 0.75–1.00 with a wide spread, or a refused set | **SET REFUSED** (exit 3): pair 4's keepalive run stalled at **0.446x** of trunk with a generator that never finished (`failed=?` — ab reported no rate), the median 0.972x [0.446, 0.988]. A hand lost a race at setup, parked holding its eight keepalive connections, and no SYN came for the rest of the run |
| the gauntlet on ws32-a | RED at `lobo-prefork` check 1c | **RED, exit 1, one step earlier**: the corpus — `prefork_e2e.lu` native hung to the 181 s ceiling, checked trapped at :254 (hand 1's own control endpoint answers nothing after one GET); `control_unix_e2e.lu` the same at :191; both left three processes behind (lobo#1's census named them). The prefork tool never ran |

So (a) is what ws27's correction said it was: an unbudgeted park, the
ws17 shape, inadmissible on lobo's own witnesses on both hosts and
worth nothing on the close count. The candidate the issue meant — a
loser that answers WITHOUT parking — needs wolf-lang#267's try-once
accept, and this measurement is posted there.

### The measurement — candidate (b), `listen … reuseport` (runs 34603182793 count, 34603185051 parity, 34603192228 profile; trunk posture beside it in 34603180650 and 34603189535)

| leg | predicted | measured |
|---|---|---|
| count, close N=4 | `accept4` → 1.00; `epoll_ctl`/`epoll_wait`/eventfd → 0; `futex` → ~0.10; `poll` 1.00–1.15; total 9.5–9.7 | **`accept4` 1.09 → 1.00; `epoll_ctl` 0.18 → 0.00; `epoll_wait` 0.17 → 0.00; eventfd `write` 0.09 → 0 and `read` 1.09 → 1.00; `futex` 0.35 → 0.12; `poll` 1.27 → 1.58**; **total 10.29 → 9.76 against nginx's 10.13** — under nginx's count on close for the first time. Every row as predicted but the probe `poll`, which GREW: a hand's own queue holds one connection per wake, so the zero-deadline probe after a burst's first accept now finds nothing on nearly every burst (0.28 → ~0.58 a connection) |
| count, keepalive N=4 | unchanged, 6.27 ± 0.05 | **6.25** (the same day's trunk 6.23) |
| parity, close N=4 | delta 1.05–1.12x; cpu 66–72 µs; nginx ÷ ws32 1.02–1.08x | **delta ws32 ÷ trunk 1.044x [1.028, 1.053]** req/s — above the floor; cpu a connection **79.6 → 73.3 µs** (nginx 62.1); **nginx ÷ ws32 1.089x [1.085, 1.111] — MET** beside nginx ÷ trunk 1.138x [1.131, 1.160] on the same VM. The shape right, the size at the low edge of the bracket: the probe `poll` that grew is the third of a syscall a connection the flag leaves behind |
| parity, keepalive N=4 | 0.95–1.01 (a hash imbalance over 32 connections) | **1.016x [0.992, 1.018]** — no imbalance cost visible; cpu a request 38.7 → 38.8 µs |
| parity, N=1 | 1.00 ± 0.01 | close **1.013x** [0.999, 1.016]; keepalive 0.974x [0.941, 1.050] — the one-member group is a socket with a flag, and the N=1 cell swings as it always has |
| by thread, close N=4, ALL hands | `wolf-reactor` absent | **absent on every hand** (the four 0.09–0.10% rows are the signal forwarders' carriers); at the trunk posture the same instrument shows **four `wolf-reactor` threads at 0.24–0.37% of the union each** (≈1.0–1.5% of a hand) |
| the hand's strace, close N=4, ALL hands | — | **zero EAGAIN in 53,567 `accept4`** (= 53,567 `recvfrom`), no `epoll_*` rows, `poll` 1.53 a connection; the trunk posture: **2,953 EAGAIN in 43,824 `accept4`** over all four hands = **0.07 lost races a connection** — the count's 1.07–1.09, and the number ws31's one-traced-hand (0.32) could not read |

The set is VALID (load 1.73, the slow class: nginx close 25.4k,
keepalive 86.1k; ab at 0.72 cores; no failed request in thirty runs).
`docs/PARITY.md`'s ledger carries the row.

**Taken, as nginx's opt-in.** The flag moved the N=4 close number by
4.4% on one VM, above the instrument's floor, with the mechanism
confirmed on three instruments (the count, the by-thread profile, the
all-hands strace) and no cost on the read/serve path. It ships as
`listen ADDR reuseport;` — nginx's grammar, nginx's default (off) —
with `docs/WORKERS.md` saying what it buys per host and what it trades
(a dead hand's own queue). lobo's DEFAULT stays the inherited socket,
which is nginx's default too and the shape that distributes on both
serving hosts; so **the bar's own row stays 1.138x NOT MET at the
default and reads 1.089x MET with the flag**, and both numbers are
in the ledger. A set with nginx's OWN `reuseport` beside lobo's is the
like-for-like not taken this sprint.

### The measurement — item 2, the cross-hand split (runs 34603187438 keepalive N=4 ALL hands; 34603189535 close N=4 ALL hands; 34603192228 close N=4 ALL hands with the flag)

`tools/lobo-profile … 4 all` took every hand at once, and the split
drive (no perf, no strace, the hands' own `/proc` counters over an 8 s
window) read:

| cell (req/s in the split window) | µs cpu a `syscw` per hand | spread | voluntary switches a request | **involuntary** switches a request |
|---|---|---|---|---|
| keepalive N=4, trunk posture (80,663) | **31.7 / 31.6 / 32.0 / 31.9** | **1.01x** | 0.024 | **0.346** |
| close N=4, trunk posture (22,656) | 70.5 / 70.5 / 70.7 / 70.7 | 1.00x | 0.282 (the park) | 0.097 |
| close N=4, `reuseport` (33,836) | 49.6 / 49.7 / 49.6 / 49.5 | 1.00x | 0.275 (the pass) | 0.041 |

and the union's leaves at keepalive N=4 (76,760 req/s under perf;
75.7 / 17.3 / 6.6 by dso): **`_raw_spin_unlock_irqrestore` 7.21%**,
`do_syscall_64` 4.34, **`finish_task_switch` 2.80**, `x64_sys_call`
2.66, `do_user_addr_fault` 1.73, `serve_main` 1.47, `srso_alias_safe_ret`
1.38, the `find` family 1.82, `ambient_alloc` 1.09 — against the close
cells' `_raw_spin_unlock_irqrestore` 4.05 / 3.94 and `finish_task_switch`
under 0.54 / 1.77.

Predicted: even within ±10% (**right: 1.01x**); involuntary switches
over 0.2 a request (**right: 0.35** — a hand is preempted every three
requests, where the close shape reads 0.04–0.10); the scheduler's and
softirq's rows at 8–12% of the union (**the switch and wake rows read
~10 points** — `finish_task_switch` 2.8 + `_raw_spin_unlock_irqrestore`
7.2, the wake path's unlock — with the syscall entry/exit another 7;
no `net_rx_action`/`__do_softirq` row over 0.4%, so the loopback
delivery is not charged to the hands' contexts as guessed); every
hand on every vcpu (**not read**: `--sort cpu` printed one row, `-001`
— a `-p` record carries no cpu field without `--sample-cpu`, fixed at
50bf8ce and re-run once, below).

**The re-run (run 34618903224, keepalive N=4 ALL hands, 61,310 req/s
under perf; a slower VM):** `--sort cpu` reads **`002` 28.8% / `003`
25.1% / `000` 24.1% / `001` 22.1%** — every hand on every vcpu, no
affinity, the four within a third of each other; the split again
**39.2 / 39.0 / 39.4 / 39.2 µs a request, spread 1.01x, involuntary
switches 0.374 a request** (0.345–0.402 per hand) — the same shape
on a second VM, and the 39 µs is the parity table's own N=4 keepalive
number (ws31: 39.1) read off `/proc` per hand.

**So the ~6 µs has a name and a shape, and not yet a row lobo owns.**
It is paid EVENLY by every hand (not one unlucky hand, not the shared
queue's imbalance); it is preemption — 0.35 involuntary context
switches a request on a VM where four hands and four generators share
four vcpus, ~10 points of the union in the switch and wake rows, the
rest the cold cache each switch leaves; and nginx's four workers do not
pay it (28 µs at N=4, 29 at N=1) because a worker's run between waits
is ~1 µs of user space where a hand's is ~7 (ws31's row 2–5: lobo's
frames, the runtime's allocations and pages, the searcher-per-`find`,
the wrappers). The exposure to preemption is the length of the run;
the lever is the same user-space rows ws31 priced, and nothing new is
filed for it. Named and partly priced (0.35 switches × ~2–3 µs direct
≈ 1 µs; the cache's share is the remainder), attributed to the
scheduler, not to a row: the next reading is the same split against
a lobo whose request is shorter.

### The measurement — item 3, wolf-lang#302 at the release pair, one leg (run 34603180650, the idle shape)

**`futex` 6,273 in 8 s over four hands, 784.1/s, ~196/s per hand,
every one an error return; nginx 0** — predicted 6,200–6,300 (ws31
read 6,269). Holds. And the probe leg gave the issue a second number
the same day: with three hands parked in an unbudgeted accept the same
instrument read **1,373/s** — (1,373 − 784) ÷ 3 = **196/s per parked
wait** — so the compensation clock is armed once per blocked wait,
not once per process; posted on #302.

### W8 restated at ws32 (linux x86-64, the CI runner, wolf v0.2.11)

| cell | at lobo's default (nginx ÷ trunk, this VM) | with `listen … reuseport` (nginx ÷ ws32) | the count |
|---|---|---|---|
| N=4 close | **1.138x** — NOT MET (79.6 µs vs 62.1) | **1.089x — MET** (73.3 µs) | 10.29 → **9.76** vs 10.13 |
| N=4 keepalive | **1.269x** — NOT MET (38.7 vs 28.7) | 1.257x — NOT MET (38.8) | 6.23 vs 6.13 |
| N=1 close | 0.991x — AT parity (65.1 vs 65.0) | 0.978x (64.2) | — |
| N=1 keepalive | 1.173x (34.0 vs 28.2) | 1.185x (33.0) | — |

The count does not claim the bar; the timing does. What remains: on
close at the default, the shared queue's lost races (wolf-lang#267);
on keepalive, ~5 µs of user space a request at one hand (ws31's rows,
#298/#299/#191/#335 and lobo's own frames, lobo#14) and ~6 µs of
preemption at four that the same rows expose. macOS: ws26's MET stands
as the last valid macOS set; no macOS set this sprint (load 5.3–5.6,
two compiler lanes on the box).

## ws33's addendum — lobo#14: the route's per-request config scan, indexed once at load, PREDICTED before either leg (2026-09-11)

### What ws31 priced, and what it is

`serve.handle_request` called `proxy.plan(c, norm)` on EVERY request
(`serve.lu:1955`, the dry-run mirror at :2304), and `http.route` ran
`match_location` beside it. Between them a **static** request — a
config with no `proxy_pass` in it at all — paid these whole-arena
walks of `c.names`, ws31's self shares on one hand under
`keepalive 1` (run 34599274095):

| leaf (self) | share of the hand's cpu | what it walked |
|---|---|---|
| `proxy.first_http` | 0.31% | every row, for the first `http` block |
| `proxy.plan` | 0.28% | every row, for `location` blocks under the server |
| `http.child_arg1` | 0.23% | every row, per `alias`/`root` lookup (three a request) |
| `proxy.first_server` | 0.15% | every row, for the first `server` under http |

plus `http.match_location`'s own location walk and two `index_list`
walks, both under ws31's 0.1% print cut. **~0.6–1.0% of a 34.2 µs
keepalive request**, spent learning that nothing proxies the path.

### The shape taken — an index in the `Conf`, not a per-path memo

The issue proposed a memo keyed `(configuration generation,
normalized path)`. This lane took the other half of the same idea and
it is strictly smaller: the config model is **immutable after parse**
(`config/parse.lu`'s header states it, and a `-s reload` builds a NEW
`Conf` and swaps), so a table derived at the end of the load and
carried BY the `Conf` needs no generation key, no invalidation and no
staleness witness — **it IS the generation**. `build_index` runs once
per load, O(rows), and adds to `Conf`:

- `ix_http` / `ix_server` — the two first-block rows, now field reads;
- `loc_row` / `loc_mod` / `loc_prefix` — the `location` blocks under
  the first server, **in row order**, with the modifier and prefix the
  matcher reads. Longest-prefix, `=`-exact-wins, `^~`, first-match on
  a tie: all unchanged, because the candidate list is the same rows in
  the same order;
- `kids` / `kid_at` / `kid_n` — every row's DIRECT children in row
  order, counting-sorted into buckets keyed `parent + 1` (bucket 0 is
  the top level). `child_row` / `child_arg1` / `index_list` walk a
  block's own children instead of the arena, and the first match in
  that window is the first match the arena scan returned.

`proxy` and `http` stopped carrying private copies of the four
scanners; both now read `config`'s. `config/logconf.lu`'s third copy
of `first_server` went with them.

**The witness that nothing routes differently** is
`tests/config/route_index.lu`: it carries the pre-index scanners
verbatim as `ref_*` and asserts the index agrees with them — on the
location table (rows, order, modifier, prefix), on `child_row` /
`child_arg1` over every block × a twelve-name battery plus the top
level and two out-of-range keys, and on the child buckets
partitioning the rows — across seven configs (no http; a lexer error;
four prefix shapes with a nested location; two servers; the three
proxy inheritance levels; top-level directives; and two generations
alive at once, each answering under its own table). All three lanes.

### The prediction (written 2026-09-11, before either leg ran)

| leg | predicted |
|---|---|
| profile, keepalive N=1, leaves in `lobo-release` over 0.1% | `proxy.first_http`, `proxy.first_server` **gone** (the functions no longer exist); `http.child_arg1` under 0.05%; `proxy.plan` 0.03–0.10% (it still scans the location table — one to four entries); the four rows' **0.6–1.0% sum falls under 0.15%**; no new row over 0.05% (the index build is once a load, off the request path) |
| parity, N=4 and N=1, both shapes | **NOT VISIBLE.** ~1% of 34.2 µs is ~0.3 µs; ws30's no-op read 1.005x [0.998, 1.006]. Predict **ws33 ÷ trunk 1.00 [0.98, 1.02]** on every cell — indistinguishable from a no-op. Saying so is the finding; the count does not claim the bar |
| the gauntlet | GREEN — zero behaviour motion, and `route_index.lu` is why |

### The measurement — the profile leg, two trees on ONE VM (run 34631696981, keepalive N=1, one hand, `profile_shape=keepalive profile_n=1 ref_tree=8fa95fd`)

`ws33` = `b6f29f2`, `trunk` = `8fa95fd`, built beside it with the same
staged toolchain, profiled back to back on the same runner: ws33
36,591 req/s under perf (load 2.70), trunk 35,889 (load 1.96), 4 ×
`ab -k -c 8` over an 8 s window, no failed request. Leaves in
`lobo-release` over 0.1%, **within this one run**:

| row | trunk | ws33 | predicted |
|---|---|---|---|
| `proxy.first_http` | **0.26%** | **gone** (the function no longer exists) | gone |
| `http.child_arg1` | **0.23%** | **gone** (under the 0.1% cut) | < 0.05% |
| `http.first_server` | **0.14%** | **gone** | gone |
| `http.index_list` | **0.13%** | **gone** (under the cut) | (implied) |
| `proxy.plan` | under the 0.1% cut | **0.13%** | 0.03–0.10% |
| `config.child_row` | — | **0.18%** | "no new row over 0.05%" |
| **the route's named rows, summed** | **0.76%** | **0.31%** | **under 0.15%** |
| by dso: `lobo-release` | 14.90% | **14.69%** | — |
| by dso: kernel / libc | 79.34 / 5.40 | 79.40 / 5.36 | — |

**Right on the shape, optimistic on the size.** All four whole-arena
scanners are gone as functions — that half was exact. What was
predicted at "under 0.15%" measured **0.31%**, so the change recovered
**0.45 points of the hand's cpu** out of the 0.6–1.0% ws31 priced,
about three fifths of it, not the four fifths predicted. The residue
has two named parts and neither is a scan any more:

- `config.child_row` 0.18% — still called FIVE times a static request
  (`http.decide` asks for `alias`, then `root` at the location and at
  the server; `proxy.plan` asks for `proxy_pass`; and `index_list`
  walks two buckets). Each call is now a bucket walk of two or three
  children instead of the whole arena, but it is still five calls with
  their own string compares. The next lever here is not a faster
  lookup, it is asking fewer times — the static decision could read
  one resolved row per location, built at load like the rest.
- `proxy.plan` 0.13% — the location table it walks is EMPTY on this
  config, so what is left is the `Plan` struct literal it builds per
  request (twelve fields, a nested `PassTarget`) BEFORE it learns
  there is nothing to proxy. Hoisting the early return above the
  literal is the obvious follow-up and was not taken here.

The dso column moved 14.90 → 14.69, a fifth of a point, which is less
than the named rows moved: run-to-run noise inside an 8 s window is
larger than the effect (`TwoWaySearcher` alone reads 0.74% on trunk
and 1.25% on ws33 in these same two windows). The per-function rows
are the reading; the dso total is not.

**The count: nothing moved, as predicted.** `strace -c` on the hand,
per request, ws33 vs trunk: `writev` 1.000 / 1.000, `openat` 1.000 /
1.000, `recvfrom` 1.000 / 1.000, `read` 1.000 / 1.000, `statx` 1.000 /
1.000, `close` 1.001 / 1.000, `poll` 0.033 / 0.031, `futex` 0.068 /
0.068. A pure user-space change has no syscall to show, and it shows
none.

### The measurement — the parity leg (run 34631705651, VALID)

**NOT VISIBLE, exactly as predicted.** ws33 ÷ trunk **0.990x**
[0.988, 1.001] on N=4 close, **0.990x** [0.976, 1.013] on N=4
keepalive, **0.992x** [0.980, 0.992] and **0.983x** [0.955, 1.081] on
the N=1 cells — every median inside the predicted [0.98, 1.02], every
bracket containing or abutting 1.00, and every median just BELOW one,
which is the opposite sign to the 0.45 points the profile measured.
0.45% of a hand's cpu is ~0.15 µs of a 34 µs request; ws30's no-op
read 1.005x [0.998, 1.006] and this instrument cannot do better.
The set is on the FAST class (nginx close 53.0k, keepalive 168.8k, load
1.81), so its nginx ÷ lobo ratios (1.197x / 1.263x) are not comparable
with ws31's or ws32's slow-class rows; `docs/PARITY.md` carries the
whole table. **The count does not claim the bar, and neither does this
row: the profile can see this change and the bar cannot, and that is
the answer the leg was run to get.**

### W8 restated at ws33 (linux x86-64, the CI runner, wolf v0.2.11)

The bar's own numbers did not move this sprint and this lane did not
touch them; B1's ruling (`docs/PARITY.md`, "The bar's configuration")
settles which row gates — the DEFAULT on both sides, with the flagged
number reported beside it:

| cell | at lobo's default (ws32's slow-class VM) | with `listen … reuseport` (ws32) |
|---|---|---|
| N=4 close | **1.138x** — NOT MET | **1.089x — MET**, reported beside it |
| N=4 keepalive | **1.269x** — NOT MET | 1.257x — NOT MET |

What remains on the keepalive shape after this lane: ~5 µs of user
space a request at one hand (ws31's rows, #298/#299/#191/#335), ~6 µs
of preemption at four (ws32's split), and of lobo#14's own ~0.3 µs
this lane took ~0.2 — the two residues named above are the rest.

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
