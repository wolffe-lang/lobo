# ws37 — the prediction, committed before the bump

Wave 46, subwave 3. Written 2026-09-24 on lobo trunk `c279138`, with
`.wolf-bin` still holding the **0.2.14 / 0.1.36** pair. Nothing below
has been measured at the new pair; every number carries the artifact
that would falsify it. The measurements land in the ws37 CHANGELOG
entry beside these lines, right or wrong.

## §2 first — what the contract said, and what origin says

Re-derived against origin the day this file was written.

| input, as the contract states it | what origin says |
|---|---|
| lobo trunk `c279138` | **holds** — `c2791383c595ba536f10fa255ccdffa92bfe9006` |
| pins wolf 0.2.14 (`30731a6`) / lupin 0.1.36 (`6e94436`) | **holds** at `origin/trunk:wolf-toolchain.toml` lines 110/139 |
| wolf 0.2.16 = tag `v0.2.16` = `93a5fe50`, four assets | **holds** — annotated tag `014dc68c` derefs to `93a5fe504593ca7642b78ba83b4986e7a03cfe71`; release 395302343, `isDraft:false`, four assets whose digests begin `b0431056` / `fe1966a4` / `f984c7a7` / `84e30c05` |
| lupin 0.1.38 = `ba357aa`, five assets, pinned on the released line | **holds** — tag `a9f07425` derefs to `ba357aa6a2e32040d4f089d2cefe05bab86c4f86`; release 393623352, five assets; `2e4ca769` is 148 commits behind `93a5fe50` on the same line |
| lobo#20, #23, #24 already CLOSED | **holds** — and so is every other lobo issue |
| "the 12 `push` sites under #385" (wave-45), orchestrator's grep "0" | **BOTH WRONG — see below** |
| lobo's `ci.yml` has the token-absent green-skip shape | **holds** — `.github/workflows/ci.yml` lines 97–115 |

**The push count is the drift that matters.** `origin/trunk` carries
**807** `.push(` call sites — 406 under `src/`, 401 under `tests/`,
0 under `tools/` — on 807 distinct lines, and **zero** of them spell
`push(take …)`. The wave-45 figure of 12 appears nowhere in lobo:
`grep -n 385 CHANGELOG.md` returns two line-number coincidences and no
mention of wolf-lang#385 at all. The orchestrator's `0` is the seventh
false-signal shape — lobo's sources are `.lu`, and a grep scoped to
the usual source extensions cannot reach them. A third reading, also
stale: the checkout at `~/GithubOrgs/wolffe-lang/lobo` on the planning
host sits at `9a4a9051`, a ws27-era commit whose `wolf-toolchain.toml`
still pins **0.2.9 / 0.1.29**; a census taken there would have been
wrong in a fourth direction.

**807 is not the interesting number and this lane does not pretend it
is.** `[mem.region.edge.elem]` at `93a5fe50` prices the change exactly:
a plain push costs "nothing at all for a scalar, a `str`, or a struct
of them", and one allocation per list or map reached, plus a byte copy
of its buffer, for an element that reaches heap storage. So the census
that decides anything is **how many push sites push an element that
reaches heap storage**, and that is what §3 predicts.

## §3 The predictions

**P1 — the heap-reaching push census.** Of the 406 `.push(` sites in
`src/`, **at most 12** push an element that reaches heap storage (a
`List`, a `Map`, or a struct or tuple containing one) and therefore
become a real deep copy at 0.2.16. **Falsified by 13 or more.**

**P2 — the hot path.** **Zero** of those heap-reaching sites lie on
the per-request serving path — the functions `lobo-profile`'s close and
keepalive shapes walk per request in `src/serve/`, `src/http/`,
`src/conn/` and `src/proxy/`. Every push there pushes a byte, an int,
a `str` or a struct of them, all of which the clause prices at nothing.
**Falsified by one site on that path**, in which case the cost is
measured with `tools/lobo-parity` and `tools/lobo-syscalls` at the
bar's own cell and not shrugged at.

**P3 — `[conf.exit]` moves no gauntlet row.** The clause makes a
*rejection* 2 and a *refusal* 4 at a **front door**. `tools/lobo-corpus`
drives `wolf conform-run` and `lupin conform-run --json`, which
`[conf.exit]` names as **not** a front door — the outcome is the
record's and the tool still exits 0 (`[proto.invoke.exit]`). lobo's
only two `run(exit=1)` fences, `tests/rig/deadline_timeout.lu` and
`tests/rig/refused_row.lu`, are programs that **compile and run** and
ride an error out of `main` with `?`: the passthrough class, whose
status is the program's own answer and is unchanged. So **zero rows
move**, and the wave's "any gauntlet row that asserted exit 1 on a
rejection was green by accident" is a hazard lobo does not carry.
**Falsified by any row going red with an observed exit of 2 or 4**, or
by any front-door invocation in `tools/` that tests a non-zero status
for equality with 1.

**P4 — `move` on a `Copy` place.** s177 / wolf-lang#444 makes the
compiler record a move for a `Copy`-typed place, so a program that
moves one and reads it afterwards now refuses with E1001. lobo has
**zero** such sites and the bump produces **no new refusal** from it.
**Falsified by one E1001 at the new pair.**

**P5 — the gauntlet at the new pair.** Source motion for the pin's own
sake is the documented ritual and nothing else: the **13** `.wolfi`
toolchain stamps and the **two** `src/shell/shell.lu` constants (lines
100 and 105). Beyond that, **at most 2 red rows** in the first full
gauntlet at 0.2.16 / 0.1.38. **Falsified by 3 or more**, or by any
source change outside those 15 lines and `wolf-toolchain.toml`.

**P6 — the CI green-skip, before it is fixed.** With `WOLF_CI_TOKEN`
absent the `gauntlet` job reports **success in under 60 seconds**,
having run the checkout, the pin read and the acquire step and
**nothing else** — no build, no `lobo-gauntlet`, no oracle. Every
lobo CI run since 2026-09-14 has taken 6–8 minutes (35670790352:
00:10:00Z → 00:17:48Z), so the tell is the duration. **Falsified by a
red, or by a run over 60 seconds, or by any toolchain step appearing
in the run's step list.**

## What this lane will NOT change

wolf-lang#438's index-store ruling is **with the maintainer**. lobo's
index stores are counted and reported here; not one is rewritten.
