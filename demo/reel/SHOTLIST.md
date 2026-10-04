# lobo — the shot list

A short film in eight scenes. Each scene is one idea, shown on this MacBook, ending with the site live on the internet at **https://wolf.espadonne.com**.

How to read a scene: **SHOW** means put this on screen and hold it; **RUN** means type this command and let the output land; the time is how long the shot holds. Times are targets for the edit, not limits.

Every command and every output below was rehearsed on this MacBook (2026-10-03: full runs preflight to teardown, both from the lobo repo and from `~/scratch/wolf/lobo-demo`, all green). `README.md` beside this file is the runbook behind it: each scene's script, the full expected output, and the source for every nginx line.

**Which lobo.** Scenes 4 to 6 as written here need lobo 0.1.2 or later (`brew upgrade lobo`), which carries ws49's three fixes: a slow download no longer holds the server (lobo#46), `lobo status` that gets no answer says so and exits 1 (lobo#47), and `-p` finds the control socket from any folder (lobo#54). The preflight expects `lobo/0.1.2`; a trunk build reads `lobo/0.1.2+dev`, so for one run `export REEL_LOBO_VERSION=lobo/0.1.2+dev` first. With Homebrew's older 0.1.1 every scene still runs: scene 4's script waits the stall out for you (the 0.1.1 notes in scene 4), raw `lobo` commands must be typed in the reel folder, and the preflight needs `export REEL_LOBO_VERSION=lobo/0.1.1`.

---

## Before you press record

| step | command | what you should see |
|---|---|---|
| terminal | a large font (20 pt or more), a dark theme, the window about 60 columns wide | text readable on a phone |
| narrow output | `export COLUMNS=60` | |
| go to the demo | `cd /Users/mfwolffe/scratch/wolf/lobo-demo` | the complete reel: `conf/nginx.conf`, the scripts, `tunnel.yml` *(the same files live in the lobo repo's `demo/reel/`; every script refuses, with the `cd` to type, if started from any other folder)* |
| preflight | `bash /Users/mfwolffe/scratch/wolf/lobo-demo/preflight.sh` | ten `ok` lines, then `GO` on the last line |

Do not film until the preflight prints **GO**. It proves the whole chain, including a machine outside your network (almanta) loading the live address, and it **leaves lobo and the tunnel running for the whole film**: nothing below starts or stops them, so nothing can fail to come up on camera. If it prints `NO GO`, it names the failing step and has already cleaned up after itself.

Every path below is a full path, so commands work from any folder: the scripts move into the reel folder themselves, and the two raw `lobo` commands name the reel's prefix and config with `-p` and `-c`. The reel folder is **/Users/mfwolffe/scratch/wolf/lobo-demo**; lobo's own source is **/Users/mfwolffe/GithubOrgs/wolffe-lang/lobo**.

---

## The music

| song | artist | where it plays | why |
|---|---|---|---|
| 4 Chords of the Apocalypse | Julian Casablancas | Scene 0 | a slow, building opener under the source code |
| I'll Try Anything Once | The Strokes | Scenes 1–3 | a quiet, steady track under the quick terminal shots; the dry run *tries* a request without serving it |
| In One Ear | Cage the Elephant | Scenes 4–5 | energy for the two live moments: a reload under load, a request refused while the site keeps serving |
| I'll Try Anything Once (live) | Julian Casablancas | Scene 6 | the live version under the live metrics |
| Blue | Mnozil Brass | Scene 7 | the finale; the live recording's applause lands on the phone loading the page |

---

## Scene 0 — "This is a web server written in wolf" (about 20 s)

**Music:** 4 Chords of the Apocalypse.

| # | action | command | hold |
|---|---|---|---|
| 0.1 | SHOW the size of the thing | `find /Users/mfwolffe/GithubOrgs/wolffe-lang/lobo/src -name '*.lu' \| xargs cat \| wc -l` | 3 s: `25496` (lines of wolf on trunk at this rehearsal; the number moves with trunk) |
| 0.2 | SHOW one whole source file | `mat /Users/mfwolffe/GithubOrgs/wolffe-lang/lobo/src/config/workerconf.lu` | 8 s, scroll slowly; it is 41 lines, nginx's `worker_processes` check, with nginx's own error message (`"worker_processes" directive invalid value`, probed against nginx 1.30.4) |
| 0.3 | SHOW the binary | `lobo -v` | 4 s: `lobo version: lobo/0.1.2 (built with wolf 0.2.23, pin 8edac3e)` |
| 0.4 | back to the demo | `cd /Users/mfwolffe/scratch/wolf/lobo-demo` | 1 s |

`bash /Users/mfwolffe/scratch/wolf/lobo-demo/scene0.sh` runs 0.1 to 0.3 against `~/GithubOrgs/wolffe-lang/lobo` (or the checkout the reel lives in, from the repo copy).

**On-screen caption idea:** "25,000 lines of wolf. One binary." *(True of the source on screen, whose count moves with trunk. The 0.1.2 binary on screen was built from 26,053 lines, the `v0.1.2` tree; if the caption sits on 0.3, "26,000" is the closer number. A 0.1.1 binary was built from 24,220.)*

---

## Scene 1 — "Built by wolf" (about 15 s)

**Music:** I'll Try Anything Once (The Strokes) starts.

| # | action | command | hold |
|---|---|---|---|
| 1.1 | SHOW the program that builds the site | `mat /Users/mfwolffe/scratch/wolf/lobo-demo/build/main.lu` | 7 s; 33 lines, none wider than 63 columns: three cards, a page, and a 1.3 MB file for scene 4 |
| 1.2 | RUN it | `cd /Users/mfwolffe/scratch/wolf/lobo-demo && wolf run build/main.lu` | 3 s: `wrote html/index.html and html/files/big.bin` / `big.bin is 1310720 bytes` |
| 1.3 | SHOW the result | `grep -o '<h1>.*</h1>' /Users/mfwolffe/scratch/wolf/lobo-demo/html/index.html` | 3 s: `<h1>hello from wolf</h1>` |

**Caption idea:** "A wolf program writes the website."

---

## Scene 2 — "The dry run that means something" (about 15 s)

| # | action | command | hold |
|---|---|---|---|
| 2.1 | SHOW the config | `mat /Users/mfwolffe/scratch/wolf/lobo-demo/conf/site.conf` | 4 s: the server, `metrics on;`, `memory_budget 128k;`, three locations (`/`, `= /`, `/files/`) |
| 2.2 | RUN a dry run of one request | `lobo -p /Users/mfwolffe/scratch/wolf/lobo-demo -c /Users/mfwolffe/scratch/wolf/lobo-demo/conf/nginx.conf -t --request 'GET http://wolf.espadonne.com/files/big.bin' 2>/dev/null \| grep -E '^location\|candidate\|^decision'` | 8 s (output below): `/files/` wins, and each other location says why it lost; no server is touched |

2.2's output:

```
location: /files/ (./conf/site.conf:11)
  candidate location / (./conf/site.conf:9) — lost: the prefix matches, but a longer prefix won (1 < 7)
  candidate location = / (./conf/site.conf:10) — lost: the path is not exactly this location's `=` argument
  candidate location /files/ (./conf/site.conf:11) — won: the longest matching prefix wins (7 bytes)
decision: would serve: html/files/big.bin (not checked)
```

`bash /Users/mfwolffe/scratch/wolf/lobo-demo/scene2.sh` adds a second request (`/`, where the exact `= /` wins) and, when an nginx binary is found, runs `nginx -t` on the same locations so the contrast is on screen: `syntax is ok` / `test is successful`, and nothing about any request.

**Honest contrast for the caption:** `nginx -t` checks that the config loads; `lobo -p /Users/mfwolffe/scratch/wolf/lobo-demo -c /Users/mfwolffe/scratch/wolf/lobo-demo/conf/nginx.conf -t --request` answers what the config would *do* with that request.

---

## Scene 3 — "Every setting knows where it came from" (about 10 s)

| # | action | command | hold |
|---|---|---|---|
| 3.1 | RUN the config with provenance | `lobo -p /Users/mfwolffe/scratch/wolf/lobo-demo -c /Users/mfwolffe/scratch/wolf/lobo-demo/conf/nginx.conf -T 2>/dev/null \| grep -B1 -E 'memory_budget\|metrics on\|location /files/'` | 8 s (output below): each directive under `# from <file>:<line> (via <the include>)` |

3.1's output:

```
        # from ./conf/site.conf:5 (via ./conf/nginx.conf:5)
        metrics on;
        # from ./conf/site.conf:6 (via ./conf/nginx.conf:5)
        memory_budget 128k;
--
        # from ./conf/site.conf:11 (via ./conf/nginx.conf:5)
        location /files/ {
```

The unfiltered `lobo -p /Users/mfwolffe/scratch/wolf/lobo-demo -c /Users/mfwolffe/scratch/wolf/lobo-demo/conf/nginx.conf -T 2>/dev/null` is 43 lines (every directive, each under its `# from` line) if you would rather scroll it.

**Honest contrast:** `nginx -T` prints the files it read; lobo marks every directive with the file and line that set it.

---

## Scene 4 — "The reload you can watch" (about 30 s)

**Music:** In One Ear starts on 4.1.

Two panes, in any folder: every command below is a full path.

| # | action | command | hold |
|---|---|---|---|
| 4.1 | SHOW lobo serving (since preflight) | `bash /Users/mfwolffe/scratch/wolf/lobo-demo/scene4.sh status` | 2 s: `generation 1: current live=1` *(live=0 or 1: the 1 is the tunnel's idle connection)* |
| 4.2 | start a slow download in the second pane | `bash /Users/mfwolffe/scratch/wolf/lobo-demo/scene4.sh download` | runs through the scene: a progress bar for about 20 s (1.3 MB at 64 KB/s) |
| 4.3 | edit the page and reload | `bash /Users/mfwolffe/scratch/wolf/lobo-demo/scene4.sh reload` | 3 s: it copies the site to `html-v2`, edits the `<h1>`, points `root` at it, `lobo -s reload` → `reload complete (generation 2)` |
| 4.4 | SHOW the drain | `bash /Users/mfwolffe/scratch/wolf/lobo-demo/scene4.sh status` | 8 s: `generation 1: draining live=2 shutdown-in-ms=21960` / `generation 2: current live=0` |
| 4.5 | the download finishes intact | (second pane) | 4 s: two identical lines, `cd9071c2e47c5e19` |
| 4.6 | SHOW the old generation retired | `bash /Users/mfwolffe/scratch/wolf/lobo-demo/scene4.sh retired` | 4 s (output below; it waits until generation 1 retires, at most 25 s after 4.3) |

4.6's output (as rehearsed; with no idle tunnel connection it reads `held=1`, one `connection-retired`, `drained=1 aborted=0`, and comes sooner):

```
generation-draining gen=1 held=2 seq=4
connection-retired gen=1 remaining=1 seq=7
connection-retired gen=1 remaining=0 seq=8
generation-retired gen=1 drained=1 aborted=1 age-ms=25041
```

`live=2` is the download plus the tunnel's idle keep-alive. lobo keeps an idle connection on a draining generation until it closes or `worker_shutdown_timeout` (25 s, in `conf/nginx.conf`) cuts it, which is the `aborted=1`.

**Off camera, after the take:** `bash /Users/mfwolffe/scratch/wolf/lobo-demo/scene4.sh restore` (v1 back, for a retake and for the finale). `bash /Users/mfwolffe/scratch/wolf/lobo-demo/scene4.sh` with no argument runs the whole scene in one pane.

Rehearsal timing (two-pane run, clock from 4.1): 4.3 can follow 4.2 at once. The download no longer holds lobo as it starts (lobo#46, fixed in 0.1.2), so the reload and its status answer while the progress bar runs; the download ends at about 20 s, and 4.6 prints about 25 s after 4.3 (when the tunnel's idle connection is aborted) or as the download ends (when there is none). *With lobo 0.1.1:* 4.3 lands 5 to 8 s after 4.2 starts, because the script first waits out that stall.

The same stanza as 4.4, typed by hand from any folder (lobo 0.1.2 or later): `lobo -p /Users/mfwolffe/scratch/wolf/lobo-demo -c /Users/mfwolffe/scratch/wolf/lobo-demo/conf/nginx.conf status`.

**Honest contrast:** nginx drains old workers on reload without a count: its log says a worker is "gracefully shutting down" (at `notice` level only) and `ps` shows "worker process is shutting down"; lobo shows each configuration generation, its open connections, the time left, and the moment it retires.

---

## Scene 5 — "The memory budget is real" (about 15 s)

| # | action | command | hold |
|---|---|---|---|
| 5.1 | SHOW the budget line in the config | `grep memory_budget /Users/mfwolffe/scratch/wolf/lobo-demo/conf/site.conf` | 3 s: `memory_budget 128k;    # lobo-native: per request` |
| 5.2 | RUN the oversized request beside normal ones | `bash /Users/mfwolffe/scratch/wolf/lobo-demo/scene5.sh burst` | 8 s (output below): `200`s on either side of one `503`, then the named reason from lobo's log |
| 5.3 | SHOW the counter | `curl -s 127.0.0.1:8088/metrics \| grep '^lobo_budget'` | 3 s: `lobo_budget_refusals_total{gen="3"} 1` *(gen 3 after scene 4's restore)* |

5.2's output:

```
200 200 200 200
503 <- the big one
200 200 200 200
[error] budget-exceeded gen=3 site=head budget=131072 would=150088
```

The big request is three 50,000-byte headers: allowed by the size limits, over the 128 KB budget. The wire answer is a plain `503`; lobo's log names why (`budget-exceeded`, where, the budget, and what the request would have cost) and its counter moves.

**Honest contrast:** nginx has size limits but no per-request memory budget (under the same limits nginx 1.30.4 answers this exact request 200); on Linux, under memory pressure the kernel's OOM killer kills the whole worker process, and every connection on it.

---

## Scene 6 — "Live metrics, built in" (about 12 s)

**Music:** I'll Try Anything Once (live).

| # | action | command | hold |
|---|---|---|---|
| 6.1 | open the metrics page | browser: `http://127.0.0.1:8088/metrics` | 10 s; scroll to `lobo_config_generation_current 3` (scene 4's reload and restore), `lobo_requests_total{class="5xx"} 1` and `lobo_budget_refusals_total{gen="3"} 1` (scene 5's refusal) |

The drain itself is on this page only while it is happening (`lobo_config_generations{state="draining"} 1`, `lobo_connections_active{gen="1"} 2`): lobo drops a generation's lines when it retires. To film it, open this page during 4.4. `bash /Users/mfwolffe/scratch/wolf/lobo-demo/scene6.sh` prints the same lines in the terminal.

**Honest contrast:** nginx's built-in `stub_status` has seven numbers; lobo's metrics carry the configuration generations (and a drain while it happens) and the budget, with no exporter.

---

## Scene 7 — "It's live" (about 20 s)

**Music:** Blue (Mnozil Brass); time the applause to 7.3.

| # | action | command | hold |
|---|---|---|---|
| 7.1 | SHOW the tunnel is up (since preflight) | `grep -o 'Registered tunnel connection connIndex=[0-9]' /Users/mfwolffe/scratch/wolf/lobo-demo/logs/tunnel.out` | 3 s: four lines, `connIndex=0` to `connIndex=3` |
| 7.2 | SHOW the address on the laptop | `bash /Users/mfwolffe/scratch/wolf/lobo-demo/scene7.sh` | 5 s: it fetches `https://wolf.espadonne.com` once more and only then opens the browser; if the page is not live it prints `NOT LIVE` and opens nothing |
| 7.3 | the reveal: your phone with **Wi-Fi off** | phone browser: `https://wolf.espadonne.com` | 8 s: the page loads over the internet, served by this MacBook |

**Caption idea:** "Written in wolf. Served by lobo. From a laptop on Starlink."

(The HTTPS is Cloudflare's tunnel; lobo serves plain HTTP on the laptop's loopback. While the tunnel is up, `/metrics` is public too: see the README's "Exposure" note.)

---

## After filming

`bash /Users/mfwolffe/scratch/wolf/lobo-demo/teardown.sh`. It stops lobo through its control socket, stops the tunnel by its exact process id, and checks from almanta that the address is dead; it ends with `teardown: DOWN (proven)`.

The address then answers HTTP 530 (Cloudflare's error 1033, "tunnel offline"), which is the correct state when you are not filming.

---

## Manual preflight (if `preflight.sh` cannot run)

```
cd /Users/mfwolffe/scratch/wolf/lobo-demo
lsof -nP -iTCP:8088 -sTCP:LISTEN          # must print nothing (8080 is llama-swap's; never use it)
cd /Users/mfwolffe/scratch/wolf/lobo-demo && wolf run build/main.lu                    # wrote html/index.html and html/files/big.bin
lobo -t                                   # ... test is successful
nohup lobo serve > logs/serve.out 2>&1 &  # start
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8088/      # 200
nohup cloudflared tunnel --no-autoupdate --config tunnel.yml run > logs/tunnel.out 2>&1 &   # wait for "Registered tunnel connection"
ssh almanta "curl -s -o /dev/null -w '%{http_code}\n' https://wolf.espadonne.com/"   # 200 = GO
```

With lobo 0.1.2 or later the control socket's relative path resolves under `-p`, so `lobo -p /Users/mfwolffe/scratch/wolf/lobo-demo -c /Users/mfwolffe/scratch/wolf/lobo-demo/conf/nginx.conf -s stop` works from any folder. With lobo 0.1.1 run lobo commands from this folder: there the path is relative to the current folder, and `-s stop` from anywhere else answers "not responding". A hand-started chain has no recorded process ids, so `teardown.sh` will not stop it: stop lobo with `lobo -s stop` and the tunnel by its own pid (`kill <pid>`), never by pattern.
