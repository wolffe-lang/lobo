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

MEASURED-PENDING — the count leg runs on the CI runner (`tools/
lobo-syscalls` is linux's; strace is the counter, and the tool skips
by name on macOS). This section is written before the run, as ws27's
and ws28's were.

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
