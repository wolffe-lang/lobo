# lib.sh: sourced by every reel script. POSIX sh.
#
# One variable decides the public address: REEL_PUBLIC_URL.
#   default -> https://wolf.espadonne.com, the named tunnel
#              wolf-demo, run from REEL_TUNNEL_CONFIG (default:
#              ./tunnel.yml beside the scripts, else the one in
#              ~/scratch/wolf/lobo-demo)
#   quick   -> the fallback: a Cloudflare quick tunnel; its
#              random URL is read from the tunnel's log into
#              logs/public_url
REEL=$(cd "$(dirname "$0")" && pwd -P)
SITE=$REEL
# The reel runs from its own folder, the one holding
# conf/nginx.conf: lobo's control socket and config paths are
# relative, and the commands typed by hand assume it.
if [ ! -f "$REEL/conf/nginx.conf" ]; then
    echo "reel: $REEL has no conf/nginx.conf; this is not a complete reel folder" >&2
    exit 2
fi
# Run from anywhere: every script moves into its own reel folder first, so a
# full path (bash /path/to/scene2.sh) always uses that folder's config and
# control socket, never whatever folder the shell happens to be in.
cd "$REEL" || exit 2
LOGS=$SITE/logs
PORT=${REEL_PORT:-8088}   # must match `listen` in conf/site.conf
LOCAL=http://127.0.0.1:$PORT
OUTSIDE=${REEL_OUTSIDE:-almanta}
H1="hello from wolf</h1>"   # v1 and scene 4's v2 both match
REEL_PUBLIC_URL=${REEL_PUBLIC_URL:-https://wolf.espadonne.com}
if [ -f "$REEL/tunnel.yml" ]; then
    REEL_TUNNEL_CONFIG=${REEL_TUNNEL_CONFIG:-$REEL/tunnel.yml}
else
    REEL_TUNNEL_CONFIG=${REEL_TUNNEL_CONFIG:-$HOME/scratch/wolf/lobo-demo/tunnel.yml}
fi
WANT_LOBO=${REEL_LOBO_VERSION:-lobo/0.1.1}
WANT_WOLF=${REEL_WOLF_VERSION:-wolf 0.2.20}
COLUMNS=${COLUMNS:-60}
export COLUMNS
cd "$SITE" || exit 2
mkdir -p "$LOGS"

if [ -t 1 ]; then
    B=$(printf '\033[1m'); C=$(printf '\033[1;36m')
    Y=$(printf '\033[33m'); R=$(printf '\033[1;31m')
    G=$(printf '\033[1;32m'); N=$(printf '\033[0m')
else
    B=; C=; Y=; R=; G=; N=
fi

# show: print a command as if typed. run: show it, then run it.
show() { printf '\n%s$ %s%s\n' "$C" "$*" "$N"; }
run() { show "$*"; eval "$*" || RUN_FAILED="${RUN_FAILED:-}[$*] "; }
# finish: a scene exits non-zero if any command it ran failed
finish() {
    [ -z "${RUN_FAILED:-}" ] && return 0
    printf '\n%sFAILED: %s%s\n' "$R" "$RUN_FAILED" "$N"
    exit 1
}
say() { printf '\n%s# %s%s\n' "$Y" "$*" "$N"; }
beat() { sleep "${REEL_BEAT:-1}"; }
scene() { printf '%s== %s ==%s\n' "$B" "$*" "$N"; }

quick() { [ "$REEL_PUBLIC_URL" = quick ]; }

public_url() {
    if quick; then
        cat "$LOGS/public_url" 2> /dev/null
    else
        echo "$REEL_PUBLIC_URL"
    fi
}

# fetch_from <where> <url>: "<status> <page:yes|no>".
# "yes" needs the h1 AND a text/html Content-Type: a page sent
# as text/plain shows its source in a browser, though curl and
# grep see the same bytes (found on camera, scene 7).
# <where> is "here" (this Mac's resolver: the browser's
# path) or an ssh host. Nothing is written on the far side.
fetch_from() {
    _cmd="curl -s -m 15 -w '\\n%{content_type}\\n%{http_code}' '$2'"
    if [ "$1" = here ]; then
        _out=$(eval "$_cmd")
    else
        _out=$(ssh -o BatchMode=yes -o ConnectTimeout=10 "$1" "$_cmd")
    fi
    _st=$(printf '%s\n' "$_out" | tail -n 1)
    _ct=$(printf '%s\n' "$_out" | tail -n 2 | head -n 1)
    if printf '%s\n' "$_out" | grep -qF "$H1" &&
       case "$_ct" in text/html*) true ;; *) false ;; esac; then
        echo "$_st yes"
    else
        echo "$_st no"
    fi
}

# our_pid <name>: the pid in logs/reel-<name>.pid if, and only
# if, that pid is alive AND its command line is exactly the
# one this reel launched AND (for lobo) its cwd is the site.
our_pid() {
    _f=$LOGS/reel-$1.pid
    [ -f "$_f" ] || return 1
    _p=$(cat "$_f")
    _c=$(ps -p "$_p" -o command= 2> /dev/null) || return 1
    [ "$_c" = "$(cat "$LOGS/reel-$1.cmd")" ] || return 1
    if [ "$1" = lobo ]; then
        _d=$(lsof -a -p "$_p" -d cwd -Fn 2> /dev/null |
            sed -n 's/^n//p')
        [ "$_d" = "$SITE" ] || return 1
    fi
    echo "$_p"
}

tunnel_cmd() {
    if quick; then
        echo "cloudflared tunnel --no-autoupdate --url $LOCAL"
    else
        echo "cloudflared tunnel --no-autoupdate --config $REEL_TUNNEL_CONFIG run"
    fi
}

port_holder() {
    lsof -nP -iTCP:$PORT -sTCP:LISTEN -t 2> /dev/null
}

now() { perl -MTime::HiRes=time -e 'printf "%.3f\n", time'; }
secs() { awk "BEGIN { printf \"%.2f\", $2 - $1 }"; }

# lobo_src: the lobo checkout (scene 0's source; the pinned
# nginx oracle lives in its tests/differential/bin)
lobo_src() {
    [ -n "${REEL_LOBO_SRC:-}" ] && { echo "$REEL_LOBO_SRC"; return; }
    _t=$(git -C "$REEL" rev-parse --show-toplevel 2> /dev/null)
    if [ -n "$_t" ] && [ -f "$_t/src/main.lu" ] && [ -f "$_t/wolf.pkg" ]; then
        echo "$_t"
    else
        echo "$HOME/GithubOrgs/wolffe-lang/lobo"
    fi
}

# nginx_side: for the nginx contrasts in scenes 2 and 3. Finds
# an nginx (REEL_NGINX, else PATH, else lobo's pinned oracle),
# puts it first on PATH so
# the command on screen is the command that runs, and builds
# an nginx prefix in logs/nginx holding the SAME site.conf
# minus lobo's two native lines (nginx -t rejects them).
# Returns 1 (and the scene skips the contrast) without one.
nginx_side() {
    _ng=${REEL_NGINX:-$(command -v nginx)}
    [ -n "$_ng" ] || _ng=$(lobo_src)/tests/differential/bin/nginx
    [ -n "$_ng" ] && [ -x "$_ng" ] || return 1
    PATH=$(dirname "$_ng"):$PATH
    NGX=$LOGS/nginx
    rm -rf "$NGX"; mkdir -p "$NGX/conf" "$NGX/logs"
    printf 'pid logs/nginx.pid;\nevents {}\nhttp {\n    include site.conf;\n}\n' \
        > "$NGX/conf/nginx.conf"
    grep -v -E 'metrics|memory_budget' conf/site.conf \
        > "$NGX/conf/site.conf"
}
