# Changelog

## 0.1.0 — 2026-09-07 — the first artifact

The first release of **lobo**, a web server written from parts in
[wolf](https://github.com/wolffe-lang/wolf-lang). It reads an
`nginx.conf`, serves static files and proxies, drains on reload
without dropping a connection, acquires its own certificates over
ACME, and is checked on every commit against a **pinned real
nginx/1.30.4** running the same config — the differential harness is
the test suite, not a comparison chart.

### Install

Download the archive for your host, unpack it, and run it in place —
there is nothing to install and no dependency to resolve:

```sh
tar -xzf lobo-0.1.0-<host>.tar.gz
cd lobo-0.1.0-<host>
./lobo -v
./lobo -t -c conf/lobo.conf
./lobo -c conf/lobo.conf serve      # then: curl -i http://127.0.0.1:8080/
```

`GETTING-STARTED.md` in the archive is the whole learner path, and it
is the same script this release's CI runs against **this** archive on
a clean runner before the release page is published.

### The hosts, and the two that are refused by name

| host | archive |
|---|---|
| `x86_64-unknown-linux-gnu` | yes |
| `aarch64-apple-darwin` | yes |
| `x86_64-pc-windows-msvc` | **no** — named refusal until s60c |
| `aarch64-unknown-linux-gnu` | **no** — named refusal until s60c |

lobo ships exactly the hosts wolf's **release tier** serves. The other
two are not an oversight and not a silence: wolf's LLVM release tier
does not build them yet (upstream s60c), and `tools/lobo-dist` refuses
to produce an archive for a host whose binary would not run. The gap
closes when the tier does.

### `lobo -v` names its own provenance

```
lobo version: lobo/0.1.0 (built with wolf 0.2.6, pin 398e5f5)
```

A binary that cannot name the toolchain that built it is a binary
nobody can debug. `-V` adds the standard-library pin, the tier and the
module set. A build that is not this release says so with a `+dev`
suffix — the archive's name carries it too, so a rehearsal build can
never be mistaken for a release.

### Reproducible from the pin, not from the runner

`wolf-toolchain.toml` pins the exact wolf (`v0.2.6`, `398e5f5`), lupin
(`v0.1.27`) and wolf-std (`bd12ef5`) this binary was built with, and
the release workflow builds that toolchain from source on every dist
host before it compiles a line of lobo — never the wolf a runner
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
place lobo deliberately differs from nginx is a **named delta** in it.

## ws19 — 2026-09-07 — the artifact (lobo gets a version, and an archive a stranger could run)

wsc07's second sprint, and the one W7 is actually about: *someone
other than us can run it*. What this sprint owed was a version, a
release workflow that builds from the pin, an archive that carries
what a first-time user needs, and a job that installs the PUBLISHED
archive on a clean machine and proves it serves. All four landed.

**THE PIN, first, because the archive is reproduced from it.** ws18
pinned wolf at a DEV-STAMPED trunk sha (`0.2.5+dev.32f66bf`) because
r09 had not tagged v0.2.6 yet. It has now, so this sprint takes the
**v0.2.6 RELEASE TAG (`398e5f5`)** — a released tag is what a stranger
can reproduce and a dev stamp is not. The contract asked for the delta
to be measured rather than assumed, and it was: `32f66bf → 398e5f5` is
**five commits** (`a369b22` spec, `6919280` ledger, `b2880a4`
CHANGELOG, `e257914` release sites, `398e5f5` merge), ten files,
+325/−89, and under `crates/` **exactly one** — the interface-pretty
test snapshot re-recording its own toolchain stamp 0.2.5 → 0.2.6. Zero
compiler source, zero runtime source. So the tag cost this sprint no
source motion at all: what moved in lobo is the `.wolfi` toolchain
stamp (0.2.6, fourteen modules, **ZERO item motion**) and the pin
file's `version_line` losing its `+dev`. lupin went v0.1.26 → v0.1.27
(is38) alongside; **the lupin lane gap narrows and this sprint does
not spend it** — `net_wait`, `net_listen_with` and `os_cpus` now exist
on the reference machine, so tests that declared `lanes: native` for
those calls alone could widen, but widening a lane is a measurement
per test, routed as residue to the next maintenance sprint. Deltas
classed: ZERO behavioral, ZERO diagnostic, one mechanical.

**THE VERSION, and the hole underneath it.** lobo is **0.1.0** and
`-v` prints

```
lobo version: lobo/0.1.0 (built with wolf 0.2.6, pin 398e5f5)
```

— nginx's prefix, wolf's parenthetical, and W7's acceptance criterion
met literally. `-V` adds the std tree, the tier posture and the module
set. The hole: **a wolf program cannot ask what compiled it.** `wolf
--version` gets its own stamp from a compile-time env its driver
reads; a wolf PROGRAM has no such input — `wolf build` takes no
define, the language has no compile-time environment read, and D33
forbids the build script that would write one. So lobo's provenance is
**SOURCE**: five constants at the top of `shell.lu`
(`release_version`, `release_channel`, `toolchain_version`,
`toolchain_pin`, `std_rev`). A source stamp is a lie waiting to
happen, so `tools/lobo-stamp` — a gauntlet step — is what keeps it
true: it holds every version site equal (`wolf.pkg`, the wire token in
`serve.default_opts`, the five constants, `wolf-toolchain.toml`'s
`[wolf] version_line` and `[std] rev`), and it holds the **channel**
against git's own tags. `""` claims to BE `v<version>` and is admitted
only when no such tag exists yet or it points at HEAD; `"+dev"` is the
honest answer everywhere else, and the gate is RED between the tag and
the commit that flips the channel — **that red is the design.** Filed
upstream as **wolf-lang#247**: a builtin naming the compiling
toolchain, D57 for programs. The day it lands, two of the five
constants become that call and this tool stops holding them.

**THE ARCHIVE.** `tools/lobo-dist` builds with the toolchain
`wolf-toolchain.toml` names — `lib-toolchain.sh` refuses identity
drift before a line compiles, which is what "reproducible from the pin
file" *means*, and the failure the target exists to prevent is
building with whatever wolf a runner has. The build is the gauntlet's
release tier flag for flag (`WOLF_MIDEND=0` while wolf-lang#146
stands, TWELFTH measurement, still open). The archive is flat: the
binary, `conf/lobo.conf` (an nginx.conf serving `html/` on loopback
8080), `html/index.html`, an empty `logs/`, `GETTING-STARTED.md`,
README, CHANGELOG, `docs/`, LICENSE, and **BUILD** — the provenance
record the smoke reads back against the binary. The pack is the
reproducible-builds recipe (`--sort=name`, one `SOURCE_DATE_EPOCH`,
`--numeric-owner`, `gzip -n`) and the tool **proves the pack half by
packing twice and comparing digests** rather than claiming it. GNU tar
is required for the pack and refused by name when absent (macOS ships
bsdtar); UNPACKING needs nothing special, because a learner has
nothing special.

Measured on nomad-1 (aarch64-apple-darwin): just under **3 MB**,
packed twice identical, and the whole build-pack-unpack-smoke cycle
runs in **7 seconds** — cheap enough that it is a gauntlet step, so
the archive a stranger would download is proven on every commit rather
than at the tag. (No digest is quoted here on purpose: this file is
*inside* the archive, so an entry naming the archive's own sha256
would be a fixed point that does not exist. The `.sha256` beside each
asset on the release page is the one that means anything.)

**THE SMOKE, twice.** `tools/lobo-dist` ends by unpacking its own
archive somewhere else with the HOST's tar and running it as a learner
would: `-v` compared against the archive's own BUILD line, `-t -c
conf/lobo.conf`, serve, `GET /`, the body **byte-compared to
`html/index.html`**, the `Server:` header, then `-s stop` and a
liveness check that it actually went down. First run: `200`, **934
bytes, byte-identical**, `Server: lobo/0.1.0`, `stop: shutting down
(generation 1)`. `.github/workflows/release.yml` then does it a second
time on a runner with **no checkout at all** — no lobo source, no
wolf, nothing but the published archive, curl and tar — after
verifying the `.sha256`. A release nobody has installed is a claim,
not a fact.

**THE WORKFLOW.** A dist matrix over the two hosts wolf's RELEASE tier
serves (linux x86-64, macOS aarch64); windows x86-64 and linux
aarch64 are **named refusals until s60c**, in the release notes and
in `lobo-dist`, which refuses to produce an archive for a host whose
binary would not run. Every leg clones the pinned siblings and builds
the pinned wolf exactly as `ci.yml` does — and **if `WOLF_CI_TOKEN` is
absent this job FAILS, loudly.** ci.yml may loud-skip because local
runs remain its gate; a release job that publishes nothing while
reporting green is a different thing, and it is a lie. The release is
a DRAFT until a `publish` job counts the assets and refuses at fewer
than two archives and two digests (#226's shape, twice-proven
upstream). Notes are cut from this file by `tools/lobo-release-notes`
(#214's mechanism: wolf's own v0.2.1 and v0.2.2 shipped empty bodies
for want of it), and `workflow_dispatch` runs the same dist and smoke
jobs from any ref — because a release workflow that has never run is
the worst kind of untested code, and the tag is not a lane's to press.

**A BUG THE SMOKE FOUND, of a shape this repo has seen before.**
`lobo-dist`'s smoke `cd`s into the unpacked archive, and
`lib-toolchain.sh` resolves the toolchain as `.wolf-bin/wolf` —
RELATIVE. From inside the archive that is a bare `No such file or
directory`. It is ws18/lobo#1's shape exactly (a tool that names its
binary relatively cannot be used from anywhere else), and it was
caught by RUNNING the smoke rather than reasoning about it. Fixed:
`lobo-dist` absolutizes `$WOLF` and `$LUPIN` before it goes anywhere.

**AND A SECOND ONE, which only the other kernel could find.** The
smoke asserted the `Server:` header with `grep -qi "^Server:
lobo/$version\r*$"`. In a POSIX **basic** regex `\r` is a literal
`r`, so under GNU grep that pattern silently reads *zero or more
`r`* and never matches a real CRLF header — macOS was green, linux
was red, and the archive built and served correctly on both. The
assertion now strips the CR instead of trying to match it. Two bugs
this sprint, both in the CHECKING code rather than the server, and
both found by running the thing on a machine that was not the one it
was written on. That is the entire argument for the learner smoke.

**WHAT W7 STILL WAITS ON, said plainly.** lobo is the only PRIVATE
repo in the org. The learner smoke is a clean-MACHINE test today — it
downloads with the workflow token — but not yet a clean-STRANGER
test, because an unauthenticated download of a private repo's release
404s. Making lobo public is the human's decision and no lane's to
take. Nothing in the workflow changes when it flips; the smoke simply
stops needing a token.

**Also**: lobo carries a **LICENSE** at last (GPL-3.0, byte-identical
to every sibling repo in the org — it was the only one without),
`docs/GETTING-STARTED.md` is the learner path the release's own CI
executes, and CLAUDE.md's host-tool list gains GNU tar and curl.

## ws18 — 2026-09-06 — the turn deletes itself (and it was worth more than the accept path)

wsc07's first sprint, and a maintenance one by contract: the human's
W7 charter (*someone other than us can run it*) is settled but does
not gate this work — ws19 and ws20 take it. What this sprint owed was
a pin bump, a deletion, a rig-hygiene fix, and **the headline table
re-run with the workaround gone**. The table is the point, and it
came back bigger than the fix was predicted to be worth.

**THE MEASUREMENT, first.** ws17 shipped an accept turn — nginx's
`accept_mutex` without a mutex — because `net_accept` parked a losing
hand in a blocking `accept(2)` after its readiness wait
(wolf-lang#242, filed by ws17 with the number the fix was worth:
11,622 req/s with the turn against 17,347 free-for-all, a predicted
**1.49x**). s138 closed #242. ws18 deleted the turn and measured the
same shape on the same box in one session — the same source built
twice, once at the commit before the deletion and once after (three
hands, `ab -n 6000 -c 32`, a connection per request, three runs each):

| build | runs | median |
|---|---|---|
| with the accept turn | 13,417 · 12,866 · 12,863 | **12,866 req/s** |
| free-for-all (ws18) | 25,470 · 23,663 · 21,443 | **23,663 req/s** |

**1.84x.** And the full table, both binaries, N=18, `ab -n 20000 -c
32`, a 1 KiB file, the pinned nginx/1.30.4 as the control:

| server | shape | with the turn | **free-for-all** | cores (turn → free) |
|---|---|---|---|---|
| lobo, 1 process | close | 13,203.76 | **13,508.27** | 0.65 → 0.69 |
| lobo, 1 process | keepalive | 10,264.27 | **9,501.84** | 0.58 → 0.58 |
| lobo, 18 hands | close | 13,557.26 | **16,120.62** | 0.84 → **3.08** |
| lobo, 18 hands | keepalive | 9,554.14 | **38,960.68** | 0.65 → **4.54** |
| nginx, 1 worker | close | 27,656.32 | 27,731.17 | 0.48 → 0.45 |
| nginx, 18 workers | keepalive | 72,960.48 | 86,432.66 | 1.95 → 2.04 |

Read four times. **(1) The deletion is worth more than the accept
path.** Eighteen hands on a KEEPALIVE load — which contains almost no
accepting at all — go from 9,554 to **38,961 req/s, 4.1x**. That is
not the thundering herd; it is `shell.accept_wait_ms`, the turn's
other half, which capped the hand's WHOLE `net_wait` budget at the
turn boundary, so a hand serving thirty-two established connections
woke on the ROUND instead of on its own sockets. The workaround was
throttling the serving path to keep the accept path correct, and
nothing in ws17 could see it, because with the turn there was no other
posture to compare against. **(2) `worker_processes N` is N-ish at
last**: cores-used 0.84 → **3.08** on close and 0.65 → **4.54** on
keepalive. **(3) One process did not move** — 13,204 → 13,508 close,
inside the noise, which is the control: `accept_turn` short-circuited
at `hands <= 1`, so a single-process lobo never paid for the turn.
**(4) On this shape lobo now passes this box's nginx at the same
count**: three hands free-for-all serve 23,663 against nginx's 19,553
at eighteen workers. The keepalive gap (38,961 against 86,433) is
real, and it is W8's.

**THE DELETION, inventoried.** `shell.accept_turn`,
`shell.accept_wait_ms` and `shell.accept_slice_ms` are gone — **84
lines of pure surface (three functions and their clauses) and, with
the plumbing, `src/shell/shell.lu` net −106**, three items out of
`shell.wolfi`
(77 → 74; the item key sets diffed BOTH ways, exactly three removed
and three signatures re-recorded, nothing else moved), the `--hands N`
flag off the hand's argv (14 elements → 12) and out of `Cli`, the
`hands` parameter out of `serve_main` and `spawn_worker`, four guard
sites out of the serving loop, and 57 lines of turn assertions out of
`tests/shell/worker_surface.lu`. What is left in `main.lu` is one
sentence: every hand keeps both listeners in its wait set on every
pass. **What replaced the tests** is the DELETION asserted (an argv
carrying `--hands` takes the ordinary unknown-option road; `--inherit`
— the one internal flag that outlived it — still refuses by name when
it rides alone) plus a new gauntlet check.

**THE CHECK THAT REPLACED THE TURN** is `tools/lobo-prefork`'s **quiet
server**, and it is the one #242 would fail: three hands free-for-all,
**one** GET, then two seconds of SILENCE, then every hand must still
answer its OWN control endpoint and the master must still read three
serving hands with no replacement. That is exactly how #242 was found
(two hands, one GET, one hand never spoke again) and it is asserted at
the level lobo cares about instead of quoted from upstream. prefork
**35/35 → 38/38**, and it is a gauntlet step, so linux CI runs it too.
The distribution was re-checked and SURVIVES the deletion: 90
connections over three hands, **36/29/26** on macOS and **26/34/31**
on the linux runner, free-for-all, against ws17's 28/32/31 through the
turn — the turn assigned slices by ordinal and the kernel does not, so
this had to be measured rather than assumed. **Linux CI (9m45s) is
GREEN at the ws18 head**: corpus 253/253, prefork 38/38 including the
quiet server (3/3 hands answering after the silence), the failover gap
1 ms.

**Pins.** wolf → **trunk `32f66bf` dev-stamped** (`0.2.5+dev.32f66bf`;
r09 had not tagged v0.2.6 at the pin step — checked, `git tag` tops
out at v0.2.5, seventeen commits behind this rev — so the either/or
takes the sha), lupin → **v0.1.26** (is37, the byte has a domain), std
→ **trunk `bd12ef5`** (sc37's `std.net.listen_with`/`adopt_listener`/
`wait` and `std.os.cpus`). Twenty-one commits over two trains.
**Deltas classed: ONE BEHAVIORAL (#242, and lobo consumes it as a
deletion), two DIAGNOSTIC-ONLY (#243, #238 — lobo's sources draw
neither), one MECHANICAL (the `.wolfi` toolchain stamp 0.2.4 → 0.2.5,
fourteen snapshots re-recorded with ZERO item motion), and zero source
motion predicted and ZERO MEASURED** — the first pin bump in this
repo's history that moves no source for the pin's own sake. The
PAIRING GAP is zero for the second time (wolf@32f66bf declares lupin
0.1.26); the LANE GAP is not — lupin 0.1.26 still conforms to
`982f857` (v0.2.4), so none of s137's builtins exist on the reference
lane and every test that names one still declares `lanes: native` (or
native+checked). wolf-lang#146 re-probed at this pin, the **ELEVENTH**
measurement: still open (the `sc_muladd` dominance ICE, reproduced
here), `WOLF_MIDEND=0` stays.

**wolf-std#6, answered and DECLINED on purpose.** sc37 wrapped the
acquisition half — `std.net.listen_with`, `adopt_listener`, `wait`,
and a new `std.os.cpus` — and asked whether lobo would move. It does
not, and the reason is the loop's own shape rather than inertia: the
serving loop is raw-fd end to end (one `net_wait` over a `List[int]`
holding the control listener, both http listeners and every open
connection, with the connection table as parallel lists indexed by
position), so a `Listener` would be built and immediately unwrapped
through `.fd` to enter the same set; the inherit PAIR would split
across tiers, because `os_spawn_with` is deliberately not wrapped
(std.process's `Command` question is open) and a master would spawn
through the builtin while its hand adopted through std; and every one
of the four is a pure delegate, so the move buys a spelling. The
posture is uniform and written into `wolf-toolchain.toml` where the
next lane will read it. lobo's preference on the `os_spawn_with`
shape — which sc37 asked for by name — is posted on the issue.

**lobo#1 — the rig reaps itself.** `tools/lib-rigproc.sh` is new: a
reap at START of anything a previous run left behind and a reap at
EXIT of the run's own, armed by `rig_arm` in all eighteen tools that
start a process, on `EXIT`/`INT`/`TERM` so a red step, a Ctrl-C and
the 600 s tool ceiling are all covered — sc12's idempotency rule
applied to processes. **The leak was not the trap you would guess**:
`wolf run tests/rig/dnssrv/dnssrv.lu &` makes `$!` the DRIVER and the
listener its child, so the tools' `kill "$dnspid"` reaped wrappers and
orphaned helpers. MEASURED before the fix: three orphaned `dnssrv`
processes on this box, one **45 hours** old and one from each of the
two gauntlet runs this sprint opened with — **exactly one leaked per
run**. After it: `rigproc: own, at exit — reaping 1 process(es)` and a
clean census; a deliberately planted orphan is met with `rigproc:
stale from an earlier run — reaping 1 process(es)` on the next tool's
first line. The marker is **argv[0], never the rest of the command
line**, and this repo paid for that distinction in the same hour: a
first cut matched the whole cmdline and killed the shell that had
merely TYPED `target/lobo-release` in a command. Every rig launch site
now passes an ABSOLUTE program path so the marker names THIS checkout
and can never reach another tree.

**Suites.** corpus **253/253** lane-runs (unchanged — the deletion
removes assertions from an existing file rather than a file), prefork
**35/35 → 38/38**, differential 3/3, proxy-differential 8/8,
control-differential 9/9, signal 20/20, membudget 17/17, resolver 9/9,
shell 15 probes (14 parity, 1 named delta, 0 red), and
metrics/logdiff/dryrun/confcheck/tls-interop/tls-renewal/acme green.
Gauntlet GREEN before every commit; GitHub CI (linux) read on every
push, with a live watch. The gauntlet's own last line is now
`rigproc: own, at exit — reaping 1 process(es)`, which is lobo#1's
measurement stated as a running total: one leak per run, and none
after.

**One finding recorded as a negative.** A single-process witness for
#242 was written, measured — and thrown away. It asserted that a take
against an emptied queue returns inside the listener's budget rather
than parking, which is true; it is also true at the OLD pin, because
one process cannot make the kernel say READY and then empty the queue
behind its own back. The park needs a real sibling. Proven by running
the candidate witness under a wolf built at `d6aeaca`: green there
too. The witness that survives is the quiet server above, which needs
three real hands and gets them.

## ws17 — 2026-09-04 — many hands, FOR REAL (the cores, and the order desk on a socket)

wsc06's closing sprint, and the one where D73's sentence — *lobo uses
all the cores, and a running lobo takes orders on every host* — stops
being a plan. ws16 built the many-hands machinery and MEASURED that
the cores stayed idle, filing four issues that named why. All four
landed upstream in one wave (s137 for #127/#233/#234/#235, s136 for
#227), and this sprint is lobo consuming them — plus the mechanical
tail the pin could not be separated from, plus one new upstream
finding the shape immediately produced.

**THE HEADLINE, first, because it is the charter's evidence**
(docs/WORKERS.md, `tools/lobo-prefork-bench`, this box: macOS 15
arm64, 18 cpus, N=18, `ab -n 20000 -c 32`, a 1 KiB file, the pinned
nginx/1.30.4 beside it — ws16's column last):

| server | shape | req/s | cores | ws16 req/s |
|---|---|---|---|---|
| lobo, 1 process | close | **11,277.81** | 0.69 | 37.37 |
| lobo, 1 process | keepalive | **10,324.18** | 0.67 | 576.21 |
| lobo, 18 hands | close | **12,329.98** | 0.84 | 69.60 |
| lobo, 18 hands | keepalive | **9,934.98** | 0.68 | 1,117.68 |
| nginx, 1 worker | close | 23,488.10 | 0.47 | 38,123.20 |
| nginx, 18 workers | keepalive | 83,831.08 | 2.18 | 111,383.38 |

Read three times. **(1) The reactor gate is gone and it was the whole
story**: one lobo process went 37 → 11,278 req/s on the
connection-per-request shape, about **300x**, from `net_wait` alone —
ws16's loop blocked 25 ms in the control accept, 25 in the listener's
and 12 per open connection every pass, so it got roughly one accept
per 62 ms. lobo at one process is now **within 2x of nginx at one
worker** on that shape, a sentence this repo has never written.
**(2) The kernel distributes**: 90 connections over three hands as
**28/32/31**, every hand `serving` on ONE socket, `accepted=` on every
status row. **(3) And N is still not N×** — 12,330 against 11,278 —
because of the accept turn below, whose cost was measured directly
(11,622 with the turn against 17,347 free-for-all, three hands).

**Pins.** wolf → **trunk `d6aeaca` dev-stamped** (`0.2.4+dev.d6aeaca`;
r08 had not tagged v0.2.5 at the pin step — checked, `git tag` tops
out at v0.2.4 — so the either/or takes the sha), lupin → **v0.1.25**
(is36, the byte arrives), std → **trunk `c0f75e8`** (sc36's
`std.net.unix`). Sixty-three commits across three trains. **Deltas
classed: one MECHANICAL-WITH-SOURCE-MOTION, one mechanical-only, five
ADDITIVE surfaces consumed on purpose, zero refused-by-name.** The
source motion is s136's #231 — the eight byte producers answer
`List[byte]` now — and ws16's prediction that lobo would stay on
`List[int]` expires with it: **306 E0401s at the first build over 21
files, closed over 51 `.lu` files (381 `List[int]` declarations become
`List[byte]`, 201 reads widen with `b as int`, 221 writes narrow with
`x as byte`; `byte as char` is E0805 and bridges through `int`)**, and
47 `.wolfi` signatures re-record with ZERO item motion in any of the
fourteen. The int lists that are NOT bytes stayed int, one by one: OID
arcs, PEM block lengths, the resolver's expiry and fd tables,
sslcert's `der_at`/`der_n`/`leaf_n`, acmeca's index tables. The
mechanical-only delta is the toolchain stamp, 0.2.3 → 0.2.4. **The pin
and the tail are ONE commit** because neither compiles without the
other, and the `.wolfi` re-record rides the next one alone (the
repo's interface law forbids mixing); the gauntlet is green across the
pair. #146 re-probed a TENTH time — still the sc_muladd dominance ICE,
`WOLF_MIDEND=0` stays. A LANE GAP is named in the pin file: lupin
0.1.25 predates s137, so none of the five new builtins exist there and
every test that names one declares `lanes: native checked`.

**Distribution: two shapes, both measured, one shipped.**
`net_listen_with(addr, reuse_port, backlog)` (#234) is **refused**,
and the witness says why rather than the page: `tests/serve/
reuse_port_posture.lu` builds a live three-member group, dials it
thirty times and prints which member the kernel woke — `0/0/30`, every
SYN to the newest bound socket on macOS, so a prefork built that way
is ws16's posture with a different cause (on linux it would work, and
a server that picks its architecture per host is a server with two
architectures). What ships is **inheritance** (#235): the master binds
the http and TLS listeners and never accepts on them, `os_spawn_with`
hands them to every child as descriptors 3 and 4 in the config's own
order, and a hand adopts by POSITION — the numbering is the contract,
so the argv carries a count (`--inherit K`) and never a descriptor.
Replacements inherit the same socket, which is why the master holds it
for life, and why a `kill -9` no longer needs ws16's 78 ms failover:
the survivors are already accepting.

**THE NEW FINDING, and it is the front gate now: wolf-lang#242.**
`net_accept` awaits readiness with the socket's deadline and then runs
a **blocking** `accept(2)`. With N hands on one listener a single
connection wakes all N; one wins and **the losers park in the syscall
until the next connection arrives** — a hand alive at 0.0% CPU
answering no control verb and running no timer, which its master then
reaps and replaces. Found with two hands and ONE GET, isolated three
ways (the non-blocking ask does not park, the blocking one does, and
removing the connection handles from the wait set does not help).
Invisible under load, fatal on a quiet server. **lobo's answer is
nginx's `accept_mutex` without a mutex**: hands take 10 ms turns off
the wall clock, so exactly one hand has the listener in its wait set
at any instant and there is no race to lose. Two halves make it a
mechanism rather than a decoration — the wait is CAPPED at the turn
boundary (without it a hand blocks 25 ms through its own 10 ms slice:
**2,725 → 11,622 req/s** when that landed) and a turn DRAINS up to 64
accepts, each after the first guarded by a zero-deadline `net_wait`.
It retires the day #242 lands: one pure function, its twin, and the
`--hands` flag come out.

**Readiness (#127), and an honest correction to its number.** One
`net_wait` over the control listener, both http listeners and every
open connection replaces the deadline ws16 armed on each; a connection
is STEPPED only when the wait names it. The floor is the SIGNAL
poll's, named rather than hidden: signals have no readiness handle, so
while reception is armed the wait cannot outlast a `kill -HUP`'s
latency — 25 ms, which is BETTER than ws16, where one pass was three
stacked accepts. **Idle cost was measured, the same binary built twice
with only the wait swapped, 120 s idle holding one keepalive
connection: 0.32 s of cpu the ws16 way against 0.26 s — about 19%,
not upstream's 37x.** lobo's idle loop was never busy; it was asleep
in a timer. What the deadline cost was WAKE LATENCY, and that is the
whole of the 300x. Quoting someone else's 37x here would have been
quoting someone else's workload.

**Cores (#233).** `worker_processes auto` reads `os_cpus()` — and the
number is SCHEDULABLE cores, quota- and affinity-aware, so a two-cpu
quota on a sixty-four-core host answers 2 where ws16's `/proc/cpuinfo`
row count answered 64 and started sixty-two hands that would never get
a core. The `io` row is not swallowed into a default. `shell.cpu_count`
and its pure twin RETIRE (they could not live there: shell is on the
lupin lane and lupin predates s137), and ws16's macOS notice with
them.

**The order desk on a socket (#227) — ws15's filing, ws16's
deferral.** `control unix:<path>` (nginx's spelling) is now the
RECOMMENDED form, because file permissions are the boundary a loopback
port cannot be: every local user on a host can dial 127.0.0.1, which
is the whole reason ws15 grew the token arm. Under `worker_processes
N` each hand gets the sibling `<path>.wN`, so **a HAND's order desk is
a uid boundary too** — ws16's residue, closed. Every row is named
rather than swallowed: `unsupported` refuses at startup BY NAME (the
distinction #227 was filed to get), `exists` refuses without
clobbering a path lobo did not bind, and a path too long for
`sun_path` says so with the ~100-byte limit spelled out — measured
with a 126-byte scratch path, which is what a real prefix looks like.
`net_close` unlinks; a hand's socket is the MASTER's to remove before
a replacement, because the process that BOUND a path owns it. lobo
calls the builtins directly and says so: std wraps neither
`listen_with` nor `adopt_listener` (**wolf-std#6** stands, sc37's).

**Also.** The master probes each hand at most every 200 ms — its probe
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

**Witnesses.** corpus 249 → **253** lane-runs
(`reuse_port_posture.lu` and `control_unix_e2e.lu` are new, native +
checked); `tools/lobo-prefork` **35/35** with the distribution counts
printed; every other suite count identical (differential 3/3, proxy
8/8, control 9/9, logdiff 4/4, signal 20/20, membudget 17/17,
resolver 9/9).

## ws16 — 2026-09-03 — many hands (prefork workers, D7 kept)

wsc06's second sprint, the first half of D73's sentence: *lobo uses
all the cores*. It ships the MACHINERY of nginx's `worker_processes`
— a master, N hands through `os.process`, supervision, fan-out, a
row per hand, a field per line — and it ships the MEASUREMENT that
says the cores are not used yet, with the two upstream filings that
name why. A prefork that does not scale is a finding; this entry is
that finding, with its number.

Pins advance first, gauntlet green at the trio before a line changed
(suite counts IDENTICAL: corpus 238/238, differential 3/3, proxy 8/8,
control 9/9, logdiff 4/4, signal 20/20, membudget 17/17, resolver
9/9): wolf → **trunk `31170d1` dev-stamped** (`0.2.3+dev.31170d1` —
r07 had not tagged v0.2.4 at the pin step; the either/or takes the
sha), lupin → **v0.1.24** (is35, the byte in the mirror — one release
ahead of wolf's declared 0.1.23 pairing, forward-only), std →
**trunk `f016303`** (sc34: the byte tier is bytes, refused with
numbers; upstream's binary pin == data pin == 31170d1, so the
compiler pins agree exactly for the first time). **Deltas classed:
one BEHAVIORAL, zero mechanical, zero refused-by-name.** The
behavioral one is #224's: the checked machine now arms a deadline on
a reset socket (s135), so the rig residue D41 carried since ws14 —
`region_measured.lu`'s swallow, `budget_cap.lu`'s drive order —
comes out. Retiring the swallow went red 1 in ~17 native runs and
taught the lesson: the rig closed the accepted socket over UNREAD
request bytes (an RST close), and the client's read raced the
reset; it now drains the request first (a FIN close on every host)
and reads its reply through `?` on both lanes. [type.byte] is zero
motion, measured (lobo's byte paths stay `List[int]` until sc35 lands
the producers — wolf-lang#231's numbers); no `.wolfi` moved for the
bump (the stamp reads the version, 0.2.3, not the dev suffix); the
`checked-refuses:` rows are UNTOUCHED (they name C1, not #224).
#146 re-probed a NINTH time — still the sc_muladd dominance ICE,
`WOLF_MIDEND=0` stays.

**The measurement first, because it is the charter's evidence
(docs/WORKERS.md, `tools/lobo-prefork-bench`, this box: macOS 15
arm64, 18 cpus, N = 18, `ab -n 4000 -c 32`, a 1 KiB file, the pinned
nginx/1.30.4 beside lobo).**

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

Read the lobo rows twice. **Cores used: 0.01 at one hand, 0.21 at
eighteen** — lobo is not CPU-bound at all. The serving loop is
DEADLINE-bound: each idle pass blocks 25 ms in the control
listener's accept and 12 ms per open connection's read step (the
ws04 shape every hand inherits), so a connection-per-request load
gets about one accept per pass. And the 1.9x from 1 to 18 hands is
NOT a second core: exactly one hand holds the listener at N=18
(`lsof` shows one LISTEN socket; one row says `serving`) — the
master's per-pass CONNECT probe lands on the serving hand's control
listener and wakes its accept, removing the 25 ms idle stall, which
doubles that one hand's pass rate. The other 0.20 cores are seventeen
standbys retrying a bind and answering probes. nginx at 1 worker
does 1000x the close-shape rate on 0.19 cores; at 18 it spends 1.70
cores because the kernel spreads the accepts.

lobo at 18 hands serves what lobo at 1 hand serves, on one core,
because the kernel is distributing nothing: the runtime binds
`std::net::TcpListener` with `SO_REUSEADDR` only (a second process's
bind of the same port is `io` — measured with a self-spawned child),
every runtime socket is CLOEXEC and `os_spawn` passes only stdio (a
spawned child's descriptor table holds ZERO TCP sockets — measured
with `lsof`), and `std.net.Listener` is a table index with nothing to
adopt. Filed **wolf-lang#234** (SO_REUSEPORT / a listener option),
**wolf-lang#235** (descriptor inheritance and adoption — the pair
`upgrade` needs too) and **wolf-std#6** (the std half). nginx at the
same N scales because its workers share the inherited socket. The
number the bench ALSO produced, and routes: lobo is not CPU-bound —
0.01 of a core at one hand — because a spawn-free loop with no
readiness surface time-slices with deadlines (25 ms in the control
accept, 12 ms per connection step, every idle pass), so the
connection-per-request rate sits near one accept per pass; the 1.9x
at 18 hands is that stall removed by the master's own probe waking
the serving hand's accept, not a second core. wolf-lang#127 (the
reactor) gets the table as its customer report; the stall itself is
a maintenance row in the closeout, not ws16's.

**The machinery, shipped.** `worker_processes N | auto` carries with
nginx's grammar and nginx's `-t` diagnostic (probed); `auto` reads
`/proc/cpuinfo` on linux and is 1 with a notice on macOS (no cpu
query — **wolf-lang#233**); `0` serves as 1, a named delta. With
N >= 2 the process that ran `lobo serve` is a MASTER: it owns the
pid file and the config's `control` endpoint, binds no http listener,
starts N hands (`os_exe()` + `os_spawn`: this executable, `serve`,
the same prefix and config, `--worker i --worker-control <ep>` — no
secret crosses the argv; a hand reads the `token <file>` itself), and
supervises them over their endpoints with a CONNECT probe (never a
round trip: `os_wait` blocks and there is no `try_wait`, so a hand's
socket is the liveness surface; a busy hand still answers from its
backlog). Three silent passes after a 3 s grace is gone: `os_kill`,
`os_wait`, `worker-exited worker=N reason=… code=…`, a fresh hand in
the slot, `worker-started … restarts=R`. **Accept distribution at
this pin is the honest shape the measurement forces:** every hand
RETRIES its bind each pass; the first to win serves, the others
stand by and take the listener the moment its holder dies —
`tools/lobo-prefork` kills the serving hand with a real `kill -9`
and measures the window: **78 ms** (minus the clock driver's own 223
ms — a `wolf run` compiles per call, and the first reading of 718 ms
was the driver's, not the server's). The day #234 lands every hand's
bind succeeds and the same loop distributes accepts, no lobo change.

**The verbs fan out** (docs/CONTROL.md): `reload` is parsed by the
master first (D2 holds: a rejected config reaches no hand) and rolled
through the hands one at a time — each swaps and DRAINS in place, the
ws08 drain per process, watchable on that hand's own stanza;
`quit`/`stop`/`reopen` fan out; replies keep ws15's prefixes and gain
`workers=K/N`. Rolling PROCESS replacement is a named delta: lobo
cannot hand a socket to a new process (#235), so a spawn-new-retire-
old reload would refuse connections in the gap, and row 2 of the
control differential (zero refusals) is a row lobo keeps. The hands
are long-lived. A SIGKILLed master orphans its hands (no channel —
named delta; `kill -TERM` is the orderly path, TERMINATE is `stop`
and `stop` fans out first).

**A row per hand** (docs/DRAIN.md, docs/WORKERS.md): `lobo status`
answers the master's head (`live-region-bytes` SUMMED over the
hands), `workers: N`, and `worker i: serving|standby|unreachable
control=… generation=… live=… events=… live-region-bytes=…
budget-503s=… restarts=…` folded from each hand's own stanza (a hand
prints `worker: N` / `listening: true|false` under its head); JSON
schema 1 stays, additive (`workers_configured`, an empty
`generations`, a `workers` array). **The meter and the cap are per
hand** (docs/BUDGET.md): the witness refuses a 24 KiB file under
`memory_budget 4k` on the serving hand, whose row reads
`budget-503s=1` beside siblings at 0. `/metrics` is one hand's
numbers and says which (`lobo_worker_id`, a new gauge; the
aggregation question is routed to the pin that carries #234).

**A field per line** (docs/LOGGING.md, docs/REPLAY.md): a hand ends
every line it emits in ` worker=N` — after `seq` on a vocabulary
event, at the end of a prose notice — appended, nothing renamed
(the ws15 line is a PREFIX of the ws16 line, asserted); the master's
lines and a single-process lobo's carry none, byte for byte. Two
events join the frozen vocabulary (`worker-started`,
`worker-exited`; nine → eleven). **REPLAY.md's multi-process
boundary:** `seq` is per PROCESS, so a merged log is N+1 total orders
separable by the stamp and orderable across each other only by the
wall clock; the completeness anchor is per stream (a hand's row
carries ITS `events`); the fan-out's order is reconstructible from
the master's stream alone.

**The either/or on #227: the ELSE arm.** s136 had not merged at Act-2
start (01:12 EDT: the issue OPEN, the worktree at 31170d1 with three
uncommitted corpus edits, no PR). Named-gate deferred to ws17, with
what lands then written down (the `unix:` address form, the token
arm demoted to windows, the hands' endpoints as unix sockets under
the prefix).

**Windows:** claimed, not measured — no lane. `os_spawn` runs there
and the runtime's sockets are non-inheritable there too, so the
posture would be the standby posture; stated as such in
docs/WORKERS.md.

**Findings filed.** wolf-lang#233 (no cpu-count query —
`worker_processes auto` cannot ask the host), wolf-lang#234 (no
SO_REUSEPORT and no listener option — N processes cannot accept on
one port), wolf-lang#235 (a spawned child inherits no listening
socket and std.net adopts no descriptor — the shared-listener shape
and `upgrade` both need the pair), wolf-std#6 (`listen_with` /
`adopt_listener` at the std tier). #146 probed a ninth time.

Corpus 238 → **249** lane-runs (`worker_processes.lu` ×3,
`worker_surface.lu` ×3, `prefork_e2e.lu` ×2, `nowms.lu` ×3); a new
gauntlet step, `tools/lobo-prefork` (32/32); `tools/lobo-prefork-
bench` (not gated — the table above); metrics registry +1 series
(`lobo_worker_id`). Branch `ws16`, unmerged.

## ws15 — 2026-09-02 — the server takes orders (and pays four small debts)

wsc06 "many hands" opens (D73: *lobo uses all the cores, and a
running lobo takes orders on every host*). This sprint is the second
half of that sentence.

Pins advance first, gauntlet green at the trio before a line changed
(suite counts IDENTICAL: corpus 233/233, differential 3/3, proxy 8/8,
signal 15/15, membudget 15/15, shell 13, confcheck 8): wolf → the
**v0.2.3 TAG** (`3befc3e`), and with it **the bare stamp at last** —
`wolf 0.2.3 (wolfgang, pin 3befc3e)`, built at the tag with
`WOLF_COMMIT=3befc3e WOLF_RELEASE=v0.2.3` so D57's release rule
grants it. lupin holds at **v0.1.23** and std at **trunk 35f69ef**,
which closes the pairing gap to **zero** for the first time in this
repo's history: wolf@3befc3e declares lupin 0.1.23 as its pairing and
that is exactly the release staged beside it. v0.2.2..v0.2.3 is six
commits and ws14 already pinned five of them, so the delta lobo takes
is r06's release train only — #212 (dist writes one archive per
target), #214 (release notes cut from the CHANGELOG), #215 (nine
literal productions, anchors held 411), #225 (filed upstream) — none
of which lobo's sources reach. **Deltas classed: zero behavioral, one
mechanical, zero refused-by-name.** The mechanical one is the
release commit's own: every `.wolfi` header embeds the toolchain
version by design, so all fourteen snapshots re-record `toolchain
0.2.2` → `0.2.3` and their export/pkg hashes and std dep-hashes
re-derive under the new driver — with **zero item motion** (verified:
not one `[n]` line moved in the diff). #146 re-probed an **EIGHTH**
time, still open, `WOLF_MIDEND=0` stays.

**The control endpoint takes orders.** ws04 built a loopback reload
pipe and left a question; D73 asks it properly. The `control`
directive now names an endpoint a running lobo answers the whole verb
set on — `reload`, `quit`, `stop`, `reopen`, `status`, `upgrade`,
`ping` — and `lobo control <verb>` is its CLI door, so `lobo -s` can
keep **exactly** nginx's four words (the parity `tools/lobo-shell`
probes against the oracle). A rejected reload, an unknown verb, an
`unauthorized` answer and `upgrade`'s named refusal are all exit 1,
so `lobo -s reload && deploy` cannot run on a reload that did not
happen — a gap the new differential found and closed.

`upgrade` exists before it works, deliberately: it is the ONE verb
the endpoint reaches that no signal does. On unix UPGRADE's bit is
lobo's own poll probe (an outside `SIGUSR2` is indistinguishable from
it — the wsm01 residue); on windows `RELOAD`/`UPGRADE` have no analog
at all. Dispatching it so it can say "when it lands it lands HERE" is
what makes the endpoint the place the binary swap will go.

**The listener, per host: loopback TCP everywhere — measured, not
assumed.** wolf has no unix-domain socket at the v0.2.3 pin. Every
spelling answers a bare `io` (`/tmp/x.sock`, `unix:/tmp/x.sock`,
`unix:///tmp/x.sock`) while `127.0.0.1:0` binds; the runtime's
`net.rs` is `TcpListener`/`TcpStream` and `spec/11-os.md` has no
clause. Filed as **wolf-lang#227**. That is why lobo cannot have the
filesystem-permissioned socket haproxy, systemd and nginx-plus use,
and why the second auth arm exists at all: **loopback is not a uid
boundary**.

**Auth: loopback always, an optional shared secret beside it.**
`control <addr> token <file>` arms a secret; the wire line becomes
`<secret> <verb>` and anything else is answered `unauthorized`,
dispatches nothing and changes nothing (the e2e witness proves the
generation did not move). Three decisions, each named rather than
implied: lobo **reads** the token file and never writes one — std has
no file-permission surface at this pin (**wolf-std#5**), so a token
lobo generated would land at the umask's mode, and a world-readable
secret is worse than none; a config naming a token file lobo cannot
read **refuses at startup**, because an endpoint whose auth silently
does nothing is the failure mode that matters; and `ping` is
**exempt**, because it is the liveness probe `-s` and the stale-pid
check use, and gating it would let a rotated token make a live master
look dead and have the next start replace a running server's pid file.

**A verb and a signal are one code path, asserted as a diff.** Both
triggers reach one dispatch and one emission site, so ws09's
vocabulary gains no event and no new key — `signal-received` grows a
trailing `source` (`signal`|`control`), appended, nothing renamed,
every earlier prefix pin still matching. `tools/lobo-signal` now
reloads one server twice, once by verb and once by `kill -HUP`,
extracts both five-line event blocks, normalizes the generation
numbers, seq stamps, content hash and age, and requires **exactly one
differing line** — then normalizes `source` too and requires the
blocks to be **byte-identical**. 15/15 → 20/20. The verbs with no
signal twin emit nothing, which is what keeps `sig`'s value set
frozen at `reload|terminate|quit`.

**The nginx differential grows an operation half**
(`tools/lobo-control-differential`, a gauntlet step; 9/9). Four rows
CARRY: config re-read, listener survival (20 connects each after the
reload, zero refusals), an already-open connection never served the
NEW config, and a bad config refused with the old one still serving
AND a non-zero exit on both. Four deltas are NAMED and measured
rather than hidden — **D1 transport** (`kill(pid, SIGHUP)` with the
kernel authorizing vs a loopback endpoint with a token), **D2 who
parses** (nginx's CLIENT parses and exits 1 before the master ever
hears; lobo's MASTER parses and answers the verdict plus the
generation that kept serving), **D3 narration** (0 drain events in
nginx's error log against 6 in lobo's), and **D4 idle keepalive at
reload** (nginx's old worker closes them once it finishes shutting
down; lobo's draining generation holds them until they close or
`worker_shutdown_timeout` bites — lobo is the more forgiving, so an
nginx-written client keeps working and a lobo-written one may not
survive nginx). docs/CONTROL.md is the page.

**ws14's windows sentence flips to a measured rule on every host.**
`lobo -s reload` against a config with no `control` directive now
refuses BY NAME — "a running lobo is reached ONLY over its control
endpoint at this pin (there is no arbitrary-pid signal send —
wolf-lang#126)" — instead of dialling the http port. The second half
of the windows promise is therefore true everywhere, for the same
reason, and it is probed on linux and macOS. What stays CLAIMED is
the windows half itself (the console-handler mapping); lobo's CI is
still linux and a windows lane is still a ws16-class decision.

**D40 resolved: the envelope follows the growth law.** ws14 measured
`charge(N) = 16 × pow2ceil(N) − 16` and found a BAND in which the
runtime refused a body the meter had ADMITTED — 33,000 bytes under
`memory_budget 40k` charged 1,048,560 against a flat-16× cap of
655,360 and died at the join. That made the cap a SECOND METER with
arithmetic no config states. The envelope is now `16 × pow2ceil(
memory_budget)`, which makes it a **backstop**: for any body the
meter admits, `N ≤ budget` so `pow2ceil(N) ≤ pow2ceil(budget)` and
the charge is strictly under the cap; the stream path's one 64 KiB
chunk (1,048,560) sits under it because admitting a streamed body
needs `budget ≥ 65,536` and therefore a cap ≥ 2,097,152.
`tests/serve/budget_cap.lu` ASSERTS that over every budget from 1
byte past the stream threshold, and `tools/lobo-membudget` MEASURES
the closure: the same file, the same config, 200 in full at
`mem-rt-hw=1048560` under a cap of 1,048,576 — a sixteen-unit margin
— with **no `site=region` event anywhere in the run**, while a
50,000-byte file beside it is still refused by the meter at
`site=file`. 15/15 → 17/17. The operator rule collapses to one
sentence ("set `memory_budget` to the bytes you are willing to
admit"); ws14's power-of-two footnote is retired. The `site=region`
mapping keeps its witness where a config can no longer reach it —
the join, driven directly.

**The other two debts.** **wolf-lang#224** (the checked machine
killing a connected peer's handle after lobo's serve sequence): s135
had NOT merged at either gauntlet — the branch exists locally with
one commit, on `[type.byte]` spec work, and the issue is open — so
the either/or's ELSE arm was taken: nothing adopted, the
`checked-refuses:` rows left standing, noted here and in the
closeout. **wolf-std#4** (a resolver surface in std.net): open, sc34
has not landed one, the ask stands unchanged.

**Findings filed this sprint.** wolf-lang#227 (no unix-domain socket
surface; every unix spelling answers a bare `io`) and wolf-std#5 (no
file-permission surface, so a program cannot create a secret that is
not world-readable). Both shaped the design rather than being worked
around, and both are named in docs/CONTROL.md where the design
touches them.

**The linux CI earned its keep.** The first push of the differential
was green on macOS and RED on the linux runner: the keepalive probe
read `pre=` empty on the lobo side only. The cause is lobo's own
write shape — it writes the head and the body with separate calls, so
Linux delivered them in two segments and one `net_read` yielded
headers with no body, while macOS coalesced them and hid it. The rig
driver now reads until the body carries a newline (bounded), and an
empty `pre` is reported as a HARNESS fault rather than a server
mismatch, so the next occurrence names itself.

Corpus 233 → **238** lane-runs (`control_verbs.lu` on three lanes,
`reloadhold.lu` on two); the gauntlet gains one step.

## ws14 — 2026-09-02 — the cap lands (and the signal arrives)

The budget is structural on BOTH halves: the meter admits, the
runtime's own region cap enforces, and the day the two disagree is
measured, not theorized.

Pins advance first, gauntlet green at the trio before a line changed
(suite counts IDENTICAL: corpus 228/228, differential 3/3, proxy
8/8, signal 15/15, membudget 5/5, resolver 9/9): wolf → **trunk
5f99b9f** (the s134 merge; r06 had not tagged v0.2.3 at the pin
step, so the D57 dev stamp `0.2.2+dev.5f99b9f` — built with
`WOLF_COMMIT=5f99b9f`, no release stamp; ci.yml's tag probe finds
none and stays `+dev`), lupin → **v0.1.23** (is34), wolf-std →
**trunk 35f69ef** (sc33; std's own machine pin is the same 0.1.23 —
the first bump at which the two repos' interpreter pins agree).
Deltas classed: the interface snapshots did not move at all (zero
re-record, the cap branch's own `interface(...)` commit rides the
merge); #146 re-probed a SEVENTH time — the same `sc_muladd`
dominance ICE, `WOLF_MIDEND=0` stays; membudget's "round B
retained" 11,072 KB (macOS) vs 12,444 KB (linux CI) — host, not
pin, both under the #191 named gate. One rig delta at the bump,
classed host-not-pin and fixed in the witness: macOS's page
compressor (holding ~40 GB on the rig that day) shrank the server's
RSS between two `ps(1)` samples so round A read 6,976 / 7,792 KB
against a 10.6 MB steady reading (2 of 9 quiet runs; 0 of 15 at the
previous pin) and the differential blamed round B — a tripped
differential is now re-driven once, both pairs printed, and only a
second trip is red (a leak trips every drive; a compressed sample
does not).

**The cap lands.** wolf-lang#219 closed at s134 — the LLVM emitter
takes a mangled symbol's address across partitions, so the proc
`src/budget` spawns from a non-entry module links under
`WOLF_MIDEND=0 --release`, the exact shape the release tier refused
at ws13 — and branch `ws13-cap` is merged at the new pin, no
conflicts, the interface snapshots already true. Per lane, stated
(docs/BUDGET.md's table): **native** runs it (`budget_cap.lu`'s
four relations, `budget_cap_e2e.lu`'s real server, `cap_shape.lu`);
**release** runs it — the gauntlet's tiers step links
`@budget.run_small.task0.entry` and every release-binary witness
runs that binary; **checked** — `wolf conform-run --checked`, the
s23 UB machine — **refuses by name**, `unsupported` at `mem` with
`x-unsupported-construct: "structured concurrency in checked
execution (C1 deferred)"`, and `tools/lobo-corpus` gains a
`//! checked-refuses: <construct>` directive that ASSERTS that
record as a lane-run (a refusal by the wrong name, a run, or a
crash is red; declaring both `checked` and `checked-refuses` is a
header error) — never a blanket skip; every witness whose refusal
fires before the proc keeps its checked lane, and the one budgeted
200 that lived in `budget_refusals.lu` moved to `budget_cap.lu`;
**lupin** runs the shape (`cap_shape.lu`) and cannot run the serve
suite (no fs — the suite's posture since ws01).

**The breach, end to end through a real socket.** ws13 could only
drive the join directly, on a theorem that the cap cannot fire on a
meter-admitted request ("the small path charges ≈ 8N + 352" — one
measurement, extrapolated). The end-to-end witness this sprint was
asked for falsified it: the ledger's growth law is `charge(N) =
16 × pow2ceil(N) − 16` (1,024 → 16,368; **1,025 → 32,752**; 4,097 →
131,056; 40,000 → 1,048,560 — the buffer doubles and the ledger keeps
every abandoned buffer), so #203's 16× holds exactly AT a power of
two and reaches 32× just past one, and **a budgeted small body is
refused by the runtime whenever `memory_budget < pow2ceil(body)`**
though the meter admitted it. `tools/lobo-membudget` now runs a
second server under `memory_budget 40k` on the release binary:
rounds A'/B' RE-BASELINED through the capped proc (A' 10,800 KB, B'
11,696 KB, difference 896 KB, 29 KB/req — the same two gates as
A/B, which read 448 KB and 27 KB/req uncapped in the same run), then a 33,000-byte
file → `503 Service Temporarily Unavailable`, `Connection: close`,
the event `budget-exceeded gen=1 site=region budget=40960
would=40961 cap=655360`, the 32,768-byte file beside it (a power of
two) 200 in full through the proc, fifty keepalive requests after
the breach (the proc died, the server lived), `budget-503s=1` and
`mem-rt-hw=524272` in `lobo status`. 15/15. The band is written into
BUDGET.md with the operator rule (round the budget up to the power
of two above the largest small file, or 64k+ — the stream path is
outside the band by construction), the directive table, and ledger
row D40: the envelope is deliberately LEFT at #203's 16× rather than
silently widened to the growth law, because `16 × pow2ceil(budget)`
makes the region site unreachable from any config again — what the
cap is FOR is the campaign closeout's decision, and every refusal in
the band is loud and named meanwhile. BUDGET.md's "which half is
structural" flips to **both**; the ws10 deferral row (D30's cap
half) closes dated, so does ws13's #219 row.

**The signal arrives (windows).** s60b landed `[os.signal.platform]`'s
windows row in the pin: CTRL_C/CTRL_CLOSE → terminate, CTRL_BREAK →
quit, RELOAD/UPGRADE with no windows analog. lobo's promise is one
sentence in docs/DRAIN.md: on windows, `lobo -s reload` reaches a
running lobo over its `control` endpoint or not at all — there is
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

**Findings filed.** wolf-lang#224 — on the checked lane (the UB
machine) a client socket's handle dies when the peer it dialled is
closed after lobo's serve sequence ran on that peer (`net_deadline`
→ `io`; native and lupin keep it; present at v0.2.2 too);
`region_measured.lu` had been swallowing exactly this since ws12,
`budget_cap.lu` orders its drives so the named refusal is reached
first and says why (D41).

Corpus 228 → 233 lane-runs (`budget_cap.lu` and `budget_cap_e2e.lu`
join — three lane-runs plus `budget_cap.lu`'s `checked-refuses`
assertion — and `cap_shape.lu` gains its own); membudget 5 → 15
checks.

## ws13 — 2026-09-02 — the name resolves in time (wsc05 opens)

The finally-list's last STRONG item ships: `proxy_pass http://name`
resolves without stalling the loop, and the pin names a release.

Pins advance first, gauntlet green at the trio before a line changed
(suite counts IDENTICAL: corpus 213/213, differential 3/3, proxy
8/8, membudget 5/5): wolf → **the v0.2.2 TAG** (8cda3aa) — the bare
stamp at last, because s132's cap and D68's fault merged BEFORE the
tag this time — lupin → **v0.1.22** (is33: the contained trap is
`fault(alloc-contract)` at the join; the two tags name each other),
wolf-std held at a62a5d4 (its trunk had not moved). #146 re-probed a
SIXTH time at the tag: the same ICE at the same site, `WOLF_MIDEND=0`
stays. The interface re-record moves every header with zero item
motion. GitHub CI's first real run on this branch refused the tag
pin as identity drift (`+dev.8cda3aa` vs the bare `0.2.2` the pin
names) — the workflow now grants xtask's own `WOLF_RELEASE` stamp
when the pinned rev is a tag, and the branch is green on GitHub.

**Async upstream DNS.** report 11 §2 item 9, the one STRONG item
wsc03 left unshipped, measured first: with a loopback resolver
holding its answer 800 ms, a static request on a SECOND connection
waited **805 ms** behind a proxied request's name — the dial
resolved the name synchronously on the one poll loop's thread, with
no deadline. There was no blocking call to wrap: std.net says in its
own header that `dns`/`resolve` is not a function it has, and the
runtime's `net_connect` hands a name to getaddrinfo (its
`connect_timeout` resolves first and reaches no lane). Both FILED
(**wolf-std#4**, **wolf-lang#217**), neither absorbed: lobo now
carries a DNS-over-TCP stub client (`resolver`, a leaf module — the
wire half pure over `List[int]`, the TTL cache with nginx's `valid=`
override and round-robin, a pending-query table the loop TICKS under
a 1 ms deadline like any other socket) and a PARK: serve asks which
name a request needs before it reads a byte past the head, the loop
skips that connection until the query settles, then steps it from
the top with the cache warm. After: **static-ms=1**, proxied 836,
cached 0 with exactly one query recorded (`tools/lobo-resolver`, a
gauntlet step; `tests/rig/dnssrv` is the resolver, in wolf). nginx's
`resolver … valid=` and `resolver_timeout` carry as directives, `-t`
answers nginx's own `invalid parameter` wording, the two parameters
lobo cannot honour refuse by name (`ipv4=off`, `status_zone=`);
LOBO-L012 names a hostname with no resolver in effect (the stall),
LOBO-L013 names the delta in lobo's favour — nginx resolves a static
`proxy_pass` name once at load and ignores `resolver` for it (trac
#1064); lobo re-resolves under the TTL. Every other delta (TCP-only,
A-only, first address, failures held 1 s, a 0-TTL held 1 s) is a
row in docs/RESOLVER.md's table; both proxy-differential confs carry
the directive so the oracle and lobo prove they parse the same line
(8/8). Two vocabulary events appended (`upstream-resolved`,
`upstream-resolve-failed`, seq-stamped), one metric family
(`lobo_upstream_resolutions_total{result}`, 22 families), the
`$upstream_addr` log variable names the resolved address.

**The cap adoption — built, witnessed, and gated by codegen.** s132's
`region r(cap: n)` and D68's proc-boundary fault are in the pin, and
ws13 consumed them: a budgeted request's regioned body work runs
inside a `spawn proc` under `cap: 16 × memory_budget` — the #203
ledger envelope, and the directive documents the arithmetic — and
the join maps the reason to 200 / close / **503 `site=region`** /
500; ws12's measured `region_bytes` comes back out of the proc
through a loopback self-pipe, because a proc's `normal(value)` is
unreadable at the join and a channel cannot be a proc argument on
wolfc. Green on the native tier, and the RELEASE tier refuses to
emit it: any proc spawned from a non-entry module lands its entry
shim outside its object (`func.addr of @budget.run_small.task0.entry
outside this object's subset` — #136's shape for a PROC), a 30-line
reproducer filed as **wolf-lang#219** with a second finding
(`conform-run --checked` answers `unsupported@mem` with an empty
diagnostic for every proc spawn, wolf-lang's own conformance files
included, while `run --checked` runs them). A proc the release tier
cannot emit is not a proc lobo can ship, so the adoption lives whole
on branch **`ws13-cap`** (the flip is a merge the day #219 closes),
and trunk carries `tests/serve/cap_shape.lu` — the exact program a
budgeted request runs, in one module, on native and lupin — plus
BUDGET.md's theorem that at this pin the cap cannot fire on any
request the meter admits (the head site's charge puts every cap
above every ledger reading lobo's shapes produce), which is the
property the contract asked for stated as an inequality rather than
a hope. The membudget suite holds its marks unchanged (the trunk
binary has no proc in it).

**#197's Tier-2 shapes, stated.** Four, re-read against s132 and
posted upstream: a capture is written on the JOIN side (a killed
proc runs no writer); the reason class is a stable key (a closed
set); the record boundary is the proc argument record (s87 copies
it at spawn — record at the proc boundary, replay the proc); and
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
**e6cf24e** — trunk, D57 dev-stamped `0.2.1+dev.e6cf24e`, because the
number this sprint came for landed in s131 AFTER the v0.2.1 tag —
lupin **v0.1.20** (wsm04's named fallback retires; lobo, wolf-std and
the driver's own pairing line name the same interpreter for the first
time) and wolf-std **a62a5d4** for sc31. #146 re-probed at the new
pin, FIFTH measurement, ICE unchanged, `WOLF_MIDEND=0` stays; #192's
misleading W1001 is GONE (r04 fixed it). The interface re-record moves
every header and export-hash with ZERO item motion in eleven modules.

**The measured half.** `region_bytes(r)` / `live_region_bytes()`
([mem.region.account.1/.2]) reach lobo: `serve` reads the ledger
inside the per-response and per-chunk regions the ws10 audit put
there, and the entry high-waters it per generation BESIDE ws10's
metered figure — two numbers answering two questions, published
together and never subtracted from each other (`mem-rt-hw` and
`live-region-bytes:` in status text, `mem_rt_high_water` and
`live_region_bytes` in the JSON; additive, schema stays 1). ws10 could
only argue the streaming path was O(1) in file size from RSS noise;
the runtime now states it as an EQUALITY — 128 KiB and 256 KiB stream
to the same high water, pinned in `tests/serve/region_measured.lu`.
The same measurement found what BUDGET.md now teaches: a 64 KiB chunk
charges its region **1,048,560 bytes**, 16× the payload — 8× because a
byte buffer is a `List[int]` and 2× because the ledger is cumulative
by contract. Not a lobo bug, not absorbed: **wolf-lang#203** filed
with the numbers, and #187 commented because the gap bears on the cap
half's units. The cap arm itself: s132 had not merged at Act-2 start,
so the contract's **named-gate defer** was taken — the meter ships
query-only and honest, #187 owns the adoption.

**`/metrics`, in core.** A new `metrics` module holds ONE registry —
name, type, label shape and help for every family — and `sample`
asserts the labels it was handed are exactly the ones declared, so a
per-URI or per-client series is not discouraged or linted but
UNWRITEABLE. `tools/lobo-metrics` (a gauntlet step) measures the
consequence on a live server: four more distinct URIs add exactly zero
series. Twenty-one families cover every landed sibling — connections,
requests by status class, a fixed 5ms..10s duration histogram, the
proxy leg, TLS handshake failures by reason, generation info as the
Prometheus info-metric idiom, ws09's dropped lines, ws11's event
count, and ws10+ws12's two memory high waters. The counters live as
plain ints in the poll loop's own frame, which is the MEASURED
hot-path answer for a spawn-free server: one mutator needs neither
shards nor atomics, an increment is one checked add, and the module
header names the day that stops being true. The endpoint is two
phase — `serve` recognises the path, `main` renders it — because
rendering per pass would leak megabytes an hour into #191's root arena
to answer a scrape a minute. `/status.json` serves ws08's object on
the same listener, proving its design-once note. The scrape is an
ORDINARY request: it counts itself one behind, it logs, and under a
tiny `memory_budget` it 503s (site `admin`, the fifth) — which is
correct, and a rig case. `metrics on|off` is lobo-native, `-t`
validated in nginx's own flag wording, and linted twice: L010 for the
one-way door, L011 when the endpoint sits on a routable listen —
because at v0 the bind address IS the access posture, and the docs say
so in four lines. `docs/metrics.md` is generated from the registry
(`tools/lobo-metricsdoc`, a gauntlet step), so a Grafana panel and a
live scrape cannot disagree; the exposition is checked clause by
clause against the vendored Prometheus text format spec.

**The row gets a name.** wolf-std#3's `named`/`row_name` are adopted
at both TLS-client error sites: forty arms re-listing a twenty-one-row
vocabulary lobo does not own become two `named(...) else |Row(name)|`
handlers plus a per-site hint table keyed by the row's stable NAME.
Messages byte-identical, `timeout` still 504 (the live
`https_gateway` case runs that arm), and a future std row now reads as
a bare name instead of breaking the build.

Corpus 203 → 213. wsc03 closes here; the closeout declares W5.

## ws11 — 2026-09-01 — replay the race

A scheduling bug becomes an artifact. The rig gains the seeded
half of lupin's determinism surface (pin HELD at 0.1.19 — v0.1.20
is match-arms, no explore change; probed day one): the corpus
runner takes `//! explore: N` (the file's whole schedule space,
every gauntlet run, green only on agreement WITH a closed frontier
— an open one is red, tense discipline) and `LOBO_SEED` (every
lupin-lane run under a bug report's seed, failures printing the
replay command). The witness pair keeps the ws08 drain-finish
hazard alive as a specimen: `drain_finish_race.lu` decides
retirement by racing the timeout message against the closes in one
select — FIFO-clean (a laptop never sees it), 3 distinct outcomes
across 16 schedules under explore — while `drain_finish_fixed.lu`
is the real loop's shape (retirement is a STATE check) and closes a
24-schedule frontier on one outcome, held by `explore: 64` forever.
`tools/lobo-replay` (a gauntlet step) walks the whole story every
run: the finding, the `.loborace` artifact (schema 1: seed +
decision stream + pinned bytes + lupin identity), three
byte-identical replays FROM the artifact (2× seed, 1× stream), the
fix's closed frontier. The server side stays honest: lobo is
spawn-free, so it never prints a seed — instead every vocabulary
event now carries `seq=` (stamped at the emission seam; builders
and prefix pins untouched) and status carries `events:` (additive,
schema stays 1), making an attached log an ordered, GAP-VISIBLE
event stream with a completeness anchor. docs/REPLAY.md states the
boundary exactly (values, real time, the membrane; no production
flight recorder — Tier 2 deferred, asks filed). Corpus 200 → 203
(the specimen pair's lupin lanes plus the fixed twin's explore run).

## wsm04 — 2026-08-31 — the doors open inward

Lobo consumes its own library's TLS client. Pins advance to wolf
b80d239 (D57 dev-stamped; no v0.2.1 tag existed at acquisition), the
lupin v0.1.19 tag, and wolf-std 26f0588 — the bump that carries
sc29's `std.x.tls.client` — with the full gauntlet green at the trio
before a line changed (corpus 195/195; #146 re-probed byte-identical,
the midend stays off). Then the last two named refusals in the config
surface retire: **`proxy_pass https://`** (D21's upstream leg) dials
through the std client — trust anchors via `proxy_ssl_trusted_
certificate` (REQUIRED: lobo has no unverified mode, nginx's
verify-off default is a named delta), SNI always, chain+hostname+
CertificateVerify before a request byte leaves, TLS failures mapped
to 502 (504 for a mid-handshake deadline) with the row named in the
error log — and the differential grows an https case where nginx and
lobo both proxy a VERIFIED fixture-cert upstream, client legs
byte-equal (8/8). **https `cert_ca`** (D25) follows: the ACME client
dials an https directory verified against `cert_ca_root`, the
harness CA serves its whole RFC 8555 directory through lobo's own
TLS server half behind the conn seam (`--tls`), and cold issuance +
renewal run over TLS end to end. The loopback law is UNCHANGED and
forever: only the https *transport* gate retired; a non-loopback CA
is still a named -t refusal. Measured honestly: the std client's
handshake costs ~3.6s on this rig (native tier, WOLF_MIDEND=0 —
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
structure audit — the sprint's soul — found lobo held ZERO region
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
the typed door — RFC 8259-validated lines, numbers as numbers, the
ws08 drain vocabulary decoded. Sinks are bounded and loud-dropping in
the spawn-free loop; logrotate's reopen cycle works end to end. Three
new lints (L005 inert level, L006 native doors, L007 what a text
format loses). Corpus 166 → 184.

## ws06 — 2026-08-30 — certificates without the dance

Built-in ACME: RFC 8555 HTTP-01 end to end, hot-swap issuance with no
reload, a renewal daemon, and `lobo cert status`. The certbot dance
still works — the coexistence test serves a certbot block live beside
a `cert auto` block. The fixture CA is a pebble-class RFC 8555 server
written in wolf, verifying account JWS on every POST with real
dial-backs; it caught two client bugs a vendored oracle would have
accepted. Deltas recorded: Ed25519 not ES256 (the frozen jose seam),
loopback-plain `cert_ca` only until a std TLS client exists (D25),
key files at umask not 0600 (D26). Corpus 158 → 166.

## wsm03 — 2026-08-29 — the name lands

Lobo (D64) — the code stops spelling wws: 86 files, the binary's own
voice (banner, diagnostics, `Server: lobo/0.1.0`, LOBO-L lint codes),
zero seam motion. Pins advance to wolf addcd7f + the lupin 0.1.16
tag, and the first macOS three-lane gauntlet runs 158/158 — two
rig-side deltas fixed on the way (the TLS oracle refuses LibreSSL by
name; the signal gate widens so a real SIGHUP drives the drain
off-linux). wolf-lang#146 re-probed unhealed; the midend stays off.

## wsm02 — 2026-08-27 — the pin pays back

Pins to wolf 53f6191 + lupin is24, zero source breakage. TLS session
keys now come from `os_random` — the OS CSPRNG, trapping loud rather
than degrading (#143 retires) — with the interim HKDF derivation
deleted and an entropy probe at TLS bind. The three W0305 sentinel
dodges revert to the natural arm re-raise (is24's #44 fix). The
midend flip-back was attempted and refused: a #142-class survivor
found, filed as wolf-lang#146, `WOLF_MIDEND=0` stays.

## ws07 — 2026-08-27 — the dry-run that means something

`-t --request` predicts the routing decision with a why-it-lost
trace: the real matcher grows a trace parameter (never a second
implementation), effective directives filter to the winning chain
with `-T` provenance, TLS and stat notes are opt-in, and unknowable
headers say UNRESOLVED by name rather than guessing. Cross-checked
against the live server: the predicted static path's bytes are the
live body, and the backend records exactly the predicted proxy
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
its first byte-equal case, the gauntlet, and CI against the pins —
committed ahead of any remote.
