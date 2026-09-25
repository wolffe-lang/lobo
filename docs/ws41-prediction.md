# ws41 — the prediction, committed before the first edit

Wave 47, subwave 3. Written 2026-09-25 on lobo trunk `d65cce0`. The
pins are wolf 0.2.16 (`93a5fe5`), lupin 0.1.38 (`ba357aa`) and std
`070884c`, and none of them moves. The oracle pin is nginx 1.30.4
(`tests/differential/NGINX-PIN`), and it does not move either. When
this file is committed, nothing under `src/` has changed, no `Range`
request has been sent to either server, and no 1 MiB response has been
timed. The measurements land at the end of this file, under these
lines, right or wrong.

## §2: the contract's inputs, re-derived against origin

| input, as the contract states it | what origin says |
|---|---|
| lobo trunk `d65cce0` (ws40) | **holds**. `origin/trunk` is `d65cce0` |
| 40-config corpus, `INDEX.md` with the blocked-directive table | **holds**: 40 config directories plus `INDEX.md` |
| `confcheck: 40 configs — 26 exit-parity (2 identical loads) … 0 red` | **holds**, measured at `d65cce0` on kasumi: `confcheck: 40 configs — 26 exit-parity (2 identical loads), 14 named exit deltas (2 lobo-lenient), 0 red` (`kasumi:~/lanes/ws41/gauntlet-trunk.log`) |
| the differential rig | **holds, and it is small**: 3 cases (`static_basic`, `head`, `cond304`), one 79-byte file, one config template per side. **Drift that matters for Range:** lobo already sends `Accept-Ranges: bytes` on every 200 (`head.case`, `static_basic.case`) and ignores `Range`, so today it advertises a feature it does not serve |
| ws40's blocked-directive table "for where Range ranked" | **Drift: Range is not in the table.** It is a request header, not a directive, and `max_ranges` appears in none of the 40 configs. The table cannot rank it; it ranks `user` first (18 configs, sole blocker in 5) |
| item 0b: `named_error` rows for blockers #2–#8 and #13–#21 | **Drift, three rows are not rows.** #8 `worker_rlimit_nofile` is already a `named_error` row (`src/config/table.lu`). #15 (`proxy_pass https://` with no trust anchors) and #17 (`ssl_protocols` without TLSv1.3) are marked "not a directive". So the item adds **13** rows: `deny`, `allow`, `uwsgi_param`, `uwsgi_pass`, `uwsgi_read_timeout`, `charset_types`, `http2`, `http2_max_concurrent_streams`, `proxy_buffer_size`, `proxy_buffers`, `ssl_ecdh_curve`, `ssl_session_tickets`, `auth_request` |
| `docs/directives.md` / README counts | **holds**: 108 rows, 46 implemented, 49 planned, 13 `named_error`; the README's "Compatibility" paragraph types the same three numbers by hand |
| RFC 9110 §14; nginx 1.30.4 as the oracle, `max_ranges` | holds; `max_ranges` has no row in lobo's table (an unknown directive today) |
| wolf-lang#417: no splice/copy_file_range/sendfile | **holds**: open, zero comments. Its number is boreutils' `cat`, not a server |
| (not in the contract) a surface for "the process is unprivileged" | **Missing at the pin.** wolf 0.2.16 has no `getuid`/`geteuid` builtin (`os_*` is cpus, cwd, exe, exit, kill, random, signal, spawn, wait) and `fs_fstat` answers kind, size and mtime only. The one route is `/proc/self/status` on linux. Where it is absent lobo cannot tell, and says so |
| (not in the contract) a positional read for a range | **Missing at the pin**: wolf-lang#426 (no seek, no tell, no pread) is open. A range starting at byte N reads and discards N bytes first |
| the 1 MiB measurement "on the CI runner" | **Drift in the host**: the lane's rules put every build and measurement on kasumi (i9-11900K, 16 threads, linux 7.2.3-cachyos). The number is kasumi's and says so |

## §3: the prediction

### P1: the `user` item (0a)

`user` becomes an implemented row. When `/proc/self/status` says the
effective uid is not 0, `-t` prints nginx's own warning and loads:

    lobo: [warn] the "user" directive makes sense only if the master process runs with super-user privileges, ignored in <file>:<line>

When the effective uid is 0, or cannot be read, `-t` refuses by name,
because lobo has no privilege drop at this pin and running as root
while the config names another user would be silently inert.

The confcheck line at the head of 0a, predicted from ws40's table (the
five configs `user` blocks alone flip lobo's exit 1 → 0):

    confcheck: 40 configs — 25 exit-parity (4 identical loads), 15 named exit deltas (2 lobo-lenient), 0 red

`flask-docs` and `nginx-pkg-oss` move from named delta to identical
load (+2 parity, −2 deltas); `crossplane-messy`, `netbox` and
`synapse-docs` move from parity-on-refusal to a named `oracle-build`
delta (−3 parity, +3 deltas). `IDENTICAL_LOADS` goes 2 → 4, and the
ratchet is red before the constant moves. Falsified by any other line.
The corpus classification ratchet goes from 11 / 6 / 23 to **16 parse-
clean / 1 named-delta / 23 refused**, and the five configs' dry-run
probes go from exit 1 to exit 0 with a routing stanza.

### P2: the `named_error` rows (0b)

13 rows. The five configs whose every load-time blocker then has a row
move from refused to named-delta: `gunicorn-asgi-uwsgi`,
`gunicorn-stress`, `h5bp-no-ssl`, `h5bp-ssl`, `uwsgi-django-docs`. The
ratchet goes to **16 / 6 / 18**. No confcheck exit moves (each still
refuses at `-t`, now by name). Status counts after 0a, 0b and
`max_ranges`: **48 implemented / 49 planned / 25 named_error (122
rows)**, and the README's sentence is checked against the table by the
gauntlet rather than typed.

### P3: the Range cases

**19 cases** join the differential, over the rig's 79-byte
`index.html` (ETag `"6955b900-4f"`). The status each gets from nginx:

| case | request | nginx |
|---|---|---|
| `range_single` | `bytes=0-9` | **206**, `Content-Range: bytes 0-9/79`, 10 bytes |
| `range_suffix` | `bytes=-10` | **206**, `bytes 69-78/79` |
| `range_open` | `bytes=70-` | **206**, `bytes 70-78/79` |
| `range_clamp` | `bytes=70-1000` | **206**, `bytes 70-78/79` (end clamped) |
| `range_multi` | `bytes=0-4,10-14` | **206** `multipart/byteranges`, boundary `00000000000000000001` (a fresh nginx's first temp number, 20 digits) |
| `range_multi_one_unsat` | `bytes=0-4,200-300` | **206** single part `bytes 0-4/79` (the unsatisfiable range is dropped) |
| `range_unsat` | `bytes=100-200` | **416**, `Content-Range: bytes */79`, nginx's error page |
| `range_reversed` | `bytes=5-2` | **416** |
| `range_suffix_zero` | `bytes=-0` | **416** |
| `range_garbage` | `bytes=abc` | **416** |
| `range_other_unit` | `items=0-5` | **200** full, `Accept-Ranges: bytes` |
| `range_overlap_declined` | `bytes=0-78,0-78` | **200** full (the ranges sum past the file) |
| `range_ifrange_etag` | `If-Range: "6955b900-4f"`, `bytes=0-9` | **206** |
| `range_ifrange_stale` | `If-Range: "00000000-4f"`, `bytes=0-9` | **200** full |
| `range_ifrange_date` | `If-Range: <Last-Modified>`, `bytes=0-9` | **206** |
| `range_head` | `HEAD`, `bytes=0-9` | **206**, headers only |
| `range_cond304` | matching `If-Modified-Since` + `bytes=0-9` | **304** (not_modified runs before the range filter) |
| `range_max1` | `max_ranges 1`, `bytes=0-4,10-14` | **200** full |
| `range_max0` | `max_ranges 0`, `bytes=0-9` | **200** full, **no** `Accept-Ranges` |

A 206 carries no `Accept-Ranges`; its headers are Server, Date,
Content-Type, Content-Length, Last-Modified, Connection, ETag,
Content-Range. Tally: **11 × 206, 4 × 416, 3 × 200, 1 × 304.**

At trunk lobo matches **4** of the 19 (`range_other_unit`,
`range_overlap_declined`, `range_ifrange_stale`, `range_cond304`: each
is the answer lobo gives by ignoring `Range`) and diverges on **15**,
two of them because lobo refuses `max_ranges` and never starts.
Falsified if any nginx status differs from the table, or if trunk's
red count is not 15.

The 416 body carries the identity footer (`<hr><center>nginx/1.30.4
</center>`), so its body and `Content-Length` cannot byte-compare
across servers. The differ gains one checked-in, commented
normalization for it, applied only when the footer is the one
difference.

### P4: the 1 MiB cost (the number for wolf-lang#417)

One 1 MiB file, keepalive GETs, one serving process per server
(`worker_processes 1` / nginx `master_process off`), a Python client on
the same host, **five interleaved runs** per arm. Server CPU is
utime + stime off `/proc/<pid>/stat` across the drive; µs is that CPU
over the request count; cores is that CPU over the drive's wall time.
Three arms, so the difference is sendfile's and not the servers':

| arm | µs of server CPU per 1 MiB request (median of 5) | band that falsifies |
|---|---|---|
| nginx, `sendfile on` | **70** | outside 30–150 |
| nginx, `sendfile off` (user-space copy, nginx's own loop) | **220** | outside 110–440 |
| lobo | **400** | outside 200–800 |

So the ask carries **~330 µs per MiB** (lobo − nginx-on), of which
~150 µs is what sendfile alone buys nginx (off − on). Cores: nginx-on
well under 1 core, lobo pinned near **1.0** (the serving process is
the bottleneck at this size).

## §3 against the measurement

Measured on kasumi (i9-11900K, 16 threads, linux 7.2.3-cachyos) on
the tree at `9f78c5f`, the lane's head when each was run.

| prediction | measured | verdict |
|---|---|---|
| P1: `user` warns and loads when unprivileged; the confcheck line `25 exit-parity (4 identical loads), 15 named exit deltas (2 lobo-lenient), 0 red` | exactly that line. Seen red first: CI run 36086771893 at `856bd58` (`confcheck: FAILED — identical loads moved: 4 vs ratchet 2`), with the annotations moved and `IDENTICAL_LOADS` not; before the annotations moved, the five configs each red by name (`kasumi:~/lanes/ws41/red-user-confcheck.log`). The warning is byte for byte nginx's own, which the pinned oracle prints on the same five configs | **held** |
| P1: the classification ratchet 11/6/23 → 16/1/23 | 16/1/23 (`tests/config/corpus_ratchet.lu` at `856bd58`) | **held** |
| P2: 13 rows; ratchet 16/6/18; counts 48/49/25 of 122 | 13 rows; 16/6/18; `122 rows: 48 implemented, 49 planned, 25 named_error` once `max_ranges` landed (121/47 before it). The README sentence is now derived and gated; seen red on a planted drift (`kasumi:~/lanes/ws41/readme-gate-red.log`) | **held** |
| P3: 19 Range cases, each nginx status as tabled | 19 of 19 statuses as tabled; the boundary `00000000000000000001`, the 206 header order and the 416 shape as predicted | **held** per case |
| P3: the tally line "11 × 206, 4 × 416, 3 × 200, 1 × 304" | the table above it says 9 × 206 and 5 × 200; the line was my arithmetic, not the oracle's | **wrong** (the tally, not a status) |
| P3: at trunk lobo matches 4 and diverges on 15, two because `max_ranges` stops it starting | 7/22 green, the same 4 range cases green, 15 red, `range_max0`/`range_max1` "lobo never answered": `kasumi:~/lanes/ws41/diff-red-trunk.log` (a `d65cce0` build with only the new cases added) and CI run 36087334136 at `7330eaa` | **held** |
| P4: nginx `sendfile on`, 70 µs (band 30–150) | **33.8** µs (33.7–34.2) | **held**, at the band's low edge |
| P4: nginx `sendfile off`, 220 µs (band 110–440) | **161.3** µs (161.0–162.6) | **held** |
| P4: lobo, 400 µs (band 200–800) | **187.2** µs (186.2–189.1) | **wrong**: below the band. lobo's copy loop is 26 µs (16 %) above nginx's own, not 2× it |
| P4: cores — nginx-on well under 1, lobo near 1.0 | nginx-on 0.356, nginx-copy 0.855, lobo 0.872 | **held** for nginx; lobo is 0.87, not saturated — the four curl clients reading 1 MiB each are the other half of the loopback copy |

The 1 MiB table (`tools/lobo-mib-bench 5 4000 4`, five interleaved
rounds with the arm order rotated each round, 4000 requests per arm
per round, raw rows `kasumi:~/lanes/ws41/mib-results.tsv`, sha256
`e65b6179…`):

| arm | µs server CPU / 1 MiB request (median, min–max) | user : system ticks | cores |
|---|---|---|---|
| nginx, `sendfile on` | 33.8 (33.7–34.2) | 4 : 63 | 0.356 |
| nginx, `sendfile off` | 161.3 (161.0–162.6) | 18 : 304 | 0.855 |
| lobo | 187.2 (186.2–189.1) | 68 : 306 | 0.872 |

**The number the ask carries: lobo spends 153 µs more server CPU than
nginx with sendfile on every 1 MiB it serves — 5.5× — and 127 µs of
that gap is what sendfile saves nginx itself.** The copy is the cost,
not lobo: against nginx's own user-space loop lobo is within 16 %.
Both copy arms spend over 80 % of their CPU in the kernel (the two
copies across the user boundary); sendfile removes one of them and
the user-space buffer with it. 22 of the corpus's 40 configs say
`sendfile on`.
