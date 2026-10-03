#!/bin/sh
# Scene 1, built by wolf: one short wolf program writes the
# page (and the big file scene 4 downloads). Re-runnable: the
# build is deterministic and overwrites its own output.
. "$(dirname "$0")/lib.sh"
scene "1. built by wolf"
say "the whole site is one wolf program"
run "cat build/main.lu"
beat
run "wolf run build/main.lu"
beat
run "grep -o '<h1>.*</h1>' html/index.html"
finish
