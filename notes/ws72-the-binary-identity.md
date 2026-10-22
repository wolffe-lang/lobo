# ws72 — the master remembers its binary

Crawl 54, lane ws72, GPT-6.1-Sol (Codex). Contract:
`wolf/sprints/wws/41-the-binary-identity/ws72-the-binary-identity.md`.
Starting tree `f32a1b7`; wolf 0.2.34 / lupin 0.1.55 / std `e036bec`
stay pinned. No release, package update, merge, or issue mutation.

## Prediction, before the first change

- P1: `fs_stat` at the pin answers device and inode, as well as size
  and mtime. No content digest fallback will be needed on linux or
  macOS. A missing field falsifies this; name the missing std row.
- P2: the replacement refusal can be deterministic under
  `taskset -c 0-3` without a fixed sleep: poll the workers' own status
  until ready, TERM one recorded pid, then poll the refusal and the
  master's status with bounded deadlines. Both a byte-appended copy
  and a byte-identical new inode are refused; an unchanged path still
  replaces a worker. Every new refusal row must first fail at trunk.
- P3: nginx needs only a copied executable, not a second nginx build:
  renaming a byte-appended copy over its path and ending a worker
  leaves the master forking its original image. Read `/proc/PID/exe`
  and process counts inside the container, never nginx's source.

## Rulings requested, not decided

- R-ws72-1: recommend (a), refuse the replacement and log once for
  that slot; keep surviving workers serving. Implement (a), not a
  master re-exec or a new-version worker. `control upgrade` remains
  explicitly unimplemented.
- R-ws72-2: recommend strict identity, including an identical copy
  with a new inode. A package-manager replacement is an image change
  even when its bytes happen to match. Implement strict identity.

## Inputs, re-derived

- lobo `origin/trunk` is `f32a1b7`; the isolated worktree is on
  `ws72`. The five PR sections follow lobo#108. `ci/tiers.py` maps
  `src/`, `tests/`, `docs/` and `CHANGELOG.md` to the linux gauntlet,
  `notes/` to prose: this is one server program, `Footprint: module`.
- wolf 0.2.34's linux archive `88a9dd3d…` and lupin 0.1.55's
  `1152abc0…`: release API digests read twice, archives checked twice
  on kasumi. Driver `2bfaf7b8…`, runtime `cc058247…`, interpreter
  `ad52ee96…`, also read twice (`logs/toolchains.log`). The archive's
  `std/STD-REV` is `e036bec318ad81ecd5a025612bc2c2adb17527f3`.
- `[os.fs.stat]` at v0.2.34 answers twenty words, with a `have` mask:
  device/inode at 9/10, size at 1, mtime seconds/nanoseconds at 14/15.
  Linux and macOS answer the pair; windows clears those bits. On
  kasumi's filesystem the native and checked test records answer
  `have=1048575`, including both identity words and exact mtime.
  No missing builtin/stdlib row blocks the linux implementation.
- `/metrics` exports the worker id but no restart counter. Refusals
  are therefore counted by their log lines, not a new metrics series.
- The oracle was built once by `docs/DIFFERENTIAL.md`'s recipe and
  pin digest, used only as a black box; its source was not read.
  nginx 1.30.4 `bf6b151c…` (this host's build). Copied, not rebuilt,
  for the image-replacement row.
- kasumi initially had 79 GB free under `/home`, load 1.90. Every
  build and process test is inside rootless podman, `taskset -c 0-3`,
  `ulimit -c 0`. The cached arch container lacks clang and the test
  utilities; the host's EXISTING `/usr` is mounted read-only inside
  it. No package is installed. A lane-owned unix podman API socket
  lets the gauntlet's `lobo-user` start its own root container; its
  configuration HOME is lane scratch, not the user's home.

## Implementation

The saved identity is immutable across reloads. Each later spawn
checks it before allocating an endpoint or calling exec. A mismatch
or failed stat retires that slot; it does not increment `restarts`
and cannot turn into a retry loop. Initial spawns bypass the guard;
an initial stat failure refuses startup before any worker. One
`[emerg]` per refused slot names startup/current identities and the
remedy. Surviving workers and the master's control endpoint remain.
The configured worker count stays visible; the vacant row has
`pid=-1` and is unreachable. A restart is required to refill it.

Linux/macOS use device/inode, size and exact mtime. Only when the
host's `have` mask lacks the pair is SHA-256 content identity used,
with size and mtime still compared (windows's specified posture,
not run here). The guard follows the final symlink, as exec does;
it is not an atomic stat-and-exec API and does not defend against
an untrusted writer racing that window. Root's snapshot gains only
the direct `std.x.crypto.sha2` dependency; no exported declaration
or other module surface changes.

## The nginx row

`logs/oracle.log`: first `--expect-reexec` is red, exit 1 at
`nginx replacement image`; then the normal expectation is green.
The old image was `(dev=50, ino=257877570, size=4509952)`;
the replaced path `(50, 257877583, 4509953)`. The new worker still
answered the old image's complete identity (mtime included), two
workers remained, and HTTP served the body. No second build was
needed. P3 held. `docs/PARITY.md`'s operational delta table and
`docs/CONTROL.md` D5 name the difference: nginx restores the count
by forking its old image; lobo refuses an exec from a changed path.

## Slips

- The first cached-container build had no clang; it exited nonzero
  (`logs/red.log`), never counted as a behavioral red. Existing host
  tools were then mounted read-only, not installed.
- The new test's explicit row first omitted `cross_device`, then
  `unsupported`; those compile failures are not behavioral evidence
  (`logs/red2.log`, `red3-compile.log`).
- A background command's delayed rsync copied the earlier test over
  a local edit. That dropped `cp -p`; the identical-copy precondition
  trapped, leaving three test processes inside the container. They
  were ended by their recorded container pids, and the harness reaped
  the checked run's three. The fixture now preserves the mtime and
  asserts that only the inode changed. No host process was signalled.
- The compiler's inline observation truncates long stdout. Full log
  dumps hid later row verdicts; compact per-row diagnostics replaced
  them before the baseline of record (`red3-truncated-record.json`
  is the earlier, truncated record).

## Follow-ups, not performed

Close lobo#110 after merge. No issue filed or closed by this lane.
The AUR `post_upgrade` note is the release maintainer's follow-up:
0.1.6 refuses a changed-image replacement and can lose worker
capacity until restarted, rather than silently mixing versions.
No tag, release, AUR, tap or planning-repo push is performed.

## Rows and prediction, against the measurement

P1 held on linux: twenty stat words, `have=1048575`, device/inode
and ns mtime answered on native and checked. The pair's macOS and
Windows posture is the pin's specification, not a local run.

The baseline is the unchanged trunk binary, built before the source
was uploaded: debug `89b6e64aa618f3b8…`, release
`c2eeca5b69daba76…` (`logs/red3-binaries.txt`).
`logs/red3.log` is red, 0/2 native/checked lane-runs; the complete
checked record is `logs/red3-record.json`, its compact rows
`logs/red3-rows.txt`:

| row | trunk, before the guard | required result |
|---|---|---|
| unchanged path | GREEN: ordinary worker replacement, restarts=1 | preserve it |
| appended byte, atomic new inode | RED: starts a replacement, restarts=1 | refuse; one survivor |
| identical bytes, new inode, size and exact mtime preserved | RED: starts a replacement, restarts=1 | refuse strictly |
| other build (release beside debug) | RED: starts a replacement, restarts=1 | refuse |
| removed path | RED: repeated executable-not-found spawn failures, restarts incremented | refuse once, no retry loop |
| same inode/size, mtime only changed | RED: starts a replacement, restarts=1 | refuse |

The implementation's final full gauntlet passed the new test on native
and checked (25 s and 23 s respectively); complete gauntlet and
dedicated row records are indexed below. Every refusal row checks
one emergency line, pid=-1 in the vacant slot, no restart increment,
the same surviving pid serving HTTP, and no repeated refusal across
further supervision passes. An identical copy explicitly preserves
size and mtime so the inode, not a timestamp side effect, is decisive.

### Validation corrections before the final head

- The first dedicated `LOBO_BIN` runs exposed a fixture bug: the
  variable was read but the copy command still named the default
  debug binary. Its supposed release record had the debug binary's
  size, and the poisoned-identity plant incorrectly went green
  (`logs/post.log`, `UNCHANGED-PLANT-EXIT=0`). Those runs are NOT
  release/plant evidence. The copy now uses the requested path and
  asserts its copied size before starting any process; `post2.log`
  is the corrected run. The default-debug gauntlet and trunk-red
  rows were not affected by this selector bug.
- A podman API service does not inherit the calling shell's CPU
  affinity. The first gauntlet's nested `lobo-user` container therefore
  was not bounded by the caller's taskset. The final gauntlet uses a
  lane-only engine wrapper that adds `--cpuset-cpus 0-3` as well as
  taskset; `logs/affinity.log` reads `pid 1's current affinity list:
  0-3`. No product/CI wrapper or host package was changed.
- `CLAUDE.md` also requires a named delta in the directive ledger.
  The `worker_processes` description in `src/config/table.lu` gains
  the strict-identity refusal and nginx's old-image fork. The page
  is regenerated through `config.directives_markdown` and the real
  `tools/lobo-directives --emit`, never hand-edited. The final full
  gauntlet is re-run after this source-description change and the
  fixture correction, not claimed from the earlier source tree.

### The corrected controls

`logs/post2.log` exits 0. All six rows are green on native and
checked against both the real debug image (17,541,200 B) and the
real release image (15,244,016 B), before the directive-description
addition. The source selector's size assertion makes a mistaken
fallback to the default image red before any child starts.

The local module plant is `logs/plant-main.lu`, sha256
`357abcfd8b595e305c2c74656e33ade7c3ff1c380f0cf4d52d18a97fb506f083`:
only the expected identity passed to replacements gains `-plant`.
The fix was committed first (`101a2a8`); the plant is a separate
scratch build, never a change to `src/` or the real binary.
`post2.log` reads `UNCHANGED-PLANT-EXIT=1`, 0/2 lane-runs, and
`logs/plant-unchanged-record.json` records `trap(assert)` with
`binary identity unchanged: RED`, a vacant pid=-1 row, restarts=0,
and the emergency naming the poisoned startup identity and the
unchanged current file. Selecting the untouched real binary then
reads 2/2 green and `binary identity unchanged: GREEN`
(`logs/control-restored-record.json`). This is behavioral red,
not a compiler failure or an unattended plant with deleted evidence.

P2 held as predicted: condition-polled readiness and supervision,
with a 20 ms polling interval rather than a guessed startup sleep,
under four CPUs. The complete six-row test takes 23–25 s on each
execution machine across the recorded runs. It is not a claim of literally sleep-free code.


## Final validation and evidence index

The final source tree, including the requested-binary fixture fix and
`worker_processes` ledger, is GREEN in `logs/green2.log`, exit 0,
0 SKIP lines, 388/388 corpus lane-runs. Both tiers build, formatting
and every `.wolfi` match; static differential 33/33, proxy differential
8/8, control differential 20/20, prefork 38/38, privilege witness
25/25, memory 25/25, resolver 9/9, TLS interop/renewal and ACME green.
The dist step packed twice identically and smoked the archive; the
final census reads `nothing left behind`. The final nested privilege
containers use the explicit four-CPU engine wrapper.

`logs/post3.log`, exit 0: all six identity rows green on native and
checked against the FINAL release binary, with the debug binary as
the other-build variant; the nginx old-image fork is green again.
The final debug/release binaries are `1746e50f82e14a9d…` and
`26ab0755e1b1c6e1…` (`logs/head-binaries.sha256`).

Every tested source/document byte was matched against the local PR
tree through `logs/tested-files.sha256` after the final runs. Only this
note, which no gauntlet tool reads, is completed afterwards. Sources
are not claimed from the earlier run: the first full gauntlet is
`logs/green.log`; the final one is `logs/green2.log`.

All paths below are under **kasumi `/home/mfwolffe/lanes/ws72/`**:

- `logs/red3.log`, `red3-record.json`, `red3-rows.txt`,
  `red3-binaries.txt`: the five refusal rows RED at trunk;
- `logs/oracle.log`: nginx's opposite-expectation RED then old-image
  fork GREEN; `logs/post3.log`: the final repeat;
- `logs/post2.log`, `plant-main.lu`, `plant-unchanged-record.json`,
  `control-restored-record.json`: genuine debug/release green,
  poisoned-identity control RED, restored control GREEN;
- `logs/green2.log`, `post3.log`, `green-release-final-record.json`:
  final full gauntlet and release-specific records;
- `logs/toolchains.log`, `affinity.log`, `tested-files.sha256`,
  `head-binaries.sha256`, `evidence.sha256`: pins, CPU bound and bytes.

SHA-256: final gauntlet `0229f5d86eef3561…`, corrected postchecks
`79104799897cf0a8…`, final release/oracle `41ddd987674fa794…`,
trunk record `a570af6aaf54bec2…`, oracle plant `5fb0910b26261130…`.
Full hashes are in `logs/evidence.sha256`.

Kasumi pruned: 1.2 GB to 29 MB after removing this lane's toolchain,
downloads, target outputs and nested rig caches with `podman unshare`.
Logs, the plant's source/records, the source checkout and the pinned
oracle remain. All ws72 containers ended and its API service stopped.

## Not verified

macOS beyond the pin's specification (no build on nomad-1); Windows
and its SHA-256 fallback; a racing writer between stat and exec;
PAX; an initial spawn failing and then retrying after an install (the
same guard is wired into that retry site, but the e2e exercises the
ordinary reaped-worker path). `control upgrade` is unimplemented.
No performance or release claim is made by this lane.
