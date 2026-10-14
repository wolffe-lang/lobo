# ws65 — lobo 0.1.4

Wave 53, lane ws65 (Opus). Written 2026-10-14 on lobo trunk `f9fea55`
(ws64's head), after the inputs below were re-derived and before any
change to the tree and before any released binary was run at a limit.
The planning contract is `sprints/wws/34-lobo-014/ws65-lobo-014.md`
in `wolffe-lang/wolf` (planning commit `f8ee4fc`); its shape and
rules are ws61's (`sprints/wws/30-lobo-013/ws61-lobo-013.md`), and
the rules of `sprints/wave-53.md` down to `wave-45.md`.

One deliverable: lobo 0.1.4 prepared to the point where the
orchestrator audits, merges and tags. The lane does not tag, merge,
publish, push a package or file an issue.

## 1. Forbidden, absolutely

- No tag, no merge, no release published, no AUR push, no tap merge.
  No issue filed or closed. No attribution or co-author trailer.
- Two disclosures, each written for a person deciding whether to
  upgrade today, with the affected versions measured by running the
  released archives: (a) a process at its descriptor limit can be
  ended by a client; (b) a master with `worker_processes` above 1 and
  no `control` directive spins a cpu and ignores HUP and TERM. For (a)
  nothing is written that goes past what pull request #86, the README
  and the regression tests already say in public: no step-by-step.
- One behaviour change an operator must act on leads the upgrade
  notes: `worker_connections` is applied.
- No source change beyond the version sites, the documents and what
  the release needs. A defect found is reported, not fixed. The pin
  does not move: wolf 0.2.29 (`6ffe7c6`), lupin 0.1.52 (`025428b`),
  wolf-std `9e5bd6b`.
- Nothing here deploys or serves anything public. lobo serves no site
  of ours; lupp.us is nginx on almanta (`sprints/HOSTING.md`). Never
  almanta, a Cloudflare tunnel or its configuration, DNS, or host
  ports 8080 and 8088; never a listing of `cloudflared`'s arguments.
  Every server this lane starts binds 127.0.0.1 on a port in
  18850–18899 or one the kernel chose, and is stopped through its
  control endpoint or by its recorded pid. The one exception is named
  where it happens: the release archive's stock configuration listens
  on 127.0.0.1:8080, so the smoke rewrites the port before it starts.
- A descriptor limit is lowered only with `ulimit -n` in the subshell
  that starts one server, or `prlimit` on a pid the test started.
  Never a host-wide or user-wide limit, never a sysctl. Old released
  binaries are run under the same rules.
- The toolchain is the pin's, from the release archives by digest,
  each digest read twice. Builds and tests run on kasumi; on nomad-1
  only what a macOS smoke of the packed archive needs, and the report
  says what that was. No package is installed on a host; the AUR
  proof runs in a throwaway container.
- kasumi: remote commands in `bash -c`, long jobs under `setsid` with
  a pid file, kill by recorded pid only (never a group, a name or a
  pattern). Scratch under `~/lanes/ws65/` only. No `rm` outside
  `~/lanes/ws65/` and the lane's own clones; no `git add -A`; nothing
  under `~/.claude`; the branch asserted before every commit.
- Strict evidence (wolf-lang#571): stdout and stderr together, every
  SKIP line counted; a `wolf build` that exits 2 is a compile error;
  the limit tests also under `taskset -c 0-3`. A green CI run of
  about ten seconds means the token lapsed: the gauntlet's own lines
  are read. Checksums carry a trailing `…`.
- At most two CI runs of this lane at once; never cancel another
  lane's. If the harness refuses an action, stop and report.

## 2. Inputs, verified (2026-10-14, about 02:00Z)

- lobo `origin/trunk` is `f9fea55` (PR #86 merged 01:56Z). Its trunk
  CI run 38498422978 was still in progress when this was written; the
  same tree's PR run 38493522448 is green on both hosts. The stamp
  reads `lobo/0.1.3+dev (built with wolf 0.2.29, pin 6ffe7c6)`.
- `v0.1.3` is on commit `d6bd15b`, release 409859402, four assets:
  linux 3,635,915 bytes (`c8a33fa0…`), macOS 3,452,422 bytes
  (`7fc88626…`). Four releases (`v0.1.0` `45820b7`, `v0.1.1`
  `7c87e0a`, `v0.1.2` `8533cb5`, `v0.1.3`), no drafts.
- 83 commits from `v0.1.3` to trunk, by pull request: #79 (the
  channel back to `+dev`), #80 ws62, #83 ws63, #86 ws64. The
  CHANGELOG has a lane entry for each of ws62, ws63 and ws64. The
  release entry is still derived from the commits and checked against
  the four pull requests.
- Open lobo issues: #68, #72, #81, #82, #85, #87. #78 is open too: it
  is the public record of 0.1.3's fix. No open pull request.
- Toolchain staged on kasumi from the release archives, each digest
  read twice (`kasumi:~/lanes/ws65/ev/digest-check.txt`): wolf 0.2.29
  linux `ae466e85…`, lupin 0.1.52 linux `f5194b74…`. Members by name:
  `wolf` `07f12158…`, `libwolf_rt.a` `fa0a0ae5…`, `lupin`
  `74043b0a…`, the bytes ws63 and ws64 used. std is wolf-std
  `9e5bd6b`. The nginx oracle is 1.30.4, `65595ac2…`.
- The four released linux archives are staged the same way and each
  binary runs on kasumi (`ev/toolchain.txt`): 0.1.0 (built with wolf
  0.2.6), 0.1.1 (0.2.16), 0.1.2 (0.2.23), 0.1.3 (0.2.27, binary
  `66a346dd…`).
- The doors: `homebrew-wolf` trunk `73710ff`, `Formula/lobo.rb` and
  `aur/lobo-bin` at 0.1.3, `tools/lobo-fill-digests` present (ws61's).
  AUR `lobo-bin` answers 0.1.3 from its RPC.
- ws64's memory figures (4,820 kB at start, 5,108 kB after 400,000
  keepalive requests) were taken on a kasumi build one fix behind the
  head. They are re-taken here on the release workflow's archive.
- **Read, for disclosure (b):** the shape ws63 fixed (`5fc7cdb`: the
  master's wait set and its wait both sat inside `if have_ctrl`) is in
  `src/main.lu` at `v0.1.1`, `v0.1.2` and `v0.1.3`. It came with the
  parked signal forwarder (`f58e38c`, ws29, 2026-09-10). `v0.1.0`
  polls for a signal in the master's own loop and has no forwarder.
  This is a reading; §3 says what the binaries should do if it is
  right.
- **Drift:** the contract says a site that served more than about 510
  clients a process "on 0.1.3" must set `worker_connections`. The
  stock `conf/lobo.conf` the archive ships has said
  `worker_connections 1024` since 0.1.0, so a site that started from
  the stock file gets 1,022 a process, not 510, and is affected only
  past that.
- **Drift:** lobo#85 names 0.1.3 only. The reading above says 0.1.1
  and 0.1.2 too.

## 3. Prediction

Each line carries what would show it wrong.

- **P1, the CHANGELOG entry.** `## 0.1.4 — 2026-10-14 — …` with these
  sections in this order: Security; Upgrading from 0.1.3; Install;
  `lobo -v`; What changed since 0.1.3; Against nginx; The hosts, and
  what is still known wrong or limited. Security holds two
  paragraphs, each saying what happens, who is exposed and what to
  do. Upgrading opens with `worker_connections`, then what `-t`
  refuses, then the 500. User-visible: ws62 (every server served, a
  replaced worker at its generation, a flat master, the pid in the
  pid file), ws63 (no ceiling on parked downloads, `-s` by signal,
  `SIGUSR1`, the master that hears), ws64 (`worker_connections`, the
  descriptor limit) and the pin 0.2.27 to 0.2.29. Not user-visible:
  #79.
- **P2, archive sizes.** `src/` is 30,918 lines against 28,725 at
  0.1.3 and the CHANGELOG the archive carries grows. linux 3.72 to
  3.98 MB (0.1.3: 3,635,915 bytes); macOS 3.53 to 3.78 MB
  (3,452,422). Each packed twice, identical.
- **P3, the documents that move.** `CHANGELOG.md`; `README.md` (the
  `-v` line, the version note with both disclosures, the known-issues
  line, a parity row if one is taken); `docs/GETTING-STARTED.md`
  (lines 41, 46, 67); `docs/PARITY.md` (the release row);
  `shell.lu`'s doc example. The stamp commit moves `src/wolf.pkg`,
  two `shell.lu` constants, the wire token in `serve.lu` and four
  lines of `tests/shell/version_text.lu`; no `.wolfi` hash moves.
  Not the reel, not `docs/CAPABILITIES.md`, and none of the "through
  0.1.3" sentences (they stay true).
- **P4, the release workflow.** No change is needed for 0.2.29: it
  builds the pin from source as `ci.yml` does and `tools/lobo-dist`
  already runs in the gauntlet on both CI hosts at 0.2.29. The
  rehearsal is green on the first dispatch; the jobs take 3 to 8
  minutes each and the wall time is the runner queue's, 20 to 120
  minutes.
- **P5, the smoke against 0.1.3** (kasumi, the two release-tier linux
  binaries from the published archive and the rehearsal's):
  - resident size of one process after 400,000 keepalive requests:
    0.1.3 between 4.2 and 4.6 MB; 0.1.4 between 4.6 and 5.4 MB (it
    holds the readiness set and two descriptors more from the start);
  - requests a second at 4 workers, 32 clients, 0.1.4 ÷ 0.1.3: 0.95x
    to 1.06x on both shapes (ws62 to ws64 each read within a percent
    of the tree before it). On a runner VM nginx ÷ 0.1.4 stays inside
    1.10: close 1.00x to 1.07x, keepalive 0.90x to 0.96x.
- **P6, disclosure (a) on the released binaries** (linux, one process
  and then `worker_processes 2`, the descriptor limit lowered for
  that server only, downloads held by clients that do not read):
  - 0.1.3 ends: the process aborts (status 134) with wolf's
    `epoll_create1 failed`; with two workers the master logs the
    worker's exit and starts another, and the connections that worker
    held are gone. 0.1.4's rehearsal binary under the same load keeps
    its pid, logs `[crit]` lines and serves again afterwards.
  - 0.1.2 (built with wolf 0.2.23, the first release to write a large
    body beside the loop) ends the same way.
  - 0.1.1 and 0.1.0 write a body inside the serving loop and never
    park; I expect them not to end but to stop answering while a slow
    download is held. This is the line I am least sure of.
  - At the host's usual limit of 1,024, slow downloads alone do not
    end 0.1.3: its first wait on a slow client comes long before the
    limit, and the readiness set then exists. A process is exposed
    when it reaches its limit having never waited on a slow client;
    whether a client can arrange that at 1,024 is measured, and I
    expect it can.
- **P7, disclosure (b) on the released binaries** (linux,
  `worker_processes 2`, no `control` directive): 0.1.3, 0.1.2 and
  0.1.1 each use about a whole cpu in the master while idle (450 to
  520 ticks in 5 s), change nothing on `kill -HUP` and are still
  running 2 s after `kill -TERM`. 0.1.0 uses under 50 ticks in 5 s
  and obeys both. 0.1.4's rehearsal binary: under 5 ticks, both
  obeyed. With a `control` directive (the stock configuration has
  one) none of the four spins or is deaf.
- **P8, the upgrade.** Every configuration 0.1.3 shipped or tested
  that loads on 0.1.3 loads on 0.1.4, except any whose
  `worker_connections` value 0.1.4 refuses (`0`, a non-number, a
  value with a suffix, a duplicate, or fewer than its listening
  sockets need): I expect none among the shipped examples and zero
  to three in 0.1.3's test corpus. The `-t` text differs where 0.1.4
  adds a warning (a later `server` setting a first-server-only
  directive, a regular-expression `server_name`, the descriptor
  warning). `-s reload` keeps the running binary; the documented path
  is stop and start, with zero or one failed request and a gap under
  100 ms when the start follows the stop at once.
- **P9, the gates on the packed binaries.** The dist smoke, the limit
  tests (`control_exhausted_e2e.lu`, `worker_connections_e2e.lu`
  through `LOBO_BIN`, on 16 cpus and under `taskset -c 0-3`) and
  `tools/lobo-membudget` (24/24) are green on the rehearsal's linux
  binary; the smoke and membudget on its macOS binary.
