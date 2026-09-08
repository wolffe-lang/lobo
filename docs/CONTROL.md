# The server takes orders (ws15)

A running nginx takes orders from `kill(2)`: `nginx -s reload` looks up
the pid in the pid file and sends `SIGHUP`, and the KERNEL does the
authorizing: you may signal that process if you own it. That answer is
not available to lobo. The pin exposes no getpid and no arbitrary-pid
signal SEND (wolf-lang#126's unlanded half), and on windows `RELOAD` and
`UPGRADE` have no analog at all ([os.signal.platform]): nothing outside
the process can raise them. So lobo has a control endpoint, a
loopback listener a running server takes verbs on, and ws15 widened
it from a reload pipe into the server's order desk.

This page is the CONTRACT for that surface. docs/DRAIN.md owns what a
reload DOES (the generation table, the status stanza, the frozen log
vocabulary); this page owns how an operator asks for it.

## The directive

```nginx
control unix:/run/lobo/control.sock;           # a uid boundary (ws17)
control 127.0.0.1:9001;                        # loopback, no secret
control 127.0.0.1:9001 token /etc/lobo/ctl;    # loopback + a shared secret
control 9001;                                  # a bare port is a LOOPBACK bind
```

Main context, one to three arguments, off by default: no `control`
directive means no listener. It is lobo-NATIVE (nginx's `-t` rejects
the name) and the second arm is spelled `token <file>`; a `control`
with a keyword and no file, or a keyword that is not `token`, is a
named `-t` error (`config.control_check`), never a silently ignored
one.

The pid file records the endpoint (the #126 residue leaves no os pid
to record), so `lobo -s`, `lobo status`, `lobo control` and the next
start's stale-pid check all find it without being told.

## The listener, per host — measured, not assumed

Two transports since ws17, and the `unix:` one is the recommended
default where the host has it.

At ws15 wolf had NO unix-domain socket on any host: every spelling
answered a bare `io`, so a program could not even tell "this host has
no unix sockets" from "that path is wrong". That sprint shipped
loopback TCP everywhere and filed wolf-lang#227. The surface landed
at the ws17 pin (`[os.net.unix]`, s136; `std.net.unix` wraps it at
wolf-std sc36) and the `control` directive gains the address form the
filing asked for:

```nginx
control unix:/run/lobo/control.sock;
```

`unix:<path>` is nginx's own spelling (`listen unix:/path`), so an
operator who knows nginx knows this one. The path is used as written.

Why it is the recommended form: a socket in the filesystem
namespace is how haproxy's `stats socket`, systemd and nginx-plus's
api authorize an operator, with file permissions as the boundary. A
loopback port is not a uid boundary: every local user on the host can
dial 127.0.0.1, which is why ws15 grew the token arm.
With a unix endpoint in a directory the operator owns, the token is
optional; it stays for the TCP form and for a host with no unix
family.

The rows, and what lobo does with each (`bind_control` in main;
`[os.net.unix]`'s vocabulary, each row refused under its own name,
which is what the filing asked for):

| row at bind | lobo |
|---|---|
| `unsupported` | **refuses at startup, by name**: "this host has no unix-domain sockets, so `control unix:…` cannot be served … use a loopback address with the token arm instead". windows at this pin |
| `exists` | **refuses, and does not clobber.** Something is already at that path — a live master, a stale socket, or an ordinary file — and which of those it is is not a decision a server can make for an operator. Remove it yourself if you know which |
| `not_found` | the directory on the way to the path does not exist |
| `denied` | the caller may not create it there |

Cleanup is the binder's. `net_close` of a unix LISTENER unlinks
its path, so an orderly `stop`/`quit` leaves nothing behind; a
SIGKILLed master leaves the socket file, and the next start's
stale-pid check tells an operator whether a master is still
alive. A hand's endpoint is the master's to clean: the master NAMES
those paths (below), so it removes a dead one before starting a
replacement, the one case `[os.net.unix]` says a program may unlink
unconditionally.

Under `worker_processes N`, the hands' endpoints follow the
master's. A unix master gives hand *i* the sibling path
`<master>.w<i>` (`/run/lobo/control.sock.w2`), so every hand's order
desk inherits the directory's permissions and a hand's endpoint is a
uid boundary too. That was ws16's residue and it closes here: under
a TCP master the hands still get loopback ports, the same
non-boundary the master has.

std is not in this path. lobo calls the builtins (`net_listen_unix`,
`net_connect_unix`) directly. `std.net.unix` exists and is good, but
std wraps neither `net_listen_with` nor `net_adopt_listener`
(wolf-std#6, still open, sc37's), so the many-hands listener path has
no std tier at this pin, and using std for one half of the control
channel and a builtin for the other would be two seams where this
repo has always had one.
The day #6 lands, these call sites move to `std.net`'s spellings with
no behavioral change.

## The verbs

One line in, one line out (`status` answers a multi-line stanza read to
close). Every verb is reachable three ways: over the wire, through
`lobo -s <verb>` for nginx's four words, and through `lobo control
<verb>` for all seven.

| verb | what it does | signal twin | reply |
|---|---|---|---|
| `reload` | re-parse the config, freeze a new generation, drain the old one | `SIGHUP` (RELOAD) | `reload complete (generation N)` / `reload rejected: …; keeping generation N` |
| `quit` | graceful: stop accepting, drain, exit | `SIGQUIT` (QUIT) | `quit: draining then exiting (generation N)` |
| `stop` | fast shutdown | `SIGTERM` (TERMINATE) | `stop: shutting down (generation N)` |
| `reopen` | cycle the log outputs | — (nginx's `SIGUSR1`; lobo does not listen for it) | `reopen: log outputs cycled (generation N)` |
| `status` (`status json`) | the ws08 drain stanza, human or schema-1 JSON | — | the stanza |
| `upgrade` | the binary-swap verb — **unclaimed at this pin**, and dispatched so it can say so | — (see below) | `upgrade: not implemented at this pin — … when it lands it lands HERE` |
| `ping` | liveness | — | `pong` |

`lobo -s` still takes nginx's four words (`stop`, `quit`, `reload`,
`reopen`), and that parity is probed against the oracle in
`tools/lobo-shell`, so `status`, `upgrade` and `ping` ride the
lobo-native `lobo control <verb>` subcommand instead of a widened `-s`.
A rejected reload, an unknown verb, an `unauthorized` answer and
`upgrade`'s named refusal are all exit 1, so an operator's `lobo -s
reload && deploy` never runs on a reload that did not happen.

Why `upgrade` exists before it works: it is the one verb the
endpoint reaches that no signal does. On unix, UPGRADE's bit is lobo's
own poll probe (the serve loop self-raises it every pass to bound its
spawn-free signal wait), so a real outside `SIGUSR2` is
indistinguishable from the probe and is ignored (the wsm01 residue). On
windows there is no external RELOAD or UPGRADE at all. Naming the verb
here puts the binary swap at this endpoint when it lands, and the
reply says as much.

With no `control` directive, `lobo -s reload` refuses and says why:

```
lobo: [error] no "control" directive in nginx.conf: a running lobo is
reached ONLY over its control endpoint at this pin (there is no
arbitrary-pid signal send — wolf-lang#126), so add
`control 127.0.0.1:<port>;` and restart
```

That is the windows sentence made operational on every host. Signals
still work where they are delivered: `kill -TERM` on a lobo with no
control directive shuts it down, and `tools/lobo-signal` witnesses
it.

## A verb and a signal are the same code path

Both triggers reach ONE dispatch in the serve loop, and ONE emission
site stamps the vocabulary event, so the log a control reload writes is
the log a `SIGHUP` writes. ws09's vocabulary gains no event and no new
key: `signal-received` grows a trailing `source` field
(appended, nothing renamed, every earlier prefix pin still matches),
and `source` is the only difference.

Measured, from one server reloaded twice, once over the endpoint and
once by a real `kill -HUP`:

```
lobo: [notice] signal-received sig=reload verb=reload source=control seq=8
lobo: [notice] generation-draining gen=2 held=0 seq=9
lobo: [notice] generation-loaded gen=3 id=18ab24c71d9f8610 seq=10
lobo: [notice] generation-activated gen=3 seq=11
lobo: [notice] generation-retired gen=2 drained=0 aborted=0 age-ms=0 seq=12

lobo: [notice] signal-received sig=reload verb=reload source=signal seq=13
lobo: [notice] generation-draining gen=3 held=0 seq=14
lobo: [notice] generation-loaded gen=4 id=18ab24c71d9f8610 seq=15
lobo: [notice] generation-activated gen=4 seq=16
lobo: [notice] generation-retired gen=3 drained=0 aborted=0 age-ms=0 seq=17
```

`tools/lobo-signal` asserts this with a diff: it extracts both
five-line blocks, normalizes the generation numbers, the seq stamps,
the content hash and the age, and requires exactly one differing line;
then it normalizes `source` too and requires the blocks to be
byte-identical.

The verbs with no signal twin (`status`, `reopen`, `ping`, `upgrade`)
emit NO vocabulary event: `sig`'s value set stays the frozen
`reload|terminate|quit`, and a verb that changes no generation writes no
generation event. An unauthorized line emits no event either; the
refusal is a prose notice at `warn`
(`lobo: [warn] control: unauthorized command rejected`), so the seq
stream stays the stream of decisions the loop took.

## Under `worker_processes N`: the verbs fan out (ws16)

With N >= 2 hands (docs/WORKERS.md) the endpoint above is the
MASTER's, and every verb it takes reaches each hand over that hand's
own loopback endpoint, in ordinal order: `reload` is parsed by the
master first (D2 holds: a rejected config reaches no hand) and then
rolled through the hands one at a time, each swapping and draining
in place; `quit`/`stop`/`reopen` fan out; `status` folds a row per
hand. The replies keep ws15's prefixes and gain a suffix naming the
fan-out (`reload complete (generation 2) workers=3/3`), so every
script and every control-differential row that reads the prefix
still reads it. A hand's endpoint is an order desk too: it is
printed in its status row, it is authorized by the same `token
<file>` (each hand reads the file itself; no secret crosses an
argv), and a verb sent to ONE hand acts on that hand alone, which
is how the witness stops a serving hand and watches a standby take
the listener.

## Authorization

Two arms, and the posture of each.

Arm 1, the loopback bind (always). The listener binds 127.0.0.1
and nothing else, forever; a bare port in the directive becomes a
loopback bind. This keeps the endpoint off the network. It does NOT
keep it away from other users of the same host.

Arm 2, the token file (opt-in). `control <addr> token <file>` arms
a shared secret. The wire line becomes `<secret> <verb>`; a line without
it, or with the wrong one, is answered `unauthorized`, dispatches
nothing, and changes nothing.

- lobo READS the token file and never writes one. The obvious
  design, generating a secret at startup with `os_random` and writing
  it out, is unavailable: std has no file-permission surface at this
  pin (no chmod, no create-with-mode, no umask query; wolf-std#5), so
  a token lobo generated would land at whatever the umask says,
  commonly world-readable. The operator creates the file with the mode
  they want; lobo reads its first line.
- A config that names a token file lobo cannot read refuses at
  startup, saying which of missing, unreadable or empty it was. That
  keeps an endpoint from arming auth that does nothing.
- `ping` is exempt. It is the liveness probe `-s` and the startup
  stale-pid check use; it reveals nothing but existence; and gating it
  would let a rotated token make a LIVE master look dead, which would
  have the next start replace a running server's pid file.
- The startup notice says which arm is live: `control 127.0.0.1:9001
  (auth: loopback + token)` or `(auth: loopback only)`.

The token is not a transport secret. It crosses loopback in clear,
and anyone who can read the token file can use it. It is a
*local user* boundary standing in for the file-permission boundary a
unix socket would give, and it is only as good as the mode the operator
put on that file. Since wolf-lang#227 landed the socket IS the
boundary and this arm becomes the windows fallback.

## The nginx differential

`tools/lobo-control-differential` (a gauntlet step) runs the pinned
oracle beside lobo, drives the same reload script at both, and measures
the same things. Four rows CARRY:

| row | measurement | both servers |
|---|---|---|
| 1. config re-read | edit the root, reload, request again | the new root serves new connections |
| 2. the listener survives | 20 connects after the reload | zero refusals (nginx keeps the socket across the fork; lobo reuses the live fd) |
| 3. old connections never get the NEW config | a keepalive connection held across the reload | neither server answers from the new generation |
| 4a. a bad config is refused | reload an unparseable config | both keep serving the previous config |
| 4b. …and says so | the `-s reload` exit code | non-zero on both |

Four rows are NAMED DELTAS, printed with their reason:

| delta | nginx | lobo | why |
|---|---|---|---|
| **D1 transport** | `kill(pid, SIGHUP)`; the kernel authorizes (same uid), the pid file is not a secret | a unix socket where the host has one, else a loopback TCP endpoint with an optional token | no getpid/kill-by-pid at this pin (#126) and no external RELOAD on windows; the unix socket #227 asked for LANDED at ws17 and is now the recommended form |
| **D2 who parses** | the CLIENT parses the config and exits 1 with the `[emerg]`; the master is never signalled | the MASTER parses and answers the verdict on the wire, naming the generation that kept serving | lobo's trigger carries a reply socket; nginx's is a signal, which cannot answer |
| **D3 narration** | the old workers drain in the dark (zero drain events in the error log) | six events per reload — `generation-draining`/`-loaded`/`-activated`/`-retired` — plus `lobo status` | docs/DRAIN.md's whole subject |
| **D4 idle keepalive at reload** | the old worker closes its IDLE keepalive connections once it finishes shutting down | the draining generation HOLDS them until they close, or `worker_shutdown_timeout` aborts them | lobo is the more forgiving of the two: a client written against nginx keeps working, a client written against lobo may not survive nginx |

Row 3 tolerates either behavior because D4 is real; it asserts the
invariant a client depends on: an already-open connection is never
served the new config.

What is NOT compared: nginx's `-s reopen` and `-s quit` semantics
are already pinned elsewhere (`tools/lobo-signal`, the drain suite);
binary upgrade (`kill -USR2`) has no lobo side to compare yet; and
nginx's windows service control has no lobo side at all.

## Windows

lobo's CI is linux; the local gauntlet runs on linux and macOS. Nothing
on this page about windows is MEASURED by lobo; it is CLAIMED from
[os.signal.platform]'s normative table (s60b) and stated as such in
docs/DRAIN.md, which holds the promise lobo makes there:

> On windows, `lobo -s reload` reaches a running lobo over its `control`
> endpoint or not at all.

That sentence now holds on every host: the refusal above fires
wherever a config has no `control` directive. `upgrade` got its place
at the same time. A windows-native lobo job is out of scope
here (the release tier still refuses on windows by name at this pin,
s60c's work) and is a ws16-class decision.

## Witnesses

- `tests/shell/control_verbs.lu`: the PURE surface on all three lanes:
  the directive's two arms, the wire line, the authorization rule, the
  verb set, the verb→meaning map, and the one event builder's two
  sources.
- `tests/shell/control_e2e.lu`: the real binary with a real token file:
  reload/reopen/stop over the channel, the routing swap, listener
  survival, and the four auth cases (right secret, no secret, wrong
  secret, `ping` exempt) with a status read proving the refused verbs
  changed nothing; `upgrade` answering with its own name.
- `tools/lobo-signal`: the two doors' event blocks diffed line by line.
- `tools/lobo-control-differential`: the rows above, against the pinned
  oracle.
- `tools/lobo-shell`: `-s` keeps four words; the no-`control`
  refusal names the directive; an invented `control` verb is refused
  before any socket is touched.
