# ws70 — lobo 0.1.5

Crawl 54, lane ws70 (Opus). Written 2026-10-21 on lobo trunk `fc9f749`
(ws69's head, PR #107 merged), after the inputs below were re-derived
and before any change to the tree and before any packed binary was run.
The planning contract is `sprints/wws/39-lobo-015/ws70-lobo-015.md` in
`wolffe-lang/wolf` (planning trunk `b9ba84a`); its shape is ws65's
(`sprints/wws/34-lobo-014/ws65-lobo-014.md`, which keeps ws61's), the
checklist ws68's (`notes/ws68-contract.md` §6), the rules
`sprints/RULES.md`. **Ruling #105** (the maintainer, 2026-10-21): tag
0.1.5 with the `nobody` default.

One deliverable: lobo 0.1.5 prepared to the point where the
orchestrator audits, merges and tags. The lane does not tag, merge,
publish, push a package or file an issue.

## 1. Forbidden, absolutely

- No tag, no merge, no release published, no AUR push (the maintainer's,
  after the orchestrator's tag), no tap merge. No issue filed or
  closed. No attribution or co-author trailer in any commit or PR text.
- The upgrade notes open with the disclosure as written: "as root with
  no `user` line, the workers are no longer root: check this before you
  upgrade a root deployment".
- No source change beyond the version sites, the documents and what the
  release needs. A defect found is reported, not fixed (lobo#100, #106
  stay as they are). The pin does not move: wolf 0.2.33 (`85dab5d`),
  lupin 0.1.54 (`0e536e8`), wolf-std `cceda63`; 0.2.34 is ws71's.
- Nothing here deploys or serves anything public. lobo serves no site
  of ours; lupp.us is nginx on almanta (`sprints/HOSTING.md`). Never
  almanta, a Cloudflare tunnel or its configuration, DNS, or host ports
  8080 and 8088; never a listing of `cloudflared`'s arguments. Every
  server this lane starts on a host binds 127.0.0.1 on a port in
  18960–18979 or one the kernel chose; inside a throwaway container's
  own network namespace it may bind port 80. Each is stopped through
  its control endpoint or by its recorded pid.
- Root, privilege drops, descriptor limits, signals to hands: only for
  a process tree the test started, inside a rootless podman container
  on kasumi. Never root on a host. No builds on nomad-1.
- The toolchain is the pin's, from the release archives by digest, each
  digest read twice. Measurements under `taskset -c 0-3` with the
  server, the upstream and the client on disjoint cores (kasumi's cpu N
  and N+8 are one core's two threads: 0-3 / 4-5 / 6-7).
- kasumi: remote commands in `bash -c`, long jobs under `setsid -f` with
  a pid file, kill by recorded pid only. Scratch under `~/lanes/ws70/`
  only; no `rm` outside it and the lane's own clones; no `git add -A`;
  nothing under `~/.claude`; the branch asserted before every commit.
  No package installed on a host.
- Strict evidence (wolf-lang#571): `WOLF_PAIRING_REQUIRE_SIBLING=1`,
  stdout and stderr together, every SKIP line counted. lobo CI is
  tiered (tl28): the PR opens without the label, `tier pr` green, then
  `full-matrix` at the final head. `gh run watch` only with
  `--interval 60`. If the harness refuses an action, stop and report.

## 2. Inputs, verified (2026-10-21, about 18:30Z)

| input | what was found |
|---|---|
| lobo trunk | `fc9f749d4302…` (ws69's notes, PR #107 merged 2026-10-20 23:13Z); origin has nothing later. Stamp `lobo/0.1.4+dev (built with wolf 0.2.33, pin 85dab5d)`, std `cceda63` |
| v0.1.4 | tag on `570e2a95…`, release 412342014 (published 2026-10-14 04:53Z, not a draft), four assets read twice through the API: linux 3,850,272 B `16a5b0ca…`, macOS 3,776,230 B `f426e83b…`, sidecars 109 and 105 B. Five releases, no draft (`v0.1.0`–`v0.1.4`) |
| since v0.1.4 | **117 commits, exactly the commits of six pull requests** (the sets compared both ways): #89 the `+dev` flip (1), #93 ws66 (16), #97 tl28 (9), #98 ws67 (23), #103 ws68 (40), #107 ws69 (28) |
| the 0.1.5 entry | `## 0.1.5 — unreleased — …` written by ws68 and ws69: a "Not released" paragraph; Upgrading from 0.1.4 (the disclosure first, then four smaller changes, then 0.1.4's upgrade path in one sentence); What changed since 0.1.4 (eight items, ws66–ws69, each named); Against nginx ("not re-taken for 0.1.5 yet"; ws66's runner set 1.031x / 0.949x); The hosts, and what is still known wrong or limited (#101, #102, the https residue, #82, #87, wolf-lang#804, #710, #671, lobo#72, #68). Every PR's user-visible change has its line; #89 and #97 (tl28's tiers) have none and need none |
| open lobo issues | #68, #72, #82, #87, #95, #100, #101, #102, #106, and the public records #78, #90, #91. No open pull request |
| wolf 0.2.33 | tag `v0.2.33` (annotated `56110e4f…`) → wolf-lang `85dab5d7e597…`; linux x86-64 archive `4f955e8d…` (80,128,936 B), macOS `9152dbd1…` (18,780,248 B), the API read twice. Staged on kasumi, `sha256sum -c` twice (`dl/digest-check.txt`): `wolf` 58e4ade4…, `libwolf_rt.a` 5321ce86…, `wolf-cimport-worker` 57c41e39…; `wolf 0.2.33 (wolfgang, pin 85dab5d)`, paired with lupin 0.1.54; the archive's `std/STD-REV` `cceda631…` — ws68's and ws69's bytes |
| lupin 0.1.54 | `175df238…` (2,971,403 B), twice; `lupin` a9856dd4… |
| the oracle, ab | nginx 1.30.4 `65595ac2…` and ApacheBench 2.3 `05f2f6d5…`, copied from ws69's lane, each checked twice |
| 0.1.4's binaries | the published linux archive staged by digest twice (and its sidecar `-c` twice): `lobo` 1d4a7b5e…, `lobo version: lobo/0.1.4 (built with wolf 0.2.29, pin 6ffe7c6)`, BUILD `source: 570e2a95… (tags: v0.1.4)`. **ws65's rehearsal (run 38500596150, at `842e558`, two doc commits before the tag) packed the same binaries as the tag run**: linux 1d4a7b5e…, macOS 6d9c1933… in both (re-downloaded and hashed here): the binary is reproducible across runners from one source tree; the archives differ by BUILD's line and the documents |
| trunk on kasumi | release tier at 0.2.33 / `cceda63` with the release archive's wolf: exit 0, **14,838,976 B** (`2c813713…`, `logs/build-trunk.log`); 0.1.4's binary is 14,157,584 B. gzip -9 of each: 3,998,945 and 3,502,383 B; the documents the archive carries gzip to about 345 KB at trunk (332 KB in 0.1.4's) |
| the release workflow | `release.yml` unchanged since 0.1.4 (`git log v0.1.4..` names no commit to it, `tools/lobo-dist`, `lobo-stamp`, `lobo-release-notes`, `lib-toolchain.sh`). It builds the pin from source as `ci.yml` does; `tools/lobo-dist` runs in every gauntlet, green at 0.2.33 in ws68's and ws69's runs. Its learner smoke runs the archive as the runner's user, so the macOS root `[warn]` (no drop on macOS at this pin) is seen nowhere today; `tools/lobo-user` skips by name off linux; `tests/config/user_directive.lu` holds the text only (`root_note` with `can_drop` false) |
| the warnings | printed once at a root start with no `user` line (`serve_main` and the master; never at `-t`): a host that cannot drop (macOS), `cert auto` (lobo#102), no account or group for `nobody` |
| the upgrade's mechanics | a reload fans `reload` out to the running hands (`fan_out`), which re-read in place: nothing is exec'd. A hand the master replaces later is exec'd from the path `os_exe()` gave at the master's start. `shell.worker_args` is the same at `v0.1.4` and trunk. A hand decides its own drop (`hands_drop` at `worker > 0`). `lobo control upgrade` answers "not implemented" |
| the doors | homebrew-wolf trunk `e2b5226` (r39's wolf 0.2.34 / lupin 0.1.55 commits on top): `Formula/lobo.rb` 0.1.4 with the published digests, its pin comment wolf 0.2.29 / `6ffe7c6`; `aur/lobo-bin` 0.1.4-1 (`PKGBUILD`, `.SRCINFO`, `lobo-bin.install`); `tools/lobo-fill-digests` (reads each digest three ways). AUR RPC: `lobo-bin` 0.1.4-1 (modified 2026-10-14 21:28Z); the AUR's `master` is `5fc9aca0…`. `doors-fresh` 39605369994 (today 13:08Z) is red on wolf 0.2.34 / lupin 0.1.55 trailing their releases (r39's, mid-flight); lobo's two rows read `ok` |
| ws69's baseline | the proxied table (`notes/ws69-contract.md` §3, kasumi, a quiet box): the head ÷ the pre-#81 tree px 0.82x, ab1 0.96x, ab32 1.06x (19,080 / 15,616 / 17,917 req/s; pre-#81 23,196 / 16,250 / 16,834), the rig `tput.sh` `e208754b…`, `tput-in.sh` `67df184f…`, `px69.py` `8efb62d3…`, `summ.py` `941b8f8a…` (copied here by digest). 0.1.4's exchange is the inline one, so ws69's pre-#81 column is the nearest thing to 0.1.4 at 0.2.33; 0.1.4 itself is built with 0.2.29 |
| kasumi | 16 cpus, load 5.6–8.6 at 18:30Z (other lanes), `/home` 24 GB free, podman 6.1.3 rootless |

## 3. Prediction

Each line carries what would show it wrong.

- **P1, the CHANGELOG entry.** `## 0.1.5 — <the final head's date> —`
  the subject line as ws68 and ws69 wrote it, the word "unreleased" and
  the "Not released" paragraph out, a short lead in its place (the
  sixth release; read the first section before upgrading a root
  deployment). Sections in this order: Upgrading from 0.1.4 (the
  disclosure paragraph unchanged, then the four smaller changes, then
  0.1.4's three numbered steps with this release's measured restart and
  reload); Install; `lobo -v`; What changed since 0.1.4 (as written);
  Against nginx (the release row from a runner VM beside `v0.1.4`, the
  proxied rows from kasumi); The hosts, and what is still known wrong
  or limited (as written, plus anything the upgrade proof finds). **No
  Security section**: nothing in 0.1.5 fixes a fault a client could trip
  that 0.1.4's notes did not already name (lobo#81 was in 0.1.4's known
  list). A finding that changes this goes to the report first.
- **P2, the archives.** linux **4.30–4.40 MB** (0.1.4: 3,850,272 B;
  +12–14 %), macOS **4.20–4.35 MB** (3,776,230 B); each packed twice,
  identical. The rehearsal's linux binary differs from kasumi's build of
  the same tree (the archive is unstripped and its debug information
  names the checkout's path; ws53's note); the tag run's binaries will
  equal the rehearsal's at the same source tree, as 0.1.4's did, and the
  tag's archives differ from the rehearsal's only by BUILD's `source:`
  line (`(tags: v0.1.5)`).
- **P3, the documents that move.** `CHANGELOG.md`; `README.md` (the
  `-v` line, stale at 0.2.29 since ws66, and the version note: 0.1.5,
  the root default first); `docs/GETTING-STARTED.md` (lines 41, 46,
  67); `docs/PARITY.md` (the release row). The stamp commit moves
  `src/wolf.pkg`, `shell.lu`'s two constants and its doc example,
  `serve.lu`'s wire token and four lines of `tests/shell/version_text.lu`;
  no `.wolfi` moves. Not the reel, not `docs/CAPABILITIES.md` or
  `docs/WORKERS.md` ("0.1.4's posture" stays true), and none of the
  "through 0.1.4" sentences.
- **P4, the release workflow.** No change for the 0.2.33 pin. **One
  addition**, the contract's macOS `[warn]`: the macOS learner smoke
  starts the archive's `lobo` as root (`sudo`, the hosted runner's) with
  the stock configuration and asserts one `[warn]` that names the
  missing drop, one root process, a 200, and `-s stop`. The rehearsal is
  green on the first dispatch: four jobs run (two dist, two smokes;
  create and publish skipped), 8–25 minutes a dist job (wolf from
  source), under 3 a smoke.
- **P5, the smoke against 0.1.4** (kasumi, the published 0.1.4 binary
  and the rehearsal's 0.1.5, release tier both):
  - resident size of one process after 400,000 static keepalive
    requests: 0.1.4 **4.5–4.9 MB** (ws65 read 4,688 kB), 0.1.5
    **4.6–5.2 MB**; growth under 1 B a request on both, and under 100 B
    a connection;
  - static requests a second at 4 workers and 32 clients, 0.1.5 ÷
    0.1.4: **0.95–1.05x** on both shapes on kasumi; on a runner VM
    (`parity=true`, `ref_tree=v0.1.4`) nginx ÷ 0.1.5 inside 1.10 —
    close 1.00–1.07x, keepalive 0.90–0.97x — and 0.1.5 ÷ 0.1.4
    0.97–1.03x;
  - proxied, ws69's rig and shapes, five alternating rounds, 0.1.5 ÷
    0.1.4: **px 0.70–0.90x, ab1 0.85–1.00x, ab32 1.00–1.15x** (ws69's
    head against the pre-#81 tree: 0.82, 0.96, 1.06; wider under load).
- **P6, the gates on the packed binaries** (kasumi, `taskset -c 0-3`,
  strict env): the archive smoke (digest, the host's tar, `-v` against
  BUILD, `-t`, the stock page byte-compared, `Server: lobo/0.1.5`,
  `-s stop`) green on the linux archive, and the macOS archive through
  the release workflow's smoke only (no run on nomad-1); the fourteen
  e2e tests that take `LOBO_BIN` (the limit tests
  `control_exhausted_e2e`, `worker_connections_e2e`,
  `start_at_limit_e2e`, `park_at_limit_e2e`, and the exchange's
  `client_abort_e2e`, `silent_upstream_e2e`, `exchange_drain_e2e`,
  `https_abort_e2e`, `pipelined_*`, `request_time_e2e`, …) green on
  native and checked against the packed binary; `tools/lobo-membudget`
  25/25 with the packed binary in place; `tools/lobo-user` 25/25 as
  root in podman against it, in `ubuntu:24.04` and in
  `archlinux:base-devel` with the pinned nginx beside it.
- **P7, the upgrade** (as root in a rootless podman
  `archlinux:base-devel` container, its own network namespace, the
  pinned nginx beside it; 0.1.4's published binary and the
  rehearsal's 0.1.5):
  - every configuration 0.1.4 shipped or tested (the archive's stock
    file, the `v0.1.4` tree's config corpus and reel, the whole-config
    blocks of the 0.1.4 archive's documents) that loads on 0.1.4 loads
    on 0.1.5 with the same exit, as a user; as root, a `user` line
    0.1.4 refused (`cannot drop privileges`) loads on 0.1.5 when the
    account exists — the only exit differences, and none of the shipped
    examples has a `user` line;
  - **a running 0.1.4 master, the binary replaced on disk under it**
    (`worker_processes 2`, the stock `control`): `-s reload` from the
    0.1.5 binary exits 0 (`reload complete (generation 2)
    workers=2/2`) and every answer after it still says `Server:
    lobo/0.1.4` (the hands re-read in place); `lobo control upgrade`
    exits 1, not implemented;
  - **a hand the master replaces in that window is the new binary** (it
    is exec'd from the path, and the arguments are the same at both
    versions): after one hand is put down by its pid, its replacement
    answers `Server: lobo/0.1.5` beside a 0.1.4 sibling. As root with no
    `user` line it drops itself to `nobody` while the 0.1.4 sibling stays
    root; the 0.1.4 master never gave the logs to `nobody`, and I expect
    the 0.1.5 hand to fail on them and the master to start it again and
    again until the restart. The line I am least sure of;
  - the documented restart (`-s stop`, then the new binary's start, a
    client every 20 ms): 0 or 1 failed requests, a gap of 20–60 ms;
    a download in flight at `-s stop` is cut short;
  - **the new default**: as root with no `user` line, 0.1.4 is one
    process `Uid: 0 0 0 0` and a root-only (0600) file answers 200;
    after the restart 0.1.5 is a master `Uid: 0 0 0 0` and one hand
    `Uid: 65534 ×4`, `Gid: 65534 ×4`, the same file **403** (the pinned
    nginx in the same container: 403), the log files `nobody:root`;
    `user root;` gives one root hand and 200; a reload of a root-only
    configuration is refused by the hand while the master says
    `complete … workers=0/1` (lobo#101);
  - **the `[warn]` paths**: as root with `cert auto` and no `user`
    line, one root process and one `[warn]` naming lobo#102; with no
    account named `nobody`, one root process and its `[warn]`; on macOS,
    the release smoke's step (P4).
- **P8, staged, not landed.** The homebrew-wolf PR (`lobo.rb` 0.1.5,
  its pin comment at wolf 0.2.33 / `85dab5d`, 64-zero digests): its
  `aur` and `doors` legs red by construction until
  `tools/lobo-fill-digests 0.1.5`. `aur/lobo-bin` 0.1.5-1: the
  version, the `.SRCINFO`, and a `post_upgrade` line pointing a root
  deployment at the new default; its container install proof green on
  the rehearsal's archive (`REHEARSAL-OK`) and red with the placeholder
  kept. The `+dev` flip on its own branch and PR: `lobo-stamp: ok`
  reads `lobo 0.1.5+dev`, nothing else moves.
