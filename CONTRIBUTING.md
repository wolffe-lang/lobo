# Contributing to lobo

lobo is a web server written in [wolf](https://github.com/wolffe-lang/wolf-lang).
It reads nginx configuration files and works with the certificate tooling an
nginx site already has. A pinned, real nginx is the oracle: the differential
harness serves the same configuration and requests through both and compares
the responses.

## Rules of the codebase

- **The compatibility contract.** An nginx.conf subset either carries over or
  fails with a named difference; certificate layouts and flows keep working.
  Where lobo must behave differently from nginx, the difference is documented
  in `docs/directives.md` and, where it shows when a configuration loads,
  reported by the linter.
- **Dependencies: none.** lobo is a from-parts wolf program with no build
  scripts; the only external artifact is the pinned nginx binary the
  differential harness runs.
- **Loopback only, in every test.** The pinned nginx runs on loopback too.
- **Module boundaries are checked-in `.wolfi` interfaces.** A module's
  internals are its own; its `.wolfi` is a contract (see
  `docs/ARCHITECTURE.md`). When a change moves one, regenerate it with
  `tools/lobo-interface --emit` and commit the snapshots alone, in a commit
  whose message starts `interface(<module>): ` (`src/root.wolfi` rides along).
  Changing another module's surface is a contract change, made in its own
  commit and named as one.
- A bug or a missing feature in wolf or wolf-std is filed upstream
  ([wolf-lang](https://github.com/wolffe-lang/wolf-lang),
  [wolf-std](https://github.com/wolffe-lang/wolf-std)) with a small program
  that shows it, never silently worked around.
- When this repository's docs and the wolf language specification disagree,
  the specification wins.

## The toolchain

`wolf-toolchain.toml` pins wolf, lupin and wolf-std by commit, and the notes
above each section name the release archive and its sha256 digest for each
host. Stage them once into `.wolf-bin/` (gitignored):

1. Download the wolf and lupin release archives for your host
   (`gh release download v<version> -R wolffe-lang/wolf-lang --pattern
   'wolf-<version>-<host>.tar.gz'`, and the same from `wolffe-lang/wolf-interp`
   for lupin), check each digest, and copy `wolf`, `libwolf_rt.a`,
   `wolf-cimport-worker` (when the archive has one) and `lupin` into
   `.wolf-bin/`.
2. Put wolf-std's `std/` tree at the `[std]` rev into `.wolf-bin/std/`
   (`git archive <rev> std | tar -x -C .wolf-bin/` in a wolf-std clone) and
   write that rev into `.wolf-bin/std/STD-REV`.

Every tool resolves the toolchain from `$WOLF_BIN` and `$LUPIN_BIN`, then
`.wolf-bin/`, then `PATH`, and refuses one whose identity drifts from the pin
(`tools/lib-toolchain.sh`). A pin moves in a commit of its own, with the gate
green at the new pin and the notes saying what the move changes.

Then build the differential oracle once, from the values in
`tests/differential/NGINX-PIN`, as `docs/DIFFERENTIAL.md` describes, into
`tests/differential/bin/` (gitignored). Until it is there the gate is red by
design.

The gate also needs, beside the toolchain: POSIX sh, awk, jq, diff and curl;
nc, ApacheBench (`ab`) and python3; GNU `timeout` (on macOS, Homebrew's
coreutils on `PATH`); a real OpenSSL 3.x for the TLS steps (macOS ships
LibreSSL as `openssl`, so point `$OPENSSL_BIN` at e.g. Homebrew's openssl@3);
and GNU tar for the release archive (`gtar` from Homebrew's gnu-tar on macOS).
The tools refuse a wrong one by name.

## The gate

```sh
tools/lobo-gauntlet     # prints `lobo-gauntlet: GREEN` when every step passes
```

It checks the toolchain pin, the manifest and its capabilities, formatting,
the build on both tiers, the `.wolfi` snapshots, the directive corpus with
warnings denied, the nginx differential and the witnesses, and that nothing of
the run is left running or left in the tree. **It is green before every
commit.** `tools/lobo-dist` builds and smoke-tests a release archive.

## What a change must bring

- Tests are first class and land in the same commit as the code they cover.
- Where the behaviour is nginx's, a differential case under
  `tests/differential/` holds lobo to the pinned nginx; a difference from
  nginx is documented as above.
- A user-visible change gets an entry under the `Unreleased` heading of
  `CHANGELOG.md`.

## Commits

- Chunked and terse: an imperative subject under 250 characters, one file or
  one coherent change a commit. Stage what you mean, never `git add -A`.
- No trailers: no co-author, sign-off or "generated with" lines.

## Pull requests

Open a pull request from a branch against `trunk`. An unlabelled pull request
runs only a cheap check, so your own run of the gate is the evidence: the
description names the head you ran `tools/lobo-gauntlet` on and its `GREEN`,
and the tests and differential cases the change adds. A change to CI, `tools/`
or the toolchain pin also needs the full CI run (the linux and macOS
gauntlets) green at its head before it merges: ask for the `full-matrix` label
once the head is the one to merge, not when the pull request opens.
