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
lobo version: lobo/0.1.4 (built with wolf 0.2.29, pin 6ffe7c6)
```

> **Version 0.1.4.** Static serving, reverse proxy, TLS, ACME, prefork
> workers, reload with connection draining, structured logs and a
> control socket all work and are tested. It has not carried anyone's
> production traffic. Please file what breaks.
>
> **Upgrade from 0.1.3 or earlier.** Two faults a client or operator
> could trip are fixed in 0.1.4, both measured on the released
> binaries: a process at its descriptor limit could be ended by a
> client (0.1.2 and 0.1.3), and a master with `worker_processes` above
> 1 and no `control` directive spun a cpu and ignored HUP and TERM
> (0.1.1 to 0.1.3). 0.1.4 also applies `worker_connections` for the
> first time — **a site that served more than about 510 connections a
> process must set it** (the stock config's 1024 gives about 1,022).
> [`CHANGELOG.md`](CHANGELOG.md) has the upgrade steps and the affected
> versions.

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

lobo is within ten percent of nginx on macOS (measured 2026-10-02)
and on linux (2026-10-11, four runner VMs): both shapes are inside
the line there, and on keepalive lobo answers more requests than
nginx does.
[`docs/PARITY.md`](docs/PARITY.md) defines the comparison (it was
written before the first measurement) as the ratio nginx ÷ lobo on one
machine, with workers equal to cpus and 32 concurrent clients, over
five interleaved runs; 1.10 or under is parity. The current ledger
(nginx 1.30.4; the macOS row re-taken with wolf 0.2.20, the first five
linux rows with wolf 0.2.27, the four below them with 0.2.26, the two
below those with 0.2.25):

| host | measured | connection-per-request | keepalive |
|---|---|---|---|
| macOS arm64, 18 cpus (load 2.80, other work on the box) | 2026-10-02 | 1.031x | 1.037x |
| linux x86-64, 4 cpus (GitHub Actions runner, load 1.78; 0.1.3's tree, 0.1.2's beside it read 1.132x and 1.161x) | 2026-10-11 | 1.020x | 0.921x |
| linux x86-64, 4 cpus (GitHub Actions runner, load 1.83) | 2026-10-11 | 1.022x | 0.918x |
| linux x86-64, 4 cpus (GitHub Actions runner, load 1.77) | 2026-10-11 | 1.031x | 0.934x |
| linux x86-64, 4 cpus (GitHub Actions runner, load 1.64) | 2026-10-11 | 1.038x | 0.927x |
| linux x86-64, 4 cpus (GitHub Actions runner, load 1.58) | 2026-10-11 | 1.027x | 0.914x |
| linux x86-64, 4 cpus (GitHub Actions runner, load 1.82, a fast VM) | 2026-10-10 | 1.104x | 1.130x |
| linux x86-64, 4 cpus (GitHub Actions runner, load 1.91) | 2026-10-10 | 1.062x | 1.082x |
| linux x86-64, 4 cpus (GitHub Actions runner, load 1.68, a slow VM) | 2026-10-10 | 1.075x | 1.111x |
| linux x86-64, 4 cpus (GitHub Actions runner, load 1.72, a slow VM) | 2026-10-09 | 1.153x | 1.254x |
| linux x86-64, 4 cpus (GitHub Actions runner, load 1.85, a slow VM) | 2026-10-09 | 1.140x | 1.260x |
| linux x86-64, 4 cpus (GitHub Actions runner, load 1.87, a fast VM) | 2026-10-08 | 1.166x | 1.185x |
| linux x86-64, 16 cpus (kasumi, load 0.34–1.89, shared) | 2026-10-02 | no valid set: ~1.84x | no valid set: ~2.04x |

The first runner row is the 0.1.3 release tree with 0.1.2's tree
built beside it on the same VM: 0.1.3 answered 1.099x the requests
0.1.2 did with a connection per request and 1.261x on keepalive.

The four runner rows under it are ws58, on four VMs, with wolf 0.2.27: a
small static file's bytes are kept and proved by one `stat` a request
(the file is seen changed, replaced, deleted or made unreadable on
the next request), where lobo and nginx each made four file calls.
Both shapes are inside ten percent on all four, and on keepalive
nginx is the slower of the two; two workers read 0.96x and
0.82x–0.84x, one worker 0.70x–0.72x and 0.81x–0.89x. The pin alone,
before the memo, read 1.06x–1.08x and 1.09x–1.11x on the same VMs.

The three runner rows under them are ws57, on three VMs: a serving lobo
no longer keeps the memory a request or a connection used (it kept
2 KB and 10 KB, and the kernel's page faults for them were most of
the gap), measured 5 to 10 % faster than the tree before it on each
VM. The connection-per-request shape is inside ten percent on two of
the three and keepalive on one. The three
runner rows under them are three more VMs (the first is ws55's pin at wolf
0.2.26, which measured 1.001x / 0.999x against the 0.2.25 tree beside
it; the second ws54's head; the third trunk's source before it); the runner's speed differs from
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

[`docs/directives.md`](docs/directives.md) has a row for each of 122 nginx directives: 50 implemented, 47 planned and 25 refused by name when the configuration loads.
<!-- the sentence above is derived from src/config/table.lu by tools/lobo-directives (--emit rewrites it, --check reds on drift); keep it on one line --> It lists every place lobo's behaviour
differs from nginx's, and where it differs, lobo says so when the
configuration loads.

Windows and linux-aarch64 builds do not exist yet. wolf's release
tier refuses windows by name, and its native code generator does not
serve linux aarch64.

## Limits

- **Connections.** `worker_connections` (default 512, nginx's) is
  the most connections one process holds, counting its listening
  sockets and one more, as nginx counts them: with one `listen` a
  process serves 510 clients at once, and `worker_processes 4` serves
  four times that. Past it lobo does what nginx does. Idle
  connections (one that has sent nothing yet, or a keep-alive
  connection between requests) are closed to make room, least
  recently used first, an eighth of them at a time, and the log says
  `[warn] 512 worker_connections are not enough, reusing connections`
  at most once a second. With none idle, the new connection is
  accepted and closed at once, and the log says `[alert] 512
  worker_connections are not enough`, one line each. Upstream
  connections count as nginx counts them: a proxied request is two
  connections while its exchange is out. A TLS connection while it is
  served is not counted (`docs/directives.md`). Through 0.1.3 the
  directive was parsed and ignored.
- **Descriptors.** An idle connection holds one descriptor; a
  download parked on a slow client holds two (its socket and its
  file), two threads and about 150 KB resident. A process holds about
  20 at rest, two of them in reserve. Set the limit where lobo is
  started (`ulimit -n`, systemd's `LimitNOFILE=`); lobo cannot set it
  (`worker_rlimit_nofile` is refused by name), and warns at start,
  `[warn] 512 worker_connections exceed open file resource limit:
  256`, when the limit is lower than the connections it may be asked
  to hold. With downloads, plan two descriptors a connection: 512
  connections that are all slow downloads need about 1,050. Out of
  descriptors lobo does what nginx does:
  - it stops accepting for half a second at a time and logs `[crit]
    accept() failed (24: Too many open files)` each time, so about
    two lines a second however many clients wait. On linux they wait
    in the kernel's queue and are served when descriptors return;
    macOS drops a connection whose accept failed, one each half
    second, and the rest wait. Nothing is restarted;
  - a request whose file cannot be opened is answered 500 (never 404)
    and logged, `[crit] open() "<path>" failed (24: Too many open
    files)`;
  - the control endpoint still answers. lobo lets one reserved
    descriptor go for the order's connection, and the other while a
    `reload` or `reopen` reads and opens files, and takes them back.
    `lobo status`, `-s reload` and `-s stop` work with the process at
    its limit.
  Built with wolf 0.2.31 or later (trunk), a process started with too
  few descriptors for the runtime's own (its readiness set and signal
  hub, made before lobo's first line) does not start: one line on stderr, `wolf: the runtime could
  not make its signal hub (Too many open files (os error 24)); the
  program did not start` (or `… its readiness set …`), and exit 71.
  Measured on linux: `ulimit -n` 4 to 8 gives that line; 9 to 11
  lobo's own `[emerg]` (a socket or the pid file it cannot open) and
  exit 1; from 12 it serves.
  Through 0.1.3 a process out of descriptors logged nothing, did not
  answer `lobo status`, and kept most of a core busy while it waited; and if
  the first download ever to wait on a slow client came with the
  process already at its limit, the process ended.
- **Threads.** A large plaintext body is written by its own proc
  beside the loop. Past the host's thread limit a download gets its
  head and its body waits for an earlier one to end; wolf's runtime
  writes one line to stderr and nothing stops. Measured at 300 tasks:
  145 of 200 downloads served, other requests answered. Built with
  wolf 0.2.29 nothing else limits how many downloads are parked: 900
  in one process were all being served (with `worker_connections`
  raised to hold them).
  Built with wolf 0.2.24 to 0.2.28 (lobo 0.1.2 and 0.1.3) a process
  served at most `4·max(cpus, 2) - 1` parked downloads, 15 on 4 cpus;
  the next got its head and its body waited.
  Under `memory_budget` a small body runs in a capped proc while fewer
  than `3·max(cpus, 2) - 2` downloads are parked: 4 on 1 cpu, 10 on 4,
  46 on 16. Past that it is written without the proc, and the budget
  still rules it. That margin was sized a quarter under the old limit
  and is kept as lobo's own: it is what keeps the loop out of a proc's
  join on a host that has run out of threads.
- **Kept files.** A regular file of at most 32 KiB that has not
  changed for three seconds is answered from bytes lobo keeps, after
  one `stat` that must match the file's device, inode, size and both
  times (plaintext, no `Range`, no `memory_budget`; everything else
  is read per request as before). Three things it leans on: the
  filesystem's clock and this host's are one clock (a network
  filesystem more than three seconds ahead is not), the filesystem
  keeps a status-change time, and files are published by writing
  beside them and renaming: one being rewritten through a shared
  `mmap` can be answered from bytes as old as the kernel's writeback
  interval.
- A range starting at byte N reads and drops N bytes first. Under
  `memory_budget` a `Range` is ignored. An `If-Range` date in RFC 850
  or asctime form is not parsed.
- **A proxied request is an exchange beside the loop.** Since ws67
  (lobo#81; through 0.1.4 `proxy_pass` asked the upstream inside the
  serving loop, so one silent upstream held every other client of
  that process for `proxy_read_timeout`) each exchange runs in a proc
  of its own and reports when it is done: a silent upstream holds its
  own request and nothing else, and `-s stop` is obeyed at once. What
  it costs: about four descriptors and a thread while an exchange is
  out, and on kasumi about half 0.1.4's proxied requests a second
  against a prompt upstream (one client in turn: 0.48x; `ab -c 32`:
  0.44-0.57x) — a proc and a loopback job socket per exchange. A
  client that closes while its exchange waits ends it at once, as
  nginx's does (since ws68, lobo#99), except behind an `https`
  upstream, whose wait is the TLS client's and lasts until
  `proxy_read_timeout`.
- **Memory.** Built with wolf 0.2.28 or 0.2.29 a serving lobo is flat
  over requests and connections (0 KB over 4,000 keepalive requests
  and over 2,000 connections in the gate), and so is a master supervising
  idle workers (it grew about 260 KB a minute through 0.1.3). Under
  `memory_budget` the runtime keeps one word for each finished
  response proc (wolf-lang#671).
- **Several server blocks.** Every `server` serves (through 0.1.3
  only the first did), chosen by the address a connection arrived on
  and its host's `server_name`. Still read from the first server
  only: `client_max_body_size`, `large_client_header_buffers`,
  `memory_budget`, `tcp_nodelay`, `access_log` and `metrics` (`-t`
  warns when a later server sets one). A `server_name` regular
  expression never matches. A reload re-routes among the addresses
  bound at start and opens no new one.
- **An idle lobo is not quiet.** A master and four workers with no
  client make about 2,100 system calls a second built with wolf
  0.2.29 (about 1,550 with 0.2.28), where nginx makes 23: each
  process's wait for a signal reads its pipe every 5 ms
  (wolf-lang#710).
- **No binary swap.** `-s reload` re-reads the configuration and
  keeps the running binary; a new lobo is installed by stopping the
  old one and starting the new.
- Known issues: the serving loop can stop accepting its control
  socket after a burst of closes on a loaded host (lobo#72, seen
  once, not located); lobo spends about 2,300 more user instructions
  a request than nginx (lobo#68). The issues 0.1.2 listed here
  (lobo#48 to #52 and #55) are fixed in 0.1.3.

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
