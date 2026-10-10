# ws57 — the returned memory

Wave 53, lane ws57 (Opus). Written 2026-10-10 (19:40–20:40Z) on lobo
trunk `d1bf135`, after the growth figures were reproduced there and
before any edit to `src/`, `tools/` or `tests/`. The planning contract
is `sprints/wws/26-the-returned-memory/ws57-the-returned-memory.md` in
`wolffe-lang/wolf`; rules are `sprints/wave-53.md` down to
`wave-45.md`. The oracle is the pinned nginx 1.30.4 (ws47's copy,
`65595ac2…`), run, never read.

## 1. Forbidden, absolutely

- nginx behaviour only from the pinned oracle; never read nginx's, any
  other server's, GNU's, glibc's, musl's or a kernel's source. The
  acme rig only, never a production ACME endpoint.
- lobo stays on wolf 0.2.26 / lupin 0.1.49. No compiler change: a wolf
  defect found is filed with a minimal repro and worked around by name.
- No behaviour change on the wire: every corpus and control row keeps
  its verdict; a row that moves is named and argued.
- No allocator tuning as the fix (`GLIBC_TUNABLES`, huge pages,
  `malloc_trim`). The memory is returned by scoping.
- Never touch the maintainer's Cloudflare tunnels, `~/.cloudflared`,
  DNS, ports 8080 or 8088, or hasu's `~/models`, `~/.local`,
  `~/pool-serve`, the :9308 server. This lane's ports are 18586–18599
  and kernel-chosen ones.
- No `rm` outside `~/lanes/ws57/` (nomad-1 and kasumi) and this lane's
  own clones. No `git add -A`. Nothing under `~/.claude`. No package
  installs, no system settings. No merge, tag or release; close no
  issue. No commit trailers or PR attribution of any kind. Checksums
  carry a trailing `…`. No "seen red" without a run id, sha, path or
  digest.
- Strict evidence (wolf-lang#571): `WOLF_PAIRING_REQUIRE_SIBLING=1`,
  stdout and stderr together, every SKIP line counted;
  process-spawning witnesses also under `taskset -c 0-3`. A
  `wolf build` that exits 2 is a compile error, never a skip. Parity
  figures only from a quiet machine; the tool's refusal is a refusal.

## 2. Inputs, verified (re-derived 2026-10-10, 19:40–19:52Z)

| input, as the contract states it | what was found |
|---|---|
| lobo trunk `d1bf135` or later (ws56 merged) | **holds**: `origin/trunk` = `d1bf13560e4e…`; pins [wolf] 0.2.26 `89dc139`, [lupin] 0.1.49, [std] `14f0ab2c` |
| the toolchain | the 0.2.26 / 0.1.49 linux x86-64 archives match the pinned digests (`05acdc5e…`, `84911a35…`; `kasumi:~/lanes/ws57/dl/digest-check.txt`), members `wolf` 272e0888…, `libwolf_rt.a` 679d77e1…, `lupin` 6d057eb1…. Trunk built there: debug 21a12e70…, release ebf2134b… (`build-trunk.log`), the release digest ws56's gauntlet recorded |
| the oracle | `65595ac2…`, nginx/1.30.4 (`nginx.sha256`) |
| the growth figures at trunk | **reproduced** (`flt-trunk.log` ef89b5a9…, `idle-trunk.log` 6a4404c6…; kasumi, `taskset -c 0-3`, 4 × `ab -c 8`, the parity file): keepalive N=1 **2,060 B** and 0.503 minor faults a request (RSS 819 MB after 400,000); close N=1 **9,940 B** and 2.42 faults a connection (2,015 MB after 200,000); keepalive N=4 3,515 B and 0.858; close N=4 12,386 B and 3.02; idle with no connection **344 kB in 20 s** (85 faults: 4.3 KB a 250 ms pass); idle with 32 kept-alive connections 1,024 kB in 20 s. The oracle (ws56's `flt-nginx.log`): 0 faults, 3.7 MB |
| lobo#66, #67, #68, #69 | open, as ws56 filed them |
| membudget's named SKIP | `tools/lobo-membudget` prints "NAMED GATE (loud skip, not a pass) … wolf-lang#191" whenever round B grows 4 MiB or more, and never fails on it; `docs/BUDGET.md` attributes the string half to #191 in six places (ws56 corrected one). wolf-lang#191 closed 2026-09-13 |
| what a step stores into long-lived state (the E1010 sites) | read in the code at `d1bf135`. **Inside `serve.conn_step`:** the memo table `ft` (`head_remember`: seven index stores, three of them `str`; `date_str`: the date `str`; `next_boundary`: a counter) and the resolver `rs` through `proxy.run` (`rotate` rebuilds the `rr` column on every proxied request to a named peer; `resolve_now` rebuilds every column when the cache went stale between the park check and the dial). **In the loop, from a step's result:** the eight row lists rebuilt every pass (two of them `str`: the carry and the parked name), `resolver.start`, the access record moved into `pass_accs`, `gens` rebuilt by `bump_live` / `on_conn_close` / `note_request` / `retire_zero` (the last one every pass), `counters` through `note_served`, `sslots` through `stream_open`, the error log's and the access sinks' `buf` strings through `ev_log` and `pump_sinks`, `sbuf`, `aevs`, and on a reload or an issuance `ssl0`, `asinks`, `elog`, `optin` |

Three things the inputs did not say, found by probe before the
prediction (`nomad-1:~/lanes/ws57/probe/`, wolf 0.2.26):

1. **A call with a `mut` argument inside a region is E1010 for any
   argument that can hold heap** (a struct of ints included; a bare
   `int` is accepted). So "a region around the pass" refuses every
   `ev_event(mut elog, …)`, `note_served(mut counters, …)`,
   `resolver.tick(mut rs, …)` in the loop as written. Direct stores
   are accepted: `x.n = …`, `xs[i] = …`, `gens[i].live = …` (all four
   machines, probe `d-p3`).
2. **`in r { … }` over a first-class region aims a call's
   allocations at `r`**, and is accepted inside a region block for
   state that lives in `r` (probe `d-p2`, `d-p3`). That is the commit
   door: `in st { f(mut state, …) }`. What `f` allocates then lives
   as long as `st`, so `f` must allocate nothing on a hot path.
3. **`net_read` answers a `str` whose bytes the runtime places in the
   process root whatever region is open** (`ambient_copy`,
   `wolf_rt/src/net.rs` at `v0.2.26`), so a region around a step does
   not return the bytes a step reads. `net_read_bytes` answers a
   `List[byte]` in the current region and `str_from_utf8` builds
   there. Worked around by name; to be filed.

And one wolf defect, to be filed and never leaned on: under
`in st { f(mut state, s) }` the checker lets `f` keep `s` (through
`copy s`, which shares the bytes) when `s` was built in the enclosing
region block. wolf 0.2.26 prints freed bytes (`ZZZZ…`), lupin 0.1.49
traps `region-fault` (probe `d-p6`). Every `in st` call in this lane
passes scalars, or strings built inside the `in` block.

## 3. Prediction, committed before the first change

**Where the regions go** (all in `serve_main`, `src/main.lu`).

- `st`: a first-class region made once, before the loop. Everything
  the loop keeps lives there. It is never freed; nothing on a hot path
  may allocate in it.
- `region memo { … }`: around a run of passes. It holds the per-hand
  head-and-date memo (`serve.FileKinds`), the one long-lived table
  whose strings change every second and which can be dropped without
  a wrong answer. The run ends, and the memo starts empty, when
  `region_bytes(memo)` passes 1 MiB.
- `region pass { … }`: the whole body of one pass (the wait set, the
  ready list, the control and signal dispatch, the accept burst, a TLS
  connection served to its end, the log pump).
- `copy region step { serve.conn_step(…) }`: one connection step. Its
  value, the `ConnStep`, is copied into `pass`.
- The existing `region resp`, `chunkr`, `skipr`, `spanr` in
  `src/serve/serve.lu` stay.

**Which stores cross a region, and how each is handled.**

| store | rule |
|---|---|
| the step's result (`ConnStep`: flags, the carry, the access record, the budget and stream fields) | `copy region step` into `pass` |
| the connection table (eight parallel lists rebuilt every pass) | the same columns, in `st`, compacted IN PLACE each pass (a write index behind the read index, so order is kept); a row count beside them; a new connection is an index store, or a push under `in st` when the table has never been that long (bounded by the most connections ever open at once) |
| the carry (`ccarry: List[str]`) | bytes in a fixed-stride `List[byte]` slab in `st` with a length column; written by direct index stores only when a step left a non-empty carry, read back with `str_from_utf8` in the step's region. A carry longer than the stride (possible only after a reload raised the header limits) is refused a slab and materialized in `st` (named, counted in the docs) |
| the parked name (`cwait: List[str]`) | an index into a list of names in `st`, appended to only for a name never parked on before (bounded by the upstream names the configs name) |
| the memo table `ft` | `conn_step` takes it read-only and returns what it would have stored (`MemoUpd` in the `ConnStep`); the loop stores it under `in memo`, the strings built there |
| the resolver `rs` | `conn_step` takes it read-only. A proxied request works on a copy made in its step; a rotation comes back as the host's name and is one in-place index store; any other change (a blocking resolve) comes back whole and replaces the table under `in st` (one table per DNS answer: named). `resolver.tick` and `take_events` are called only when a query is in flight or an event is waiting, under `in st` |
| `gens` | `gens[i].live`, `.drained`, `.aborted`, `.mem_hw`, `.mem_rt_hw`, `.bud_hits` stored in place; a rebuild (`start_reload`, `mark_draining`, `retire_zero`) only when a generation actually enters or leaves, under `in st` (bounded by reloads) |
| the error log and the access sinks | the pending text is a pass's own (`buf` is empty at the end of every pass once the error log's flush moves to the pass's end); what persists is scalars (descriptor, open flag, drop counts, the event sequence), read into a pass-local value at the top of a pass and stored back at its end |
| `counters` | `note_served` under `in st` (an index write, no allocation) |
| `sslots`, `ssl0`, `asinks`, `optin`, the stream pipe's partial line, a reload | under `in st`: bounded by streams ever in flight at once, by reloads and issuances, and by the partial line's length (a slab cell) |
| the bytes a step reads | `net_read_bytes` + `str_from_utf8` in `conn_step`, `conn.read`, the proxy's upstream reads, the stream and budget pipes (the workaround of §2.3) |

**Bytes retained after the change** (kasumi, the same drive as §2;
RSS is counted in 4 KiB pages, so "0" means under one page per 100,000
requests):

| | trunk | predicted |
|---|---|---|
| keepalive, a request, N=1 | 2,060 B | **under 4 B** |
| close, a connection, N=1 | 9,940 B | **under 8 B** |
| keepalive / close, N=4 | 3,515 / 12,386 B | under 8 / under 16 B |
| idle, no connection, 20 s | 344 kB | **0 kB** |
| idle, 32 kept-alive connections, 20 s | 1,024 kB | **0 kB** |
| RSS after 400,000 keepalive requests, N=1 | 819 MB | **under 8 MB** |
| minor faults a request | 0.50 / 2.42 / 0.86 / 3.02 | **under 0.01** in all four cells |

**Parity.** ws56's ablation removed the faults and left the bytes
touched; reuse should do at least that. Against that: a `ConnStep`
copy and two region cycles a request, and the carry and memo
plumbing. User instructions a request at 0.2.26 (ws56's
`prof-0226.log` is the before): within **±4 %** on both shapes.

| cell | ws56 (kasumi, plain → huge pages) | predicted, kasumi | predicted, the runner |
|---|---|---|---|
| keepalive N=4 | 1.192x → 1.118x | 1.09–1.14x | **1.10–1.17x: not met, or met by a hair** |
| close N=4 | 1.138x → 1.081x | 1.03–1.09x | **1.04–1.11x: met** |
| keepalive N=1 | 1.137x → 1.050x | 1.02–1.08x | 1.03–1.10x |
| close N=1 | 1.100x → 0.939x | 0.90–1.00x | 0.92–1.03x |

The runner's "before" is trunk measured in the same job on the same
VM (`ref_tree`), because two dispatches differ by more than the lever.

**The gate.** `tools/lobo-membudget` loses the named skip and gains
three hard rows on each of its two servers' plain path: RSS growth
over 4,000 keepalive requests on one connection, over 2,000
connections of one request each, and over 10 idle seconds with 16
kept-alive connections held open, each **under 512 KB**. At trunk the
same rows read about 80 MB, 20–40 MB and 0.5 MB, so all three are red
there (by CI run id, linux and macOS) before any fix is pushed. A
planted break (the `step` region removed) is red on the first two.

**Item 4 (lobo#67).** Taken only if the keepalive cell is still above
1.10 after item 1 and there is time inside the lane; otherwise left
for ws58 with the measured room.

**Item 5 (lobo#69).** Reproduced at the head. I expect the fix to be
small (the hand that runs the daemon is hand 1, or the single process;
the others never start one and pick the certificate up from the store
when it changes), but separable only if a hand can learn of an
issuance without a new channel; if it needs one, it stays filed.

**CI.** Both gauntlet jobs green at the head; the gate pushed before
the fix, so trunk's code is red by run id.

### §3 against the measurement (written at the close, 2026-10-10)

- **Where the regions go: held, with one name changed.** `life`
  (the note called it `st`; a step's result is `st`), `region memo`,
  `region pass`, `copy region step`, all in `serve_main`. The memo's
  region is let go at 1 MiB as written.
- **The stores that cross: held in shape; three rows differ.**
  - *The carry.* Not "a fixed-stride slab with a fallback": a pool of
    buffers, one a row, each grown to the longest carry it ever held
    (`carry_put`, `carry_str`). The stride would have reserved the
    longest possible carry for every connection holding a partial
    head, and reading a slab back by slice is about 60 times slower
    than decoding a buffer whole (8.7 µs against 0.13 µs on 4 KiB,
    `probe/d-p9`, `d-p10`). There is no "longer than the stride" case
    left, so nothing of a carry is ever materialized in `life`.
  - *The resolver.* As written, and `resolver.tick` and `start` also
    run on a copy made in the pass (not "under `in life`"): the tick's
    own work then dies with the pass and only a changed table is kept.
  - *The error log and the access sinks.* As written. The pass-local
    log value cannot hold a string of a longer-lived region beside its
    own (E1004: "the two regions must be one"), so its level is one of
    eight literals (`level_lit`) and the path is read where the flush
    happens (`sink_flush_lines`).
  - Not predicted: **the copy out of the step costs a call per
    string** (11 % of user cycles with the whole `ConnStep` copied),
    so the result is packed first (`serve.step_pack`, `StepOut`); and
    `retire_zero` could not run under `in life` with the pass's log
    (E1010, rightly), so it is three functions.
- **Bytes retained: held for idle, missed for requests and
  connections, and the miss is not lobo's.**

  | | trunk | predicted | measured (`162e8ee`) |
  |---|---|---|---|
  | keepalive, a request, N=1 | 2,060 B | under 4 B | **4.6 B** |
  | close, a connection, N=1 | 9,940 B | under 8 B | **70 B** |
  | keepalive / close, N=4 | 3,515 / 12,386 B | under 8 / under 16 B | **6.6 / 63 B** |
  | idle, no connection, 20 s | 344 kB | 0 kB | **0 kB** |
  | idle, 32 kept-alive, 20 s | 1,024 kB | 0 kB | **0 kB** |
  | RSS after 400,000 keepalive requests | 819 MB | under 8 MB | **6.0 MB** |
  | minor faults a request | 0.50 / 2.42 / 0.86 / 3.02 | under 0.01 | **0.0011 / 0.0094 / 0.0015 / 0.0158** |

  The residue is linear and is the runtime's two handle tables: 4.0
  bytes per `fs_open` and 52–63 bytes per accepted connection, each
  reproduced with no lobo code (wolf-lang#661). The close cell at
  four hands misses the fault prediction for the same reason.
- **Instructions: held on keepalive, better on close.** −0.4 % and
  −4.0 % (keepalive, N=1 and N=4), −7.8 % and −10.9 % (close),
  against ±4 %.
- **Parity.**

  | cell | predicted, kasumi | kasumi | predicted, the runner | the runner, three VMs |
  |---|---|---|---|---|
  | keepalive N=4 | 1.09–1.14x | **1.130x** [1.112, 1.139] | 1.10–1.17x: not met, or by a hair | **1.130x, 1.082x, 1.111x**: met on one of three |
  | close N=4 | 1.03–1.09x | **1.034x** [1.029, 1.042] | 1.04–1.11x: met | **1.104x, 1.062x, 1.075x**: met on two of three |
  | keepalive N=1 | 1.02–1.08x | 1.099x [1.095, 1.141] | 1.03–1.10x | (1.048x refused), 1.056x, 1.058x |
  | close N=1 | 0.90–1.00x | 0.929x [0.904, 0.938] | 0.92–1.03x | (0.940x refused), 0.914x, 0.897x |

  The close cells held on both hosts (the runner's verdict "met"
  held on two VMs of three). The keepalive cells held at four hands
  on both hosts (one runner VM read better than the band) and missed
  on kasumi at one hand (1.099x against 1.02–1.08x): ws56's ablation was taken on a lobo built with
  wolf-lang trunk, where s222 had already removed a tenth of the user
  instructions; at the pin they are still there and are the gap now.
  **The bar, plainly: connection-per-request is met on kasumi and on
  two of three runner VMs (the third reads 1.104x); keepalive is met
  on one runner VM of three and not on kasumi. Close is at the bar;
  keepalive is not yet.**
- **The gate: held, with the idle bound tightened and the capped
  rows widened.** Three hard rows on the plain server (512 KB,
  512 KB, and 128 KB for the idle row, not 512: trunk's idle row
  reads 320 KB, so 512 would not have been red). Red at trunk's code
  on both hosts by run id. The capped server's two rows carry a 4 MB
  bound, because a budgeted response is a proc and the runtime keeps
  about 280 bytes of every proc (wolf-lang#662, not predicted); they
  are red at trunk as well (81 MB, 65 MB). "A planted break (the
  `step` region removed) is red on the first two" was **wrong**: with
  the step's region removed the pass's region frees the same memory,
  and with the pass's removed the memo's does (the gate stays green,
  a megabyte more resident). No one region carries the property. The
  plant that is red is the loop body back in the ambient region (the
  memo's and the pass's regions both removed): 21 MB and 12 MB on the
  first two rows, the idle row green at 28–32 KB.
- **Item 4 (lobo#67): not taken, for want of a sound stat.** The
  keepalive cell is still above 1.10 on most readings, so the
  condition held; but at 0.2.26 a path stat is two calls (`fs_size`,
  `fs_modified_ms`) and answers neither the inode nor the kind, so a
  memo validated by it would save two calls of four and could serve
  a file replaced within the same millisecond at the same size, or
  treat a fifo as a file. s218's one-call `fs_stat` record (inode,
  kind, nanosecond times) is in wolf-lang trunk and arrives with the
  next pin. Left for ws58; the room is ws56's count (lobo#67: about
  1.05 µs of a request's CPU in the four calls), of a request that
  now costs 5.85 µs at four hands.
- **Item 5 (lobo#69): held.** Reproduced at the head (two loud
  failures in 7 s, one a hand); the fix was small and separable (one
  owner; the others read the installed chain's modification time
  once a second) and needed no new channel.
- **CI: held.** The gate before the fix, the rig case before its
  fix, each red by run id.

Corrections to §2: none of the inputs drifted. To §1: nothing touched
outside `~/lanes/ws57/` on either box; one throwaway branch
(`ws57-plant`, the planted break) was pushed to lobo's origin for its
CI run and deleted by this lane afterwards.

## 4. Evidence index

kasumi paths are under `~/lanes/ws57/`; nomad-1 paths under
`~/lanes/ws57/`.

| claim | artifact |
|---|---|
| the archives by digest, the oracle | `dl/digest-check.txt`, `toolchain-tc-0226.txt`, `nginx.sha256` (65595ac2…) |
| the prediction before the first change | commit `f3b6dbc` |
| growth and faults at trunk | `flt-trunk.log` ef89b5a9…, `idle-trunk.log` 6a4404c6… (release ebf2134b…, `build-trunk.log` b4afbf57…) |
| growth and faults after | `flt-head1.log` 3b6db73a…, `idle-head1.log` b0440442…, `lin-head1-ka.log` 81ef683d…, `lin-head1-close.log` 8423921a… (`162e8ee`, release 96553ee8…, `build-head1.log` e927dfea…) |
| the residue is the runtime's | `p13.log` d0b6d9d4… (the socket table), `probe/p14` (the file table), `probe/p12` (procs); wolf-lang#661, #662 |
| the memory gate red at trunk's code | CI run **38081745433** at `de83c54` (linux and macOS: 80 MB, 64 MB, 320 KB; the capped rows 81 MB, 65 MB); `nomad-1: ci-red-38081745433.log` c0b0d34f… |
| the memory gate green after | CI run 38086265653 at `ce44526` passes membudget on both hosts (it is red later, at the acme rig, by design); kasumi `g-ghead1.log` 37ff73b1… (22/22); the head's CI run in the PR body |
| the planted break (the memo's and the pass's regions removed) red in CI | CI run **38086881295** at `aa221ec` on the deleted branch `ws57-plant` (linux and macOS: 21 MB, 12 MB; idle 28–32 KB green); `ci-plant-38086881295.log` d11fdfed… |
| instructions and CPU a request | `prof-head1.log` 1a68fb6f…, `prof-trunk.log` 855e7c4f…, `prof-nginx.log` e53dde50… (and ws56's 48200551…); the first build's cost in `prof-work1.log` a2f38dc1…, `cg-work1-keepalive-1.log` 794fb05f…; after the pack `prof-work2.log` 35a9e1f9…, `cg-work2-keepalive-4.log` 72b3a36b… |
| parity, kasumi, VALID | `par-head1b.log` 9ce9ac44… (`162e8ee`, load 0.54); earlier valid sets on work builds `par-w1.log` 48f0a72f…, `par-w2.log` fcac38e2…; one REFUSED set (another lane's build mid-set) `par-head1.log` 53b4e102… |
| parity, the runner, three VALID sets | CI runs **38085780224** (`dbd68b1`), **38088570687** and **38089299844** (`91247eb`), each with `ref_tree=d1bf135`; logs `ci-parity-*.log` e25a29e2…, 00bde054…, bc99e7ca… |
| lobo#69 at the head before the fix | `a69-head-w2.log` 2e404553… (2 failures, one a hand) |
| lobo#69 red on the code before the fix | CI run **38086265653** at `ce44526` (acme, linux 3 red, macOS 2 red); `nomad-1: acme-red69.log` 18f911df… |
| lobo#69 green | `162e8ee` onward; `a69-head1.log` 9b144900… (1 failure, worker=1); the rig GREEN in `g-ghead1.log` |
| the wolf soundness gap, never leaned on | wolf-lang#660; `nomad-1: probe/d-p6`, `kasumi: probe/p6` |
| gauntlet GREEN at the code head, strict, the whole gauntlet under `taskset -c 0-3` | `g-ghead1.log` 37ff73b1… at `162e8ee`: exit 0; SigBlk 0x10000 / SigIgn 0x7; corpus 318/318, signal 21/21, prefork 38/38, membudget 22/22, resolver 9/9, acme GREEN; 0 SKIP lines (one line holds the word, a step's header) |
| CI green at the head on linux and macOS | in the PR body |

## 5. Done-when

- [x] Branch `ws57` on origin; PR open against `trunk`, unmerged, five
  sections by name, commit shas as bullets, a test checklist.
- [x] Item 1: a pass and a connection step each run in a region that
  is freed; idle growth zero.
- [x] Item 2: the memory gate hard, red at trunk by run id, green
  after; `docs/BUDGET.md` corrected.
- [x] Item 3: parity on the runner (three valid sets) and on a quiet
  kasumi, both shapes, 1 and 4 workers, against the same nginx, trunk
  beside it in every set.
- [x] Item 4: said why there is no sound footing at this pin; left for
  ws58.
- [x] Item 5: lobo#69 reproduced at the head and fixed, red first.
- [ ] CI green at the head sha on linux and macOS;
  `wolf/tools/lane-audit.sh lobo ws57 <PR>` run; kasumi worktrees
  removed and the build directories pruned (logs kept); no orphan
  pids. Nothing closed by this lane.
