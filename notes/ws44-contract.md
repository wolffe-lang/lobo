# ws44 — lobo at 0.2.19 / 0.1.42

Wave 52, lane ws44 (Opus). Written 2026-09-30 on lobo trunk `bfa9ad6`,
before any edit to the pin or to `src/`. The template is ws43
(`notes/ws43-contract.md`, PR #42, its row in `wave-50.md`). The wave-52
row says only "lobo at wolf 0.2.19". The orchestrator's brief adds four
conditions. Every site the pin names moves. The nginx differential and
every existing gate hold. Any new diagnostic or behaviour change is fixed
in lobo or reported, never waived. The oracle is lobo's own gauntlet at
the new pair, and the retention instrument (`tools/lobo-membudget`) is
read before and after. This file lives under `notes/`, not `docs/`,
because `tools/lobo-dist` ships every `docs/*.md` (lobo#34).

## 1. Forbidden, absolutely

- No `rm` outside `~/lanes/ws44/` on kasumi, this worktree and this lane's scratchpad. No deletion in any tree this lane did not create. The nginx oracle is *copied* from `~/lanes/ws38/lobo/tests/differential/bin/nginx` (read only, 1.30.4, `65595ac2…`, `~/lanes/ws44/nginx.sha256`).
- No `git add -A`. No edit to another lane's file. No `~/.claude`.
- No build on nomad-1. Every build and every gauntlet runs on kasumi under `~/lanes/ws44/`, with `CARGO_BUILD_JOBS=4`.
- No merge and no rebase-merge. No `2>/dev/null` on a checkout. No commit trailers of any kind.
- No "seen red" without a run id, sha, path or digest in the same paragraph.
- **The pin comes from the release archive by digest**, never from a clone or `~/.local/bin`. Every member is hashed by name (`_wolf` is the zsh completion script, `2d1e4801…` at every pin).
- Kill only this lane's own pids. Never a pattern, never a process group (pgid 861 on kasumi is tailscaled's). Jobs start under `setsid`.
- No `WOLF_MIDEND` flip-back. It has been owed since ws37 and belongs to its own lane. No index-store rewrite.
- No change to what lobo serves. The nginx differential is the check, and a moved byte is a red.
- Diagnostics are counted with `--error-limit=0`. **Searches use portable patterns.** On macOS, `git grep -E` never matches `\b`: `git grep -cE '\bfn main' -- src/main.lu` prints nothing. Each pattern is seen to match a planted line with the same engine before its zero is believed.

## 2. Inputs, verified (re-derived 2026-09-30 against origin and on kasumi)

All kasumi paths are under `~/lanes/ws44/`.

| input, as the brief states it | what origin says |
|---|---|
| lobo trunk `bfa9ad6a` | **holds**: `bfa9ad6` is `origin/trunk`, ws43's evidence-index commit. The trunk push run 36506248979 is green (8 m 22 s) |
| pins today | wolf 0.2.18 `ec56a08` / lupin 0.1.41 `0cfc0cf` / std `14f0ab2` (`wolf-toolchain.toml`) |
| wolf **0.2.19**, release **400208356** | tag `v0.2.19` → tag object `ba0b43a7` → commit **`c2401f05f37794a078d2acf62f837dad98e5950d`**. Release 400208356, `isDraft:false`, four assets, published 2026-09-30T16:02:58Z, `Latest`. The linux x86-64 archive digest is **`9f3873d80118681a583a7bc00ead8d00186d447d2584aea75bc65a81f8238c8e`**, and the file downloaded on kasumi hashes the same (`dl/digest-check.txt` asserts each digest is non-empty, then equal). Darwin arm64 is `8e9a9653…`. `--version`: `wolf 0.2.19 (wolfgang, pin c2401f0)` / `paired with lupin 0.1.42 (reference interpreter), pin ec56a08`. Highest glibc symbol is `GLIBC_2.34` (`dl/toolchain-0219.txt`) |
| lupin **0.1.42**, release **400022505** | tag `v0.1.42` → `4f299fdf` → commit **`8e2516dc47bf808512388cc687e070981d331d98`**. Release 400022505, `isDraft:false`, five assets (four archives plus a bare `lupin.exe`, the same shape as 0.1.41). The linux x86-64 digest is **`9856335aacbb26d22bd3fde867f28238c6ffde98e5d9fc15ecdedf4103998ab6`**, which matches wolf's CHANGELOG (`9856335a…`) and kasumi. Darwin arm64 is `756d6498…`. `--version`: `lupin 0.1.42 (wolf-interp, reference interpreter at pin ec56a08)`. glibc floor `GLIBC_2.34` |
| members that move, by name (linux x86-64) | `wolf` a9556245… → **3821bfaa…**; `libwolf_rt.a` 5360ecd6… → **f7e7236d…**; `wolf-cimport-worker` b2525d00… → **65498b6a…**; `lupin` c5a65edf… → **03f4a710…**. `wolf.1` and `README.md` move too. `_wolf` (2d1e4801…), `wolf.bash`, `wolf.fish`, `LICENSE` and `LICENSE-EXCEPTION` do not move (`dl/toolchain-0218.txt` beside `dl/toolchain-0219.txt`). 0.2.18's members reproduce ws43's pin note byte for byte |
| pairing | **pairing gap zero**: 0.2.19 declares lupin 0.1.42. **The lane gap closes from two releases to one**: lupin 0.1.42's conformance pin is `ec56a08` = v0.2.18. So 0.2.19's EG2, #472 and header-read rulings are wolf-side at lupin's pin. lupin 0.1.42 carries their lupin halves (wolf-interp#143–#146, #149, #151, #152), per the CHANGELOG |
| std `14f0ab2`, re-derived against 0.2.19 **before this section was written (B151)** | `14f0ab2` is **still** wolf-std's `origin/trunk`. No newer tree exists, so the only question is whether this one holds at 0.2.19. **Measured:** trunk's source built against it on both tiers with `--error-limit=0` (`probe/build-trunksrc-0219-{debug,release}.log`). Both exit 0 with 0 errors and 0 warnings; 0.2.18 also gives 0 and 0 (`probe/summary.txt`). The 0.2.18 release binary is `932b158d…`, which equals ws43's bump binary, so the probe reproduces ws43. The 0.2.19 release binary is `f4520ebe…` (`probe/binaries.sha256`). The std pin holds for the std modules lobo imports |
| what 0.2.19 **newly refuses** | **Nothing in `src/`**: zero diagnostics above. The CHANGELOG narrows exactly one thing. Under `--deny-warnings`, #464's shape now reports E1001 at mem, where it used to report a promoted W1002 at resolve (#469). Both are rejects. lobo's build does not pass `--deny-warnings`, and `tools/lobo-corpus` fails any non-empty warnings array itself. **The probe fires**: `plant-summary.txt`, `plant-dw464`, gives 0.2.18 `W1002=3 E1001=0` and 0.2.19 `E1001=2 W1002=0`, exit 2 on both |
| what 0.2.19 **newly accepts**: EG2 element claims (eg02), 1(c) under a claim (eg02b, #472), header reads beside a moved element (s185, #474) | **No lobo site waits on any of them.** Searched with portable patterns over the 160 `src/`/`tests/` `.lu` files, comment lines excluded. There are **0** element claims (`mut x[…]`) and **0** two-field claims in one call. There are 83 single field claims: 75 receivers like `(mut t.kinds).push(…)`, and 8 one-claim arguments like `tls.sess_write(mut cn.sess, body)`, each beside non-`mut` arguments. There are **0** `move`, **0** element `take`, **0** `] = take`, **0** `Map[` and **0** `Pool`. Every pattern matched a planted line with the same engine first. **The compiler sees each shape**, planted into a scratch copy of `main.lu` (`plant-summary.txt`). `plant-eg2` is E1002 at 0.2.18 and exit 0 at 0.2.19. `plant-m1c`, `bump(mut xs[0], xs.len)`, is E1002 then 0. `plant-hdr`, `xs.count()` after `move xs[0]`, is E1001 then 0 |
| #470 (release-tier ICE, fixed) | **Cannot reach lobo.** The CHANGELOG's own witness, standalone (`w470/summary.txt`): 0.2.18 `--release` **ICEs with the mid-end on** and prints `2 12` **with `WOLF_MIDEND=0`**. 0.2.19 prints `2 12` both ways. lobo's release build is `WOLF_MIDEND=0` (gauntlet, dist, CI), and lobo has no call with two `mut` field arguments. The same shape planted as an **uncalled** function in `main.lu` did **not** ICE at 0.2.18 even with the mid-end on (`plant-ice470`). A dead function is never inlined, so that plant is not evidence, and the standalone witness is |
| issues the pin notes cite | wolf-lang#469, #470, #471, #472 and #474 are CLOSED (2026-09-29/30). wolf-interp#149 is CLOSED. #466, #476, #477 and #479 are OPEN. #476 is a soundness gap in the compiler under a `mut` element claim, which lobo does not make. #417 and #426 are OPEN, so `sendfile` and the range seek stay "at this pin". #446 is OPEN |
| retention at trunk (0.2.18 pair), the **before** | Five of five runs give **19 KB/req plain and 20 through the capped proc** (`instr-trunk/`, binary `932b158d…`). Plain round B is 7952–7956 KB and cap round B 8088–8104. **The access-log variant** (ws42's scratch sed, 900 log lines per run, never committed) gives **24 KB/req, round B 9680–9684** (`instr-trunk-acc/`). That is ws43's after, within 8 KB |
| open lobo issues | #32–#34 and #36–#38. None names 0.2.19 or any issue the release fixed |
| a stale-looking helper found on the way | `src/main.lu` `replace_int`/`replace_str` rebuild a list "(index assignment is a one-lane shape…)". It came from ws16 (`f569e55`, 2026-09-03) and predates 0.2.17's index-store work. 0.2.19 does not move it. It is **named, not changed**: a rewrite is a serving-path change outside a pin lane (§1) |

## 3. Prediction, committed before the bump and before any gauntlet or retention measurement at 0.2.19

**P1: the bump is stamps only.** The source motion at 0.2.19 is the pin
file, the **14 `.wolfi`** toolchain stamps (13 modules plus root,
`toolchain 0.2.18` → `0.2.19`, **no `export_hash`/`pkg_hash` line
moves**), and **two** `src/shell/shell.lu` constants
(`toolchain_version`, `toolchain_pin`) plus the `version_report` doc
line. `std_rev` does not move. The compiler needs zero source edits.
**Falsified** by any hash line moving, by any other file needing an
edit, or by `lobo-stamp --check` asking for a third constant.

**P2: the gauntlet is GREEN at the bump, with 299/299 lane-runs.** That
includes the corpus's lupin lane at 0.1.42, which now traps whole-read
methods on a partly moved container and reads `.len` as a member. lobo
moves nothing, so neither can fire. **Falsified** by any red row. A red
row on a `tests/` file is named by file and diagnostic, then fixed or
reported.

**P3: nothing to revert.** The release unblocks no lobo site (§2). The
lane ends with zero source edits beyond P1's stamps. **Falsified** by
any site the gauntlet or a reviewer shows was spelled around a shape
0.2.19 now accepts.

**P4: retention at 0.2.19.** On the unmodified instrument, five runs:
plain **19 KB/req** and cap **20**, with plain round B within
**±150 KB** of 7956 and cap round B within ±150 KB of 8096. On the
access-log variant: **24 KB/req**, round B within ±150 KB of 9680. The
#470 fix changes inlining only with the mid-end on, and lobo builds
with it off. **Falsified** by a ratchet line other than 19/20/24, or by
any round-B shift over 150 KB.

**P5: the binary moves, the bytes served do not.** The 0.2.19 release
build is not byte-identical to 0.2.18's (`f4520ebe…` against
`932b158d…`). Every differential row still matches. CI at the head is
green in 6 to 10 minutes; a green under 60 s means the token lapsed.

## 4. Evidence index (filled in at the close)

All kasumi paths are under `~/lanes/ws44/`. Logs are kept; build trees are pruned.

| claim | artifact |
|---|---|
| archives by digest | `dl/digests.txt` and `dl/digest-check.txt` (each asserted non-empty, then equal to the release asset's digest). wolf 0.2.19 is `9f3873d8…` (release 400208356) and lupin 0.1.42 `9856335a…` (400022505). For the before: 0.2.18 `da027bf9…` and 0.1.41 `18848901…`. Members are hashed by name in `dl/toolchain-0219.txt` and `dl/toolchain-0218.txt`; the restaged ones are in `instr-*/toolchain.txt` |
| std pin holds at 0.2.19 (B151) | `probe/build-trunksrc-0219-{debug,release}.log`: `build-exit=0`, 0 errors, 0 warnings, `--error-limit=0`. Also `probe/summary.txt`, and the binaries in `probe/binaries.sha256` (the 0.2.18 release build `932b158d…` equals ws43's bump binary) |
| newly refused in `src/`: nothing, and the probe fires | `probe/build-trunksrc-0219-*.log` (0 diagnostics). `plant-summary.txt`, `plant-dw464`: 0.2.18 `W1002=3`, 0.2.19 `E1001=2`, both exit 2 under `--deny-warnings`. Logs in `plant/logs/`, script `plant.sh` |
| newly accepted: nothing waiting, and the probe fires | `plant-summary.txt`: `plant-eg2`, `plant-m1c` (E1002 → exit 0) and `plant-hdr` (E1001 → exit 0), each 0.2.18 → 0.2.19. The portable-pattern counts are in §2, each seen to match a planted line. `git grep -cE '\bfn main' -- src/main.lu` prints nothing on macOS, so `\b` is dark there |
| #470 cannot reach lobo | `w470/summary.txt`: 0.2.18 `midend-on build-exit=2 ICE=1`, `midend-off … out=[2 12]`; 0.2.19 `[2 12]` both ways. The logs are `w470/02{18,19}-{on,off}.log` |
| newly refused in `tests/`: nothing | `gauntlet-bump.log`, `gauntlet-head.log` and `gauntlet-final.log`: `corpus: 299/299 lane-runs green` |
| retention before (trunk `bfa9ad6`, 0.2.18) | `instr-trunk/`: 19/20 KB/req, round B 7952–7956 / 8088–8104, binary `932b158d…`. `instr-trunk-acc/`: 24 KB/req, round B 9680–9684, 900 lines per run |
| `.wolfi` stamps only, no hash moves | `wolfi-bump.diff` (14 `toolchain` lines, 0 `export_hash`/`pkg_hash` lines) and `interface-emit.log` (`emit-exit=0`) = commit `358d1ca` |
| gauntlet GREEN at the bump | `gauntlet-bump.log` at `358d1ca` (`gauntlet-bump.head`): exit 0, 258 s, 299/299 lane-runs, differential 22/22, proxy 8/8, control 9/9, signal 21/21 |
| retention after (bump `358d1ca`, 0.2.19) | `instr-bump/`: 19/20 KB/req, round B 7952–7964 / 8096–8160, binary `46565129…`. `instr-bump-acc/`: 24 KB/req, round B 9680 |
| the first head gauntlet RED, and why | `gauntlet-head-masked.log` at `68fddf4`: `lobo-signal: RED — 1 of 21`, `gauntlet-exit=1`, after `kill -QUIT` pended for 5 min. `hang-head1/state.txt` shows `ShdPnd 0x4`; `hang-head1/per-task-sigblk.txt` shows all 19 threads at `SigBlk 0x6`; `hang-head1/ancestors-sig.txt` shows the launcher `head-run.sh` at `SigBlk 0x10006`. The only pid killed was the lane's own hung `lobo-release` 2259572 |
| the mask, not the compiler | `sigctl/summary.txt`: 0.2.18 and 0.2.19 give `clean exit=0 … 21/21` and `blocked exit=124 quit=0`, with logs in `sigctl/signal-02{18,19}-{clean,blocked}.log`. Filed as **wolf-lang#483** |
| gauntlet GREEN at the head (clean mask) | `gauntlet-head.log` at `68fddf4` (`gauntlet-head.mask`: `SigBlk 0x10000`, SIGCHLD only): exit 0, 257 s, 299/299, signal 21/21, `lobo-stamp: ok` |
| gauntlet GREEN at the last code commit | `gauntlet-final.log` at `eb8c697` (`gauntlet-final.head`, `gauntlet-final.mask` SIGCHLD only): exit 0, 244 s, 299/299, differential 22/22, proxy 8/8, control 9/9, signal 21/21, `lobo-stamp: ok` |
| CI at the head | the PR's run, cited in the PR body and the lane report |

### §2 drift and corrections found by the lane

- The brief's inputs all held: `bfa9ad6`, release 400208356 and release 400022505, with lupin 0.1.42's pin at `ec56a08` as the CHANGELOG says. **The lane gap is one release, not two.**
- **`\b` in `git grep -E` is dark on macOS.** ws43's §4 cites `git grep -nE` with `\bmove [a-z_]` and `\bPool\b`. If those ran on this Mac, they could not match. Re-run portably at `bfa9ad6`, both are still 0, so ws43's conclusion stands and only its search was unsound.
- `plant-ice470` (the #470 shape as an **uncalled** function in `main.lu`) did not ICE at 0.2.18 even with the mid-end on. A dead function is never inlined, so that plant cannot fire. The standalone witness `w470/` is the evidence.
- The lane's own slip: one scratch file was written to and removed from `/tmp` on nomad-1 (a grep fixture, `/tmp/ws44-fire.txt`), outside the lane's namespace. Nothing else was touched, and later fixtures went to the scratchpad.

## 5. Done-when

- [ ] Branch `ws44` on origin; PR open against `trunk`, **unmerged**.
- [ ] CI green at the head sha, read with `gh run view` (never `watch` without `--interval 60`), on a run that acquired the toolchain and ran the gauntlet (6 minutes or more).
- [ ] The pin moves in its own commit; the shell constants in their own; `.wolfi` in its own `interface(…)` commit.
- [ ] Anything 0.2.19 newly refuses or newly accepts is named by file, or shown to be zero by a search that was seen to fire.
- [ ] Retention before and after, by path, on the unmodified instrument and on the access-log variant.
- [ ] The gauntlet GREEN at the head on kasumi, by log path.
- [ ] §2 drift and §3's verdicts reported; the CHANGELOG entry carries them.
- [ ] The worktree is gone, the kasumi build dirs are pruned (logs kept), and no orphans remain.
