# wolf-wws — agent guidance

A production web server in wolf, and a flagship many-hands wolf
codebase. Working name; NO public remote until the human names it —
never create one.

## Read before writing a line of wolf
1. `.docs/refs/AN_AGENTS_GUIDE_TO_WRITING_GOOD_WOLF.md` — the living
   guide (canonical copy in wolf-std; sync per `.docs/refs/MANIFEST.md`).
2. `.docs/refs/API-CONVENTIONS.md` — naming/modes/docs rules.
3. Your sprint contract under the planning repo's `sprints/wws/` —
   contracts are binding; deltas go in the campaign closeout.
4. `.docs/refs/11-nginx-owned-bugs-and-the-finally-list.md` — the
   charter's evidence layer.

## Hard rules (inherited from the wolf org, binding here)
- The gauntlet (`wws-gauntlet`, once ws00 lands: fmt, both tiers
  build, tests, corpus runner) is green before ANY commit.
- Tests are first-class and land in the same commit as the code.
- **Loopback only, in every test, forever.** The differential
  harness's pinned nginx runs on loopback too.
- Module boundaries are `.wolfi` interfaces, checked in. Editing
  another module's `.wolfi` is a cross-lane contract change: its own
  commit, named as such. Your module's internals are yours.
- Language potholes are FILED upstream (wolf-lang/wolf-std issues),
  never silently worked around. This track is upstream's best
  bug-finder; that is half its job.
- Commits: chunked, terse imperative, <250 chars, never coauthor or
  generated-with trailers, never `git add -A`.
- No build scripts (D33). Dependencies: none — this is a from-parts
  wolf program; the only external artifact is the PINNED nginx
  binary the differential harness vendors.
- The compat contract is sacred: nginx.conf subsets CARRY or fail
  with NAMED deltas; cert layouts/flows keep working. When wws
  behavior must differ from nginx, the delta is documented in the
  directive table and, where load-visible, linted.
- Deferrals go in `.docs/sprints/deferrals.md` (local, gitignored)
  under its two-kinds rule — named-gate or probed-and-routed; an
  unrouted entry past its wave is a process failure.
- When this repo's docs and the wolf spec disagree, the spec wins.
