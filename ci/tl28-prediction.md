# tl28 — the prediction, before the first change (ruling #92)

Written before any tl28 change to this repository is committed, against
trunk `9a4723c`.

**Before** (the ten completed push/pull_request runs of `ci` up to
39174295177): two jobs a run, the linux gauntlet (18 to 22 minutes) and the
macOS gauntlet (18 to 26, a 90-minute ceiling); **41.9 job-minutes** a run
(median 43.2) and **26.2 minutes of wall** (median; max 49.1, queueing on
the org's five macOS slots).

**After, predicted:**

1. A pull-request push is `tier pr`: the plan (under 1 job-minute, the
   planner's test inside it), `gauntlet` (18 to 22) and the verdict (under
   1): **19 to 24 job-minutes, about 20 minutes of wall**, the macOS
   gauntlet skipped: about half the job-minutes, and no macOS slot taken.
2. A notes-only pull request (the lanes' contracts and evidence) is
   `tier noop`.
3. The `full-matrix` label at the head is `tier full`: both gauntlets,
   **about 43 job-minutes and 26 of wall**, as before.
4. A dispatch with `-f tier=pr` of a branch that adds a path no rule names
   comes out `tier full`. A dispatch with parity, profile or syscalls is
   `tier measure`, the linux job alone, as before.
5. The planted break (an unmapped path classified pr in `ci/tiers.py`) reds
   the plan job at "the planner can say no", skips both gauntlets, and the
   verdict job, `tier unplanned`, is red: **1 to 2 job-minutes**.
