# lobo

A web server written in [wolf](https://github.com/wolffe-lang/wolf-lang).
It reads nginx configuration files and works with the certificate
tooling you already have.

```sh
brew install wolffe-lang/wolf/lobo     # macOS arm64
yay -S lobo-bin                        # Arch x86-64
```

To serve the stock page:

```sh
mkdir -p ~/lobo && cd ~/lobo
cp -R "$(brew --prefix lobo)"/share/lobo/{conf,html} .   # or /usr/share/lobo
mkdir -p logs
lobo -c conf/lobo.conf serve      # serves html/ on 127.0.0.1:8080
lobo -s stop -c conf/lobo.conf
```

`lobo -v` prints the version and the compiler that built it:

```
lobo version: lobo/0.1.2 (built with wolf 0.2.23, pin 8edac3e)
```

> **Version 0.1.2.** Static serving, reverse proxy, TLS, ACME, prefork
> workers, reload with connection draining, structured logs and a
> control socket all work and are tested. It has not carried anyone's
> production traffic. Please file what breaks.

## Why another web server

nginx is excellent and twenty years old. Some of its sharpest edges
come from the language it is written in, and some from decisions that
hardened before anyone knew better. lobo keeps the configuration
format and the operational habits that made nginx worth learning, and
changes the parts underneath.

Memory safety is a property of the language. wolf checks arithmetic in
every build profile, ties request memory to regions, and has no
undefined behaviour. The historical nginx CVE inputs are in this
repository's test corpus, and CI requires each one to be refused or to
trap cleanly.

Configuration mistakes are reported when the file loads. The `if`
directive, directive inheritance and alias traversal all carry over
from nginx, and the linter points out the places where nginx would have
failed quietly.

The compatibility claim is tested. CI runs a pinned copy of nginx
1.30.4 next to lobo with the same configuration files and compares the
responses.

## What lobo adds

- ACME is built in, so certificates can be issued and renewed without
  certbot. certbot still works if you prefer it.
- `lobo -t --request 'GET https://host/path'` dry-runs a request through
  the routing rules and reports what would happen.
- Reloads expose their connection draining, so you can watch a reload
  finish instead of guessing.
- `-T` reports which file set every directive.
- Per-vhost memory budgets are enforced.
- wolf's scheduler is deterministic under test, so a race reported from
  the field can be replayed.

## Performance

One process went from 37 to 13,508 req/s when the serving loop switched
from time-slicing to blocking on readiness. Prefork workers came after:
the master binds the listeners and passes them to each worker, every
worker accepts on the same socket, and the kernel distributes the
connections.

lobo is within ten percent of nginx on macOS and not yet on linux.
[`docs/PARITY.md`](docs/PARITY.md) defines the comparison (it was
written before the first measurement) as the ratio nginx ÷ lobo on one
machine, with workers equal to cpus and 32 concurrent clients, over
five interleaved runs; 1.10 or under is parity. The current ledger
(nginx 1.30.4; the macOS row re-taken with wolf 0.2.20, the linux rows
with wolf 0.2.25):

| host | measured | connection-per-request | keepalive |
|---|---|---|---|
| macOS arm64, 18 cpus (load 2.80, other work on the box) | 2026-10-02 | 1.031x | 1.037x |
| linux x86-64, 4 cpus (GitHub Actions runner, load 1.85, a slow VM) | 2026-10-09 | 1.140x | 1.260x |
| linux x86-64, 4 cpus (GitHub Actions runner, load 1.87, a fast VM) | 2026-10-08 | 1.166x | 1.185x |
| linux x86-64, 16 cpus (kasumi, load 0.34–1.89, shared) | 2026-10-02 | no valid set: ~1.84x | no valid set: ~2.04x |

The two runner rows are two VMs a day apart (the first is ws54's head,
the second trunk's source before it); the runner's speed differs from
VM to VM by up to 2.3x, so ratios compare only within one row. At one
worker the runner reads 1.00–1.05x on connection-per-request and
1.09–1.18x on keepalive. Where the remaining linux gap goes — lobo's
own user space, a fifth of a request, much of it the runtime's string
allocation, and the herd's extra wakeups on connection-per-request — is
[`docs/PROFILE.md`](docs/PROFILE.md)'s ws54 addendum.

The kasumi row is indicative: all three sets were refused because
nginx's own five runs spread more than the definition allows. At one
worker kasumi reads about 1.17x and 1.20x, close to the runner; on kasumi the
gap is the sixteen-worker cell's, and
[`docs/PROFILE.md`](docs/PROFILE.md) has why. The earlier rows are kept
as history:

| host | measured | wolf | connection-per-request | keepalive |
|---|---|---|---|---|
| linux x86-64, 4 cpus (GitHub Actions runner) | 2026-10-07 | 0.2.25 | 1.208x | 1.239x |
| linux x86-64, 4 cpus (GitHub Actions runner) | 2026-10-07 | 0.2.24 | 1.151x | 1.255x |
| linux x86-64, 4 cpus (GitHub Actions runner) | 2026-10-02 | 0.2.20 | 1.151x | 1.240x |
| macOS arm64, 18 cpus | 2026-09-09 | 0.2.8 | 1.033x | 1.072x |
| linux x86-64, 4 cpus (GitHub Actions runner) | 2026-09-11 | 0.2.11 | 1.197x | 1.263x |

On linux, `listen … reuseport` took the connection-per-request ratio
to 1.089x against 1.138x without it on the same VM (2026-09-11); the
tables keep lobo's default. The runner's speed differs from VM to VM,
so ratios compare only within one ledger entry.

The 110.9x linux keepalive figure this page gave for 0.1.0 was a
delayed-ACK stall on lobo's two-write response, fixed in 0.1.1.

[`docs/PROFILE.md`](docs/PROFILE.md) has where the time goes. Its
first profile (2026-09-08, macOS arm64, 0.1.0's source built with wolf
0.2.6, pin 398e5f5) measured 63 µs per keepalive request against
nginx's 19; the addenda after it follow each change since, on both
hosts.

## Compatibility

[`docs/directives.md`](docs/directives.md) has a row for each of 122 nginx directives: 48 implemented, 49 planned and 25 refused by name when the configuration loads.
<!-- the sentence above is derived from src/config/table.lu by tools/lobo-directives (--emit rewrites it, --check reds on drift); keep it on one line --> It lists every place lobo's behaviour
differs from nginx's, and where it differs, lobo says so when the
configuration loads.

Windows and linux-aarch64 builds do not exist yet. wolf's release
tier refuses windows by name, and its native code generator does not
serve linux aarch64.

## Limits

- **Downloads beside the loop.** A large plaintext body is written by
  its own proc beside the loop, and a download parked on a slow client
  holds workers in wolf's runtime pool. Under `memory_budget` a small
  body runs in a capped proc while fewer than `3·max(cpus, 2) - 2`
  downloads are parked: 4 on 1 cpu, 10 on 4, 46 on 16. Past that it
  is written without the proc, and the budget still rules it. Built
  with wolf 0.2.24 that proc was measured to run beside up to
  `4·max(cpus, 2) - 2` downloads (6, 14 and 62), so the room leaves a
  quarter in hand. Past `4·max(cpus, 2) - 1` parked downloads a new
  one gets its head and its body waits for a worker. lobo 0.1.2, built
  with wolf 0.2.23, wrote the small body without its proc from
  `cpus / 2 - 2` downloads on (wolf-lang#570, fixed in 0.2.24).
- A range starting at byte N reads and drops N bytes first. Under
  `memory_budget` a `Range` is ignored. An `If-Range` date in RFC 850
  or asctime form is not parsed.
- Known issues: a relative `root` or `alias` resolves against the
  start folder, not `-p` (lobo#55); an exact location aliased to a
  file answers 404 (lobo#48); `-t -q` still prints (lobo#49); a reload
  ignores a changed `worker_shutdown_timeout` (lobo#50); a finished
  drain's count leaves `/metrics` with its generation (lobo#51); on
  macOS, which has no `/proc`, `user` is refused where nginx warns and
  loads (lobo#52).

## Documentation

| | |
|---|---|
| [GETTING-STARTED.md](docs/GETTING-STARTED.md) | start here |
| [directives.md](docs/directives.md) | every directive, and every difference from nginx |
| [WORKERS.md](docs/WORKERS.md) | prefork, descriptor handoff, distribution measurements |
| [CONTROL.md](docs/CONTROL.md) · [DRAIN.md](docs/DRAIN.md) | the control socket; reload and draining |
| [DRYRUN.md](docs/DRYRUN.md) | routing dry-runs |
| [LOGGING.md](docs/LOGGING.md) · [log-variables.md](docs/log-variables.md) | structured logs and their variables |
| [BUDGET.md](docs/BUDGET.md) | per-vhost memory budgets |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | how it is put together |
| [DIFFERENTIAL.md](docs/DIFFERENTIAL.md) · [PARITY.md](docs/PARITY.md) | the nginx comparison, and the parity definition |

## Building from source

`wolf-toolchain.toml` pins an exact wolf compiler, interpreter and
standard library, and the build refuses any other. That is why the
packages above are prebuilt: a distribution's `wolf` package moves
ahead of the pin, and a source package depending on it would stop
building at that point.

To build anyway, put the pinned toolchain in `.wolf-bin/` and the
pinned nginx in `tests/differential/bin/` (the build commands are in
`wolf-toolchain.toml` and `docs/DIFFERENTIAL.md`), then run:

```sh
tools/lobo-gauntlet     # build, both tiers, corpus, differential
tools/lobo-dist         # a release archive, packed reproducibly and smoke-tested
```

Each release archive includes a `BUILD` file with the toolchain, source
commit and pins it was built from.

## License

[GPL-3.0-or-later](LICENSE). The
[wolf Training Data Permission](LICENSE-TRAINING-DATA) lets you train
models on this repository's text and ship excerpts of it in datasets
under CC BY 4.0.
