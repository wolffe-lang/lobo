# ws40 — the prediction, committed before the first config lands

Wave 47, subwave 3. Written 2026-09-25 on lobo trunk `bba69d3`. The
pins are wolf 0.2.16 (`93a5fe5`), lupin 0.1.38 (`ba357aa`) and std
`070884c`, and none of them moves. The oracle pin is nginx 1.30.4
(`tests/differential/NGINX-PIN`), and it does not move either. When
this file is committed, no new config is in `tests/config-corpus/` and
none has been run through `lobo -t` or `nginx -t`. The measurements
land in `tests/config-corpus/INDEX.md` next to these lines, whether
they are right or wrong.

## §2: the contract's inputs, re-derived against origin

| input, as the contract states it | what origin says |
|---|---|
| lobo trunk at ws39's release | **holds**: `v0.1.1` is `7c87e0a`, and trunk is `bba69d3` (the `+dev` flip, lobo#35). CI run 36081001619 at `bba69d3` (PR #35) is green. Push run 36082162339 was in progress at launch |
| `tests/config-corpus/` has **8** entries | **holds at 8**. **Drift:** 7 of the 8 are `source=synthetic`. Only `distro-default` (nginx's own `conf/nginx.conf`) is a real config. W2 says "a public corpus of REAL nginx.confs", and 1 of the 8 at trunk is one |
| `docs/directives.md` has 108 rows | **holds**: 46 implemented, 49 planned, 13 named_error |
| the pinned nginx 1.30.4 loads each config as the oracle | **Drift, and it decides the fifth prediction.** The pin's configure line is `--without-http_rewrite_module --without-http_gzip_module --with-http_ssl_module`, with no PCRE. So `return`, `rewrite`, `if`, `set`, `gzip*` and every regex location are **unknown or refused on the oracle**. At trunk, `tools/lobo-confcheck` already reports **5 of 8 configs that load on lobo and not on the pinned nginx**: certbot-vhost, map-and-if, php-fpm, redirect-farm and static-site. Each is annotated `oracle-build` (`kasumi:~/lanes/ws40/gauntlet-trunk.log`). The contract's "predict zero" for that direction was already false before this lane started, against the pinned binary |
| the ratchet is new work | **Drift:** it exists. `tests/config/corpus_ratchet.lu` gates 8 configs (7 parse-clean, 1 named-delta, 0 silent). `tools/lobo-confcheck` gates exit parity per config against a checked-in `# lobo-corpus: oracle-exit=N lobo-exit=M [delta=…]` header, 3 of them exit-parity at trunk. `tests/dryrun/probe_ratchet.lu` requires **one dry-run probe per corpus config** (9 probes). This lane extends all three rather than adding a fourth |
| ws01's corpus policy | `sprints/wws/00-scaffolding/ws01-the-config-carries.md` §4 allows sources "whose license permits redistribution … provenance line per file". §3 says "EVERY directive nginx users write has a row", "Everything else in a real config gets a table row with `named_error` + the honest note", and "A directive with NO row is" a load error. So a named delta row here is a `named_error` row in `src/config/table.lu`, which regenerates `docs/directives.md`. It refuses by name and **implements nothing** |

Two more facts shape the measurement.

- **`nginx -t` is not a pure parse.** It binds every `listen`, so an
  unprivileged oracle cannot take 80 or 443. It opens every log file
  and every certificate. `distro-default` already carries the one edit
  this forces (`listen 80 -> 18080`). Every new config gets the same
  mechanical, stated rewrite: privileged port `N` becomes `18000+N`;
  `/etc/nginx/…` becomes prefix-relative; `/var/log/…` and other log
  paths become `logs/…`; certificate paths point at a test pair copied
  from `certbot-vhost`. The edits are listed per config in the index.
- **`lobo -t` stops at the first error**, and the named-delta class
  reports only its first row on stderr. So the blocked-directive
  table comes from a peel loop, a measurement script that is never
  committed as a gate. The loop removes the reported blocker from a
  scratch copy and re-runs, until the config loads or stops at
  something that is not a directive.

A second nginx, the measurement-only **stock** build, answers the
question the pinned oracle cannot. It is 1.30.4 from the pinned
tarball (sha256 checked), built with rewrite, gzip and PCRE on, plus
`--with-http_ssl_module --with-http_v2_module --with-http_realip_module
--with-http_stub_status_module --with-http_sub_module
--with-http_gzip_static_module --with-http_auth_request_module
--with-stream --with-stream_ssl_module`. It lives at
`kasumi:~/lanes/ws40/nginx-stock/nginx`. It is not a pin and it is not
in CI; the gate stays on the pinned binary.

## §3: the prediction

The corpus goes from 8 to **40**: 32 new configs from permissively
licensed public repositories. The sources are nginx's own packaging
(`nginx/pkg-oss`, BSD-2-Clause), h5bp `server-configs-nginx` (MIT),
Ubuntu 14.04's stock nginx as carried in certbot's test data
(Apache-2.0), Nginx Proxy Manager (MIT), Zulip (Apache-2.0), NetBox
(Apache-2.0), Apache Superset (Apache-2.0), gunicorn (MIT), nginx's
njs-examples (BSD-2-Clause), crossplane's parser fixtures (Apache-2.0),
and the nginx blocks in the Flask, Puma, Laravel, Synapse, JupyterHub
and uWSGI docs.

- **P1: size.** 40 configs. Falsified if fewer than 38 land.
- **P2: identical loads** (pinned `nginx -t` exit 0 **and** `lobo -t`
  exit 0). There are 2 at trunk (distro-default, reverse-proxy). I
  predict **6 of 40**. Falsified outside 3 to 9. Most real configs
  carry `user`, a regex location, `return` or `gzip`. The first is a
  lobo `named_error` row and the last three are unknown to the pinned
  oracle.
- **P3: fail on a named delta.** Of the 32 new configs, **24** exit 1
  on `lobo -t` with a named row (a `named_error` row, old or added
  here). Falsified outside 19 to 29. **Zero** fail silently, meaning
  structural error, unnamed outcome or crash. Falsified by one.
- **P4: the top five missing directives by configs blocked**, counted
  over every blocker in each config after peeling, not only the
  first:
  1. `user`: a named_error row already, and I expect it in about 12
     configs
  2. `http2`: the `listen … http2` parameter and the directive
  3. `types_hash_max_size` / `server_names_hash_bucket_size`: the
     hash-sizing pair
  4. `uwsgi_pass` / `uwsgi_param`
  5. `js_import` / `js_content`: njs

  Falsified if fewer than three of these five appear in the measured
  top five.
- **P5: lobo loads and nginx does not.** Against the **stock** build I
  predict **zero**; crossplane's deliberately broken fixtures must be
  refused by both. Falsified by one. Against the **pinned** oracle I
  predict **at least 8**: trunk's 5 plus new ones on
  rewrite/gzip/PCRE. The contract's "predict zero" was about the
  pinned binary, so it is recorded here as **already false at
  trunk**.
