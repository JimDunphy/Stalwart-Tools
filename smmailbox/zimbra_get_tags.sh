#!/usr/bin/env bash

set -euo pipefail

# ----------------------------
# CONFIG
# ----------------------------
ZIMBRA_HOST="mail.example.com"
USERNAME="user@example.com"
PASSWORD="CHANGE_ME"

SOAP_URL="https://${ZIMBRA_HOST}/service/soap"

# ----------------------------
# LOGIN: Get Auth Token
# ----------------------------
AUTH_XML="$(cat <<'EOF'
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
  <soap:Body>
    <AuthRequest xmlns="urn:zimbraAccount">
      <account by="name">__USERNAME__</account>
      <password>__PASSWORD__</password>
    </AuthRequest>
  </soap:Body>
</soap:Envelope>
EOF
)"

AUTH_XML="${AUTH_XML/__USERNAME__/${USERNAME}}"
AUTH_XML="${AUTH_XML/__PASSWORD__/${PASSWORD}}"

AUTH_RESPONSE="$(curl -sk "${SOAP_URL}" \
  -H "Content-Type: application/soap+xml" \
  --data "${AUTH_XML}")"

AUTH_TOKEN="$(echo "${AUTH_RESPONSE}" | sed -n 's:.*<authToken>\(.*\)</authToken>.*:\1:p')"

if [[ -z "${AUTH_TOKEN}" ]]; then
  echo "ERROR: Failed to obtain auth token"
  echo
  echo "Raw response:"
  echo "${AUTH_RESPONSE}"
  exit 1
fi

echo "Auth token obtained."

# ----------------------------
# GET TAGS
# ----------------------------
TAG_XML="$(cat <<'EOF'
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
  <soap:Header>
    <context xmlns="urn:zimbra">
      <authToken>__TOKEN__</authToken>
    </context>
  </soap:Header>
  <soap:Body>
    <GetTagRequest xmlns="urn:zimbraMail"/>
  </soap:Body>
</soap:Envelope>
EOF
)"

TAG_XML="${TAG_XML/__TOKEN__/${AUTH_TOKEN}}"

TAG_RESPONSE="$(curl -sk "${SOAP_URL}" \
  -H "Content-Type: application/soap+xml" \
  --data "${TAG_XML}")"

echo
echo "Raw SOAP response:"
echo "----------------------------"
echo "${TAG_RESPONSE}"
echo

# ----------------------------
# Extract tag lines
# ----------------------------
echo "Parsed tags:"
echo "----------------------------"

echo "${TAG_RESPONSE}" \
  | tr '<' '\n' \
  | grep '^tag ' \
  || true

