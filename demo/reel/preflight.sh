#!/bin/sh
# preflight.sh: bring the whole chain up and PROVE it, in
# order, loudly. Prints GO, or the exact step that failed
# (and tears down whatever it started).
. "$(dirname "$0")/lib.sh"
T=10
step() { STEP="$1/$T $2"; printf '%s[%s]%s ' "$B" "$STEP" "$N"; }
ok() { printf '%sok%s %s\n' "$G" "$N" "$*"; }
nogo() {
    printf '%sFAIL%s %s\n' "$R" "$N" "$*"
    if [ "${STARTED:-0}" = 1 ]; then
        echo "-- tearing down what preflight started --"
        "$REEL/teardown.sh" > "$LOGS/preflight-teardown.out" 2>&1
        tail -n 1 "$LOGS/preflight-teardown.out"
    fi
    printf '\n%sNO GO: failed at step %s%s\n' "$R" "$STEP" "$N"
    exit 1
}

step 1 "versions"
v=$(lobo -v 2>&1 | head -n 1)
case $v in *"$WANT_LOBO "*) ;; *) nogo "lobo: '$v', want $WANT_LOBO" ;; esac
w=$(wolf --version 2>&1 | head -n 1)
case $w in "$WANT_WOLF "*) ;; *) nogo "wolf: '$w', want $WANT_WOLF" ;; esac
c=$(cloudflared --version 2>&1) || nogo "cloudflared missing"
ok "$WANT_LOBO, $WANT_WOLF, ${c#cloudflared version }"

step 2 "port $PORT free, nothing of ours running"
h=$(port_holder)
[ -z "$h" ] || nogo "port $PORT held by pid $h: $(ps -p "$h" -o command=)"
for n in lobo tunnel; do
    p=$(our_pid $n) && nogo "a reel $n is running (pid $p): ./teardown.sh"
done
if ! quick && [ ! -f "$REEL_TUNNEL_CONFIG" ]; then
    nogo "no tunnel config at $REEL_TUNNEL_CONFIG"
fi
ok

step 3 "the build (wolf run build/main.lu)"
rm -rf html html-v2
wolf run build/main.lu > "$LOGS/build.out" 2>&1 ||
    nogo "wolf run failed: $(tail -n 2 "$LOGS/build.out")"
grep -qF "$H1" html/index.html || nogo "no $H1 in html/index.html"
sz=$(wc -c < html/files/big.bin | tr -d ' ')
[ "$sz" = 1310720 ] || nogo "big.bin is $sz bytes, want 1310720"
ok "page + big.bin ($sz bytes)"

step 4 "lobo -t"
lobo -t > "$LOGS/t.out" 2>&1 || nogo "$(tail -n 3 "$LOGS/t.out")"
ok "$(tail -n 1 "$LOGS/t.out" | sed 's/^lobo: //')"

step 5 "lobo serving locally"
rm -f "$LOGS"/serve.out "$LOGS"/control.sock "$LOGS"/nginx.pid
STARTED=1
nohup lobo serve > "$LOGS/serve.out" 2>&1 &
echo $! > "$LOGS/reel-lobo.pid"
echo "lobo serve" > "$LOGS/reel-lobo.cmd"
i=0
until grep -q 'serving on 127.0.0.1:8088' "$LOGS/serve.out"; do
    i=$((i + 1)); [ $i -ge 50 ] && nogo "no 'serving on' line in 10 s: $(tail -n 2 "$LOGS/serve.out")"
    sleep 0.2
done
our_pid lobo > /dev/null || nogo "lobo exited: $(tail -n 2 "$LOGS/serve.out")"
r=$(fetch_from here "$LOCAL/")
[ "$r" = "200 yes" ] || nogo "local GET / -> $r"
ok "pid $(cat "$LOGS/reel-lobo.pid"), GET / 200 with the h1"

step 6 "the tunnel up"
tc=$(tunnel_cmd)
rm -f "$LOGS/tunnel.out" "$LOGS/public_url"
nohup $tc > "$LOGS/tunnel.out" 2>&1 &
echo $! > "$LOGS/reel-tunnel.pid"
echo "$tc" > "$LOGS/reel-tunnel.cmd"
i=0
until grep -q 'Registered tunnel connection' "$LOGS/tunnel.out"; do
    i=$((i + 1)); [ $i -ge 150 ] && nogo "no registered connection in 30 s: $(tail -n 2 "$LOGS/tunnel.out")"
    our_pid tunnel > /dev/null || nogo "cloudflared exited: $(tail -n 2 "$LOGS/tunnel.out")"
    sleep 0.2
done
if quick; then
    grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOGS/tunnel.out" |
        head -n 1 > "$LOGS/public_url"
fi
url=$(public_url)
[ -n "$url" ] || nogo "no public URL"
ok "$url"

# outside FIRST: this Mac must not ask DNS before the name exists
# (a cached NXDOMAIN would fail the browser in the finale)
step 7 "outside: $OUTSIDE fetches the public URL"
i=0
while :; do
    t0=$(now); r=$(fetch_from "$OUTSIDE" "$url"); t1=$(now)
    [ "$r" = "200 yes" ] && break
    i=$((i + 1)); [ $i -ge 20 ] && nogo "$OUTSIDE: $url -> $r"
    sleep 3
done
ok "200 with the h1 ($(secs $t0 $t1) s incl. ssh)"

step 8 "this Mac fetches the public URL (the browser's path)"
r=$(fetch_from here "$url")
[ "$r" = "200 yes" ] || nogo "here: $url -> $r"
ok "200 with the h1"

step 9 "/metrics answers"
m=$(curl -s -m 5 "$LOCAL/metrics")
echo "$m" | grep -q '^lobo_build_info{.*} 1$' ||
    nogo "no lobo_build_info in /metrics"
ok "$(echo "$m" | grep -c '^lobo_') series"

step 10 "the control socket answers"
p=$(lobo control ping 2>&1)
[ "$p" = pong ] || nogo "lobo control ping -> '$p'"
g=$(lobo status | grep '^current generation')
ok "pong; $g"

printf '\n%sGO%s  lobo on %s, public at %s\n' "$G" "$N" "$LOCAL" "$url"
