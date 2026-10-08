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
