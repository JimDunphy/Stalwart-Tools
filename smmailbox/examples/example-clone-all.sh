#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SMM="$SCRIPT_DIR/../smmailbox"

: "${ZIMBRA_PASS:?set ZIMBRA_PASS in the environment}"
: "${STALWART_PASS:?set STALWART_PASS in the environment}"

"$SMM" clone-all \
  --src-host mail.example.com \
  --src-user user@example.com \
  --src-password-env ZIMBRA_PASS \
  --dst-host stalwart.example.com \
  --dst-user user@example.com \
  --dst-password-env STALWART_PASS
