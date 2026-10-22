# ws72 — the master remembers its binary

Crawl 54, lane ws72, GPT-6.1-Sol (Codex). Contract:
`wolf/sprints/wws/41-the-binary-identity/ws72-the-binary-identity.md`.
Starting tree `f32a1b7`; wolf 0.2.34 / lupin 0.1.55 / std `e036bec`
stay pinned. No release, package update, merge, or issue mutation.

## Prediction, before the first change

- P1: `fs_stat` at the pin answers device and inode, as well as size
  and mtime. No content digest fallback will be needed on linux or
  macOS. A missing field falsifies this; name the missing std row.
- P2: the replacement refusal can be deterministic under
  `taskset -c 0-3` without a fixed sleep: poll the workers' own status
  until ready, TERM one recorded pid, then poll the refusal and the
  master's status with bounded deadlines. Both a byte-appended copy
  and a byte-identical new inode are refused; an unchanged path still
  replaces a worker. Every new refusal row must first fail at trunk.
- P3: nginx needs only a copied executable, not a second nginx build:
  renaming a byte-appended copy over its path and ending a worker
  leaves the master forking its original image. Read `/proc/PID/exe`
  and process counts inside the container, never nginx's source.

## Rulings requested, not decided

- R-ws72-1: recommend (a), refuse the replacement and log once for
  that slot; keep surviving workers serving. Implement (a), not a
  master re-exec or a new-version worker. `control upgrade` remains
  explicitly unimplemented.
- R-ws72-2: recommend strict identity, including an identical copy
  with a new inode. A package-manager replacement is an image change
  even when its bytes happen to match. Implement strict identity.
