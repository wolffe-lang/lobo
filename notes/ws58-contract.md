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

## 4. Evidence index

Filled at the close.

## 5. Done-when

- [ ] Branch `ws58` on origin; PR open against `trunk`, unmerged, five
  sections by name, commit shas as bullets, a test checklist.
- [ ] Item 1: the pin by digest in its own commit; parity and the
  memory gate at the pin alone.
- [ ] Item 2: the memo; a test for each of the six changes on both
  tiers; the bound and the eviction named; memory inside the gate; no
  memo across a reload.
- [ ] Item 3: the #665 survey.
- [ ] Item 4: parity at 1, 2 and 4 hands, both shapes, kasumi and
  three runner VMs; the ablation if keepalive at four is over 1.10.
- [ ] Item 5: lobo#68 taken or the reason not.
- [ ] CI green at the head on linux and macOS; the planted break (a
  memo that skips validation) red in CI by run id.
- [ ] The audit run from the org directory, exit status read directly;
  worktrees gone; outputs pruned; no orphans.
