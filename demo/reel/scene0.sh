#!/bin/sh
# Scene 0, lobo itself: the size of its wolf source, one whole
# source file, the binary. Read-only. The source is the lobo
# checkout this reel lives in (REEL_LOBO_SRC to override).
. "$(dirname "$0")/lib.sh"
SRC=$(lobo_src)
[ -f "$SRC/src/main.lu" ] || { echo "${R}no lobo source at $SRC (set REEL_LOBO_SRC)${N}"; exit 1; }
CAT=$(command -v mat || echo cat)
CAT=$(basename "$CAT")
scene "0. a web server written in wolf"
cd "$SRC" || exit 1
run "find src -name '*.lu' | xargs cat | wc -l"
beat
run "$CAT src/config/workerconf.lu"
beat
run "lobo -v"
finish
