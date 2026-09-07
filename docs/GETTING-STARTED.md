# Getting started

You have a `lobo-<version>-<host>` directory, unpacked from a release
archive. This page is the whole learner path: the same commands the
release's own CI runs against the same archive on a clean machine
before the release is published (`.github/workflows/release.yml`,
the learner smoke). If a line here does not do what it says, that is
a bug in the release, not in you — file it.

## What is in the box

```
lobo                  the server, one static binary (nothing to install)
conf/lobo.conf        the stock config: serves html/ on 127.0.0.1:8080
html/index.html       the page it serves
logs/                 where the pid file, the control socket and the logs go
BUILD                 provenance: what -v prints, the toolchain pins, the host,
                      the source commit, the timestamp every file carries
GETTING-STARTED.md    this page
README.md             what lobo is for
CHANGELOG.md          every release, newest first
docs/                 the contracts: directives.md, CONTROL.md, DRAIN.md,
                      DRYRUN.md, LOGGING.md, WORKERS.md, BUDGET.md, …
LICENSE               GPL-3.0
```

## The first five minutes

Run everything from the archive directory: the config's paths are
relative to it (`-p .` is the default prefix, as nginx's is).

```sh
./lobo -v
```

prints the version **and the toolchain it was built with** — the
`pin` is the wolf compiler's commit, and `BUILD` beside the binary
records the same line:

```
lobo version: lobo/0.1.0 (built with wolf 0.2.6, pin 398e5f5)
```

`./lobo -V` adds the standard-library pin, the tier and the module
set, one fact per line, nginx's shape. A build that is not a release
says so: `lobo/0.1.0+dev`.

```sh
./lobo -t -c conf/lobo.conf
```

tests the config. nginx's `-t` checks syntax; lobo's also resolves
every `root`, `listen` and `include`, and can dry-run a request
against the routing (`-t --request 'GET http://localhost/'` —
docs/DRYRUN.md). Then:

```sh
./lobo -c conf/lobo.conf serve
```

serves in the foreground. In another shell:

```sh
curl -i http://127.0.0.1:8080/
```

answers `200`, `Server: lobo/0.1.0`, and the bytes of
`html/index.html`. Edit `conf/lobo.conf` — it is an `nginx.conf`, and
docs/directives.md is the table of what carries and what does not —
then:

```sh
./lobo -s reload -c conf/lobo.conf     # loads the new config; connections drain, none drop
./lobo status -c conf/lobo.conf        # the generations, the drain, the workers
./lobo -s stop -c conf/lobo.conf       # stops it
```

`-s` talks to the running server over the control endpoint the config
names (`control unix:logs/control.sock;` — a socket in a directory you
own, so file permissions are the boundary; docs/CONTROL.md). There is
no pid to `kill`: at this pin the pid file records the endpoint.

## Reaching the network

The stock config binds loopback on purpose. To serve a network,
change `listen 127.0.0.1:8080;` to `listen 80;` (every interface, as
nginx does), point `root` somewhere real, and run `-t` again. TLS is
`ssl_certificate`/`ssl_certificate_key` exactly as in nginx — or
`cert auto` for built-in ACME (docs/directives.md, `cert`). Your
certbot layout keeps working; docs/DIFFERENTIAL.md is the harness
that proves it against a pinned real nginx on every commit.

## Which hosts

The release archives are wolf's **release tier**: `x86_64-unknown-linux-gnu`
and `aarch64-apple-darwin`. **Windows x86-64 and linux aarch64 have no
archive** — wolf's LLVM release tier does not serve them until s60c
upstream, and lobo refuses to build one rather than ship a binary that
will not run. That is a named gap, not an oversight; it closes when
the tier does.

## Building from source

`wolf-toolchain.toml` at the repository root pins the exact wolf,
lupin and wolf-std the release was built with, and carries the build
command for each. `tools/lobo-dist` rebuilds this archive from those
pins and refuses any other toolchain by name; `tools/lobo-gauntlet` is
the gate every commit passes. A binary built any other way is a
different binary, and `-v` can only name the toolchain the pin file
names — the reason is wolf-lang#247.
