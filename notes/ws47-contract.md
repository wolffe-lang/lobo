# ws47 — the parity ledger at wolf 0.2.20, and lobo#32–#34, #36–#38

Wave 53, subwave 53d, lane ws47 (Opus). Written 2026-10-02 on lobo
trunk `f49f014`, before any measurement and before any edit to `src/`.
The toolchain template is ws46 (`notes/ws46-contract.md`): archives by
digest, members hashed by name, builds on kasumi under `setsid`, masks
recorded. The row in `wave-53.md`: "the parity ledger re-taken on wolf
0.2.20 (both rows predate 0.2.16), and the six open lobo issues
(#32–#34, #36–#38)". The oracle for the ledger is `docs/PARITY.md`'s
bar as written on 2026-09-08 and `tools/lobo-parity`, which implements
it; the oracle for the issues is the stock and pinned nginx 1.30.4
(`nginx -t`), the nginx source at 1.30.4, and lobo's own gauntlet.
This file lives under `notes/`, not `docs/`, because `tools/lobo-dist`
ships every `docs/*.md` (lobo#34, which this lane fixes).

## 1. Forbidden, absolutely

- No `rm` outside `~/lanes/ws47/` on kasumi, this worktree
  (`/private/tmp/ws47`) and this lane's scratchpad. No deletion in any
  tree this lane did not create. The pinned nginx is *copied*, never
  rebuilt in place: kasumi from `~/lanes/ws38/lobo/tests/differential/bin/nginx`
  (`65595ac2…`), this Mac from
  `~/GithubOrgs/wolffe-lang/lobo/tests/differential/bin/nginx`
  (`09e61975…`). The stock nginx source is *read* from
  `~/lanes/ws40/nginx-stock/` and that build is *run*, never written.
- No `git add -A`. No edit to another lane's file. No `~/.claude`.
- **No build on this Mac except the macOS parity run's lobo**, compiled
  with the published darwin archive pair by digest. Every other build,
  gauntlet and test runs on kasumi under `~/lanes/ws47/` with
  `CARGO_BUILD_JOBS=4`. No package installs anywhere (kasumi has no
  `ab`; it is built from Apache's source tarballs into
  `~/lanes/ws47/ab/`, a lane-local binary like ws40's stock nginx, and
  nothing is installed system-wide). No `sudo`.
- No merge and no rebase-merge. No `2>/dev/null` on a checkout. **No
  commit trailers of any kind.**
- No "seen red" without a run id, a sha, a path or a digest in the
  same paragraph. Each issue fix lands its test in a commit before the
  fix, and the red is a kasumi log path at that commit.
- **The pin does not move.** wolf 0.2.20 (`cdde128`) / lupin 0.1.43
  (`6d6cde5`) / std `14f0ab2`, from the release archives by digest.
- Kill only this lane's own pids, recorded at launch. Never a pattern,
  never a process group (pgid 861 on kasumi is tailscaled's). `setsid`
  on kasumi (never `ssh -f`); on this Mac `nohup … & disown`, the
  launch verified by its first log line.
- Waits print. A silent 600 s ends the lane. `gh run view`, never
  `gh run watch` without `--interval 60`.
- A bench set runs only on a quiet host: `uptime` read and recorded
  before each set. kasumi is shared with s199 and bu14: wait for load
  under 2, or record what it was. The tool refuses a set above 3.0 on
  its own; a refused set is named, never entered as a row.
- Every signal run (`lobo-signal`, inside each gauntlet) records the
  launcher's `SigBlk`/`SigIgn` beside its log.
- No change to what lobo serves on the differential's workload. A
  moved byte in `tools/lobo-differential` is a red.

## 2. Inputs, verified (re-derived 2026-10-02, 19:35–19:50Z)

| input, as the brief states it | what origin and the hosts say |
|---|---|
| lobo trunk `f49f014`, pinned at wolf 0.2.20 / lupin 0.1.43 | **holds**: `origin/trunk` is `f49f014` (ws46's evidence index). `wolf-toolchain.toml`: wolf `v0.2.20` `cdde128`, lupin `0.1.43` `6d6cde5`, std `14f0ab2` |
| wolf 0.2.20 release archives | release **401498582**, `draft:false`, `releases/latest` (no 0.2.21 yet: r26 has not released). linux x86-64 **`24855d5e…`**, darwin arm64 **`c8a3f1a3…`** (the asset digests, read from the API) |
| lupin 0.1.43 release archives | release **401010971**, `draft:false`. linux x86-64 **`e957c8de…`**, darwin arm64 **`24d3e8f1…`** |
| "both parity rows predate wolf 0.2.16, taken with 0.2.8 and 0.2.11" | **holds**: README's table carries macOS arm64 2026-09-09 (ws26, 1.033x / 1.072x, wolf 0.2.8) and linux x86-64 2026-09-11 (ws33's set, 1.197x / 1.263x, wolf 0.2.11). PARITY's newest ledger row is ws33's (2026-09-11) |
| "nginx ÷ lobo, workers = cpus, 32 concurrent clients, five interleaved runs, connection-per-request and keepalive" | **holds** as `docs/PARITY.md` §"The bar" writes it: `ab -t 5 -n 1000000 -c 32 [-k]` split over k = 4 generators, five interleaved pairs, the median of five per-pair ratios with min and max, gating cell N = cpus, informative cell N = 1, refusals for load > 3.0, generator cpu ÷ wall > 0.90, nginx max ÷ min > 1.15, any failed or non-2xx request. Both servers at their defaults (B1, 2026-09-11) |
| linux on **kasumi** | **drift**: PARITY's linux host is the CI runner (`ubuntu-latest`, 4 vcpus); every linux ledger row is the runner's. kasumi has never carried a row. The lane takes **both**: kasumi as the brief asks (a new host, named as such, never compared with the runner's rows), and the runner through `ci.yml`'s `parity=true` dispatch, which is the host the bar wrote down. kasumi: **16 cpus** (Intel i9-11900K, 8 cores × 2 threads, one socket), load **0.00 / 0.25 / 0.96** at 15:36 EDT (19:36Z), `/home` 80 G free |
| kasumi can run the bar | **drift**: `ab` is **absent** on kasumi (`/usr/bin/ab` missing; no `apr`, `apr-util` or `httpd` package). The lane builds `ab` from Apache's source tarballs (apr, apr-util, httpd's `support/ab.c`) into `~/lanes/ws47/ab/`, digests recorded; the macOS `ab` is `2.3 <$Revision: 1923142 $>`. `perf_event_paranoid` is **2** and the lane takes no `sudo`, so any linux profile is taken on the CI runner (`profile=true`, `syscalls=true`), which is where every linux profile in `docs/PROFILE.md` was taken |
| this Mac | **nomad-1**, Apple M5 Pro, **18 cpus**; sysctl names the levels **6 "Super" + 12 "Performance"** (PARITY wrote "12 performance + 6 efficiency" at ws22; the count holds, the names moved). macOS 26.4.1. Load **2.05 / 2.10 / 2.32** at 15:37 EDT (19:37Z) with other lanes' and the maintainer's processes up (bun, qemu, a Rust build); 52 G free |
| nginx's version | **1.30.4** on both hosts (`tests/differential/NGINX-PIN`; `-V` reads `nginx/1.30.4`, `--without-http_rewrite_module --without-http_gzip_module --with-http_ssl_module`). kasumi copy `65595ac2…` (ws46's), Mac binary `09e61975…`. The stock 1.30.4 (rewrite + PCRE + ssl) is ws40's at `kasumi:~/lanes/ws40/nginx-stock/nginx` |
| #32 CHANGELOG claims `try_files` | **holds**: `CHANGELOG.md:188` (the 0.1.0 entry, the v0.1.0 release body) says "nginx's `root`/`index`/`try_files` resolution"; `src/config/table.lu:190` marks `try_files` `planned(ws02)`; no implementation in `src/` |
| #33 release.yml header | **holds**: `.github/workflows/release.yml:28–37` says lobo is "the ONE PRIVATE repo in the org" and the smoke is "not yet a clean-STRANGER test". The repo is **public** (API `visibility: public`). The smoke's tag-run download (`gh release download`, line ~353) still carries `GH_TOKEN` |
| #34 predictions ship | **holds and grew**: `docs/` holds `ws37`–`ws41-prediction.md` (five, not three); `tools/lobo-dist:145–147` copies every `docs/*.md` but GETTING-STARTED into the archive |
| #36 "a quoted regex holding `\(`" | **the issue's mechanism is the filer's hypothesis, and the source says otherwise.** `src/config/lexer.lu`'s state 5 (just past a closing quote) accepts only whitespace, `;` and `{`; nginx 1.30.4's `ngx_conf_read_token` (`src/core/ngx_conf_file.c:647–650`) also accepts **`)`**, which then starts a new word. The `\(` is spliced correctly inside the quotes; the refusal is the `")` |
| #37 `client_max_body_size 4G` | **holds**: `size_bytes` (`src/config/logconf.lu:41`) takes k/K and m/M only. nginx sets `client_max_body_size` through `ngx_conf_set_off_slot` → `ngx_parse_offset` (k, m, g); `client_header_buffer_size` and `large_client_header_buffers` go through `ngx_parse_size` (k, m only) |
| #38 two lobo-lenient configs | **holds**: `tools/lobo-confcheck` `LOBO_LENIENT=2`, annotated on `certbot-vhost` and `crossplane-empty-value-map`. nginx opens `ssl_dhparam` (relative to the conf prefix) in `ngx_http_ssl_merge_srv_conf` for a server that has certificates (`ngx_ssl_dhparam`, `BIO_new_file` then `PEM_read_bio_DHparams`); a map value's `$var` is resolved when variables are initialised (`unknown "arg" variable`) |

## 3. Prediction, committed before any measurement, build or edit

**P1, the CI runner (the bar's linux host), N = 4, c = 32, wolf 0.2.20:
NOT MET on both shapes.** Close **1.10–1.25x**, keepalive **1.20–1.35x**
(ws31–ws33 read 1.14–1.20 and 1.26–1.29 at 0.2.11; nothing since
removes the herd or the ~5 µs of user space a keepalive request
costs, and ws41 measured the copy loop within 16 % of nginx's).
**Falsified** by either median outside its band, or by either at or
under 1.10.

**P2, kasumi, N = 16, c = 32: NOT MET on keepalive; close near the
bar.** Close **1.00–1.20x**, keepalive **1.10–1.40x**. A risk named
before the set: 16 hands, 16 nginx workers and four single-threaded
`ab`s share 16 hardware threads, and nginx's keepalive rate here may
put a generator over 0.90 cores, which refuses the cell; the bar's own
remedy is more generators (`gens` 8, four connections each), taken
and said if it happens. **Falsified** by either median outside its
band.

**P3, macOS arm64, N = 18, c = 32: MET on close, keepalive within
±0.07 of the bar.** Close **0.95–1.10x**, keepalive **0.98–1.15x**
(ws26 1.033x / 1.072x at 0.2.8; ws28's indicative 0.977x / 1.007x). The
box is shared with other lanes and the maintainer, so the set may be
refused on load; a refused set is reported as refused, retried in a
quieter window, and never entered as a row. **Falsified** by either
median outside its band.

**P4, if linux is still outside 1.10 (P1 says it will be): the runner
profile names the same two costs ws31 named** — at N = 1 the
keepalive gap is lobo's user space (lobo + libc ≥ 15 % of the hand's
samples against nginx's ≤ 5 %), and at N = 4 lobo pays more µs of cpu
per request than at N = 1 while nginx does not. **Falsified** by a
kernel-only gap at N = 1 keepalive, or by lobo's µs a request at N = 4
not exceeding its N = 1 figure.

**P5, #36: the backslash is incidental.** `if ($x ~ "abc") {` (no
backslash) is refused by lobo today with the same `unexpected ")"`,
and `lexer_quotes.lu`'s new case (`"a")` → `d|a`, `w|)`) is red at
trunk. After the fix the issue's minimal repro gets past the lexer,
and NPM's corpus entry still refuses (it has 20+ other blockers) with
a different first stop. **Falsified** by the backslash-free form
loading at trunk.

**P6, #37: one function, one directive.** A new offset parser (k, m,
g) serves `client_max_body_size` only; `client_header_buffer_size`,
`large_client_header_buffers` and the access-log `buffer=` keep
refusing `g`, as the stock nginx does (measured on both sides before
the fix). `gunicorn-example` stays refused (`accept_mutex` first).
**Falsified** by stock nginx accepting `g` on either size directive.

**P7, #38: both configs go to "both refuse", `LOBO_LENIENT` 2 → 0,
and no other corpus config moves.** lobo refuses an absent or
non-DH `ssl_dhparam` for a server with a certificate, as nginx does,
and a map value or source naming a variable no nginx module defines
and the config never declares. `IDENTICAL_LOADS` stays 4; every other
annotation holds. **Falsified** by any third config changing exit.

**P8, #32, #33, #34 are documents and packaging.** #32: an erratum
under the 0.1.0 entry, the entry's own text untouched. #33: the header
rewritten to the public fact, and the smoke's tag-run download drops
`GH_TOKEN` (anonymous `curl -L` of a v0.1.1 asset answers 200 today).
#34: the five predictions move to `notes/`, and `lobo-dist` refuses to
pack any `docs/*-prediction.md` or `notes/` file, its test red at
trunk on the five files.

**P9: every gate holds.** The gauntlet at the head is green on
kasumi: corpus 299/299 lane-runs or more, differential 22/22, proxy
8/8, control 9/9, signal 21/21 (mask recorded), `lobo-stamp: ok`,
confcheck green with `LOBO_LENIENT=0`. CI at the head runs 6–10 min;
a green under 60 s means the token lapsed.

### §3 against the measurement (written at the close)

- **P1 held.** Runner close **1.151x** (band 1.10–1.25), keepalive
  **1.240x** (1.20–1.35); NOT MET (run 37056568350).
- **P2 falsified.** kasumi was outside both bands by far: every pair
  of three sets read N=16 close above 1.40 and keepalive above 1.56
  (indicative medians ~1.84x / ~2.04x), and no set was valid — the
  tool refused all three on nginx's own N=16 spread. The risk I named
  (the generator ceiling) never fired (`ab` at most 0.77 cores); the
  one I did not name (an oracle that will not hold still on this box
  at sixteen workers) refused every set. My band assumed kasumi would
  look like the runner with more hands; at sixteen hands lobo's herd
  and its uneven keepalive distribution are the gap (PROFILE's ws47
  addendum).
- **P3 held.** macOS close **1.031x** (0.95–1.10), keepalive
  **1.037x** (0.98–1.15); MET; one set, valid on the gating cell.
- **P4 held.** One hand keepalive on the runner: lobo + libc 24.5 %
  of the samples (≥ 15 %). The nginx-side ≤ 5 % half was not measured
  (the profile leg profiles lobo only); the cpu a request says the same
  thing (5.2 µs a request more than nginx at one hand). Four hands:
  lobo 33.6 → 38.4 µs a request and 67.2 → 81.8 µs a connection; nginx
  28.5 → 29.0 and 65.5 → 62.9.
- **P5 held, but for one clause.** The backslash-free
  `if ($query_string ~ "abc")` refused with `unexpected ")"` at trunk
  (`probe-base.txt` row b), the lexer test was red at `30ab05e`
  (`t-red1.log`), and the repro loads after the fix. **Wrong:**
  NPM's first stop did not change; it is `pcre_jit` before and after,
  so the `if` was never NPM's first refusal.
- **P6 held.** `4G`/`4g` load; `1t`, `4mg`, `client_header_buffer_size
  1g`, `large_client_header_buffers 4 1g` and `access_log … buffer=1g`
  refuse on the pinned and stock nginx and on lobo; `0g` loads on all
  three. gunicorn-example still stops at `accept_mutex`.
- **P7 held**, with one correction to the means: the map refusal is
  located at the reading row (nginx prints no location) because the
  corpus ratchet counts a refusal with no line as silent; the ratchet
  test caught it on the first full run (`t-green2.log`).
  `LOBO_LENIENT` 2 → 0, `IDENTICAL_LOADS` 4 unchanged, no third config
  moved (confcheck at the head: 27 exit-parity, 13 named deltas, 0
  lenient, 0 red). Ratchet 16/6/18 → 15/6/19.
- **P8 held** for #34 (dist red at `625fe40`, green after the move).
  #32 and #33 are a document and a workflow: neither has a test that
  can go red before a tag (the smoke's download runs only on a tag
  push, which is the orchestrator's act), so each is fixed and the
  evidence is the measured fact under it.
- **P9 held**: see the index.

## 4. Evidence index

kasumi paths are under `~/lanes/ws47/`; Mac paths under this lane's
scratchpad `ws47/mac/`.

| claim | artifact |
|---|---|
| the pair by digest | `dl/digest-check.txt` (wolf 0.2.20 `24855d5e…`, lupin 0.1.43 `e957c8de…`, each asserted non-empty then equal), `dl/toolchain-0220.txt` (members by name, `--version`); darwin `mac/dl/digest-check.txt` (`c8a3f1a3…`, `24d3e8f1…`) and `mac/toolchain-0220-darwin.txt` |
| `ab` on kasumi, lane-local | `ab/digests.txt` (apr 1.7.6 `6a10e7f7…`, apr-util 1.6.5 `f43a1c8c…`, httpd 2.4.69 `c551b986…`, each against Apache's `.sha256`), `ab/ab.identity` (`05f2f6d5…`, `2.3 <$Revision: 1934973 $>`) |
| baseline gauntlet GREEN | `gauntlet-base.log` at `f6195bc`: exit 0, 255 s, mask `gauntlet-base.mask` (SigBlk 0x10000, SigIgn 0x6); release binary `6d0fca17…` = ws46's head bytes |
| runner parity, profile, count | run **37056568350** (workflow_dispatch at `f6195bc`): VALID, 1.151x / 1.240x; dso 75.09 / 17.72 / 6.75; calls a request 6.30/6.14 and 10.24/10.13 |
| macOS parity | `mac/parity-m1.log`: load 2.80, VALID (3 of 4), 1.031x / 1.037x; lobo `5c7818e3…` built by `mac/build.sh` (`mac/build.log`, the only build on this Mac); nginx `09e61975…` |
| kasumi parity, refused ×3 | `parity-k1.log`, `parity-k2.log`, `parity-k3.log` (each `parity-exit=3`, the refusal reasons printed, SigBlk recorded); lobo `6d0fca17…`, nginx `65595ac2…` |
| kasumi split | `split-s1.log` (script `ksplit.sh`), load 4.19 at the start |
| issue probes, pinned / stock / lobo | `probe-base.txt`, `probe-base2.txt` (trunk lobo `lobo-debug-base`), `probe-head1.txt` (head lobo): every row's lobo exit equals the stock nginx's at the head; script `probe/probe.sh` |
| #36, #37 red then green | `t-red1.log` at `b1b0baf` (0/6 lane-runs; lexer_quotes and limits_directives `trap(assert)`), `t-green1.log` at `fd2333c` (95/95) |
| #38 red then green | `t-red2.log` at `7ca6203` (0/4; map_vars `got ok` on lupin), `t-green2.log` at `c8f9484` (91/93: corpus_ratchet's silent class and a test path — both fixed in `2ea2bfd`, `44d1464`); the gauntlet below |
| #34 red then green | `run-dist-red.log` at `625fe40` (`FAILED — docs/ws37-prediction.md is a lane's working file`), `run-dist-green.log` at `a79cf46` (the archive's `docs/` lists no `ws*` file) |
| #33 | scratchpad `ws47/stranger/anon-check.txt`: v0.1.1's linux archive and `.sha256` fetched with no token, `OK` |
| #32 | `git show v0.1.0:src/config/table.lu`: `try_files` `planned(ws02)`; `probe-head1.txt` row z7 (a `try_files` config loads on all three) |
| gauntlet GREEN at the fixes | `gauntlet-head1.log` at `32eed53`: exit 0, 254 s, 303/303 lane-runs, differential 22/22, proxy 8/8, control 9/9, logdiff 4/4, signal 21/21, membudget 17/17, confcheck 0 red with 0 lenient, `lobo-stamp: ok`; mask SigBlk 0x10000 |
| gauntlet GREEN at the docs head | `gauntlet-head2.log` at `f1d347d` (everything but this index): exit 0, 262 s under load ~6 (s199), 303/303, differential 22/22, proxy 8/8, control 9/9, logdiff 4/4, signal 21/21, confcheck 0 red / 0 lenient, `lobo-stamp: ok`; mask SigBlk 0x10000, SigIgn 0x6 |
| CI at the fixes | PR #45, run 37058805833 at `32eed53`: success |

## 5. Done-when

- [x] Branch `ws47` on origin; PR #45 open against `trunk`,
  **unmerged**, five sections, commit-hash bullets, a test checklist.
- [ ] CI green at the head sha, read with `gh run view`, on a run
  that built the toolchain and ran the gauntlet.
- [x] PARITY's ledger gains dated rows for kasumi, the CI runner and
  macOS (or a refused set named for each host that would not quiet);
  README's table carries the new rows and keeps the old ones as
  history; nginx's version, cpu count and load on each.
- [x] If linux is outside 1.10: a `docs/PROFILE.md` addendum naming
  where the time goes, by run id.
- [x] #32, #33, #34, #36, #37, #38 each fixed with a test seen red
  first (log path at the test's commit), or closed with the reason;
  closures run only after the PR's evidence exists, and never claim a
  merge.
- [x] The gauntlet green at the head on kasumi, by log path, mask
  recorded; confcheck's ratchet moved with its annotations.
- [x] §2 drift and §3's verdicts reported; a CHANGELOG lane entry.
- [ ] The worktree gone, kasumi build dirs pruned (logs kept), no
  orphans.
