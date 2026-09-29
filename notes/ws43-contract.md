# ws43 — lobo at 0.2.18 / 0.1.41

Wave 50, lane ws43 (Opus). Written 2026-09-28 on lobo trunk `8e9aaab`,
before any edit to the pin or to `src/`. The template is ws42
(`notes/ws42-contract.md`, its row in `wave-48.md`). The wave-50 row
asks for three things: the pin at the pair with the std pin re-derived
first, anything the release unblocks named, and retention before and
after. One oracle: lobo's own gauntlet at the new pair, with the
retention instrument (`tools/lobo-membudget`) read before and after.
This file lives under `notes/`, not `docs/`, because `tools/lobo-dist`
ships every `docs/*.md` (lobo#34).

## 1. Forbidden, absolutely

- No `rm` outside `~/lanes/ws43/` on kasumi and this worktree. No deletion in any tree this lane did not create. The nginx oracle is *copied* from `~/lanes/ws38/lobo/tests/differential/bin/nginx` (read only, 1.30.4, `65595ac2…`).
- No `git add -A`. No edit to another lane's file. No `~/.claude`.
- No build on nomad-1. Every build and every gauntlet runs on kasumi under `~/lanes/ws43/` with `CARGO_BUILD_JOBS=4`.
- No merge, no rebase-merge. No `2>/dev/null` on a checkout.
- No "seen red" without a run id, sha, path or digest in the same paragraph.
- **The pin is taken from the release archive by digest**, never from a clone or `~/.local/bin`. Every member is hashed by name (`_wolf` is the zsh completion script, `2d1e4801…` at every pin).
- Kill only this lane's own pids. Never a pattern, never a process group (pgid 861 on kasumi is tailscaled's).
- No `WOLF_MIDEND` flip-back. It has been owed since ws37 and is its own lane. No index-store rewrite.
- No change to what lobo serves. The nginx differential is the check, and a moved byte is a red.
- Diagnostics are counted with `--error-limit=0` (ws42's lesson: the default stops printing at 25).

## 2. Inputs, verified (re-derived 2026-09-28 against origin and on kasumi)

All kasumi paths are under `~/lanes/ws43/`.

| input, as the row states it | what origin says |
|---|---|
| lobo trunk `8e9aaab` | **holds**: `8e9aaab` is `origin/trunk`, ws42's evidence-index commit. CI on trunk is green: push run 36277634150 (7 m 4 s) |
| pins today | wolf 0.2.17 `02afce8` / lupin 0.1.40 `54f85e6` / std `14f0ab2` (`wolf-toolchain.toml`) |
| wolf **0.2.18** `ec56a08f`, release 397723077 | tag `v0.2.18` → tag object `d9732fbe` → commit **`ec56a08f04ff318ea659fd58683f7ae4f22dc7a5`**. Release **397723077**, `isDraft:false`, four assets, published 2026-09-27T16:38:47Z. The linux x86-64 archive digest is **`da027bf9da4c5a9dfa42c4ac6c7da3072ffce84922916650f024af83701e6bd4`**; the file downloaded on kasumi hashes the same (`dl/digests.txt`). Darwin arm64 is `b8f36045…`. `--version`: `wolf 0.2.18 (wolfgang, pin ec56a08)` / `paired with lupin 0.1.41 (reference interpreter), pin 93a5fe5`. Highest imported glibc symbol is `GLIBC_2.34` (`dl/toolchain-0218.txt`) |
| lupin **0.1.41** `0cfc0cf`, release 397709135 | tag `v0.1.41` → `0390e810` → commit **`0cfc0cfc89af5fd2aeb71d46c86742745b902869`**. Release **397709135**, `isDraft:false`, five assets (four archives plus a bare `lupin.exe`, the shape 0.1.40 had). The linux x86-64 digest is **`18848901a5202162c9d0c3001a62fa3ac57276d8c0fce9c2d4f43d8d50b4e8d4`**, identical on kasumi. Darwin arm64 is `2b8c14b0…`. `--version`: `lupin 0.1.41 (wolf-interp, reference interpreter at pin 93a5fe5)`. glibc floor `GLIBC_2.34` |
| members that move, by name (linux x86-64) | `wolf` 5cdd936e… → **a9556245…**; `libwolf_rt.a` c5384a5c… → **5360ecd6…**; `wolf-cimport-worker` 7031dd13… → **b2525d00…**; `lupin` 18d64444… → **c5a65edf…**. `wolf.1` and `README.md` move too. `_wolf` (2d1e4801…), `wolf.bash`, `wolf.fish`, `LICENSE` and `LICENSE-EXCEPTION` are identical (`dl/toolchain-0217.txt` beside `dl/toolchain-0218.txt`) |
| pairing | **gap zero**: 0.2.18 declares lupin 0.1.41. **Lane gap two releases now**: lupin 0.1.41's conformance pin is still `93a5fe5`, which is v0.2.16. 0.1.40 had the same pin, so the gap widened by one with this release. So #460, #464 and #452 are wolf-side at this pin. On lupin the change is its own is56 (wolf-interp#141): an element read traps on a moved element |
| std `14f0ab2`, re-derived against 0.2.18 **before this section was written (B151)** | `14f0ab2c6a64…` is **still** wolf-std trunk: the compare `14f0ab2...trunk` is ahead by 0. So no newer tree exists, and the question is only whether this one holds at 0.2.18. **Measured:** trunk's source built against it at 0.2.18 on both tiers, `--error-limit=0` (`probe/build-trunksrc-0218-{debug,release}.log`). Both exit 0, with 0 errors and 0 warnings. The same at 0.2.17 (`probe/build-trunksrc-0217-*.log`) is also 0 and 0. The 0.2.17 release binary is `2db67fbc…`, byte-identical to ws42's head binary, so the probe reproduces ws42. At 0.2.18 it is `25bc2353…` (`probe/binaries.sha256`). The std pin holds, and this covers only the std modules lobo imports |
| what 0.2.18 **newly refuses** (s184's #464 rule, eg01's #460 rule) | **Nothing in `src/`.** The release build above has zero diagnostics at 0.2.18. **The probe was shown to fire before this zero was believed.** Each witness was planted into a scratch copy of trunk's `src/main.lu` (`plant.sh`, `plant-summary.txt`). #464's `var t = move xs` in a `mut` parameter gives `E1001=1` and exit 2 at 0.2.18, and 0 errors with 1 warning (W1002) at 0.2.17. #460's `move xs[0]; xs[1] = [5]` then a read of `xs[0]` gives `E1001=1` at 0.2.18 and 0 at 0.2.17. `tests/` is not covered by this probe. The gauntlet's corpus step at the bump is its measurement (§3 P2) |
| what 0.2.18 **newly accepts** (element-granular moves for literal indices; R1/R3 over any `Copy` local, eg01b) | **No workaround in lobo waits on either.** Searched in `src/` and `tests/`. There are **0** `move` expressions and **0** `take <place>[…]` element moves. There are **0** index stores of a `take` (`] = take`) and **0** `Map[` types. There is no `Pool` or `handle`. The 21 `copy <place>[…]` sites are all copies out of a `read` parameter (the lend rule, ws37) or of an `int` element. None exists to dodge a sibling-element refusal, since there were no element moves to refuse. The 14 index stores in `src/` store `int`/`str` scalars through a local index, with no call on either side, so #452's order cannot move them |
| issues the pin notes cite | wolf-lang#460 CLOSED 2026-09-27, #464 CLOSED 2026-09-27, #452 CLOSED 2026-09-27; #446 OPEN (ruling owed); #417 and #426 OPEN, so `sendfile` and the range seek stay "at this pin" |
| retention at trunk (0.2.17 pair, lobo's instrument), the **before** | Five of five runs give **19 KB/req plain and 20 through the capped proc** (`instr-trunk/`, binary `2db67fbc…`). Plain round B is 7952–7956 KB and cap round B 8132–8160. **The access-log variant** (ws42's scratch sed, one `access_log` line, 900 log lines per run, never committed) gives **24 KB/req, round B 9680–9684 KB** (`instr-trunk-acc/`). That reproduces ws42's head figures to within 4 KB |
| open lobo issues | #32–#34 and #36–#38. None names 0.2.18, #460, #464 or #452 |

## 3. Prediction, committed before the bump and before any measurement at 0.2.18 beyond §2's build probe

**P1: the bump is stamps only.** The source motion at 0.2.18 is the
pin file, the **14 `.wolfi`** toolchain stamps (13 modules plus root,
`toolchain 0.2.17` → `0.2.18`, **no `export_hash`/`pkg_hash` line
moves**), and **two** `src/shell/shell.lu` constants
(`toolchain_version`, `toolchain_pin`) plus the `version_report` doc
line. `std_rev` does not move because the std pin does not. There are
zero source edits for the compiler's sake. **Falsified** by any hash
line moving, by any other file needing an edit, or by `lobo-stamp
--check` asking for a third constant.

**P2: the gauntlet is GREEN at the bump, with zero red rows.** That
includes the corpus's lupin lane at 0.1.41, which now traps a read of a
moved element, and its checked lane, whose store order moved under #452.
No lobo test reads a moved element and none stores through an index
with a call on each side. `tests/` holds nothing 0.2.18 newly refuses.
**Falsified** by any red row. A red row on a `tests/` file is the thing
the row asks me to name, and the report names it by file and diagnostic.

**P3: nothing to revert.** The release unblocks no lobo site (§2). The
lane ends with zero source edits beyond P1's stamps. **Falsified** by
any site the gauntlet or a reviewer shows was spelled around a shape
0.2.18 now accepts.

**P4: retention at 0.2.18.** On the unmodified instrument, five runs:
plain **19 KB/req** and cap **20**, with plain round B within
**±150 KB** of 7952 and cap round B within ±150 KB of 8160. On the
access-log variant: **24 KB/req**, round B within ±150 KB of 9680. The
release changes the rules that decide which programs compile, not what
an accepted program allocates. **Falsified** by a ratchet line other
than 19/20/24, or by any round-B shift over 150 KB.

**P5: the binary moves, the bytes served do not.** The 0.2.18 release
build is not byte-identical to 0.2.17's (`25bc2353…` against
`2db67fbc…`, because the compiler and runtime members moved). Every
differential row still matches. CI at the head is green in 6 to 9
minutes; a green under 60 s means the token lapsed.

## 4. Evidence index (filled in at the close)

## 5. Done-when

- [ ] Branch `ws43` on origin; PR open against `trunk`, **unmerged**.
- [ ] CI green at the head sha, read with `gh run view` (never `watch` without `--interval 60`), on a run that acquired the toolchain and ran the gauntlet (6 minutes or more).
- [ ] The pin moves in its own commit; the shell constants in their own; `.wolfi` in its own `interface(…)` commit.
- [ ] Anything 0.2.18 newly refuses or newly accepts is named by file, or shown to be zero by a search that was seen to fire.
- [ ] Retention before and after, by path, on the unmodified instrument and on the access-log variant.
- [ ] The gauntlet GREEN at the head on kasumi, by log path.
- [ ] §2 drift and §3's verdicts reported. The CHANGELOG entry carries them.
- [ ] The worktree is gone, the kasumi build dirs are pruned (logs kept), and no orphans remain.
