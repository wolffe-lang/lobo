# ws61 — lobo 0.1.3: inputs and prediction

Written 2026-10-11, before any change to the tree. The lane prepares
the 0.1.3 release up to the point where the orchestrator audits,
merges and tags. It does not tag, merge, publish or push a package.

## Forbidden

- No tag, merge, published release, AUR push or tap merge by the lane.
  No issue filed or closed.
- The security paragraph says three things and no more: 0.1.2 and
  earlier can lose a worker to one unauthenticated request whose bytes
  split a UTF-8 scalar; with `worker_processes 1` the server stops;
  0.1.3 answers 400. No request bytes that reproduce it appear in the
  CHANGELOG, the notes, the PR or a commit message. The regression
  tests already in the tree are the only place they live.
- No source change beyond the version sites, the documents and what
  the release needs. A defect found is reported, not fixed here. The
  toolchain pin does not move.
- The toolchain comes from the release archives by digest. Builds run
  on kasumi; nomad-1 runs only what the macOS smoke needs.

## Inputs, verified (2026-10-11, about 16:30Z)

- lobo `origin/trunk` is `b256d2e` (PR #75 merged). Trunk CI run
  38128926329 is green there. The stamp reads `lobo/0.1.2+dev (built
  with wolf 0.2.27, pin 0ddda6b)`.
- `v0.1.2` is tag `fb86468` on commit `8533cb5`, release 403185701,
  four assets: linux 3,328,968 bytes (`43882448…`), macOS 3,240,415
  bytes (`0bd30835…`). Three releases, no drafts.
- 143 commits from `v0.1.2` to trunk, by PR: #58 (the channel back to
  `+dev`), #59 ws51, #60 ws52, #61 ws53, #63 ws54, #64 ws55, #70 ws56,
  #71 ws57, #73 ws58, #74 ws59, #75 ws60.
- The CHANGELOG has a lane entry for ws51 to ws58. **It has none for
  ws59 or ws60.** The release entry is therefore derived from the
  commits, and each of the eleven PRs is checked against it.
- Open lobo issues: #68 (user-space cost per request) and #72
  (`carry_e2e` red on a loaded host). No others. No open PR.
- Toolchain staged on kasumi from the release archives, each digest
  read twice: wolf 0.2.27 linux `5e17eebe…` (release 409367590), lupin
  0.1.50 linux `e2867a35…` (release 409303515). Members by name:
  `wolf` `6f5713a2…`, `libwolf_rt.a` `ab575b27…`,
  `wolf-cimport-worker` `96f93227…`, `lupin` `3a476442…`, as
  `wolf-toolchain.toml` records. std is wolf-std `14f0ab2`. The nginx
  oracle is 1.30.4, `65595ac2…`.
- The doors: `homebrew-wolf` trunk `660a752`, `Formula/lobo.rb` and
  `aur/lobo-bin` at 0.1.2. AUR `lobo-bin` is 0.1.2-1.
- The release workflow last ran as a rehearsal on 2026-10-07 at wolf
  0.2.25 (run 37702622092) and has not run at 0.2.26 or 0.2.27.
- Parity figures of record are ws58's and ws59's, taken at 4 workers
  on GitHub's hosted runners (4 vcpus) and on kasumi (16 cpus, loaded
  that day). macOS parity has not been taken since ws47 (wolf 0.2.20).
- wolf-lang#713 (open): a program that parks one task per connection
  stalls once about max(16, 8 × cpus) tasks are parked. Whether any
  lobo configuration reaches it is measured below, not argued.

## Prediction

- **P1, the CHANGELOG entry.** `## 0.1.3 — 2026-10-11 — …`, with these
  sections in this order: Security; Upgrading from 0.1.2; Install;
  `lobo -v`; What changed since 0.1.2; Against nginx; The hosts, and
  what is still known wrong. The security section is the three
  sentences above plus what to do (upgrade; there is no configuration
  that avoids it). User-visible lanes: ws51 (stream room), ws52
  (relative `root` and `alias` under `-p`), ws54 (lobo#48 to #52),
  ws55 (the ACME schedule), ws56 (lobo#62, #65), ws57 (memory flat,
  lobo#66, #69), ws58 (the file memo, lobo#67), ws59 (the parser),
  ws60 (the fix), and the pin 0.2.23 to 0.2.27. Not user-visible:
  #58, ws53.
- **P2, the documents that move.** `CHANGELOG.md`; `README.md` (lines
  25, 28 and the 0.1.2 sentence near 180); `docs/GETTING-STARTED.md`
  (41, 46, 67); `docs/CAPABILITIES.md` (31, the audit line);
  `src/shell/shell.lu`'s doc example; `demo/reel/lib.sh`'s default
  and the reel's README and SHOTLIST version lines. The stamp commit
  moves `src/wolf.pkg`, two `shell.lu` constants, the wire token in
  `serve.lu` and four lines of `tests/shell/version_text.lu`. No
  `.wolfi` hash moves.
- **P3, archive sizes.** `src/` is 28,725 lines against 26,053 at
  0.1.2. linux 3.50 to 3.85 MB (0.1.2: 3,328,968 bytes); macOS 3.40
  to 3.75 MB (3,240,415 bytes). Each packed twice, identical.
- **P4, the release workflow.** No change is needed for 0.2.27. It
  builds wolf from source at the pin and stages `wolf`,
  `libwolf_rt.a`, `lupin` and the std pin, as `ci.yml` does, and
  `tools/lobo-dist` already runs inside the gauntlet on both CI hosts
  at 0.2.27. The rehearsal is green on the first dispatch, in 8 to 25
  minutes.
- **P5, the smoke against 0.1.2** (kasumi, the two release-tier linux
  binaries, same config):
  - RSS of one worker after 400,000 keepalive requests: 0.1.2 between
    0.6 and 1.2 GB; 0.1.3 under 10 MB.
  - requests per second at 4 workers, c = 32, 0.1.3 ÷ 0.1.2:
    keepalive 1.25x to 1.50x; close 1.05x to 1.25x.
- **P6, wolf-lang#713.** No lobo configuration reaches it. The serving
  loop polls its connections and does not park a task for each, so
  256 idle keepalive connections on one worker held to one cpu leave
  a new request answered. Streams park in a write but are capped at
  `3·max(cpus, 2) - 2` (4 on one cpu), under the threshold. The one I
  am least sure of is the proxy with many stalled upstreams; it is
  measured with the others.
- **P7, the upgrade.** 0.1.2's shipped `conf/lobo.conf`, the
  GETTING-STARTED examples and the reel's configs load on 0.1.3 with
  `-t` unchanged. `-s reload` does not replace the binary (a reload
  re-reads the config in the running master), so the documented path
  is stop and start; a client sees refused connections for the gap.
- **P8, the gates on the packed binaries.** Smoke, the split-scalar
  tests and `tools/lobo-membudget` green on both archives' binaries.
  The 0.1.2 binary loses its worker to the tests' shapes; the 0.1.3
  binary keeps its pid and answers 400.
