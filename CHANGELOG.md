# Changelog

## ws11 — 2026-09-01 — replay the race

A scheduling bug becomes an artifact. The rig gains the seeded
half of lupin's determinism surface (pin HELD at 0.1.19 — v0.1.20
is match-arms, no explore change; probed day one): the corpus
runner takes `//! explore: N` (the file's whole schedule space,
every gauntlet run, green only on agreement WITH a closed frontier
— an open one is red, tense discipline) and `LOBO_SEED` (every
lupin-lane run under a bug report's seed, failures printing the
replay command). The witness pair keeps the ws08 drain-finish
hazard alive as a specimen: `drain_finish_race.lu` decides
retirement by racing the timeout message against the closes in one
select — FIFO-clean (a laptop never sees it), 3 distinct outcomes
across 16 schedules under explore — while `drain_finish_fixed.lu`
is the real loop's shape (retirement is a STATE check) and closes a
24-schedule frontier on one outcome, held by `explore: 64` forever.
`tools/lobo-replay` (a gauntlet step) walks the whole story every
run: the finding, the `.loborace` artifact (schema 1: seed +
decision stream + pinned bytes + lupin identity), three
byte-identical replays FROM the artifact (2× seed, 1× stream), the
fix's closed frontier. The server side stays honest: lobo is
spawn-free, so it never prints a seed — instead every vocabulary
event now carries `seq=` (stamped at the emission seam; builders
and prefix pins untouched) and status carries `events:` (additive,
schema stays 1), making an attached log an ordered, GAP-VISIBLE
event stream with a completeness anchor. docs/REPLAY.md states the
boundary exactly (values, real time, the membrane; no production
flight recorder — Tier 2 deferred, asks filed). Corpus 200 → 203
(the specimen pair's lupin lanes plus the fixed twin's explore run).

## wsm04 — 2026-08-31 — the doors open inward

Lobo consumes its own library's TLS client. Pins advance to wolf
b80d239 (D57 dev-stamped; no v0.2.1 tag existed at acquisition), the
lupin v0.1.19 tag, and wolf-std 26f0588 — the bump that carries
sc29's `std.x.tls.client` — with the full gauntlet green at the trio
before a line changed (corpus 195/195; #146 re-probed byte-identical,
the midend stays off). Then the last two named refusals in the config
surface retire: **`proxy_pass https://`** (D21's upstream leg) dials
through the std client — trust anchors via `proxy_ssl_trusted_
certificate` (REQUIRED: lobo has no unverified mode, nginx's
verify-off default is a named delta), SNI always, chain+hostname+
CertificateVerify before a request byte leaves, TLS failures mapped
to 502 (504 for a mid-handshake deadline) with the row named in the
error log — and the differential grows an https case where nginx and
lobo both proxy a VERIFIED fixture-cert upstream, client legs
byte-equal (8/8). **https `cert_ca`** (D25) follows: the ACME client
dials an https directory verified against `cert_ca_root`, the
harness CA serves its whole RFC 8555 directory through lobo's own
TLS server half behind the conn seam (`--tls`), and cold issuance +
renewal run over TLS end to end. The loopback law is UNCHANGED and
forever: only the https *transport* gate retired; a non-loopback CA
is still a named -t refusal. Measured honestly: the std client's
handshake costs ~3.6s on this rig (native tier, WOLF_MIDEND=0 —
#146's residue), stated where it moves deadlines, asserted nowhere
tighter. Corpus 195 → 200.

## ws10 — 2026-08-31 — the budget is real

Per-vhost memory budgets, enforced: `memory_budget <size>;` refuses a
request that would blow its budget with a 503-with-a-name (nginx's
answer is the OOM killer), deterministically per exceed-site
(head/body/body-chunked/file, fence-first at every site), observable
as the `budget-exceeded` error event and the status stanza's per-gen
`mem-hw`/`budget-503s` aggregates. The perimeter fence lands
nginx-named: `client_max_body_size` and `large_client_header_buffers`
implemented with the oracle's own invalid-value spellings. The
structure audit — the sprint's soul — found lobo held ZERO region
blocks (every allocation process-lifetime): response bodies now die
in per-response regions (~290 → ~25 KB/request, the
`lobo-membudget` gauntlet witness pins bodies-O(1) differentially),
and the str half plus the region query/cap are filed as the sprint's
three upstream asks (wolf-lang#187/#191/#192; #187 owns the gated
region-cap half). docs/BUDGET.md is the model. Corpus 184 → 195.

## ws09 — 2026-08-30 — logs that parse

`log_format`, `access_log` and `error_log` carry: the escape rules
probed byte-for-byte against the oracle, and the access-log
differential (identical directives, identical adversarial requests on
both servers) reads 4/4 identical modulo timestamps. `format=json` is
the typed door — RFC 8259-validated lines, numbers as numbers, the
ws08 drain vocabulary decoded. Sinks are bounded and loud-dropping in
the spawn-free loop; logrotate's reopen cycle works end to end. Three
new lints (L005 inert level, L006 native doors, L007 what a text
format loses). Corpus 166 → 184.

## ws06 — 2026-08-30 — certificates without the dance

Built-in ACME: RFC 8555 HTTP-01 end to end, hot-swap issuance with no
reload, a renewal daemon, and `lobo cert status`. The certbot dance
still works — the coexistence test serves a certbot block live beside
a `cert auto` block. The fixture CA is a pebble-class RFC 8555 server
written in wolf, verifying account JWS on every POST with real
dial-backs; it caught two client bugs a vendored oracle would have
accepted. Deltas recorded: Ed25519 not ES256 (the frozen jose seam),
loopback-plain `cert_ca` only until a std TLS client exists (D25),
key files at umask not 0600 (D26). Corpus 158 → 166.

## wsm03 — 2026-08-29 — the name lands

Lobo (D64) — the code stops spelling wws: 86 files, the binary's own
voice (banner, diagnostics, `Server: lobo/0.1.0`, LOBO-L lint codes),
zero seam motion. Pins advance to wolf addcd7f + the lupin 0.1.16
tag, and the first macOS three-lane gauntlet runs 158/158 — two
rig-side deltas fixed on the way (the TLS oracle refuses LibreSSL by
name; the signal gate widens so a real SIGHUP drives the drain
off-linux). wolf-lang#146 re-probed unhealed; the midend stays off.

## wsm02 — 2026-08-27 — the pin pays back

Pins to wolf 53f6191 + lupin is24, zero source breakage. TLS session
keys now come from `os_random` — the OS CSPRNG, trapping loud rather
than degrading (#143 retires) — with the interim HKDF derivation
deleted and an entropy probe at TLS bind. The three W0305 sentinel
dodges revert to the natural arm re-raise (is24's #44 fix). The
midend flip-back was attempted and refused: a #142-class survivor
found, filed as wolf-lang#146, `WOLF_MIDEND=0` stays.

## ws07 — 2026-08-27 — the dry-run that means something

`-t --request` predicts the routing decision with a why-it-lost
trace: the real matcher grows a trace parameter (never a second
implementation), effective directives filter to the winning chain
with `-T` provenance, TLS and stat notes are opt-in, and unknowable
headers say UNRESOLVED by name rather than guessing. Cross-checked
against the live server: the predicted static path's bytes are the
live body, and the backend records exactly the predicted proxy
target. Text stanzas or schema-1 JSON.

## ws05 — 2026-08-27 — TLS integrates

`listen … ssl` serves HTTPS over wolf's own TLS 1.3 stack (the
wolf-std handshake, record layer and certificate rungs), OpenSSL
interop 8/8, SNI selection, and the certbot renewal-reload cycle
carries.

## wsm01 — 2026-08-27 — the pin catches up

Pins to wolf 64a38f3 + lupin b682bcf: a real SIGHUP drives the drain
(the signal surface landed upstream), and binary files serve over
byte paths.

## ws08 — 2026-08-27 — the drain you can watch

Reload's connection draining becomes observable: per-generation live
counters on the status surface, the drain witnessed in tests, and the
serve loop reshaped into the multiplexer poll loop the later sprints
build on.

## ws04 — 2026-08-27 — the shell

CLI and exit-code parity with nginx (`-t`, `-T`, `-s`, the signal
set), and control-channel reload with connection draining. The
serving campaign (wsc01) closes.

## ws03 — 2026-08-27 — it proxies

Upstream pools, `proxy_pass`, hop-by-hop header discipline; the
two-sided differential runs 7/7 byte-equal to nginx.

## ws02 — 2026-08-26 — it serves

HTTP/1.1 static serving over an RFC 9112 MUST-checklist parser, the
historical-CVE corpus v0 held to refuse-or-trap-clean, byte-equal to
nginx on the differential. W1 declared.

## ws01 — 2026-08-26 — the config carries

The nginx config surface: 76 oracle probes, 87 directive table rows,
three lints firing at load, and `-T` that knows which file set every
directive. The scaffolding campaign (wsc00) closes.

## ws00 — 2026-08-26 — the repo and the harness

Pins (wolf 87405ac / lupin e2dbd40, the `.wolf-bin` ritual), the
loopback HTTP rig written in wolf, the pinned-nginx differential with
its first byte-equal case, the gauntlet, and CI against the pins —
committed ahead of any remote.
