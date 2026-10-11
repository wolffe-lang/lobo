# ws59 — the parse

Wave 53, lane ws59 (Opus). Written 2026-10-11 on lobo trunk `bea04ee`,
after the profile of record at trunk was taken (item 1 measures and
changes nothing) and before any edit to `src/`, `tools/` or `tests/`.
The planning contract is `sprints/wws/28-the-parse/ws59-the-parse.md`
in `wolffe-lang/wolf`; rules are `sprints/wave-53.md` down to
`wave-45.md`. The oracle is the pinned nginx 1.30.4 (ws47's copy,
`65595ac2…`), run, never read.

One deliverable: lobo's user instructions per static keepalive request
brought from 18,070 toward nginx's 13,599 by the bounded levers lobo#68
names (parsing, the loop's bookkeeping, head and route), each lever
measured alone, with parity at four hands no worse on any row than
ws58's; and lobo#72's second cause found or bounded.

## 1. Forbidden, absolutely

- nginx behaviour only from the pinned oracle; never read nginx's, any
  other server's, GNU's, glibc's, musl's or a kernel's source.
- The toolchain is the pin, staged from the release archives by digest:
  never a clone, Homebrew or `~/.local/bin`; never a build of wolf-lang
  trunk.
- No `rm` outside `~/lanes/ws59/` (nomad-1 and kasumi) and this lane's
  own clones, `/tmp` included; no scratch in `/tmp`. No `git add -A`.
  Nothing under `~/.claude`. No package installs. No merge, tag or
  release; close no issue. No commit trailers or PR attribution of any
  kind. Checksums carry a trailing `…`. No "seen red" without a run
  id, sha, path or digest.
- Strict evidence (wolf-lang#571): `WOLF_PAIRING_REQUIRE_SIBLING=1`,
  stdout and stderr together, every SKIP line counted; a `wolf build`
  that exits 2 is a compile error, never a skip; spawning, signal and
  concurrency rows also under `taskset -c 0-3`.
- No correctness trade for speed: every parser change keeps the
  differential corpus and the fuzz rows green, and a request lobo
  refused before is still refused, with the same status.
- The three open soundness shapes (wolf-lang#660, #665, #678): no new
  `spawn proc`, no channel send, nothing moved across a region block.
- kasumi: remote commands in `bash -c`, `setsid` with a pid file, kill
  by recorded pid only, outputs pruned; `strace` and `perf` start the
  server, they do not attach. No build on nomad-1. At most two CI runs
  of this lane at once; never cancel another lane's.
- Never touch the maintainer's Cloudflare tunnels, `~/.cloudflared`,
  DNS, ports 8080 or 8088, or hasu's `~/models`, `~/.local`,
  `~/pool-serve`, the :9308 server. This lane's ports are 18630–18659
  and kernel-chosen ones. The live site is not this lane's to redeploy.
- No parity figure without the host's load beside it; the runner VMs
  give the numbers of record.

## 2. Inputs, verified (re-derived 2026-10-11)

| input | what was found |
|---|---|
| lobo trunk | `origin/trunk` = `bea04ee` (ws58): pins [wolf] 0.2.27 `0ddda6b`, [lupin] 0.1.50 `32b970d`, [std] `14f0ab2c` |
| the archives | from the release API: wolf 0.2.27 linux x86-64 `5e17eebe…`, lupin 0.1.50 linux x86-64 `e2867a35…`; both match on kasumi (`dl/digest-check.txt`); members `wolf` 6f5713a2…, `libwolf_rt.a` ab575b27…, `lupin` 3a476442… (`toolchain-tc-0227.txt`), the same as ws58 staged |
| the trunk build | release `2c3729e9…`, the digest ws58 measured its head at; debug 73000367… (`build-trunk.log`) |
| instructions a request | keepalive, one process: lobo **18,046** (18,037–18,060 over three), nginx **13,598**; four hands 19,832 against 13,675; close 18,149 against 14,319 at one process and 20,405 against 14,418 at four (`prof-trunk.log` 55b518a9…, `prof-nginx.log` 7b4dea02…; kasumi at load 2–3). ws58's 18,070 and 13,599 reproduce |
| syscalls a request | keepalive 3.04 (statx, recvfrom, writev), close 6.08; nginx 6.03 and 10.00 (`sys-trunk.log` 95e1f255…, `sys-nginx.log` 6b909f96…) |
| where they are (keepalive, one process, `cg-trunk-keepalive-1.log` c34b584a…) | `str_find` 14.2 % inclusive (12.7 self); `http.parse_request` 30.5 % inclusive (6.3 self; `split_lines_strict` 8.2, `lower_token` 3.1, `ci_contains` 2.9, `is_tchar` 2.4, `eq_fold` 1.0, `trim_ows` 0.9); `head_cut` 10.3 % inclusive, all of it two `str_find` calls; `memo_look` 12.9 % inclusive, of which `fs_stat` 10.0 (wolf-lang#690); `serve_main` self 6.0; list building 10 % (`push_int` 5.6, `list_new` 4.5); the clock 2.6; `head_warm_at` 2.9; `http.decide` 2.9; `net_deadline` 1.2 |
| wolf-lang#654 | **open, not fixed at 0.2.27**: the profile still shows `str_find` as `Iter<u8>::position`, a byte loop |
| wolf-lang#690 | open; `fs_stat` is measured around, not fixed here |
| `bytes_find`, `bytes_count` | in 0.2.27 (`[mem.list.bytes]`): a `List[byte]`, one byte, a start index; SSE2 on x86-64; lupin 0.1.50 has both. A request arrives as `net_read_bytes`' list before it is a string (`conn.sock_read`), so the scan can run on what the socket gave |
| lobo#68, lobo#72 | open, as ws56 and ws58 filed them. #72's one capture (`kasumi:~/lanes/ws58/dbg-wt-gpin.log`) is the server asleep with its listeners and self-pipes and the test in its `status` retry: forty tries of two seconds each explain the client's side, so the question is the server's |
| the idle server | ws58's figure (about 1,100 syscalls a second across four hands, futex 900, madvise 160) is to be re-measured under `strace -f -c` from the start, not by attach |

## 3. Prediction, committed before the first change

Instructions are user instructions a request, keepalive, one process,
the parity file; the base is 18,046.

| lever | what changes | saved a request | the parity row it moves |
|---|---|---|---|
| A. the head cut | the blank line is found by `bytes_find` over the bytes the read returned, not by two `str_find` passes over the string | 1,000–1,500 | keepalive at every N |
| B. the line split | the scan that finds the blank line records each line end and proves the CRLF discipline; `split_lines_strict`'s byte loop and its list of slices are not run on that path | 900–1,300 | the same |
| C. the fields | the request line and each header field are read in one pass each (no `find` for the spaces, the `?` or the colon; the name's fold and its token test in the same walk; `Connection` by whole-value compare before the general scan) | 1,200–2,200 | the same |
| D. the loop's bookkeeping | a step's clock reads and deadline arms folded (one clock a step; the 12 ms poll arm dropped where the wait already named the socket), fewer lists built a step | 400–1,000 | keepalive; close a little |
| E. head and route | the head memo's compare and the route's string work for a path already seen | 300–900 | keepalive |
| all five | | **3,800–6,900**: 11,100–14,200 a request, nginx's 13,599 inside the band | |

`fs_stat` stays about 1,700 (wolf-lang#690). A lever that saves under
1 % (180 instructions) is reverted and listed.

**Parity** (this lane's ratio as ws58 wrote it, nginx ÷ lobo by CPU
per request, lower is better; ws58's rows are the floor to hold). User
time is about a third of lobo's CPU time on keepalive, so a quarter to
a third fewer instructions is 8–12 % of the request:

| cell | ws58, runner VMs | predicted, runner VMs |
|---|---|---|
| keepalive N=4 | 0.914–0.934x | 0.85–0.91x |
| keepalive N=1 | 0.81–0.90x | 0.75–0.86x |
| close N=4 | 1.022–1.038x | 1.00–1.04x |
| close N=1 | 0.70–0.82x | 0.68–0.82x |

kasumi's rows move the same way and are read with their load. No row
is worse than ws58's beyond the VMs' own spread; syscalls a request
stay 3.04 and 6.08; the memory gate keeps 23/23.

**lobo#72.** The client's side is explained without a second bug: the
test's `status` loop is forty tries of a two-second deadline, so a
server that does not answer keeps the test past any ceiling. The
server is the question. I expect the cause in this order:

1. (55 %) the loop's thread parked inside the runtime, in a call lobo
   bounds with a deadline that is not honoured under load (a `net_wait`
   or a read whose budget is lost): a runtime defect, to be filed with
   a wolf-only witness;
2. (30 %) lobo's own loop: a call that can block with no budget on the
   pass after the last row closes (the control listener's accept has
   no budget armed where the http listener's has 5 ms);
3. (15 %) the test or its rig (the port chosen, the server reaped).

How it is caught: the test looped under `taskset -c 0-3` with busy
loops of this lane's own on the same four cpus; when a round passes
its time, an ancestor of the server (yama allows nothing else) reads
every server thread's blocked syscall from `/proc/<pid>/task/*/syscall`
and takes a `gdb` backtrace of every thread, and `ss` lists both ends
of the control port. If it does not reproduce in 300 rounds, the
table of what was ruled out and the harness are the deliverable.

**The idle syscalls.** I expect the futex calls to be the runtime's
(its pool's workers waking on a timer) and the madvise calls to be the
allocator returning a pass's region; lobo's share, if any, is a wait
shorter than it need be (the stream pipe's 50 ms budget, the 250 ms
pass). Fixed if lobo's; filed if the runtime's.
