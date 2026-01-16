#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SMM="$SCRIPT_DIR/../smmailbox"

"$SMM" bridge-import-tags \
  --tagmap-json "$SCRIPT_DIR/tagmap.json" \
  --bridge-host stalwart.example.com \
  --bridge-username user@example.com \
  --bridge-account-id c
