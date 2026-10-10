# ws56 — the open two, and the gap after s222

Wave 53, lane ws56 (Opus). Written 2026-10-10 (18:20–18:50Z) on lobo
trunk `ebace85`, after both issues were reproduced there and before any
edit to `src/`, `tools/` or `tests/`. The planning contract is
`sprints/wws/25-the-open-two/ws56-the-open-two.md` in
`wolffe-lang/wolf`; rules are `sprints/wave-53.md` down to
`wave-45.md`. The oracle is the pinned nginx 1.30.4 (ws47's copy,
`65595ac2…`), run, never read.

## 1. Forbidden, absolutely

- nginx behaviour only from the pinned oracle (ws47's copy, copied to
  `kasumi:~/lanes/ws56/nginx-oracle`, digest checked); never read
  nginx's, any other server's, GNU's, glibc's, musl's or a kernel's
  source. Where this note explains a kernel behaviour it says
  "inferred" and names the measurement it rests on.
- No certificate request against a production ACME endpoint: the
  loopback rig CA (`tests/rig/acmeca`) and a listener that never
  answers, nothing else.
- lobo's trunk and this branch stay pinned to wolf 0.2.26 / lupin
  0.1.49. The profile against wolf-lang trunk (`76436101`) is taken in
  `kasumi:~/lanes/ws56/` with a toolchain built there from source; no
  pin change is committed to any branch pushed to lobo's origin.
- Never touch the maintainer's Cloudflare tunnels, `~/.cloudflared`,
  DNS, ports 8080 or 8088, or hasu's `~/models`, `~/.local`,
  `~/pool-serve`, the :9308 server. This lane's ports are 18560–18599
  and kernel-chosen ones.
- No `rm` outside `~/lanes/ws56/` (nomad-1 and kasumi) and this lane's
  own clones. No `git add -A`. Nothing under `~/.claude`. No package
  installs, no sudo. No merge, tag or release; close no issue. No
  commit trailers or PR attribution of any kind. Checksums carry a
  trailing `…`. No "seen red" without a run id, sha, path or digest.
- Strict evidence (wolf-lang#571): gauntlets with
  `WOLF_PAIRING_REQUIRE_SIBLING=1`, lupin present, stdout and stderr
  together, every SKIP line counted; process-spawning witnesses also
  under `taskset -c 0-3`; SigBlk/SigIgn recorded beside every run. A
  `wolf build` that exits 2 is a compile error, never a skip.
- kasumi: `ssh kasumi "bash -c '( setsid nohup … & echo $! > pid )'"`,
  done-files, kill by recorded pid only, `CARGO_INCREMENTAL=0`, one
  target dir, pruned at the close. Waits print at least every five
  minutes; `gh run view`, never `gh run watch` without
  `--interval 60`; cancel only this lane's own superseded runs.

## 2. Inputs, verified (re-derived 2026-10-10, 18:20–18:35Z)

| input, as the contract states it | what was found |
|---|---|
| lobo trunk `ebace85` or later, on wolf 0.2.26 | **holds**: `origin/trunk` = `ebace85460a8…`; `wolf-toolchain.toml` [wolf] `89dc1394` (0.2.26), [lupin] `f516a5f4` (0.1.49), [std] `14f0ab2c`. Two lobo issues open (#62, #65), no PR open |
| the toolchain | the 0.2.26 and 0.1.49 linux x86-64 archives match the pinned digests (`05acdc5e…`, `84911a35…`; `kasumi:~/lanes/ws56/dl/digest-check.txt`); members `wolf` 272e0888…, `libwolf_rt.a` 679d77e1…, `lupin` 6d057eb1… as ws55 recorded. Trunk built there: debug 6a7ebe4e…, release d2d78003… (`build-trunk.log`) |
| the oracle | `65595ac2…`, nginx/1.30.4 (`nginx.sha256`) |
| lobo#62: a streamed response is aborted ~25 s after a 2 s `worker_shutdown_timeout`; nginx 2 s | **reproduced** at `ebace85` (release d2d78003…, `taskset -c 0-3`, `kasumi:~/lanes/ws56/sab-trunk.log`): `generation-retired gen=1 drained=0 aborted=1 age-ms=26796`; the oracle's old worker is gone 2.15 s after the reload ("gracefully shutting down" 14:27:27, "exiting" 14:27:29). One second into the download `ss -tm` reads the connection's send buffer as `tb2626560` with `w2609344` queued |
| lobo#65: each ACME transaction blocks the serve loop up to its deadline | **reproduced** at `ebace85` (`acw-trunk.log`): `cert auto` against a CA that takes the dial and never answers; ten GETs of a static page half a second apart from the moment lobo announces its port: **5006 ms** and **5002 ms** for the two that met a transaction (the first attempt, and the retry after the 2 s backoff), 0 ms for the other eight |
| ws54's parity profile | `docs/PROFILE.md` (ws54) and the ws54 index entry: on keepalive at 4 workers lobo's user space (~3.5 µs a request) is the whole gap; the close shape costs 2.78 more syscalls a connection than nginx |
| s222's figures | `sprints/wave-53.md` (2026-10-10): lobo −12.0 % / −12.8 % user instructions a request; runner nginx÷lobo keepalive 1.266x → **1.203x**, close 1.159x → **1.145x**; bar 1.10 not met. On kasumi (`~/lanes/s222/st-f3.log`, N=1, `taskset -c 0-3`): 17,179 instructions:u a request on keepalive (19,532 before), 18,182 on close (20,847 before) |
| wolf-lang trunk | `764361017d07…` (s218's merge), which contains s222 (`d6372f5e`); built on kasumi as `tc-trunk` (`bt-trunk.log`) |

## 3. Prediction, committed before the first change

**P1, lobo#62 — the cause.** The stream proc's `net_write_bytes` is
parked with no budget when the timeout arrives, and the 1 ms budget
the loop arms on the socket rules only a call that BEGINS after it
(`[os.net.io]`: every park goes against the budget computed when the
call began). So the abort waits for the parked write to be woken, and
that is the kernel's decision, not lobo's: inferred from the
measurement above (not from any source), the kernel reports a socket
writable again only once a fixed share of its send buffer has
drained, about a third. A third of 2,626,560 bytes at curl's 32 KB/s
is 26.7 s; the measurement is 26.8 s. docs/DRAIN.md's "stops within
one 64 KiB chunk" is therefore wrong by the size of the buffer, not
by a constant. **A check of the cause, predicted before it is run:**
the same witness with the reader at 64 KB/s aborts after about
**13–14 s**, and at 16 KB/s after about 53 s.

**P1, the fix's shape.** Nothing but a kill reaches a parked net wait
(the runtime's net park is kill-only; a cancel keeps waiting), so the
loop must hold the stream's proc handle. `List[Proc[int]]` does not
compile at this pin ("cannot compile this yet — this prelude
container instantiation"), a struct with a `Proc[int]` field in a
list does, and a kill through it ends a proc parked in a net wait in
5 ms on both tiers (probe `kasumi:~/lanes/ws56/probe/d-p4`). So:
serve hands the open file back instead of spawning; the LOOP spawns
the stream and keeps `(sock, id, file, proc)` in a slot; the stream no
longer closes the file (a killed proc runs no defer and no further
code, `[conc.proc.kill]`, so the loop must own it); the stream's line
carries its id so a late line can never be read as another
connection's on a reused descriptor; at the timeout the loop kills
and joins the proc, closes the socket and the file, and retires the
row as aborted. The 1 ms budget goes away.

**P1, what moves.** With `worker_shutdown_timeout 2s` the streamed
download is aborted **2.0–2.5 s** after the reload (`age-ms` in
[2000, 2500]; tolerance stated in docs/DRAIN.md as the timeout plus
one loop pass, under 500 ms), where trunk reads 26.8 s and nginx
2.15 s. `tools/lobo-control-differential` gains **row 8** (the abort
of a streamed response, nginx and lobo side by side, both inside
[2 s, 3 s]), red at trunk and green after. Rows 1–7 hold. The stream
cap's witness (`tests/serve/stream_cap_e2e.lu`) keeps its rooms 4 /
10 / 46: still one proc a stream. membudget's retention stays 19–20
KB a request (the slots are bounded by the streams in flight and
reused). The same row holds on macOS (kill reaches the kqueue park
too); if it does not, that is a finding.

**P2, lobo#65 — the cause.** `acme.tick` runs in the serve loop and
its `step` makes blocking loopback transactions (`http_txn` 5 s,
`tls_txn` 15 s); while one waits on the CA nothing else in the
process runs. The rig's coexistence race is the same fact seen from
the CA: the CA validates by dialling lobo back while lobo sits in the
authz poll.

**P2, the fix's shape.** The renewal daemon moves into ONE proc
beside the loop, which owns the `Flow` for the life of the process:
it sleeps until the flow's next due time, ticks, and writes one line
per event (`acme issued`, `acme failed <why>`) down the loop's stream
pipe, whose read end is already in the wait set. The loop's step 3b
becomes "act on an ACME line": the same SslConf swap and the same
LOUD error line as today. A host that refuses the pipe keeps the
in-loop tick (said out loud at start, as the stream's fallback is).
The 800 ms authz-poll wait stays (it is still the polite interval),
but it no longer guards a deadlock: lobo answers the CA's dial-back
while its own poll is in flight.

**P2, what moves.** A static GET sent while a transaction is wedged
answers in **under 250 ms** (5006 ms at trunk); the gate's stated
bound is 1000 ms. `-s stop` during a wedged transaction answers
inside the control client's 2 s (at trunk it can wait out the
transaction). `tools/lobo-acme` gains a **wedged-CA case** (a CA that
takes the dial and never answers: every one of ten GETs under the
bound, the failure still LOUD), red at trunk and green after; its
four existing cases stay green, the coexistence case under
`taskset -c 0`, `0-3` and all cores and on macOS in CI.
`tests/acme/tick_clock.lu` holds unchanged (`tick` keeps its
contract). The daemon is one more parked proc: with `cert auto` on,
the pool's limit `4·max(cpus, 2) - 2` still exceeds the stream room
`3·max(cpus, 2) - 2` by at least 2, so the room does not move.

**P3, the profile on wolf-lang trunk** (kasumi, `taskset -c 0-3`,
4 × `ab -c 8`, the parity file; instructions are the load-proof
number). Predicted before the trunk-built lobo is measured:

- lobo's user instructions a request at N=1: **17.0–17.4 k** on
  keepalive and **18.0–18.4 k** on close (s222's 17,179 and 18,182;
  s218–s225 changed no code on this path). nginx, never measured this
  way by an earlier lane: **under 8 k** on keepalive.
- Syscalls a request on keepalive are within one of nginx's (the gap
  there is user space); on close lobo still spends **2–3 more a
  connection** (ws54's 2.78), which I expect to be the wait set's
  registration of each new socket and the per-connection setup calls
  rather than the accept or the close.
- Where lobo's remaining user cycles sit on keepalive, three
  candidates with the share I expect of lobo's own user time:
  **(a) request parsing** (`http.parse_request` and what it calls:
  `str_find`, `split_lines_strict`, `ci_contains`, `lower_token`,
  `eq_fold`, `is_tchar`) **about 25 %**; **(b) the file a request
  opens, stats, reads and closes** (`serve.serve_file` inclusive,
  with the runtime's fs calls and the body's list) **about 25 %**;
  **(c) the loop's own per-pass bookkeeping** (`serve_main` self, the
  row lists rebuilt every pass, the wait set, the clock reads, the
  per-step `net_deadline`) **about 15 %**. The head (`head_warm`,
  `head_cut`) is a fourth at about 10 %.
- The upper bounds: nginx÷lobo if a lever's cost were zero is the
  measured ratio times (1 − the lever's share of lobo's whole CPU time
  a request, kernel included). User space is a minority of that time,
  so I predict **no single user-space lever crosses 1.10 on
  keepalive**: (a) and (b) each bound at about 1.15–1.17 from 1.203,
  (c) at about 1.18; (a) and (b) together reach about 1.12. The close
  shape (1.145) needs only 3.9 % of a request's time and is the one a
  single lever can cross: the extra syscalls.
- So the recommendation I expect to write: ws57 takes the file path
  (b) with the close shape's extra syscalls, and parsing after it.
  Falsified if one function family holds 40 % or more of lobo's user
  time, or if kernel time, not user time, is the keepalive gap.

**P4, CI.** Both gauntlet jobs green at the head. Each witness is
pushed BEFORE its fix, so trunk's code is red in CI at that sha by
run id (linux and macOS), and green at the fix.

### §3 against the measurement (written at the close, 2026-10-10)

- **P1, the cause: held.** The check predicted before it was run: a
  64 KB/s reader is aborted after 13.8 s (`age-ms=13771`,
  `sab-trunk64.log`; predicted 13–14), where 32 KB/s read 26.8 s. The
  16 KB/s run was not aborted inside the witness's 40 s window
  (predicted 53 s; not measured to its end). A client that reads
  nothing is never aborted at trunk (`stream_abort_e2e.lu` waits 8 s).
- **P1, the fix's shape: held as written.** `StreamSlot` in
  `budget.lu`; serve hands the file back; the loop spawns, kills,
  joins and closes. One thing the prediction did not name: a
  generation already past its timeout when a step hands a stream back
  starts none (the head is on the wire, the row closes as aborted).
- **P1, what moves: held.** `age-ms=2005`/`2006` (release), `2008`
  (debug) with the 32 KB/s reader (`sab-head.log`, `sab-h2.log` at
  `45b7052`); 2030 and 2070 ms for the client that reads nothing
  (`stream_abort_e2e.lu`, printed). Row 8 red at trunk's code and
  green after; rows 1–7 hold (20/20). Stream cap rooms unchanged
  (`tests/serve/stream_cap_e2e.lu` green under `taskset -c 0`, `0-3`
  and all cores). membudget 20 / 20 KB a request, 17/17. macOS: the
  corpus witness is green there (run 38077177455); row 8 was red on
  macOS in that run for a reason of the row's own, not lobo's — it
  timed the oracle by counting 0.1 s sleeps, which read 1.3 s for 2 s
  on that runner — and is green with the rig's clock (`45b7052`, run
  38078339632).
- **P2: held.** Under 10 ms for every GET (0 ms by curl's clock)
  against 5006 ms; `status` in 1–6 ms; `stop` in 1–7 ms (it was not
  slow at trunk either unless it met a transaction). The wedged-CA
  case red at trunk's code (5006 ms on kasumi, 5005 ms in CI) and
  green after; the four older cases green under three cpusets;
  `tick_clock.lu` unchanged and green. Not predicted: `spawn proc
  acme.daemon(…)` does not compile from another module ("a dotted
  proc path"), so the module carries `daemon_start` (wolf-lang#655);
  and the daemon is counted in the stream room rather than argued out
  of it.
- **P3: the instruments held, the explanation did not.**
  - lobo on wolf trunk: 16,990 instructions on keepalive (predicted
    17.0–17.4 k: ten under the band) and 17,912 on close (predicted
    18.0–18.4 k: under it). nginx: **13,605, not "under 8 k" —
    falsified.**
  - Calls on keepalive within one of nginx's: held (6.06 / 6.04).
    "2–3 more a connection on close": **falsified** — 9.14 against
    10.00 at one process, 10.11 against 10.13 at four.
  - Shares of user time: parsing 21.2 % (predicted 25), the file
    27.6 % for `serve_file` inclusive (predicted 25), bookkeeping up
    to 19.5 % (predicted 15), head 12.5 % (predicted 10).
  - "No single user-space lever crosses 1.10 on keepalive": held.
  - **"Falsified if kernel time, not user time, is the keepalive
    gap": FALSIFIED, and this is the lane's finding.** 0.90 of the
    1.23 µs at four hands is system time, with equal calls. The cause
    is memory: 0.5 to 3.0 minor faults a request from 2 to 12 KB a
    request that is never returned (nginx: none), shown by an ablation
    with no code change (malloc's heap on huge pages): 1.192x → 1.118x
    keepalive, 1.138x → 1.081x close at four hands.
  - The recommendation I expected to write (the file path with the
    close shape's extra calls, parsing after) is not the one written:
    the extra calls do not exist, and the memory is first.
- **P4: held.** Run 38077091798 (`6f4920c`, the witnesses on trunk's
  code): red at the corpus on `stream_abort_e2e.lu`, linux and macOS.
  Run 38077177455 (`edc2a16`, lobo#62 fixed, lobo#65 not): the corpus
  and row 8 green on linux, red at the acme rig's wedged-CA case.
  Run 38078339632 (`45b7052`): green on both.

Corrections to §2: none of the inputs drifted. To §1: nothing touched
outside `~/lanes/ws56/` on either box; the trunk toolchain was never
pinned on a pushed branch, so the runner's parity was not re-taken
(the brief forbids the pin on origin) and kasumi's set was refused by
the tool for load.

## 4. Evidence index

kasumi paths are under `~/lanes/ws56/`.

| claim | artifact |
|---|---|
| the archives by digest, the oracle | `dl/digest-check.txt` 43c51a48…, `toolchain-tc-0226.txt` 6efcfbdc…, `nginx.sha256` ce8daa6e… |
| the prediction before the first change | commit `3556503` |
| lobo#62 at trunk: 26.8 s, nginx 2.15 s; 13.8 s at 64 KB/s | `sab-trunk.log` 93a8413b…, `sab-trunk64.log` 97ee9256… (release d2d78003…, `build-trunk.log` 74f58b35…) |
| lobo#62 red on trunk's code | CI run **38077091798** at `6f4920c` (corpus, both jobs); `corp-red-corp.log` 84aea7dd…, `rig-red-ctl.log` 21676a35… (row 8: nginx 2.1 s, lobo none in 10 s) |
| lobo#62 green | `31614a8` onward; `sab-h2.log` 54761240… (`age-ms=2006`, nginx 2.11 s) and `rig-ctl2-03.log` 98c6309a… (20/20; row 8 nginx 2111 ms, lobo 2002) at `45b7052`; CI run 38077177455 (linux row 8: nginx 2.1 s, lobo `age-ms=2249`) |
| lobo#65 at trunk: 5006 ms | `acw-trunk.log` 1b951e4a… |
| lobo#65 red with lobo#62 fixed | CI run **38077177455** at `edc2a16` (acme, linux: 5005 ms); `rig-red-acme.log` c0d8224e… |
| lobo#65 green | `90a8e13` onward; `acw-h2.log` 3719b7ae… at `45b7052` |
| the witnesses under three cpusets at `0374b1c` | `corp-w-0.log` 57835313…, `corp-w-03.log` 9f0e8adb…, `corp-w-all.log` 056a4489… (7/7 each: stream abort, slow stream, stream cap, tick clock); `rig-acme-0.log` 7a6ae82e…, `rig-acme-03.log` 17b9db71…, `rig-acme-all.log` 07027703… (GREEN each); 0 SKIP lines in all six |
| gauntlet GREEN at the code head | `g-head1.log` 02a58dca… at `0374b1c`: exit 0; SigBlk 0x10000 / SigIgn 0x7; corpus 318/318, control 20/20, signal 21/21, prefork 38/38, membudget 17/17, resolver 9/9; 2 SKIP lines, both named (signal's linux-only header, membudget's wolf-lang#191 gate); release ebf2134b…, debug dc65b4e5… |
| the trunk toolchain and the two lobos profiled | `bt-trunk.log` c56fcf59… (wolf-lang `76436101`, `wolf` 95daf2d2…, `libwolf_rt.a` a08075b1…); `lb.log` 4f901933… (lobo `ebace85`: trunk wolf 052967a8…, 0.2.26 d2d78003…) |
| instructions, cycles, user and system time a request | `prof-tw.log` 768a9687…, `prof-nginx.log` 48200551…, `prof-0226.log` 1ac757dc… |
| calls a request | `sys-tw.log` c366219d…, `sys-nginx.log` e01e003e… |
| faults and growth a request, idle growth | `flt-tw.log` 3f3bfae5…, `flt-0226.log` 958b748e…, `flt-nginx.log` 58a1abdb…, `idle-tw.log` 01471bc6…, `idle-0226.log` 4bc8a198… |
| what a fault and the four file calls cost this kernel | `pf.log` a54d89a8…, `pf2.log` d81e139d…, `fsys.log` 79edf632… |
| the huge-page ablation, one window | `flt-tw-thp.log` b992ed29…, `prof-tw-thp.log` c7412480…, `prof-tw2.log` f38b36c7…, `prof-nginx2.log` 9126689b… |
| user time by function, four cells | `cg-tw-keepalive-1.log` 865cb121…, `cg-tw-keepalive-4.log` 27c90bbc…, `cg-tw-close-1.log` 995bb889…, `cg-tw-close-4.log` 29e7bc35… |
| kasumi parity, REFUSED for load (indicative) | `parity-kasumi.log` c5520c8c… |
| CI green at `45b7052` on linux and macOS | run **38078339632** |
| CI at the head | in the PR body (the head is this commit's child) |

## 5. Done-when

- [x] Branch `ws56` on origin; PR open against `trunk`, unmerged, five
  sections by name, commit shas as bullets, a test checklist.
- [x] lobo#62 and lobo#65 each red first by run id, then green.
- [x] The profile on wolf-lang trunk: instructions and calls a request
  for keepalive and close at 1 and 4 workers, lobo beside nginx,
  attributed to functions; six levers ranked with a bound each, each
  filed in the repository that owns it (lobo#66, #67, #68;
  wolf-lang#654).
- [x] The recommendation for ws57 (the PR body and docs/PROFILE.md).
- [ ] CI green at the head sha on linux and macOS;
  `wolf/tools/lane-audit.sh lobo ws56 <PR>` run; kasumi worktrees
  removed and the build directories pruned (logs kept); no orphan
  pids. Nothing closed by this lane.
