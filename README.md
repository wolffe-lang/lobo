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
lobo -s stop
```

`lobo -v` prints the version and the compiler that built it:

```
lobo version: lobo/0.1.0 (built with wolf 0.2.6, pin 398e5f5)
```

> **Version 0.1.0.** Static serving, reverse proxy, TLS, ACME, prefork
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

lobo is slower than nginx, and on linux it is much slower on keepalive
traffic. [`docs/PARITY.md`](docs/PARITY.md) defines the comparison (it
was written before the first measurement) as the ratio nginx ÷ lobo on
one machine, with workers equal to cpus, over five interleaved runs:

| host | connection-per-request | keepalive |
|---|---|---|
| macOS arm64, 18 cpus | 1.15x | 2.76x |
| linux x86-64, 4 cpus | 2.27x | 110.9x |

The linux keepalive figure is a stall. lobo answers about one request
every 41 ms per connection because the kernel's 40 ms delayed ACK
interacts with Nagle's algorithm on lobo's two-write response. macOS
does not show it, which is how 0.1.0 shipped with it. A single-buffer
write removes it and is the next change.

[`docs/PROFILE.md`](docs/PROFILE.md) has the rest: 63 µs per request
against nginx's 19 on the same machine, with about half of the
difference spent in the runtime parking on its reactor thread before
syscalls on sockets that were already ready. That part is the
language's, and is filed upstream.

## Compatibility

108 nginx directives are supported. [`docs/directives.md`](docs/directives.md)
lists each one and every place lobo's behaviour differs from nginx's.
Where it differs, lobo says so when the configuration loads.

Windows and linux-aarch64 builds do not exist yet, because the
compiler's native code generator does not serve those hosts. On those
hosts the compiler refuses and names the reason.

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

[GPL-3.0-or-later](LICENSE).
