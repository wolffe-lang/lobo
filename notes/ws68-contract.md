# ws68 — lobo at 0.2.33, the `user` default, and what 0.1.5 carries

Crawl 54, the 0.2.33 downstream round's lobo step, lane ws68 (Opus).
Written 2026-10-20 on lobo trunk `9e4ce7f` (ws67's head, PR #98
merged), after the inputs below were re-derived and measured (trunk at
both pins, the pinned nginx as a black box) and before any change to
`src/`, `tests/`, `tools/`, `docs/`, `wolf-toolchain.toml` or the
CHANGELOG. The planning contract is
`sprints/wws/37-lobo-at-0233/ws68-lobo-at-0233.md` in
`wolffe-lang/wolf` (planning trunk `31d9e72`); the rules are
`sprints/RULES.md` (canonical since 2026-10-19).

One deliverable, five items:

1. lobo pinned from wolf 0.2.32 / lupin 0.1.54 / wolf-std `d37c911`
   to **wolf 0.2.33 / lupin 0.1.54 / wolf-std `cceda63`** (own
   commits); the bare pin's gauntlet rows against 0.2.32's; the
   gauntlet, lobo-shell's 44 probes, membudget, proxy-differential and
   the resolver green on the new pin, plain and under `taskset -c 0-3`;
   what moved, by name.
2. **The `user` default** (a ruling asked at audit; the recommendation
   implemented): as root with no `user` line nginx runs its workers as
   its default `user nobody nobody`; lobo keeps root and warns (ws67).
   Recommended: match nginx, the warning kept for the case where
   `nobody` does not exist. Measured as root in a container (a hand's
   `/proc/self/status` Uid/Gid), and the row re-recorded against nginx.
3. **What 0.1.5 carries**, under a `0.1.5` heading in the CHANGELOG
   (ws66's bump, ws67's three fixes with their named deltas, this pin
   and the default), and the release checklist as ws61 left it. No tag.
4. **lobo#99** (a client that closes mid-exchange is not noticed) if
   `os_signal_wait_fds` is not needed for it, else said so.
5. **lobo#100** (proxied throughput) measured once more on the new pin,
   left for its own lane unless the job-socket reuse is a one-commit
   1.2x.

## 1. Forbidden, absolutely

- **Nothing here deploys or serves anything public.** lobo serves no
  site of ours; lupp.us is nginx on almanta (`sprints/HOSTING.md`).
  Never almanta, the live nginx, any Cloudflare tunnel or
  `~/.cloudflared`, DNS, or host ports 8080 and 8088; never a listing
  of `cloudflared`'s arguments. Every server this lane starts binds
  127.0.0.1 on a kernel-chosen port or one of 18920–18939, or port 80
  INSIDE a throwaway container's own network namespace, and is stopped
  through its control endpoint, by its handle, or by its recorded pid.
- **Root only inside a container.** The `user` default, port 80 and
  every id change are measured as root in a rootless podman container
  on kasumi (and, in CI, a docker container on the linux runner); never
  as root on a host. Signals, id changes and faults only to processes
  the test started, inside a container.
- **Clean-room against nginx's source**: its documentation (`user`,
  `proxy_ignore_client_abort`, `proxy_read_timeout`, the configure
  page's `--user`/`--group`) and black-box runs of the pinned 1.30.4
  (`65595ac2…`) only.
- No merge, no tag, no release, no tap or AUR change (0.1.5 is the
  release lane's, on the maintainer's word). No issue filed or closed
  (listed in the report). No attribution or co-author trailer in any
  commit or PR text.
- Toolchains only from the published release archives by digest, each
  digest read twice.
- No assertion deleted or weakened without the row it moves to; no
  timeout or retry as a fix.
- No `rm` outside `~/lanes/ws68/` (nomad-1 and kasumi); no `git add -A`;
  nothing under `~/.claude`; no package installs on any host; the
  branch asserted before every commit; no build on nomad-1. kasumi:
  `bash -c`, `setsid` with a pid file, kill by recorded pid only.
- Strict evidence (wolf-lang#571): `WOLF_PAIRING_REQUIRE_SIBLING=1`,
  stdout and stderr together, every SKIP line counted; process, signal
  and descriptor rows also under `taskset -c 0-3`. No "seen red"
  without a run id, sha, path or digest.
- lobo CI is tiered (tl28): the PR opens without the label, `tier pr`
  goes green, `full-matrix` is added at the final head; a plant is the
  smallest run that shows the row red (RULES.md §7: here the PR run
  itself). Never cancel another lane's run. If the harness refuses an
  action, stop and report.

## 2. Inputs, verified (re-derived 2026-10-20)

Logs under `kasumi:~/lanes/ws68/` (digests in §4).

| input | what was found |
|---|---|
| lobo trunk | `9e4ce7fc6b80…` (ws67's notes after the rebase onto tl28's `52a2ae7`; PR #98 merged); origin has nothing later |
| wolf 0.2.33 | tag `v0.2.33` (annotated `56110e4f…`) → wolf-lang `85dab5d7e597…`; release 417610226, not a draft, four assets. API digests read twice, identical (`nomad-1` scratch `api-digests-{1,2}.txt`): linux x86-64 `4f955e8d…` (80,128,936 B), macOS arm64 `9152dbd1…` (18,780,248 B), linux aarch64 `24cde9e4…`, windows `96774801…`. Staged on kasumi, `sha256sum -c` twice (`dl/digest-check.txt`): `wolf` 58e4ade4…, `libwolf_rt.a` 5321ce86…, `wolf-cimport-worker` 57c41e39…; `wolf 0.2.33 (wolfgang, pin 85dab5d)`, `paired with lupin 0.1.54`; GLIBC_2.34; the archive's `std/STD-REV` is `cceda631…` (`toolchains.txt`) |
| lupin 0.1.54 | unchanged: tag `v0.1.54` (annotated `9c98d445…`) → wolf-interp `0e536e8f…`; release 415937354; linux x86-64 `175df238…` (2,971,403 B), twice; `lupin` a9856dd4…. wolf@v0.2.33 declares 0.1.54: pairing gap zero |
| wolf 0.2.32 beside it | re-staged by digest twice (`4c37f9c5…`): `wolf` 81bdf8d4…, `libwolf_rt.a` 74d55d5f…, `wolf-cimport-worker` 0498e8e1…: ws66's and ws67's bytes; its archive's std `d37c911f…` |
| wolf-std | lobo's `[std]` is `d37c911` (ws66). 0.2.33 bundles `cceda631…` (sc64 and sc65; API read twice). Under `std/` two files differ (`process/process.lu` +313, `signal/signal.lu` +186; 478 insertions, 21 deletions): lobo `use`s both (`std.process.set_ids` since ws67, `std.signal` since ws63) and calls nothing new |
| the 0.2.33 CHANGELOG | read at `v0.2.33` (`nomad-1` scratch `ws68-wolf-CHANGELOG-0233.md`). For lobo: "**lobo, muzzle, pax:** the pin." What a running program can see change: `os_signal_text(0)` answers words (#787; lobo does not call it); **a SEGV or BUS another process sends ends the program** under the default disposition, where a program that had run a task lived through the first (#784); a program that names `os_signal_wait_fd` starts with two more descriptors (#781); the bundled std is `cceda63`. Five new prelude names |
| new prelude names | `os_signal_ignore_one`, `os_signal_default_one`, `os_exit_signal`, `os_wait_status_core`, `os_wait_poll_core`: `git grep` over `src tests tools` at `9e4ce7f` finds no declaration and no use |
| trunk at both pins | `src/` at `9e4ce7f` builds on both tiers at `--error-limit=0` with **zero diagnostics** at 0.2.32/`d37c911`, at 0.2.33/`d37c911` and at 0.2.33/`cceda63` (`logs/build-t32.log`, `build-t33-sd3.log`, `build-t33.log`). Release 14,750,688 → 14,804,112 → 14,805,592 bytes (text 1,873,554 → 1,875,382 → 1,877,062); dev 16,982,528 → 17,036,912 → 17,049,168. Every digest differs |
| at rest, trunk | one process, 1.2 s after start, every inherited descriptor closed before the exec, on cpus 8–11: **20 descriptors and 9 threads** at both pins on both tiers, the same 20 targets (the set at 3 and 4, the hub's pipes 5–8; no shared wake pipe: lobo does not reach `os_signal_wait_fd`). RSS release 4,660–4,664 kB (0.2.32) / 4,684–4,708 kB (0.2.33) (`ev/rest-pins.log`) |
| #784 at lobo | in a container, unprivileged, each binary its own child: a GET and a proxied GET, then `kill -SEGV`: **0.2.32 lives through the first and ends at the second; 0.2.33 ends at the first** (wait status 139); the pinned nginx (`master_process off`) ends at the first (`ev/segv-pins.log`) |
| trunk's gauntlet at 0.2.32 | **GREEN**, exit 0, 1,469 s under `taskset -c 0-3`, strict env, 0 SKIP lines (`logs/g-t32.log` ab92b2f1…): corpus 372/372 lane-runs, `proxy-differential` 8/8, `lobo-shell` 44 probes / 42 parity / 2 named deltas / 0 red, `lobo-signal` 22/22, `lobo-user` 14/14 (podman on kasumi), `lobo-membudget` 25/25, `lobo-resolver` 9/9. The measuring shell's mask: SigBlk `0x10000`, SigIgn `0x4` (`g-t32.mask`) |
| **the `user` default, nginx** | as root in podman, `archlinux:base-devel` (`ev/ng68-oracle.log`, `ng68b-oracle.log`, `ng68c-oracle.log`). **No `user` line, root**: master `Uid: 0 0 0 0`; each worker `Uid: 65534 ×4`, `Gid: 65534 ×4`, `Groups: 65534` (one worker and two); port 80 200; a root-only 0600 file **403**; logs `root:root` at start, `nobody:root` after `-s reopen`; nothing in the error log at `info`. **The rule, by black box**: the uid is the account NAMED `nobody`'s (renumbered to 99:99 → `Uid: 99`, `Gid: 99`; to 65000 with group nobody 65001 → `Uid: 65000`, `Gid: 65001`), else **65534** (no account named nobody: `Uid: 65534`); the gid is the group NAMED `nobody`'s, else **65534** — not the account's own gid (account nobody 65000:65000 and no group named nobody → `Gid: 65534`); the groups are that gid and every group listing `nobody` (`extra:x:1700:nobody` → `Groups: 1700 65534`, with or without the account). No account, no group, no `/etc/passwd`, no `/etc/group`: it still starts and drops (65534:65534), silently. `user nobody;` and `user nobody nobody;` give the same lines as no `user` line when both exist. `master_process off`: no drop. **The contract's premise does not hold**: nginx needs no account named `nobody` |
| the images | `ubuntu:24.04` (lobo-user's, CI's): `nobody:x:65534:65534`, no group named nobody (`nogroup:x:65534`), `libcrypt.so.1`, `libssl.so.3`, `libz.so.1` present. `archlinux:base-devel`: `nobody:x:65534:65534`, `nobody:x:65534` (group), `libcrypt.so.2`. The kasumi oracle links `libcrypt.so.2` (built on CachyOS), so it runs in the arch image and not in ubuntu's; CI's oracle is built on the ubuntu runner (`libcrypt.so.1`) |
| **the `user` default, lobo trunk** | `src/config/userconf.lu`: `user_row` -1 → `user_verdict` "" → no drop; `root_note` prints the named delta's `[warn]` (`src/main.lu` 1304–1310, `serve_main`); `main` (6976) starts a master only for `worker_processes` > 1 or root with a `user` row. `tools/lobo-user` row 6 holds it: one process, `Uid: 0 0 0 0`, the `[warn]` |
| what runs as root today | through 0.1.4 a root `user` line refused to start, so **every root deployment of a release has no `user` line** and runs one root process: its logs, its ACME store, its keys and its configuration are root's. Under a drop: the master gives the logs to the user (ws67's `give_logs`); hand 1 owns `cert auto`'s renewal and writes the store (lobo#102: unverified under a drop); a hand re-reads a reload's files as the user (lobo#101: a root-only file refuses the reload in every hand, and the master says `reload complete … workers=0/N`) |
| **#99, nginx** | `ev/abort99-nginx.log` (loopback, unprivileged, an upstream that accepts and never answers, `proxy_read_timeout 10s`): a client that closes 1 s after its request — and one that only half-closes (`shutdown(SHUT_WR)`) — has its upstream connection **closed at once** (+0.000 s); the access line is `499 0 … up=127.0.0.1:<port> ust=- rt=1.000`; the error log at `info`: `epoll_wait() reported that client prematurely closed connection, so upstream connection is closed too while sending request to upstream`. Two pipelined requests to a proxied location: both answered, no `Connection: close` (pipelined bytes are not an abort) |
| **#99, lobo trunk** | `ev/abort99-t33.log`: neither the close nor the half-close is seen; the upstream connection stays open (the exchange waits until the upstream answers or `proxy_read_timeout`), and the request is logged with the UPSTREAM's later answer, `200 3 … ust=200` (nginx: 499). The wait is `read_up_head`'s blocking `net_read` on the upstream under its deadline (`src/proxy/proxy.lu` 1212) |
| **#99, the means** | `net_wait(fds: List[int], deadline_ms) -> List[int] ! {io}` (`[os.net.wait]`, in every pin since 0.2.0) already waits on several SOCKETS with a deadline; the client and the upstream are both sockets. `os_signal_wait_fds` (wolf-lang#795, s248, 0.2.34) is for a descriptor that is not a socket beside a signal set (yew's tty): **not needed** for a plaintext upstream. An https upstream's reads are `std.x.tls.client`'s (blocking, inside the std) |
| **#100 at the new pin** | `ev/tput-pins.log` (ws67's `px81.py`, copied by digest `6ddc1608…`; 20,000 proxied keepalive requests over 20 connections in turn, a prompt upstream, the server on cpus 8–11, client and upstream on 12–15, load 7.1–7.2, three alternating rounds): pre-#81 tree (`52a2ae7`) at 0.2.32 20,864 / 20,032 / 20,739 req/s; trunk at 0.2.32 10,057 / 9,977 / 10,029; **trunk at 0.2.33 9,962 / 10,082 / 10,067**: head ÷ pre-#81 **0.48–0.50x**, 0.2.33 ÷ 0.2.32 0.99–1.01x. (Five connections, `px81`'s default, cross `keepalive_requests 1000`: the first round's misses, kept in the log) |
| #100, the reuse | ws67's experiment (not kept): an exchange's job socket kept for the next gave 1.21x and 1.26x on two runs of three, and holds idle descriptors at rest |
| PAX | pax's kernel has the credential calls (`kernel/cred/`: `setresuid`, `setresgid`, `setgroups`, all-zero is root) and pax's lobo runs (px24/px25's `strace-lobo.sh`) start lobo with the stock config as the PAX user, which is root: after this lane such a run drops its hands to 65534 |
| lobo#99–#102, #87, #82 | open; #101 and #102 are ws67's drop findings, #87 ws64's limits leftovers, #82 per-server rows: none is this lane's but where the default reaches them |
| kasumi | 16 cpus, load 2–12 (other lanes), `/home` 33 G free, `ulimit -n` 2048; podman 6.1.3, rootless |

## 3. Prediction, committed before the first change

### 1. The pin

- `[wolf]` moves to `85dab5d7` (`wolf 0.2.33 (wolfgang, pin 85dab5d)`)
  in its own commit; `[lupin]` keeps its rev (0.1.54, `0e536e8`), its
  note says the pairing gap is zero at 0.2.33. The stamp constants
  (`0.2.33`, `85dab5d`) and the fourteen `.wolfi` headers follow in
  their own commits, as at ws66. Then `[std]` to `cceda63` in its own
  commit, `shell.std_rev` with it, and the `.wolfi` surfaces whose std
  hashes move (`std.process` and `std.signal`: at least `shell` and
  `root`) in an `interface(…)` commit.
- The gauntlet is GREEN at the bare pin (0.2.33 with std `d37c911`)
  and at the std move with trunk-at-0.2.32's verdicts, row for row:
  corpus 372/372 lane-runs, `lobo-shell` 44 probes / 42 parity / 2
  named deltas / 0 red, `lobo-signal` 22/22, `lobo-membudget` 25/25,
  `proxy-differential` 8/8, `lobo-resolver` 9/9, `lobo-user` 14/14,
  0 SKIP lines; under `taskset -c 0-3` and on all 16 cpus.
- `wolf audit --ci --dir src` holds with the manifest unchanged.
- **What moves, by name**: (a) **#784**: a SIGSEGV sent to a lobo
  process ends it at the first (measured above), as nginx's; (b) the
  binaries by the runtime and the std (+53,424 / +1,480 bytes release);
  (c) nothing else: no new name collides (W0304), no refusal, the
  at-rest count 20 holds (#781 does not reach lobo), the start ladder
  at the descriptor limit (ws66's 71 band) is unchanged because lobo
  names no `os_signal_wait_fd`. The docs gain one dated audit line in
  `docs/CAPABILITIES.md`.

### 2. The `user` default (the recommendation implemented)

- **The rule, nginx's as measured**: as root, on a host that can drop
  (linux), with no `user` line, the process that ran `lobo serve` is a
  master that keeps root, and each hand drops to uid = the account
  named `nobody`'s, else 65534; gid = the group named `nobody`'s, else
  65534; groups = that gid and every group listing `nobody`
  (`std.os.users.groups_of(group, "nobody", gid)`). With
  `worker_processes 1`, a master and one hand. Resolved off the
  account files' texts by a pure function (`config.default_ids`), so
  all three lanes run its rows; a file that cannot be read is an empty
  text (nginx starts without either file).
- **Measured in the container** (`tools/lobo-user`, ubuntu:24.04, as
  root): the master `Uid: 0 0 0 0`; the hand `Uid: 65534 65534 65534
  65534`, `Gid: 65534 65534 65534 65534`, `Groups: 65534`; port 80
  answers 200; the root-only file **403** (trunk: 200); the logs are
  `nobody:root` (ws67's named delta: from the start). Row 6 compares the
  hand's lines with the pinned nginx's worker's IN THE SAME CONTAINER
  where the oracle runs there (CI: built on the ubuntu runner; kasumi:
  with `LOBO_USER_IMAGE` the arch image), so the row is recorded
  against nginx, not against a constant.
- **Red first**: row 6's new expectation with trunk's `src/` (the
  root-keeping row) is red — one process, `Uid: 0 0 0 0` — in the PR's
  own `tier pr` run at the commit that changes the row (RULES.md §7);
  green at the commit after.
- **The warning kept where `nobody` does not exist** — implemented on
  the measured premise: nginx drops to 65534:65534 with no account and
  says nothing, so lobo drops as nginx does (parity on the ids) and
  keeps one `[warn]` saying no account is named `nobody` and the hands
  run as uid 65534. A recommendation to the orchestrator, not a
  deviation from the ids: keeping root in that case (the contract's
  literal reading) is a one-line change in `default_drops`.
- **Where lobo cannot match**, root kept, one `[warn]` each (named
  deltas): a host that cannot drop (macOS: `set_ids` is linux's at this
  pin); a configuration with **`cert auto`** (hand 1 writes lobo's own
  ACME store, and that is lobo#102, unverified under a drop: a default
  that turned a renewing root deployment into a failing one would be
  worse than the delta; nginx has no `cert auto`).
- **`user root;`** keeps root in the hands (nginx's too); it is the
  documented way to keep 0.1.4's posture.
- Not root, or with a `user` line: unchanged. The reload refusal
  (lobo#101) now reaches root deployments with no `user` line whose
  configuration or keys only root may read: named in the CHANGELOG's
  upgrade note, not fixed here.
- `tests/config/user_directive.lu` gains the default's rows (the ids
  off texts for the stock, renumbered, missing-account, missing-group
  and member shapes, all nginx's measured lines; the verdict for root
  and not root; the cert-auto and no-drop-host keeps).

### 3. lobo#99 (the client abort)

- **Not blocked on `os_signal_wait_fds`.** While a plaintext exchange
  waits on its upstream (the head, and a length- or close-delimited
  body), it waits with `net_wait([upstream, client], proxy_read_timeout)`
  instead of a blocking upstream read. The client readable means it
  closed or sent bytes: a read that answers `closed` (a close or a
  half-close) ends the exchange — the upstream closed at once, nothing
  written, the access line `499 0 … ust=-` with `$request_time` the
  wait (nginx's line) — and the proc reports, so the loop frees both
  connections. Bytes (a pipelined request) stop the watch; the reply is
  then sent with `Connection: close` and the connection closes after it
  (a named delta: nginx answers the pipelined request; the bytes cannot
  be handed back to the loop's carry from the proc without a carry in
  the account, which is #99's own follow-up if anyone pipelines to a
  slow upstream).
- **Measured** (`abort99.py`, the release binary): the close and the
  half-close end the exchange inside 50 ms of the client (trunk: never
  before the upstream), `499 0 … ust=-`; pipelined requests to a prompt
  upstream unchanged (both answered, they arrive in one segment and are
  the loop's carry before the job starts).
- **Not covered, named**: an https upstream (its reads are inside
  `std.x.tls.client`); the connect and the request write (bounded by
  their own deadlines); the error log's `info` line. `lobo-shell`'s
  row F (eight proxied requests, the clients close): lobo `after=200`
  as nginx, so its named delta becomes parity: **44 probes, 43 parity,
  1 named delta**. A test, `tests/serve/client_abort_e2e.lu` (native,
  checked): red at trunk (the upstream keeps its connection until the
  timeout), green after.
- The proxy suite unchanged: `proxy-differential` 8/8, the log
  differential, `lobo-resolver` 9/9, membudget 25/25 (the proxied row
  flat); throughput against a prompt upstream within 0.95–1.05x of the
  pin's (one `net_wait` per upstream read).

### 4. lobo#100

- Left for its own lane. The reuse is not a one-commit change: a kept
  job socket is two descriptors held at rest (the at-rest 20 becomes
  22 after the first proxied request), counted against ws64's reserve
  and `worker_connections`, and the drain's kill path closes both ends
  by the slot; ws67 measured 1.21x and 1.26x on two runs of three, not
  a steady 1.2x. Measured again above: 0.48–0.50x, unmoved by the pin.

### 5. 0.1.5

- `## 0.1.5 — unreleased —` at the top of the CHANGELOG, written for a
  person upgrading from 0.1.4 (Upgrading; What changed; Against nginx;
  The hosts, and what is still known wrong or limited), listing: ws66
  (0.2.32, the park at start retired, a start at the limit refused in
  one line), ws67 (lobo#94, #96, #81, each with its named deltas), this
  pin (0.2.33, #784), the `user` default with its upgrade note, #99.
  The version stamp stays `0.1.4+dev`; the release lane stamps it.
- The release checklist (ws61's §5 shape, ws65's steps) in these notes
  (§6), each step with its check, for the release lane.

### What would make this wrong

- A `.wolfi` hash that moves on a module that imports neither changed
  std module (the surface carries transitive hashes).
- The CI oracle not running in `ubuntu:24.04` (a library the image
  lacks): row 6 then records nginx's measured lines as constants and
  says so, as ws67's rows did.
- `set_ids` to 65534 refused in rootless podman (65534 is inside
  kasumi's map: 1 → 100000, 65536 ids).
- The proc's `net_wait` on the client racing the loop: the loop must
  not poll a client whose exchange is out (it does not: the row's fd
  leaves the poll set while `proxying`).
