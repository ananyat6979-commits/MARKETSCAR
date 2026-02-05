#!/usr/bin/env bash
set -e
OUT=${1:-.secrets}
mkdir -p "$OUT"
PRIVATE="$OUT/dev_rsa.pem"
PUBLIC="$OUT/dev_rsa.pub"
openssl genpkey -algorithm RSA -out "$PRIVATE" -pkeyopt rsa_keygen_bits:2048
openssl rsa -in "$PRIVATE" -pubout -out "$PUBLIC"
chmod 600 "$PRIVATE"
echo "Generated keys: $PRIVATE, $PUBLIC"
