# The lobo reel

A short film in eight scenes (0 to 7), shot on one MacBook (macOS arm64,
Starlink, carrier-grade NAT). Each scene shows something lobo does
that nginx does not, and each nginx line below is sourced and
worded to be exactly true. The last scene opens the public address
in a browser.

Nothing here is a mock. Every scene is a script that runs the
commands it shows, `rehearse.sh` runs the whole reel end to end,
and `preflight.sh` proves the whole chain (build, server, tunnel,
an outside machine fetching the page) right before filming.

## Before filming

| what | value |
|---|---|
| lobo | 0.1.1 (Homebrew) |
| wolf | 0.2.20 (`~/.local/bin` first on `PATH`) |
| cloudflared | 2026.9.3 |
| local address | `http://127.0.0.1:8088` (port 8080 is llama-swap: never used here) |
| public address | `REEL_PUBLIC_URL`, default `https://wolf.espadonne.com` (named tunnel `wolf-demo`, config `REEL_TUNNEL_CONFIG`, default `~/scratch/wolf/lobo-demo/tunnel.yml`) |
| fallback | `REEL_PUBLIC_URL=quick` runs a Cloudflare quick tunnel and reads its random URL from the tunnel log |
| outside witness | `ssh almanta` (`REEL_OUTSIDE`) |
| nginx contrast | scenes 2 and 3 run a real `nginx -t` / `-T` when one is found (`REEL_NGINX`, else `PATH`); without one they skip that beat |

Terminal: about 60 columns, large font, the shell in `demo/reel/`
(every script `cd`s there itself, but the commands typed by hand in
the shot list assume it). `SHOTLIST.md` is the maintainer's edit
plan, shot by shot, built on these scripts; this file is the
runbook behind it.

```sh
cd demo/reel
./preflight.sh      # must end in GO
./scene0.sh         # ... one take per scene; any scene can be re-run
./scene7.sh         # the finale opens the browser
./teardown.sh       # must end in "teardown: DOWN (proven)"
```

`REEL_BEAT` (seconds, default 1) is the pause between commands.

### What preflight proves, in order

1. lobo is `lobo/0.1.1`, wolf is `wolf 0.2.20`, cloudflared runs
2. port 8088 is free and no reel lobo or tunnel is running
3. `wolf run build/main.lu` writes the page (with its `<h1>`) and the 1,310,720-byte `big.bin`
4. `lobo -t` passes
5. lobo starts and `GET /` answers 200 with the `<h1>`
6. the tunnel registers a connection
7. **almanta fetches the public URL: 200 with the `<h1>`** (asked before this Mac ever looks the name up, so no cached NXDOMAIN can poison the browser)
8. this Mac fetches the public URL (the browser's resolver and path)
9. `/metrics` answers
10. the control socket answers `pong`

It prints `GO`, or `NO GO: failed at step N` with the reason, and
tears down anything it started.

### What teardown proves

lobo stopped through its control socket (`lobo -s stop`), the tunnel
process stopped by its exact pid, port 8088 free, no reel process
left, and the public URL no longer serving the page from almanta
(the named tunnel answers 530 when it is down).

Processes are identified by the pid each script recorded AND their
exact command line (AND, for lobo, its working directory), never by
pattern.

## The scenes

Expected output is trimmed to what fits a phone. Times are from the
rehearsals recorded in the PR.

### 0. A web server written in wolf (about 1 s plus holds)

**Say:** "This is lobo: a web server written in wolf."

```
$ find src -name '*.lu' | xargs cat | wc -l
   25496
$ mat src/config/workerconf.lu      # 41 lines; cat if mat is absent
$ lobo -v
lobo version: lobo/0.1.1 (built with wolf 0.2.16, pin 93a5fe5)
```

The count is the source of the lobo checkout the reel lives in
(trunk at this branch's base: 25,496 lines). The 0.1.1 binary on
screen was built from 24,220 lines (the `v0.1.1` tag), so "about
25,000 lines of wolf" is true of the source shown, and "about
24,000" of the binary.

**nginx:** no contrast here.

### 1. Built by wolf (about 2 s)

**Say:** "This whole site is one wolf program."

```
$ cat build/main.lu            # 33 lines, none wider than 63
$ wolf run build/main.lu
wrote html/index.html and html/files/big.bin
big.bin is 1310720 bytes
$ grep -o '<h1>.*</h1>' html/index.html
<h1>hello from wolf</h1>
```

**nginx:** no contrast here; this scene is about wolf.

### 2. The dry run that means something (about 3 s)

**Say:** "Which location serves this URL? lobo answers without
sending a request, and says why every other candidate lost."

```
$ grep location conf/site.conf
    location / { }
    location = / { }
    location /files/ {
$ lobo -t --request 'GET http://wolf.espadonne.com/files/big.bin' 2>/dev/null | grep -E '^location|candidate|^decision'
location: /files/ (./conf/site.conf:11)
  candidate location / (./conf/site.conf:9) — lost: the prefix matches, but a longer prefix won (1 < 7)
  candidate location = / (./conf/site.conf:10) — lost: the path is not exactly this location's `=` argument
  candidate location /files/ (./conf/site.conf:11) — won: the longest matching prefix wins (7 bytes)
decision: would serve: html/files/big.bin (not checked)
$ lobo -t --request 'GET http://wolf.espadonne.com/' 2>/dev/null | grep ...
location: / (./conf/site.conf:10)
  ... = / ... — won: exact match — `location =` beats every prefix and regex
$ nginx -p . -c conf/nginx.conf -t
nginx: the configuration file ./conf/nginx.conf syntax is ok
nginx: configuration file ./conf/nginx.conf test is successful
```

**nginx (true as worded):** `nginx -t` validates that a config
loads; nothing in nginx tells you which location a URL will hit
without sending it a real request. Source: `docs/DRYRUN.md` ("`nginx
-t` checks syntax. `lobo -t --request ...` checks MEANING"). Softened:
`nginx -t` does more than parse (it opens files and checks values),
so the scene says "validates", not "only checks syntax". The nginx
beat runs the same `site.conf` minus lobo's two native lines, which
nginx rejects.

### 3. Provenance (about 2 s)

**Say:** "Every directive, with the file and line it came from, and
the include that pulled it in."

```
$ grep include conf/nginx.conf
    include site.conf;
$ lobo -T 2>/dev/null | grep -B1 -E 'memory_budget|metrics on|location /files/'
        # from ./conf/site.conf:5 (via ./conf/nginx.conf:5)
        metrics on;
        # from ./conf/site.conf:6 (via ./conf/nginx.conf:5)
        memory_budget 128k;
--
        # from ./conf/site.conf:11 (via ./conf/nginx.conf:5)
        location /files/ {
$ nginx -p . -c conf/nginx.conf -T 2>/dev/null | grep -n -E '^# configuration|location /files'
1:# configuration file ./conf/nginx.conf:
8:# configuration file ./conf/site.conf:
17:    location /files/ {
```

**nginx (true as worded):** nginx has `-T` too: it names each file
and pastes it whole. It does not stamp a directive with its line or
with the include chain. Measured with nginx 1.30.4 (the lobo
differential's pinned oracle); lobo's side is `docs/DRYRUN.md`'s
"effective directives with `-T` provenance". Softened from "nginx
can't dump its config", which is false.

### 4. The reload you can watch (about 30 s)

**Say:** "A slow download is in flight. I ship version 2 and reload.
The old generation keeps the download, the new one serves v2, and
you can watch the old one drain and retire."

```
$ curl -s --limit-rate 64k -o logs/dl.bin localhost:8088/files/big.bin &
$ cp -R html html-v2
$ sed -i '' 's/hello from/v2: hello from/' html-v2/index.html
$ sed -i '' 's/root html;/root html-v2;/' conf/site.conf
$ lobo -s reload
reload complete (generation 2)
$ lobo status | grep '^generation' | cut -d' ' -f1-4,10
generation 1: draining live=2 shutdown-in-ms=24997
generation 2: current live=0
$ curl -s localhost:8088/ | grep -o '<h1>.*</h1>'
<h1>v2: hello from wolf</h1>
$ curl -s localhost:8088/metrics | grep -E '^lobo_(config_generations|connections_active)'
lobo_config_generations{state="current"} 1
lobo_config_generations{state="draining"} 1
lobo_connections_active{gen="1"} 2
lobo_connections_active{gen="2"} 1
$ wait  # for the download
$ shasum html/files/big.bin logs/dl.bin | cut -c1-16
cd9071c2e47c5e19
cd9071c2e47c5e19
$ until grep -q 'retired gen=1' logs/serve.out; do sleep 1; done
$ grep -E '(draining|retired) gen=1 ' logs/serve.out | cut -c16- | cut -d' ' -f1-5
generation-draining gen=1 held=2 seq=4
connection-retired gen=1 remaining=1 seq=7
connection-retired gen=1 remaining=0 seq=8
generation-retired gen=1 drained=1 aborted=1 age-ms=25049
```

Two connections, not one: the second is the tunnel's idle keep-alive
to lobo (cloudflared pools its origin connections). lobo holds an
idle keep-alive on a draining generation until it closes or
`worker_shutdown_timeout` (25 s here) aborts it, which is why the
retirement reads `drained=1 aborted=1`. If the tunnel has no idle
connection at that moment, the stanza reads `live=1`, `held=1`, and
`drained=1 aborted=0`, and generation 1 retires the moment the
download ends (about 15 s sooner). Both are correct; say whichever
one the take shows.

Off camera, the script puts v1 back (one more reload, generation 3)
and removes `html-v2`, so the scene can be re-run for a retake.

The shot list films this scene in two panes with sub-steps:
`scene4.sh status`, `scene4.sh download` (pane 2: progress bar, then
the checksums), `scene4.sh reload`, `scene4.sh retired` (waits for
the old generation to retire, then prints its four log lines), and,
off camera, `scene4.sh restore`. `reload` refuses if v2 is already
live. Before reloading, `reload` waits out lobo#46 (a slow download's
start holds the loop for up to 8 s) and never trusts an empty `lobo
status` (lobo#47).

**nginx (true as worded):** nginx's old workers drain with no
connection count and nothing to ask: at its default log level the
error log is silent, at `notice` it says a worker is "gracefully
shutting down" and later "exited", and `ps` shows "worker process is
shutting down". lobo names the generation, counts what it holds,
counts down the deadline, and logs each connection's retirement.
Sources: `docs/DRAIN.md` ("nginx's `-s reload` is a shrug: the old
workers drain in the dark"), `docs/CONTROL.md` deltas D3 and D4.
Softened: D3 says "zero drain events in the error log", which holds
at nginx's default level; measured with nginx 1.30.4 at `notice`, it
logs the three lines above, so the scene does not say "nothing".
Also true and worth knowing (D4): nginx closes idle keep-alives on a
reload; lobo keeps them until they close or the timeout.

### 5. The memory budget is real (about 4 s)

**Say:** "Every request gets 128 KB. Normal traffic keeps flowing
while one request that wants more gets a 503 with a name."

```
$ grep memory_budget conf/site.conf
    memory_budget 128k;    # lobo-native: per request
$ curl -s localhost:8088/metrics | grep '^lobo_budget'
lobo_budget_refusals_total{gen="3"} 0
$ BIG=$(head -c 50000 /dev/zero | tr '\0' w)
$ (for i in 1 2 3 4 5 6 7 8; do curl -s -o /dev/null -w '%{http_code} ' localhost:8088/; sleep 0.25; done; echo) &
200 200 200 200
$ curl -s -o /dev/null -w '%{http_code} <- the big one\n' -H "A: $BIG" -H "B: $BIG" -H "C: $BIG" localhost:8088/
503 <- the big one
200 200 200 200
$ grep budget-exceeded logs/serve.out | tail -n 1 | cut -d' ' -f2-7
[error] budget-exceeded gen=3 site=head budget=131072 would=150088
$ curl -s localhost:8088/metrics | grep '^lobo_budget'
lobo_budget_refusals_total{gen="3"} 1
```

The request is three 50,000-byte headers: inside the fence
(`large_client_header_buffers 4 64k`), over the budget. The wire
answer is nginx's own `503 Service Temporarily Unavailable`; the
name (`budget-exceeded site=head`, with the budget and what the
request would have cost) is in lobo's log and its counter.

**nginx (true as worded):** nginx caps sizes
(`client_max_body_size`, `large_client_header_buffers`) but has no
per-request memory budget; on Linux, memory pressure is answered by
the kernel's OOM killer, which takes the whole worker and every
connection on it. Measured with nginx 1.30.4 under the same
`large_client_header_buffers 4 64k`: this exact request is a 200.
Source: `docs/BUDGET.md` ("nginx's answer to memory pressure is the
OOM killer ... lobo's answer is a 503 with a name"),
`docs/directives.md` (`memory_budget`, http or server context; the
directive is not allowed in a `location`).

### 6. Live metrics (about 1 s)

**Say:** "One line of config, and lobo speaks Prometheus: the
reloads from scene 4 and the refusal from scene 5 are right there."

```
$ curl -s localhost:8088/metrics | grep -c '^lobo_'
61
$ curl -s localhost:8088/metrics | grep -E '^lobo_(config_generation_current|config_generations|budget|requests_total)'
lobo_config_generation_current 3
lobo_config_generations{state="current"} 1
lobo_config_generations{state="draining"} 0
lobo_requests_total{class="2xx"} 22
lobo_requests_total{class="3xx"} 0
lobo_requests_total{class="4xx"} 0
lobo_requests_total{class="5xx"} 1
lobo_budget_refusals_total{gen="3"} 1
```

Generation 3 is current: scene 4 reloaded twice (v2, then v1 back
off camera). The drain itself is visible at `/metrics` only while it
happens, which is why scene 4 scrapes mid-drain: lobo drops a
generation's series when it retires (lobo#51).

**nginx (true as worded):** open-source nginx's built-in status page
is `stub_status`: seven numbers, not Prometheus format, and nothing
about config generations; Prometheus needs a separate exporter or
the commercial NGINX Plus. Source: `docs/metrics.md` and lint
`LOBO-L010`. Softened: L010 says nginx's metrics story is "a
third-party module or the commercial build", which skips
`stub_status`; the scene names it.

### 7. Live (about 2 s)

**Say:** "This is the laptop, behind carrier-grade NAT, on the public
internet."

```
$ open https://wolf.espadonne.com
```

Before the browser opens, the script fetches the URL itself; if it
is not a 200 with the page's `<h1>`, it prints `NOT LIVE` and does
not open anything. Rehearsals (`REEL_REHEARSAL=1`) fetch the URL from
this Mac and from almanta instead of opening a browser.

**nginx:** no contrast. The public HTTPS here is Cloudflare's tunnel;
lobo serves plain HTTP on loopback. (lobo has ACME, `cert auto`, but
behind carrier-grade NAT nothing can reach ports 80/443, and nginx
1.29+ has an ACME module too, so the reel claims nothing about
certificates.)

## Known issues at lobo 0.1.1 that the reel works around

All found while building this reel, filed with witnesses, and
reproduced on trunk (866789c) as well as 0.1.1:

- lobo#46: **a slow download stalls the server for 3 to 8 s as it
  starts.** Requests and control verbs that arrive in that window
  wait. Scene 4 waits it out off camera before it reloads.
- lobo#47: **`lobo status` prints nothing and exits 0** when the
  control socket does not answer within 2 s. Scene 4 never reads an
  empty status as an answer.
- lobo#51: **a generation's series leave `/metrics` when it
  retires**, so the final `drained` count of a finished drain is
  never scrapeable. Scene 4 scrapes during the drain.
- lobo#50: **`worker_shutdown_timeout` is read once, at start**:
  changing it and reloading has no effect until a restart. The reel's
  value is in `conf/nginx.conf` from the first start.
- lobo#48: `location = /x { alias file; }` answers 404 (nginx: 200).
  lobo#49: `lobo -t -q` still prints the two success lines (nginx
  prints nothing). The reel uses neither.
- lobo#52: on macOS the gauntlet is red at confcheck (`user` is
  refused without /proc where nginx warns and loads); not a reel
  issue, found while gating this branch.

Also: `wolf run` cannot compile interpolation inside a multiline
string yet (wolf-lang#268's conservatism inventory), so
`build/main.lu` builds its page head as a plain multiline string and
interpolates on one line.

## Exposure while the tunnel is up

`metrics on` publishes `/metrics` and `/status.json` on the server's
own listener. lobo's posture is "bind to loopback or an admin
network" (`docs/metrics.md`), and the server is bound to loopback,
but the tunnel forwards every path, so both are public while the
reel runs (generation ids, request counts, memory high waters;
nothing secret, but not nothing). To hide them, add a rule above the
hostname's rule in the tunnel config:

```yaml
  - hostname: wolf.espadonne.com
    path: ^/(metrics|status\.json)$
    service: http_status:404
```

## Files

| file | what |
|---|---|
| `build/main.lu` | the wolf program that writes the site |
| `conf/nginx.conf`, `conf/site.conf` | the config (lobo reads nginx's grammar; the default config path means `lobo -t`, `-T`, `-s`, `status` need no flags) |
| `lib.sh` | shared settings and helpers |
| `preflight.sh`, `scene0.sh` ... `scene7.sh`, `teardown.sh` | the reel (`scene4.sh` and `scene5.sh` also take the shot list's sub-steps) |
| `SHOTLIST.md` | the maintainer's shot list for the edit |
| `rehearse.sh` | the whole reel, timed, with scene 7 fetching instead of opening |
