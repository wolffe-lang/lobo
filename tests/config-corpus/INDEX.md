# The real-config corpus: index

W2's claim is that a public corpus of real nginx.confs either loads
on lobo with identical observable routing or fails with a named,
documented delta. This file measures that claim for every config under
`tests/config-corpus/`. The ws01 seed has 8 configs, 7 of them
synthetic. ws40 (2026-09-25) added 32 real ones from permissively
licensed public repositories.

## The rules every entry follows

- **Licence first.** Each entry's `nginx.conf` starts with a
  `# lobo-corpus: source=… license=…` line that names the source file at
  a pinned commit, plus an `edits=` line. Only permissive licences
  appear: MIT, BSD-2-Clause, BSD-3-Clause and Apache-2.0. Nothing comes
  from a private host. The certbot repository's `79-configs` set was
  **not** used: it is scraped third-party sites with real domains.
  Zulip's production vhost was not used either: it needs Zulip's
  ERB-rendered includes.
- **What was stripped.** Only hostnames that nginx would resolve at
  `-t` and that exist only inside a container network:
  `host.docker.internal` in superset, and the docker-compose service
  names `gunicorn`, `gunicorn-*` in five gunicorn entries. Each became
  `127.0.0.1` on the same port. No config carried a key, token or
  password. The only key material in the corpus is lobo's own TEST
  Ed25519 pair (copied from `certbot-vhost/live/example.org/`) and
  Zulip's published DH group (`jupyterhub-docs/certs/dhparam.pem`,
  Apache-2.0).
- **What was edited, and why.** `nginx -t` is not a pure parse. It
  binds every `listen`, and it opens every log, the pid file and every
  certificate. So, mechanically: a privileged port `N` becomes
  `18000+N`; `/etc/nginx/` paths become prefix-relative; log paths
  become `logs/`; an absolute `pid` becomes `logs/nginx.pid`;
  certificate paths point at the TEST pair. A vhost-only source (one
  `server {}` file) sits in `conf.d/` under nginx's own packaged
  `nginx.conf` (nginx/pkg-oss, BSD-2-Clause), which is what the
  official image and packages put around it. Each entry's `edits=`
  line lists exactly what it received.

## The oracles

- **pinned**: the differential's nginx 1.30.4
  (`tests/differential/NGINX-PIN`). It is built
  `--without-http_rewrite_module --without-http_gzip_module
  --with-http_ssl_module`, with no PCRE and no HTTP/2. This is what CI
  gates on, through `tools/lobo-confcheck`.
- **stock**: the same pinned tarball (sha256 checked), built on kasumi
  with rewrite, gzip and PCRE on, plus `--with-http_ssl_module
  --with-http_v2_module --with-http_realip_module
  --with-http_stub_status_module --with-http_sub_module
  --with-http_gzip_static_module --with-http_auth_request_module
  --with-stream --with-stream_ssl_module` (sha256 `376c6de4…`). It is a
  measurement only, not a pin, and it is not in CI. It answers the
  question the pinned build cannot: would a normal nginx load this?
- **lobo**: `lobo -t` at `bba69d3`. ws40 changed nothing in `src/`.
- **The peel**: `lobo -t` stops at its first refusal. To list
  *everything* that blocks a config, a measurement script
  (`kasumi:~/lanes/ws40/measure.py`, sha256 `dfa28eec…`, never a
  gate) removes the reported directive from a scratch copy and re-runs,
  until the config loads or stops on something it cannot remove. The
  raw results are `kasumi:~/lanes/ws40/measure-trunk.jsonl` (sha256
  `2e1ba025…`), one line per config. One entry was renamed after the
  measurement: `ubuntu-1.4.6-default` became `ubuntu-trusty-default`,
  because `tools/lobo-dryrun` reads a probe's config name up to the
  first dot.

## The count (ratcheted)

| class | configs | gate |
|---|---|---|
| **identical load**: pinned `-t` 0 and lobo `-t` 0 | **4** (distro-default, reverse-proxy; flask-docs and nginx-pkg-oss since ws41's `user`) | `IDENTICAL_LOADS=4`, `tools/lobo-confcheck` |
| loads on lobo and on stock nginx; the pinned build lacks rewrite, gzip, PCRE or HTTP/2 | 10 (crossplane-messy, netbox and synapse-docs joined at ws41) | the per-config annotation, `oracle-build` |
| **lobo-lenient**: lobo loads, and every nginx build refuses | **2** (certbot-vhost, crossplane-empty-value-map; lobo#38) | `LOBO_LENIENT=2`, `tools/lobo-confcheck` |
| lobo refuses, stock nginx loads | 16 | per-config annotation + the blocked table below |
| both refuse | 8 | per-config annotation |
| **total** | **40** | `tests/config/corpus_ratchet.lu`: 16 parse-clean / 1 named-delta / 23 refused-by-name / **0 silent** |

Every config's exits are pinned in its own `# lobo-corpus: oracle-exit=N
lobo-exit=M delta=…` line. `tools/lobo-confcheck` runs both binaries on
every entry and reds on any exit that differs from its annotation. So a
lobo change that flips one config reds by name, and a hand edit that
lowers the count reds on the constant. Against the stock build, lobo
loads 16 of 40 (11 before ws41's `user`) and nginx loads 30 of 40.

**Identical routing.** Every entry carries a `lobo -t --request`
dry-run probe under `tests/dryrun/probes/` (41 probes, gated by
`tools/lobo-dryrun` and `tests/dryrun/probe_ratchet.lu`). A refused
config predicts nothing (exit 1, empty). For a config that loads, the
probe pins lobo's routing decision and names every directive lobo
parses but does not apply. That is where the routing deltas show:
`crossplane-simple` and `crossplane-with-comments` answer
`return 200 "foo bar baz"` on nginx, and lobo predicts a 404 because
`return` is a planned row. Every loading config also gets the
host-blind `server_name` delta. **Not measured by ws40:** a live
request-by-request comparison against nginx for each corpus config. The
differential harness does that on its own configs, not on these. It is
a named gap for the lane that implements `return` and `server_name`.

## Per config

| config | source | licence | pinned `-t` | stock `-t` | lobo `-t` | verdict | what lobo refuses (peeled, in order; `*` = not a missing directive) |
|---|---|---|---|---|---|---|---|
| `certbot-vhost` | synthetic | n/a-synthetic | 1 | 1 | 0 | **lobo-lenient** | — |
| `distro-default` | nginx-1.30.4 | BSD-2-Clause | 0 | 0 | 0 | **identical load** | — |
| `lua-openresty` | synthetic | n/a-synthetic | 1 | 1 | 1 | both refuse | `lua_shared_dict`, `content_by_lua_block` |
| `map-and-if` | synthetic | n/a-synthetic | 1 | 0 | 0 | loads on both (pinned build lacks a module) | — |
| `php-fpm` | synthetic | n/a-synthetic | 1 | 0 | 0 | loads on both (pinned build lacks a module) | — |
| `redirect-farm` | synthetic | n/a-synthetic | 1 | 0 | 0 | loads on both (pinned build lacks a module) | — |
| `reverse-proxy` | synthetic | n/a-synthetic | 0 | 0 | 0 | **identical load** | — |
| `static-site` | synthetic | n/a-synthetic | 1 | 0 | 0 | loads on both (pinned build lacks a module) | — |
| `certbot-nginx-fixture` | [certbot/certbot](https://github.com/certbot/certbot/blob/485649333422392901e7ef891630f0129985df8e/certbot/src/certbot/_internal/tests/plugins/nginx/testdata/etc_nginx/nginx.conf) | Apache-2.0 | 1 | 1 | 1 | both refuse | `empty`, `ssl`, `deny`, `user`, `listen*`, `ssl_certificate*` |
| `crossplane-empty-value-map` | [nginxinc/crossplane](https://github.com/nginxinc/crossplane/blob/16de93a158661719f002c5f53711926176cedbc7/tests/configs/empty-value-map/nginx.conf) | Apache-2.0 | 1 | 1 | 0 | **lobo-lenient** | — |
| `crossplane-includes-globbed` | [nginxinc/crossplane](https://github.com/nginxinc/crossplane/blob/16de93a158661719f002c5f53711926176cedbc7/tests/configs/includes-globbed/nginx.conf) | Apache-2.0 | 1 | 0 | 0 | loads on both (pinned build lacks a module) | — |
| `crossplane-includes-regular` | [nginxinc/crossplane](https://github.com/nginxinc/crossplane/blob/16de93a158661719f002c5f53711926176cedbc7/tests/configs/includes-regular/nginx.conf) | Apache-2.0 | 1 | 1 | 1 | both refuse | `include*` |
| `crossplane-messy` | [nginxinc/crossplane](https://github.com/nginxinc/crossplane/blob/16de93a158661719f002c5f53711926176cedbc7/tests/configs/messy/nginx.conf) | Apache-2.0 | 1 | 0 | 0 | loads on both (pinned build lacks a module; `user` resolved at ws41) | — |
| `crossplane-quote-behavior` | [nginxinc/crossplane](https://github.com/nginxinc/crossplane/blob/16de93a158661719f002c5f53711926176cedbc7/tests/configs/quote-behavior/nginx.conf) | Apache-2.0 | 1 | 1 | 1 | both refuse | `outer-quote*`, `*` |
| `crossplane-russian-text` | [nginxinc/crossplane](https://github.com/nginxinc/crossplane/blob/16de93a158661719f002c5f53711926176cedbc7/tests/configs/russian-text/nginx.conf) | Apache-2.0 | 0 | 0 | 1 | lobo refuses, nginx loads | `env` |
| `crossplane-simple` | [nginxinc/crossplane](https://github.com/nginxinc/crossplane/blob/16de93a158661719f002c5f53711926176cedbc7/tests/configs/simple/nginx.conf) | Apache-2.0 | 1 | 0 | 0 | loads on both (pinned build lacks a module) | — |
| `crossplane-with-comments` | [nginxinc/crossplane](https://github.com/nginxinc/crossplane/blob/16de93a158661719f002c5f53711926176cedbc7/tests/configs/with-comments/nginx.conf) | Apache-2.0 | 1 | 0 | 0 | loads on both (pinned build lacks a module) | — |
| `flask-docs` | [pallets/flask](https://github.com/pallets/flask/blob/d73fa1cdcbd8b1465c151db8924ba58b1dd14e35/docs/deploying/nginx.rst) | BSD-3-Clause | 0 | 0 | 0 | **identical load** (since ws41's `user`) | — |
| `gunicorn-asgi-compliance` | [benoitc/gunicorn](https://github.com/benoitc/gunicorn/blob/afc7d2fd5dd9f1de455b1be6c10044030c0adf8e/tests/docker/asgi_compliance/nginx.conf) | MIT | 1 | 0 | 1 | lobo refuses, nginx loads | `chunked_transfer_encoding`, `proxy_next_upstream`, `proxy_next_upstream_tries`, `proxy_buffer_size`, `proxy_buffers`, `http2`, `http2_max_concurrent_streams` |
| `gunicorn-asgi-uwsgi` | [benoitc/gunicorn](https://github.com/benoitc/gunicorn/blob/afc7d2fd5dd9f1de455b1be6c10044030c0adf8e/tests/docker/test_asgi_uwsgi/nginx.conf) | MIT | 1 | 0 | 1 | lobo refuses, nginx loads | `uwsgi_pass`, `uwsgi_param`, `user` |
| `gunicorn-example` | [benoitc/gunicorn](https://github.com/benoitc/gunicorn/blob/afc7d2fd5dd9f1de455b1be6c10044030c0adf8e/examples/nginx.conf) | MIT | 1 | 0 | 1 | lobo refuses, nginx loads | `accept_mutex`, `user`, `client_max_body_size*` |
| `gunicorn-http2` | [benoitc/gunicorn](https://github.com/benoitc/gunicorn/blob/afc7d2fd5dd9f1de455b1be6c10044030c0adf8e/tests/docker/http2/nginx.conf) | MIT | 1 | 0 | 1 | lobo refuses, nginx loads | `http2`, `http2_max_concurrent_streams`, `early_hints`, `proxy_buffer_size`, `proxy_buffers`, `proxy_pass*` |
| `gunicorn-stress` | [benoitc/gunicorn](https://github.com/benoitc/gunicorn/blob/afc7d2fd5dd9f1de455b1be6c10044030c0adf8e/tests/docker/stress/nginx.conf) | MIT | 1 | 0 | 1 | lobo refuses, nginx loads | `http2`, `http2_max_concurrent_streams`, `uwsgi_read_timeout`, `uwsgi_pass`, `uwsgi_param`, `proxy_pass*` |
| `gunicorn-uwsgi` | [benoitc/gunicorn](https://github.com/benoitc/gunicorn/blob/afc7d2fd5dd9f1de455b1be6c10044030c0adf8e/tests/docker/uwsgi/nginx.conf) | MIT | 0 | 0 | 1 | lobo refuses, nginx loads | `uwsgi_buffer_size`, `uwsgi_buffers`, `uwsgi_busy_buffers_size`, `uwsgi_read_timeout`, `uwsgi_pass`, `uwsgi_param` |
| `h5bp-no-ssl` | [h5bp/server-configs-nginx](https://github.com/h5bp/server-configs-nginx/blob/d2f2c3e2fac76f429adb738894499b8fb756d2f3/nginx.conf) | MIT | 1 | 0 | 1 | lobo refuses, nginx loads | `charset_types`, `deny`, `user`, `worker_rlimit_nofile` |
| `h5bp-ssl` | [h5bp/server-configs-nginx](https://github.com/h5bp/server-configs-nginx/blob/d2f2c3e2fac76f429adb738894499b8fb756d2f3/nginx.conf) | MIT | 1 | 0 | 1 | lobo refuses, nginx loads | `charset_types`, `ssl_session_tickets`, `ssl_ecdh_curve`, `deny`, `user`, `worker_rlimit_nofile`, `ssl_protocols*` |
| `h5bp-test-vhosts` | [h5bp/server-configs-nginx](https://github.com/h5bp/server-configs-nginx/blob/d2f2c3e2fac76f429adb738894499b8fb756d2f3/nginx.conf) | MIT | 1 | 0 | 1 | lobo refuses, nginx loads | `charset_types`, `ssl_session_tickets`, `ssl_ecdh_curve`, `deny`, `gzip_static`, `user`, `worker_rlimit_nofile`, `ssl_protocols*` |
| `jupyterhub-docs` | [jupyterhub/jupyterhub](https://github.com/jupyterhub/jupyterhub/blob/9abe5fb83f4c21754ed12adac2f834c33ee9ea39/docs/source/howto/configuration/config-proxy.md) | BSD-3-Clause | 1 | 1 | 1 | both refuse | `ssl`, `allow`, `user` |
| `laravel-docs` | [laravel/docs](https://github.com/laravel/docs/blob/eff8739e9090c2a0216fefac8e33dacdd689f8f6/deployment.md) | MIT | 1 | 0 | 1 | lobo refuses, nginx loads | `log_not_found`, `fastcgi_buffer_size`, `fastcgi_buffers`, `fastcgi_busy_buffers_size`, `fastcgi_hide_header`, `deny`, `user` |
| `netbox` | [netbox-community/netbox](https://github.com/netbox-community/netbox/blob/b56c866d4c23e8a9a4ecd4c0d85a04b4e83c286c/contrib/nginx.conf) | Apache-2.0 | 1 | 0 | 0 | loads on both (pinned build lacks a module; `user` resolved at ws41) | — |
| `nginx-pkg-oss` | [nginx/pkg-oss](https://github.com/nginx/pkg-oss/blob/d16a981d5921b9d27985a24998d3438fb73bb1d7/debian/debian/nginx.conf) | BSD-2-Clause | 0 | 0 | 0 | **identical load** (since ws41's `user`) | — |
| `nginx-proxy-manager` | [NginxProxyManager/nginx-proxy-manager](https://github.com/NginxProxyManager/nginx-proxy-manager/blob/2cfd3395cf979b901cecb390dd3d78810c46b596/docker/rootfs/etc/nginx/nginx.conf) | MIT | 1 | 0 | 1 | lobo refuses, nginx loads | `pcre_jit`, `client_body_temp_path`, `proxy_ignore_client_abort`, `server_names_hash_bucket_size`, `proxy_cache_path`, `set_real_ip_from`, `real_ip_header`, `real_ip_recursive`, `if_modified_since`, `proxy_cache_key`, `proxy_ignore_headers`, `proxy_hide_header`, `proxy_cache_bypass`, `proxy_no_cache`, `proxy_cache_use_stale`, `if*`, `auth_basic`, `auth_request`, `allow`, `ssl_reject_handshake`, `stream`, `daemon`, `user`, `listen*`, (stop: unknown "upstream_cache_status" variable) |
| `njs-complex-redirects` | [nginx/njs-examples](https://github.com/nginx/njs-examples/blob/d5de982e5f720f8aaaad9996080209195fee01b2/conf/http/complex_redirects.conf) | BSD-2-Clause | 1 | 1 | 1 | both refuse | `load_module`, `js_path`, `js_import`, `js_content`, `auth_request`, `auth_request_set`, `internal` |
| `njs-decode-uri` | [nginx/njs-examples](https://github.com/nginx/njs-examples/blob/d5de982e5f720f8aaaad9996080209195fee01b2/conf/http/decode_uri.conf) | BSD-2-Clause | 1 | 1 | 1 | both refuse | `load_module`, `js_path`, `js_import`, `js_set`, `js_content` |
| `njs-hello` | [nginx/njs-examples](https://github.com/nginx/njs-examples/blob/d5de982e5f720f8aaaad9996080209195fee01b2/conf/http/hello.conf) | BSD-2-Clause | 1 | 1 | 1 | both refuse | `load_module`, `js_path`, `js_import`, `js_content` |
| `puma-docs` | [puma/puma](https://github.com/puma/puma/blob/306daddfd07fdf0ca902eb7ea89ceb7dd6139050/docs/nginx.md) | BSD-3-Clause | 1 | 0 | 1 | lobo refuses, nginx loads | `break`, `user` |
| `superset` | [apache/superset](https://github.com/apache/superset/blob/599026a0e5a82f9728a333aea0e07b6a7bf8f771/docker/nginx/nginx.conf) | Apache-2.0 | 1 | 0 | 1 | lobo refuses, nginx loads | `output_buffers`, `port_in_redirect`, `user`, (stop: log format variable "$connection_requests" is not implemente) |
| `synapse-docs` | [matrix-org/synapse](https://github.com/matrix-org/synapse/blob/be65a8ec0195955c15fdb179c9158b187638e39a/docs/reverse_proxy.md) | Apache-2.0 | 1 | 0 | 0 | loads on both (pinned build lacks HTTP/2; `user` resolved at ws41) | — |
| `ubuntu-trusty-default` | [certbot/certbot](https://github.com/certbot/certbot/blob/485649333422392901e7ef891630f0129985df8e/certbot/src/certbot/_internal/tests/plugins/nginx/testdata/etc_nginx/ubuntu_nginx_1_4_6/default_vhost/nginx/nginx.conf) | Apache-2.0 | 1 | 0 | 1 | lobo refuses, nginx loads | `types_hash_max_size`, `user` |
| `uwsgi-django-docs` | [unbit/uwsgi-docs](https://github.com/unbit/uwsgi-docs/blob/5784c30866a94942a5200db4d5f6c2850afb1caa/tutorials/Django_and_nginx.rst) | MIT | 0 | 0 | 1 | lobo refuses, nginx loads | `uwsgi_pass`, `uwsgi_param`, `user` |

## Provenance: source at a pinned commit, and what was edited or stripped

| config | pinned source | what was edited or stripped |
|---|---|---|
| `certbot-vhost` | synthetic (the certbot-managed vhost shape: HTTP-01 webroot location + the ssl_certificate pair certbot writes; parse-clean here is the W4 compat story. ws05: the pair is REAL — a TEST Ed25519 chain under live/<domain>/ in the certbot layout, relative to the prefix, so lobo -t exercises the whole load+pair-match path; the /etc/letsencrypt absolute paths became prefix-relative for hermeticity, same layout) license=n/a-synthetic | ws01 seed; ws40 corrected its annotation only (lobo-lenient, lobo#38) |
| `distro-default` | nginx-1.30.4 tarball conf/nginx.conf (verbatim below this header, ONE edit: listen 80 -> 18080 because nginx -t BINDS its listen sockets and the unprivileged oracle cannot take 80 — probed via confcheck, bind() 13: Permission denied) license=BSD-2-Clause (nginx's own LICENSE) | ws01 seed (synthetic or verbatim, see its header); unchanged by ws40 |
| `lua-openresty` | synthetic (the OpenResty *_by_lua_block shape — the named_error exhibit: lobo refuses BY NAME with the block brace-skipped; the class-C posture, never silent) license=n/a-synthetic | ws01 seed (synthetic or verbatim, see its header); unchanged by ws40 |
| `map-and-if` | synthetic (the map + if footgun exhibits: LOBO-L001 fires on the if-in-location, LOBO-L003 on the alias off-by-slash) license=n/a-synthetic | ws01 seed (synthetic or verbatim, see its header); unchanged by ws40 |
| `php-fpm` | synthetic (the fastcgi/php-fpm shape from nginx docs + distro fastcgi snippets; parse-only at ws01) license=n/a-synthetic | ws01 seed (synthetic or verbatim, see its header); unchanged by ws40 |
| `redirect-farm` | synthetic (the redirect/rewrite farm shape: apex-to-www, legacy paths, trailing-slash normalization) license=n/a-synthetic | ws01 seed (synthetic or verbatim, see its header); unchanged by ws40 |
| `reverse-proxy` | synthetic (composed from nginx docs' proxying + upstream keepalive patterns; also the LOBO-L002 lint exhibit) license=n/a-synthetic | ws01 seed (synthetic or verbatim, see its header); unchanged by ws40 |
| `static-site` | synthetic (composed from nginx docs' documented patterns: gzip, expires, autoindex) license=n/a-synthetic | ws01 seed (synthetic or verbatim, see its header); unchanged by ws40 |
| `certbot-nginx-fixture` | https://github.com/certbot/certbot/blob/485649333422392901e7ef891630f0129985df8e/certbot/src/certbot/_internal/tests/plugins/nginx/testdata/etc_nginx/nginx.conf + foo.conf, server.conf, mime.types, sites-enabled/* (certbot's nginx-plugin parser fixture; deliberately odd: an empty{} block, a second http{} via foo.conf) license=Apache-2.0 | listen 80/443 -> 18080/18443 on listen lines; nothing stripped |
| `crossplane-empty-value-map` | https://github.com/nginxinc/crossplane/blob/16de93a158661719f002c5f53711926176cedbc7/tests/configs/empty-value-map/nginx.conf (+ every file beside it; crossplane's parser fixture) license=Apache-2.0 | none beyond this header; nothing stripped |
| `crossplane-includes-globbed` | https://github.com/nginxinc/crossplane/blob/16de93a158661719f002c5f53711926176cedbc7/tests/configs/includes-globbed/nginx.conf (+ every file beside it; crossplane's parser fixture) license=Apache-2.0 | none beyond this header; nothing stripped |
| `crossplane-includes-regular` | https://github.com/nginxinc/crossplane/blob/16de93a158661719f002c5f53711926176cedbc7/tests/configs/includes-regular/nginx.conf (+ every file beside it; crossplane's parser fixture) license=Apache-2.0 | none beyond this header; nothing stripped |
| `crossplane-messy` | https://github.com/nginxinc/crossplane/blob/16de93a158661719f002c5f53711926176cedbc7/tests/configs/messy/nginx.conf (+ every file beside it; crossplane's parser fixture) license=Apache-2.0 | none beyond this header; nothing stripped |
| `crossplane-quote-behavior` | https://github.com/nginxinc/crossplane/blob/16de93a158661719f002c5f53711926176cedbc7/tests/configs/quote-behavior/nginx.conf (+ every file beside it; crossplane's parser fixture) license=Apache-2.0 | none beyond this header; nothing stripped |
| `crossplane-russian-text` | https://github.com/nginxinc/crossplane/blob/16de93a158661719f002c5f53711926176cedbc7/tests/configs/russian-text/nginx.conf (+ every file beside it; crossplane's parser fixture) license=Apache-2.0 | none beyond this header; nothing stripped |
| `crossplane-simple` | https://github.com/nginxinc/crossplane/blob/16de93a158661719f002c5f53711926176cedbc7/tests/configs/simple/nginx.conf (+ every file beside it; crossplane's parser fixture) license=Apache-2.0 | none beyond this header; nothing stripped |
| `crossplane-with-comments` | https://github.com/nginxinc/crossplane/blob/16de93a158661719f002c5f53711926176cedbc7/tests/configs/with-comments/nginx.conf (+ every file beside it; crossplane's parser fixture) license=Apache-2.0 | none beyond this header; nothing stripped |
| `flask-docs` | https://github.com/pallets/flask/blob/d73fa1cdcbd8b1465c151db8924ba58b1dd14e35/docs/deploying/nginx.rst (the code-block under 'nginx'), as conf.d/site.conf, wrapped in nginx/pkg-oss's packaged nginx.conf (BSD-2-Clause, d16a981d5921b9d27985a24998d3438fb73bb1d7) license=BSD-3-Clause | listen privileged N -> 18000+N; wrapper paths prefix-relative, logs -> logs/, pid -> logs/nginx.pid; nothing stripped |
| `gunicorn-asgi-compliance` | https://github.com/benoitc/gunicorn/blob/afc7d2fd5dd9f1de455b1be6c10044030c0adf8e/tests/docker/asgi_compliance/nginx.conf (gunicorn's docker test rig) license=MIT | /etc/nginx/ -> prefix-relative; /var/log/nginx/ -> logs/; an absolute pid -> logs/nginx.pid (nginx -t opens it); /certs/server.{crt,key} -> certs/ (lobo's TEST pair); STRIPPED: docker-compose service hostnames (gunicorn, gunicorn-*) -> 127.0.0.1, same ports |
| `gunicorn-asgi-uwsgi` | https://github.com/benoitc/gunicorn/blob/afc7d2fd5dd9f1de455b1be6c10044030c0adf8e/tests/docker/test_asgi_uwsgi/nginx.conf as conf.d/default.conf (the official image's slot), wrapped in nginx/pkg-oss's packaged nginx.conf (BSD-2-Clause, d16a981d5921b9d27985a24998d3438fb73bb1d7) license=MIT | listen 80 -> 18080; wrapper paths prefix-relative, logs -> logs/, pid -> logs/nginx.pid; STRIPPED: the compose service hostname gunicorn -> 127.0.0.1 |
| `gunicorn-example` | https://github.com/benoitc/gunicorn/blob/afc7d2fd5dd9f1de455b1be6c10044030c0adf8e/examples/nginx.conf license=MIT | /var/log/nginx/ -> logs/; an absolute pid -> logs/nginx.pid (nginx -t opens it); listen 80 -> 18080; mime.types is nginx-1.30.4's; nothing stripped |
| `gunicorn-http2` | https://github.com/benoitc/gunicorn/blob/afc7d2fd5dd9f1de455b1be6c10044030c0adf8e/tests/docker/http2/nginx.conf (gunicorn's docker test rig) license=MIT | /etc/nginx/ -> prefix-relative; /var/log/nginx/ -> logs/; an absolute pid -> logs/nginx.pid (nginx -t opens it); /certs/server.{crt,key} -> certs/ (lobo's TEST pair); STRIPPED: docker-compose service hostnames (gunicorn, gunicorn-*) -> 127.0.0.1, same ports |
| `gunicorn-stress` | https://github.com/benoitc/gunicorn/blob/afc7d2fd5dd9f1de455b1be6c10044030c0adf8e/tests/docker/stress/nginx.conf (gunicorn's docker test rig) license=MIT | /etc/nginx/ -> prefix-relative; /var/log/nginx/ -> logs/; an absolute pid -> logs/nginx.pid (nginx -t opens it); /certs/server.{crt,key} -> certs/ (lobo's TEST pair); STRIPPED: docker-compose service hostnames (gunicorn, gunicorn-*) -> 127.0.0.1, same ports |
| `gunicorn-uwsgi` | https://github.com/benoitc/gunicorn/blob/afc7d2fd5dd9f1de455b1be6c10044030c0adf8e/tests/docker/uwsgi/nginx.conf (gunicorn's docker test rig) license=MIT | /etc/nginx/ -> prefix-relative; /var/log/nginx/ -> logs/; an absolute pid -> logs/nginx.pid (nginx -t opens it); /certs/server.{crt,key} -> certs/ (lobo's TEST pair); STRIPPED: docker-compose service hostnames (gunicorn, gunicorn-*) -> 127.0.0.1, same ports |
| `h5bp-no-ssl` | https://github.com/h5bp/server-configs-nginx/blob/d2f2c3e2fac76f429adb738894499b8fb756d2f3/nginx.conf + h5bp/ + conf.d/no-ssl.default.conf + conf.d/templates/no-ssl.example.com.conf (the README's http-only enablement) license=MIT | /var/log/nginx/ -> logs/; an absolute pid -> logs/nginx.pid (nginx -t opens it); listen 80 -> 18080 (and [::]:80 -> [::]:18080); nothing stripped |
| `h5bp-ssl` | https://github.com/h5bp/server-configs-nginx/blob/d2f2c3e2fac76f429adb738894499b8fb756d2f3/nginx.conf + h5bp/ + conf.d/.default.conf (enabled as conf.d/default.conf, per the README) + conf.d/templates/example.com.conf license=MIT | /var/log/nginx/ -> logs/; an absolute pid -> logs/nginx.pid (nginx -t opens it); listen 443 -> 18443; h5bp/tls/certificate_files.conf now reads certs/default.{crt,key}, holding lobo's TEST Ed25519 pair (from certbot-vhost); nothing stripped |
| `h5bp-test-vhosts` | https://github.com/h5bp/server-configs-nginx/blob/d2f2c3e2fac76f429adb738894499b8fb756d2f3/nginx.conf + h5bp/ + test/vhosts/*.conf as conf.d/ (the repo's own test rig layout) license=MIT | /var/log/nginx/ -> logs/; an absolute pid -> logs/nginx.pid (nginx -t opens it); listen 80/443 -> 18080/18443; certificate_files.conf -> certs/default.{crt,key} (the TEST pair); nothing stripped |
| `jupyterhub-docs` | https://github.com/jupyterhub/jupyterhub/blob/9abe5fb83f4c21754ed12adac2f834c33ee9ea39/docs/source/howto/configuration/config-proxy.md (the fenced block for sites.enabled/jupyterhub.conf), as conf.d/site.conf, wrapped in nginx/pkg-oss's packaged nginx.conf (BSD-2-Clause, d16a981d5921b9d27985a24998d3438fb73bb1d7) license=BSD-3-Clause | listen privileged N -> 18000+N; wrapper paths prefix-relative, logs -> logs/, pid -> logs/nginx.pid; the letsencrypt pair -> certs/ (lobo's TEST pair), ssl_dhparam -> certs/dhparam.pem (Zulip's published ffdhe2048, Apache-2.0); nothing stripped |
| `laravel-docs` | https://github.com/laravel/docs/blob/eff8739e9090c2a0216fefac8e33dacdd689f8f6/deployment.md (the fenced nginx block under Server Configuration), as conf.d/site.conf, wrapped in nginx/pkg-oss's packaged nginx.conf (BSD-2-Clause, d16a981d5921b9d27985a24998d3438fb73bb1d7) license=MIT | listen privileged N -> 18000+N; wrapper paths prefix-relative, logs -> logs/, pid -> logs/nginx.pid; fastcgi_params is nginx-1.30.4's; nothing stripped |
| `netbox` | https://github.com/netbox-community/netbox/blob/b56c866d4c23e8a9a4ecd4c0d85a04b4e83c286c/contrib/nginx.conf as conf.d/netbox.conf, wrapped in nginx/pkg-oss's packaged nginx.conf (BSD-2-Clause, d16a981d5921b9d27985a24998d3438fb73bb1d7) license=Apache-2.0 | listen [::]:443/[::]:80 -> 18443/18080; the netbox.crt/.key pair -> certs/ (lobo's TEST pair); wrapper paths prefix-relative, logs -> logs/, pid -> logs/nginx.pid; nothing stripped |
| `nginx-pkg-oss` | https://github.com/nginx/pkg-oss/blob/d16a981d5921b9d27985a24998d3438fb73bb1d7/debian/debian/nginx.conf (byte-identical to rpm/SOURCES/nginx.conf and alpine/alpine/nginx.conf; conf.d/default.conf is debian/debian/nginx.default.conf, identical across the three) license=BSD-2-Clause | /etc/nginx/ paths prefix-relative; /var/log/nginx/ -> logs/; an absolute pid -> logs/nginx.pid (nginx -t opens it); listen 80 -> 18080; mime.types is nginx-1.30.4's (the package installs the same file); nothing stripped |
| `nginx-proxy-manager` | https://github.com/NginxProxyManager/nginx-proxy-manager/blob/2cfd3395cf979b901cecb390dd3d78810c46b596/docker/rootfs/etc/nginx/nginx.conf + conf.d/default.conf + conf.d/include/*.conf + conf.d/production.conf.template rendered with NPM_ADMIN_PORT=81 (the image's default) license=MIT | /etc/nginx/ -> prefix-relative; /data/logs/ -> logs/; /data/nginx/ -> data/nginx/ (all optional [.]conf globs, empty as on a fresh install); /tmp/nginx/body -> client_body; /var/lib/nginx/cache/{public,private} -> cache_{public,private} (nginx -t creates one directory level, not a tree); pid -> logs/nginx.pid; listen 80/81/443 -> 18080/18081/18443; dev.conf omitted (dev image only); nothing stripped |
| `njs-complex-redirects` | https://github.com/nginx/njs-examples/blob/d5de982e5f720f8aaaad9996080209195fee01b2/conf/http/complex_redirects.conf license=BSD-2-Clause | listen 80 -> 18080; js_path /etc/nginx/njs/ -> njs/ (prefix-relative; the .js modules are not carried — the config is refused before they are read); nothing stripped |
| `njs-decode-uri` | https://github.com/nginx/njs-examples/blob/d5de982e5f720f8aaaad9996080209195fee01b2/conf/http/decode_uri.conf license=BSD-2-Clause | listen 80 -> 18080; js_path /etc/nginx/njs/ -> njs/ (prefix-relative; the .js modules are not carried — the config is refused before they are read); nothing stripped |
| `njs-hello` | https://github.com/nginx/njs-examples/blob/d5de982e5f720f8aaaad9996080209195fee01b2/conf/http/hello.conf license=BSD-2-Clause | listen 80 -> 18080; js_path /etc/nginx/njs/ -> njs/ (prefix-relative; the .js modules are not carried — the config is refused before they are read); nothing stripped |
| `puma-docs` | https://github.com/puma/puma/blob/306daddfd07fdf0ca902eb7ea89ceb7dd6139050/docs/nginx.md (the fenced nginx block), as conf.d/site.conf, wrapped in nginx/pkg-oss's packaged nginx.conf (BSD-2-Clause, d16a981d5921b9d27985a24998d3438fb73bb1d7) license=BSD-3-Clause | listen privileged N -> 18000+N; wrapper paths prefix-relative, logs -> logs/, pid -> logs/nginx.pid; /myapp/log/ -> logs/ (nginx -t opens log files); nothing stripped |
| `superset` | https://github.com/apache/superset/blob/599026a0e5a82f9728a333aea0e07b6a7bf8f771/docker/nginx/nginx.conf + docker/nginx/templates/superset.conf.template rendered as the image's envsubst does with SUPERSET_APP_ROOT="/" (docker/.env's default) license=Apache-2.0 | /etc/nginx/ -> prefix-relative; /var/log/nginx/ -> logs/; an absolute pid -> logs/nginx.pid (nginx -t opens it); listen 80 -> 18080; STRIPPED: host.docker.internal (a docker-internal hostname nginx -t would resolve) -> 127.0.0.1 |
| `synapse-docs` | https://github.com/matrix-org/synapse/blob/be65a8ec0195955c15fdb179c9158b187638e39a/docs/reverse_proxy.md (the fenced nginx block), as conf.d/site.conf, wrapped in nginx/pkg-oss's packaged nginx.conf (BSD-2-Clause, d16a981d5921b9d27985a24998d3438fb73bb1d7) license=Apache-2.0 | listen privileged N -> 18000+N; wrapper paths prefix-relative, logs -> logs/, pid -> logs/nginx.pid; ADDED the two ssl_certificate lines (lobo's TEST pair) the doc leaves to the reader — without them nginx -t refuses every 'listen … ssl' server; nothing stripped |
| `ubuntu-trusty-default` | https://github.com/certbot/certbot/blob/485649333422392901e7ef891630f0129985df8e/certbot/src/certbot/_internal/tests/plugins/nginx/testdata/etc_nginx/ubuntu_nginx_1_4_6/default_vhost/nginx/nginx.conf (Ubuntu 14.04's stock nginx 1.4.6 /etc/nginx tree as certbot carries it; sites-enabled/default was a symlink to sites-available/default, materialized) license=Apache-2.0 | /etc/nginx/ -> prefix-relative; /var/log/nginx/ -> logs/; an absolute pid -> logs/nginx.pid (nginx -t opens it); listen 80 -> 18080; naxsi*/sites-available copies omitted (not included by nginx.conf); nothing stripped |
| `uwsgi-django-docs` | https://github.com/unbit/uwsgi-docs/blob/5784c30866a94942a5200db4d5f6c2850afb1caa/tutorials/Django_and_nginx.rst (the mysite_nginx.conf block), as conf.d/site.conf, wrapped in nginx/pkg-oss's packaged nginx.conf (BSD-2-Clause, d16a981d5921b9d27985a24998d3438fb73bb1d7) license=MIT | listen privileged N -> 18000+N; wrapper paths prefix-relative, logs -> logs/, pid -> logs/nginx.pid; include /path/to/your/mysite/uwsgi_params -> uwsgi_params (nginx-1.30.4's, which the tutorial says to copy); nothing stripped |

## The blocked-directive table: ws41+'s input, ordered by configs blocked

"Configs blocked" counts every config in which the item blocks lobo's
`-t` after peeling, not only the first refusal. "Sole blocker in" lists
the configs that would **load on lobo** if that one item were resolved.
`no row` means lobo's table has no row, so `-t` says
`unknown directive`. A `named_error` row means lobo refuses the
directive by name on purpose. Items marked "not a directive" are other
refusals the peel met. The ordering is by configs blocked, then by how
many of those configs a stock nginx loads.

| # | what blocks | kind | configs blocked | of which stock nginx loads | sole blocker in | configs |
|---|---|---|---|---|---|---|
| 1 | `user` (**resolved at ws41**: warns and loads when unprivileged) | `named_error` row at ws40 | 18 | 16 | `crossplane-messy`, `flask-docs`, `netbox`, `nginx-pkg-oss`, `synapse-docs` | certbot-nginx-fixture, crossplane-messy, flask-docs, gunicorn-asgi-uwsgi, gunicorn-example, h5bp-no-ssl, h5bp-ssl, h5bp-test-vhosts, jupyterhub-docs, laravel-docs, netbox, nginx-pkg-oss, nginx-proxy-manager, puma-docs, superset, synapse-docs, ubuntu-trusty-default, uwsgi-django-docs |
| 2 | `deny` | no row | 5 | 4 | — | certbot-nginx-fixture, h5bp-no-ssl, h5bp-ssl, h5bp-test-vhosts, laravel-docs |
| 3 | `uwsgi_param` | no row | 4 | 4 | — | gunicorn-asgi-uwsgi, gunicorn-stress, gunicorn-uwsgi, uwsgi-django-docs |
| 4 | `uwsgi_pass` | no row | 4 | 4 | — | gunicorn-asgi-uwsgi, gunicorn-stress, gunicorn-uwsgi, uwsgi-django-docs |
| 5 | `charset_types` | no row | 3 | 3 | — | h5bp-no-ssl, h5bp-ssl, h5bp-test-vhosts |
| 6 | `http2_max_concurrent_streams` | no row | 3 | 3 | — | gunicorn-asgi-compliance, gunicorn-http2, gunicorn-stress |
| 7 | `http2` | no row | 3 | 3 | — | gunicorn-asgi-compliance, gunicorn-http2, gunicorn-stress |
| 8 | `worker_rlimit_nofile` | `named_error` row | 3 | 3 | — | h5bp-no-ssl, h5bp-ssl, h5bp-test-vhosts |
| 9 | `js_content` | no row | 3 | 0 | — | njs-complex-redirects, njs-decode-uri, njs-hello |
| 10 | `js_import` | no row | 3 | 0 | — | njs-complex-redirects, njs-decode-uri, njs-hello |
| 11 | `js_path` | no row | 3 | 0 | — | njs-complex-redirects, njs-decode-uri, njs-hello |
| 12 | `load_module` | no row | 3 | 0 | — | njs-complex-redirects, njs-decode-uri, njs-hello |
| 13 | `proxy_buffer_size` | no row | 2 | 2 | — | gunicorn-asgi-compliance, gunicorn-http2 |
| 14 | `proxy_buffers` | no row | 2 | 2 | — | gunicorn-asgi-compliance, gunicorn-http2 |
| 15 | `proxy_pass https://` with no `proxy_ssl_trusted_certificate` (lobo verifies always) | not a directive | 2 | 2 | — | gunicorn-http2, gunicorn-stress |
| 16 | `ssl_ecdh_curve` | no row | 2 | 2 | — | h5bp-ssl, h5bp-test-vhosts |
| 17 | `ssl_protocols` without TLSv1.3 (lobo serves 1.3 only) | not a directive | 2 | 2 | — | h5bp-ssl, h5bp-test-vhosts |
| 18 | `ssl_session_tickets` | no row | 2 | 2 | — | h5bp-ssl, h5bp-test-vhosts |
| 19 | `uwsgi_read_timeout` | no row | 2 | 2 | — | gunicorn-stress, gunicorn-uwsgi |
| 20 | `allow` | no row | 2 | 1 | — | jupyterhub-docs, nginx-proxy-manager |
| 21 | `auth_request` | no row | 2 | 1 | — | nginx-proxy-manager, njs-complex-redirects |
| 22 | `listen … ssl` with no certificate (NPM: `ssl_reject_handshake on` server) | not a directive | 2 | 1 | — | certbot-nginx-fixture, nginx-proxy-manager |
| 23 | `ssl` | removed from nginx in 1.25.1; nginx 1.30 refuses too | 2 | 0 | — | certbot-nginx-fixture, jupyterhub-docs |
| 24 | `$connection_requests` in a log_format (planned variable) | not a directive | 1 | 1 | — | superset |
| 25 | `$upstream_cache_status` in a log_format (unknown variable) | not a directive | 1 | 1 | — | nginx-proxy-manager |
| 26 | `accept_mutex` | no row | 1 | 1 | — | gunicorn-example |
| 27 | `auth_basic` | no row | 1 | 1 | — | nginx-proxy-manager |
| 28 | `break` | no row | 1 | 1 | — | puma-docs |
| 29 | `chunked_transfer_encoding` | no row | 1 | 1 | — | gunicorn-asgi-compliance |
| 30 | `client_body_temp_path` | no row | 1 | 1 | — | nginx-proxy-manager |
| 31 | `client_max_body_size 4G` (the g suffix, lobo#37) | not a directive | 1 | 1 | — | gunicorn-example |
| 32 | `daemon` | `named_error` row | 1 | 1 | — | nginx-proxy-manager |
| 33 | `early_hints` | no row | 1 | 1 | — | gunicorn-http2 |
| 34 | `env` | no row | 1 | 1 | `crossplane-russian-text` | crossplane-russian-text |
| 35 | `fastcgi_buffer_size` | no row | 1 | 1 | — | laravel-docs |
| 36 | `fastcgi_buffers` | no row | 1 | 1 | — | laravel-docs |
| 37 | `fastcgi_busy_buffers_size` | no row | 1 | 1 | — | laravel-docs |
| 38 | `fastcgi_hide_header` | no row | 1 | 1 | — | laravel-docs |
| 39 | `gzip_static` | no row | 1 | 1 | — | h5bp-test-vhosts |
| 40 | `if ($x ~ "…\(")` lexed wrong (lobo#36) | not a directive | 1 | 1 | — | nginx-proxy-manager |
| 41 | `if_modified_since` | no row | 1 | 1 | — | nginx-proxy-manager |
| 42 | `log_not_found` | no row | 1 | 1 | — | laravel-docs |
| 43 | `output_buffers` | no row | 1 | 1 | — | superset |
| 44 | `pcre_jit` | no row | 1 | 1 | — | nginx-proxy-manager |
| 45 | `port_in_redirect` | no row | 1 | 1 | — | superset |
| 46 | `proxy_cache_bypass` | no row | 1 | 1 | — | nginx-proxy-manager |
| 47 | `proxy_cache_key` | no row | 1 | 1 | — | nginx-proxy-manager |
| 48 | `proxy_cache_path` | no row | 1 | 1 | — | nginx-proxy-manager |
| 49 | `proxy_cache_use_stale` | no row | 1 | 1 | — | nginx-proxy-manager |
| 50 | `proxy_hide_header` | no row | 1 | 1 | — | nginx-proxy-manager |
| 51 | `proxy_ignore_client_abort` | no row | 1 | 1 | — | nginx-proxy-manager |
| 52 | `proxy_ignore_headers` | no row | 1 | 1 | — | nginx-proxy-manager |
| 53 | `proxy_next_upstream_tries` | no row | 1 | 1 | — | gunicorn-asgi-compliance |
| 54 | `proxy_next_upstream` | no row | 1 | 1 | — | gunicorn-asgi-compliance |
| 55 | `proxy_no_cache` | no row | 1 | 1 | — | nginx-proxy-manager |
| 56 | `real_ip_header` | no row | 1 | 1 | — | nginx-proxy-manager |
| 57 | `real_ip_recursive` | no row | 1 | 1 | — | nginx-proxy-manager |
| 58 | `server_names_hash_bucket_size` | no row | 1 | 1 | — | nginx-proxy-manager |
| 59 | `set_real_ip_from` | no row | 1 | 1 | — | nginx-proxy-manager |
| 60 | `ssl_reject_handshake` | no row | 1 | 1 | — | nginx-proxy-manager |
| 61 | `stream` | no row | 1 | 1 | — | nginx-proxy-manager |
| 62 | `types_hash_max_size` | no row | 1 | 1 | — | ubuntu-trusty-default |
| 63 | `uwsgi_buffer_size` | no row | 1 | 1 | — | gunicorn-uwsgi |
| 64 | `uwsgi_buffers` | no row | 1 | 1 | — | gunicorn-uwsgi |
| 65 | `uwsgi_busy_buffers_size` | no row | 1 | 1 | — | gunicorn-uwsgi |
| 66 | : unexpected "l" | not a directive | 1 | 0 | — | crossplane-quote-behavior |
| 67 | `auth_request_set` | no row | 1 | 0 | — | njs-complex-redirects |
| 68 | `content_by_lua_block` | `named_error` row | 1 | 0 | — | lua-openresty |
| 69 | `empty` | not an nginx directive (certbot's fixture); nginx refuses too | 1 | 0 | — | certbot-nginx-fixture |
| 70 | `internal` | no row | 1 | 0 | — | njs-complex-redirects |
| 71 | `js_set` | no row | 1 | 0 | — | njs-decode-uri |
| 72 | `lua_shared_dict` | `named_error` row | 1 | 0 | — | lua-openresty |
| 73 | a missing include file (crossplane fixture; nginx refuses too) | not a directive | 1 | 0 | `crossplane-includes-regular` | crossplane-includes-regular |
| 74 | an absent certificate file (certbot fixture; nginx refuses too) | not a directive | 1 | 0 | — | certbot-nginx-fixture |
| 75 | quote-joined words (crossplane fixture; nginx refuses too) | not a directive | 1 | 0 | — | crossplane-quote-behavior |

The top of the table in one line: **`user` blocks 18 of 40 configs, 16
of which a stock nginx loads, and it is the only blocker in 5.** Two of
those five are identical loads in waiting: `flask-docs` and
`nginx-pkg-oss` load on the pinned oracle. `user` was a `named_error`
row at ws40 ("privilege drop is ws14's"), and nginx itself only warns
about it when unprivileged. **ws41 resolved it**: lobo now warns as
nginx does when unprivileged and loads, so the five load and the two
became identical loads (the confcheck line went to `25 exit-parity (4
identical loads), 15 named exit deltas`). Next come the access module (`deny`,
`allow`), uwsgi (`uwsgi_pass`, `uwsgi_param`, 4 configs), and a
three-way tie among `charset_types`, HTTP/2 (`http2`,
`http2_max_concurrent_streams`) and `worker_rlimit_nofile`. The njs
rows (`js_*`, `load_module`) block 3 configs that no nginx here loads
either, because the stock build has no njs module.

## §3 against the measurement (`docs/ws40-prediction.md`)

| prediction | measured | verdict |
|---|---|---|
| P1: 40 configs (falsified below 38) | 40 | **held** |
| P2: 6 identical loads (band 3 to 9) | **2** | **wrong.** `user` alone keeps `flask-docs` and `nginx-pkg-oss` out; everything else that loads on lobo fails the pinned build on `return`, `gzip` or PCRE |
| P3: 24 of 32 new configs refused by name (band 19 to 29), 0 silent | 28 refused (5 on a `named_error` row, 23 on a located refusal); **0 silent** | **held** |
| P4: top five are `user`, `http2`, hash sizing, uwsgi, njs (at least 3 of 5) | `user` 18, `deny` 5, `uwsgi_param` 4, `uwsgi_pass` 4, then an 8-way tie at 3 that includes `http2` and `js_*`; hash sizing blocks 1 | **held only through the tie.** `deny` (the access module) was not predicted at all |
| P5: zero configs load on lobo and not on stock nginx | **2** (lobo#38) | **wrong** |
| P5: at least 8 load on lobo and not on the pinned build | 9 | **held**. The contract's "predict zero" against the pinned binary was already false at trunk (5 of 8) |
