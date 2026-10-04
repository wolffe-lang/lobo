#!/bin/sh
# Scene 6, live metrics: lobo's own Prometheus endpoint (no
# exporter, no module), showing the generations scene 4's
# reloads made and scene 5's budget refusal. Read-only.
. "$(dirname "$0")/lib.sh"
scene "6. live metrics"
say "one line in the config: metrics on;"
run "curl -s localhost:$PORT/metrics | grep -c '^lobo_'"
beat
run "curl -s localhost:$PORT/metrics | grep -E '^lobo_(config_generation_current|config_generations|budget|requests_total)'"
finish
