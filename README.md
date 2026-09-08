# lobo

A web server written in [wolf](https://github.com/wolffe-lang/wolf-lang).
Your `nginx.conf` carries. Your certificates and their tooling keep
working.

```sh
brew install wolffe-lang/wolf/lobo     # macOS arm64
yay -S lobo-bin                        # Arch x86-64
```

Then:

```sh
mkdir -p ~/lobo && cd ~/lobo
cp -R "$(brew --prefix lobo)"/share/lobo/{conf,html} .   # or /usr/share/lobo
mkdir -p logs
lobo -c conf/lobo.conf serve      # serves html/ on 127.0.0.1:8080
lobo -s stop
```

`lobo -v` names the version **and the compiler that built it**, because
a binary that cannot say what it is cannot be debugged:

```
lobo version: lobo/0.1.0 (built with wolf 0.2.6, pin 398e5f5)
```

> **0.1.0 — early.** The core is real and tested: static serving,
> reverse proxy, TLS, ACME, prefork workers, reload with draining,
> structured logs, a control socket. It has not run anyone's
> production traffic yet. Treat it accordingly, and please file what
> breaks.

## Why another web server

nginx is excellent and twenty years old. Some of its sharpest edges
are not bugs it failed to fix — they are consequences of the language
it is written in and decisions that hardened before anyone knew
better. lobo's charter is to keep everything that made nginx worth
learning and drop the rest:

**The memory-corruption class is structural, not vigilant.** wolf has
checked arithmetic in every build profile, region-owned request
memory, and no undefined behaviour. Historical nginx CVE inputs live
in this repo's corpus; the acceptance is refuse-or-trap-clean, in CI,
forever.

**Config footguns are named at load.** The `if`-is-evil class,
inheritance surprises, alias traversal — your config still works, and
the linter tells you where nginx would have quietly hurt you.

**The drop-in claim is falsifiable.** CI runs a pinned real nginx
(1.30.4) beside lobo on the same configs and diffs the responses. The
claims ratchet; they are not hand-waved.

## What you get that nginx doesn't have

- **Built-in ACME** — certificates without the certbot dance, and the
  certbot dance still works.
- **A dry-run that exercises routing**, not just syntax:
  `lobo -t --request 'GET https://host/path'` tells you what *would*
  happen.
- **Observable reloads** — connection draining you can watch, not
  infer.
- **`-T` that says which file set every directive**, so config
  archaeology stops being archaeology.
- **Per-vhost memory budgets that are enforced**, not hoped.
- **Replayable races.** wolf's scheduler is deterministic under test,
  so a scheduling bug from a report can be replayed.

## Performance

One process went from 37 to 13,508 req/s when the serving loop learned
to block on readiness instead of time-slicing. Workers then made it a
real prefork server — the master binds the listeners and hands them
down, every worker accepts on one socket, and the kernel distributes
the work:

| workers | shape | req/s |
|---|---|---|
| 3 | connection per request | 23,663 |
| 18 | connection per request | 16,120 |
| 18 | keepalive | 38,961 |

Measured on macOS arm64 (18 cores) against the same box's pinned
nginx, which does 24,158 and 83,831 on the last two rows. **lobo is
not at parity yet** — roughly 1.5x on connection-per-request and 2.2x
on keepalive. Closing that is the current campaign, and the numbers
above will move; `docs/PARITY.md` defines what "parity" has to mean
before any of it is claimed.

## Compatibility

108 nginx directives, with every deliberate difference documented in
[`docs/directives.md`](docs/directives.md) rather than discovered in
production. Where lobo must differ, it says so at load.

Not yet: windows and linux-aarch64 builds (the compiler's native tier
does not serve those hosts yet — they refuse by name, never silently).

## Documentation

| | |
|---|---|
| [GETTING-STARTED.md](docs/GETTING-STARTED.md) | your first five minutes, start here |
| [directives.md](docs/directives.md) | every directive, and every difference from nginx |
| [WORKERS.md](docs/WORKERS.md) | prefork, descriptor handoff, distribution measurements |
| [CONTROL.md](docs/CONTROL.md) · [DRAIN.md](docs/DRAIN.md) | the control socket; reload and draining |
| [DRYRUN.md](docs/DRYRUN.md) | routing dry-runs |
| [LOGGING.md](docs/LOGGING.md) · [log-variables.md](docs/log-variables.md) | structured logs and their variables |
| [BUDGET.md](docs/BUDGET.md) | per-vhost memory budgets |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | how it is put together |
| [DIFFERENTIAL.md](docs/DIFFERENTIAL.md) · [PARITY.md](docs/PARITY.md) | the nginx oracle, and the parity bar |

## Building from source

lobo pins its toolchain by exact identity — a specific wolf compiler,
interpreter and standard library, named in `wolf-toolchain.toml`. That
is why the packages above ship a prebuilt binary: a distro's rolling
`wolf` would break the build the day it moved ahead of the pin.

To build anyway, stage the pinned toolchain into `.wolf-bin/` and the
pinned nginx into `tests/differential/bin/` (each section of
`wolf-toolchain.toml` and `docs/DIFFERENTIAL.md` carry their build
commands), then:

```sh
tools/lobo-gauntlet     # the full gate: build, both tiers, corpus, differential
tools/lobo-dist         # a release archive, packed reproducibly and smoke-tested
```

Every release archive carries a `BUILD` file recording the toolchain,
the source commit and the pins it was built from.

## License

[GPL-3.0-or-later](LICENSE).
