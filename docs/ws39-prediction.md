# ws39 — the prediction, committed before the first edit

Wave 47, subwave 3: lobo 0.1.1. Written 2026-09-24 on lobo trunk
`fcee184`, pins wolf 0.2.16 (`93a5fe5`) / lupin 0.1.38 (`ba357aa`) /
std `070884c`, all unmoved. Nothing else in the tree has been edited
when this file is committed. The release commit, the README and the
release run land after it, and each prediction below is checked
against them in the ws39 report, right or wrong.

## §2 — the contract's inputs, re-derived against origin

| input, as the contract states it | what origin says |
|---|---|
| lobo trunk `fcee184` (ws38), CI run 36031630943 green | **holds** — `fcee18474f45…`; run 36031630943 `success`, 8m10s |
| 219 commits since `v0.1.0` | **holds** — `git log v0.1.0..fcee184` counts 219 |
| `v0.1.0` (2026-09-07) the only release | **drift** — the tag and the release are **2026-09-08** 15:15Z (the CHANGELOG heading says 09-07, the day the entry was written). And the releases API lists **two** v0.1.0 releases: the published one (id 384847504, four assets) and an **empty draft** (id 384850526, zero assets). The 0.1.0 run left a stray draft, #226's shape, and it is still there |
| zero open PRs; no lobo lane running | **holds** — `gh pr list` empty; `git worktree list` shows only the main checkout before this lane's |
| pins 0.2.16 `93a5fe50` / 0.1.38 `ba357aa` / std `070884c` | **holds** — `wolf-toolchain.toml` lines 141, 164, 243 |
| `release.yml`: `dist` on two hosts, `publish`, `smoke`; trigger `push: tags: ["v*"]` | **holds** — plus `workflow_dispatch` (the rehearsal) |
| version sites: `wolf.pkg:10`, `src/shell/shell.lu:61` and `:87` (`-v`/`-V` strings) | **drift** — `shell.lu:61` is `shell.version()`, the shell MODULE's interface version, one of **twelve** module `version()` constants that read `"0.1.0"` since August and are printed by `-V` as the module set; they are not the package version and `tools/lobo-stamp` does not hold them. The sites the stamp holds are `wolf.pkg:10`, `shell.lu:87` (`release_version`), `shell.lu:94` (`release_channel`, `"+dev"` → `""` at the release commit), `src/serve/serve.lu:292` (the wire token `lobo/X`, the `Server` header), and a `## X` CHANGELOG entry |
| README says linux keepalive 110.9× | **holds** (README lines 83–91) |
| the stall was fixed by ws24's single gathered write and ws35's head-as-`str` | **drift** — the stall was fixed by **ws23**'s one-buffer write (`b8f8e48`, lobo#3): keepalive 110.7× → 3.315× on the runner (run 34296065145). ws24's `net_writev` replaced ws23's body copy with a gathered write and ws35's `net_writev_head` took 288 B a response out of the region ledger; neither moved the stall, which was already gone |
| ledger (2026-09-11, ws33, the CI runner, 4 cpus): close 1.197×, keepalive 1.263×, N=1 close 0.994× | **drift on the third number** — ws33's set (run 34631705651, the FAST class) reads close 1.197× and keepalive 1.263× at N=4, and **N=1 close 1.146×**. The 0.994× is **ws31**'s N=1 close (run 34598621850, the SLOW class, same day). The ledger's own note: the classes are not comparable across sets |
| macOS: W8 met at ws26 | **holds** — 2026-09-09, nomad-1, three VALID sets, close 1.033×, keepalive 1.072× at N=18 |
| `docs/PROFILE.md` 63 µs vs 19 µs at 0.1.0 | **holds, with the pin named**: ws22, 2026-09-08, nomad-1 (macOS arm64), one process keepalive, lobo `0.1.0+dev` at **wolf 0.2.6 pin 398e5f5**, nginx 1.30.4 |
| tap `Formula/lobo.rb` at 0.1.0, two URLs + sha256s | **holds** (homebrew-wolf trunk `1fde9ff`) |
| AUR `lobo-bin` 0.1.0-1, remote head `4810a4d`, modified 2026-09-08 | **holds** — `git ls-remote` `4810a4d0…`; the RPC says 0.1.0-1, maintainer `espadon`, 2026-09-08 16:28:24Z |
| tl12 moving the AUR sources into `homebrew-wolf/aur/` | **holds** — PR #20 open on branch `tl12` (head `d98d950`), which carries `aur/lobo-bin/{PKGBUILD,.SRCINFO,lobo-bin.install}` still at 0.1.0-1. Not on trunk |
| kasumi has podman | **holds** — `/usr/bin/podman` |

Found beside the inputs, not in them:

- **README says "108 nginx directives are supported."** `docs/directives.md`
  has 108 ROWS: 46 implemented, 13 refused by name, 49 planned (45 /
  13 / 50 at v0.1.0). The sentence was false at 0.1.0 and is false now.
- **"the CVE corpus" is not a change since 0.1.0.** `tests/cve-corpus/`
  moved by one line (`nodelay: true` in a `Limits` literal, ws24). It
  is still in CI and still green at this pin; it is not new.
- `release.yml`'s header still says lobo is "the ONE PRIVATE repo in
  the org". It is public; an anonymous download of a v0.1.0 asset
  answers 200.

## §3 — predictions

**P1 — the CHANGELOG entry's section list.** `## 0.1.1 — 2026-09-24 —
<title>` with the 0.1.0 entry's shape: *Install*, *What changed since
0.1.0*, *Hosts, and what is still refused*, *`lobo -v`*. Under D65's
rule (user-visible only, the sprint id named):

- user-visible, named in the entry: **ws23** (the linux keepalive
  stall), **ws24** (`tcp_nodelay` served; one gathered write),
  **ws28** (retained bytes a request), **ws30** (one open a request),
  **ws32** (`listen … reuseport`), **ws33** and **ws34** (the route
  read once at load), **ws36** (lobo#23, a killed hand's socket file
  removed), **ws37** (the 0.2.16 pin), **ws38** (retention 19 KB/req).
  Ten lanes.
- not user-visible, not named: **ws22** (the bar and the tools),
  **ws25** (the leak gate and the profile leg; the fstat's gain is
  folded into the ws30 line), **ws26** (a measurement; W8's macOS
  verdict appears as a number, not as a change), **ws27** (a pin and
  a one-second cache the later router superseded), **ws29** (the
  signal forwarder: the operator sees the same signals answered),
  **ws31** (a pin and a profile), **ws35** (a pin and 288 B of region
  ledger, under every instrument's floor). Seven lanes.

Falsified if the finished entry names a lane from the second list as
a change a user can see, or leaves out one from the first.

**P2 — version sites.** The release commit moves **five stamp-held
sites** (`wolf.pkg:10`, `shell.lu:87`, `shell.lu:94` the channel,
`serve.lu:292`, the new `## 0.1.1` heading), **four test lines**
(`tests/shell/version_text.lu:16, :23, :35, :38`, which assert the
literal), and the docs that print a version: README 2 lines,
`docs/GETTING-STARTED.md` 3 lines, the doc comment at `shell.lu:460`.
**Not moved**, and named so: the twelve module `version()` constants,
the five fixture tokens in `tests/proxy/*` and
`tests/serve/budget_shapes.lu` (a caller-supplied string, not the
build's version), and every historical `0.1.0` in PARITY/PROFILE/
ARCHITECTURE, `release.yml`'s comment and the two tools' examples.
Falsified if `tools/lobo-stamp --check` needs a site not on the list,
or the gauntlet reds on a version literal not on it.

**P3 — the two archives.** 0.1.0 shipped 2,975,457 B (darwin) and
3,045,847 B (linux). The shipped text grew ~143 KB gzipped since then
(CHANGELOG, PROFILE, PARITY); the binary is a new compiler's.
Predicted: darwin **3.2 MB**, linux **3.3 MB**, each inside
**[2.8, 3.7] MB**. The pack is **byte-reproducible** on both legs
(`tools/lobo-dist` packs twice and compares). Falsified outside the
band, or by a digest mismatch in either dist log.

**P4 — the smoke.** The 0.1.0 run's smoke jobs took **4 s** (linux,
15:23:08–15:23:12Z) and **9 s** (macOS, 15:23:13–15:23:22Z), run
34243584257. Predicted at 0.1.1: linux **≤ 20 s**, macOS **≤ 30 s**,
both green, `-v` printing `lobo version: lobo/0.1.1 (built with wolf
0.2.16, pin 93a5fe5)` bare. The whole run near 0.1.0's 7m51s: dist
builds the pinned wolf from source on each host, and 0.2.16 is a
bigger compiler, so **8–15 min**.

**P5 — the draft.** Nothing in `release.yml` has changed since the
0.1.0 run, and that run left a second, empty draft release beside the
published one (id 384850526). Both dist legs call `gh release create
--draft` and a draft cannot be found by its tag, so the later leg
makes another. **Predicted: the v0.1.1 run leaves one empty draft
beside the published release**, and item 5's "zero drafts" fails
unless the workflow changes before the tag. This lane changes no
workflow (the contract: a fix is an issue), so the prediction goes to
the orchestrator before the tag.
