# Changelog

## 0.1.0 — 2026-09-07 — the first artifact

The first release of lobo, a web server written from parts in
[wolf](https://github.com/wolffe-lang/wolf-lang). It reads an
`nginx.conf`, serves static files and proxies, drains on reload
without dropping a connection, acquires its own certificates over
ACME, and is checked on every commit against a pinned real
nginx/1.30.4 running the same config.

### Install

Download the archive for your host, unpack it, and run it in place;
there is nothing to install and no dependency to resolve:

```sh
tar -xzf lobo-0.1.0-<host>.tar.gz
cd lobo-0.1.0-<host>
./lobo -v
./lobo -t -c conf/lobo.conf
./lobo -c conf/lobo.conf serve      # then: curl -i http://127.0.0.1:8080/
```

`GETTING-STARTED.md` in the archive is the whole learner path, and it
is the same script this release's CI runs against this archive on
a clean runner before the release page is published.

### The hosts, and the two that are refused by name

| host | archive |
|---|---|
| `x86_64-unknown-linux-gnu` | yes |
| `aarch64-apple-darwin` | yes |
| `x86_64-pc-windows-msvc` | **no** — named refusal until s60c |
| `aarch64-unknown-linux-gnu` | **no** — named refusal until s60c |

lobo ships the hosts wolf's release tier serves. For the other
two, wolf's LLVM release tier does not build them yet (upstream
s60c), and `tools/lobo-dist` refuses
to produce an archive for a host whose binary would not run. The gap
closes when the tier does.

### `lobo -v` names its own provenance

```
lobo version: lobo/0.1.0 (built with wolf 0.2.6, pin 398e5f5)
```

`-V` adds the standard-library pin, the tier and the module set. A
build that is not this release says so with a `+dev` suffix, and the
archive's name carries it too, so a rehearsal build cannot be
mistaken for a release.

### Reproducible from the pin, not from the runner

`wolf-toolchain.toml` pins the wolf (`v0.2.6`, `398e5f5`), lupin
(`v0.1.27`) and wolf-std (`bd12ef5`) this binary was built with, and
the release workflow builds that toolchain from source on every dist
host before it compiles a line of lobo, never the wolf a runner
happens to have. The archive's `BUILD` file records all of it, and the
pack is byte-reproducible (`--sort=name`, one `SOURCE_DATE_EPOCH`,
`gzip -n`), proven by packing twice and comparing digests. Each
archive ships a `.sha256` beside it.

### What is in it

Static serving with nginx's `root`/`index`/`try_files` resolution and
its MIME map; a reverse proxy with upstreams, a resolver and the
gateway error surface; TLS, including `cert auto` (built-in ACME)
beside a working certbot symlink layout; `worker_processes N` prefork
with inherited listeners and per-hand control sockets; reload/quit/
stop/reopen over a unix-domain control endpoint; nginx-format access
and error logs (byte-compared against nginx's own output in CI); a
Prometheus metrics endpoint; a memory budget; and `-t --request`, a
config dry-run that answers *what would this config actually do*.

`docs/directives.md` is the directive-by-directive table, and every
place lobo differs from nginx is a named delta in it.

## ws30 — 2026-09-11 — the router takes the syscalls (wolf pinned at fc07cc5; one open that cannot park; the count and the parked task's futex measured)

Three items; two runtime syscalls become one router site; every
number was written down before its run.

- **Item 1 — the pin, and the one site.** `[wolf]` moves 4c60946
  (v0.2.9) → **fc07cc5**, s149 merged on trunk, dev-stamped `wolf
  0.2.10+dev.fc07cc5 (wolfgang, pin fc07cc5)` — the ws18/ws24 shape,
  since v0.2.10 is 62 commits behind it and s149 is the reason. Built
  with `cargo xtask dist` in a scratch worktree (the archive is named
  0.2.10; the binary says `+dev.fc07cc5`) and staged into the main
  checkout's `.wolf-bin`, which every lane's worktree symlinks; the
  main checkout at trunk therefore refuses its own tools on identity
  drift until it is re-staged or re-pinned, as ws28/ws29 recorded. The
  sixty-two commits are classed in `wolf-toolchain.toml`: s149 is the
  point (#289 `fs_open_mode` 5, a read open carrying `O_NONBLOCK`;
  #290 `accept4(SOCK_NONBLOCK|SOCK_CLOEXEC)` and `TCP_NODELAY` paid at
  the write Nagle could hold, not at every accept); s148's #292 makes
  every `.wolfi` hash re-derive ONCE (the hashes are over the
  interface now, not the release string — this is the last pin bump
  that moves them); #293's E0416 (`s[a..b] = …` refused) is zero here,
  grepped; s146's W0601 (a `!()` tail in a unit context is a warned
  discard) is measured by the gauntlet, which denies warnings, and it
  fired nowhere; s147's range arms and #284's two clauses move
  nothing. The pairing gap is **two releases, named and not closed**:
  wolf@fc07cc5 declares lupin 0.1.31, `[lupin]` stays at 0.1.29 (this
  lane's contract pins `[wolf]`; the disk held one toolchain build);
  neither 0.1.30 nor 0.1.31 names the fs tier, so no lupin lane
  reaches the code the bump moves. #146 re-probed a SEVENTEENTH time
  at this pin: `WOLF_MIDEND=1` still ICEs on `sc_muladd`'s dominance
  (`%19 is not dominated by its definition`); `WOLF_MIDEND=0` stays.
  - **The site count, read off the tree**: s149's hand-off said one
    site; it is one serving-path site with two halves and one mirror.
    `serve.is_file_warm` (`fs_is_file` behind ws27's one-second kind
    table, the guard) and `serve_file`'s `fs_open` + `fs_fstat` (the
    open it guarded) become **`serve.classify`**: ONE `fs_open_mode(p,
    5)` and ONE `fs_fstat` on the handle, the kind decided off what
    came back — 0 serve through the open handle, 1 the router's
    directory arm (a 301 without a second stat), 2 a fifo, a device or
    a socket (refused: nginx's "is not a regular file", 404), `denied`
    403 (nginx's EACCES answer; a stat-first router said 404 to an
    unsearchable parent, now it says what nginx says), the open's `io`
    (ENOTDIR through a file, ELOOP, a name too long) 404 as before.
    The kind table's kind half is retired with the stat it remembered
    — there is nothing left to remember and no second in which a swap
    for a fifo could park a hand; ws28's head cache and date memo stay
    on the same struct. The mirror is `dryrun.stat_note` (`-t
    --request`'s prediction), which classifies the same way so the
    prediction and the demonstration keep agreeing; it is not on the
    serving path. `budget.lu`'s open (the capped proc's, on a path the
    router already classified) and `obs.lu`'s log open do not move.
    **A path with a trailing slash asks its index candidates directly
    and never opens the directory** — nginx's index module's shape —
    so `GET /` costs what it did, not an extra open+fstat+close.
  - **The witnesses.** `tests/serve/classify.lu` (a regular file is
    kind 0 with an open handle whose read is the file; a directory 1;
    a missing path 3; a file that appears or goes is seen AT ONCE —
    ws27's test pinned a one-second memory of a deleted file, and that
    memory is what this sprint retired; a FIFO made by `mkfifo(1)`
    answers kind 2 in 0 ms). `tests/serve/fifo_e2e.lu` (a real lobo
    with a writerless fifo under its root answers `GET /hole.html`
    **404 at once** and serves the file beside it after: the hand was
    never parked). `tests/serve/classify_e2e.lu` (ws27's
    `file_kinds_e2e.lu` rewritten: a swap for a directory is nginx's
    301 at once, not a 404 inside a window). The negative control was
    run by hand: `fs_open_mode(fifo, 0)` — the old open — parks until
    `timeout` kills it (exit 124); mode 5 answers a handle in 0 ms,
    kind 2.
  - **The census, predicted then measured.** Predicted: the corpus row
    moves by one witness, every other row identical. Measured
    (gauntlet at the pin, macOS arm64, GREEN exit 0): **corpus 270 →
    272 lane-runs** (the new witness on its two lanes; the two
    rewrites are one-for-one), differential 3/3, proxy 8/8, control
    9/9, logdiff 4/4, signal 21/21, prefork 38/38, membudget 17/17,
    resolver 9/9, replay 2/2, metrics, dryrun, shell, confcheck, tls,
    acme, dist — identical. Two `.wolfi` motions, each its own
    `interface(…)` commit: the stamp `0.2.9 → 0.2.10` in every header
    with every hash re-derived once (#292), emitted from a worktree at
    the pin commit so the intermediate tree is self-consistent; then
    `serve` gaining `classify`/`Classified` and losing `is_file_warm`
    and the two kind lists.

- **Item 2 — the count, PREDICTED against trunk, then measured.**
  s149's own prediction (keepalive 7.41 → 6.41, close 13.36 → 10.34)
  was against ws27's PRE-kind-table table; this sprint's prediction
  (`docs/PROFILE.md`, ws30 addendum, committed before the pin was
  staged) was against trunk, and said the pin buys the keepalive
  table NOTHING at two decimals and the close table exactly the
  accept side: **6.26 → 6.26** and **12.27 → 10.27**. Measured, one
  instrument, one day, one runner class (CI runs 34553773533 before
  at wolf 0.2.9, 34554207566 after at fc07cc5):
  - **keepalive 6.29 → 6.25** against nginx 6.14 → 6.15 (gap +0.15 →
    **+0.10**) — right: `ioctl` leaves the table (raw 221 → 0),
    `setsockopt` stays 0.00 (raw 221 → 114 — paid at a stream's SECOND
    write, so the master's one-write probe connections never pay and
    only `ab`'s do; the prediction said ~231 and counted every accept),
    and every per-request row (`statx` 1.00, `openat`, `read`,
    `recvfrom`, `writev`, `close`) holds to a hundredth.
  - **close 12.27 → 10.16** against nginx 10.13 (gap +2.13 →
    **+0.03**; **1.21x → 1.003x in calls**) — right on the mechanism,
    0.11 better than the figure: `ioctl` 1.00 → gone, `setsockopt`
    1.00 → gone, the accept side per connection **3.08 → 1.08**
    (predicted 3.08 → 1.08), `accept4` 1.08 → 1.08 (the herd, lobo#5,
    untouched), `poll` 1.28 → 1.28 (per connection, and it holds).
    The 0.11 is three per-time rows reading lower on a faster box
    (`futex` 0.39 → 0.32, `read`, `close` a hundredth each).
  - **The per-time drift, named before and measured after.** nginx's
    traced rate went 8,672 → 13,740 req/s keepalive (+58%) and 5,210
    → 7,320 close (+40%) between the two boxes. Read raw: keepalive
    `futex` 6,846 → 6,976 a drive — FLAT under 46% more requests (a
    clock), `poll` +51% (the pass's wait, scales with requests); close
    `futex` +32% under +61% more requests (the clock plus the
    reactor's parks), `poll` +61% (per connection). ws29's amendment
    read exactly as written: the per-request rows hold, the per-time
    rows move with the box, and this sprint's change is in neither —
    it is two per-CONNECTION rows going to zero.
  - **Every row that moved**: `ioctl`, `setsockopt` (close). **Every
    row that did not**: the twelve others, both shapes.
  - **The timing, PREDICTED then measured** (the parity leg, run
    34554232695, `ref_tree` = the pin-only tree `08d9362`: the same
    fc07cc5 pin with the OLD router, so the set isolates the router
    half on one VM — the ref tree must pin the toolchain the job
    staged, and a one-VM before/after of a PIN is not something the
    workflow can take; named, not worked around). Predicted on PR #12
    before the set was read: ws30 ÷ pin-only ~1.00 both shapes,
    nginx ÷ ws30 keepalive ~1.29x, close ~1.08x. Measured, VALID, the
    fast class (nginx close 46.4k): **ws30 ÷ pin-only 1.005x close /
    1.004x keepalive** at N=4 — right, the router half is worth what
    the count said (nothing; a lookup, not a syscall); **nginx ÷ ws30
    keepalive 1.286x** — right; **close 1.161x — wrong**: ws28's ledger
    row was 1.161x on the slow class with the old accept posture,
    this is 1.161x on the fast class with the new one, and a
    cross-class comparison cannot separate them. Cores 1.81 / 1.81 /
    1.62 close, 2.67 / 2.68 / 2.45 keepalive.
  - **W8 restated for linux, the count beside the timing.** Count:
    keepalive **6.25 vs 6.15** (1.02x), close **10.16 vs 10.13**
    (1.003x). Timing: keepalive **1.286x**, close **1.161x** — **NOT
    MET on both shapes**. The count says the remaining gap is not
    syscalls on either shape — on close lobo makes nginx's calls to
    three hundredths and is 16% slower; the timing says the bar is
    not met; the count does not claim the bar. What is left has a
    name on each shape: the string runtime and the transmit path on
    keepalive (ws28), the herd's parks on close (`accept4` 1.08,
    `poll` 1.28, the reactor's `futex`/`epoll_wait` — a wait behind
    each fraction of a call; lobo#5, wolf-lang#267). N=1 close 1.065x
    is inside the bar on the non-gating cell. `docs/PARITY.md`'s
    ws30 entry carries the table.

- **Item 3 — the parked task's cost, measured on lobo.**
  `tools/lobo-syscalls` grows an **`idle` shape**: the same serving
  processes for the same window with no generator, calls ÷ SECONDS —
  the per-time rows read with the only divisor they have. CI's count
  leg runs it after both drives. Measured before and after the pin,
  same day: **`futex` 6,266 → 6,262 calls in 8 s over four hands, every
  one an error return — ~196/s per hand, and the pin did not move it**
  (s149 touched `fs.rs` and `net.rs`, nothing in `task/`). Predicted
  ~100–110/s: **wrong by half** — ws29's ~106 was a subtraction of two
  drives whose "before" carried the old self-raise probe's own
  handoffs. Under the keepalive drive the idle clock is ~90% of every
  `futex` the hands make. nginx's four workers make **zero** syscalls
  in the same window. Posted on wolf-lang#302 with both raw tables;
  the runtime lane reads it there. A row the prediction did not know:
  the master's 200 ms liveness probe costs each idle hand six syscalls
  a probe before this pin and **four after** (`ioctl` and
  `setsockopt` were the two) — 16 calls/s per hand for supervision
  without a channel, lobo's own design (`docs/WORKERS.md`), named
  because an idle count now exists to show it.

- **Gates.** Local gauntlet at the 0.2.9 pair before Phase A's
  commits (GREEN, exit 0; a first run was red at tls-interop only
  because the lane's shell had no `$OPENSSL_BIN` — LibreSSL refused by
  name, as designed — and was re-run whole); local gauntlet at the
  fc07cc5 pair before Phase B's (GREEN, exit 0, 272/272); the three
  witnesses 6/6 lane-runs; `tools/lobo-interface --check` on the final
  tree; CI gauntlet, the count leg twice and the parity leg on the
  runner (run ids in the PR).

## ws29 — 2026-09-10 — the probe and the parity lane (the signal poll retired for a parked forwarder; the rig's filesystem half; two stale pages re-read)

Three items, and one of them stops before it starts.

- **Item 1 — lobo#8, the signal self-raise probe: FLIPPED, not
  retired.** A serving hand raised a signal to ITSELF every 25 ms and
  waited once, to learn whether an operator had sent one — `kill` +
  `getpid` + `rt_sigreturn` + the runtime's self-pipe `write`, four
  syscalls a probe, MEASURED at ws27 as ~0.12 per request at N=4 and
  re-measured on trunk `9a4a905` at this sprint's open (0.04 keepalive
  / 0.12 close, CI run 34539376264: the figure moves with the rate
  because the cost is per unit TIME divided by requests). **Retiring it
  outright was refused**: the probe is how the loop hears `kill -HUP`
  at all, and a server that does not answer an operator's signal is
  not nginx-compatible — the compat contract is sacred. So it flips to
  the shape `src/main.lu`'s header has promised since ws08.
  `sig_forwarder` parks ONE proc in `os_signal_wait` for the process's
  life and writes each meaning down a loopback self-pipe whose READ END
  joins the loop's ordinary wait set: a signal becomes READINESS, like
  every other event, and the loop asks nothing and pays nothing per
  pass. The blocker was wolf-lang#136 (s43's cluster partition follows
  CALL edges only, so a task-entry shim could land outside its
  spawner's object and the LLVM tier refused the address); #136 is
  closed and the pin is v0.2.9, and the flip was PROBED on the release
  tier before a line of lobo moved — a spawned proc parks with nothing
  pending, forwards a real meaning, and the process still exits.
  - **The only self-raise left in lobo is the ONE that retires the
    forwarder at shutdown.** ([conc.proc.root] kills a parked proc at
    process exit anyway — measured — but the explicit raise makes the
    teardown ordered, so the forwarder is gone before the log closes
    under it.)
  - **`wait_budget`'s 25 ms signal floor is gone.** That floor was the
    honest limit on how much of wolf-lang#127's win a server that must
    notice a SIGHUP could take, and the function's own doc-comment said
    so. An armed loop now waits the same 250 ms an unarmed one does.
  - **Signal latency IMPROVES**, from within `sig_poll_ms` plus a pass
    to the wait's own return.
  - **D7 moves, and is still one sentence**: the serving LOOP is
    spawn-free, and `sig_forwarder` is the one proc beside it — two
    ints and a socket, touching no server state. The header, `docs/
    ARCHITECTURE.md` and `docs/DRAIN.md` say it that way now.
  - **The witness.** `tools/lobo-signal` goes 20 → 21 checks. The new
    one is the forwarder's own: every other check signals a server the
    harness is also talking to (`poll` opens a control connection every
    100 ms), so the loop's wait keeps returning for reasons that are
    not the signal. This one signals a server with nothing held,
    nothing in flight and nobody polling it — a loop sitting in its
    longest wait — and asks ONCE, after a fixed interval. Drop the
    forwarder's pipe from the wait set and it is the check that hangs;
    that negative control was run, and it does.
  - **The count, PREDICTED then MEASURED** (`docs/PROFILE.md`'s ws29
    addendum carries both tables; CI runs 34539376264 on trunk
    `9a4a905` and 34540847393 on `ws29@ece69e7`). The acceptance
    criterion is MET: `kill`, `getpid` and `rt_sigreturn` are gone
    from both shapes' tables — not 0.01, not 0.03, absent, because
    the calls are — and `write` falls with them. **The per-request
    totals barely move** (keepalive 6.28 → 6.26 against nginx's 6.15,
    the gap +0.13 → +0.11; close 12.27 → 12.27), and the prediction
    of 6.22–6.24 / 12.15–12.20 was WRONG. Reading the raw column over
    the same 8-second drive says why, and says two things the
    prediction got wrong in opposite directions:
    - the probe is gone — 4,113 and 4,053 calls a drive to zero;
    - **`poll` fell too, and by more than the probe did** (15,241 →
      10,727 keepalive, 60,975 → 45,768 close), which is
      `wait_budget`'s floor lifting 25 ms → 250 ms. Predicted
      unchanged; wrong, and in lobo's favour;
    - **`futex` ROSE** (3,205 → 6,608 and 11,770 → 13,861, with the
      error count going 539 → 6,593), which is the named risk landing
      on a row the prediction did not put it on. A task parked in
      `os_signal_wait` for the process's life costs the runtime's
      blocking compensation ~106 futex/s per process while doing
      nothing at all. **Filed as wolf-lang#302** — lobo has no cheaper
      spelling; the alternatives are the poll this replaced or no
      signal reception.
    - Net: **−5,224 and −17,169 calls a drive**. A win, and a smaller
      one than "the probe is gone" suggests.
  - **ws25's rule wants an amendment, and this entry is where it is
    written.** ws25 established the COUNT as the one linux number a
    shared VM holds still (identical across runs whose req/s spread
    13%). That held here for every per-REQUEST row — `read`, `statx`,
    `openat`, `writev`, `close`, `recvfrom` all read 1.00–1.01 in both
    runs, unmoved — and it does NOT hold for the per-TIME rows
    (`poll`, `futex`, `epoll_wait`, and the probe while it existed).
    The after-drive was slower for BOTH servers (nginx itself traced
    23% lower), so per-TIME work divided by fewer requests read higher
    per request and hid a real win. A per-request count is stable for
    work the REQUEST does and is a rate in disguise for work the CLOCK
    does; this is the first sprint to change one of the latter.

- **Item 2 — s149's two syscalls: NOT RUN, and why.** The contract
  makes it conditional on s149's dev sha existing. s148 merged into
  wolf-lang trunk at 23:02 on the day of this sprint and **s149 has no
  branch, no PR and no commit**; there is no sha to take. The item
  stops here, unstarted rather than half-done. `fs_open` with
  `O_NONBLOCK` in the router (`statx` 2 → 1 per request) and the accept
  posture (`ioctl` + `setsockopt` per connection) are still the two
  biggest named rows in the count table, and the next lane with a dev
  sha takes them the way ws24 took bd7caff.

- **Item 3a — lobo#2, the rig's filesystem half.** `tests/serve/
  budget_cap.lu` wrote its document root as the bare relative path
  `ws13_cap`, so 128 KiB of it landed in whatever the runner's cwd was
  — the REPO ROOT — and survived every corpus run as untracked debris
  one `git add -A` from being committed. It DID call
  `fs_remove_dir_all` at the end; that was never enough, because the
  remove is the last statement and every `?` above it leaves early
  (reproduced: `tools/lobo-corpus tests/serve/budget_cap.lu` left the
  directory on a fully green run). The scratch moves under `target/`,
  the one directory this repo already treats as disposable, in both
  that file and `budget_cap_e2e.lu`.
  - **And the gate, so the next one is caught rather than filed.** The
    gauntlet's census step — ws25's process assertion, lobo#1's — grows
    its filesystem half: `rig_census_fs` fails RED, by name, on a run
    that left a file in the tree. It is a DIFFERENCE, not an absolute:
    an author's new, not-yet-added test file is untracked too, and
    redding on that would make a new file impossible to commit under
    the gauntlet's own before-any-commit rule. So `rig_arm` records the
    untracked set as a run BEGINS and the census names only what
    appeared while it ran. Self-tested both ways.
  - `.gitignore` loses two trailing slashes. `.wolf-bin/` and
    `tests/differential/bin/` matched a directory only, and a lane
    stages both by SYMLINK from the main checkout — so every lane's
    worktree showed them as untracked, and they would have tripped the
    new gate on the first run.

- **Item 3b — lobo#4, the two stale pages: RE-READ, and mostly already
  fixed.** The re-read found the issue's own two items closed on trunk:
  `docs/ARCHITECTURE.md` was rewritten against the tree at `c1dad8c`
  (no `[stub; wsNN]`, no "intended call direction once real", no
  "honest edition: mostly stubs" survive anywhere), and `docs/
  DRAIN.md`'s transport paragraph already says "TWO transports since
  ws17" and carries its own note about superseding the ws15 text. What
  the re-read DID find is that the stale sentences moved into code
  headers nobody re-read with the pages:
  - `src/shell/shell.lu`'s header still said "wolf has no unix-domain
    socket at this pin (measured; wolf-lang#227), which is why the
    listener is loopback TCP on every host" — contradicted six hundred
    lines below by the module's own `is_unix_addr`/`unix_path_of` and
    by `net_listen_unix` in `main.lu`. `[os.net.unix]` landed at the
    ws17 pin and `unix:<path>` is the recommended default.
  - `src/proxy/proxy.lu`'s header claimed the locked direction
    `serve → proxy → {http, obs}`. lobo has never had the `obs` arrow
    — proxy raises no log line of its own; it answers and its caller
    logs. ARCHITECTURE.md's re-read says so and this header had not
    been re-read with it. It now names the arrows the `use` lines have:
    `{main, serve} → proxy → {config, http, resolver}`.
  - ARCHITECTURE.md's own residue, found by re-reading it rather than
    trusting the last re-read: it was pinned "at v0.1.0 / ws22" six
    sprints back; `src/main.lu` is ~3,700 lines, not ~3,500; the test
    section linked a `.docs/STYLE.md` that does not exist in the tree
    and listed two rig sub-harnesses where there are five, omitting
    `acmeca/`, `dnssrv/`, `rigback/`, `tests/config-corpus/` and
    `tests/cve-corpus/`; and `PROFILE.md`, `REPLAY.md` and
    `GETTING-STARTED.md` were in `docs/` but in no link table. All
    fixed, and the three GENERATED pages are now labelled with their
    generators so a reader knows not to hand-edit them.

- **The toolchain, again, and it is a standing hazard.** The main
  checkout's `.wolf-bin` held lupin **0.1.27** where `wolf-toolchain.
  toml` pins **0.1.29**, so `lib-toolchain.sh` refused every tool in
  this lane on identity drift — the same shape ws28 hit with the wolf
  half. The pair was built as the pin's own notes say (a scratch
  worktree of wolf-interp at the v0.1.29 tag, `cargo build --release
  --bin lupin`, giving `lupin 0.1.29 (wolf-interp, reference
  interpreter at pin e9a17cb)`) and staged into THIS worktree's own
  `.wolf-bin` beside the 0.2.9 wolf pair, the std tree symlinked from
  the main checkout (STD-REV `bd12ef5`, the pin's). `tools/lobo-stamp
  --check` reads `+dev` on the channel, as a lane's build must. A lane
  that takes the main checkout's staging on trust starts red.

## ws28 — 2026-09-10 — the string runtime (the strings on the serving path, counted; the ones lobo stops paying)

The bar is `docs/PARITY.md` (ws22, unchanged; the ws23 refusal scope
applies). ws27 left the linux keepalive cell at 1.72x–1.82x with the
count settled (6.31 calls against nginx's 6.13) and the profile
reading kernel 64 / lobo 22 / libc 13.5, a third of the request user
space and most of that the runtime materializing strings
(wolf-lang#191's seam). This entry counts those strings by source
line, PREDICTED before any run, then says which rows lobo can stop
paying with no new wolf surface, predicts the delta per row, and
measures. Every number below was written before it was measured, and
the entry says which. The macOS box was not confirmed quiet (load
2.2–2.4 at the open with the user's daemons on it), so every macOS
set and profile is INDICATIVE and named so; the linux numbers are
the CI runner's.

- **The toolchain, first.** The main checkout's `.wolf-bin` held the
  0.2.8 pair (wolf 5c729e8, lupin 0.1.27), not the 0.2.9 pair the pin
  names, so `lib-toolchain.sh` refused every tool. The pair was built
  as `wolf-toolchain.toml` says — `cargo xtask dist` in a scratch
  worktree of wolf-lang at the v0.2.9 tag (the D57 stamp: `wolf 0.2.9
  (wolfgang, pin 4c60946)`, paired with lupin 0.1.29 pin e9a17cb) and
  `cargo build --release --bin lupin` at wolf-interp's v0.1.29 tag —
  and staged into THIS worktree's own `.wolf-bin` (the std tree
  symlinked from the main checkout: STD-REV bd12ef5, the pin's), the
  main checkout's staging left as it was found. Both scratch
  worktrees removed once the pair was staged.

- **Item 1 — the strings on the serving path, counted.** The unit of
  the count is the runtime's, read from `wolf_rt` at 4c60946: a
  materialized `str` is an `ambient_alloc` — a bump in the
  process-lifetime arena behind a mutex, never freed (#191) — and an
  interpolation is `strbuf_new` (a boxed Rust `String`), one
  `push_str` per segment (the `String` growing through `malloc`/
  `realloc`), then `strbuf_finish` (a second copy of the whole result
  into the arena, then the `String` and its box freed). So one
  interpolation of n bytes is **1 arena alloc, ~5 libc calls, 2n bytes
  copied**; `lower()` is a `String` + an arena copy; a slice, `find`,
  `starts_with`, `trim` and `bytes()` in a consuming position are
  views and cost nothing; a `List[byte]` built from `bytes()` in a
  `let` is a copy (`[mem.str.view.lend]`); every list header and
  every list growth outside a `region` is an arena alloc too. The
  request is the parity file's: `ab -k`'s 117-byte head (`GET
  /index.html HTTP/1.0`, Host, User-Agent, Accept, `Connection:
  Keep-Alive`), a 1 KiB `text/html` file, a 241-byte response head
  (nine lines, `lobo/0.1.0` as the token). PREDICTED per keepalive
  request, one row per operation, read from `serve.lu`, `http.lu`,
  `proxy.lu`, `obs.lu` and `main.lu` at c58b4f1 — A = arena allocs,
  M = libc malloc/realloc/free calls, B = bytes copied:

  | # | where | what materializes | A | M | B | what removes it |
  |---|---|---|---|---|---|---|
  | 1 | `net_read(fd, 4096)` | the runtime's zeroed 4 KiB `Vec`, then the 117-byte head copied into the arena | 1 | 2 | 117 (+4,096 zeroed) | a read into the arena or a caller buffer — RUNTIME |
  | 2 | `conn_step`: `buf = "{buf}{piece}"` | the head again, through a strbuf, with an EMPTY carry | 1 | 5 | 234 | `buf = piece` when the carry is empty — lobo |
  | 3 | `conn_step`: `conn_mod_plain` | `tls.no_sess()`'s six empty `List[byte]` headers, built for the error arms only | 6 | 0 | 0 | build the seam in the arms that write — lobo |
  | 4 | `head_cut` ×2 + `carry_has_head` per pass | 4–6 `find`s (a `StrSearcher` each), the bare-LF search over the whole buffer even after CRLFCRLF hit | 0 | 0 | 0 | an emptiness guard; the LF search bounded to `[0..m1]` — lobo |
  | 5 | `serve_request`: `conn_mod_plain`, `access_new` | six + two empty lists | 8 | 0 | 0 | the seam's is needed (the write); stays |
  | 6 | `parse_request` | `split_lines_strict`'s list (2), `empty_request`'s two lists (2), `target.lower()` ×2 for the absolute-form probe (2 A, 22 B), `name.lower()` ×4 (4 A, 30 B), hnames/hvals growth (2), `ci_contains` ×2 lowering `Keep-Alive` (2 A, 20 B) | 14 | 8 | 72 | interned lowercase names for the common set (views into rodata), an ASCII case-insensitive prefix test, an ASCII fold when the value is ASCII — lobo; the four lists stay |
  | 7 | `fill_req_acc` | `"{method} {target} {version}"` — a copy of the raw line the record ALREADY holds (48 B); `access_header` ×4 re-lowering names the parser lowered (4 A, 30 B); two list growths | 7 | 9 | 78 | keep the raw line; push the parser's names — lobo |
  | 8 | `proxy.resolve_need` (the ws13 wait check, every request) | `percent_decode`: a `List[byte]` (2) + 11 byte pushes + `str_from_utf8`'s arena copy (11 B); `normalize_path`: the segment list (2) + `"{out}/{s}"` (22 B); `plan`: none | 6 | 5 | 33 | a fast path returning the INPUT as a view when it holds no `%` / is already canonical — the bytes are identical, so exact — lobo |
  | 9 | `serve_request`: `percent_decode` + `normalize_path` again, `proxy.plan` again | the same pair a second time | 6 | 5 | 33 | the same fast path (both callers) — lobo |
  | 10 | `http.route` | `trace_new()`: SEVEN empty lists for a trace `route` never fills; the Decision's index list (1); `index_list` ×2 (2); `join_path(root, path)` — the fs path, ~96 B through a strbuf | 11 | 5 | 192 | the matcher split from the tracer so `route` builds no trace — lobo; the join stays (a new byte sequence; a norm→fs table is config-generation-bound, not this sprint) |
  | 11 | `is_file_warm` (warm) | a byte fold and one compare | 0 | 0 | 0 | — |
  | 12 | `serve_file`, before the head | `fs_open`'s CString (1 M); `fs_fstat`'s `List[int]` (2 A); `http_date(mtime)`: four `pad2` + the date (5 A, 90 B); the ETag: `to_hex` ×2 = 8 + 3 one-digit interpolations, then the tag (12 A, 120 B); `mime_for`: `extension().lower()` (1 A, 4 B); `now_date()` (5 A, 90 B); `"{size}"` (1 A, 8 B) | 26 | ~117 | 312 | a head cached beside the kind table (below); `pad2` as a view into a digit table; `lower()` skipped when the extension has no uppercase — lobo |
  | 13 | `serve_file`, the head | `hline` ×8 (8 A, 440 B); `head = "{head}{…}"` ×9, each copying the WHOLE head so far (9 A; 17+41+78+103+125+171+195+217+239 = 1,186 B into the `String` and again into the arena) | 17 | ~85 | 2,812 | the same cache: a warm file's head is one `str` for the second it is valid in — lobo |
  | 14 | the region block | `read_exact` (the body: a region list + 1,024 B — the file read itself); `head.bytes()` in a `let`: a 241-byte `List[byte]` copy (F-0072); `parts`; `net_writev`'s `Vec` | 0 (region) | ~3 | 1,265 | a `net_writev` that takes a `str` part / a formatted write straight to the socket — RUNTIME |
  | 15 | `main.lu` after the step | `AccRow { a: copy a2 }` — a deep copy of the record's two lists, with NO access output configured; `pass_accs` growth | 3 | 0 | 128 | push only when a sink exists — lobo |
  | 16 | the pass's own lists (`nfds` … `nwait`, `wfds`, `ready`, `pass_accs`) | ~18 arena allocs per pass ÷ ~7 requests per pass | ~2.6 | 0 | 0 | not this sprint |
  | | **per request** | | **~108** | **~245** | **~5.3 KB** (+4 KiB zeroed) | |

  Of the ~108 arena allocs, ~43 are the response head (rows 12–13)
  and ~200 of the ~245 libc calls are its interpolations; of the
  5.3 KB copied, 3.1 KB are the head, 1.3 KB the region block's
  (the body read, which is the file, and the head's byte copy), the
  rest the parse, the record and the two decode/normalize passes.
  The arena's 5.3 KB per request are RETAINED (#191): at 18k req/s
  that is ~95 MB/s of arena, a fresh 64 KiB chunk every ~12
  requests, which is the `brk` in ws27's count and the ~3% of page
  faults in its profile. PREDICTED after the no-surface changes
  (rows 2, 3, 4, 6, 7, 8, 9, 10, 12, 13, 15 built): **~30 A, ~10 M,
  ~0.4 KB** per request (the read's 117 B, the region copies, the
  route's join), the arena growing ~0.4 KB per request instead of
  5.3. PREDICTED delta in req/s, two trees on one VM (`LOBO_REF`): the
  string share ws27's profile read on this cell (`malloc`/`cfree`/
  `realloc`/`finish_grow`/`reserve` ~4.7%, `ambient_alloc` +
  `strbuf_str` 3.2%, `StrSearcher`/`to_lowercase` 2.2%, the page
  faults ~3.1%: ~13% of a keepalive request at N=1) less what stays
  (~20% of the allocs, ~10% of the bytes, the lists): **N=1
  keepalive +8% [+4, +14]**, **N=4 keepalive +7% [+3, +12]** (the
  per-hand saving, four hands on four vcpus with the generators),
  **N=4 close +3% [0, +6]** and N=1 close +3% [0, +6] (the same
  absolute saving on a request twice as long: accept and teardown).
  The ratio on the fast VM class: keepalive 1.82x → ~1.70x, close
  1.365x → ~1.33x, NOT MET on both shapes still. The syscall count:
  unchanged on every row (nothing here touches a syscall; `brk`
  0.04 → ~0). The head bytes on the wire: identical, byte for byte —
  the differential harness is the guard. RSS growth over a 20k-request
  drive at N=1: ~106 MB → ~8 MB. MEASURED, the count first (host-
  independent; `tools/lobo-strings`, one process, 20,000 keepalive
  requests after a 2,000-request warm-up, RSS off `ps`): the pin
  retains **6,373 bytes per request** on the keepalive shape and
  12,934 on the close shape (the accept path's per-connection lists
  on top); ws28 retains **2,315** and **8,779**; nginx 0 on both.
  Before, the prediction (5.3 KB) under-read the list rows — a
  `List[str]` header is 48 bytes rounded and its first buffer 128,
  not the 40 and 0 the table carried — and the arena's 16-byte
  rounding; after, it missed by 1.9 KB and the miss is LISTS, not
  strings: every string row named above is gone (the profile says
  so, below), and the remainder is the runtime's own per-call list
  headers and eight-slot buffers — `tls.no_sess()`'s six (the seam
  the response writes through), the parser's four, the record's two,
  `fs_fstat`'s `List[int]`, the route's three, the loop's per-pass
  lists (~150 B per request amortized), the read's 117-byte arena
  copy — plus one the count FOUND: `metrics.hist_observe` built an
  eleven-element bucket list per observation (2,510 → 2,315 once it
  read its bounds by index; `tests/metrics/registry_shapes.lu` pins
  the two ladders equal). The rows that remain are all the runtime's
  (a wolf program cannot write a list without its header) and #191's
  (retained for the process's life). MEASURED, the macOS profile
  (INDICATIVE — load 3.3 before, 5.4 after; `sample`, one hand under
  `ab -k`, the main thread's INCLUSIVE counts per function): the
  string runtime — `strbuf_*` + `str_case` + `str_find` + `list_*` —
  **26.4% → 3.7%** of the thread (1,795 → 251 of ~6,800 samples), user
  space **36% → 12%**, `strbuf_str` 669 → 45, `strbuf_finish` 413 → 0,
  `str_case` 116 → 0, `ambient_alloc` 252 → 79, `memmove` 336 → 68,
  the `String` frees 425 → 55, `hline`/`http_date`/`to_hex` 375/355/
  248 → 0, `parse_request` 163 → 92, `normalize_path` + `percent_decode`
  120 → ~15; what the memo costs is `head_warm` 32 + `is_file_warm`
  52 + `head_cut` 25; the drive under the profile 58,771 → 71,908
  req/s (a heavier load on the second — the shares are the number,
  not the rate; `docs/PROFILE.md`, ws28's addendum, has the table).
  MEASURED, macOS two trees (INDICATIVE — refused on load 5.26 and on
  the oracle's N=18 keepalive spread; the ledger carries it named
  so): ws28 ÷ pin **N=1 keepalive 1.280x** [0.918, 1.300] (68,499 vs
  53,528 — past the top of the +8% [4, 14] band, on the one cell the
  profile was taken on; the band is this box's P/E-core swing on
  every N=1 row), N=18 keepalive 1.038x [0.909, 1.054] and N=18 close
  1.017x [0.973, 1.058] (the predicted shape: the hands are not
  cpu-bound here, 8.5 cores for 100k req/s), N=1 close 0.956x [0.868,
  1.096] (noise); fewer cores for the same req/s on every cell (4.54
  vs 4.69, 8.46 vs 8.56, 0.70 vs 0.78). MEASURED, linux (the
  result): run 34536710553 (`parity=true ref_tree=c58b4f1`, the
  profile leg on the keepalive shape and the count leg in the same
  job), a VALID set, load 1.72, on the runner's SLOWEST class (nginx
  close 25.2k — the ws27 pin set's class): ws28 ÷ pin **N=4 keepalive
  1.306x** [1.288, 1.322] (66,790 vs 51,044), **N=4 close 1.081x**
  [1.074, 1.089] (21,920 vs 20,273), N=1 keepalive **1.551x** [1.534,
  1.624] (29,307 vs 18,394), N=1 close 1.218x [1.190, 1.256]; the
  count leg in the same job: keepalive **6.37** against nginx's 6.14
  and close **12.38** against 10.13 — UNCHANGED (ws27 read 6.31 and
  12.41; the difference is `poll` 0.17 vs 0.15), `brk` 0.04 → 0.01
  as predicted (the arena growing at 2.3 KB per request instead of
  6.4); the profile leg: one hand under `ab -k` at **31,047 req/s
  against the pin's 18,625** in the perf window, the dso split
  **kernel 74.4 / lobo 18.2 / libc 6.9** against 64.1 / 22.6 / 13.1,
  `do_syscall_64` inclusive 68.9% against 55.2%, and the leaves that
  named the string runtime gone from the top of the table (`malloc`
  1.87 → under 0.4, `strbuf_str` 1.53 → 0, `to_lowercase` 0.40 → 0,
  `ambient_alloc` 1.71 → 0.85, `TwoWaySearcher` 1.10 → 0.67, `cfree`/
  `realloc`/`reserve`/`finish_grow` ~2.7 → under 0.4 together), the
  memo's own cost in their place (`head_warm` 0.70, `is_file_warm`
  0.67, `lower_token` 0.40). THE PREDICTION WAS WRONG BY A FACTOR OF
  TWO TO FOUR ON EVERY CELL, in the direction of the change: +30.6%
  against +7% [3, 12] on the gating keepalive cell, +55.1% against
  +8% [4, 14] at N=1, +8.1% and +21.8% against +3% [0, 6] on close.
  What it priced was the ~13% of a request that ws27's `perf` LEAVES
  summed under the string runtime's names; what it did not price is
  what a leaf table cannot show — ~110 arena bumps behind a mutex,
  ~245 libc calls and 6.4 KB of copies per request, retained forever,
  paid in cache lines and in the kernel's own fault path (`clear_page_
  erms`, `do_anonymous_page`, the `brk`) under kernel symbols the
  leaf count filed as the kernel's. The count that would have priced
  it right was the BYTES count, which this sprint built after the
  prediction was written; the next lane starts from it. The bar on
  this class: nginx ÷ ws28 **close 1.161x** [1.134, 1.168], **keepalive
  1.286x** [1.281, 1.298] — NOT MET on both shapes, the keepalive cell
  moved **1.687x → 1.286x** on one VM (the largest single move this
  ledger has recorded since the gathered write) and the close cell
  1.247x → 1.161x. W8's linux standing after ws28: NOT MET, close
  ~1.16x and keepalive ~1.29x on the slow class; macOS: ws26's MET,
  indicative at ws28. What is left on the keepalive cell, read from
  the ws28 profile: the kernel's transmit path (`writev` 39.5%
  inclusive, which nginx pays too), the file's open/stat/read/close,
  and ~18% lobo-release of which the runtime's remaining lists and
  `ambient_alloc` are ~2%, the searchers ~1.5%, and lobo's own frames
  (`serve_main`, `serve_request`, `parse_request`, the two tables)
  ~5%.

- **Item 2 — the ones lobo can stop paying without a new surface,
  built.** For each row above, does `std.strbuf`, a byte view or a
  pre-formatted head remove the copy? `std.strbuf` removes NOTHING:
  at this pin its `push_str` is `b.s += s` — the same interpolation
  seam, a full copy per append (its own header says so: "O(n·m) where
  the SSO builder is amortized O(n+m)"), so a head built through it
  costs exactly rows 12–13. A byte view removes rows 8, 9, parts of
  6, 7 and 12 (the answers that are the input's own bytes, or a
  literal's). A pre-formatted head removes rows 12–13. Built, in
  order, each its own commit:
  1. **The head cache, beside the kind table.** `serve.FileKinds`
     grows per slot the last head served for that path and what it
     was built from — the file's size and mtime (the fstat's answer),
     the second (the Date's), the keep token — and `serve_file`
     answers a warm request's head from the slot when THIS request's
     `fs_fstat` says the same size and mtime, the clock says the same
     second and the connection wants the same token; a miss builds
     the head as before and remembers it. Nothing a client sees is
     ever stale: Content-Length, Last-Modified and the ETag are
     validated against this request's own stat, and the Date against
     this request's own clock — the cache is a memo of a pure
     function of (path, size, mtime, second, keep), never a window.
     The Date string itself is cached per second beside the table
     (`http_date` is five interpolations), and `pad2` reads a view of
     a 200-byte digit table instead of interpolating. The wire is
     byte-identical (the differential and `tests/serve/static_get.lu`
     hold it); `tests/serve/head_cache_e2e.lu` is the contract: two
     requests in a second answer one head; a file rewritten to a
     different size answers the new Content-Length/ETag at once; a
     second later the Date moves.
  2. **The reader** (rows 2, 3, 4): `conn_step` adopts the read as
     the buffer when the carry is empty, builds the conn seam only in
     the arms that write, and `head_cut` answers an empty buffer
     without searching and bounds the bare-LF search to the bytes
     before the CRLFCRLF it found (a hit past it is never the marker;
     a hit before it lies wholly before it — exact).
  3. **The parser and the record** (rows 6, 7): header names are
     lowercased by an ASCII fold that answers a LITERAL for the
     twelve names a static request carries (`host`, `user-agent`,
     `accept`, `connection`, `content-length`, `transfer-encoding`,
     `if-modified-since`, `accept-encoding`, `cache-control`,
     `pragma`, `range`, `if-none-match`) and the receiver itself when
     it is already lowercase — a token is ASCII by `is_token`, so the
     fold IS `lower()` there; the absolute-form probe is an ASCII
     case-insensitive prefix test; the `Connection` token tests fold
     ASCII values and fall back to `lower()` for a non-ASCII one (the
     Kelvin sign lowercases to `k`; the fallback keeps that path
     exact). The access record keeps the raw line it already holds
     (identical to the interpolation for every request that parsed:
     the line is method SP target SP version by construction) and
     takes the parser's names without lowering them again.
  4. **The path** (rows 8, 9): `percent_decode` returns its input
     when no byte is `%`; `normalize_path` returns its input when
     every segment is non-empty and neither `.` nor `..` (a trailing
     empty segment is the preserved slash). Both are the identity on
     those inputs by the functions' own definitions —
     `tests/http/path_fast.lu` pins the fast path equal to the slow
     one on both sides of each rule, every lane.
  5. **The route** (row 10): the location matcher is one function
     returning what it matched; `route` builds a Decision from it and
     no trace; `route_traced` builds the trace after it, from the
     same match. The dry-run's trace is unchanged
     (`tests/http/route_trace.lu`).
  6. **The record's copy** (row 15): the entry pushes a pass record
     only when an access output exists to render it.
  PREDICTED per row (A / M / B removed per request): 1 → 43 / ~200 /
  3,124; 2 → 7 / 5 / 234; 3 → 11 / 17 / 150; 4 → 12 / 10 / 66; 5 →
  7 / 0 / 0; 6 → 3 / 0 / 128. Measured as one tree against the pin
  tree (`LOBO_REF`): the deltas above are the sum; the per-row split
  is by the count — `tools/lobo-strings` (new): the arena never
  frees, so a serving hand's RSS growth over a drive at N=1, divided
  by the requests the drive counted, IS the bytes materialized per
  request, on either host, and it is read per tree — not by req/s,
  which a VM cannot hold still row by row.

- **The rows that need a runtime surface, filed with the bytes
  beside them.** Row 14 (the head's 241-byte copy into a
  `List[byte]` so `net_writev` can carry it — 1 list and 241 B per
  request, and the only copy of the response left on the plaintext
  path), rows 1 (the read's 4 KiB zeroed `Vec` and its second copy)
  and the shape under rows 12–13 (an interpolation copies its result
  twice and a chained append copies the whole accumulator every time:
  9 appends of a 241-byte head are 2,372 B and ~45 libc calls; a
  builder whose `+=` appends in place — D24's SSO strbuf — is the
  surface `std.strbuf` is written to sit on) and `lower()` (eight
  calls a request materialize 82 B that are the receiver's own bytes
  seven times in eight; a `lower()` that answers the receiver as a
  view when nothing changes, or an ASCII `eq_ci`) — filed on
  wolf-lang, and the retained bytes per request posted on #191.

- **Item 3 — wolf-lang#289/#290: not landed this wave.** No dev sha
  was messaged; nothing adopted, nothing predicted.

## ws27 — 2026-09-10 — the linux half (the pin at 0.2.9, the count leg, what one syscall is worth)

The bar is `docs/PARITY.md` (ws22, unchanged; the ws23 refusal scope
applies). Every number below was PREDICTED in this entry before it
was measured, and the entry says which. The macOS box carried the
user's own daemons all day (the Photos indexer again; load 4–6 at
the open, per the orchestrator), no window was confirmed, so every
macOS set is INDICATIVE and named so; the linux numbers are VALID
sets and counts on the CI runner.

- **The pin moves to wolf v0.2.9 (4c60946, the release tag) and lupin
  0.1.29 (99feca3, the pairing wolf declares — the pairing gap is
  zero).** Fifty-one commits over one train (r12: s143, s144, s145),
  classed in `wolf-toolchain.toml` at the bump: s143's `parse` row
  for `str.to_int` — the one source-breaking change in 0.2.9,
  refused by name — is ZERO here (lobo never calls `to_int`; no
  `NotAnInt` in src/, tests/ or the pinned std tree, grepped); s143's
  `{x}` rendering every value and `channel[T]` in a signature are
  ADDITIVE (every hole lobo writes is a primitive or a str); s144's
  leading `else` is GRAMMAR-WIDENING with the formatter unchanged
  (lobo has no leading `else`), its `closed`/`cancelled` and `pop`
  → `none` rulings SPEC-SAYS-WHAT-THE-COMPILER-DID (lobo's `closed`
  rows are the net tier's, its one `pop` takes the row with an
  `else`); s145's `str + char` and closure `return` are ZERO here
  (lobo is spawn-free, D7, has no closure body, and its `else |e| {
  return … }` blocks are the defaulting operator, whose `return` was
  and is the enclosing function's). Runtime motion in the whole
  train: `str.rs` (the char-append path holes already had) and
  `task/conc_abi.rs` (a proc's int result rides its exit reason) —
  neither on the serving path; BEHAVIORAL-COST predicted none. The
  pair was built as the contract says: `cargo xtask dist` in a clean
  wolf-lang worktree at the tag (the D57 stamp: `wolf 0.2.9
  (wolfgang, pin 4c60946)`, paired with lupin 0.1.29 pin e9a17cb),
  lupin at its tag, both worktrees removed once the pair was staged.
  PREDICTED source motion for the pin's own sake: the `.wolfi`
  toolchain stamp (0.2.8 → 0.2.9 in every header, hashes re-derived)
  and the two `shell.lu` constants, ZERO item lines; `tcp_nodelay`'s
  row text unchanged (it cites #254 and `[os.net.nodelay]`, neither
  respelled). MEASURED: exactly that — fourteen `.wolfi` files, 88
  lines each way, every one a header stamp or a hash (the export,
  pkg and the six std dep-hashes, re-derived under the new driver),
  not one item line; `shell.lu` two lines; `tcp_nodelay`'s row byte
  for byte. wolf-lang#146 re-probed at this pin (the SIXTEENTH
  measurement): still the `sc_muladd` dominance ICE (`%19 is not
  dominated by its definition`, `wir verify error [dominance]`), so
  `WOLF_MIDEND=0` stays on the release step and the archive. THE LANE
  GAP, named: lupin 0.1.29's conformance pin is e9a17cb (past
  v0.2.8; s141's `net_writev`/`net_nodelay` are in its builtin table)
  but it does not name `fs_fstat`, so the static small-file arm stays
  native-only — lupin resolves a builtin at the call (probed at
  ws24), no lupin-lane test drives that arm, and the corpus at the
  bump is the measurement.

- **Both hosts re-measured at the pin.** PREDICTED before the
  dispatch: the pin carries nothing on the request path, so the linux
  ratio is ws25's fstat row inside the VM lottery, named by the VM
  class nginx's own close rate reports (28–29k: the ws25 class; 45k,
  56k, 75k: the faster ones ws24 met). On the 28–29k class, a single
  VALID set at N=4 c=32: close **1.26x** [1.22, 1.32], keepalive
  **1.65x** [1.58, 1.75]; N=1 close 1.35x [1.28, 1.45], N=1 keepalive
  1.60x [1.52, 1.70]; NOT MET on both shapes. macOS indicative (the
  box at load 4–6): close ~1.03x [0.98, 1.10] and keepalive ~1.10x
  [1.05, 1.40] at N=18, the keepalive cell the one the load moves
  (ws26: 1.36–1.62x loaded, 1.07x quiet), refused by the tool on
  load. MEASURED: (below, per host, when the sets return).

- **The count leg (`tools/lobo-syscalls`, new): what one request costs
  the kernel on BOTH servers, at the bar's own cell.** ws25 counted
  lobo's syscalls on the close shape at N=1 and never nginx's, and
  the profile leg (`tools/lobo-profile`) samples one hand under the
  close shape only; the linux keepalive cell is the larger half of
  the gap and nobody had counted it. The new tool attaches `strace -c
  -f` to every serving process of one server BEFORE the drive and
  detaches AFTER it (so the division calls ÷ completed requests is
  exact; req/s under ptrace is printed and is not a rate), lobo then
  nginx, `worker_processes N` both, and prints the union of syscalls
  per request side by side with the difference — lobo's extras on
  top. `ci.yml` grows `syscalls` (both shapes at N=nproc) and
  `profile_shape` (the profile leg can drive `ab -k` now;
  `tools/lobo-profile` takes the shape as its fourth argument). On
  macOS the tool skips by name (dtruss needs SIP down). PREDICTED per
  request at N=4 c=32 keepalive on the runner, from the source
  (`serve.lu`'s router and `serve_file`, `main.lu`'s pass, wolf_rt's
  `net.rs`/`fs.rs` at v0.2.9, nginx's `ngx_http_static_module` with
  `sendfile off` and `open_file_cache off`, its defaults):

  | syscall | lobo | nginx | what it is |
  |---|---|---|---|
  | `recvfrom` | 1 | 1 | the request; one read answers the whole head on both |
  | `statx` / `newfstatat` | **2** | **1** | lobo: the router's `fs_is_file` PATH stat (the fifo guard) + `fs_fstat` on the handle; nginx: `fstat` on the fd it opened |
  | `openat` | 1 | 1 | the file, both |
  | `read` / `pread64` | 1 | 1 | lobo `read` (the size the fstat named), nginx `pread64` |
  | `writev` | 1 | 1 | the response, one gather each |
  | `close` | 1 | 1 | the file, both (the socket lives on) |
  | `poll` / `epoll_wait` | ~0.5 [0.25, 1.0] | ~0.5 [0.25, 1.0] | one wait per PASS; eight connections per hand under `ab -k`, several ready per pass on both |
  | per connection, amortized | ~0 | ~0 | lobo: `accept4` + `ioctl(FIONBIO)` + `setsockopt(TCP_NODELAY)`; nginx: `accept4(SOCK_NONBLOCK)` + `epoll_ctl` + `setsockopt(TCP_NODELAY)` on the first keepalive response — thousands of requests per connection at `-t 8` |
  | **calls per request** | **~7.5** | **~6.5** | **lobo − nginx ≈ +1.0: the router's path stat** |

  On the close shape, the same plus the accept: lobo `accept4` 1,
  `ioctl` 1, `setsockopt` 1, `close` 2, `poll` ~1.5 (the pass's wait
  plus the zero-budget probe before every accept after the first in a
  burst, ws25 read 1.06 at N=1) ≈ **12.2** (ws25's number); nginx
  `accept4` 1, `epoll_ctl` 1, `close` 2, `epoll_wait` ~1, and no
  `setsockopt` (nginx sets `TCP_NODELAY` only when a connection goes
  keepalive) ≈ **10**; lobo − nginx ≈ +2: the path stat, and the
  `ioctl` + `setsockopt` + the probe `poll` against nginx's one
  `epoll_ctl`. The prediction the whole item rests on, stated so it
  can be wrong: **the keepalive gap is NOT in the count** — one
  syscall of ~7.5 at ~3.5% per syscall (ws25: three fewer read as
  +10.5%) is ~3–4% of a 1.65x gap, and the rest is the cost per call
  (`poll` over eleven fds against `epoll_wait`; `writev` and `close`
  are the kernel's and nginx pays them too) and lobo's user space
  (the runtime's string materialization, ws22's ~5 of 63 µs). The
  profile leg on the keepalive shape (`profile_shape=keepalive`,
  dispatched in the same job) is what says which. MEASURED (run
  34504504973, the same VM as the pin's set, both shapes at N=4
  c=32; the first cut of the tool printed a doubled total by counting
  strace's own `total` row as a syscall — fixed, the per-syscall rows
  were right): keepalive **lobo 7.41, nginx 6.14, +1.27** — `statx`
  2.00 vs `fstat` 1.00 (the router's path stat is the +1.00, exactly
  the prediction), `read` 1.02 vs `pread64` 1.00, `recvfrom`/`openat`/
  `writev`/`close` 1.00 each on both, `poll` 0.15 vs `epoll_wait` 0.13
  (the pass's wait serves ~7 requests on both — the loop shape is
  nginx's), and the small change nginx has none of: the signal
  self-raise probe (`kill` + `getpid` + `rt_sigreturn` + `write`, 0.03
  each, 0.12 together — `sig_poll_ms` fires every ~33 requests at this
  rate), `futex` 0.06 and `brk` 0.04 (the runtime's), the accept side
  0.03. Close: **lobo 13.36, nginx 10.13, +3.22** — on top of the path
  stat, `ioctl(FIONBIO)` 1.01 and `setsockopt(TCP_NODELAY)` 1.01 per
  connection (the runtime's accept posture: std's `accept4` carries
  only `SOCK_CLOEXEC`, then a separate non-blocking ioctl, then Nagle
  off on every stream; nginx's `accept4(SOCK_NONBLOCK)` is one call
  and it sets `TCP_NODELAY` only on a connection that goes keepalive,
  so on this shape never), `poll` 1.28 (the pass's wait plus the
  zero-budget probe before every accept after a burst's first, 0.28)
  against nginx's `epoll_wait` 1.00 + `epoll_ctl` 1.13, and the herd's
  residue at four hands — `accept4` 1.08 (0.08 lost races answering
  EAGAIN), whose parks show as the reactor thread's `futex` 0.27,
  `epoll_ctl` 0.14, `epoll_wait` 0.13 and the eventfd `write`/`read`
  0.11 each: ~0.1 parks per connection, ~0.9 syscalls (wolf-lang#267,
  lobo#5: the count at N=4 on linux). The prediction held: the
  keepalive gap is NOT in the count — 7.41 against 6.14 is 1.21x in
  calls where the cell reads 1.72x in req/s — and the profile leg
  says where it is: one hand under `ab -k`, `perf` on the same VM,
  **kernel 64.2%, lobo-release 22.0%, libc 13.5%** (the close shape at
  ws25 read 76/14.5/9), `writev`'s transmit path 31% inclusive, and
  the leaves under lobo's own dso are the runtime's string work —
  `malloc`/`cfree`/`realloc`/`finish_grow` ~4.5%, `ambient_alloc`
  1.8%, `__wolf_rt_strbuf_str` 1.4%, `StrSearcher`/`TwoWaySearcher`
  1.7% (`str.find`), `to_lowercase` 0.5%, and lobo's frames
  (`serve_request` 0.9%, `serve_main` 0.9%, `parse_request` 0.5%,
  `conn_step`, `serve_file`, `http_date`, `hline`, `split_lines_strict`
  ~0.4% each). A third of a keepalive request on linux is user space,
  and most of that is the runtime materializing strings (wolf-lang#191's
  seam) — the number the next lane on this cell starts from.

- **The herd (item 3): nothing to build.** wolf-lang#267 gained no
  surface this wave — a lost race on a shared listener still parks
  through the reactor, and `net_deadline(fd, 0)` still clears the
  budget — so it is said and stopped at, as the contract wrote. What
  this sprint added to it is the linux count at four hands (above:
  0.08 lost races per close-shape connection, ~0.9 syscalls of parks),
  posted on #267 and lobo#5 beside ws24's eighteen-hand macOS number.

- **The one that needs no new wolf surface, built: the warm kind
  table.** Of the calls lobo makes that nginx does not, each is named
  with what removes it: the router's path `statx` (+1.00 per request
  on both shapes) goes with an `fs_open` that opens `O_NONBLOCK` (the
  way nginx opens, so a fifo answers instead of parking the hand and
  the classification moves to the `fstat` the handle already pays) —
  a wolf surface, FILED; `ioctl(FIONBIO)` (+1.01 per connection) goes
  with `accept4(SOCK_NONBLOCK)` in the runtime — no lobo surface, a
  wolf_rt change, FILED; `setsockopt(TCP_NODELAY)` on every accept
  (+1.01 per close-shape connection) goes with setting it lazily, the
  way nginx does — a runtime posture (#254's default), FILED with the
  count; the signal self-raise probe (+0.12) goes with a signal poll
  that does not park — a wolf surface, FILED; the probe `poll` and the
  herd's parks (+0.28, +0.9 per close connection) are wolf-lang#267's
  and stop there. The path stat is the only one lobo can remove
  alone, and it removes it by REMEMBERING: `serve.FileKinds`, a
  256-slot direct-mapped table (a byte-fold hash, one compare, never
  a scan) of the paths the router classified as regular files and
  when, threaded beside the resolver through `conn_step` → `step_serve`
  → `serve_request` → `handle_request` (one table per hand; one per
  connection on the standalone `serve_conn` path), answering
  `is_file_warm` from memory for ONE SECOND after a stat said yes and
  from `fs_is_file` otherwise. Only the KIND is remembered — size and
  mtime stay on `serve_file`'s `fs_fstat` on the handle it opens, so
  Content-Length, Last-Modified and the ETag are never a second old;
  negatives are never remembered (a file that appears is seen at once);
  a collision is a miss and a miss is the stat the router always paid.
  The exposure, named: a path swapped for a fifo with no writer inside
  the second parks the hand on the open (the guard's whole reason;
  nginx has none of it because of `O_NONBLOCK`, which is why the
  surface is filed); a path swapped for a directory inside the second
  is 404 from the handle's kind (the swap-under-us arm) instead of the
  301 the router answers once the window expires; a deleted file is
  404 from the open either way. Tests: `tests/serve/file_kinds.lu`
  (the table's contract, both lanes: cold stat, warm after a delete,
  expired after 1.1 s, a directory and a missing path answer no and
  are not remembered, a file that appears is seen) and
  `tests/serve/file_kinds_e2e.lu` (the real server: 200, the swap to
  a directory inside the window is 404, a deletion is 404, past the
  window the directory is 301). PREDICTED before the two-tree dispatch
  (this tree ÷ the pin tree `9a24fde`, one VM, the same toolchain):
  `statx` 2.00 → 1.00 per request on both shapes, every other count
  unchanged; N=4 keepalive **+3.5%** [+1.5, +5.5] (one call of 7.41,
  at ws25's ~3.5% per call on this host), N=4 close **+1.5%** [0,
  +3] (one of 13.36, and the close shape is accept- and
  teardown-bound), N=1 keepalive +3% [+1, +5], N=1 close +1.5% [0,
  +3]; the ratio 1.718x → ~1.66x on the pin set's VM class, NOT MET
  on both shapes still. MEASURED, macOS first (indicative — load 6.18
  at the start, refused on load; `LOBO_REF` the pin tree built with
  the same staged pair, 17:09Z): warm ÷ pin N=18 close **0.993x**
  [0.977, 0.998], N=18 keepalive **1.035x** [0.965, 1.306], N=1 close
  0.997x, N=1 keepalive 1.025x — the predicted sign on both keepalive
  cells (+3.5%, +2.5%) and noise on close, with nginx's own N=18
  keepalive numbers swinging 1.4x between pairs on this box, so it is
  a shape and not a number. MEASURED, linux (the result): run 34506393898
  (`parity=true ref_tree=9a24fde`, plus the count leg), a VALID set,
  load 1.95, on the runner's FASTEST class (nginx close 77.2k — ws24's
  75.4k class; the pin's own set that morning sat on the 25k class,
  so the two are read by ratio only): warm ÷ pin **N=4 close 1.021x**
  [1.011, 1.049] (56,369 vs 55,357), **N=4 keepalive 1.027x** [0.993,
  1.049] (129,474 vs 125,874), N=1 close 1.003x [0.983, 1.027], N=1
  keepalive 1.006x [0.979, 1.109]; the count leg in the same job:
  `statx` **2.00 → 1.00** per request on both shapes and every other
  row unchanged — keepalive **6.31** against nginx's 6.13 (+0.18: the
  probe, `futex`, `brk`), close **12.41** against 10.13 (+2.28: the
  accept posture and the herd). The two gating deltas landed inside
  their bands (+2.7% against +3.5% [1.5, 5.5]; +2.1% against +1.5%
  [0, 3]), the N=1 keepalive cell under its band (+0.6% against +3%
  [1, 5]) — one path stat is ~2–3% of a keepalive request on this
  host, a little under ws25's ~3.5% per call (that arithmetic was
  three calls on a slower class). The bar on this class: nginx ÷ warm
  close **1.365x** [1.346, 1.409], keepalive **1.822x** [1.744, 1.834]
  — NOT MET on both shapes, and the count now says why with nothing
  left in it: lobo is 6.31 calls to nginx's 6.13 on the keepalive
  shape and 1.82x slower, so the linux keepalive cell is the string
  runtime's third of the request (the profile above) and the kernel's
  per-call cost, not the number of calls. W8's linux standing after
  ws27: NOT MET, close 1.255x–1.365x and keepalive 1.718x–1.822x by
  VM class; macOS: ws26's MET, indicative at this pin.

## ws26 — 2026-09-09 — the quiet set (W8 MET on macOS; the load was the whole story)

The bar is `docs/PARITY.md` (ws22, unchanged; the ws23 refusal scope
applies). No code moved this sprint. The box went quiet at 20:20Z for
the first time in three waves and the one deliverable was to spend
that window on the macOS set this ledger has owed since ws22 —
refused on load at every attempt from ws23 on — and to state W8's
macOS standing from VALID rows only, beside ws25's linux rows.

- **Four sets at trunk `d0a1e67`, three VALID, one refused.** lobo
  0.1.0+dev at wolf 0.2.8 (pin 5c729e8), nginx 1.30.4, 5 pairs ×
  `ab -t 5`, c=32 over 4 generators, load(1m) read and recorded
  before each set and the box let back under 3.0 between them
  (1.83, 2.71, 2.65, 2.81). Sets 1–3 **VALID**; set 4 **REFUSED** by
  the tool, exit 3, on the gating cell's oracle spread (nginx's own
  five N=18 close numbers spread 1.168 against the 1.15 rule) — it
  is named in `docs/PARITY.md` and averaged into nothing. A refused
  set was not re-rolled: running until one comes back valid is the
  bias the ledger's own rules exist to refuse.

- **W8 is MET on macOS arm64, on both shapes.** From the three valid
  sets only, median of the set medians: N=18 close **1.033x**
  (across-set [1.032, 1.056], per-pair [1.010, 1.077]) and N=18
  keepalive **1.072x** (across-set [1.071, 1.084], per-pair [1.052,
  1.093]), against a bar of 1.10 — **6.1% and 2.5% inside it**. The
  three sets agree to ±1.2% and ±0.6%, tighter than the margin on the
  keepalive cell, so the verdict does not rest on one set landing
  well. Generators 0.26–0.38 cores against the 0.90 ceiling, nothing
  failed on any run of any set.

- **The load was the whole story on this host.** lobo answers 113k
  keepalive req/s at N=18 here against ~85k in ws24's and ws25's
  indicative sets, while nginx's own number moved only 115k → 122k;
  the macOS keepalive gap that read 2.76x (ws22), 1.62x (ws24's
  baseline) and 1.36–1.39x (ws24's pin and gather rows) is **1.07x**
  on a box nobody else is using. Nothing in lobo changed between
  ws25's macOS sets and these — trunk `d0a1e67` is ws25's docs
  commit. Every prior macOS number was a measurement of the other
  lanes, and the quiet-rig rule refused them for exactly that.

- **Two cells that are new, and are not the bar's business.** On the
  keepalive gating cell lobo reaches 1.07x while burning **fewer**
  cores than nginx (10.2 against 12.5) — the first cell in the ledger
  where it is nearer on both axes at once. At N=1 on the close shape
  lobo is **faster** than nginx (0.985x, 34.4k against 34.0k), the
  first sub-1.0 cell the informative row has held. The N=1 keepalive
  cell is still 1.47x adrift and is the per-request read/serve cost
  with no distribution in the way — the number a profile leg takes
  next.

- **W8 overall is NOT met, because W8 is both hosts.** macOS is met;
  linux is not (ws25: close 1.258x, keepalive 1.652x on the CI
  runner's VM class), and the keepalive cell there is the larger half
  of the remaining gap. "Met on macOS" is a sentence about macOS,
  which is what `docs/PARITY.md` says it is.

- **The oracle had to be rebuilt before a set could be taken.** The
  pinned nginx binary was absent from this box —
  `tests/differential/bin/` is gitignored, the machine's copy was
  gone (the main checkout's path was a self-referential symlink), and
  the cached source tree under the shared scratchpad had been emptied
  by a disk reclaim. `tools/lobo-parity` refused by name (`REFUSED —
  pinned nginx missing`, exit 1) until it was restored. Rebuilt by
  `docs/DIFFERENTIAL.md`'s documented one-time recipe at the pinned
  version, tarball SHA-256 verified against
  `tests/differential/NGINX-PIN` (exact match) and `bin/nginx -v`
  reading `nginx/1.30.4`; `make -j6`, under a minute, load 2.3. This
  is a deviation from the sprint's "no build before the sets" rule,
  taken because without the oracle there is no set at all and the
  rule was protecting a window that could not otherwise be used; it
  is recorded here rather than left silent. The differential's oracle
  is restored for every lane that follows.

## ws25 — 2026-09-09 — the profile leg (the leak gate, the gather read on one VM, the fstat)

The bar is `docs/PARITY.md` (ws22, unchanged; the ws23 refusal scope
applies). Every number below was PREDICTED in this entry before it
was measured. The macOS box was never quiet this sprint (load 5–11,
the other lanes' gauntlets and the user's own daemons; no window was
announced because the orchestrator said the floor had not moved), so
every macOS set is INDICATIVE and named so; the linux numbers are
read on ONE runner VM by the instrument this sprint built.

- **lobo#1 closed: a test that leaves a process is red, by name.**
  ws18's reaper matched argv[0] absolute under this root, and the
  corpus TESTS never met it: they spawn `target/lobo-debug` relative
  (no root in the command line), and `os_kill` is SIGKILL, so a test
  that trapped an assertion, or died at the runner's ceiling, left a
  master the reaper could not see and hands the master RESPAWNED as
  the reaper killed them — three lanes killed such masters by hand
  last wave, and one was alive at this sprint's open (5 h 30 m old,
  `target/lobo-debug serve -p . -c ws16_e2e/lobo.conf`, cwd
  `/private/tmp/ws24` — a worktree already deleted — two loopback
  listeners held). Four changes, one gate: (1) `tools/lib-rigproc.sh`
  gains the second arm of the marker — a RELATIVE argv[0] with a
  slash whose working directory is under this root (`/proc` on
  linux, one `lsof` on macOS, for those candidates only; a bare name
  and the pinned toolchain are never candidates) — reaps MASTERS
  FIRST and waits for them (a hand killed under a live master is
  replaced), then TERM, then KILL, then scans once more; and gains
  `rig_census` (name what is left, fail, kill nothing) and a
  process-group registry the exit trap takes down whole. (2)
  `tools/lobo-corpus` runs every lane under `timeout -k 5
  $LOBO_LANE_CEILING` (60 s) in the process group `timeout` leads,
  registered for the life of the run — the ceiling kills the group
  (TERM, KILL after 5 s), a signal to the runner returns from `wait`
  at once and its trap kills the same group — and after EVERY test
  file takes the census with three seconds of grace: a test that
  returned and left a process is red by name and reaped. It also
  keeps a lane's stderr and prints its tail on a red (an `assert`
  names itself there, and the runner used to throw it away). (3) The
  thirteen spawning tests spawn `{os_cwd()}/target/lobo-debug`, so a
  master they leave carries the root in argv[0]; `proxy_e2e` and
  `budget_cap_e2e` stop their master through its desk and WAIT
  instead of SIGKILLing it (the kill stays for a desk that does not
  answer). (4) The gauntlet's last step is the census: a step that
  leaked is RED there, by name, before the exit trap reaps. Proved
  by killing `prefork_e2e` mid-run four ways, the census empty after
  each: TERM to the runner (its trap killed the group), the ceiling
  at `LOBO_LANE_CEILING=4` (exit 124, group killed), `kill -9` on
  the runner then the next tool's `rig_reap_stale` (collected at
  once — the master is absolute now), and `kill -9` on the runner
  with nothing else run (the group died at the ceiling + grace).
  And proved by the gate itself: G1 of this sprint went red at
  corpus on `prefork_e2e [checked]` — a `trap(assert)` under load
  8 — and the per-file census named the master and two hands the
  trap had left, and reaped them; that is the red the issue asked
  for. Then the flake itself, chased for two hours because the gate
  kept catching it: `prefork_e2e` went red INSIDE the corpus runner
  5 times in 14 invocations (G1, G3, a sanity run, two runner loops;
  `trap(assert)` on either lane, or the native lane at the ceiling)
  and 1 time in 57 outside it (`conform-run` foreground and
  background, `wolf run`, with and without a re-stage, at loads 4–21).
  What the chase established, each with its instrument: (a)
  `conform-run --native` SWALLOWS the child's stderr (0 server lines
  on every native run, 45 on every checked one), so a ceiling kill
  on the native lane leaves no account; (b) neither rung surfaces an
  `assert`'s MESSAGE — `wolf run` prints the location only, the
  record carries the kind (and the checked machine a byte span),
  filed as a comment on wolf-lang#150 — so the test now prints a
  `step N` marker before each step (the record keeps stdout) and the
  runner maps a checked-lane `x-trap-span` to a line; (c) the two
  reds that carried server events trapped at two different steps
  (once with the hands just up, once right after step 4's `stop`),
  which is load meeting one-shot asserts and 6–10 s bounds, not one
  mechanism: the step-2 GET is a poll now and every bound in the
  file is ~2.5x wider (ceilings for a hung server, on a box at load
  5–20). Then G5 named it: with the markers and the span-to-line in
  place, the red said `step 3: distribution` and `prefork_e2e.lu:300`
  — the assertion that sixty connection-per-request GETs reach BOTH
  hands. This host distributes nothing over the shared listener
  (s137: the hands race, and a hand the scheduler has parked loses
  every race while it is parked), so on a loaded box all sixty went
  to one hand and the 2 s status poll that followed sent no more.
  The check keeps sending while it polls now, up to ~600 more; the
  assertion is unchanged. The runner-only concentration is recorded, not explained;
  what IS explained is the native lane's ceiling — the runner remakes
  the stage every run, so the native lane's compile is cold and
  inside its ceiling, and under this box's load the compile-plus-run
  passed 60 s five times (G3, G4, and three loop runs; the census
  found nothing behind any of them and the next lane ran at once),
  so the native lane's ceiling is 3x and a lane past 20 s prints
  its wall beside its verdict. And one more thing the short-ceiling
  proofs found: `timeout -k` TERMs the group and returns the moment
  its own child dies, so its KILL never reaches the REST of the
  group, and a master that took the TERM mid-`quit` absorbed it
  (master and two hands alive after a 3 s ceiling, caught by the
  census); the runner now TERMs and KILLs the group itself after a
  ceiling — at `LOBO_LANE_CEILING=2` both lanes die and the census is
  empty.
  Beside all that, `os_kill` being SIGKILL-only and no process-group
  surface existing in the language is the reason the whole gate had
  to live in sh: commented on wolf-lang#141 with the shape a test
  needs (`os_kill_with(h, meaning)` and a group to name).

- **lobo#6: the gather, read on ONE VM.** `tools/lobo-parity` takes
  `LOBO_REF=<binary>`: every pair then runs THREE fresh servers —
  this tree, the reference, nginx — the two lobos alternating their
  order pair by pair, and the table carries nginx ÷ each and the
  DELTA this ÷ ref with its min and max. `ci.yml` grows `ref_tree`
  (a second ref built beside the checkout with the SAME staged
  toolchain, in a worktree) and `profile` (the profile leg).
  The reference is a THROWAWAY branch, `ws25-copy-arm` (`965ddda`):
  trunk `7c99905` with ws23's copy back on the plaintext small arm
  — the body pushed byte by byte behind the head, one
  `net_write_bytes` — and nothing else, at the v0.2.8 pin. PREDICTED
  before the dispatch: gather ÷ copy on one 4-vcpu runner VM —
  N=1 keepalive **1.15x** [1.08, 1.25], N=1 close **1.08x** [1.03,
  1.15], N=4 keepalive **1.10x** [1.04, 1.18], N=4 close **1.04x**
  [0.98, 1.10]; the per-pair spread of the delta inside one VM under
  ±3%, so the delta is READABLE from the parity leg and lobo#6's
  "worse on linux" was the VM lottery (ws24's own correction). The
  reasoning: on macOS at N=1 the copy cost 13–16% of a 21–32 µs
  request — ~4 µs in situ, twice the 1.8 ns/byte microbench, the
  buffer's doubling reallocations and the cache being the rest — and
  the runner's core is ~2x slower per byte on a request ~2x longer,
  so the share is the same order; at N=4 the close cell is
  accept-bound and dilutes it, keepalive does not. The profile leg
  (`tools/lobo-profile`: `perf record` on the one serving process
  under the close shape, `perf report` by symbol and by dso, then
  `strace -c` on a separate drive) is dispatched in the same job so
  the SHARES sit beside the ratio: predicted, `writev` at the same
  count `sendto` had, the byte loop's self time present in the copy
  tree's profile and absent from the gather's, syscall shares
  otherwise identical. MEASURED, linux x86-64, run 34355608599, a
  VALID set (load 1.81, nginx close 28,337 — the pin run's class of
  VM): gather ÷ copy N=4 close **1.005x** [1.003, 1.017] (21,924 vs
  21,696; nginx ÷ gather 1.301x, ÷ copy 1.310x), N=4 keepalive
  **1.020x** [1.001, 1.034] (53,509 vs 52,708; 1.820x / 1.857x), N=1
  close 0.998x [0.977, 1.031], N=1 keepalive 1.014x [0.971, 1.058].
  The delta's own spread inside one VM is ±1.5% on the gating cells:
  the instrument reads to ~2%, the ~10% lobo#6 was filed on would
  have been plain, and it is not there — the gather is +0.5% / +2%,
  the two-and-two reading was two VM classes. **The prediction was
  wrong** (1.10–1.15x), and wrong for a reason worth writing down:
  it was made from macOS N=1 cells that the tool had REFUSED (the
  single-process P/E-core swing is 30%+ there), and this sprint's
  own indicative macOS set reads gather ÷ copy 0.989x [0.976, 1.036]
  / 0.999x [0.986, 1.095] at N=18 and 1.126x [0.618, 1.176] on the
  refused N=1 keepalive cell — a refused cell is not a number in
  either direction. **The number came from the parity leg.** The
  profile leg's `strace -c` (same run, `docs/PROFILE.md`) confirms
  the shape without a rate: 10,972 `writev` where the copy has
  11,065 `sendto`, every other count per request identical — and
  counts FOUR `statx` per file request, the fourth the runtime's own
  inside `fs_read_bytes`, which ws22 could not see and item 3
  removes. Its `perf report` tables were empty by a tool bug (the
  data file chowned away from the user that reads it), fixed the
  same day and re-run with the fstat pair. lobo#6 closed with the
  table.

- **`fs_fstat` consumed (wolf-lang#261, item 3).** `serve_file`
  opens FIRST and asks the handle — kind, size, mtime in one
  `fs_fstat` — where ws23 left `fs_size` and `fs_modified_ms` as
  two path stats ahead of a `fs_read_bytes` that opened the file
  again (and, inside the runtime's `fs::read`, fstat'd it once more
  for its buffer). Every arm reads through that handle (`read_exact`,
  the size the fstat named) and closes it on its own way out; the
  budgeted arms close it and hand the PATH to their proc as before;
  the streamed arm no longer opens a second time after the head. The
  router's `fs_is_file` stays (the guard against a blocking open on
  a fifo, which no stat after the open can be). `dryrun`'s probe
  takes the same shape. Per file request: three path stats → one,
  plus one fstat (nginx: one open, one fstat). PREDICTED: on the
  runner VM, fstat ÷ ref at N=1 keepalive **1.03x** [1.00, 1.06]
  (two `newfstatat` at ~1 µs each of a ~30 µs request), N=1 close
  1.02x [0.99, 1.05], both N=4 cells inside the pair spread — ws23's
  "within noise" still holds on the gating cells with the
  syscall-first runtime; `strace -c` shows `newfstatat` per request
  3 → 1. macOS indicative: N=1 keepalive +2–5%. MEASURED, linux
  x86-64, run 34362397588, a VALID set on the same VM class as the
  lobo#6 read (load 1.95, nginx close 28,860), fstat ÷ gather: N=4
  close **1.038x** [1.036, 1.041] (22,956 vs 22,094), N=4 keepalive
  **1.105x** [1.094, 1.111] (59,626 vs 53,985), N=1 close 1.090x
  [1.023, 1.100], N=1 keepalive 1.129x [1.127, 1.171] — every spread
  under ±2%, and ABOVE the prediction: three syscalls fewer per
  request (`strace -c`, same run: `statx` 4 → 2 — the fourth was the
  runtime's own inside `fs_read_bytes` — and `read` 2 → 1, ~15.3 →
  ~12.2 calls per request) is a tenth of a keepalive request on this
  host once the reactor trips are gone. ws23's "within noise" does
  not hold with the syscall-first runtime on linux. W8's linux cells
  read **close 1.258x** [1.240, 1.277] and **keepalive 1.652x**
  [1.638, 1.671] on this VM class (1.301x / 1.820x before it), NOT
  MET on both. The profile leg's `perf` tables came through this
  time (`docs/PROFILE.md`): the process is 76% kernel, `writev`'s
  transmit path a quarter and `close(2)` a sixth of it,
  `link_path_walk` halved, lobo's own frames under 1%. macOS
  (REFUSED on load 9.77, indicative): fstat ÷ gather N=18 close
  1.016x [0.998, 1.026], N=18 keepalive 1.102x [0.628, 1.544]
  (unreadable), N=1 close 0.980x, N=1 keepalive 1.082x [1.002,
  1.104] — the same sign, not a number.

- **The herd (item 4): nothing to build.** wolf-lang#267 has no
  surface this wave; ws24's number stands (64% of a hand at N=18,
  the losers' park is the reactor round-trip). Not re-probed.

- Gates, exit-code checked, none piped: G1 RED (exit 1 — the leak
  gate proving itself on `prefork_e2e`'s trapped checked lane; the
  census named and reaped its master and two hands), G2 **GREEN**
  (exit 0, 255/255, nothing left behind) → the lobo#1 and instrument
  commits; G3 RED, G4 RED, G5 RED (exit 1 each — `prefork_e2e` at
  the native ceiling, at the native ceiling, and the checked trap
  that G5's instrumentation finally named: step 3, line 300), G6
  **GREEN** (exit 0, 255/255, differentials 3/3, 8/8, 9/9, nothing
  left behind) → the fstat and hardening commits. CI: 34355608599
  (lobo#6's read, VALID) and 34362397588 (the fstat pair, VALID),
  both success, watched once each at `--interval 120`.

## ws24 — 2026-09-09 — the quiet box (refused at the bound), the syscall-first pin, one gathered write

The bar is `docs/PARITY.md` (ws22, unchanged; the ws23 refusal scope
applies). Every change below was predicted in this entry BEFORE it
was measured, then measured by `tools/lobo-parity` on both hosts,
the load quoted beside the number. The linux series is six VALID sets on
the CI runner (one per step, a control at the pin, one at the
v0.2.8 tag), against a baseline taken at trunk
`1318cfe` in this session (run 34307802770, load 1.97): close
**1.981x** [1.962, 2.028] (14,380 vs 28,783 req/s), keepalive
**3.178x** [2.954, 3.496] (30,361 vs 97,902), N=1 close 2.917x, N=1
keepalive 4.475x. The macOS series is INDICATIVE, every set refused
on load, for the reason the first item states.

- The quiet macOS baseline, owed since ws22, is REFUSED at the
  bound. The sprint's first deliverable was a set at `1318cfe`
  under the quiet-rig rule before any code moved: the window was
  announced to the orchestrator at 03:38Z with its bound (fifty
  minutes of waiting, then a refusal), the sibling lanes held their
  gauntlets, and a waiter polled `uptime` for load(1m) < 3.0. It
  never saw it — 4.98, 11.37, 8.48, 7.07, 5.41, 4.09, 6.14, 5.06,
  7.74, 8.00, 7.08 … 4.81 at 04:28Z — and the residents were the
  user's own `mediaanalysisd` (15–123% cpu the whole window) and
  `XprotectService` (~50%), plus one sibling's `cargo xtask ci`. So
  the set was refused by name, W8 stays UNMEASURED on macOS, and
  the orchestrator's call at the bound was no further window that
  night. One INDICATIVE set was taken at the bound (04:29Z, load
  3.92 at the start, 20 during it as the other lanes resumed; the
  tool refused it on load and on nginx's N=18 keepalive spread
  1.278): close 1.096x [0.937, 1.183] (19,093 vs 20,919), keepalive
  1.623x [1.508, 1.971] (60,950 vs 113,353), N=1 close 2.271x, N=1
  keepalive 3.180x (cells refused on their own spread). Beside
  ws23's four refused sets (1.067x / 1.637x) it is the same shape.
  The ledger carries the load beside every row. A quiet macOS set
  is still the first thing the next lane on this box owes; this
  sprint's macOS rows are indicative by the same rule and are never
  averaged in.

- The pin moves to the syscall-first runtime: wolf 398e5f5 (v0.2.6)
  → **bd7caff** (trunk, `0.2.7+dev.bd7caff`, D57 dev-stamped the way
  ws18 pinned 32f66bf), because r11 had not tagged v0.2.8 when this
  sprint reached its pin step (`git tag` tops out at v0.2.7, six
  commits behind, carrying neither #257 nor #254); the re-pin to the
  tag rides r11's landing. Forty-five commits over three trains,
  classed in `wolf-toolchain.toml`: **#257 closes** (`[os.net.io]`,
  every parking net call tries the syscall first and parks on
  WouldBlock only — BEHAVIORAL-COST-ONLY, the rows unchanged);
  **#254 closes** (`net_writev`, `net_nodelay`, and **TCP_NODELAY on
  by default** on every stream — two new builtins and one behavioral
  default); s140's `--help` and the E0301 std-root note
  (DIAGNOSTIC-ONLY); s139's sched admission (spec/xtask); r10's
  v0.2.7 and the docs passes (MECHANICAL: the `.wolfi` toolchain
  stamp). Predicted source motion for the pin's own sake: ZERO;
  measured: zero — the re-record moves every `.wolfi` header's stamp
  (0.2.6 → 0.2.7+dev.bd7caff), the export/pkg hashes and the six
  std dep-hashes (re-derived under the new driver, the ws18 shape),
  and NOT ONE item line in fourteen modules. lupin stays 0.1.27
  (the pairing gap is ZERO again — wolf@bd7caff declares 0.1.27; the
  LANE gap is named: `net_writev`/`net_nodelay` are not on the lupin
  lane until wolf-interp#67, and lupin resolves a builtin at the
  call, probed, so the lupin-lane tests that stage `serve` keep
  their lanes). wolf-lang#146 re-probed at this pin (the FOURTEENTH
  measurement): still the `sc_muladd` dominance ICE, `WOLF_MIDEND=0`
  stays. Predicted, from ws22's arithmetic (three reactor trips per
  request ~30 of 63 µs; ws23's one write took one; s141 measured
  53.3 → 21.2 µs at N=1 on this box under load with the two-write
  lobo): linux N=4 keepalive 3.178x → ~2.0x [1.8, 2.3] (lobo's hands
  are not idle — 3.16 cores — so the two trips' share of a request's
  cpu, ~35–40%, comes back as throughput), N=4 close 1.981x → ~1.7x
  [1.5, 1.9] (the accept keeps its park; the read/write trips go);
  macOS N=18 keepalive ~1.62x → ~1.25x [1.15, 1.4] (s141's 2.45x →
  1.60x and ws23's 2.55x → 1.64x remove overlapping trips, so the
  sum is less than the product), N=18 close ~1.10x → ~1.03x [0.98,
  1.08] (herd-bound; the losers still park), N=1 keepalive ~3.2x →
  ~1.6x [1.4, 1.9], N=1 close ~2.3x → ~1.15x [1.0, 1.3]. The
  TCP_NODELAY default gets no number of its own: lobo already wrote
  once on the measured path (ws23), so there is no second segment
  for Nagle to hold; on linux it retires the CLASS of stall.
  Measured, linux x86-64 (run 34311866103, load 1.99, a VALID set, against the session's baseline run 34307802770): keepalive **3.178x → 1.862x** [1.852, 1.870], lobo 30,361 → 52,818 req/s at 2.97 cores (nginx 98,529); close **1.981x → 1.300x** [1.290, 1.310], 14,380 → 21,879 at 2.01 cores (was 2.39; nginx 28,454 at 1.58); N=1 close 2.917x → 1.464x (6,545 → 13,150); N=1 keepalive 4.475x → 1.821x (9,558 → 23,748). Keepalive landed inside its prediction; close landed BELOW it (1.30x against ~1.7x [1.5, 1.9]): the winner of the accept race no longer parks either, and at four hands the winner's path is more of the cell than the losers' parks — the prediction charged the whole accept path to the herd. Measured, macOS arm64
  (REFUSED on load 7.53 — 14.7 during — and on nginx's N=18 keepalive
  spread 1.317; indicative, against the session's own refused
  baseline): keepalive 1.623x → **1.355x** [1.322, 1.385], lobo
  60,950 → 85,375 req/s at 10.23 cores (nginx 117,096 at 11.12);
  close 1.096x → **1.010x** [0.998, 1.043], 19,093 → 19,829 at 5.35
  cores (was 6.24; nginx 20,210 at 3.40); N=1 close 2.271x → 1.039x
  (12,083 → 27,807); N=1 keepalive 3.180x → 1.775x (21,513 →
  43,968). Every cell inside its prediction; the N=1 keepalive cell
  is the profile's own number — 21.5k → 44.0k is 46 → 23 µs, the
  ~20 µs two reactor trips were priced at.

- One gathered write, no copy (wolf-lang#254 consumed). ws23's
  `serve.one_write` copied the body behind the head's bytes at
  ~1.8 ns per byte (2 µs on the 1 KiB parity body) on keepalive up
  to 64 KiB and on close up to 4 KiB, and wrote twice above that,
  because the copy was priced against the stall and the second
  reactor trip. `net_writev` costs neither: the plaintext small-file
  arm now materializes the head's bytes in the response region
  (F-0072), MOVES the body behind them into a two-part gather (a
  push moves the list header, not its bytes — checked against the
  runtime: `__wolf_rt_net_writev` reads the part headers through the
  outer list, nothing is copied), and hands both to the kernel as
  one `writev(2)`. `one_write` and its size rules are RETIRED: every
  small plaintext response, either shape, any size to 64 KiB, is one
  syscall. Two arms keep their shape, each with its reason in the
  source: the TLS arm keeps the copy (the record layer seals a
  contiguous plaintext; the gather cannot reach a sealed socket, and
  the copy is ~1.8 ns/byte beside the seal's own per-byte work), and
  the budgeted arm (`budget.body_small`) keeps its two writes,
  because the gather's two-part list must live in the capped region
  beside the body (E1010 forbids storing it outside) and D40's
  envelope leaves that region exactly sixteen ledger units at a
  power-of-two body — `charge(N) = 16 × pow2ceil(N) − 16` under a
  cap of `16 × pow2ceil(budget)` — which is less than one list
  header; with TCP_NODELAY the runtime's default and a write into
  an empty buffer parking nowhere, its second write is one syscall
  on the budgeted path only, and re-deriving D40 with a constant for
  the gather is named residue. `tcp_nodelay` moves from
  `planned(ws02)` — twenty-two waves — to **implemented**, with the
  delta named in the table: nginx's default is `on` and applies to
  keepalive connections only; lobo's `on` is the runtime's posture on
  every accepted stream, and `off` puts Nagle back (`net_nodelay`
  on accept, both listeners), resolved first-server-else-http like
  the rest of the limits family, the -t half refusing a bad flag in
  the oracle's own words, a location-level row parsing and not
  applying (the L009 posture). Witnesses:
  `tests/serve/writev_sizes.lu` (four files at the retired bounds'
  edges — 4095, 4097, 65536, 65537 — served on both shapes and
  compared byte for byte; `tcp_nodelay` resolved through
  `serve.resolve_limits`), `tests/config/limits_directives.lu`
  (the flag's resolution and its -t diagnostic), and
  `tests/serve/keepalive_one_write.lu` kept as the clock. Predicted:
  the copy is ~2 µs of a ~21 µs post-pin request at N=1, so linux
  N=4 keepalive ~2.0x → ~1.85x and N=1 keepalive lobo +5–10%; close
  cells within noise (2 µs against an accept-bound request); macOS
  N=18 keepalive ~1.25x → ~1.15x [1.05, 1.25]. Measured, linux
  x86-64 (run 34316912557, load 1.91, a VALID set — on a runner VM
  2.3–2.6x faster than the pin's, nginx's own close 28.5k → 75.4k
  req/s): keepalive 1.862x → **1.929x** [1.892, 1.943], lobo 52,818
  → 118,854 (nginx 229,209); close 1.300x → **1.413x** [1.396,
  1.421], 21,879 → 53,768 (nginx 75,387); N=1 close 1.464x →
  1.510x; N=1 keepalive 1.821x → 2.081x. NOT the predicted ~1.85x:
  every ratio reads a few percent higher, and the VM change is the
  larger effect by an order of magnitude (the gather replaces a
  2 µs byte loop with one list and one syscall, and moved the
  macOS N=1 cells +13–16%), so the linux delta for this change is
  not readable off these two runs and this entry does not claim
  one; the same-box ratio is the statistic, and the runner is not
  the same box run to run. A second dispatch (run 34317432651, load 1.79, VALID on the gating
  cells, a third VM: nginx close 56.5k) read close **1.439x** [1.436,
  1.450] (39,205 vs 56,515) and keepalive **2.086x** [2.056, 2.117]
  (85,193 vs 178,211). A CONTROL at the pin commit, dispatched after both
  (run 34318089358, load 1.92, VALID, the slowest VM of the series:
  nginx close 25.6k), read close **1.296x** [1.283, 1.313] and
  keepalive 1.928x [1.860, 1.991] — two pin runs agreeing to 0.3%,
  two gather runs ~10% above them, and this entry filed that as a
  regression (lobo#6). Then the re-pin at the v0.2.8 tag (the next
  item: the same lobo source) read close **1.273x** on a sixth VM,
  the best close ratio of the whole series, with the gather in
  place. CORRECTED, in this entry rather than by rewriting it: six
  VALID sets on six VMs (nginx's own close 25.6k–75.4k req/s) spread
  1.27x–1.44x on close and 1.78x–2.09x on keepalive with no change
  to lobo, which is wider than any delta a 2 µs byte loop against
  one list and one syscall could carry. The prediction (~1.85x,
  close within noise) is neither confirmed nor refuted on linux —
  the runner cannot see a change of this size in either direction —
  and it is confirmed on macOS at N=1 (+13–16%, indicative). lobo#6
  stays open, downgraded from a regression to the instrument nobody
  has run (a linux profile leg: `strace -c` / `perf stat`, `writev`
  vs `sendto`, `drain_vectored` vs the byte loop); the change stands
  as measured. Measured, macOS arm64 (REFUSED on
  load 7.43 — 16.0 during — indicative, against the session's pin
  set): N=18 keepalive 1.355x → **1.369x** [1.352, 1.404], lobo
  85,375 → 84,154 req/s at 10.67 cores (nginx 115,005 at 11.18) —
  NOT the predicted ~1.15x, within the pair spread of no change;
  N=18 close 1.010x → 1.014x [0.982, 1.025] (19,829 → 20,100), as
  predicted within noise; N=1 keepalive 1.775x → **1.627x** (43,968
  → 50,842, +16%) and N=1 close 1.039x → **0.987x** (27,807 →
  31,321, +13%) — the copy's share of a single hand's request,
  larger than the ~10% predicted. The two cells disagree for a
  reason worth stating: at eighteen hands on this box lobo answers
  ~85k keepalive req/s at ~10.5 cores against nginx's ~115k at ~11.2
  with or without the copy, so the gap there is not per-request
  user-space cost at all — it is what a hand does between
  requests (the `poll` over a shared set, the parks), which the N=1
  cell never pays.

- The re-pin, at the tag. r11 tagged **v0.2.8** (`5c729e8`, trunk
  HEAD: s141 and s142) while this sprint was measuring, and the pin
  moved to it the same day as its own commit, the D57 release stamp
  granted at the tag (`wolf 0.2.8 (wolfgang, pin 5c729e8)`; lobo's
  `-v` says `built with wolf 0.2.8`; the channel stays `+dev`).
  bd7caff → 5c729e8 is nine commits: s142's `str.to_int` (#263) and
  `fs_fstat(fd)` (#261 — lobo's own ws23 filing, answered: kind,
  size and mtime from one metadata read on an open handle; the two
  path stats `serve_file` still pays are now foldable, and that is
  the next lane's line, not this pin's), the version sites, the
  CHANGELOG and the interface-pretty snapshot. Predicted source
  motion for the re-pin's own sake: zero; measured: zero (the
  `.wolfi` stamp 0.2.7+dev.bd7caff → 0.2.8 in fourteen headers,
  not one item line). Predicted numbers: none move — nothing on
  lobo's request path is in the nine commits. Measured, linux
  x86-64 (run 34321060660, load 1.88, VALID, a sixth VM — nginx
  close 45.3k): close **1.273x** [1.245, 1.303] (35,472 vs 45,342),
  keepalive **1.784x** [1.754, 1.860] (90,675 vs 163,157), N=1
  close 1.485x, N=1 keepalive 1.870x — nothing moved that the
  runner's own VM spread does not cover, and the close cell read
  the best ratio of the series with the gather in place (see the
  previous item's correction). Measured, macOS arm64 (REFUSED on load 5.26 —
  14.3 during — indicative): N=18 close 1.016x [0.804, 1.035]
  (20,781 vs 20,496), keepalive 1.387x [1.363, 1.458] (85,373 vs
  118,260), N=1 close 1.044x (31,469 vs 32,394), N=1 keepalive
  1.664x (52,104 vs 82,012) — against the dev-sha pin's 1.014x /
  1.369x / 0.987x / 1.627x, nothing moved, as predicted. wolf-lang#146 re-probed at the tag (the
  FIFTEENTH measurement): still open, `WOLF_MIDEND=0` stays. The
  pairing gap is zero (wolf@v0.2.8 declares lupin 0.1.27).

- The herd, re-probed only as far as the park cost moved — and it
  did not. ws22's probe shape on the pin tree (`8859ac9`, lobo's
  source untouched): eighteen hands, the close shape under four `ab
  -t 20 -c 8` generators (20,546 req/s summed; ws22 saw 19,300),
  `sample(1)` ten seconds at 1 ms on one hand's main thread, 7,931
  samples, load 7.7 (a one-thread profile's proportions survive a
  loaded box — ws22 measured that twice). Predicted: cvwait falls
  but stays the largest leaf, ~45–55% of the hand. Measured:
  `net_accept` **69.4%** inclusive (ws22: 58.5%), of which
  `__psynch_cvwait` under `reactor::submit → wait_on` is **64.0%**
  (ws22: 63.6%), `accept(2)` itself 2.6%, the caller's `kevent`
  2.5%, `net_wait` 18.3%, serving ~5%. **The herd is still 64% of a
  hand, to the tenth of a point** — above the prediction, because
  #257 removed the park a call made BEFORE its syscall, and a losing
  hand never had a use for that one: its `accept(2)` answers EAGAIN
  and it parks AFTER, against the 5 ms budget, and that park is the
  same reactor round-trip it always was. The `wolf-reactor` thread
  the N=1 keepalive shape no longer starts is running in every hand
  of a herd; what #257 bought the close cell is the WINNER's path
  (linux 1.981x → 1.300x, the cores 6.24 → 5.35 here), not the
  seventeen parks per connection. ws23's probe shape (watch the
  listener every 2nd/4th pass, a 1 ms budget) was not re-run: it
  priced knobs against a park cost that has not changed. What would
  move it, named and FILED, not built: a lost race that answers
  without parking — and `net_deadline(fd, 0)` CLEARS a budget
  (net.rs, `ms <= 0`), so nothing in the language asks for "try
  once, `timeout` on EAGAIN", the shape a level-triggered `net_wait`
  loop wants; that is wolf-lang#267, with lobo#5 holding lobo's
  side (the posture, the table, and the other lever: a wake the
  kernel distributes — `EPOLLEXCLUSIVE`, or `reuse_port` where it
  distributes, which is linux and not here). `docs/PROFILE.md`
  carries the table.

- Not done, by name: the linux profile leg lobo#6 asks for (the
  runner's VM spread is wider than the gather's delta, and only a
  profile on that host reads under it); consuming `fs_fstat` (the
  two path stats, wolf-lang#261 answered at the tag); the streamed arm's head still leaves
  before its first chunk (one more syscall per streamed response,
  no stall now that Nagle is off — a gather of head + first chunk
  is a dozen lines for the next lane that measures a large-file
  shape); D40's re-derivation; no `open_file_cache`; no stat cache;
  no quiet macOS set (the box, not the lane).

## ws23 — 2026-09-09 — the gap closes (ws22's list, in its order, a number beside each)

The bar is `docs/PARITY.md` (ws22, unchanged); every change below
was predicted in this entry BEFORE it was measured, then measured
by `tools/lobo-parity` on both hosts, the load quoted beside the
number. The definition question ws22 left open is settled first,
in `docs/PARITY.md` under *Refusal scope*: the validity rules are
read per cell, a refused N=1 cell marks its own rows and leaves the
gating verdict standing, and the tool implements it.

The baseline this entry measures against (trunk `023ec64`, taken
in this session): see the ledger rows dated 2026-09-09. The linux
series is four VALID sets. The macOS series is four sets the tool
REFUSED on the quiet-rig rule, every one: the box carried other
lanes' work for the whole sprint (a fuzzer at four cores, a VM, a
`rustc`, s141's own lobo bench, `mediaanalysisd`), the quiet-box
waiter never saw load(1m) under 2.8 in two hours, and the sets
were taken at loads 7.24 / 4.19 / 9.84 / 8.25 so the sprint would
have the shape of the number rather than nothing. They are
indicative, named as refused, and not in the ledger as results; a
quiet-box re-measure is the first thing the next lane on this box
owes. Read with that caveat, they move the same way linux did.

- One buffer, one write (lobo#3). A small static response's head
  and body left as two `net_write`s; on linux the second, small
  segment waited behind Nagle for a delayed ACK, 40 ms per keepalive
  request. Now the head's bytes are materialized in the response
  region and the body pushed behind them (~1.8 ns per byte: 2 µs
  for a 1 KiB body, measured at 300k iterations), one
  `net_write_bytes`, one reactor round-trip fewer. The rule
  (`serve.one_write`): every keepalive response up to the 64 KiB
  small-file bound takes the copy (40 ms against at most ~120 µs);
  a `Connection: close` response, which never stalls, takes it up to
  4 KiB where the copy costs about what the second round-trip did.
  The TLS arm writes one record the same way. The budgeted arm keeps
  its two writes: its region cap is exactly the ledger's charge for
  one body copy at a power-of-two budget (D40), and a second copy
  would breach a cap the meter had admitted. Named delta until
  wolf-lang#254's `writev`: a keepalive response between 4 and
  64 KiB pays the copy on every host, including the two that never
  stalled.
  `tests/serve/keepalive_one_write.lu` is the witness: eight
  keepalive requests inside 100 ms (stalled, they take 320+).
  Predicted, linux N=4: keepalive 110.9x → 3–4x (the stall is
  the whole number; lobo's keepalive lands at 2–2.5x its own close
  rate, 22–28k req/s against nginx's 86k), close 2.27x → ~2.1x (one
  reactor trip fewer of three). Predicted, macOS N=18: keepalive
  2.76x → 2.3x [2.1, 2.5] (one of three reactor round-trips per
  request gone, and at eighteen hands the round-trips are most of
  the 285 µs of cpu a request burns), close 1.15x → ~1.10x (a
  herd-bound cell; little of it is the write); N=1 keepalive 3.99x →
  ~3.5x, N=1 close 2.42x → ~2.2x. Measured, linux x86-64 (the
  runner, load 1.90, a VALID set, run 34296065145 against the
  session's baseline run 34294755111 at load 1.91): keepalive
  **110.7x → 3.315x** [3.215, 3.503], lobo 781 → 26,189 req/s;
  close **2.267x → 1.971x** [1.941, 1.985], 11,127 → 12,891; N=1
  close 3.410x → 2.695x; N=1 keepalive 44.1x → 4.525x (781 →
  7,667). The stall is gone; what is left on linux is the reactor
  round-trip (wolf-lang#257) and the accept path. Measured, macOS
  arm64 (REFUSED on load, indicative; load 4.19, the oracle stable
  on both gating cells, against the session's own refused baseline
  at load 7.24 and ws22's quiet set): keepalive 2.550x → **1.990x**
  [1.986, 2.044], lobo 44,864 → 61,082 req/s against nginx's
  121,715 (ws22's quiet 2.761x); close 1.105x → **1.085x** [1.029,
  1.097] (ws22's quiet 1.151x); N=1 close 2.875x → 2.018x, N=1
  keepalive 3.083x → 3.240x (the N=1 cell refused on its own
  spread in both sets). Predicted 2.3x and ~1.10x on the gating
  cells; the write was worth more than one round-trip in three.

- The stats. ws22 counted three per file request; there were four:
  `fs_is_dir` and `fs_is_file` in the router, `fs_size` and
  `fs_modified_ms` in `serve_file`, each a `stat(2)` of the path,
  against nginx's one `fstat` on the fd it opened. The router now
  asks `fs_is_file` first (what nearly every request names), so a
  file request pays three; a directory request pays the two it did
  (the index candidate is tried before the directory is stat'ed,
  nginx's own order), and what any request observes is unchanged: a
  fifo, device or socket under the root still never reaches an
  `open` that could block. The other two cannot go without a
  runtime call that answers kind, size and mtime at once, or an
  fstat on the open fd; filed as wolf-lang#261 with the number. Measured on
  this box at 100k iterations: two path stats cost 1.05 ms per
  100k, ~0.5 µs each, and a read-first shape (`fs_open` +
  `fs_read_chunk` + a confirming read + `fs_close`, the size taken
  from the read) costs the same as `fs_read_bytes` within noise,
  which is why the folding stops here. Predicted: within the bar's
  noise on every cell (one stat of ~0.5 µs in a 63 µs request; the
  method sees nothing under ten percent). Measured, linux x86-64
  (run 34296624364, load 1.85, VALID, against the one-write run):
  close 1.971x → 1.952x [1.925, 1.983], keepalive 3.315x → 3.297x
  [3.066, 3.522], N=1 close 2.695x → 2.684x, N=1 keepalive 4.525x →
  4.519x: within noise, as predicted (lobo's req/s rose 2–3% on
  every cell and nginx's rose with it). Measured, macOS arm64
  (REFUSED on load 9.84, indicative): close 1.085x → 1.079x [1.057,
  1.113], keepalive 1.990x → 2.007x [1.917, 2.053], N=1 close 2.018x
  → 1.890x, N=1 keepalive 3.240x → 3.369x: within noise, as
  predicted.

- The signal poll, on a budget. Every pass of a serving hand raised
  the probe meaning to itself and waited once on the runtime's
  queue, a real signal plus a cross-thread handoff, and a loaded
  hand's pass is one request long: at eighteen hands on the
  keepalive shape that was ~10% of a hand's time (`os_signal_wait`
  7.2% + `signal::raise` 3.0%, docs/PROFILE.md). The poll now runs
  when 25 ms have passed since the last one, the wait budget's own
  signal floor, so an idle hand polls exactly as often as before, a
  loaded one polls once per budget instead of once per request, and
  an operator's `kill -HUP` is seen within one budget plus one pass
  either way. Predicted, macOS N=18: keepalive 2.3x (after the one
  write) → ~2.1x and about one core fewer burned; close: the poll
  ran once per herd wake, so the cores column falls and the ratio
  moves little (the cell is accept-bound); N=1: within noise (one
  poll amortized over the many connections a saturated hand serves
  per pass). Predicted, linux N=4: keepalive a few percent, close
  within noise. Measured, linux x86-64 (run 34297057715, load 1.71,
  VALID, against the stats run): keepalive 3.297x → 3.258x [3.183,
  3.525], close 1.952x → 2.038x [1.939, 2.156], N=1 close 2.684x →
  2.968x, N=1 keepalive 4.519x → 4.419x — within the spreads on the
  gating cells, as predicted; this run landed on a faster runner VM
  (nginx's own close went 25.9k → 36.9k req/s, lobo's 13.3k →
  18.2k), which is why the statistic is a same-box ratio. Measured,
  macOS arm64 (REFUSED on load 8.25, indicative, the N=1 cell valid
  on its own rules for the first time today): keepalive 2.007x →
  **1.637x** [1.602, 1.695], lobo 60,996 → 75,482 req/s against
  nginx's 123,477, at 11.66 cores to nginx's 11.53; close 1.079x →
  **1.067x** [1.064, 1.076] at 6.78 cores (was 7.13); N=1 close
  1.890x → 1.934x, N=1 keepalive 3.369x → 3.259x. Predicted ~2.1x
  and "the cores fall, the ratio moves little": the keepalive cell
  moved 18%, twice the prediction, because at eighteen hands a
  pass IS a request and the poll was a full cross-thread handoff
  on every one of them.
- The accept herd, measured and not changed. ws22's profile put a
  hand at eighteen hands on the close shape 64% parked in
  `net_accept`: every hand wakes on the level-triggered listener,
  one wins, the rest park in the reactor against the 5 ms accept
  budget. Two knobs were probed on a throwaway branch
  (`ws23-herd-probe`, run 34297109312, linux N=4, 3 pairs each, the
  same runner VM; the second, third and fifth sets carry the
  previous set's load, 3.07–3.38, and are refused by the rule, but
  the direction is not in doubt): a hand joining the listener to
  its wait set every second pass took close from 1.954x to 2.225x
  and keepalive from 3.17x to 3.44x; every fourth pass took close
  to 19.2x (1,474 req/s) and N=1 close to 33.7x, because a hand
  that is not watching the listener leaves connections queued while
  the watchers serve; and the accept budget at 1 ms instead of 5
  changed nothing (1.955x / 3.19x against 1.954x / 3.17x), because a
  parked loser is woken by the next connection, not by its
  deadline. So wake-fewer costs and the budget is inert, on the
  host with four hands; the eighteen-hand cell is macOS's and is in
  the ledger when the box is quiet. The win the profile priced needs
  the runtime not to park a loser at all (wolf-lang#257, the
  optimistic accept; numbers posted there) or a wake the kernel
  distributes (`EPOLLEXCLUSIVE`, or `reuse_port` where it
  distributes), and lobo's free-for-all posture stands.
- Not done, by name: `TCP_NODELAY` and `writev` (wolf-lang#254,
  s141's); no `open_file_cache`; no stat cache (nginx's default has
  none, and a cached mtime is a different thing to serve); the
  budgeted arm's two writes (D40's envelope would need re-deriving
  first); no pin bump: no v0.2.7 was tagged during the sprint, and
  the one being cut carries neither wolf-lang#257 nor #254 (s141's
  PR #262, the syscall first and `net_writev` + `TCP_NODELAY` by
  default, landed after its release commit, unmeasured, and is
  0.2.8's), so the two-numbers-per-row re-measure rides that tag.

## ws22 — 2026-09-08 — the gap measured (the bar first, then the profile; nothing optimized)

W8 is nginx parity. This sprint wrote the bar down first
(`docs/PARITY.md`, committed before the tool existed), built the tool
that measures it as written (`tools/lobo-parity`; a `parity`
workflow_dispatch input runs it on the CI runner), and only then asked
where the time goes (`docs/PROFILE.md`, `sample(1)`, six profiles).

- The bar: both shapes (close, keepalive) gate; N = cpus at
  c = 32; five interleaved pairs of `ab -t 5`; the median per-pair
  ratio nginx ÷ lobo ≤ 1.10; on linux x86-64 AND macOS arm64; a set
  refused with its reason on load, generator ceiling, oracle spread or
  any failure. The first set on each host was refused: one `ab` is the
  ceiling on keepalive (0.93–1.04 cores), so the load is split across
  four generators now.
- linux x86-64, a valid set (the runner, 4 cpus): close 2.27x,
  keepalive 110.9x, NOT MET. lobo's keepalive on linux is
  781 req/s: one request per 41 ms per connection, the 40 ms
  delayed ACK meeting Nagle on lobo's two-write response. Nobody had
  taken lobo's req/s on linux before; macOS hides it (lobo#3).
- macOS arm64, the quiet box (load 2.55, after the last sibling lane
  left): close 1.15x [1.13, 1.19], keepalive 2.76x [2.65,
  2.77] at N = 18, NOT MET on both; 0.1.0's 1.50x/2.15x were one
  20k-request run and an `ab`-bound nginx. Two earlier macOS sets,
  taken under sibling-lane load, are in the ledger as REFUSED with
  their loads.
- Where the time goes, one process, keepalive, 63 µs/request:
  ~30 µs is the runtime's reactor round-trip (the serving thread
  parked in `__psynch_cvwait` 38% of the time, waiting for
  `wolf-reactor` to confirm a readiness `net_wait` had already
  reported, three times per request; the syscalls are 12%); ~16 µs
  file syscalls (one `open`, THREE `stat`); ~8 µs two `sendto`; ~7 µs
  user space of which lobo's own code is ~1.5. At eighteen hands on
  the close shape a hand is 64% parked in the accept herd. nginx's
  whole request on the same box is 19 µs. Profiled twice, loaded and
  quiet, and every proportion held within two points.
- wolf's vs lobo's: ~35 µs the language's, ~12 lobo's, ~16 the
  kernel's that nginx pays too. Filed: wolf-lang#257 (optimistic I/O
  in the runtime), wolf-lang#254 (no `TCP_NODELAY`, no `writev`),
  lobo#3 (the linux stall; one write per response is ws23's first
  change).
- The mid-end (`WOLF_MIDEND=0`, #146, re-probed: the thirteenth
  measurement, same ICE) is worth nothing measurable on lobo's
  parse + response-head path: 534/527/534 ms vs 546/542/536 ms per
  300k iterations, and 563/555/558 vs 570/571/555 on the quiet box.
  The compiler is not where the gap is.
- Trunk was RED at the stamp step before this sprint: `be46c61`
  landed past the `v0.1.0` tag without flipping the channel to
  `+dev`. Flipped here, as `lobo-stamp` prescribes.
- `tcp_nodelay` has been `planned(ws02)` in the directive table for
  twenty waves because the language cannot set it; the linux number
  is what that costs.

## ws19 — 2026-09-07 — the artifact (lobo gets a version, and an archive a stranger could run)

wsc07's second sprint, and the one W7 is actually about: *someone
other than us can run it*. What this sprint owed was a version, a
release workflow that builds from the pin, an archive that carries
what a first-time user needs, and a job that installs the PUBLISHED
archive on a clean machine and proves it serves. All four landed.

THE PIN, first, because the archive is reproduced from it. ws18
pinned wolf at a DEV-STAMPED trunk sha (`0.2.5+dev.32f66bf`) because
r09 had not tagged v0.2.6 yet. It has now, so this sprint takes the
v0.2.6 RELEASE TAG (`398e5f5`): a released tag is what a stranger
can reproduce and a dev stamp is not. The contract asked for the delta
to be measured rather than assumed, and it was: `32f66bf → 398e5f5` is
five commits (`a369b22` spec, `6919280` ledger, `b2880a4`
CHANGELOG, `e257914` release sites, `398e5f5` merge), ten files,
+325/−89, and under `crates/` exactly one, the interface-pretty
test snapshot re-recording its own toolchain stamp 0.2.5 → 0.2.6. Zero
compiler source, zero runtime source. So the tag cost this sprint no
source motion at all: what moved in lobo is the `.wolfi` toolchain
stamp (0.2.6, fourteen modules, ZERO item motion) and the pin
file's `version_line` losing its `+dev`. lupin went v0.1.26 → v0.1.27
(is38) alongside; the lupin lane gap narrows and this sprint does
not spend it. `net_wait`, `net_listen_with` and `os_cpus` now exist
on the reference machine, so tests that declared `lanes: native` for
those calls alone could widen, but widening a lane is a measurement
per test, routed as residue to the next maintenance sprint. Deltas
classed: ZERO behavioral, ZERO diagnostic, one mechanical.

THE VERSION, and the hole underneath it. lobo is 0.1.0 and
`-v` prints

```
lobo version: lobo/0.1.0 (built with wolf 0.2.6, pin 398e5f5)
```

That is nginx's prefix, wolf's parenthetical, and W7's acceptance
criterion met literally. `-V` adds the std tree, the tier posture and
the module set. The hole: a wolf program cannot ask what compiled it.
`wolf --version` gets its own stamp from a compile-time env its driver
reads; a wolf PROGRAM has no such input: `wolf build` takes no
define, the language has no compile-time environment read, and D33
forbids the build script that would write one. So lobo's provenance is
SOURCE: five constants at the top of `shell.lu`
(`release_version`, `release_channel`, `toolchain_version`,
`toolchain_pin`, `std_rev`). `tools/lobo-stamp` (a gauntlet step) is
what keeps that stamp
true: it holds every version site equal (`wolf.pkg`, the wire token in
`serve.default_opts`, the five constants, `wolf-toolchain.toml`'s
`[wolf] version_line` and `[std] rev`), and it holds the channel
against git's own tags. `""` claims to BE `v<version>` and is admitted
only when no such tag exists yet or it points at HEAD; `"+dev"` is the
answer everywhere else, and the gate is RED between the tag and
the commit that flips the channel, which is the design. Filed
upstream as wolf-lang#247: a builtin naming the compiling
toolchain, D57 for programs. The day it lands, two of the five
constants become that call and this tool stops holding them.

THE ARCHIVE. `tools/lobo-dist` builds with the toolchain
`wolf-toolchain.toml` names: `lib-toolchain.sh` refuses identity
drift before a line compiles, which is what "reproducible from the pin
file" *means*, and the failure the target exists to prevent is
building with whatever wolf a runner has. The build is the gauntlet's
release tier flag for flag (`WOLF_MIDEND=0` while wolf-lang#146
stands, TWELFTH measurement, still open). The archive is flat: the
binary, `conf/lobo.conf` (an nginx.conf serving `html/` on loopback
8080), `html/index.html`, an empty `logs/`, `GETTING-STARTED.md`,
README, CHANGELOG, `docs/`, LICENSE, and BUILD, the provenance
record the smoke reads back against the binary. The pack is the
reproducible-builds recipe (`--sort=name`, one `SOURCE_DATE_EPOCH`,
`--numeric-owner`, `gzip -n`) and the tool proves the pack half by
packing twice and comparing digests. GNU tar
is required for the pack, and its absence is a named refusal (macOS
ships bsdtar); UNPACKING needs nothing special, because a learner has
nothing special.

Measured on nomad-1 (aarch64-apple-darwin): just under 3 MB,
packed twice identical, and the whole build-pack-unpack-smoke cycle
runs in 7 seconds, cheap enough that it is a gauntlet step, so
the archive a stranger would download is proven on every commit rather
than at the tag. (No digest is quoted here on purpose: this file is
*inside* the archive, so an entry naming the archive's own sha256
would be a fixed point that does not exist. The `.sha256` beside each
asset on the release page is the one that means anything.)

THE SMOKE, twice. `tools/lobo-dist` ends by unpacking its own
archive somewhere else with the HOST's tar and running it as a learner
would: `-v` compared against the archive's own BUILD line, `-t -c
conf/lobo.conf`, serve, `GET /`, the body byte-compared to
`html/index.html`, the `Server:` header, then `-s stop` and a
liveness check that it actually went down. First run: `200`, 934
bytes, byte-identical, `Server: lobo/0.1.0`, `stop: shutting down
(generation 1)`. `.github/workflows/release.yml` then does it a second
time on a runner with no checkout at all (no lobo source, no
wolf, nothing but the published archive, curl and tar) after
verifying the `.sha256`.

THE WORKFLOW. A dist matrix over the two hosts wolf's RELEASE tier
serves (linux x86-64, macOS aarch64); windows x86-64 and linux
aarch64 are named refusals until s60c, in the release notes and
in `lobo-dist`, which refuses to produce an archive for a host whose
binary would not run. Every leg clones the pinned siblings and builds
the pinned wolf as `ci.yml` does, and if `WOLF_CI_TOKEN` is
absent this job FAILS. ci.yml may loud-skip because local
runs remain its gate; a release job that publishes nothing while
reporting green would report a release that does not exist. The release is
a DRAFT until a `publish` job counts the assets and refuses at fewer
than two archives and two digests (#226's shape, twice-proven
upstream). Notes are cut from this file by `tools/lobo-release-notes`
(#214's mechanism: wolf's own v0.2.1 and v0.2.2 shipped empty bodies
for want of it), and `workflow_dispatch` runs the same dist and smoke
jobs from any ref, so the workflow is exercised before a tag, which
is not a lane's to press.

A BUG THE SMOKE FOUND, of a shape this repo has seen before.
`lobo-dist`'s smoke `cd`s into the unpacked archive, and
`lib-toolchain.sh` resolves the toolchain as `.wolf-bin/wolf`,
RELATIVE. From inside the archive that is a bare `No such file or
directory`. It is ws18/lobo#1's shape (a tool that names its
binary relatively cannot be used from anywhere else), and it was
caught by RUNNING the smoke rather than reasoning about it. Fixed:
`lobo-dist` absolutizes `$WOLF` and `$LUPIN` before it goes anywhere.

AND A SECOND ONE, which only the other kernel could find. The
smoke asserted the `Server:` header with `grep -qi "^Server:
lobo/$version\r*$"`. In a POSIX basic regex `\r` is a literal
`r`, so under GNU grep that pattern reads *zero or more
`r`* and never matches a real CRLF header: macOS was green, linux
was red, and the archive built and served correctly on both. The
assertion now strips the CR instead of trying to match it. Two bugs
this sprint, both in the CHECKING code rather than the server, and
both found by running the thing on a machine that was not the one it
was written on.

WHAT W7 STILL WAITS ON. lobo is the only PRIVATE
repo in the org. The learner smoke is a clean-MACHINE test today (it
downloads with the workflow token) but not yet a clean-STRANGER
test, because an unauthenticated download of a private repo's release
404s. Making lobo public is the human's decision and no lane's to
take. Nothing in the workflow changes when it flips; the smoke simply
stops needing a token.

Also: lobo carries a LICENSE at last (GPL-3.0, byte-identical
to every sibling repo in the org; it was the only one without),
`docs/GETTING-STARTED.md` is the learner path the release's own CI
executes, and CLAUDE.md's host-tool list gains GNU tar and curl.

## ws18 — 2026-09-06 — the turn deletes itself (and it was worth more than the accept path)

wsc07's first sprint, and a maintenance one by contract: the human's
W7 charter (*someone other than us can run it*) is settled but does
not gate this work; ws19 and ws20 take it. What this sprint owed was
a pin bump, a deletion, a rig-hygiene fix, and the headline table
re-run with the workaround gone. The table came back bigger than the
fix was predicted to be worth.

THE MEASUREMENT, first. ws17 shipped an accept turn (nginx's
`accept_mutex` without a mutex) because `net_accept` parked a losing
hand in a blocking `accept(2)` after its readiness wait
(wolf-lang#242, filed by ws17 with the number the fix was worth:
11,622 req/s with the turn against 17,347 free-for-all, a predicted
1.49x). s138 closed #242. ws18 deleted the turn and measured the
same shape on the same box in one session: the same source built
twice, once at the commit before the deletion and once after (three
hands, `ab -n 6000 -c 32`, a connection per request, three runs each):

| build | runs | median |
|---|---|---|
| with the accept turn | 13,417 · 12,866 · 12,863 | **12,866 req/s** |
| free-for-all (ws18) | 25,470 · 23,663 · 21,443 | **23,663 req/s** |

1.84x. And the full table, both binaries, N=18, `ab -n 20000 -c
32`, a 1 KiB file, the pinned nginx/1.30.4 as the control:

| server | shape | with the turn | **free-for-all** | cores (turn → free) |
|---|---|---|---|---|
| lobo, 1 process | close | 13,203.76 | **13,508.27** | 0.65 → 0.69 |
| lobo, 1 process | keepalive | 10,264.27 | **9,501.84** | 0.58 → 0.58 |
| lobo, 18 hands | close | 13,557.26 | **16,120.62** | 0.84 → **3.08** |
| lobo, 18 hands | keepalive | 9,554.14 | **38,960.68** | 0.65 → **4.54** |
| nginx, 1 worker | close | 27,656.32 | 27,731.17 | 0.48 → 0.45 |
| nginx, 18 workers | keepalive | 72,960.48 | 86,432.66 | 1.95 → 2.04 |

Four readings. (1) The deletion is worth more than the accept
path. Eighteen hands on a KEEPALIVE load, which contains almost no
accepting at all, go from 9,554 to 38,961 req/s, 4.1x. The cause is
`shell.accept_wait_ms`, the turn's other half, not the thundering
herd; it capped the hand's WHOLE `net_wait` budget at the
turn boundary, so a hand serving thirty-two established connections
woke on the ROUND instead of on its own sockets. The workaround was
throttling the serving path to keep the accept path correct, and
nothing in ws17 could see it, because with the turn there was no other
posture to compare against. (2) `worker_processes N` is N-ish at
last: cores-used 0.84 → 3.08 on close and 0.65 → 4.54 on
keepalive. (3) One process did not move: 13,204 → 13,508 close,
inside the noise, which is the control: `accept_turn` short-circuited
at `hands <= 1`, so a single-process lobo never paid for the turn.
(4) On this shape lobo now passes this box's nginx at the same
count: three hands free-for-all serve 23,663 against nginx's 19,553
at eighteen workers. The keepalive gap (38,961 against 86,433) is
real, and it is W8's.

THE DELETION, inventoried. `shell.accept_turn`,
`shell.accept_wait_ms` and `shell.accept_slice_ms` are gone: 84
lines of pure surface (three functions and their clauses) and, with
the plumbing, `src/shell/shell.lu` net −106, three items out of
`shell.wolfi`
(77 → 74; the item key sets diffed BOTH ways, exactly three removed
and three signatures re-recorded, nothing else moved), the `--hands N`
flag off the hand's argv (14 elements → 12) and out of `Cli`, the
`hands` parameter out of `serve_main` and `spawn_worker`, four guard
sites out of the serving loop, and 57 lines of turn assertions out of
`tests/shell/worker_surface.lu`. What is left in `main.lu` is one
sentence: every hand keeps both listeners in its wait set on every
pass. What replaced the tests is the DELETION asserted (an argv
carrying `--hands` takes the ordinary unknown-option road; `--inherit`,
the one internal flag that outlived it, still refuses by name when
it rides alone) plus a new gauntlet check.

THE CHECK THAT REPLACED THE TURN is `tools/lobo-prefork`'s quiet
server, and it is the one #242 would fail: three hands free-for-all,
one GET, then two seconds of SILENCE, then every hand must still
answer its OWN control endpoint and the master must still read three
serving hands with no replacement. That is how #242 was found
(two hands, one GET, one hand never spoke again) and it is asserted at
the level lobo cares about. prefork
35/35 → 38/38, and it is a gauntlet step, so linux CI runs it too.
The distribution was re-checked and SURVIVES the deletion: 90
connections over three hands, 36/29/26 on macOS and 26/34/31
on the linux runner, free-for-all, against ws17's 28/32/31 through the
turn; the turn assigned slices by ordinal and the kernel does not, so
this had to be measured rather than assumed. Linux CI (9m45s) is
GREEN at the ws18 head: corpus 253/253, prefork 38/38 including the
quiet server (3/3 hands answering after the silence), the failover gap
1 ms.

Pins. wolf → trunk `32f66bf` dev-stamped (`0.2.5+dev.32f66bf`;
r09 had not tagged v0.2.6 at the pin step, checked: `git tag` tops
out at v0.2.5, seventeen commits behind this rev, so the either/or
takes the sha), lupin → v0.1.26 (is37, the byte has a domain), std
→ trunk `bd12ef5` (sc37's `std.net.listen_with`/`adopt_listener`/
`wait` and `std.os.cpus`). Twenty-one commits over two trains.
Deltas classed: ONE BEHAVIORAL (#242, and lobo consumes it as a
deletion), two DIAGNOSTIC-ONLY (#243, #238; lobo's sources draw
neither), one MECHANICAL (the `.wolfi` toolchain stamp 0.2.4 → 0.2.5,
fourteen snapshots re-recorded with ZERO item motion), and zero source
motion predicted and ZERO MEASURED, the first pin bump in this
repo's history that moves no source for the pin's own sake. The
PAIRING GAP is zero for the second time (wolf@32f66bf declares lupin
0.1.26); the LANE GAP is not: lupin 0.1.26 still conforms to
`982f857` (v0.2.4), so none of s137's builtins exist on the reference
lane and every test that names one still declares `lanes: native` (or
native+checked). wolf-lang#146 re-probed at this pin, the ELEVENTH
measurement: still open (the `sc_muladd` dominance ICE, reproduced
here), `WOLF_MIDEND=0` stays.

wolf-std#6, answered and DECLINED. sc37 wrapped the
acquisition half (`std.net.listen_with`, `adopt_listener`, `wait`,
and a new `std.os.cpus`) and asked whether lobo would move. It does
not, and the reason is the loop's own shape rather than inertia: the
serving loop is raw-fd end to end (one `net_wait` over a `List[int]`
holding the control listener, both http listeners and every open
connection, with the connection table as parallel lists indexed by
position), so a `Listener` would be built and immediately unwrapped
through `.fd` to enter the same set; the inherit PAIR would split
across tiers, because `os_spawn_with` is not wrapped
(std.process's `Command` question is open) and a master would spawn
through the builtin while its hand adopted through std; and every one
of the four is a pure delegate, so the move buys a spelling. The
posture is uniform and written into `wolf-toolchain.toml` where the
next lane will read it. lobo's preference on the `os_spawn_with`
shape, which sc37 asked for, is posted on the issue.

lobo#1, the rig reaps itself. `tools/lib-rigproc.sh` is new: a
reap at START of anything a previous run left behind and a reap at
EXIT of the run's own, armed by `rig_arm` in all eighteen tools that
start a process, on `EXIT`/`INT`/`TERM` so a red step, a Ctrl-C and
the 600 s tool ceiling are all covered, sc12's idempotency rule
applied to processes. The leak was not where you would guess:
`wolf run tests/rig/dnssrv/dnssrv.lu &` makes `$!` the DRIVER and the
listener its child, so the tools' `kill "$dnspid"` reaped wrappers and
orphaned helpers. MEASURED before the fix: three orphaned `dnssrv`
processes on this box, one 45 hours old and one from each of the
two gauntlet runs this sprint opened with: exactly one leaked per
run. After it: `rigproc: own, at exit — reaping 1 process(es)` and a
clean census; a planted orphan is met with `rigproc:
stale from an earlier run — reaping 1 process(es)` on the next tool's
first line. The marker is argv[0], never the rest of the command
line, and this repo paid for that distinction in the same hour: a
first cut matched the whole cmdline and killed the shell that had
merely TYPED `target/lobo-release` in a command. Every rig launch site
now passes an ABSOLUTE program path so the marker names THIS checkout
and can never reach another tree.

Suites. corpus 253/253 lane-runs (unchanged; the deletion
removes assertions from an existing file rather than a file), prefork
35/35 → 38/38, differential 3/3, proxy-differential 8/8,
control-differential 9/9, signal 20/20, membudget 17/17, resolver 9/9,
shell 15 probes (14 parity, 1 named delta, 0 red), and
metrics/logdiff/dryrun/confcheck/tls-interop/tls-renewal/acme green.
Gauntlet GREEN before every commit; GitHub CI (linux) read on every
push, with a live watch. The gauntlet's own last line is now
`rigproc: own, at exit — reaping 1 process(es)`, which is lobo#1's
measurement stated as a running total: one leak per run, and none
after.

One finding recorded as a negative. A single-process witness for
#242 was written, measured, and thrown away. It asserted that a take
against an emptied queue returns inside the listener's budget rather
than parking, which is true; it is also true at the OLD pin, because
one process cannot make the kernel say READY and then empty the queue
behind its own back. The park needs a real sibling. Proven by running
the candidate witness under a wolf built at `d6aeaca`: green there
too. The witness that survives is the quiet server above, which needs
three real hands and gets them.

## ws17 — 2026-09-04 — many hands, FOR REAL (the cores, and the order desk on a socket)

wsc06's closing sprint, and the one where D73's sentence (*lobo uses
all the cores, and a running lobo takes orders on every host*) stops
being a plan. ws16 built the many-hands machinery and MEASURED that
the cores stayed idle, filing four issues that named why. All four
landed upstream in one wave (s137 for #127/#233/#234/#235, s136 for
#227), and this sprint is lobo consuming them, plus the mechanical
tail the pin could not be separated from, plus one new upstream
finding the shape immediately produced.

THE HEADLINE, first, because it is the charter's evidence
(docs/WORKERS.md, `tools/lobo-prefork-bench`, this box: macOS 15
arm64, 18 cpus, N=18, `ab -n 20000 -c 32`, a 1 KiB file, the pinned
nginx/1.30.4 beside it, ws16's column last):

| server | shape | req/s | cores | ws16 req/s |
|---|---|---|---|---|
| lobo, 1 process | close | **11,277.81** | 0.69 | 37.37 |
| lobo, 1 process | keepalive | **10,324.18** | 0.67 | 576.21 |
| lobo, 18 hands | close | **12,329.98** | 0.84 | 69.60 |
| lobo, 18 hands | keepalive | **9,934.98** | 0.68 | 1,117.68 |
| nginx, 1 worker | close | 23,488.10 | 0.47 | 38,123.20 |
| nginx, 18 workers | keepalive | 83,831.08 | 2.18 | 111,383.38 |

Three readings. (1) The reactor gate is gone and it was the whole
story: one lobo process went 37 → 11,278 req/s on the
connection-per-request shape, about 300x, from `net_wait` alone.
ws16's loop blocked 25 ms in the control accept, 25 in the listener's
and 12 per open connection every pass, so it got roughly one accept
per 62 ms. lobo at one process is now within 2x of nginx at one
worker on that shape, a sentence this repo has never written.
(2) The kernel distributes: 90 connections over three hands as
28/32/31, every hand `serving` on ONE socket, `accepted=` on every
status row. (3) And N is still not N×, 12,330 against 11,278,
because of the accept turn below, whose cost was measured directly
(11,622 with the turn against 17,347 free-for-all, three hands).

Pins. wolf → trunk `d6aeaca` dev-stamped (`0.2.4+dev.d6aeaca`;
r08 had not tagged v0.2.5 at the pin step, checked: `git tag` tops
out at v0.2.4, so the either/or takes the sha), lupin → v0.1.25
(is36, the byte arrives), std → trunk `c0f75e8` (sc36's
`std.net.unix`). Sixty-three commits across three trains. Deltas
classed: one MECHANICAL-WITH-SOURCE-MOTION, one mechanical-only, five
ADDITIVE surfaces consumed on purpose, zero refused-by-name. The
source motion is s136's #231, where the eight byte producers answer
`List[byte]` now, and ws16's prediction that lobo would stay on
`List[int]` expires with it: 306 E0401s at the first build over 21
files, closed over 51 `.lu` files (381 `List[int]` declarations become
`List[byte]`, 201 reads widen with `b as int`, 221 writes narrow with
`x as byte`; `byte as char` is E0805 and bridges through `int`), and
47 `.wolfi` signatures re-record with ZERO item motion in any of the
fourteen. The int lists that are NOT bytes stayed int, one by one: OID
arcs, PEM block lengths, the resolver's expiry and fd tables,
sslcert's `der_at`/`der_n`/`leaf_n`, acmeca's index tables. The
mechanical-only delta is the toolchain stamp, 0.2.3 → 0.2.4. The pin
and the tail are ONE commit because neither compiles without the
other, and the `.wolfi` re-record rides the next one alone (the
repo's interface law forbids mixing); the gauntlet is green across the
pair. #146 re-probed a TENTH time: still the sc_muladd dominance ICE,
`WOLF_MIDEND=0` stays. A LANE GAP is named in the pin file: lupin
0.1.25 predates s137, so none of the five new builtins exist there and
every test that names one declares `lanes: native checked`.

Distribution: two shapes, both measured, one shipped.
`net_listen_with(addr, reuse_port, backlog)` (#234) is refused,
and the witness says why rather than the page: `tests/serve/
reuse_port_posture.lu` builds a live three-member group, dials it
thirty times and prints which member the kernel woke, `0/0/30`, every
SYN to the newest bound socket on macOS, so a prefork built that way
is ws16's posture with a different cause (on linux it would work, and
a server that picks its architecture per host is a server with two
architectures). What ships is inheritance (#235): the master binds
the http and TLS listeners and never accepts on them, `os_spawn_with`
hands them to every child as descriptors 3 and 4 in the config's own
order, and a hand adopts by POSITION; the numbering is the contract,
so the argv carries a count (`--inherit K`) and never a descriptor.
Replacements inherit the same socket, which is why the master holds it
for life, and why a `kill -9` no longer needs ws16's 78 ms failover:
the survivors are already accepting.

THE NEW FINDING, and it is the front gate now: wolf-lang#242.
`net_accept` awaits readiness with the socket's deadline and then runs
a blocking `accept(2)`. With N hands on one listener a single
connection wakes all N; one wins and the losers park in the syscall
until the next connection arrives, a hand alive at 0.0% CPU
answering no control verb and running no timer, which its master then
reaps and replaces. Found with two hands and ONE GET, isolated three
ways (the non-blocking ask does not park, the blocking one does, and
removing the connection handles from the wait set does not help).
Invisible under load, fatal on a quiet server. lobo's answer is
nginx's `accept_mutex` without a mutex: hands take 10 ms turns off
the wall clock, so exactly one hand has the listener in its wait set
at any instant and there is no race to lose. Two halves make it a
mechanism: the wait is CAPPED at the turn
boundary (without it a hand blocks 25 ms through its own 10 ms slice:
2,725 → 11,622 req/s when that landed) and a turn DRAINS up to 64
accepts, each after the first guarded by a zero-deadline `net_wait`.
It retires the day #242 lands: one pure function, its twin, and the
`--hands` flag come out.

Readiness (#127), and a correction to its number. One
`net_wait` over the control listener, both http listeners and every
open connection replaces the deadline ws16 armed on each; a connection
is STEPPED only when the wait names it. The floor is the SIGNAL
poll's: signals have no readiness handle, so
while reception is armed the wait cannot outlast a `kill -HUP`'s
latency, 25 ms, which is BETTER than ws16, where one pass was three
stacked accepts. Idle cost was measured, the same binary built twice
with only the wait swapped, 120 s idle holding one keepalive
connection: 0.32 s of cpu the ws16 way against 0.26 s, about 19%
and not upstream's 37x. lobo's idle loop was never busy; it was asleep
in a timer. What the deadline cost was WAKE LATENCY, and that is the
whole of the 300x. Quoting someone else's 37x here would have been
quoting someone else's workload.

Cores (#233). `worker_processes auto` reads `os_cpus()`, and the
number is SCHEDULABLE cores, quota- and affinity-aware, so a two-cpu
quota on a sixty-four-core host answers 2 where ws16's `/proc/cpuinfo`
row count answered 64 and started sixty-two hands that would never get
a core. The `io` row is not swallowed into a default. `shell.cpu_count`
and its pure twin RETIRE (they could not live there: shell is on the
lupin lane and lupin predates s137), and ws16's macOS notice with
them.

The order desk on a socket (#227), ws15's filing and ws16's
deferral. `control unix:<path>` (nginx's spelling) is now the
RECOMMENDED form, because file permissions are the boundary a loopback
port cannot be: every local user on a host can dial 127.0.0.1, which
is why ws15 grew the token arm. Under `worker_processes
N` each hand gets the sibling `<path>.wN`, so a HAND's order desk is
a uid boundary too, closing ws16's residue. Every row is named
rather than swallowed: `unsupported` refuses at startup under that
name (the
distinction #227 was filed to get), `exists` refuses without
clobbering a path lobo did not bind, and a path too long for
`sun_path` says so with the ~100-byte limit spelled out, measured
with a 126-byte scratch path, which is what a real prefix looks like.
`net_close` unlinks; a hand's socket is the MASTER's to remove before
a replacement, because the process that BOUND a path owns it. lobo
calls the builtins directly and says so: std wraps neither
`listen_with` nor `adopt_listener` (wolf-std#6 stands, sc37's).

Also. The master probes each hand at most every 200 ms; its probe
is a fresh connection every time, and at 25 ms that is ephemeral-port
pressure the master makes for itself; three transient failures reaped
a HEALTHY hand in an e2e run before the interval existed. `accepted=`
joins a hand's stanza head and the master's row (appended, nothing
renamed) because with one shared socket the only way to SEE
distribution is to ask each hand what it took. `/metrics` now lands on
a random hand, and the aggregation decision ws16 routed is re-routed
with the numbers that decide it: a `worker` label would multiply a
61-series exposition by N (1,098 series for one server on this box)
against the cardinality fence, while the master already folds two
facts on the control path and could fold the rest.

Witnesses. corpus 249 → 253 lane-runs
(`reuse_port_posture.lu` and `control_unix_e2e.lu` are new, native +
checked); `tools/lobo-prefork` 35/35 with the distribution counts
printed; every other suite count identical (differential 3/3, proxy
8/8, control 9/9, logdiff 4/4, signal 20/20, membudget 17/17,
resolver 9/9).

## ws16 — 2026-09-03 — many hands (prefork workers, D7 kept)

wsc06's second sprint, the first half of D73's sentence: *lobo uses
all the cores*. It ships the MACHINERY of nginx's `worker_processes`
(a master, N hands through `os.process`, supervision, fan-out, a
row per hand, a field per line) and it ships the MEASUREMENT that
says the cores are not used yet, with the two upstream filings that
name why.

Pins advance first, gauntlet green at the trio before a line changed
(suite counts IDENTICAL: corpus 238/238, differential 3/3, proxy 8/8,
control 9/9, logdiff 4/4, signal 20/20, membudget 17/17, resolver
9/9): wolf → trunk `31170d1` dev-stamped (`0.2.3+dev.31170d1`;
r07 had not tagged v0.2.4 at the pin step, so the either/or takes the
sha), lupin → v0.1.24 (is35, the byte in the mirror, one release
ahead of wolf's declared 0.1.23 pairing, forward-only), std →
trunk `f016303` (sc34: the byte tier is bytes, refused with
numbers; upstream's binary pin == data pin == 31170d1, so the
compiler pins agree exactly for the first time). Deltas classed:
one BEHAVIORAL, zero mechanical, zero refused-by-name. The
behavioral one is #224's: the checked machine now arms a deadline on
a reset socket (s135), so the rig residue D41 carried since ws14
(`region_measured.lu`'s swallow, `budget_cap.lu`'s drive order)
comes out. Retiring the swallow went red 1 in ~17 native runs and
taught the lesson: the rig closed the accepted socket over UNREAD
request bytes (an RST close), and the client's read raced the
reset; it now drains the request first (a FIN close on every host)
and reads its reply through `?` on both lanes. [type.byte] is zero
motion, measured (lobo's byte paths stay `List[int]` until sc35 lands
the producers, wolf-lang#231's numbers); no `.wolfi` moved for the
bump (the stamp reads the version, 0.2.3, not the dev suffix); the
`checked-refuses:` rows are UNTOUCHED (they name C1, not #224).
#146 re-probed a NINTH time: still the sc_muladd dominance ICE,
`WOLF_MIDEND=0` stays.

The measurement first, because it is the charter's evidence
(docs/WORKERS.md, `tools/lobo-prefork-bench`, this box: macOS 15
arm64, 18 cpus, N = 18, `ab -n 4000 -c 32`, a 1 KiB file, the pinned
nginx/1.30.4 beside lobo).

| server | shape | req/s | cpu s | wall s | cores used |
|---|---|---|---|---|---|
| lobo worker_processes 1 | close | 37.37 | 1.11 | 107.38 | 0.01 |
| lobo worker_processes 1 | keepalive | 576.21 | 0.35 | 7.18 | 0.05 |
| lobo worker_processes 18 | close | 69.60 | 11.90 | 57.77 | 0.21 |
| lobo worker_processes 18 | keepalive | 1117.68 | 1.06 | 3.82 | 0.28 |
| nginx worker_processes 1 | close | 38123.20 | 0.07 | 0.36 | 0.19 |
| nginx worker_processes 1 | keepalive | 73607.89 | 0.05 | 0.31 | 0.16 |
| nginx worker_processes 18 | close | 24158.09 | 0.80 | 0.47 | 1.70 |
| nginx worker_processes 18 | keepalive | 111383.38 | 0.28 | 0.34 | 0.82 |

Read the lobo rows twice. Cores used: 0.01 at one hand, 0.21 at
eighteen, so lobo is not CPU-bound at all. The serving loop is
DEADLINE-bound: each idle pass blocks 25 ms in the control
listener's accept and 12 ms per open connection's read step (the
ws04 shape every hand inherits), so a connection-per-request load
gets about one accept per pass. And the 1.9x from 1 to 18 hands is
NOT a second core: exactly one hand holds the listener at N=18
(`lsof` shows one LISTEN socket; one row says `serving`), because the
master's per-pass CONNECT probe lands on the serving hand's control
listener and wakes its accept, removing the 25 ms idle stall, which
doubles that one hand's pass rate. The other 0.20 cores are seventeen
standbys retrying a bind and answering probes. nginx at 1 worker
does 1000x the close-shape rate on 0.19 cores; at 18 it spends 1.70
cores because the kernel spreads the accepts.

lobo at 18 hands serves what lobo at 1 hand serves, on one core,
because the kernel is distributing nothing: the runtime binds
`std::net::TcpListener` with `SO_REUSEADDR` only (a second process's
bind of the same port is `io`, measured with a self-spawned child),
every runtime socket is CLOEXEC and `os_spawn` passes only stdio (a
spawned child's descriptor table holds ZERO TCP sockets, measured
with `lsof`), and `std.net.Listener` is a table index with nothing to
adopt. Filed wolf-lang#234 (SO_REUSEPORT / a listener option),
wolf-lang#235 (descriptor inheritance and adoption, the pair
`upgrade` needs too) and wolf-std#6 (the std half). nginx at the
same N scales because its workers share the inherited socket. The
number the bench ALSO produced, and routes: lobo is not CPU-bound,
0.01 of a core at one hand, because a spawn-free loop with no
readiness surface time-slices with deadlines (25 ms in the control
accept, 12 ms per connection step, every idle pass), so the
connection-per-request rate sits near one accept per pass; the 1.9x
at 18 hands is that stall removed by the master's own probe waking
the serving hand's accept, not a second core. wolf-lang#127 (the
reactor) gets the table as its customer report; the stall itself is
a maintenance row in the closeout, not ws16's.

The machinery, shipped. `worker_processes N | auto` carries with
nginx's grammar and nginx's `-t` diagnostic (probed); `auto` reads
`/proc/cpuinfo` on linux and is 1 with a notice on macOS (no cpu
query; wolf-lang#233); `0` serves as 1, a named delta. With
N >= 2 the process that ran `lobo serve` is a MASTER: it owns the
pid file and the config's `control` endpoint, binds no http listener,
starts N hands (`os_exe()` + `os_spawn`: this executable, `serve`,
the same prefix and config, `--worker i --worker-control <ep>`; no
secret crosses the argv, and a hand reads the `token <file>` itself), and
supervises them over their endpoints with a CONNECT probe (never a
round trip: `os_wait` blocks and there is no `try_wait`, so a hand's
socket is the liveness surface; a busy hand still answers from its
backlog). Three silent passes after a 3 s grace is gone: `os_kill`,
`os_wait`, `worker-exited worker=N reason=… code=…`, a fresh hand in
the slot, `worker-started … restarts=R`. Accept distribution at
this pin is the shape the measurement forces: every hand
RETRIES its bind each pass; the first to win serves, the others
stand by and take the listener the moment its holder dies.
`tools/lobo-prefork` kills the serving hand with a real `kill -9`
and measures the window: 78 ms (minus the clock driver's own 223
ms; a `wolf run` compiles per call, and the first reading of 718 ms
was the driver's, not the server's). The day #234 lands every hand's
bind succeeds and the same loop distributes accepts, no lobo change.

The verbs fan out (docs/CONTROL.md): `reload` is parsed by the
master first (D2 holds: a rejected config reaches no hand) and rolled
through the hands one at a time, each swapping and DRAINING in place,
the ws08 drain per process, watchable on that hand's own stanza;
`quit`/`stop`/`reopen` fan out; replies keep ws15's prefixes and gain
`workers=K/N`. Rolling PROCESS replacement is a named delta: lobo
cannot hand a socket to a new process (#235), so a spawn-new-retire-
old reload would refuse connections in the gap, and row 2 of the
control differential (zero refusals) is a row lobo keeps. The hands
are long-lived. A SIGKILLed master orphans its hands (no channel, a
named delta; `kill -TERM` is the orderly path, TERMINATE is `stop`
and `stop` fans out first).

A row per hand (docs/DRAIN.md, docs/WORKERS.md): `lobo status`
answers the master's head (`live-region-bytes` SUMMED over the
hands), `workers: N`, and `worker i: serving|standby|unreachable
control=… generation=… live=… events=… live-region-bytes=…
budget-503s=… restarts=…` folded from each hand's own stanza (a hand
prints `worker: N` / `listening: true|false` under its head); JSON
schema 1 stays, additive (`workers_configured`, an empty
`generations`, a `workers` array). The meter and the cap are per
hand (docs/BUDGET.md): the witness refuses a 24 KiB file under
`memory_budget 4k` on the serving hand, whose row reads
`budget-503s=1` beside siblings at 0. `/metrics` is one hand's
numbers and says which (`lobo_worker_id`, a new gauge; the
aggregation question is routed to the pin that carries #234).

A field per line (docs/LOGGING.md, docs/REPLAY.md): a hand ends
every line it emits in ` worker=N`, after `seq` on a vocabulary
event and at the end of a prose notice, appended, nothing renamed
(the ws15 line is a PREFIX of the ws16 line, asserted); the master's
lines and a single-process lobo's carry none, byte for byte. Two
events join the frozen vocabulary (`worker-started`,
`worker-exited`; nine → eleven). REPLAY.md's multi-process
boundary: `seq` is per PROCESS, so a merged log is N+1 total orders
separable by the stamp and orderable across each other only by the
wall clock; the completeness anchor is per stream (a hand's row
carries ITS `events`); the fan-out's order is reconstructible from
the master's stream alone.

The either/or on #227: the ELSE arm. s136 had not merged at Act-2
start (01:12 EDT: the issue OPEN, the worktree at 31170d1 with three
uncommitted corpus edits, no PR). Named-gate deferred to ws17, with
what lands then written down (the `unix:` address form, the token
arm demoted to windows, the hands' endpoints as unix sockets under
the prefix).

Windows: claimed, not measured; there is no lane. `os_spawn` runs there
and the runtime's sockets are non-inheritable there too, so the
posture would be the standby posture; stated as such in
docs/WORKERS.md.

Findings filed. wolf-lang#233 (no cpu-count query, so
`worker_processes auto` cannot ask the host), wolf-lang#234 (no
SO_REUSEPORT and no listener option, so N processes cannot accept on
one port), wolf-lang#235 (a spawned child inherits no listening
socket and std.net adopts no descriptor; the shared-listener shape
and `upgrade` both need the pair), wolf-std#6 (`listen_with` /
`adopt_listener` at the std tier). #146 probed a ninth time.

Corpus 238 → 249 lane-runs (`worker_processes.lu` ×3,
`worker_surface.lu` ×3, `prefork_e2e.lu` ×2, `nowms.lu` ×3); a new
gauntlet step, `tools/lobo-prefork` (32/32); `tools/lobo-prefork-
bench` (not gated; the table above); metrics registry +1 series
(`lobo_worker_id`). Branch `ws16`, unmerged.

## ws15 — 2026-09-02 — the server takes orders (and pays four small debts)

wsc06 "many hands" opens (D73: *lobo uses all the cores, and a
running lobo takes orders on every host*). This sprint is the second
half of that sentence.

Pins advance first, gauntlet green at the trio before a line changed
(suite counts IDENTICAL: corpus 233/233, differential 3/3, proxy 8/8,
signal 15/15, membudget 15/15, shell 13, confcheck 8): wolf → the
v0.2.3 TAG (`3befc3e`), and with it the bare stamp at last,
`wolf 0.2.3 (wolfgang, pin 3befc3e)`, built at the tag with
`WOLF_COMMIT=3befc3e WOLF_RELEASE=v0.2.3` so D57's release rule
grants it. lupin holds at v0.1.23 and std at trunk 35f69ef,
which closes the pairing gap to zero for the first time in this
repo's history: wolf@3befc3e declares lupin 0.1.23 as its pairing and
that is exactly the release staged beside it. v0.2.2..v0.2.3 is six
commits and ws14 already pinned five of them, so the delta lobo takes
is r06's release train only: #212 (dist writes one archive per
target), #214 (release notes cut from the CHANGELOG), #215 (nine
literal productions, anchors held 411), #225 (filed upstream), none
of which lobo's sources reach. Deltas classed: zero behavioral, one
mechanical, zero refused-by-name. The mechanical one is the
release commit's own: every `.wolfi` header embeds the toolchain
version by design, so all fourteen snapshots re-record `toolchain
0.2.2` → `0.2.3` and their export/pkg hashes and std dep-hashes
re-derive under the new driver, with zero item motion (verified:
not one `[n]` line moved in the diff). #146 re-probed an EIGHTH
time, still open, `WOLF_MIDEND=0` stays.

The control endpoint takes orders. ws04 built a loopback reload
pipe and left a question; D73 asks it properly. The `control`
directive now names an endpoint a running lobo answers the whole verb
set on (`reload`, `quit`, `stop`, `reopen`, `status`, `upgrade`,
`ping`) and `lobo control <verb>` is its CLI door, so `lobo -s` can
keep nginx's four words (the parity `tools/lobo-shell`
probes against the oracle). A rejected reload, an unknown verb, an
`unauthorized` answer and `upgrade`'s named refusal are all exit 1,
so `lobo -s reload && deploy` cannot run on a reload that did not
happen, a gap the new differential found and closed.

`upgrade` exists before it works: it is the ONE verb
the endpoint reaches that no signal does. On unix UPGRADE's bit is
lobo's own poll probe (an outside `SIGUSR2` is indistinguishable from
it, the wsm01 residue); on windows `RELOAD`/`UPGRADE` have no analog
at all. Dispatching it so it can say "when it lands it lands HERE" is
what makes the endpoint the place the binary swap will go.

The listener, per host: loopback TCP everywhere, measured rather than
assumed. wolf has no unix-domain socket at the v0.2.3 pin. Every
spelling answers a bare `io` (`/tmp/x.sock`, `unix:/tmp/x.sock`,
`unix:///tmp/x.sock`) while `127.0.0.1:0` binds; the runtime's
`net.rs` is `TcpListener`/`TcpStream` and `spec/11-os.md` has no
clause. Filed as wolf-lang#227. That is why lobo cannot have the
filesystem-permissioned socket haproxy, systemd and nginx-plus use,
and why the second auth arm exists at all: loopback is not a uid
boundary.

Auth: loopback always, an optional shared secret beside it.
`control <addr> token <file>` arms a secret; the wire line becomes
`<secret> <verb>` and anything else is answered `unauthorized`,
dispatches nothing and changes nothing (the e2e witness proves the
generation did not move). Three decisions, each named rather than
implied: lobo reads the token file and never writes one, because std
has no file-permission surface at this pin (wolf-std#5), so a token
lobo generated would land at the umask's mode and could be
world-readable; a config naming a token file lobo cannot
read refuses at startup, because an endpoint whose auth silently
does nothing is the failure mode that matters; and `ping` is
exempt, because it is the liveness probe `-s` and the stale-pid
check use, and gating it would let a rotated token make a live master
look dead and have the next start replace a running server's pid file.

A verb and a signal are one code path, asserted as a diff. Both
triggers reach one dispatch and one emission site, so ws09's
vocabulary gains no event and no new key: `signal-received` grows a
trailing `source` (`signal`|`control`), appended, nothing renamed,
every earlier prefix pin still matching. `tools/lobo-signal` now
reloads one server twice, once by verb and once by `kill -HUP`,
extracts both five-line event blocks, normalizes the generation
numbers, seq stamps, content hash and age, and requires exactly one
differing line; then it normalizes `source` too and requires the
blocks to be byte-identical. 15/15 → 20/20. The verbs with no
signal twin emit nothing, which is what keeps `sig`'s value set
frozen at `reload|terminate|quit`.

The nginx differential grows an operation half
(`tools/lobo-control-differential`, a gauntlet step; 9/9). Four rows
CARRY: config re-read, listener survival (20 connects each after the
reload, zero refusals), an already-open connection never served the
NEW config, and a bad config refused with the old one still serving
AND a non-zero exit on both. Four deltas are NAMED and measured
rather than hidden: D1 transport (`kill(pid, SIGHUP)` with the
kernel authorizing vs a loopback endpoint with a token), D2 who
parses (nginx's CLIENT parses and exits 1 before the master ever
hears; lobo's MASTER parses and answers the verdict plus the
generation that kept serving), D3 narration (0 drain events in
nginx's error log against 6 in lobo's), and D4 idle keepalive at
reload (nginx's old worker closes them once it finishes shutting
down; lobo's draining generation holds them until they close or
`worker_shutdown_timeout` bites, so lobo is the more forgiving and an
nginx-written client keeps working while a lobo-written one may not
survive nginx). docs/CONTROL.md is the page.

ws14's windows sentence flips to a measured rule on every host.
`lobo -s reload` against a config with no `control` directive now
refuses, naming the directive: "a running lobo is reached ONLY over
its control endpoint at this pin (there is no arbitrary-pid signal
send — wolf-lang#126)", instead of dialling the http port. The second
half of the windows promise is therefore true everywhere, for the same
reason, and it is probed on linux and macOS. What stays CLAIMED is
the windows half itself (the console-handler mapping); lobo's CI is
still linux and a windows lane is still a ws16-class decision.

D40 resolved: the envelope follows the growth law. ws14 measured
`charge(N) = 16 × pow2ceil(N) − 16` and found a BAND in which the
runtime refused a body the meter had ADMITTED: 33,000 bytes under
`memory_budget 40k` charged 1,048,560 against a flat-16× cap of
655,360 and died at the join. That made the cap a SECOND METER with
arithmetic no config states. The envelope is now `16 × pow2ceil(
memory_budget)`, which makes it a backstop: for any body the
meter admits, `N ≤ budget` so `pow2ceil(N) ≤ pow2ceil(budget)` and
the charge is strictly under the cap; the stream path's one 64 KiB
chunk (1,048,560) sits under it because admitting a streamed body
needs `budget ≥ 65,536` and therefore a cap ≥ 2,097,152.
`tests/serve/budget_cap.lu` ASSERTS that over every budget from 1
byte past the stream threshold, and `tools/lobo-membudget` MEASURES
the closure: the same file, the same config, 200 in full at
`mem-rt-hw=1048560` under a cap of 1,048,576, a sixteen-unit margin,
with no `site=region` event anywhere in the run, while a
50,000-byte file beside it is still refused by the meter at
`site=file`. 15/15 → 17/17. The operator rule collapses to one
sentence ("set `memory_budget` to the bytes you are willing to
admit"); ws14's power-of-two footnote is retired. The `site=region`
mapping keeps its witness where a config can no longer reach it:
the join, driven directly.

The other two debts. wolf-lang#224 (the checked machine
killing a connected peer's handle after lobo's serve sequence): s135
had NOT merged at either gauntlet (the branch exists locally with
one commit, on `[type.byte]` spec work, and the issue is open) so
the either/or's ELSE arm was taken: nothing adopted, the
`checked-refuses:` rows left standing, noted here and in the
closeout. wolf-std#4 (a resolver surface in std.net): open, sc34
has not landed one, the ask stands unchanged.

Findings filed this sprint. wolf-lang#227 (no unix-domain socket
surface; every unix spelling answers a bare `io`) and wolf-std#5 (no
file-permission surface, so a program cannot create a secret that is
not world-readable). Both shaped the design rather than being worked
around, and both are named in docs/CONTROL.md where the design
touches them.

The linux CI earned its keep. The first push of the differential
was green on macOS and RED on the linux runner: the keepalive probe
read `pre=` empty on the lobo side only. The cause is lobo's own
write shape: it writes the head and the body with separate calls, so
Linux delivered them in two segments and one `net_read` yielded
headers with no body, while macOS coalesced them and hid it. The rig
driver now reads until the body carries a newline (bounded), and an
empty `pre` is reported as a HARNESS fault rather than a server
mismatch, so the next occurrence names itself.

Corpus 233 → 238 lane-runs (`control_verbs.lu` on three lanes,
`reloadhold.lu` on two); the gauntlet gains one step.

## ws14 — 2026-09-02 — the cap lands (and the signal arrives)

The budget is structural on BOTH halves: the meter admits, the
runtime's own region cap enforces, and the day the two disagree is
measured.

Pins advance first, gauntlet green at the trio before a line changed
(suite counts IDENTICAL: corpus 228/228, differential 3/3, proxy
8/8, signal 15/15, membudget 5/5, resolver 9/9): wolf → trunk
5f99b9f (the s134 merge; r06 had not tagged v0.2.3 at the pin
step, so the D57 dev stamp `0.2.2+dev.5f99b9f`, built with
`WOLF_COMMIT=5f99b9f`, no release stamp; ci.yml's tag probe finds
none and stays `+dev`), lupin → v0.1.23 (is34), wolf-std →
trunk 35f69ef (sc33; std's own machine pin is the same 0.1.23,
the first bump at which the two repos' interpreter pins agree).
Deltas classed: the interface snapshots did not move at all (zero
re-record, the cap branch's own `interface(...)` commit rides the
merge); #146 re-probed a SEVENTH time, the same `sc_muladd`
dominance ICE, `WOLF_MIDEND=0` stays; membudget's "round B
retained" 11,072 KB (macOS) vs 12,444 KB (linux CI) is host, not
pin, both under the #191 named gate. One rig delta at the bump,
classed host-not-pin and fixed in the witness: macOS's page
compressor (holding ~40 GB on the rig that day) shrank the server's
RSS between two `ps(1)` samples so round A read 6,976 / 7,792 KB
against a 10.6 MB steady reading (2 of 9 quiet runs; 0 of 15 at the
previous pin) and the differential blamed round B. A tripped
differential is now re-driven once, both pairs printed, and only a
second trip is red (a leak trips every drive; a compressed sample
does not).

The cap lands. wolf-lang#219 closed at s134: the LLVM emitter
takes a mangled symbol's address across partitions, so the proc
`src/budget` spawns from a non-entry module links under
`WOLF_MIDEND=0 --release`, the shape the release tier refused
at ws13. Branch `ws13-cap` is merged at the new pin, no
conflicts, the interface snapshots already true. Per lane, stated
(docs/BUDGET.md's table): native runs it (`budget_cap.lu`'s
four relations, `budget_cap_e2e.lu`'s real server, `cap_shape.lu`);
release runs it, and the gauntlet's tiers step links
`@budget.run_small.task0.entry` while every release-binary witness
runs that binary; checked (`wolf conform-run --checked`, the
s23 UB machine) refuses by name, `unsupported` at `mem` with
`x-unsupported-construct: "structured concurrency in checked
execution (C1 deferred)"`, and `tools/lobo-corpus` gains a
`//! checked-refuses: <construct>` directive that ASSERTS that
record as a lane-run (a refusal by the wrong name, a run, or a
crash is red; declaring both `checked` and `checked-refuses` is a
header error), never a blanket skip; every witness whose refusal
fires before the proc keeps its checked lane, and the one budgeted
200 that lived in `budget_refusals.lu` moved to `budget_cap.lu`;
lupin runs the shape (`cap_shape.lu`) and cannot run the serve
suite (no fs, the suite's posture since ws01).

The breach, end to end through a real socket. ws13 could only
drive the join directly, on a theorem that the cap cannot fire on a
meter-admitted request ("the small path charges ≈ 8N + 352", one
measurement, extrapolated). The end-to-end witness this sprint was
asked for falsified it: the ledger's growth law is `charge(N) =
16 × pow2ceil(N) − 16` (1,024 → 16,368; 1,025 → 32,752; 4,097 →
131,056; 40,000 → 1,048,560, because the buffer doubles and the
ledger keeps every abandoned buffer), so #203's 16× holds exactly AT
a power of two and reaches 32× just past one, and a budgeted small
body is refused by the runtime whenever
`memory_budget < pow2ceil(body)` though the meter admitted it.
`tools/lobo-membudget` now runs a
second server under `memory_budget 40k` on the release binary:
rounds A'/B' RE-BASELINED through the capped proc (A' 10,800 KB, B'
11,696 KB, difference 896 KB, 29 KB/req, the same two gates as
A/B, which read 448 KB and 27 KB/req uncapped in the same run), then
a 33,000-byte
file → `503 Service Temporarily Unavailable`, `Connection: close`,
the event `budget-exceeded gen=1 site=region budget=40960
would=40961 cap=655360`, the 32,768-byte file beside it (a power of
two) 200 in full through the proc, fifty keepalive requests after
the breach (the proc died, the server lived), `budget-503s=1` and
`mem-rt-hw=524272` in `lobo status`. 15/15. The band is written into
BUDGET.md with the operator rule (round the budget up to the power
of two above the largest small file, or 64k+; the stream path is
outside the band by construction), the directive table, and ledger
row D40: the envelope is LEFT at #203's 16× rather than
widened to the growth law, because `16 × pow2ceil(budget)`
makes the region site unreachable from any config again; what the
cap is FOR is the campaign closeout's decision, and every refusal in
the band is named meanwhile. BUDGET.md's "which half is
structural" flips to both; the ws10 deferral row (D30's cap
half) closes dated, so does ws13's #219 row.

The signal arrives (windows). s60b landed `[os.signal.platform]`'s
windows row in the pin: CTRL_C/CTRL_CLOSE → terminate, CTRL_BREAK →
quit, RELOAD/UPGRADE with no windows analog. lobo's promise is one
sentence in docs/DRAIN.md: on windows, `lobo -s reload` reaches a
running lobo over its `control` endpoint or not at all: there is
no signal that reloads it, and a config without a `control`
directive cannot be reloaded without a restart; `upgrade` (unclaimed
everywhere at this pin) will be a control-channel verb and the only
trigger for it there. The seam falls out small: `-s` always sent
over the channel (no getpid surface, the wsm01 residue), so nothing
in the dispatch moves; the startup notice now names the MEANINGS
and both platform maps in one line (the listen SUCCEEDS on windows,
so its answer cannot tell the operator what will arrive, and the
language has no platform query). Measured vs claimed, stated:
lobo's CI is linux-only, the windows-native tier refuses `--release`
by name (s60c's), so every windows statement is CLAIMED from the
clause and wolf-lang's windows floor, and the control-channel path
is measured on linux+macOS only.

Findings filed. wolf-lang#224: on the checked lane (the UB
machine) a client socket's handle dies when the peer it dialled is
closed after lobo's serve sequence ran on that peer (`net_deadline`
→ `io`; native and lupin keep it; present at v0.2.2 too);
`region_measured.lu` had been swallowing exactly this since ws12,
`budget_cap.lu` orders its drives so the named refusal is reached
first and says why (D41).

Corpus 228 → 233 lane-runs (`budget_cap.lu` and `budget_cap_e2e.lu`
join (three lane-runs plus `budget_cap.lu`'s `checked-refuses`
assertion) and `cap_shape.lu` gains its own); membudget 5 → 15
checks.

## ws13 — 2026-09-02 — the name resolves in time (wsc05 opens)

The finally-list's last STRONG item ships: `proxy_pass http://name`
resolves without stalling the loop, and the pin names a release.

Pins advance first, gauntlet green at the trio before a line changed
(suite counts IDENTICAL: corpus 213/213, differential 3/3, proxy
8/8, membudget 5/5): wolf → the v0.2.2 TAG (8cda3aa), the bare
stamp at last, because s132's cap and D68's fault merged BEFORE the
tag this time; lupin → v0.1.22 (is33: the contained trap is
`fault(alloc-contract)` at the join; the two tags name each other),
wolf-std held at a62a5d4 (its trunk had not moved). #146 re-probed a
SIXTH time at the tag: the same ICE at the same site, `WOLF_MIDEND=0`
stays. The interface re-record moves every header with zero item
motion. GitHub CI's first real run on this branch refused the tag
pin as identity drift (`+dev.8cda3aa` vs the bare `0.2.2` the pin
names). The workflow now grants xtask's own `WOLF_RELEASE` stamp
when the pinned rev is a tag, and the branch is green on GitHub.

Async upstream DNS. report 11 §2 item 9, the one STRONG item
wsc03 left unshipped, measured first: with a loopback resolver
holding its answer 800 ms, a static request on a SECOND connection
waited 805 ms behind a proxied request's name, because the dial
resolved the name synchronously on the one poll loop's thread, with
no deadline. There was no blocking call to wrap: std.net says in its
own header that `dns`/`resolve` is not a function it has, and the
runtime's `net_connect` hands a name to getaddrinfo (its
`connect_timeout` resolves first and reaches no lane). Both FILED
(wolf-std#4, wolf-lang#217), neither absorbed: lobo now
carries a DNS-over-TCP stub client (`resolver`, a leaf module: the
wire half pure over `List[int]`, the TTL cache with nginx's `valid=`
override and round-robin, a pending-query table the loop TICKS under
a 1 ms deadline like any other socket) and a PARK: serve asks which
name a request needs before it reads a byte past the head, the loop
skips that connection until the query settles, then steps it from
the top with the cache warm. After: static-ms=1, proxied 836,
cached 0 with exactly one query recorded (`tools/lobo-resolver`, a
gauntlet step; `tests/rig/dnssrv` is the resolver, in wolf). nginx's
`resolver … valid=` and `resolver_timeout` carry as directives, `-t`
answers nginx's own `invalid parameter` wording, the two parameters
lobo cannot honour refuse by name (`ipv4=off`, `status_zone=`);
LOBO-L012 names a hostname with no resolver in effect (the stall),
LOBO-L013 names the delta in lobo's favour: nginx resolves a static
`proxy_pass` name once at load and ignores `resolver` for it (trac
#1064); lobo re-resolves under the TTL. Every other delta (TCP-only,
A-only, first address, failures held 1 s, a 0-TTL held 1 s) is a
row in docs/RESOLVER.md's table; both proxy-differential confs carry
the directive so the oracle and lobo prove they parse the same line
(8/8). Two vocabulary events appended (`upstream-resolved`,
`upstream-resolve-failed`, seq-stamped), one metric family
(`lobo_upstream_resolutions_total{result}`, 22 families), the
`$upstream_addr` log variable names the resolved address.

The cap adoption, built, witnessed, and gated by codegen. s132's
`region r(cap: n)` and D68's proc-boundary fault are in the pin, and
ws13 consumed them: a budgeted request's regioned body work runs
inside a `spawn proc` under `cap: 16 × memory_budget` (the #203
ledger envelope, and the directive documents the arithmetic), and
the join maps the reason to 200 / close / 503 `site=region` /
500; ws12's measured `region_bytes` comes back out of the proc
through a loopback self-pipe, because a proc's `normal(value)` is
unreadable at the join and a channel cannot be a proc argument on
wolfc. Green on the native tier, and the RELEASE tier refuses to
emit it: any proc spawned from a non-entry module lands its entry
shim outside its object (`func.addr of @budget.run_small.task0.entry
outside this object's subset`, #136's shape for a PROC), a 30-line
reproducer filed as wolf-lang#219 with a second finding
(`conform-run --checked` answers `unsupported@mem` with an empty
diagnostic for every proc spawn, wolf-lang's own conformance files
included, while `run --checked` runs them). A proc the release tier
cannot emit is not a proc lobo can ship, so the adoption lives whole
on branch `ws13-cap` (the flip is a merge the day #219 closes),
and trunk carries `tests/serve/cap_shape.lu` (the program a
budgeted request runs, in one module, on native and lupin) plus
BUDGET.md's theorem that at this pin the cap cannot fire on any
request the meter admits (the head site's charge puts every cap
above every ledger reading lobo's shapes produce), which is the
property the contract asked for stated as an inequality. The
membudget suite holds its marks unchanged (the trunk
binary has no proc in it).

#197's Tier-2 shapes, stated. Four, re-read against s132 and
posted upstream: a capture is written on the JOIN side (a killed
proc runs no writer); the reason class is a stable key (a closed
set); the record boundary is the proc argument record (s87 copies
it at spawn: record at the proc boundary, replay the proc); and
what a proc can say back bounds what a capture can carry (a token
made inside a proc cannot leave it). docs/REPLAY.md has the text.

Corpus 213 → 228 (+13 resolver lane-runs, +2 cap shape). wsc05 opens
with this sprint; its campaign file sits beside the contract.

## ws12 — 2026-09-01 — the numbers speak

lobo stops guessing at its own memory and starts reporting it, and
the counters an operator pages on land in core with no recompile and
no module.

Pins advance first, gauntlet green at the trio before a line changed
(suite counts IDENTICAL to the old pin, deltas classed): wolf
e6cf24e (trunk, D57 dev-stamped `0.2.1+dev.e6cf24e`, because the
number this sprint came for landed in s131 AFTER the v0.2.1 tag),
lupin v0.1.20 (wsm04's named fallback retires; lobo, wolf-std and
the driver's own pairing line name the same interpreter for the first
time) and wolf-std a62a5d4 for sc31. #146 re-probed at the new
pin, FIFTH measurement, ICE unchanged, `WOLF_MIDEND=0` stays; #192's
misleading W1001 is GONE (r04 fixed it). The interface re-record moves
every header and export-hash with ZERO item motion in eleven modules.

The measured half. `region_bytes(r)` / `live_region_bytes()`
([mem.region.account.1/.2]) reach lobo: `serve` reads the ledger
inside the per-response and per-chunk regions the ws10 audit put
there, and the entry high-waters it per generation BESIDE ws10's
metered figure: two numbers answering two questions, published
together and never subtracted from each other (`mem-rt-hw` and
`live-region-bytes:` in status text, `mem_rt_high_water` and
`live_region_bytes` in the JSON; additive, schema stays 1). ws10 could
only argue the streaming path was O(1) in file size from RSS noise;
the runtime now states it as an EQUALITY: 128 KiB and 256 KiB stream
to the same high water, pinned in `tests/serve/region_measured.lu`.
The same measurement found what BUDGET.md now teaches: a 64 KiB chunk
charges its region 1,048,560 bytes, 16× the payload, 8× because a
byte buffer is a `List[int]` and 2× because the ledger is cumulative
by contract. Not a lobo bug, not absorbed: wolf-lang#203 filed
with the numbers, and #187 commented because the gap bears on the cap
half's units. The cap arm itself: s132 had not merged at Act-2 start,
so the contract's named-gate defer was taken: the meter ships
query-only, and #187 owns the adoption.

`/metrics`, in core. A new `metrics` module holds ONE registry
(name, type, label shape and help for every family) and `sample`
asserts the labels it was handed are exactly the ones declared, so a
per-URI or per-client series is not discouraged or linted but
UNWRITEABLE. `tools/lobo-metrics` (a gauntlet step) measures the
consequence on a live server: four more distinct URIs add exactly zero
series. Twenty-one families cover every landed sibling: connections,
requests by status class, a fixed 5ms..10s duration histogram, the
proxy leg, TLS handshake failures by reason, generation info as the
Prometheus info-metric idiom, ws09's dropped lines, ws11's event
count, and ws10+ws12's two memory high waters. The counters live as
plain ints in the poll loop's own frame, which is the MEASURED
hot-path answer for a spawn-free server: one mutator needs neither
shards nor atomics, an increment is one checked add, and the module
header names the day that stops being true. The endpoint is two
phase (`serve` recognises the path, `main` renders it) because
rendering per pass would leak megabytes an hour into #191's root arena
to answer a scrape a minute. `/status.json` serves ws08's object on
the same listener, proving its design-once note. The scrape is an
ORDINARY request: it counts itself one behind, it logs, and under a
tiny `memory_budget` it 503s (site `admin`, the fifth), which is
correct, and a rig case. `metrics on|off` is lobo-native, `-t`
validated in nginx's own flag wording, and linted twice: L010 for the
one-way door, L011 when the endpoint sits on a routable listen,
because at v0 the bind address IS the access posture, and the docs say
so in four lines. `docs/metrics.md` is generated from the registry
(`tools/lobo-metricsdoc`, a gauntlet step), so a Grafana panel and a
live scrape cannot disagree; the exposition is checked clause by
clause against the vendored Prometheus text format spec.

The row gets a name. wolf-std#3's `named`/`row_name` are adopted
at both TLS-client error sites: forty arms re-listing a twenty-one-row
vocabulary lobo does not own become two `named(...) else |Row(name)|`
handlers plus a per-site hint table keyed by the row's stable NAME.
Messages byte-identical, `timeout` still 504 (the live
`https_gateway` case runs that arm), and a future std row now reads as
a bare name instead of breaking the build.

Corpus 203 → 213. wsc03 closes here; the closeout declares W5.

## ws11 — 2026-09-01 — replay the race

A scheduling bug becomes an artifact. The rig gains the seeded
half of lupin's determinism surface (pin HELD at 0.1.19; v0.1.20
is match-arms, no explore change, probed day one): the corpus
runner takes `//! explore: N` (the file's whole schedule space,
every gauntlet run, green only on agreement WITH a closed frontier;
an open one is red, tense discipline) and `LOBO_SEED` (every
lupin-lane run under a bug report's seed, failures printing the
replay command). The witness pair keeps the ws08 drain-finish
hazard alive as a specimen: `drain_finish_race.lu` decides
retirement by racing the timeout message against the closes in one
select, FIFO-clean (a laptop never sees it), with 3 distinct outcomes
across 16 schedules under explore, while `drain_finish_fixed.lu`
is the real loop's shape (retirement is a STATE check) and closes a
24-schedule frontier on one outcome, held by `explore: 64` forever.
`tools/lobo-replay` (a gauntlet step) walks the whole story every
run: the finding, the `.loborace` artifact (schema 1: seed +
decision stream + pinned bytes + lupin identity), three
byte-identical replays FROM the artifact (2× seed, 1× stream), the
fix's closed frontier. On the server side lobo is
spawn-free, so it never prints a seed. Instead every vocabulary
event now carries `seq=` (stamped at the emission seam; builders
and prefix pins untouched) and status carries `events:` (additive,
schema stays 1), making an attached log an ordered, GAP-VISIBLE
event stream with a completeness anchor. docs/REPLAY.md states the
boundary (values, real time, the membrane; no production
flight recorder, Tier 2 deferred with the asks filed). Corpus 200 → 203
(the specimen pair's lupin lanes plus the fixed twin's explore run).

## wsm04 — 2026-08-31 — the doors open inward

Lobo consumes its own library's TLS client. Pins advance to wolf
b80d239 (D57 dev-stamped; no v0.2.1 tag existed at acquisition), the
lupin v0.1.19 tag, and wolf-std 26f0588 (the bump that carries
sc29's `std.x.tls.client`) with the full gauntlet green at the trio
before a line changed (corpus 195/195; #146 re-probed byte-identical,
the midend stays off). Then the last two named refusals in the config
surface retire: `proxy_pass https://` (D21's upstream leg) dials
through the std client, with trust anchors via `proxy_ssl_trusted_
certificate` (REQUIRED: lobo has no unverified mode, nginx's
verify-off default is a named delta), SNI always, chain+hostname+
CertificateVerify before a request byte leaves, TLS failures mapped
to 502 (504 for a mid-handshake deadline) with the row named in the
error log; and the differential grows an https case where nginx and
lobo both proxy a VERIFIED fixture-cert upstream, client legs
byte-equal (8/8). https `cert_ca` (D25) follows: the ACME client
dials an https directory verified against `cert_ca_root`, the
harness CA serves its whole RFC 8555 directory through lobo's own
TLS server half behind the conn seam (`--tls`), and cold issuance +
renewal run over TLS end to end. The loopback law is UNCHANGED and
forever: only the https *transport* gate retired; a non-loopback CA
is still a named -t refusal. Measured: the std client's
handshake costs ~3.6s on this rig (native tier, WOLF_MIDEND=0,
#146's residue), stated where it moves deadlines, asserted nowhere
tighter. Corpus 195 → 200.

## ws10 — 2026-08-31 — the budget is real

Per-vhost memory budgets, enforced: `memory_budget <size>;` refuses a
request that would blow its budget with a 503-with-a-name (nginx's
answer is the OOM killer), deterministically per exceed-site
(head/body/body-chunked/file, fence-first at every site), observable
as the `budget-exceeded` error event and the status stanza's per-gen
`mem-hw`/`budget-503s` aggregates. The perimeter fence lands
nginx-named: `client_max_body_size` and `large_client_header_buffers`
implemented with the oracle's own invalid-value spellings. The
structure audit found lobo held ZERO region
blocks (every allocation process-lifetime): response bodies now die
in per-response regions (~290 → ~25 KB/request, the
`lobo-membudget` gauntlet witness pins bodies-O(1) differentially),
and the str half plus the region query/cap are filed as the sprint's
three upstream asks (wolf-lang#187/#191/#192; #187 owns the gated
region-cap half). docs/BUDGET.md is the model. Corpus 184 → 195.

## ws09 — 2026-08-30 — logs that parse

`log_format`, `access_log` and `error_log` carry: the escape rules
probed byte-for-byte against the oracle, and the access-log
differential (identical directives, identical adversarial requests on
both servers) reads 4/4 identical modulo timestamps. `format=json` is
the typed door: RFC 8259-validated lines, numbers as numbers, the
ws08 drain vocabulary decoded. Sinks are bounded and drop-and-report
in the spawn-free loop; logrotate's reopen cycle works end to end. Three
new lints (L005 inert level, L006 native doors, L007 what a text
format loses). Corpus 166 → 184.

## ws06 — 2026-08-30 — certificates without the dance

Built-in ACME: RFC 8555 HTTP-01 end to end, hot-swap issuance with no
reload, a renewal daemon, and `lobo cert status`. The certbot dance
still works: the coexistence test serves a certbot block live beside
a `cert auto` block. The fixture CA is a pebble-class RFC 8555 server
written in wolf, verifying account JWS on every POST with real
dial-backs; it caught two client bugs a vendored oracle would have
accepted. Deltas recorded: Ed25519 not ES256 (the frozen jose seam),
loopback-plain `cert_ca` only until a std TLS client exists (D25),
key files at umask not 0600 (D26). Corpus 158 → 166.

## wsm03 — 2026-08-29 — the name lands

Lobo (D64): the code stops spelling wws over 86 files, in the
binary's own voice (banner, diagnostics, `Server: lobo/0.1.0`,
LOBO-L lint codes), with zero seam motion. Pins advance to wolf
addcd7f + the lupin 0.1.16 tag, and the first macOS three-lane
gauntlet runs 158/158, with two
rig-side deltas fixed on the way (the TLS oracle refuses LibreSSL by
name; the signal gate widens so a real SIGHUP drives the drain
off-linux). wolf-lang#146 re-probed unhealed; the midend stays off.

## wsm02 — 2026-08-27 — the pin pays back

Pins to wolf 53f6191 + lupin is24, zero source breakage. TLS session
keys now come from `os_random`, the OS CSPRNG, which traps instead of
degrading (#143 retires), with the interim HKDF derivation
deleted and an entropy probe at TLS bind. The three W0305 sentinel
dodges revert to the natural arm re-raise (is24's #44 fix). The
midend flip-back was attempted and refused: a #142-class survivor
found, filed as wolf-lang#146, `WOLF_MIDEND=0` stays.

## ws07 — 2026-08-27 — the dry-run that means something

`-t --request` predicts the routing decision with a why-it-lost
trace: the real matcher grows a trace parameter (never a second
implementation), effective directives filter to the winning chain
with `-T` provenance, TLS and stat notes are opt-in, and unknowable
headers say UNRESOLVED instead of guessing. Cross-checked
against the live server: the predicted static path's bytes are the
live body, and the backend records the predicted proxy
target. Text stanzas or schema-1 JSON.

## ws05 — 2026-08-27 — TLS integrates

`listen … ssl` serves HTTPS over wolf's own TLS 1.3 stack (the
wolf-std handshake, record layer and certificate rungs), OpenSSL
interop 8/8, SNI selection, and the certbot renewal-reload cycle
carries.

## wsm01 — 2026-08-27 — the pin catches up

Pins to wolf 64a38f3 + lupin b682bcf: a real SIGHUP drives the drain
(the signal surface landed upstream), and binary files serve over
byte paths.

## ws08 — 2026-08-27 — the drain you can watch

Reload's connection draining becomes observable: per-generation live
counters on the status surface, the drain witnessed in tests, and the
serve loop reshaped into the multiplexer poll loop the later sprints
build on.

## ws04 — 2026-08-27 — the shell

CLI and exit-code parity with nginx (`-t`, `-T`, `-s`, the signal
set), and control-channel reload with connection draining. The
serving campaign (wsc01) closes.

## ws03 — 2026-08-27 — it proxies

Upstream pools, `proxy_pass`, hop-by-hop header discipline; the
two-sided differential runs 7/7 byte-equal to nginx.

## ws02 — 2026-08-26 — it serves

HTTP/1.1 static serving over an RFC 9112 MUST-checklist parser, the
historical-CVE corpus v0 held to refuse-or-trap-clean, byte-equal to
nginx on the differential. W1 declared.

## ws01 — 2026-08-26 — the config carries

The nginx config surface: 76 oracle probes, 87 directive table rows,
three lints firing at load, and `-T` that knows which file set every
directive. The scaffolding campaign (wsc00) closes.

## ws00 — 2026-08-26 — the repo and the harness

Pins (wolf 87405ac / lupin e2dbd40, the `.wolf-bin` ritual), the
loopback HTTP rig written in wolf, the pinned-nginx differential with
its first byte-equal case, the gauntlet, and CI against the pins,
committed ahead of any remote.
