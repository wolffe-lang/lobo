# lib-toolchain.sh — sourced by every tool; not executable on its own.
# Resolves the pinned toolchain (wolf-std's order: $WOLF_BIN/$LUPIN_BIN
# → .wolf-bin/ → PATH) and verifies IDENTITY against
# wolf-toolchain.toml before anything runs. Identity is the FIRST line
# of `--version` only (the F-0064 lesson: wolf's second line names its
# lupin pairing — reported by doctor, never gated — and lupin's line
# names its conformance pin, which is information, not the rev).
# Callers get: $WOLF, $LUPIN, and libwolf_rt.a beside $WOLF.

toml_value() { # toml_value <section> <key>
    awk -v s="[$1]" -v k="$2" '
        $0 == s { in_s = 1; next }
        /^\[/ { in_s = 0 }
        in_s && $1 == k {
            sub(/^[^=]*= */, "")
            gsub(/"/, "")
            print
            exit
        }
    ' wolf-toolchain.toml
}

resolve_bin() { # resolve_bin <envval> <name>
    if [ -n "$1" ]; then echo "$1"; return; fi
    if [ -x ".wolf-bin/$2" ]; then echo ".wolf-bin/$2"; return; fi
    command -v "$2" 2>/dev/null
}

WOLF=$(resolve_bin "${WOLF_BIN:-}" wolf)
LUPIN=$(resolve_bin "${LUPIN_BIN:-}" lupin)

fail_pin() {
    echo "toolchain: REFUSED — $1" >&2
    echo "toolchain: the pin is wolf-toolchain.toml (wolf @ $(toml_value wolf rev | cut -c1-7), lupin @ $(toml_value lupin rev | cut -c1-7)); build per that file's notes into .wolf-bin/" >&2
    exit 1
}

[ -n "$WOLF" ] && [ -x "$WOLF" ] || fail_pin "no \`wolf\` binary (\$WOLF_BIN, .wolf-bin/, PATH all empty)"
[ -n "$LUPIN" ] && [ -x "$LUPIN" ] || fail_pin "no \`lupin\` binary (\$LUPIN_BIN, .wolf-bin/, PATH all empty)"

want_wolf=$(toml_value wolf version_line)
want_lupin=$(toml_value lupin version_line)
have_wolf=$("$WOLF" --version 2>/dev/null | head -1)
have_lupin=$("$LUPIN" --version 2>/dev/null | head -1)
[ "$have_wolf" = "$want_wolf" ] || fail_pin "wolf identity drift: have \"$have_wolf\", pin wants \"$want_wolf\""
[ "$have_lupin" = "$want_lupin" ] || fail_pin "lupin identity drift: have \"$have_lupin\", pin wants \"$want_lupin\""

# The native tier links against the runtime staticlib beside the driver.
if [ ! -f "$(dirname "$WOLF")/libwolf_rt.a" ] && [ -z "${WOLF_RT_LIB:-}" ]; then
    fail_pin "libwolf_rt.a is not beside $WOLF (and \$WOLF_RT_LIB is unset) — the native tier cannot link"
fi
