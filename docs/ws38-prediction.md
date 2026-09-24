# ws38 — the prediction, committed before the edit

Wave 47, subwave 3, lobo#28. Written 2026-09-24 on lobo trunk
`1055f84`, pins wolf 0.2.16 (`93a5fe5`) / lupin 0.1.38 (`ba357aa`) /
std `070884c`, all unmoved. Nothing in `src/` has been edited when
this file is committed; the measurements land beside these lines in
the ws38 CHANGELOG entry, right or wrong.

## §2 — the contract's inputs, re-derived against origin

| input, as the contract states it | what origin says |
|---|---|
| lobo trunk `1055f84` (ws37) | **holds** — `1055f84a04df21564fffed315389d9c3bc24e5c8` |
| pins 0.2.16 / 0.1.38 / std `070884c` | **holds** — `wolf-toolchain.toml`; the kasumi archives hash `84e30c05…` (wolf) and `828b5c55…` (lupin), the release assets' own digests, members identical to ws37's table |
| 13 `List[GenRow]` rebuild sites in `src/main.lu` | **holds at 13**, but the contract's (and lobo#28's) list of functions omits one: `start_reload` carries **three** of the thirteen. The full list: `bump_live` 2, `note_request` 2, `on_conn_close` 2, `retire_zero` 1, `start_reload` 3, `mark_draining` 2, the generation-1 seed 1 |
| `bump_live` fires per accepted connection | **holds**, and it is **not** what the instrument sees — below |
| ws37 measured 19 → 24 KB/req, ratchet 64 | **holds at trunk**: five runs on kasumi, **24 / 26 KB/req** in all five (`~/lanes/ws38/instr-trunk/run{1..5}.log`) |
| lobo#28 has comments | it has **none** |

**The discriminating observation.** `tools/lobo-membudget` drives 400
keep-alive requests over **one** connection per round, so a
per-connection rebuild fires twice per 400 requests and could not
move a per-request figure by 5 KB. What does move it: a probe build of
trunk (six `eprint` lines, one per rebuild function, never committed;
`~/lanes/ws38/probe-count`) run under the instrument counts, on the
plain server, **`retire_zero` 1,807 times** against `bump_live` 3,
`on_conn_close` 3, `note_request` 2 — and on the capped server 1,916
against 7 / 7 / 4. `retire_zero` runs at the end of **every poll
pass** (`src/main.lu`, step 4 of the loop) and rebuilds the whole
table with a plain `push(g)` whether or not anything retires: **a deep
copy of the configuration model per poll pass, about two per
request.** lobo#28 names the right family and the wrong member.

## §3 — the prediction

**P1 — the shape.** `push(take …)` through the rebuild, **not** "no
rebuild at all". Every rebuild function takes its list (`take gens`;
every caller is already `gens = f(gens, …)`), and every row goes in
with `push(take g)` or `push(take GenRow { … })`. Why not an in-place
update: the table's own header says index-assignment is a one-lane
shape, and wolf-lang#438 (an index store aligns with `push`) is being
implemented this wave (s180) — a store whose cost and lane coverage
are changing under us is not the fix for a copy. A rebuild that moves
its rows costs one small list allocation of a handful of rows and is
what the code always meant. `start_reload`'s fresh row keeps the
caller's `ng.conf` alive (the sinks and the log are rebuilt from it
after), so it is spelled `copy` there: once per reload, exactly the
copy the plain push made silently.

**P2 — the sites.** **13** push sites, plus the **5** signatures that
do not yet take (`note_request` already does) and their **9** call
sites. **Falsified** by any other push site needing to change, or by
any `copy` spelled other than `start_reload`'s.

**P3 — the instrument after.** Per-request retention **19 ± 1
KB/req**, through the capped proc **20 ± 1**. **Falsified by > 20** on
the plain server in any of five runs. (A reading of 24 would mean the
copies were never the retention and lobo#28's measurement is not
explained by the table.)

**P4 — served bytes.** **None change.** The gauntlet's nginx
differential, parity and every corpus row compare served bytes; a
single moved row falsifies.

**P5 — the probe counts do not change.** The same probe on the
change counts the same calls (the fix removes the copies, not the
calls): `retire_zero` within ±5% of 1,807 / 1,916. Falsified if the
call counts move, which would mean the drive changed, not the table.

**P6 — the push census after.** ws37's method: **807** `.push(` sites
(406 `src/`, 401 `tests/`), **15** reaching heap storage. After this
change the 807 and the 15 are unchanged (the sites move, they do not
disappear), and the heap-reaching sites that still copy on a **plain**
push fall from **14 to 1**: the `List[AccRow]` pass record in the
serving loop, whose element is already spelled `copy` and which fires
only when an access output is configured. That one is reported, not
changed here.
