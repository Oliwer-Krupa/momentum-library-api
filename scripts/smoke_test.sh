#!/bin/sh
set -eu

BASE_URL="${BASE_URL:-http://localhost:8000}"
SERIAL="${SERIAL:-999001}"

RESP="/tmp/smoke_resp.$$"
trap 'rm -f "$RESP"' EXIT

request() {
  method="$1"
  url="$2"
  body="${3-}"
  if [ -n "$body" ]; then
    code=$(curl -s -o "$RESP" -w "%{http_code}" -X "$method" \
      -H "Content-Type: application/json" -d "$body" \
      "${BASE_URL}${url}")
  else
    code=$(curl -s -o "$RESP" -w "%{http_code}" -X "$method" \
      "${BASE_URL}${url}")
  fi
  printf "%s" "$code"
}

assert_code() {
  expected="$1"
  actual="$2"
  step="$3"
  if [ "$actual" -ne "$expected" ]; then
    echo "FAIL: ${step} (expected ${expected}, got ${actual})"
    cat "$RESP"
    exit 1
  fi
}

echo "Waiting for API at ${BASE_URL} ..."
i=1
while [ "$i" -le 30 ]; do
  if curl -fsS "${BASE_URL}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 1
  i=$((i + 1))
done
if [ "$i" -gt 30 ]; then
  echo "FAIL: API did not become ready in time"
  exit 1
fi

echo "Smoke test start"

code=$(request "GET" "/health")
assert_code 200 "$code" "health"

code=$(request "DELETE" "/books/${SERIAL}")
if [ "$code" -ne 204 ] && [ "$code" -ne 404 ]; then
  assert_code 204 "$code" "cleanup"
fi

create_body=$(printf '{"serial_number":"%s","title":"Smoke Test","author":"Smoke Tester"}' "$SERIAL")
code=$(request "POST" "/books/" "$create_body")
assert_code 201 "$code" "create"

code=$(request "GET" "/books/")
assert_code 200 "$code" "list"

borrow_body='{"borrower_card_number":"654321"}'
code=$(request "PATCH" "/books/${SERIAL}/borrow" "$borrow_body")
assert_code 200 "$code" "borrow"

code=$(request "GET" "/books/?status=BORROWED")
assert_code 200 "$code" "filter"

code=$(request "PATCH" "/books/${SERIAL}/return")
assert_code 200 "$code" "return"

code=$(request "DELETE" "/books/${SERIAL}")
assert_code 204 "$code" "delete"

echo "Smoke test OK"
