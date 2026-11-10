#!/bin/bash
# Regenerate one path's lines of app_decks.md5 — the list of decks the APPS ship, which is the only thing this repo
# may serve.
#
# ONE update path: regenerate from the iOS release branch that ships the decks, commit it in the same PR as the deck
# change here, and the deck-parity check verifies the PR against it.
# (Android's bundled decks are held byte-identical to iOS by the apps' own md5 parity test.)
#
#   usage:  tools/regen_app_decks_md5.sh <path-to-forbidden-ios-checkout> <ref> [topics7]
#   e.g.    tools/regen_app_decks_md5.sh ../ios origin/release/2.9.0            # the root (apps up to 2.13.0)
#           tools/regen_app_decks_md5.sh ../ios origin/release/2.14.0 topics7    # the apps that ship Geography
#
# Without a third argument it rewrites the ROOT lines (and the legacy game_data.json alias) and refuses a deck with a
# topic outside the six older ones: older apps read the root (contract topic_rotation.md section 8). With `topics7`
# it rewrites only the `topics7/` lines. Lines of the other path are kept as they are. Writes app_decks.md5 only.
case "${1:-}" in -h|--help) sed -n '2,/^[^#]/{/^#/s/^# \{0,1\}//p;}' "$0"; exit 0 ;; esac
set -euo pipefail
IOS="${1:?path to the forbidden-ios checkout}"; REF="${2:?git ref of the shipping release, e.g. origin/release/2.9.0}"
PATHNAME="${3:-}"
case "$PATHNAME" in ""|topics7) ;; *) echo "unknown path '$PATHNAME' (root or topics7)" >&2; exit 2 ;; esac
PRE="${PATHNAME:+$PATHNAME/}"
DIR="Taboo/Resources/Data"
SHA=$(git -C "$IOS" rev-parse --short "$REF")
OUT="$(cd "$(dirname "$0")/.." && pwd)/app_decks.md5"
files=$(git -C "$IOS" ls-tree --name-only "$REF" "$DIR/" | sed "s#^$DIR/##" | grep -E '^game_data_[a-z]+\.json$')
[ -n "$files" ] || { echo "no game_data_*.json under $DIR at $REF" >&2; exit 1; }
md5of() { git -C "$IOS" show "$REF:$DIR/$1" | python3 -c 'import hashlib,sys;print(hashlib.md5(sys.stdin.buffer.read()).hexdigest())'; }
if [ -z "$PRE" ]; then
  for f in $files; do
    git -C "$IOS" show "$REF:$DIR/$f" | python3 -c '
import json,sys
old={"cultural","sports","movies_tv","food_drink","science","history"}
extra=sorted({t.get("topic") for t in json.load(sys.stdin).get("data",[])}-old)
if extra: sys.exit(f"'"$f"': carries {extra}; the root serves only the six older topics (use: ... topics7)")
'
  done
fi
tmp=$(mktemp)
{
  echo "# App-bundled decks. Do not edit by hand: tools/regen_app_decks_md5.sh writes each path's lines."
  echo "# game_data.json is the legacy (v2.0.0) alias of the English deck. topics7/ = apps that ship Geography."
  # keep the other path's lines (and its source note)
  if [ -f "$OUT" ]; then
    grep -E '^# (root|topics7): ' "$OUT" | grep -v "^# ${PATHNAME:-root}: " || true
    grep -vE '^#' "$OUT" | awk -v pre="$PRE" 'NF==2 { isT=($2 ~ /^topics7\//); if ((pre=="" && isT) || (pre!="" && !isT)) print }'
  fi
  echo "# ${PATHNAME:-root}: from forbidden-ios $REF @ $SHA ($DIR)"
  for f in $files; do
    printf '%s  %s\n' "$(md5of "$f")" "$PRE$f"
  done
  [ -z "$PRE" ] && printf '%s  %s\n' "$(md5of game_data_en.json)" "game_data.json"
  true
} > "$tmp"
mv "$tmp" "$OUT"
echo "wrote $OUT ($(grep -vc '^#' "$OUT") decks; ${PATHNAME:-root} from $REF @ $SHA)"
