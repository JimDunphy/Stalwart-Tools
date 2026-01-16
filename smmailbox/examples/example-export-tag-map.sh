#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SMM="$SCRIPT_DIR/../smmailbox"

: "${ZIMBRA_PASS:?set ZIMBRA_PASS in the environment}"

"$SMM" export-tag-map \
  --src-host mail.example.com \
  --src-user user@example.com \
  --src-password-env ZIMBRA_PASS \
  --out-csv "$SCRIPT_DIR/tagmap.csv"
