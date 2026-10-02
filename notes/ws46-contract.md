# ws46 — lobo at 0.2.20 / 0.1.43

Wave 52, lane ws46 (Fable). Written 2026-10-02 on lobo trunk `35f93a3`,
before any edit to the pin or to `src/`. The template is ws44
(`notes/ws44-contract.md`, PR #43, its row in `wave-52.md`). The wave-52
row says "lobo; also witnesses #483's runtime fix under a blocked mask".
The orchestrator's brief adds the conditions ws44 carried (every site
the pin names moves; the nginx differential and every existing gate
hold; retention re-measured; any new diagnostic or behaviour change
fixed in lobo or reported, never waived) and two specific to 0.2.20:
(1) wolf-lang#483 is fixed in the runtime (s188), so `lobo-signal`
must pass 21/21 under SIGINT+SIGQUIT blocked, with SigBlk recorded for
every signal run; (2) ruling #17 made reads after a `mut` argument
legal and s192 made a write of a `mut` receiver inside its own
arguments E1002, both measured clean on lobo upstream, so the
expectation is 0 new diagnostics, said out loud if it holds. The
oracle is lobo's own gauntlet at the new pair, and the retention
instrument (`tools/lobo-membudget`) is read before and after. This
file lives under `notes/`, not `docs/`, because `tools/lobo-dist` ships
every `docs/*.md` (lobo#34).

## 1. Forbidden, absolutely

- No `rm` outside `~/lanes/ws46/` on kasumi, this worktree
  (`/private/tmp/ws46`) and this lane's scratchpad. No deletion in any
  tree this lane did not create. The nginx oracle is *copied* from
  `~/lanes/ws38/lobo/tests/differential/bin/nginx` (read only, 1.30.4,
  `65595ac2…`, `~/lanes/ws46/nginx.sha256`). wolf-std is *read* from
  `~/lanes/ws38/wolf-std` (`git archive`, nothing written there).
- No `git add -A`. No edit to another lane's file. No `~/.claude`.
- No build on this Mac. Every build and every gauntlet runs on kasumi
  under `~/lanes/ws46/`, with `CARGO_BUILD_JOBS=4`. Build dirs are
  pruned the moment each item's evidence is written (kasumi `/home`
  has about 80 G free and three pin lanes share it); logs are kept.
- No merge and no rebase-merge. No `2>/dev/null` on a checkout. No
  commit trailers of any kind.
- No "seen red" without a run id, sha, path or digest in the same
  paragraph.
- **The pin comes from the release archive by digest**, never from a
  clone or `~/.local/bin`. Every member is hashed by name (`_wolf` is
  the zsh completion script, `2d1e4801…` at every pin).
- Kill only this lane's own pids. Never a pattern, never a process
  group (pgid 861 on kasumi is tailscaled's). Jobs start under
  `setsid` on kasumi (never `ssh -f`); on this Mac `nohup … & disown`,
  the launch verified by its first log line. Tars with
  `COPYFILE_DISABLE=1`.
- Waits print. A silent 600 s ends the lane. `gh run view`, never
  `gh run watch` without `--interval 60`.
- No `WOLF_MIDEND` flip-back. It has been owed since ws37 and belongs
  to its own lane. No index-store rewrite. No rewrite of
  `replace_int`/`replace_str` (named by ws44, not a pin lane's).
- No change to what lobo serves. The nginx differential is the check,
  and a moved byte is a red.
- Diagnostics are counted with `--error-limit=0`. **Searches use
  portable patterns**: on macOS `git grep -E` never matches `\b`
  (ws44). Each pattern is seen to match a planted line with the same
  engine before its zero is believed.
- The signal witness records the mask. Every `lobo-signal` run writes
  its launcher's `SigBlk`/`SigIgn` and, where it can be caught, the
  server's per-thread `SigBlk`, beside its log. A run whose mask is
  not recorded is not evidence.

## 2. Inputs, verified (re-derived 2026-10-02 against origin and on kasumi)

All kasumi paths are under `~/lanes/ws46/`.

| input, as the brief states it | what origin says |
|---|---|
| lobo trunk `35f93a35` | **holds**: `35f93a3` is `origin/trunk`, ws44's evidence-index commit (PR #43, merged). The trunk push run 36754425901 is green |
| pins today | wolf 0.2.19 `c2401f0` / lupin 0.1.42 `8e2516d` / std `14f0ab2` (`wolf-toolchain.toml`) |
| wolf **0.2.20**, release **401498582** | tag `v0.2.20` → tag object `db412213` → commit **`cdde128a30999652c9d70189664226b766a206f0`** (wolf-lang, "changelog: 0.2.20's pairing"). Release 401498582, `draft:false`, four assets, published 2026-10-02T03:16:00Z, `releases/latest`. The linux x86-64 archive digest is **`24855d5efae9515ac092f1db11613187838f018f017dc20416f70905fb816ce9`**, and the file downloaded on kasumi hashes the same (`dl/digest-check.txt` asserts each digest non-empty, then equal). Darwin arm64 is `c8a3f1a3…`. `--version`: `wolf 0.2.20 (wolfgang, pin cdde128)` / `paired with lupin 0.1.43 (reference interpreter), pin c2401f0`. Highest glibc symbol `GLIBC_2.34` (`dl/toolchain-0220.txt`) |
| lupin **0.1.43**, release **401010971** | tag `v0.1.43` → tag object `818ea0b0` → commit **`6d6cde553ba980527dcbebd4dbe81d63f898d658`** (wolf-interp, "release: lupin 0.1.43"). Release 401010971, `draft:false`, five assets (four archives plus a bare `lupin.exe`, the same shape as 0.1.42). The linux x86-64 digest is **`e957c8def153f507520a1f7f98f7f391cd43e731ee73c25c6a7bdef4d3090d48`**, which matches wolf's CHANGELOG (`e957c8de…`) and kasumi. Darwin arm64 is `24d3e8f1…`. `--version`: `lupin 0.1.43 (wolf-interp, reference interpreter at pin c2401f0)`. glibc floor `GLIBC_2.34` |
| members that move, by name (linux x86-64) | `wolf` 3821bfaa… → **3fb48c1d…**; `libwolf_rt.a` f7e7236d… → **c011f2ae…**; `wolf-cimport-worker` 65498b6a… → **13a61554…**; `lupin` 03f4a710… → **3b0702c0…**. `wolf.1` and `README.md` move too. `_wolf` (2d1e4801…), `wolf.bash` (29eb2d75…), `wolf.fish` (51a1b6a8…), `LICENSE` and `LICENSE-EXCEPTION` do not move (`dl/toolchain-0219.txt` beside `dl/toolchain-0220.txt`). 0.2.19's and 0.1.42's members reproduce ws44's pin note byte for byte |
| pairing | **pairing gap zero**: 0.2.20 declares lupin 0.1.43. **The lane gap stays one release**: lupin 0.1.43's conformance pin is `c2401f0` = v0.2.19. So 0.2.20's two-phase arguments, EG3, #486, #487 and #484 are wolf-side at lupin's pin, while 0.1.43 carries their lupin halves (wolf-interp#155, #157, #159, #160, #162, #164, all CLOSED) and the CHANGELOG says every 0.1.42 gate pin was dropped at the pairing |
| std `14f0ab2`, re-derived against 0.2.20 **before this section was written (B151)** | `14f0ab2` is **still** wolf-std's `origin/trunk` (`dl/std.txt`). No newer tree exists, so the only question is whether this one holds at 0.2.20. **Measured:** trunk's source built against it on both compilers and both tiers with `--error-limit=0` (`probe/build-trunksrc-02{19,20}-{debug,release}.log`). All four exit 0 with 0 errors and 0 warnings (`probe/summary.txt`). The 0.2.19 release binary is `46565129…`, which equals ws44's bump binary, so the probe reproduces ws44. The 0.2.20 release binary is `e468eb30…` (`probe/binaries.sha256`). The std pin holds for the std modules lobo imports |
| what 0.2.20 **newly refuses** | **Nothing in `src/`**: zero diagnostics above, on both tiers. The CHANGELOG lists four narrowings: a write, move, re-claim or lend of a `mut`-claimed place or `mut` receiver inside a later argument of the same call (E1002, s186/s192, #476/#487); a moded fn used as a value (refused by name, s188, #484); a call to a nested fn that omits its parameter's mode (E1007, s186, #466); a read of a local after `W { local }` moved it (E1001, s190, #486). Upstream measured lobo `35f93a35` clean on each (s186, s190, s192: 46 of 46 builds). This lane's own build agrees. The probe will be made to fire on each shape (§3 P3) |
| what 0.2.20 **newly accepts** | a direct read of a claimed place in a later argument (`grow(mut xs, xs.len)`, E1002 through 0.2.19, ruling #17), and two claims in one call through an offset or loop index (EG3). **lobo has nine two-phase read sites already in their natural spelling**: `src/main.lu:1013` (`ev_log(mut el, level, shell.ev_seq(body, el.seq))`) and eight in `src/acme/flow.lu` (`fail(mut fl, "…{fl.store}…")` at 655, 658, 661, 673, 742, 809 on one line; 668 and 765 across lines). They compiled at 0.2.19 because a read one call down or inside an interpolation was already legal; ruling #17 only widens the direct form. ws45 (the hoist lane) was stood down, so **there is no workaround to revert**. Searched with portable patterns over the 160 `src/`/`tests/` `.lu` files, comment lines excluded, each pattern seen to fire on a planted line first: **0** element claims (`mut x[…]`), **0** two-claim index pairs, **0** nested `fn`, **0** struct-literal field shorthands (the one match is a comment at `src/acme/acme.lu:661`), 7 one-line two-phase reads (the pattern cannot see the two multi-line ones). A search for a moded fn used as a value is not discriminating (`start`, `step`, `reload`, `fail` are also variable names); the 0.2.20 build with 0 diagnostics is the oracle there |
| #483 (an armed signal under an inherited blocked mask, s188) | **This is the behaviour change the lane witnesses.** lobo arms RELOAD, TERMINATE, QUIT (`shell.sig_mask()` = 7: SIGHUP, SIGTERM, SIGQUIT) plus the UPGRADE probe (SIGUSR2); it never arms SIGINT. ws44's 2×2 at 0.2.18 and 0.2.19 gave `blocked exit=124 quit=0` (`~/lanes/ws44/sigctl/summary.txt`). The fix unblocks exactly the armed signals on the runtime's `wolf-signal` thread and leaves every other signal's inherited mask alone |
| issues the pin notes cite | wolf-lang#476, #466, #479, #477, #481, #483, #484, #486, #487, #492, #494, #496, #503 are CLOSED. #490 (the windows twin of #483), #497, #498, #499 (await rulings), #511 (release-archive path), #417, #426 and #446 are OPEN, so `sendfile` and the range seek stay "at this pin". wolf-interp#163 is OPEN (a flow out of an argument list leaves the `mut` tag; lobo's corpus lupin lane is the measurement) |
| retention at trunk (0.2.19 pair), the **before** | Five of five runs give **19 KB/req plain and 20 through the capped proc** (`instr-trunk/`, binary `46565129…`, launcher mask `SigBlk 0x10000`). Plain round B is 7952–7964 KB and cap round B 8216–8284. **The access-log variant** (ws42's scratch sed, 900 log lines per run, never committed) gives **24 KB/req, round B 9680–9684** (`instr-trunk-acc/`). That is ws44's after, within 124 KB on the cap cell and 8 KB elsewhere |
| open lobo issues | #32–#34 and #36–#38. None names 0.2.20 or any issue the release fixed |
| the sites the pin names | `wolf-toolchain.toml` (two `rev`, two `version_line`, the notes), `src/shell/shell.lu` (`toolchain_version`, `toolchain_pin`, the `version_report` doc line), the 14 `.wolfi` toolchain stamps. `README.md:25` and `docs/GETTING-STARTED.md:41` quote a sample `-v` line at wolf 0.2.16; the pin does not name 0.2.16 and three pin lanes left it, so it is **named, not changed** (a `docs/` edit changes what `lobo-dist` ships) |
| the launcher's mask on kasumi | A job started by `setsid bash x.sh &` from `ssh kasumi "bash -lc …"` has `SigBlk 0x10000` (SIGCHLD) and `SigIgn 0x6` (SIGINT, SIGQUIT ignored: bash's rule for a background job in a non-interactive shell). An ignored disposition is replaced when the program installs a handler, so lobo's listen works under it, and ws44's gauntlets were green under the same mask. The blocked-mask runs set the mask explicitly through `pthread_sigmask` in a python wrapper, as wolf-lang#483 did |

## 3. Prediction, committed before the bump and before any gauntlet, signal witness, plant or retention measurement at 0.2.20

**P1: the bump is stamps only.** The source motion at 0.2.20 is the pin
file, the **14 `.wolfi`** toolchain stamps (13 modules plus root,
`toolchain 0.2.19` → `0.2.20`, **no `export_hash`/`pkg_hash` line
moves**), and **two** `src/shell/shell.lu` constants
(`toolchain_version` → `"0.2.20"`, `toolchain_pin` → `"cdde128"`) plus
the `version_report` doc line. `std_rev` does not move. The compiler
needs zero source edits. **Falsified** by any hash line moving, by any
other file needing an edit, or by `lobo-stamp --check` asking for a
third constant.

**P2: the gauntlet is GREEN at the bump, with 299/299 lane-runs.** That
includes the corpus's lupin lane at 0.1.43, which now traps a `mut`
receiver written inside its own arguments and runs the two-phase reads
#17 allows. lobo has no such write, so neither can fire. The
differential is 22/22, the proxy 8/8, the control 9/9, the signal
witness 21/21, `lobo-stamp: ok`. **Falsified** by any red row. A red
row on a `tests/` file is named by file and diagnostic, then fixed or
reported.

**P3: zero new diagnostics, and the probe fires both ways.** Six
shapes planted one at a time into a scratch copy of trunk's `main.lu`
and built with `--error-limit=0` on both compilers: `recv` (#487,
`(mut xs).push({ xs = [9]; 5 })`) is exit 0 at 0.2.19 and **E1002** at
0.2.20; `shorthand` (#486, `var w = W { xs }` then `xs.len`) is exit 0
then **E1001**; `fnval` (#484, `var g = f; g(xs)` against
`fn f(mut xs: List[int])`) is exit 0 then **refused** (an
`unsupported` by name); `nested` (#466, a nested `fn f(mut xs: …)`
called as `f(xs)`) is exit 0 then **E1007**; `twophase` (ruling #17,
`grow(mut xs, xs.len)`) is **E1002** at 0.2.19 and exit 0 at 0.2.20;
`eg3` (R1, `add2(mut xs[i], mut xs[i + 1])`) is **E1002** then exit 0.
Trunk's unplanted `src/` stays at 0 diagnostics on both tiers (§2).
**Falsified** by any plant that does not move between the compilers as
stated, or by any diagnostic on the unplanted tree.

**P4: nothing to revert.** The nine two-phase read sites were never
hoisted (ws45 stood down), so the lane ends with zero source edits
beyond P1's stamps. **Falsified** by any site the gauntlet or a
reviewer shows was spelled around a shape 0.2.20 now accepts.

**P5: retention at 0.2.20.** On the unmodified instrument, five runs:
plain **19 KB/req** and cap **20**, with plain round B within
**±150 KB** of 7956 and cap round B within ±150 KB of 8240. On the
access-log variant: **24 KB/req**, round B within ±150 KB of 9682.
Nothing in 0.2.20 touches lowering on lobo's path (s193's write-back
change needs a view-set receiver, which lobo does not declare; the
release notes say its emitted code is unchanged). **Falsified** by a
ratchet line other than 19/20/24, or by any round-B shift over 150 KB.

**P6: #483 is fixed for lobo, and the mask says why.** A 2×2 of build
× mask on trunk's source: the 0.2.19 build (`46565129…`) is 21/21
under a clean mask and **times out (124, `kill -QUIT` pending)** under
SIGINT+SIGQUIT blocked, as ws44 measured; the 0.2.20 build is 21/21
under a clean mask **and 21/21, exit 0, under SIGINT+SIGQUIT
blocked**. Caught mid-run on the blocked lane, the 0.2.20 server's
`wolf-signal` thread shows `SigBlk` with SIGQUIT (0x4) cleared and
SIGINT (0x2) still set, and every other thread still shows `0x6`; the
0.2.19 server shows `0x6` on every thread, `wolf-signal` included.
The head gauntlet, launched under the ordinary `setsid` mask, stays
21/21. **Falsified** by a timeout on the 0.2.20 blocked lane, by
SIGINT found unblocked anywhere (the fix would be wider than its
clause), or by a signal run whose mask was not recorded.

**P7: the binary moves, the bytes served do not.** The 0.2.20 release
build is not byte-identical to 0.2.19's (`e468eb30…` against
`46565129…`). Every differential row still matches. CI at the head is
green in 6 to 10 minutes; a green under 60 s means the token lapsed.

## 4. Evidence index (filled in at the close)

All kasumi paths are under `~/lanes/ws46/`. Logs are kept; build trees are pruned.

| claim | artifact |
|---|---|
| archives by digest | `dl/digests.txt` and `dl/digest-check.txt` (each asserted non-empty, then equal to the release asset's digest). wolf 0.2.20 is `24855d5e…` (release 401498582) and lupin 0.1.43 `e957c8de…` (401010971). For the before: 0.2.19 `9f3873d8…` and 0.1.42 `9856335a…`. Members are hashed by name in `dl/toolchain-0220.txt` and `dl/toolchain-0219.txt`; the restaged ones are in `instr-*/toolchain.txt`. The launcher's mask for the setup job is `setup.mask` |
| std pin holds at 0.2.20 (B151) | `probe/build-trunksrc-02{19,20}-{debug,release}.log`: `build-exit=0`, 0 errors, 0 warnings, `--error-limit=0`, on both compilers. `probe/summary.txt`; the binaries in `probe/binaries.sha256` (the 0.2.19 release build `46565129…` equals ws44's bump binary; the 0.2.20 one of trunk's source is `e468eb30…`). `dl/std.txt`: wolf-std `origin/trunk` is `14f0ab2` |
| newly refused in `src/`: nothing, and the probe fires | `probe/build-trunksrc-0220-*.log` (0 diagnostics). `plant-summary.txt` and `plant/logs/plant-{recv,shorthand,fnval,nested}-02{19,20}.log`: each `build-exit=0` at 0.2.19; at 0.2.20 `recv` E1002 (exit 2), `shorthand` E1001 (exit 2), `nested` E1007 (exit 2), `fnval` exit 4 ("cannot compile this yet — a fn with `mut` or `take` parameters used as a value"). Script `plant.sh` |
| newly accepted: nothing waiting, and the probe fires | `plant-summary.txt`: `twophase` and `eg3` are E1002 (exit 2) at 0.2.19 and exit 0 at 0.2.20. The portable-pattern counts are in §2, each seen to match a planted line in the lane's scratchpad fixture first. The nine two-phase read sites are in §2 by file and line |
| newly refused in `tests/`: nothing | `gauntlet-bump.log` and `gauntlet-head.log`: `corpus: 299/299 lane-runs green` |
| retention before (trunk `35f93a3`, 0.2.19) | `instr-trunk/`: 19/20 KB/req, round B 7952–7964 / 8216–8284, binary `46565129…`, `mask` SIGCHLD only. `instr-trunk-acc/`: 24 KB/req, round B 9680–9684, `run*.acclines` 900 each |
| `.wolfi` stamps only, no hash moves | `wolfi-bump.diff` (14 files, 14 `toolchain` lines each way, 0 `export_hash`/`pkg_hash` lines: `wolfi-bump.counts`) and `interface-emit.log` (`emit-exit=0`) = commit `9a04fc8` |
| gauntlet GREEN at the bump | `gauntlet-bump.log` at `9a04fc8` (`gauntlet-bump.head`, `gauntlet-bump.mask`: `SigBlk 0x10000`, `SigIgn 0x6`): exit 0, 414 s, 299/299 lane-runs, differential 22/22, proxy 8/8, control 9/9, logdiff 4/4, signal 21/21, membudget 17/17, TLS interop 8 cases 0 red, `lobo-stamp: ok` |
| retention after (bump `9a04fc8`, 0.2.20) | `instr-bump/`: 19/20 KB/req, round B 7952–7956 / 8160–8244, binary `6d0fca17…`. `instr-bump-acc/`: 24 KB/req, round B 9680–9688, 900 lines per run |
| #483 fixed for lobo, by build × mask | `sigctl/summary.txt`: `signal 0219 clean exit=0 … 21/21`, `signal 0219 blocked exit=124 quit=0`, `signal 0220 clean exit=0 … 21/21`, `signal 0220 blocked exit=0 quit=1 green=21/21`. Builds `sigctl/build-02{19,20}.log` (`46565129…`, `6d0fca17…`). Launcher mask per run in `sigctl/signal-*.mask` (`SigBlk 0x10000`, `SigIgn 0x6`); the server's per-thread masks in `sigctl/signal-*.threads`: the 0.2.19 blocked server has 18 threads at `0x6`, `wolf-signal` included; the 0.2.20 blocked server has 17 at `0x6` and `wolf-signal` at `0x2`; both clean servers are `0x0` throughout. Logs `sigctl/signal-*.log`. No server survived any run (`sigctl/*.pids`, nothing killed) |
| gauntlet GREEN at the head | `gauntlet-head.log` at `488c38f` (`gauntlet-head.head`, `gauntlet-head.mask` SIGCHLD only): exit 0, 367 s, 299/299, differential 22/22, proxy 8/8, control 9/9, signal 21/21, `lobo-stamp: ok`; binary `6d0fca17…` (`gauntlet-head.binary`), the third build of the bump source to give those bytes |
| CI at the head | PR #44, run 36965212091 at `488c38f`: success, 8 m 40 s, toolchain built from source at 0.2.20 / 0.1.43 (`wolf 0.2.20 (wolfgang, pin cdde128)`), 299/299 lane-runs, differential 22/22, proxy 8/8, signal 21/21, `lobo-stamp: ok`. The run at this index commit is cited in the PR body |

### §2 drift and corrections found by the lane

- The brief's inputs all held: `35f93a35`, release 401498582 and release 401010971, with lupin 0.1.43's pin at `c2401f0` = v0.2.19 as the CHANGELOG says. The lane gap stays one release.
- The brief says ws44 found "seven prose claims beyond the toml". The sites the pin names outside the toml are the three `shell.lu` lines and the 14 `.wolfi` stamps, and that is all ws44's commits moved; no seventh prose site exists in the tree. The only other version prose is the 0.2.16 sample `-v` line in `README.md` and `docs/GETTING-STARTED.md`, named in §2 and left.
- P7 named the trunk-source 0.2.20 binary `e468eb30…`; the bump's binary is `6d0fca17…` because the shell constants are in it. The prediction's substance (the binary moves, the served bytes do not) holds; the digit was the probe's, not the bump's.
- `timeout`(1) runs its command in its own process group and signals the group, so the 0.2.19 blocked-mask run reaped its own hung server on the way out (`sigctl/*.pids` show no survivor). ws44's orphan came from a different launcher. A lane that runs `lobo-signal` under a mask without `timeout` must still expect the orphan.
- Under `setsid bash … &` from a non-interactive `bash -lc`, SIGINT and SIGQUIT are *ignored* (`SigIgn 0x6`), not blocked. The clean-mask servers show `SigIgn 0x2`: lobo's handler replaced the inherited ignore on SIGQUIT, and SIGINT (never armed) stays ignored. That is why ws44's and this lane's ordinary gauntlets never saw #483; only an inherited *block* did.

## 5. Done-when

- [x] Branch `ws46` on origin; PR #44 open against `trunk`, **unmerged**.
- [x] CI green at the head sha, read with `gh run view` (never `watch` without `--interval 60`), on a run that acquired the toolchain and ran the gauntlet (6 minutes or more): 36965212091 at `488c38f`, 8 m 40 s; the index commit's run is in the PR body.
- [x] The pin moves in its own commit (`2a5f70e`); the shell constants in their own (`46382fc`); `.wolfi` in its own `interface(…)` commit (`9a04fc8`).
- [x] Anything 0.2.20 newly refuses or newly accepts is named by file, or shown to be zero by a search that was seen to fire and by a build at `--error-limit=0`.
- [x] `lobo-signal` 21/21 under SIGINT+SIGQUIT blocked on the 0.2.20 build, the 0.2.19 control red beside it, SigBlk recorded for every signal run.
- [x] Retention before and after, by path, on the unmodified instrument and on the access-log variant.
- [x] The gauntlet GREEN at the head on kasumi, by log path, with its mask recorded.
- [x] §2 drift and §3's verdicts reported; the CHANGELOG entry carries them.
- [x] The worktree is gone, the kasumi build dirs are pruned (logs kept), and no orphans remain (done after this commit; the lane report says so).
