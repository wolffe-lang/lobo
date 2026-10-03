#!/bin/sh
# Scene 4, the reload you can watch. A slow download holds a
# connection on generation N; v2 ships (a new root, a reload);
# lobo status shows N draining while N+1 serves; the download
# finishes intact; N retires. If the tunnel holds an idle
# keep-alive on N, worker_shutdown_timeout (25 s) aborts it
# and the retirement reads aborted=1.
#
#   scene4.sh            the whole scene, one pane (rehearsals)
#   scene4.sh download   pane 2: the slow download + checksum
#   scene4.sh reload     pane 1: ship v2, reload
#   scene4.sh status     the generations, trimmed for a phone
#   scene4.sh retired    wait for N to retire, show its story
#   scene4.sh restore    off camera: v1 back, for a retake
. "$(dirname "$0")/lib.sh"

status_line() {
    run "lobo status | grep '^generation' | cut -d' ' -f1-4,10"
}

# lobo 0.1.1 stalls its loop for up to ~8 s as a slow stream
# starts, and `lobo status` then prints NOTHING and exits 0
# (both filed, see README). Never read an empty status as an
# answer: retry until it names the current generation.
current_gen() {
    _i=0
    until _g=$(lobo status | sed -n 's/^current generation: //p') &&
        [ -n "$_g" ]; do
        _i=$((_i + 1))
        [ $_i -ge 10 ] && { echo "${R}lobo status never answered${N}" >&2; return 1; }
    done
    echo "$_g"
}

do_download() {
    rm -f "$LOGS"/dl.*
    say "a slow client downloads 1.3 MB at 64 KB/s"
    if [ "${1:-}" = bg ]; then
        run "curl -s --limit-rate 64k -o logs/dl.bin localhost:8088/files/big.bin &"
        DL=$!
        return 0
    fi
    current_gen > "$LOGS/dl.gen" || exit 1
    run "curl -# --limit-rate 64k -o logs/dl.bin localhost:8088/files/big.bin"
    run "shasum html/files/big.bin logs/dl.bin | cut -c1-16"
    cmp -s html/files/big.bin logs/dl.bin ||
        RUN_FAILED="the download differs from the file"
}

do_reload() {
    if grep -q 'root html-v2;' conf/site.conf; then
        echo "${R}v2 is already live: ./scene4.sh restore first${N}"
        exit 1
    fi
    OLD=$(current_gen) || exit 1
    echo "$OLD" > "$LOGS/old.gen"
    cp conf/site.conf "$LOGS/site.conf.v1"
    rm -rf html-v2
    say "ship v2: a new page in a new root, then reload"
    run "cp -R html html-v2"
    run "sed -i '' 's/hello from/v2: hello from/' html-v2/index.html"
    run "sed -i '' 's/root html;/root html-v2;/' conf/site.conf"
    run "lobo -s reload"
    status_line
}

do_retired() {
    OLD=${OLD:-$(cat "$LOGS/old.gen" 2> /dev/null)}
    [ -n "$OLD" ] || { echo "${R}no reload recorded: run reload first${N}"; exit 1; }
    say "generation $OLD retires"
    show "until grep -q 'retired gen=$OLD' logs/serve.out; do sleep 1; done"
    _i=0
    until grep -q "generation-retired gen=$OLD " logs/serve.out; do
        _i=$((_i + 1))
        if [ $_i -ge 40 ]; then
            RUN_FAILED="gen $OLD did not retire in 40 s"
            break
        fi
        sleep 1
    done
    run "grep -E '(draining|retired) gen=$OLD ' logs/serve.out | cut -c16- | cut -d' ' -f1-5"
}

do_restore() {
    if [ -f "$LOGS/site.conf.v1" ]; then
        cp "$LOGS/site.conf.v1" conf/site.conf && rm -f "$LOGS/site.conf.v1"
        lobo -s reload > /dev/null || RUN_FAILED="the restoring reload failed"
    fi
    rm -rf html-v2 "$LOGS"/dl.* "$LOGS/old.gen"
    printf '(off camera: v1 live, %s)\n' "$(lobo status | grep '^current')"
}

case ${1:-all} in
    download) do_download ;;
    reload) do_reload ;;
    status) status_line ;;
    retired) do_retired ;;
    restore) do_restore ;;
    all)
        scene "4. the reload you can watch"
        do_download bg
        sleep 2
        do_reload
        beat
        run "curl -s localhost:8088/ | grep -o '<h1>.*</h1>'"
        run "curl -s localhost:8088/metrics | grep -E '^lobo_(config_generations|connections_active)'"
        say "the old generation still holds the download"
        show "wait  # for the download"
        wait $DL
        run "shasum html/files/big.bin logs/dl.bin | cut -c1-16"
        cmp -s html/files/big.bin logs/dl.bin ||
            RUN_FAILED="the download differs from the file"
        do_retired
        echo
        do_restore
        ;;
    *)
        echo "usage: scene4.sh [download|reload|status|retired|restore]"
        exit 2
        ;;
esac
finish
