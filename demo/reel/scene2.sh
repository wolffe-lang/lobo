#!/bin/sh
# Scene 2, the dry run that means something: lobo -t answers
# "what would this config DO with this request", offline.
# Read-only: touches nothing.
. "$(dirname "$0")/lib.sh"
scene "2. the dry run that means something"
say "three locations. which one serves /files/big.bin?"
run "grep location conf/site.conf"
beat
run "lobo -t --request 'GET http://wolf.espadonne.com/files/big.bin' 2>/dev/null | grep -E '^location|candidate|^decision'"
beat
say "and the home page?"
run "lobo -t --request 'GET http://wolf.espadonne.com/' 2>/dev/null | grep -E '^location|candidate|^decision'"
if nginx_side; then
    beat
    say "nginx -t, same locations (lobo-only lines cut)"
    cd "$NGX" && run "nginx -p . -c conf/nginx.conf -t"
    rm -rf "$NGX"
fi
finish
