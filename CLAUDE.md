# Lobo — agent guidance

A production web server in wolf, and a flagship many-hands wolf
codebase. Named **Lobo** by the human 2026-08-29 (D64); the name
landed at wsm03 (the sprint prefixes stay `ws`/`wsm` — contract
history). NO public remote until ws16 opens the door — a private org
remote is the orchestrator's call, never a lane's.

## Read before writing a line of wolf
1. `.docs/refs/AN_AGENTS_GUIDE_TO_WRITING_GOOD_WOLF.md` — the living
   guide (canonical copy in wolf-std; sync per `.docs/refs/MANIFEST.md`).
2. `.docs/refs/API-CONVENTIONS.md` — naming/modes/docs rules.
3. Your sprint contract under the planning repo's `sprints/wws/` —
   contracts are binding; deltas go in the campaign closeout.
4. `.docs/refs/11-nginx-owned-bugs-and-the-finally-list.md` — the
   charter's evidence layer.

## Entering the repo (the ws00 ritual — do this once, in order)
1. **Toolchain**: build the pins in `wolf-toolchain.toml` (each
   section carries its build command) and stage the binaries into
   `.wolf-bin/` (gitignored): `wolf`, `libwolf_rt.a`, `lupin`.
   Resolution order everywhere: `$WOLF_BIN`/`$LUPIN_BIN` →
   `.wolf-bin/` → PATH. Every tool refuses on identity drift.
2. **Differential oracle**: build the pinned nginx once per
   `docs/DIFFERENTIAL.md` into `tests/differential/bin/`
   (gitignored). The harness refuses while it is missing — a red
   gauntlet until you do this is the designed behavior.
3. **Verify**: `tools/lobo-gauntlet` → `lobo-gauntlet: GREEN`.
Host tools the rig leans on beyond the toolchain: POSIX sh, awk, jq,
diff — plus a real OpenSSL 3.x for the TLS steps (macOS ships
LibreSSL as `openssl`; point `$OPENSSL_BIN` at e.g. Homebrew's
openssl@3 — the tools refuse a non-OpenSSL oracle by name), GNU tar
for the release archive's reproducible pack (`gtar` from Homebrew's
gnu-tar on macOS; `tools/lobo-dist` refuses bsdtar by name) and curl
for its smoke.

## Hard rules (inherited from the wolf org, binding here)
- The gauntlet (`tools/lobo-gauntlet`: toolchain pin, manifest, fmt,
  both tiers build, `.wolfi` freshness, corpus runner over every
  directive test's declared lanes with warnings denied, the nginx
  differential) is green before ANY commit.
- A commit that moves a `.wolfi` snapshot contains ONLY `.wolfi`
  files, message starting `interface(<module>): ` (root.wolfi rides
  along; `tools/lobo-interface --emit` regenerates). The gauntlet
  fails on unsynced surfaces — see `.docs/STYLE.md`.
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
  with NAMED deltas; cert layouts/flows keep working. When lobo
  behavior must differ from nginx, the delta is documented in the
  directive table and, where load-visible, linted.
- Deferrals go in `.docs/sprints/deferrals.md` (local, gitignored)
  under its two-kinds rule — named-gate or probed-and-routed; an
  unrouted entry past its wave is a process failure.
- When this repo's docs and the wolf spec disagree, the spec wins.
