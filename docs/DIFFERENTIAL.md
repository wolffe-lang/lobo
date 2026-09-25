# The nginx differential harness

The drop-in claim gets tested: same config, same requests → same
responses as a pinned REAL nginx, on loopback, in CI. At ws00 the
harness is a skeleton: the pin, the case format, the differ, one
static-file case green. From ws02 on, lobo runs beside the oracle and
both replies go through the same differ.

## The pin, and the D33-safe build ritual

`tests/differential/NGINX-PIN` records the oracle's version, source
tarball SHA-256, and configure line. The binary itself is
NEVER committed (`tests/differential/bin/` is gitignored) and the
harness never builds it: D33 (no build scripts in the wolf
ecosystem) means building the oracle is a documented ONE-TIME
human/agent action, part of entering this repo, like building the
wolf toolchain into `.wolf-bin/`:

```sh
# from the values in tests/differential/NGINX-PIN, in a scratch dir:
curl -LO https://nginx.org/download/nginx-1.30.4.tar.gz
sha256sum -c <(echo "4261dc90e9e47c1c4041276e9aaa3d48ebe2e664f728e14fa95ae6c67d57a08b  nginx-1.30.4.tar.gz")
tar xzf nginx-1.30.4.tar.gz && cd nginx-1.30.4
./configure --without-http_rewrite_module --without-http_gzip_module --with-http_ssl_module
# macOS: clang finds no OpenSSL headers by default — point the build
# at Homebrew's openssl@3 (host-specific flags, NOT part of the pin):
#   ./configure ... --with-cc-opt="-I$(brew --prefix openssl@3)/include" \
#                   --with-ld-opt="-L$(brew --prefix openssl@3)/lib"
make -j"$(nproc)"
cp objs/nginx <repo>/tests/differential/bin/nginx
# delete the scratch dir; the repo carries the pin, not the source
```

CI builds the same thing in a cached step keyed on the pin file. A
CI step falls outside D33's meaning of a build script (wolf-lang's
own CI compiles things); the wsc00 closeout records that
interpretation for review.

`tools/lobo-differential` REFUSES, naming the pin, when the binary is
absent or `bin/nginx -v` disagrees with the pinned version. A
configure-line drift (`-v` right, `-V` different) is reported but
not gated: the version is the behavioral identity, the configure
line the recipe. The refusal turns the gauntlet red, so a green
gauntlet means the differential ran.

The configure line drops rewrite (PCRE) and gzip (zlib) so the
oracle builds from a bare toolchain everywhere; neither module
affects the static-file corpus this harness serves, and a future case
that needs one changes the PIN and leaves the harness alone. That
route has been walked once, at wsm04: `--with-http_ssl_module` joined
the line so the oracle can serve the https UPSTREAM of the proxy
differential's https case and dial `proxy_pass https://` itself
(OpenSSL headers are a build-time need; the recipe above notes the
macOS spelling).

## The case format

One file per case under `tests/differential/cases/<name>.case`:
`//` comment lines, then a `--- request` section holding the RAW
request bytes (CRLF line endings; the file mixes line endings, so
editors will show `^M`. The wire bytes are the checked-in truth),
then a `--- expect` section holding
the expected reply, stored pre-normalized (see below). git must
never translate these files (no autocrlf).

An optional `--- server` section (ws41) holds directives spliced into
BOTH servers' `server {}` block at the templates' `@SERVER@` line, so
a case can carry the one directive it is about (`max_ranges 1;`)
without a second template pair. A case without one splices nothing.

## The normalization list is checked in, never folklore

`tests/differential/NORMALIZE` lists the response headers whose
VALUES the differ replaces with `<normalized>`, on BOTH sides, before
byte-comparing. At ws00 it is `Server` and `Date`, each with its
reason in the file. Everything else byte-compares, CRLF included.
Adding an entry requires a why-comment in the file.

One entry is a BODY rule (ws41): `@error-footer`. A default error page
ends in the server's identity footer (`<hr><center>nginx/1.30.4
</center>` on the oracle, lobo's token on lobo), so a 416's body and
its `Content-Length` differ by exactly the token. On a 4xx/5xx reply
whose body carries that footer line, the footer's text becomes
`<normalized>`, and so does `Content-Length` — only when the declared
length equals the body's real byte count, so a wrong length still
reds.

## Range (ws41)

Nineteen `range_*` cases over the 79-byte `index.html`: single,
suffix, open and clamped ranges; a multipart set (a fresh nginx's
first boundary is `00000000000000000001`, and lobo counts per process
the same way); a set with one unsatisfiable member; four 416 shapes;
an unknown unit and an oversized set (both a full 200); `If-Range` by
ETag, by a stale ETag and by date; `HEAD`; a 304 that outranks the
range; and `max_ranges 1` / `max_ranges 0`. At trunk `d65cce0` lobo
matched 4 of them and 15 were red (`docs/ws41-prediction.md`).

## Determinism

`Last-Modified` and `ETag` derive from the served file's mtime and
size, so the harness pins the corpus mtime (`touch -d
2026-01-01T00:00:00Z`) before starting the oracle, and those headers
byte-compare. The oracle listens
on a loopback ephemeral port chosen by the OS (`tests/rig/
freeport.lu`), with a retry loop against the release-to-rebind race;
its config is rendered from the checked-in minimal
`tests/differential/nginx.conf.in` with every path (pid, logs, root)
inside the case's scratch dir under `target/`; the rig stays out of
system paths. The wire half is the wolf rig
(`tests/rig/diffsend.lu` over `httpc`): requests sent verbatim,
replies read to close under a 5s deadline.
