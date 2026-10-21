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

## 3. The prediction against the measurement

Measured on kasumi (16 cpus, load 1.1–6.9 while measuring; other lanes
beside it) and on GitHub's runners, the toolchains of §2; logs under
`kasumi:~/lanes/ws70/` (digests in §4). §3 above is as committed
(`ba42a59`). The release tree's `src/` is final at `f0d11c5` (the
stamp); every later commit is a workflow step or a document, so the
binaries measured (rehearsal 1, run 39654225786 at `4ce9b5b`) are the
release's: the later rehearsals' binaries are compared by digest in the
pull request.

- **P1 held.** The entry's sections in the predicted order; the
  disclosure paragraph unchanged; no Security section. Added beyond
  the prediction: the window (below) in the upgrade steps and in the
  known list.
- **P2 wrong on the sizes.** linux **3,992,984** B (`e4c19d0d…`), macOS
  **3,879,275** B (`a00c3ea2…`), each "packed twice, identical" (run
  39654225786); predicted 4.30–4.40 and 4.20–4.35 MB. The basis was
  kasumi's build, and the runner's binary is another binary: 14,636,104
  B against kasumi's 14,838,976 B, its sections in another order. ws61
  wrote this down for 0.1.3 (the release tier links with the host's C
  toolchain) and I did not use it. The rest held: rehearsal 2 (run
  39655459695, `09cd04e`) packed linux 3,992,992 B (`16b52252…`) and
  macOS 3,879,268 B (`d2571ae8…`), the archives differing by BUILD's
  source line; 0.1.4's rehearsal binaries equal its tag's (§2).
- **P3 held**, plus the release workflow (P4) and a ws70 lane entry in
  the CHANGELOG.
- **P4 held, with one bug of mine first.** No change for the pin. The
  macOS root step's first run (39654225786, job "learner smoke
  (aarch64-apple-darwin)") went red with no line printed: `pgrep -P`
  exits 1 with no children and `pipefail` ended the step at the
  assignment. Fixed (`09cd04e`). **Seen red on a plant**:
  `ws70-plant-macwarn` (`9f82bfb`: `src/` not printing the single
  process's root note, the release matrix cut to macOS), run
  **39655455898**, job 119420104974: `as root: pid 1032 runs as root
  with 0 child process(es)` then `the root start printed 0 copies of
  the cannot-drop [warn], wanted 1`. Green at the release tree in run
  39655459695 (job 119419003740): `lobo: [warn] running as root with no
  "user" directive: nginx would run its workers as nobody (its
  default), but this host cannot drop privileges …`, `as root: pid 1065
  runs as root with 0 child process(es)`, `-s stop`. Four jobs ran
  each time; dist 5–9 minutes (the rust cache), smoke under a minute.
- **P5 held.**
  - RSS of one process after 400,000 keepalive requests
    (`ev/rss.log`, two rounds each, ab on cpus 6-7): 0.1.4 **4,588**
    and **4,636** kB, 0.1.5 **4,740** and **4,664** kB; growth 0 B a
    request and 0 B a connection on both (the integer of 200 kB over
    400,000).
  - Static, four workers, 32 clients over two ab processes on cpus 6
    and 7, five rounds (`ev/tput-rel5.log`): keepalive 0.1.5 638,278,
    0.1.4 631,482 (**1.011x**), nginx 497,352; a connection per request
    125,781 / 127,672 (**0.985x**), nginx 126,742. On a runner VM (run
    **39656019826**, VALID): nginx ÷ 0.1.5 close **1.032x** [1.010,
    1.048], keepalive **0.933x** [0.928, 0.952], MET; 0.1.5 ÷ 0.1.4
    **1.003x** and **1.002x**; at one worker 0.734x / 0.813x and
    1.008x / 1.018x.
  - Proxied, ws69's rig, five rounds: px 0.1.5 16,605 (spread
    12,582–18,515), 0.1.4 21,649 — **0.767x**; ab1 15,758 / 16,457 —
    **0.958x** (nginx 16,603); ab32 17,761 / 16,766 — **1.059x**
    (nginx 17,844). 0.1.5's px spread is 36 %: its rounds 1 and 3 read
    12,582 and 15,185, the others 16,605–18,515.
- **P6 held** (`logs/gates-reh1.log`, the packed binary `0da8d84d…`,
  SigBlk `0x10000`, SigIgn `0x4`, 0 SKIP lines): the archive smoke;
  `corpus: 28/28 lane-runs green` over the fourteen `LOBO_BIN` tests
  on native and checked; `lobo-membudget` 25/25 (`flat, proxied`: 140
  KB over 2,000 proxied requests, bound 512); `lobo-user` 25/25 in
  `ubuntu:24.04` (the oracle does not run there: the measured rule)
  and 25/25 in `archlinux:base-devel`, where each default row read the
  pinned nginx's worker beside lobo's hand (`Uid: 65534 ×4|Gid: 65534
  ×4|Groups: 65534|`, `Groups: 1700 65534` with a group listing
  `nobody`, root with `user root;`).
- **P7, the upgrade** (`ev/upgrade-reh1.log`, `ev/upgrade-reh1-de.log`,
  `ev/confload.log`):
  - **Held**: as a user 45/45 configurations the same exit and text, 17
    loading on both; as root one exit difference
    (`corpus/crossplane-messy`: `user nobody;`, refused by 0.1.4, loads
    on 0.1.5) and four text differences (`user nginx;`: 0.1.4's `cannot
    drop privileges` became `getpwnam("nginx") failed`). None of the
    shipped examples has a `user` line.
  - **Held**: the 0.1.5 binary's `-s reload` to a running 0.1.4 answers
    `reload complete (generation 2)` (`workers=2/2` with two); every
    answer after it says `Server: lobo/0.1.4`, the processes'
    `/proc/<pid>/exe` read `… (deleted)`; `control upgrade` exit 1.
  - **Held**: the restart — 0 or 1 refused (A: 0 and 1 in two runs; B:
    1; C as root: 0), the first 0.1.5 answer within 20 ms of the
    start; the download in flight cut: **2,588,927 of 25,165,824 bytes,
    then end-of-stream**, in both runs.
  - **Half wrong — the window.** A hand put down while 0.1.5 is on
    disk is replaced by 0.1.5, as predicted (B: 1.2 s later; D, as
    root: about 4 s, the killed hand unreaped for 3 s). As a user it
    serves beside its 0.1.4 sibling (7 and 42 of 60 GETs in two runs).
    As root with no `user` line it drops itself to `Uid: 65534 ×4`
    beside a root 0.1.4 sibling — but it does **not** fail and loop: it
    **serves**, a root-only file answers **403** from it and **200**
    from the sibling (GET rounds: 4 / 60 / 0 of 60 to the new hand),
    and each of its access-log lines is dropped (`[warn] access log
    "/w/D/logs/access.log": dropped 1 line(s) (buffer overflow or
    unwritable path; 54 total) worker=1`): the logs are root's 0644,
    never given away by the 0.1.4 master. `status` shows `restarts=1
    pid=73` and nothing else amiss.
  - **Held**: the new default — 0.1.4 as root: one process `Uid: 0 0 0
    0`, the 0600 file 200, the logs `0:0`; 0.1.5 after the restart: a
    master `Uid: 0 0 0 0` and one hand `Uid: 65534 65534 65534 65534`,
    `Gid: 65534 …`, `Groups: 65534`, the file **403**, `access.log`
    and `error.log` `65534:0`. The pinned nginx in the same container,
    as root with no `user` line: worker `Uid: 65534 ×4`, the file 403.
    `user root;`: hand `Uid: 0 0 0 0`, 200. A reload of the
    configuration made 0600: `reload complete (generation 2)
    workers=0/1` (lobo#101, on the release binary).
  - **Held**: the warnings — `cert auto` as root (with a plaintext
    listener for its challenge; my first config had none and `-t`
    refused it by name): one root process and `[warn] running as root
    with no "user" directive and `cert auto`: … (a named delta,
    lobo#102)`; no account named `nobody`: one root process, the 0600
    file 200, `[warn] … no account named "nobody" in /etc/passwd: nginx
    would refuse to start here …`; macOS: P4.
- **P8 held.** The tap branch `ws70`: `924032f` (formula), `c02c39d`
  (`aur/lobo-bin` 0.1.5-1, zeros), `ef47d93` (`post_upgrade`). The
  container proof, extended: it first builds the tap trunk's 0.1.4-1
  from 0.1.4's published archive (staged by digest, no download) and
  installs it, then builds 0.1.5-1 on the rehearsal's archive and
  installs it **over** it with `pacman -U`: `upgrading lobo-bin...`,
  the 0.1.5 note once under the real `vercmp`, `lobo-bin 0.1.5-1`,
  `lobo -v` 0.1.5, `/usr/bin/lobo` equal to the archive's binary
  (`0da8d84d…`), 16 documents, BUILD, no lane file, the page served as
  a user, `REHEARSAL-OK` (`ev/aur-rehearsal.log`); with the zeros kept,
  `==> ERROR: One or more files did not pass the validity check!`
  (`ev/aur-rehearsal-red.log`). The tap PR's CI and the `+dev` PR are in
  the pull request.

### Found, reported, not fixed (for the orchestrator to file)

- **A hand replaced during an upgrade is the new binary.** The master
  exec's a replacement from the path `os_exe()` gave at its start, so
  after a package manager renames the new binary over the old, any
  hand the old master restarts (a crash, a kill) runs the new version
  beside old hands, under a master that does not know. 0.1.4 → 0.1.5
  as root with no `user` line makes it visible: the new hand drops to
  `nobody` and answers root-only files 403 beside a root sibling's
  200, and cannot write the logs the old master kept root's. nginx's
  workers are forks of their master and never meet this. Written in
  the upgrade notes ("restart right after the install") and the known
  list; the AUR `post_upgrade` says it. A fix would be the master
  holding its own image (exec'ing `/proc/self/exe`, or refusing to
  start a hand whose `-v` is not its own).
- lobo#101 confirmed on the release binary (above).
- 0.1.4 writes no `error.log` until it has an error; 0.1.5's master
  makes the file (to give it to the hands). Noted, harmless.

### Slips, named

- I wrote `commit.gpgsign false` into the shared lobo checkout's
  config (worktrees share it) and removed it at once; the commits are
  signed as trunk's are.
- `upgrade.py`'s first full run read an error log that 0.1.4 had not
  made, raised, and left its container running on a live client
  thread; I stopped my own container by name (`podman stop`), made the
  reads total and the threads daemons, gave the container a
  `--timeout`, and re-ran; the log of record is the second run's (the
  first, overwritten, had the same A and B lines).
- `launch.sh` exec's `bash "$@"`: my first launch passed `bash -c …`
  and died at once (`cannot execute binary file`); relaunched with the
  script itself.
- A worktree path given relative to `git -C lobo` landed inside the
  clone; removed and re-made at the absolute path.
- P2's basis (above).

## 4. Evidence index

kasumi `~/lanes/ws70/` (sha256 prefixes): `toolchains.txt`
2c9b658e4600…, `dl/digest-check.txt` b8e300d66583…,
`logs/build-trunk.log` 9b1d95a7813f…, `logs/gates-reh1.log`
e3ef95441753…, `ev/upgrade-reh1.log` de35ff953250…,
`ev/upgrade-reh1-de.log` 2b1c4cf81011…, `ev/rss.log` c5f5c1a13813…,
`ev/tput-rel5.log` 7e1b2c4fd89a…, `ev/confload.log` 539065ede4dc…,
`ev/aur-rehearsal.log` 46f29a36464a…, `ev/aur-rehearsal-red.log`
16bb600bd195…; the gauntlet at the head `logs/g-head.log` (in the pull
request). Scripts (`scripts/`): stage.sh a4968c8b8959…, build.sh
3c518c4ea216…, g.sh 18040f938250…, launch.sh 3ba39ba2e1c0…, gates.sh
886e9ac79e68…, archive-smoke.sh 22e9add29869… (ws65's), rss.sh
1a6f2ad324a2…, upgrade.sh cb5c9f017a5e…, upgrade.py 757fc8a716fa…,
confload.sh 6936f96fb6ab…, confload-run.sh 6489a0082202…, tput.sh
6b6a7c4a5c6a… and tput-in.sh 309c631feedb… (ws69's `e208754b…` and
`67df184f…` with this lane's paths and two static shapes), px69.py
8efb62d375e7… and summ.py 941b8f8adfac… (ws69's, unchanged), chain1.sh
5f5ec18c451b…; `door/aur-proof.sh` fde53fdfd604… (ws65's, with the
upgrade).

CI: rehearsal 1 **39654225786** (`4ce9b5b`: dist green both hosts, the
macOS root step red on its own `pgrep`); the plant **39655455898**
(`ws70-plant-macwarn` `9f82bfb`, job 119420104974, red at the `[warn]`
count); rehearsal 2 **39655459695** (`09cd04e`, green, six jobs, two
skipped by design); parity **39656019826** (`tier measure`, VALID); the
final rehearsal, `tier pr`, `tier full` and the tap's runs at the final
head are in the pull request.

## Not verified

The macOS archive on a Mac by hand (the release workflow's smoke and
root step are its runs; no build or run on nomad-1); the Homebrew
formula installed (`ruby -c` only; the tap's `doors` legs are red by
construction until the fill); `-s quit` with a download in flight
(only `-s stop` measured); the window on macOS; `cert auto` actually
issuing under the default (the CA was absent; lobo#102 keeps root
there); PAX (ws68 §6's note stands).

## 5. Done-when

Branch `ws70`, its PR open and unmerged with five sections by name,
commit shas as bullets and a test checklist; `tier pr` green at the
final head and the `full-matrix` label added there; `bash
wolf/tools/lane-audit.sh lobo ws70 <PR>` from the org directory
passing but for `tier full`'s green; the tap PR (draft) and the `+dev`
PR (draft) open. Then the hand-back with the full run's id (RULES.md
§6). The orchestrator merges, tags `v0.1.5` at the merge, watches the
release run (four assets, the binaries equal to the final rehearsal's),
runs `tools/lobo-fill-digests 0.1.5` in the tap, merges the tap PR,
hands the AUR push to the maintainer, then doors-fresh and the `+dev`
merge. `ws70-plant-macwarn` stays on origin as evidence.
