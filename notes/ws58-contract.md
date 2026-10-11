# ws58 — the file memo

Wave 53, lane ws58 (Opus). Written 2026-10-11 on lobo trunk `c9eff15`,
before the 0.2.27 / 0.1.50 archives were downloaded or unpacked and
before any edit to `src/`, `tools/` or `tests/`. The planning contract
is `sprints/wws/27-the-file-memo/ws58-the-file-memo.md` in
`wolffe-lang/wolf`; rules are `sprints/wave-53.md` down to
`wave-45.md`. The oracle is the pinned nginx 1.30.4 (ws47's copy,
`65595ac2…`), run, never read.

One deliverable: lobo pinned to wolf 0.2.27 / lupin 0.1.50 by digest,
the static-file path memoised on one `fs_stat` a request (lobo#67), and
the parity table re-measured with keepalive at four hands held to the
1.10 bar: met, or the rest of the gap attributed by ablation.

## 1. Forbidden, absolutely

- nginx behaviour only from the pinned oracle; never read nginx's, any
  other server's, GNU's, glibc's, musl's or a kernel's source.
- The pin is taken from the release archives by digest: never a clone,
  Homebrew or `~/.local/bin`; never a build of wolf-lang trunk.
- No `rm` outside `~/lanes/ws58/` (nomad-1 and kasumi) and this lane's
  own clones, `/tmp` included; no scratch in `/tmp`. No `git add -A`.
  Nothing under `~/.claude`. No package installs. No merge, tag or
  release; close no issue. No commit trailers or PR attribution of any
  kind. Checksums carry a trailing `…`. No "seen red" without a run
  id, sha, path or digest.
- Strict evidence (wolf-lang#571): `WOLF_PAIRING_REQUIRE_SIBLING=1`,
  stdout and stderr together, every SKIP line counted; a `wolf build`
  that exits 2 is a compile error, never a skip; process-spawning and
  concurrency rows also under `taskset -c 0-3`.
- kasumi: remote commands in `bash -c`, `setsid` with a pid file, kill
  by recorded pid only, `CARGO_INCREMENTAL=0`, outputs pruned. No
  build on nomad-1. At most two CI runs of this lane at once; never
  cancel another lane's.
- Never touch the maintainer's Cloudflare tunnels, `~/.cloudflared`,
  DNS, ports 8080 or 8088, or hasu's `~/models`, `~/.local`,
  `~/pool-serve`, the :9308 server. This lane's ports are 18610–18629
  and kernel-chosen ones. The live site is not this lane's to redeploy.
- No parity figure from a loaded host: `uptime` is read and the load is
  written beside every number; the parity tool's refusal is a refusal.

## 2. Inputs, verified (re-derived 2026-10-11, from the release API)

| input | what was found |
|---|---|
| wolf 0.2.27 | tag `v0.2.27` → wolf-lang `0ddda6b7ab9f…`; release 409367590, published 2026-10-11T04:12:05Z. Asset digests as the API gives them: linux x86-64 `5e17eebe…`, linux aarch64 `c475e5dc…`, macOS arm64 `ea461a76…`, windows `ac784416…` |
| lupin 0.1.50 | tag `v0.1.50` → wolf-interp `32b970da7f3a…`; release 409303515, published 2026-10-11T00:53:58Z. linux x86-64 `e2867a35…`, linux aarch64 `a0c0c707…`, macOS arm64 `2cbd192d…`, windows zip `420e02c0…`, `lupin.exe` `b37b13bf…` |
| 0.2.27's CHANGELOG | read at the tag: "Read this before you bump the pin", the pairing, the std section, s222's and s218's entries, and the two known soundness issues (wolf-lang#660, #665) |
| the archive carries `std/` | wolf-std `87ba162` beside `wolf`, with `std/STD-REV`. lobo's pin is `[std] 14f0ab2c`; whether lobo's staging copies the whole archive into `.wolf-bin/` is read in `tools/lib-toolchain.sh` and CI before the pin commit (§3 says what is expected) |
| seventeen new prelude names | to grep at the pin commit; the release's own grep of lobo `d1bf135` found none |
| lobo trunk | `origin/trunk` = `c9eff15` (ws57): pins [wolf] 0.2.26 `89dc139`, [lupin] 0.1.49 `f516a5f`, [std] `14f0ab2c`; the regions `life`, `memo`, `pass`, `step` in `serve_main`; `tools/lobo-membudget` a hard gate |
| lobo#67, #68 | open, as ws56 filed them |
| ws57's reading of the path | read in the code: `classify` is one `fs_open_mode(path, 5)` and one `fs_fstat`; `serve_file` reads the body in `region resp`, gathers head and body in one `net_writev_head`, closes. Four file calls a request. The memo table `ft` lives in `region memo` (let go at 1 MiB); a step reads it and notes what it would store in a `MemoUpd`, which the loop stores under `in memo` |
| not in 0.2.27 | s228's `net_read` into the ambient region and the handle-table residue fix are on wolf-lang trunk only: lobo's `sock_read` workaround stays, with a dated comment naming the pin that removes it |

## 3. Prediction, committed before the archives are unpacked

### The pin alone (no source change but what the pin forces)

- **Source.** Nothing refused: zero diagnostics on both tiers, no
  W0304 (no local name among the seventeen), no manifest change. The
  staging step needs the `.wolf-bin/std` removal only if it copies the
  whole archive; I expect lobo's `lib-toolchain.sh` copies named
  members, so the removal is a guard and not a fix. If lobo stages its
  own std over the archive's, the archive's `std/` is removed first.
- **Binary size.** The release binary moves by under 2 % either way
  (the runtime's arena and read buffers change; the exec, signal and
  stat members are linked only where called, and lobo calls none yet).
- **RSS and the gate.** RSS after 400,000 keepalive requests stays at
  6.0 MB within 0.6 MB (s222's per-thread windows are 64 KiB each);
  growth stays 4–7 B a keepalive request and 55–75 B a connection (the
  handle tables' residue is not fixed in 0.2.27); idle growth 0. Every
  membudget row keeps its verdict.
- **Instructions.** User instructions a request fall 10–13 % on
  keepalive and on close (s222 measured −12.0 % / −12.8 % on lobo
  before the regions; the regions removed some of what the arena
  touched, so the low end is likelier).
- **Parity at the pin alone (nginx ÷ lobo; under 1.10 is met).**

  | cell | kasumi | the runner |
  |---|---|---|
  | keepalive N=4 | 1.07–1.11x | 1.05–1.11x |
  | close N=4 | 1.00–1.04x | 1.03–1.09x |
  | keepalive N=1 | 1.04–1.08x | 1.02–1.06x |
  | close N=1 | 0.89–0.94x | 0.87–0.93x |

  Keepalive at four hands lands on the bar and is not safely inside it
  by the pin alone.

### The memo (lobo#67)

- **Shape.** A per-hand table in `region memo`, beside the head memo,
  direct-mapped by the path's slot (256 slots): the path, the file's
  identity as `fs_stat` answers it (device, inode, size, modification
  and status-change times to the nanosecond) and **the bytes**, held as
  a one-part gather so the write lends them and copies nothing. A
  request for a path whose slot holds it makes **one** `fs_stat` by
  path; when every word matches and the kind is a regular file, the
  head comes from the head memo and the body from the table, and the
  response is one `writev`. Anything else falls to today's path (open,
  fstat, read, close), unchanged.
- **Bytes, not the open descriptor.** A kept descriptor still needs
  the path stat (a permission change, a rename and a deletion are
  invisible through a descriptor) and then a positional read: two
  calls where the bytes need one. It also pins a deleted file's blocks
  and a descriptor per entry per hand. The bytes cost memory, which is
  bounded, and open one window a descriptor does not have (a rewrite
  in place inside one timestamp tick), closed by the admission rule
  below.
- **What it must check to stay correct.**
  1. *Replaced* (a rename over the name): a new inode. *Truncated,
     grown*: the size. *Rewritten in place*: the modification time.
     *Made unreadable* (mode, owner, ACL): the status-change time,
     which no `utimes` can set back; the miss then opens, and the open
     answers 403 as today. *Deleted*: the stat answers `not_found`,
     the miss answers 404. *Swapped for a symlink*: `fs_stat` follows
     it to another inode (or to the same one, whose bytes are the
     same). A directory in the path made unsearchable or replaced:
     the stat walks the path every request.
  2. *The same-tick rewrite.* A file written twice inside one
     timestamp tick has one size-and-times record for two contents.
     So a file is admitted only when its status-change time is at
     least 3 s older than the clock at the stat that admits it (the
     rule version-control tools use for the same race): any later
     write then moves the times. A file younger than that is served
     the old way until it is not.
  3. *The fill.* The bytes are read from a descriptor and the identity
     from the path, so a fill stats the path before the open and again
     after the read and keeps the bytes only when the two records are
     word-for-word equal, admissible, and agree with the descriptor's
     own size and mtime.
  4. Only the plain shape is served from the table: a `GET` or `HEAD`
     with no `Range`, plaintext, no memory budget, a regular file of
     at most 32 KiB. Ranges, TLS, budgeted locations and larger files
     take today's path.
  5. A reload drops the table (it is also keyed by the full path and
     validated every request, so a root change could not make an
     entry wrong; the drop is the contract's letter).
- **The bound and the eviction.** At most 256 entries of at most
  32 KiB a hand, and no more than the memo region's existing cap
  (1 MiB), at which the whole table is let go, as the head memo is
  today. A slot's entry is displaced by another path only when it was
  filled in an earlier second, and a path is admitted on its second
  miss in a row for its slot, so a cold walk over many files pays no
  extra stat and two hot paths in one slot trade places at most once
  a second.
- **Syscalls a request, by strace count** (one hand, the parity file).
  Keepalive: `openat` 1 → 0, `read` (the file) 1 → 0, `close` 1 → 0,
  the stat 1 → 1 (by path where it was by descriptor): **three fewer**,
  about 6.4 → 3.4 with the loop's wait and the socket's read and
  `writev`. Close: about 12.4 → 9.4.
- **Memory.** The gate's rows move by under 64 KB (one 1 KiB body and
  its row); RSS after 400,000 keepalive requests under 6.7 MB.
- **Instructions.** User instructions a request fall a further 8–14 %
  on keepalive (the four runtime calls were 14.6 % of user cycles;
  one comes back as `fs_stat`, which builds a twenty-word list).
- **Parity with the memo.**

  | cell | kasumi | the runner |
  |---|---|---|
  | keepalive N=4 | 1.00–1.06x: **met** | 0.99–1.07x: **met** |
  | close N=4 | 0.96–1.02x | 0.98–1.05x |
  | keepalive N=1 | 0.97–1.03x | 0.96–1.02x |
  | close N=1 | 0.86–0.92x | 0.84–0.91x |

  If keepalive at four hands is still over 1.10 on any host, the
  ablation says what nginx does not do that lobo does, in syscalls and
  instructions a request.

### The #665 survey

I expect lobo's sends to be few (the stream pipe, the budget procs'
reports, the ACME daemon's events are pipes and descriptors, not
channels) and expect to find **no** helper that sends an argument on a
channel; the #660 shape is the one ws57 worked around by name (`in
life` calls take scalars or strings built inside the block). Every
`send` in `src/` is listed with its payload's origin either way.

### lobo#68

Not small: three levers (parsing, bookkeeping, head and route), each a
profile-and-rewrite of its own. I expect to take none of it and say so,
unless the memo's hit path makes one of them a few lines.

### §2, what the staging found (after the prediction was committed)

- The archives match the release API's digests on kasumi
  (`dl/digest-check.txt` 174ba404…). Members by name (linux x86-64):
  `wolf` 6f5713a2…, `libwolf_rt.a` ab575b27…, `wolf-cimport-worker`
  96f93227…, `lupin` 3a476442…, `libwolf_rt_none.a` 46544be6…
  (`toolchain-tc-0227.txt` ba6933bf…).
- The archive's `std/` is wolf-std `87ba162`, 55 files, and differs
  from lobo's pin `14f0ab2` in six files and two licences
  (`std-compare.txt`). lobo stages named members, and CI builds
  `wolf` from source, so nothing needed removing; the two trees give
  byte-identical lobo binaries at 0.2.27 (debug 95dfc14b…, release
  a6e9d15c…; `build-pin0.log` 92afa18d…, `build-pin0-alt.log`
  2dcec19b…). The pin holds at `14f0ab2`.
- No declaration of any of the seventeen new prelude names in `src/`
  or `tests/` (grep, 0 lines).
- `fs_stat`'s record, read in the spec at the tag (`[os.fs.stat]`):
  twenty words; kind 0, size 1, modified_ms 2, `have` 3, device 9,
  inode 10, mtime 14–15 and ctime 16–17 as seconds and nanoseconds.

### §3 against the measurement (written at the close, 2026-10-11)

**The pin alone.**

| | predicted | measured |
|---|---|---|
| source | nothing refused, no W0304, no manifest change | **held**: zero diagnostics on both tiers at `--error-limit=0`; gauntlet GREEN at `51089ef` on kasumi (`g-gpin.log` d101c296…, 0 SKIP lines) and in CI on linux and macOS (run 38112705120) |
| the `.wolf-bin/std` removal | a guard, not a fix | **held**: not needed, said in `wolf-toolchain.toml` |
| release binary | within 2 % | **missed on the file, held on the text**: 12,804,744 → 13,495,664 B (+5.4 %); text 1,661,106 → 1,667,954 (+0.4 %) |
| RSS after 400,000 keepalive requests | 6.0 MB within 0.6 | **held**: 6.1 → 6.0 MB |
| growth a keepalive request / a connection | 4–7 B / 55–75 B | **held**: 4.6 / 66.5 B (5.4 / 62.4 at four hands) |
| the gate | every row keeps its verdict | **held**: 22/22 (4 KB, 228 KB, 0) |
| user instructions | −10 to −13 % | **missed**: −7.0 % and −6.7 % (keepalive, connection-per-request, one process), −7.3 % and −6.4 % at four hands |
| parity, the runner, keepalive N=4 | 1.05–1.11x | **held**: 1.090x (and 1.094x–1.113x on four more VMs as the reference tree) |
| parity, the runner, close N=4 | 1.03–1.09x | **held**: 1.062x (1.060x–1.075x) |
| parity, the runner, N=1 keepalive / close | 1.02–1.06x / 0.87–0.93x | **missed, better**: 1.001x / 0.824x |
| parity, kasumi, keepalive N=4 | 1.07–1.11x | **held**: 1.104x, 1.097x |
| parity, kasumi, close N=4 | 1.00–1.04x | **held once of twice**: 1.067x, 1.038x |
| parity, kasumi, N=1 keepalive / close | 1.04–1.08x / 0.89–0.94x | **held**: 1.051x–1.053x / 0.882x–0.895x (one reading a hair under the band) |

"Keepalive at four hands lands on the bar and is not safely inside
it by the pin alone": held. Five VMs read 1.090x to 1.113x.

**The memo.**

| | predicted | measured |
|---|---|---|
| shape | a table in `region memo`, direct-mapped, 256 slots; the path, the stat identity, the bytes as a one-part gather; one `fs_stat` a request | **held**, as written |
| what it checks | device, inode, size, mtime and ctime to the nanosecond; admitted only 3 s after its last status change; a fill between two equal stats; the plain shape only; dropped at a reload | **held**, and one limit the prediction did not name: a file rewritten through a shared `mmap` moves its times late (the kernel's, not the rule's) |
| the bound and the eviction | 256 entries of at most 32 KiB inside the region's 1 MiB; admitted on the second miss in a row; displaced at most once a second | **held**; one rule added: a refused admission is not retried for a second |
| syscalls a keepalive request | three fewer, about 6.4 → 3.4 | **held**: 6.05 → 3.04 (one process), 6.31 → 3.25 (four hands); the runner 6.24 → 3.24–3.27 |
| syscalls a connection | about 12.4 → 9.4 | **held in the difference, the level was stale**: 9.09 → 6.08 and 9.94 → 7.12 (ws57 had already taken the level down; the note quoted ws27's) |
| the gate's rows | move by under 64 KB | **held, the other way**: 4 → 0 KB, 228 → 72 KB, 0 → 0 (the runtime's 4 bytes per `fs_open` stop accruing); 23/23 |
| RSS after 400,000 keepalive requests | under 6.7 MB | **held**: 4.6 MB |
| user instructions | a further −8 to −14 % on keepalive | **missed**: −1.2 % and −0.8 %. The four calls were cheap in instructions and dear in kernel time; `fs_stat` costs about 1,700 (wolf-lang#690); the first build was +5 % until the path was folded once and by its short end |
| parity, kasumi, keepalive N=4 | 1.00–1.06x: met | **held**: 1.025x, 1.004x |
| parity, the runner, keepalive N=4 | 0.99–1.07x: met | **missed, better**: 0.914x–0.934x on four VMs |
| parity, close N=4 | kasumi 0.96–1.02x, the runner 0.98–1.05x | kasumi **missed by a hair** (1.026x, 1.015x); the runner **held** (1.022x–1.038x) |
| parity, N=1 | keepalive 0.96–1.03x, close 0.84–0.92x | **missed, better** on both hosts: keepalive 0.81–0.90x, close 0.70–0.82x |

Not predicted at all: that a drive begun on a file written a moment
ago measures the OLD path (the first strace difference came out
negative for that reason), so every bench tool now ages its file
four seconds and the memory gate takes each path on purpose.

**The #665 survey: held, and the neighbour was not predicted.** No
channel, no send and no `Mutex` in `src/`; the only sends in the
repository are two replay tests' `closes.send(1)` and
`deadline.send(1)` on a `channel[int]` (four lines, an integer
literal: nothing that can name region bytes). Every `spawn proc`:

| site | arguments | can the payload outlive its region? |
|---|---|---|
| `main.lu` ×2, `sig_forwarder(w, mask, probe)` | three ints | no bytes |
| `budget.stream_open` ×2, `stream_body(sock, fd, out, id)` | four ints | no bytes |
| `acme.daemon_start` → `daemon(store, names, contact, ca_url, ca_root, …)` | five strings from the configuration, built in `serve_main`'s own region before `life` is made | no: the process root outlives the proc |
| `budget.run_small` → `body_small(sock, path, head, cap, pipe)` | `path` and `head` built in the request's step region | **it could, on one arm**: the join's `timeout(600.s)` returned with the proc alive. Each of the proc's writes is bounded by the socket's 60 s budget, so the arm was not reachable while the proc held the strings. Fixed anyway: the arm kills and joins (`end_body`) |
| `budget.run_stream` → `body_stream(sock, path, cap, pipe)` | `path`, the same region | **it could**: a long stream to a slow reader can outlast 600 s, ten chunks at 60 s each. The proc reads `path` in its first statement only, so no freed byte was read. Fixed the same way |

The compiler's part is wolf-lang#678: a `spawn proc` argument built
in a region block is not refused, with or without a helper, and
0.2.27 prints the freed bytes (`probe/s1_helper.lu`,
`probe/s2_direct.lu`; `s12.log` d7c3dc84…; control `s3.log`
0428e32c…). Writing the fix's witness found wolf-lang#683: a killed
proc parked in `net_read` runs on to its next park on native and
release (`probe/k1_kill.lu`, `k1.log` 2c4f08f3…), so the join, not
the kill, is what makes the rule true. #660's shape: 28 `in life`
and `in memo` blocks in `main.lu`, read one by one; each call takes
scalars, a string built inside the block, or (`carry_put`, twice) a
string whose bytes it copies into a byte buffer and does not keep.

**lobo#68: not taken**, as predicted, and for the reason predicted.

Corrections to §2: the level the note quoted for syscalls a request
(12.4 a connection) was ws27's; at ws57's trunk it was 9.1 to 9.9.
To §1: nothing touched outside `~/lanes/ws58/` on either box; one
worktree was first made inside this lane's own clone on kasumi by a
slip (`git -C lobo worktree add` with a relative path) and removed
with `git worktree remove` a moment later; one throwaway branch
(`ws58-plant`, the planted break) was pushed to lobo's origin for
its CI run and deleted by this lane afterwards.

## 4. Evidence index

kasumi paths are under `~/lanes/ws58/`; nomad-1 paths under
`~/lanes/ws58/`.

| claim | artifact |
|---|---|
| the archives by digest, the members, the oracle | `dl/digest-check.txt` 174ba404…, `toolchain-tc-0227.txt` ba6933bf…, `nginx.sha256` (65595ac2…) |
| the prediction before the archives | commit `d8108b5` (04:26:26Z; the staging began 04:27:19Z, `stage.STATUS`) |
| std re-derived | `build-pin0.log` 92afa18d…, `build-pin0-alt.log` 2dcec19b…, `std-compare.txt` |
| the pin green | kasumi `g-gpin.log` d101c296… at `51089ef` (exit 0, 0 SKIP lines, membudget 22/22); CI run **38112705120** (linux and macOS) |
| instructions and CPU a request, three trees and the oracle | `prof-trunk2.log` d56d630e…, `prof-pin2.log` 70cfda4d…, `prof-head2.log` b54c764c…, `prof-nginx2.log` bd32ab25… |
| syscalls a request by strace count, before and after | kasumi `sys-trunk2.log` dbde6c18…, `sys-pin0.log` a62ddf1a…, `sys-pin0-n4.log` 9e7276ba…, `sys-head2.log` a31b1616…, `sys-head-n4.log` b9e63849…, `sys-nginx.log` a8956f19…, `sys-nginx-n4.log` 8929eae7…; the runner: run **38113500739** at the pin, runs **38114237409** and **38115586226** at the memo (`nomad-1: ci-sys-pin-38113500739.log` 30db25fe…, `ci-parity-38114237409.log` 16d276bf…, `ci-parity-38115586226.log` 04f827f9…) |
| where the instructions are | `cg-pin0-keepalive-1.log` c1d28f4d…, `cg-work1-keepalive-1.log` 9e0e851c… (the first build), `cg-work3-keepalive-1.log` bfcae5bb… (the head's serving code) |
| growth, faults, idle | `flt-trunk.log` 532226a3…, `flt-pin.log` bcac5b3f…, `flt-head2.log` 19354ccf…, `lin-head-ka.log` 883a5722…, `lin-head-close.log` b046091d…, `idle-head.log` 18565346… |
| the memory gate's rows | at the pin: `g-gpin.log` (22/22); at the head: `g-ghead2.log` 91190944… (23/23: 0 KB, 72 KB, 0 KB, the kept file 0 KB; the capped rows 1,208 and 784 KB); CI at the head in the PR body |
| parity, the runner, the pin against 0.2.26 | run **38112700746** (`ci-parity-38112700746.log` 697074fe…) |
| parity, the runner, the memo against the pin, four VMs | runs **38114237409**, **38115586226**, **38116620581** (its two-hand set REFUSED, so the run is red by the tool's exit 3), **38116627609**; logs 16d276bf…, 04f827f9…, 40eacbba…, 7daaf704… |
| parity, kasumi | `par-k4.log` adf49b94… (`309255c`'s build), `par-k4b.log` 749e8e8d… and `par-k2b.log` f122fac2… (the head's build, 2c3729e9…); REFUSED on load: `par-k2.log` 8e9ac2aa…; the loads waited on: `chainP2.loads` |
| the #665 survey's witnesses | `probe/s12.log` d7c3dc84…, `probe/s3.log` 0428e32c…, `probe/k1.log` 2c4f08f3…; wolf-lang#678, #683 |
| the planted break (a memo that skips validation) red in CI | run **38117753437** at c8789c3 on the deleted branch `ws58-plant`, linux and macOS: `tests/serve/file_memo.lu` on both lanes (its in-place rewrite row) and `tests/serve/file_memo_e2e.lu` on both (the same change on the keep-alive connection; the native lane at its ceiling); 322 of 327 lane-runs green, nothing else red; `nomad-1: ci-plant-38117753437.log` 04b6e64d… |
| gauntlet GREEN at the head, strict, the whole gauntlet under `taskset -c 0-3` | `g-ghead2.log` 91190944… at `ce02889`: exit 0; SigBlk 0x10000 / SigIgn 0x7; corpus 327/327, differential 24/24, control-differential 20/20, signal 21/21, prefork 38/38, membudget 23/23, resolver 9/9, acme GREEN; 0 SKIP lines |
| the carry test's flake is not this lane's | `loop-wt-gpin-carry_e2e.log` 89397cb0… (the pin: 22 of 25), `loop-carry_e2e.log` af2d56eb… (this branch: 22 of 25), `dbg-wt-gpin.log` 8ac47573… (the hang's sockets); lobo#72 |
| CI green at the head on linux and macOS | in the PR body |

Seen red, each by its artifact: the first work-tree gauntlet
(`g-gwork1.log`: `tests/proxy/gateway_502.lu` [checked] at the 60 s
ceiling on a box at load 9, green alone and green at the pin and at
the head); the gauntlet at `c038dd5` (`g-ghead1.log` and CI run
38114233221: `tests/serve/range_plan.lu` did not compile, a caller
of `memo_store` this lane had not updated; fixed in `309255c`; the
same log holds one `carry_e2e` ceiling, lobo#72).

## 5. Done-when

- [x] Branch `ws58` on origin; PR open against `trunk`, unmerged, five
  sections by name, commit shas as bullets, a test checklist.
- [x] Item 1: the pin by digest in its own commit; parity and the
  memory gate at the pin alone, before any other change.
- [x] Item 2: the memo; a test for each change on both tiers and
  beside the oracle; the bound and the eviction named; memory inside
  the gate; no memo across a reload.
- [x] Item 3: the #665 survey, a fix for the one site found and two
  compiler issues filed with witnesses.
- [x] Item 4: parity at 1, 2 and 4 hands, both shapes, on kasumi and
  on four runner VMs (two hands: two VMs valid, one refused).
  Keepalive at four hands is under 1.10 on every host, so no ablation
  table is owed; `docs/PROFILE.md` has the per-request table anyway.
- [x] Item 5: lobo#68 not taken; why is in §3.
- [x] The planted break red in CI by run id (38117753437).
- [ ] CI green at the head on linux and macOS, and the audit run from
  the org directory with its exit status read directly; worktrees
  gone; outputs pruned; no orphans. These come after this file's
  last commit and are recorded in the PR body.
