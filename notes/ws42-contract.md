# ws42 — lobo at 0.2.17, and the #449 workarounds come out

Wave 48, lane ws42 (Opus). Written 2026-09-26 on lobo trunk `3fbe943`,
before any edit to `src/`. The contract template is ws37's
(`wolf/sprints/lobo/ws37-the-pin-at-0216.md`) plus the wave-48 row.
One oracle: lobo's own gauntlet at the new pair, with the retention
instrument (`tools/lobo-membudget`) read before and after. This file
lives under `notes/`, not `docs/`, because `tools/lobo-dist` ships
every `docs/*.md` (lobo#34).

## 1. Forbidden, absolutely

- No `rm` outside `~/lanes/ws42/` on kasumi and this worktree; no deletion in any tree this lane did not create.
- No `git add -A`; no edit to another lane's file (the `docs/ws3*-prediction.md` files stay as written); no `~/.claude`.
- No build on nomad-1. Every build and every gauntlet runs on kasumi under `~/lanes/ws42/` with `CARGO_BUILD_JOBS=4`.
- No merge, no rebase-merge; no `2>/dev/null` on a checkout.
- No "seen red" without a run id, sha, path or digest in the same paragraph.
- **The pin is taken from the release archive by digest**, never from a clone or `~/.local/bin`, with every member hashed by name (`_wolf` is the zsh completion script and hashes `2d1e4801…` at every pin).
- Kill only this lane's own pids. Never a pattern, never a process group (pgid 861 on kasumi is tailscaled's).
- No index-store rewrite (wolf-lang#438 shipped in 0.2.17, but it is not this lane's item). No `WOLF_MIDEND` flip-back: it is owed since ws37 and is its own lane.
- No change to what lobo serves. The nginx differential is the check, and a moved byte is a red.

## 2. Inputs, verified (re-derived 2026-09-26 against origin)

| input, as the row states it | what origin says |
|---|---|
| lobo trunk `3fbe943` | **holds**: `3fbe943227c824c1be6263e1edd67d0f05d2a058`, ws41's last commit. Its CI on trunk is green: run 36093103080, 6 m 31 s |
| pins today | wolf 0.2.16 `93a5fe5` / lupin 0.1.38 `ba357aa` / std `070884c` (`wolf-toolchain.toml`) |
| wolf **0.2.17** | tag `v0.2.17` → tag object `4da2f151` → commit **`02afce84f05c7841856a10671b6d7924f79193cc`**; release **397045016**, `isDraft:false`, four assets. The linux x86-64 archive digest is `a95d0f0f8fe384fdb70047bb893c857573cc62dd10b2967ab7788fc9a8ce24ce` (the downloaded file on kasumi hashes the same). Darwin arm64 is `525c9143…`. `--version`: `wolf 0.2.17 (wolfgang, pin 02afce8)` / `paired with lupin 0.1.40 …, pin 93a5fe5`. Highest imported glibc symbol is `GLIBC_2.34` |
| lupin **0.1.40** | tag `v0.1.40` → `e9f76ec1` → commit **`54f85e694d4c03e5cd40bef461f85ca0ac373332`**; release **397033025**, `isDraft:false`, five assets. The linux x86-64 archive digest is `509929e67b7ae97463973d6bb7c61b9f93dc47a523957055def816c56fb23384`, identical on kasumi. Darwin arm64 is `197f1957…`. `--version`: `lupin 0.1.40 (wolf-interp, reference interpreter at pin 93a5fe5)` |
| members that move, by name (linux x86-64) | `wolf` b53b5328… → **5cdd936e…**; `libwolf_rt.a` c4c5f670… → **c5384a5c…**; `wolf-cimport-worker` cf2c47a9… → **7031dd13…**; `lupin` f202d47f… → **18d64444…**; `wolf.1` and `README.md` move too. `_wolf` (2d1e4801…), `wolf.bash`, `wolf.fish`, `LICENSE` and `LICENSE-EXCEPTION` are identical |
| pairing | **gap zero**: 0.2.17 declares lupin 0.1.40. **Lane gap one release**: lupin 0.1.40's conformance pin is `93a5fe5`, which is v0.2.16. So s178's #449 fix and s180's index-store rule are wolf-side at this pin, and lupin never refused #449's shape in the first place |
| std `14f0ab2`, re-derived against 0.2.17 **before this section was written (B151)** | `14f0ab2c6a64…` is wolf-std trunk (default branch `trunk`). The span `070884c..14f0ab2` is 12 commits. Under `std/` it touches **one file, `std/map/map.lu`** (B117's `remove`), and no module under `std/` `use`s `std.map`, so nothing lobo imports can reach it. **Measured:** trunk's source built at 0.2.17 with each std tree (`~/lanes/ws42/probe/build-trunksrc-0217-std{070884c,14f0ab2}.log`) exits 0 with zero diagnostics both times, and the two binaries are **byte-identical** (`d54ed342…`). wolf-std's own vendored binary pin at `14f0ab2` is 0.2.16 / 0.1.38 (`fbbc86c`), one release behind. No wolf-std commit pins 0.2.17 yet, so `14f0ab2` is the nearest trunk sha, and it holds |
| "the 16 #449 workaround sites" | **The 16 is a count of diagnostics, not of edits, and the contract's own sources disagree about it.** wolf-lang#449 (CLOSED 2026-09-24T07:15:53Z) and the ws37 CHANGELOG say **16** (main 5, serve 9, resolver 1, http 1). The issue comment spells serve's 9 as "six `send_err` … and four `return req_out`", which is 10. `wolf-toolchain.toml`'s `[wolf]` note says **"21 sites here"**. ws37's commits contain **nine workaround shapes**: four in `src/main.lu` where the message is chosen before one claim (`serve_main`'s signal word, `master_main`'s signal word, and `spawn_worker`'s two spawn handlers), plus five helpers rotated to take the `mut` parameter last (`ev_event` with 23 callers, `write_all` 10, `fill_req_acc` 1, `pending_drop` 1, `apply_segment` 2). The flagged lines (`send_err`, `req_out`) were never edited; they were the *inner* claims. **A tenth shape is not in any count: ws41's `put` in `src/serve/serve.lu`** (1407), which exists "so no handler arm holds a claim on `cn` (wolf-lang#449's leg)" and takes `mut cn` last. The lane reverts all ten shapes |
| `pass_accs` plain push (B156) | **holds**: `src/main.lu:2129`, `(mut pass_accs).push(AccRow { a: copy a2 })`. That is a deep `copy` of the record plus a plain push of a non-`Copy` temporary, so two copies per logged request, and only when an access output is configured. `a2` is read once more afterwards, by `note_served(mut counters, a2, admitted)` |
| retention at trunk (0.2.16 pair, lobo's instrument) | **19 KB/req plain, 20 through the capped proc, five of five runs** (`~/lanes/ws42/instr-trunk/`, binary `b8d8d98e…`). Plain round B retained 7952–7964 KB and cap round B 8096–8104 KB, so the spread is ±12 KB. **The instrument configures no access log, so the `pass_accs` push never fires under it.** A scratch variant (never committed) adds one `access_log` line to the plain server (`~/lanes/ws42/instr-trunk-acc/`, 900 log lines per run as expected) and reads **24 KB/req, round B 9916–9924 KB**. The access-log path therefore retains about 4.9 KB/req at trunk |
| open lobo issues | #32–#34 and #36–#38. None names #449 or `pass_accs` |

## 3. Prediction, committed before any edit or measurement at 0.2.17

**P1 — every reverted shape compiles at 0.2.17.** All ten shapes are
restored to their pre-#449 spelling: the message is claimed inside
the branch or arm, and the `mut` parameter goes back first on the six
helpers. The tree then builds at 0.2.17 with **zero** E1002. The same
reverted tree built with the **0.2.16** archive refuses with
**between 16 and 22 E1002 diagnostics**, every one of them on a line
inside a reverted shape's function. That count is the proof that each
revert is the shape #449 refused. **Falsified** by any E1002 at 0.2.17,
by fewer than 16 or more than 22 at 0.2.16, or by any 0.2.16
diagnostic outside the ten shapes. **Zero shapes are left**; if one has
to stay, the report says which and why.

**P2 — the bump itself moves no gauntlet row.** Before the revert, the
source motion at 0.2.17 is the pin file, the **14 `.wolfi`** toolchain
stamps (13 modules plus root) and **two** `src/shell/shell.lu`
constants. That is zero source edits for the compiler's sake, because
trunk builds unchanged (§2). The first full gauntlet at the new pair
is **GREEN with zero red rows**. The riskiest input is lupin 0.1.39's
change to `conform-run` path resolution (is55, `[os.fs.path]`),
because `tools/lobo-corpus` drives it from staged directories.
**Falsified** by any red row.

**P3 — retention at 0.2.17, before and after the revert.** On the
unmodified instrument, five runs each: plain **19 KB/req** and cap
**20**, with plain round B within **±150 KB** of trunk's 7952 and cap
round B within ±150 KB of 8100. The same holds after the #449 revert
and after the `pass_accs` change. Argument order and branch shape do
not allocate, and the instrument never reaches `pass_accs`.
**Falsified** by a ratchet line other than 19/20, or by a round-B
shift over 150 KB.

**P4 — `pass_accs` (B156).** The shape is to fold the counters first,
then `push(take AccRow { a: take a2 })`. No `copy`, and the push
moves. On the scratch access-log variant, plain round B **drops by 40
to 400 KB** from its value at the same pin before the change (0.1–1.0
KB/req). The ratchet line stays at 24 or reads 23. The copies are two
small list buffers per request; most of the access path's 4.9 KB/req
is the rendered line (#191), which this change does not touch.
**Falsified** by a drop under 40 KB (the copies were never retained)
or over 400 KB.

**P5 — the census.** Heap-reaching plain pushes in `src/` go from **1
to 0**. **Falsified** by any other plain push of a `List`/`Map`-bearing
element found by the same method (ws37's: element type of every
`.push(` in `src/`).

**P6 — served bytes.** None change. The gauntlet's nginx differential,
the proxy differential and the corpus rows are the check. CI at the
head is green in 6 to 9 minutes, and a green under 60 s means the
token lapsed.

## 4. Evidence index (filled in at the close)

## 5. Done-when

- [ ] Branch `ws42` on origin; PR open against `trunk`, **unmerged**.
- [ ] CI green at the head sha, read with `gh run view` (never `watch` without `--interval 60`), on a run that acquired the toolchain and ran the gauntlet (6 minutes or more).
- [ ] The pin moves in its own commit; `.wolfi` in its own `interface(…)` commit; each reverted shape in its own commit, each compiled at 0.2.17 before it is committed.
- [ ] The 0.2.16 red of the reverted tree cited by log path, with every diagnostic mapped to its shape.
- [ ] Retention before and after, by path, on the unmodified instrument and on the access-log variant.
- [ ] The gauntlet GREEN at the head on kasumi, by log path.
- [ ] §2 drift and §3's verdicts reported. The CHANGELOG entry carries them.
- [ ] The worktree is gone, the kasumi build dirs are pruned (logs kept), and no orphans remain.
