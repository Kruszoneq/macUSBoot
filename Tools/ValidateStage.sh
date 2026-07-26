#!/bin/sh

set -eu
export LC_ALL=C

fail() {
    echo "StageTwo validation failed: $1" >&2
    exit 1
}

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <stage-artifact>" >&2
    exit 2
fi

artifact=$1

[ -f "$artifact" ] || fail "artifact is not a regular file"

size=$(wc -c < "$artifact" | tr -d ' ')
[ "$size" -gt 0 ] || fail "artifact is empty"
[ $((size % 512)) -eq 0 ] || fail "size is not a multiple of 512 bytes"

set -- $(od -An -tu1 -N2 "$artifact")
[ "$1" -eq 235 ] || fail "header does not begin with a short jump"
[ "$2" -le 127 ] || fail "entry jump is not a positive short displacement"
jump_target=$((2 + $2))

magic=$(od -An -tx1 -j2 -N4 "$artifact" | tr -d ' \n')
[ "$magic" = "4d555342" ] || fail "magic is not MUSB"

set -- $(od -An -tu1 -j6 -N2 "$artifact")
[ "$1" -eq 1 ] || fail "unsupported format version"
[ "$2" -eq 16 ] || fail "header size is not 16 bytes"

set -- $(od -An -tu1 -j8 -N2 "$artifact")
sector_count=$(( $1 + $2 * 256 ))
[ "$sector_count" -ge 1 ] || fail "sector count is zero"
[ "$sector_count" -le 64 ] || fail "sector count exceeds 64"
[ "$size" -eq $((sector_count * 512)) ] || fail "sector count does not match artifact size"

set -- $(od -An -tu1 -j10 -N2 "$artifact")
entry_offset=$(( $1 + $2 * 256 ))
[ "$entry_offset" -ge 16 ] || fail "entry offset overlaps the header"
[ "$entry_offset" -lt $((size - 4)) ] || fail "entry offset overlaps or follows the end marker"
[ "$entry_offset" -eq "$jump_target" ] || fail "entry offset does not match the initial jump"

set -- $(od -An -tu1 -j12 -N4 "$artifact")
[ "$1" -eq 0 ] && [ "$2" -eq 0 ] && [ "$3" -eq 0 ] && [ "$4" -eq 0 ] || fail "version 1 flags are not zero"

tail=$(od -An -tx1 -j$((size - 4)) -N4 "$artifact" | tr -d ' \n')
[ "$tail" = "4d454e44" ] || fail "final marker is not MEND"

echo "StageTwo format valid: ${sector_count} sectors, ${size} bytes, entry offset ${entry_offset}."
