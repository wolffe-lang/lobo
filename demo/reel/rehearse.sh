#!/bin/sh
# rehearse.sh: the whole reel, exactly as filmed, preflight to
# teardown, timed. Scene 7 fetches instead of opening a
# browser (REEL_REHEARSAL=1). Exit 0 only if every step did.
. "$(dirname "$0")/lib.sh"
REEL_REHEARSAL=1
export REEL_REHEARSAL
total0=$(now)
rc=0
for s in preflight scene0 scene1 scene2 scene3 scene4 scene5 scene6 scene7 teardown; do
    t0=$(now)
    "$REEL/$s.sh"
    r=$?
    t1=$(now)
    printf '\n%s>> %s: exit %s, %s s%s\n\n' "$B" "$s" "$r" "$(secs $t0 $t1)" "$N"
    TIMES="$TIMES $s=$(secs $t0 $t1)"
    if [ $r -ne 0 ]; then
        rc=1
        [ $s = preflight ] && break
        [ $s = teardown ] || { "$REEL/teardown.sh"; break; }
    fi
done
echo "timings:$TIMES total=$(secs $total0 $(now))"
[ $rc -eq 0 ] && echo "${G}REHEARSAL GREEN${N}" || echo "${R}REHEARSAL RED${N}"
exit $rc
