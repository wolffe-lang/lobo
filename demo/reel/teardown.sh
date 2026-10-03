#!/bin/sh
# teardown.sh: stop lobo through its control socket, stop the
# tunnel, then PROVE the chain is down: no reel process, port
# 8088 free, and the public URL dead from outside.
. "$(dirname "$0")/lib.sh"
fail=0
url=$(public_url)

printf '%s[1/5] lobo: stop over the control socket%s\n' "$B" "$N"
if p=$(our_pid lobo); then
    lobo -s stop
    i=0
    while kill -0 "$p" 2> /dev/null && [ $i -lt 50 ]; do
        sleep 0.2; i=$((i + 1))
    done
    if kill -0 "$p" 2> /dev/null; then
        echo "  lobo pid $p ignored stop; TERM to that pid only"
        kill -TERM "$p"; sleep 2
    fi
    kill -0 "$p" 2> /dev/null && { echo "  ${R}lobo $p STILL ALIVE${N}"; fail=1; }
    kill -0 "$p" 2> /dev/null || echo "  lobo pid $p exited"
else
    echo "  no reel lobo running"
fi

printf '%s[2/5] tunnel: stop the exact process%s\n' "$B" "$N"
if p=$(our_pid tunnel); then
    kill -TERM "$p"
    i=0
    while kill -0 "$p" 2> /dev/null && [ $i -lt 50 ]; do
        sleep 0.2; i=$((i + 1))
    done
    kill -0 "$p" 2> /dev/null && { echo "  ${R}cloudflared $p STILL ALIVE${N}"; fail=1; }
    kill -0 "$p" 2> /dev/null || echo "  cloudflared pid $p exited"
else
    echo "  no reel tunnel running"
fi

printf '%s[3/5] port %s free%s\n' "$B" "$PORT" "$N"
h=$(port_holder)
if [ -n "$h" ]; then
    echo "  ${R}port $PORT still held by pid $h:${N}"
    ps -p "$h" -o pid=,command=
    fail=1
else
    echo "  free"
fi

printf '%s[4/5] no reel process left%s\n' "$B" "$N"
left=
for n in lobo tunnel; do
    p=$(our_pid $n) && left="$left $n:$p"
done
if [ -n "$left" ]; then
    echo "  ${R}left:$left${N}"; fail=1
else
    echo "  none"
fi

printf '%s[5/5] public URL dead from %s%s\n' "$B" "$OUTSIDE" "$N"
if [ -z "$url" ]; then
    echo "  no public URL was ever recorded"
else
    i=0
    while :; do
        r=$(fetch_from "$OUTSIDE" "$url")
        case $r in "200 yes") ;; *) break ;; esac
        i=$((i + 1))
        [ $i -ge 15 ] && break
        sleep 2
    done
    echo "  $url -> HTTP ${r% *} (page: ${r#* })"
    case $r in
        "200 yes") echo "  ${R}STILL SERVING THE PAGE${N}"; fail=1 ;;
    esac
fi

# an interrupted scene 4 leaves its backup: put v1 back
if [ -f "$LOGS/site.conf.v1" ]; then
    mv "$LOGS/site.conf.v1" "$SITE/conf/site.conf"
    echo "  restored conf/site.conf from scene 4's backup"
fi
rm -rf "$SITE/html-v2" "$LOGS"/dl.* "$LOGS/old.gen"
[ $fail -eq 0 ] && rm -f "$LOGS"/reel-*.pid "$LOGS"/reel-*.cmd
if [ $fail -eq 0 ]; then
    echo "${G}teardown: DOWN (proven)${N}"
else
    echo "${R}teardown: NOT CLEAN, see above${N}"
fi
exit $fail
