# ws54 — the open five, and the gap to nginx

Wave 53, lane ws54 (Opus). Written 2026-10-08 (12:40–13:00Z) on lobo
trunk `a728fab`, before any edit to `src/` or `tools/`. The planning
contract is `sprints/wws/23-the-open-five/ws54-the-open-five.md` in
`wolffe-lang/wolf`; rules are `sprints/wave-53.md` down to
`wave-45.md`. The oracle is the pinned nginx 1.30.4 (ws47's copy,
`65595ac2…`), run, never read.

## 1. Forbidden, absolutely

- nginx behaviour only from the pinned oracle (ws47's copy, COPIED to
  `kasumi:~/lanes/ws54/nginx-oracle`, digest checked); never read
  nginx, kernel or libc source.
- Never touch `~/scratch/wolf/*-demo`, `~/scratch/wolf/pax-shell`,
  port 8088, the `wolf-demo` tunnel, `~/.cloudflared` or port 8080.
  Probes use loopback ports 18541–18559.
- Stay on lobo's pin: wolf 0.2.25 / lupin 0.1.48 / std `14f0ab2`, from
  the RELEASE ARCHIVES by digest. A wolf gap found while profiling or
  fixing is filed upstream with a witness, never worked around with
  `extern "c"`.
- Parity numbers only from a VALID runner set or a kasumi set the tool
  accepts; a refused set is reported as refused. Debug digests compare
  within one tree only.
- No `rm` outside `kasumi:~/lanes/ws54/`, `~/lanes/ws54/` on nomad-1
  (this worktree's parent) and this lane's scratchpad. No `git add -A`.
  No edit to another lane's file. Nothing under `~/.claude`. No build
  on nomad-1. No package installs, no sudo.
- No merge, tag or release; close no issue. No `2>/dev/null` on a
  checkout. No commit trailers or PR attribution of any kind.
  Checksums carry a trailing `…`.
- No "seen red" without a run id, sha, path or digest beside it.
  Strict evidence (wolf-lang#571): gauntlets run with
  `WOLF_PAIRING_REQUIRE_SIBLING=1`, lupin present, stdout and stderr
  together, every SKIP line counted; concurrency and signal rows also
  under `taskset -c 0-3`; SigBlk/SigIgn recorded beside every run.
- kasumi: `ssh kasumi "bash -c '( setsid nohup … & echo $! > pid )'"`,
  done-files, kill by recorded pid only (pgid 861 is tailscaled's),
  `scp`, prune `target/` as I go (/home at 96 %, 46 GB free at
  12:40Z).
- Waits print at least every five minutes. `gh run view`, never
  `gh run watch` without `--interval 60`. Cancel only my own runs.

## 2. Inputs, verified (re-derived 2026-10-08, 12:40–13:00Z)

| input, as the contract states it | what origin says |
|---|---|
| lobo trunk `a728fab` (ws53) | **holds**: `origin/trunk` = `a728fab707aa…`; `wolf-toolchain.toml` [wolf] `6710f9e0` (0.2.25), [lupin] `531bf058` (0.1.48), [std] `14f0ab2c…` |
| the pin's archives | **hold**: wolf 0.2.25 linux x86-64 `9d91f533…`, lupin 0.1.48 linux x86-64 `81cfd77a…`, both digest-ok (`kasumi:~/lanes/ws54/dl/digest-check.txt`); staged `wolf` `8373b0cd…`, `libwolf_rt.a` `6ac563e7…`, `lupin` `734caee6…` (`toolchain-tc-0225.txt`) |
| the oracle `65595ac2…` at ws47's path | **holds**: `kasumi:~/lanes/ws47/lobo/tests/differential/bin/nginx` `65595ac28d29…`, `nginx/1.30.4`; copied, digest re-checked (`kasumi:~/lanes/ws54/nginx.sha256`). `ab` is ws47's build `05f2f6d5…`, copied |
| the five issues #48–#52 | **hold**: exactly these five are open on lobo, each as filed by ws48 at `866789c`. Re-derived against the oracle (`kasumi:~/lanes/ws54/oprobe.log`): #48 nginx answers `GET /hello` 200 (`text/plain`, the URI has no extension) for `location = /hello { alias html/index.html; }`, also for an absolute alias; `/hello/` is 404. #49 `nginx -t -q` on a good config prints NOTHING and exits 0; on a bad config the `[emerg]` and `test failed` lines still print (exit 1); a `[warn]` still prints under `-q`. #50 the oracle drains an old worker with the timeout of the config THAT WORKER WAS STARTED WITH: added by a reload, it does not bite the generation started without it (the worker drained the whole download); present when a generation started, it bites that generation 2 s after ITS reload even when the reload removes it (`gracefully shutting down` 08:45:05 → `exiting` 08:45:07). #52 unprivileged nginx warns on `user` and `-t` exits 0 |
| the issues' diagnoses | **#48 holds** (`http.lu` `join_path(alias, "")` gives `alias/`). **#49 holds** (`Cli.quiet` set at `shell.lu:297`, never read). **#50 holds** (`main.lu:1412` reads `shutdown_ms` once from `c0`). **#51 holds** (`retire_zero` drops the row; `render_metrics` iterates live rows only). **#52 holds**: wolf 0.2.25 has no uid surface at all (no getuid/geteuid builtin; `fs_fstat` answers kind/size/mtime only; std 14f0ab2 `fs`/`os`/`process` have none) — the `/proc/self/status` read is the only one, so macOS has none |
| the parity gap: nginx ÷ lobo ~1.21x close / ~1.24x keepalive on the runner (ws53) | **holds**: ws53's row (run 37701293832) 1.208x / 1.239x; ws52's 1.151x / 1.255x; ws47's 1.151x / 1.240x (`docs/PARITY.md`). The close cell moves with the VM class (51k vs 22k req/s); keepalive has sat at 1.24–1.28 since ws31 |
| ws47's named costs | **hold as text** (`docs/PROFILE.md` ws47 addendum): N=1 keepalive user space 24.5 % (lobo 17.7 + libc 6.8) ≈ 5.2 µs a request over nginx; four hands pay +14.6 µs a connection (close) and +4.8 µs a request (keepalive) that one hand does not; at idle lobo's hands make 782 `futex` a second; on kasumi's 16 hands keepalive connections spread 4.1x unevenly. Re-measured by this lane below, not carried |
| the runner parity workflow | **holds**: `ci.yml` `workflow_dispatch` inputs `parity`, `ref_tree`, `ref_name`, `this_name`, `profile`, `profile_shape`, `profile_n`, `profile_hands`, `syscalls`, `listen_args`; recent parity runs take 10–12 min |
| `BUDGET.md` | `docs/BUDGET.md` (the per-request memory budget; `tools/lobo-membudget` gates retention, ws53: 19/20 KB a request). Any parity fix re-runs it |
| README's parity table | **stale as stated**: it still carries ws47's 2026-10-02 rows (1.151x / 1.240x on the runner) and nothing from ws52 or ws53 |
| CI hosts | `ci.yml` runs ONE gauntlet job, ubuntu-latest. **No CI job runs the gauntlet on macOS**, so #52's red has never been a CI red; ws48 found it on nomad-1 |

## 3. Prediction, committed before the first change

### 3a. The five issues (written 13:00Z, before any edit to `src/`, `tools/` or `tests/`)

Each issue gets a row that is RED at trunk `a728fab` and GREEN at its
fix, in a harness the gauntlet already runs; where nginx defines the
behaviour the row is differential against the pinned oracle.

- **#48 — alias to a file.** Fix in `http.decide`: an EMPTY remainder
  maps to the alias itself, not `join_path(alias, "")` = `alias/`.
  Row: `tests/differential/cases/alias_exact_file.case`
  (`location = /hello { alias www/index.html; }`, `GET /hello` → 200,
  the file's bytes, `Content-Type` nginx's default type because the URI
  has no extension) plus `alias_exact_file_slash.case` (`/hello/` →
  404 on both). Predicted: the first case RED at trunk on lobo only
  (lobo 404, nginx 200), the second green at trunk and after; both
  green at the fix. Falsified if lobo's 200 differs from nginx's in any
  header the NORMALIZE list does not cover (the default type is the
  likeliest).
- **#49 — `-t -q`.** Fix in `shell.lu`/`main.lu`: `-t` with `quiet`
  prints neither success line; errors and warnings still print, exit
  codes unchanged. Row: `tools/lobo-shell` gains three output-gated
  probes (good config → both print NOTHING, exit 0; bad config → both
  print a `test failed` line, exit 1; a `user` config unprivileged →
  both print the `[warn]` and no `successful` line, exit 0). Predicted:
  the first probe RED at trunk (lobo prints 2 lines), the other two
  green at trunk; all three green at the fix.
- **#50 — `worker_shutdown_timeout` across reloads.** Fix in
  `main.lu`: the deadline a DRAINING generation is held to is read from
  THAT generation's own frozen config (nginx's measured behaviour: the
  old worker keeps the value it was started with), never `c0`'s. Row:
  `tools/lobo-control-differential` row 7: one slow download held
  across each of three reloads, on both servers — (7a) a generation
  started WITHOUT the directive and drained by a reload that ADDS 2 s
  is still alive 4 s later; (7b) a generation started WITH 2 s and
  drained by a reload that REMOVES it is gone (nginx: the worker
  exited; lobo: `generation-retired … aborted=1`) within 4 s; (7c) a
  generation started without, after that, is alive 4 s later.
  Predicted at trunk (lobo started without the directive, so its one
  `shutdown_ms` is 0): 7a green, **7b RED** (lobo never aborts), 7c
  green; all green at the fix. Also under `taskset -c 0-3` on kasumi,
  SigBlk/SigIgn recorded.
- **#51 — a finished drain is scrapeable.** Fix: two process-wide
  counters that outlive a generation —
  `lobo_drained_connections_total{outcome}` (drained / aborted, summed
  over every generation that ever drained) and
  `lobo_generations_retired_total`; the per-generation
  `lobo_connections_retired_total{gen,outcome}` keeps its meaning and
  docs/metrics.md says it leaves with its generation. Row:
  `tools/lobo-metrics` gains an exact-count clause: a one-connection
  drain, scraped after `generation-retired`, reads
  `lobo_drained_connections_total{outcome="drained"} 1` and
  `lobo_generations_retired_total 1`. Predicted RED at trunk (the
  series do not exist), green at the fix; the cardinality fence holds
  (two fixed label values and one unlabelled series).
- **#52 — `user` without /proc.** wolf 0.2.25 has no uid surface
  (§2), so the fix cannot read the uid on macOS; it ASKS the host:
  where `/proc/self/status` is absent lobo runs `/bin/sh -c` with a
  test of `id -u` and reads the answer off the EXIT CODE (the only
  thing `process.run` returns at this pin): unprivileged → nginx's
  `[warn]` and the config loads; root → the existing `[emerg]` (lobo
  cannot drop privileges); no answer → the existing `[emerg]`. The gap
  is filed upstream (wolf-lang: no getuid/geteuid) with a witness.
  Rows: (i) a NEW `gauntlet-macos` CI job (macos-latest, the pinned
  toolchain built from source as the linux job builds it, the pinned
  nginx with Homebrew's openssl@3) — predicted **RED at confcheck** on
  trunk's source with ws48's five configs (`identical loads moved`),
  and GREEN at the fix; (ii) `tests/config/user_directive.lu` keeps the
  pure verdict rows. Falsified if the macOS job reds at a step BEFORE
  confcheck (then the job's first red is a different defect and is
  reported as found, not hidden).

### 3b. The parity gap — the profile first, then the prediction (written 2026-10-09 15:50Z, before any change to the serving path)

**The profile at trunk's source** (`a728fab`'s `src/`, wolf 0.2.25):

- Runner, VALID set, run **37779490101** (load 1.87, the fast class, nginx close 46.3k): **close 1.166x [1.142, 1.204], keepalive 1.185x [1.157, 1.197]**; N=1 1.045x / 1.093x. Per request at N=4: keepalive lobo 18.2 µs of cpu (2.51 cores ÷ 138.3k) against nginx 14.8 (2.41 ÷ 163.1k), **+3.4 µs**; close 42.4 against 33.5 µs a connection, **+8.9**.
- Runner `perf`, all four hands, keepalive N=4 (same run): **kernel 80.4 %, lobo-release 13.1 %, libc 6.0 %** — lobo's user space is 19.1 % of 18.2 µs ≈ **3.5 µs, the whole keepalive gap**. Leaves: `str::ambient_alloc` 2.30 % (the largest user leaf), `serve_main` 0.91, `head_warm` 0.90, `str_find` 0.81, `parse_request` 0.59, `list_new` 0.56. Close N=4 (run 37779498932, a slow VM): kernel 78.8 %, lobo 14.4 %; keepalive N=1 (run 37779510438): kernel 75.6 %, lobo 16.7 %.
- Runner count (run 37779490101): keepalive **6.25 calls a request against nginx's 6.14**, close **10.25 against 10.13**; lobo's extra close rows are the herd's: `poll` 1.28, `read` 1.08, `futex` 0.34, `accept4` 1.08 a connection where nginx pays 0 / 0 / 0 / 1.00; at idle lobo's four hands make **1155 calls a second**, nginx 0.
- **The herd and the spread, named with numbers.** Herd: the four close-shape rows above (+2.78 calls a connection lobo pays and nginx does not), and on kasumi (`kasumi:~/lanes/ws54/prof-base.log`, N=4 under `taskset -c 0-3`, load 10, shares not rates) lobo 14.1 µs a connection against nginx 9.9. **Keepalive spread: 1.01x** across the runner's four hands (requests a hand, max ÷ min, run 37779490101's split) and **1.04x** on kasumi at N=4 — the 4.1x ws47 measured is a sixteen-hand effect, not the runner's cell; at the bar's N=4 there is no spread to fix.
- kasumi, one hand, keepalive, `perf --call-graph lbr`, user space only (`kasumi:~/lanes/ws54/cg-ka1.log`; paranoid 2, no kernel): inclusive `serve_request` 68.7 %, `parse_request` 15.5, `handle_request` 39.7, `serve_file` 24.0, `classify` 7.3, `decide` 7.1, `str_find` 6.8, `list_new` 6.5, `join_path` 5.2, `head_cut` 5.1, **`proxy.resolve_need` 3.1 (on a server with no `proxy_pass`)**; self `serve_main` 8.1, **`ambient_alloc` 7.4 (of which `Mutex<Arena>::lock`/`unlock` ≈ 6: one lock per string allocation in a single-threaded hand)**, `retire_zero` 0.8 (a rebuild of the generation table every pass).
- The load-proof per-request number, `perf stat -e instructions:u` over 400,000 keepalive / 200,000 close requests at N=1 (`kasumi:~/lanes/ws54/st-trunk.log`, three repeats): **keepalive 19,776 / 19,949 / 19,925, close 21,686 / 21,735 / 21,777 user instructions a request**.

**What is lobo's to fix, and what is not.** The kernel is four fifths of a request and lobo's syscall count is nginx's plus 0.11; the user-space fifth is where lobo's own code is, and inside it the single largest cost is the runtime's string arena mutex (`wolf_rt::str::ambient_alloc`), which is wolf's, not lobo's: filed upstream with this profile, not worked around. The herd's extra calls are the runtime's `net_wait`/`net_accept` mechanics at the default posture; the measured lobo-side cure (`listen … reuseport`, ws32) is a posture change the maintainer ruled the bar does not take (B1), so it is not this lane's. What remains lobo's are per-request costs that do no work for this request:

- **F1 — `proxy.resolve_need` on a server with no `proxy_pass`.** Every request percent-decodes, normalizes and plans its path a second time (`handle_request` does it again) only to learn there is no upstream. Fix: answer `no_need` at once when no resolved route row carries a `proxy_pass` (`rr_pass` all empty — read off the load-time table). Predicted: **−2.5 % to −4 % user instructions a request** on both shapes (≈ 500–800 of ~19,900).
- **F2 — the per-pass generation-table rebuild.** `retire_zero` rebuilds the `List[GenRow]` on every poll pass whether or not anything is draining. Fix: skip it when no generation is draining. Predicted: **−0.5 % to −1.5 %** keepalive (several requests share a pass), about the same on close.

**Predicted effect on the bar:** F1 + F2 take **3–5 %** of lobo's user instructions, which is **0.6–1.0 %** of a request's cpu (user space is ~19 % of it): nginx ÷ lobo moves by **at most 0.01** on either shape, inside one pair's spread. **The 1.10 bar stays NOT MET** (predicted close 1.14–1.20x, keepalive 1.16–1.21x at the head on the runner), and the honest statement of why is the profile above: lobo's remaining gap is the runtime's string arena and the herd's mechanics. Falsified if F1 moves user instructions by less than 1.5 % or the head's runner keepalive ratio leaves 1.15–1.22x on a VALID set.
