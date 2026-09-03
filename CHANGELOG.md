# Changelog

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
