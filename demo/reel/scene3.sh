#!/bin/sh
# Scene 3, provenance: lobo -T prints the effective config
# with every directive's source file and line, through the
# include that pulled it in. Read-only.
. "$(dirname "$0")/lib.sh"
scene "3. provenance"
say "the server block lives in an included file"
run "grep include conf/nginx.conf"
beat
run "lobo -T 2>/dev/null | grep -B1 -E 'memory_budget|metrics on|location /files/'"
if nginx_side; then
    beat
    say "nginx -T names each file, then pastes it whole"
    cd "$NGX" && run "nginx -p . -c conf/nginx.conf -T 2>/dev/null | grep -n -E '^# configuration|location /files'"
    rm -rf "$NGX"
fi
finish
