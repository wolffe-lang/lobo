#!/bin/sh
# Scene 7, the finale: the page at its public address, from
# this laptop behind carrier-grade NAT. Checks the URL one last
# time BEFORE the browser opens; never opens a dead page.
# REEL_REHEARSAL=1 fetches instead of opening a browser.
. "$(dirname "$0")/lib.sh"
url=$(public_url)
r=$(fetch_from here "$url")
if [ "$r" != "200 yes" ]; then
    echo "${R}NOT LIVE: $url -> $r. Do not film; run ./preflight.sh${N}"
    exit 1
fi
scene "7. live"
say "one laptop, behind carrier-grade NAT"
if [ "${REEL_REHEARSAL:-0}" = 1 ]; then
    show "open $url"
    echo "(rehearsal: no browser; the same URL fetched instead)"
    t0=$(now); r1=$(fetch_from here "$url"); t1=$(now)
    t2=$(now); r2=$(fetch_from "$OUTSIDE" "$url"); t3=$(now)
    echo "  this Mac: $r1  ($(secs $t0 $t1) s)"
    echo "  $OUTSIDE:  $r2  ($(secs $t2 $t3) s incl. ssh)"
    [ "$r1" = "200 yes" ] && [ "$r2" = "200 yes" ] || exit 1
else
    run "open $url"
fi
