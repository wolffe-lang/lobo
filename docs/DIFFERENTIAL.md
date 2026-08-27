# The nginx differential harness

The drop-in claim is falsifiable or it is marketing: same config,
same requests → same responses as a pinned REAL nginx, on loopback,
in CI. ws00 ships the SKELETON — the pin, the case format, the
differ, one static-file case green. From ws02 on, wws runs beside
the oracle and both replies go through the same differ.

## The pin, and the D33-safe build ritual

`tests/differential/NGINX-PIN` records the oracle's version, source
tarball SHA-256, and exact configure line. The binary itself is
NEVER committed (`tests/differential/bin/` is gitignored) and the
harness never builds it: D33 (no build scripts in the wolf
ecosystem) means building the oracle is a documented ONE-TIME
human/agent action — part of entering this repo, like building the
wolf toolchain into `.wolf-bin/`:

```sh
# from the values in tests/differential/NGINX-PIN, in a scratch dir:
curl -LO https://nginx.org/download/nginx-1.30.4.tar.gz
sha256sum -c <(echo "4261dc90e9e47c1c4041276e9aaa3d48ebe2e664f728e14fa95ae6c67d57a08b  nginx-1.30.4.tar.gz")
tar xzf nginx-1.30.4.tar.gz && cd nginx-1.30.4
./configure --without-http_rewrite_module --without-http_gzip_module
make -j"$(nproc)"
cp objs/nginx <repo>/tests/differential/bin/nginx
# delete the scratch dir; the repo carries the pin, not the source
```

CI builds the same thing in a cached step keyed on the pin file —
a CI step is not a build script in the D33 sense (wolf-lang's own CI
compiles things); the wsc00 closeout records that interpretation for
review.

`tools/wws-differential` REFUSES, naming the pin, when the binary is
absent or `bin/nginx -v` disagrees with the pinned version. A
configure-line drift (`-v` right, `-V` different) is reported but
not gated: the version is the behavioral identity, the configure
line the recipe. The refusal is a red gauntlet — deliberately: a
green gauntlet always means the differential actually ran.

The configure line drops rewrite (PCRE) and gzip (zlib) so the
oracle builds from a bare toolchain everywhere; neither module
affects the static-file corpus this harness serves, and a future
case that needs one changes the PIN, not the harness.

## The case format

One file per case under `tests/differential/cases/<name>.case`:
`//` comment lines, then a `--- request` section holding the RAW
request bytes (CRLF line endings — the file deliberately mixes line
endings; editors will show `^M`, and that is the point: the wire
bytes are the checked-in truth), then a `--- expect` section holding
the expected reply, stored pre-normalized (see below). git must
never translate these files (no autocrlf).

## The normalization list is checked in, never folklore

`tests/differential/NORMALIZE` names the response headers whose
VALUES the differ replaces with `<normalized>` — on BOTH sides —
before byte-comparing. At ws00 it is exactly `Server` and `Date`,
each with its reason in the file. Everything else byte-compares,
CRLF included. Adding an entry requires a why-comment; a differ that
quietly normalizes is a differ that lies (the benchmarketing lesson,
applied to compat).

## Determinism

`Last-Modified` and `ETag` derive from the served file's mtime and
size, so the harness pins the corpus mtime (`touch -d
2026-01-01T00:00:00Z`) before starting the oracle — those headers
byte-compare rather than being normalized away. The oracle listens
on a loopback ephemeral port chosen by the OS (`tests/rig/
freeport.lu`), with a retry loop against the release-to-rebind race;
its config is rendered from the checked-in minimal
`tests/differential/nginx.conf.in` with every path (pid, logs, root)
inside the case's scratch dir under `target/` — a test rig never
scribbles on system paths. The wire half is the wolf rig
(`tests/rig/diffsend.lu` over `httpc`): requests sent verbatim,
replies read to close under a 5s deadline.
