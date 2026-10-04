#!/bin/sh
# Scene 5, the memory budget is real: every request may bring
# at most memory_budget bytes. Normal requests keep answering
# 200 while one 150 KB request gets a 503 that lobo names in
# its log and counts at /metrics. Read-only on the config.
#
#   scene5.sh         the whole scene (rehearsals)
#   scene5.sh burst   only the moment: the 200s, the 503, the
#                     named reason (the shot list's 5.2)
. "$(dirname "$0")/lib.sh"
metric() { curl -s localhost:$PORT/metrics | sed -n "s/^$1 //p"; }
G=$(lobo status | sed -n 's/^current generation: //p')
[ -n "$G" ] || { echo "${R}lobo status did not answer${N}"; exit 1; }
r0=$(metric "lobo_budget_refusals_total{gen=\"$G\"}")
x0=$(metric 'lobo_requests_total{class="5xx"}')

burst() {
    say "normal traffic, and one request carrying 150 KB of headers"
    run "BIG=\$(head -c 50000 /dev/zero | tr '\\0' w)"
    run "(for i in 1 2 3 4 5 6 7 8; do curl -s -o /dev/null -w '%{http_code} ' localhost:$PORT/; sleep 0.25; done; echo) &"
    LOOP=$!
    sleep 0.8
    run "curl -s -o /dev/null -w '%{http_code} <- the big one\\n' -H \"A: \$BIG\" -H \"B: \$BIG\" -H \"C: \$BIG\" localhost:$PORT/"
    wait $LOOP
    beat
    say "lobo names the refusal"
    run "grep budget-exceeded logs/serve.out | tail -n 1 | cut -d' ' -f2-7"
}

case ${1:-all} in
    burst) burst ;;
    all)
        scene "5. the memory budget is real"
        say "every request gets a budget"
        run "grep memory_budget conf/site.conf"
        run "curl -s localhost:$PORT/metrics | grep '^lobo_budget'"
        beat
        burst
        say "and counts it"
        run "curl -s localhost:$PORT/metrics | grep '^lobo_budget'"
        ;;
    *) echo "usage: scene5.sh [burst]"; exit 2 ;;
esac
r1=$(metric "lobo_budget_refusals_total{gen=\"$G\"}")
x1=$(metric 'lobo_requests_total{class="5xx"}')
[ "$r1" = $((r0 + 1)) ] || RUN_FAILED="refusals $r0 -> $r1"
[ "$x1" = $((x0 + 1)) ] || RUN_FAILED="${RUN_FAILED} 5xx $x0 -> $x1"
finish
