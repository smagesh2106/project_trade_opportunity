#!/usr/bin/env bash
# Trade Opportunity Explorer API manual test commands
# Start the backend first:
# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

echo "=== 1. Supplier search ==="
curl -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":"Find suppliers of electrical panels to India"}'
echo

echo "=== 2. Global supplier search ==="
curl -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":"Find suppliers of electrical panels"}'
echo

echo "=== 3. Global buyer search ==="
curl -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":"Who imports electrical panels?"}'
echo

echo "=== 4. Buyer search in India ==="
curl -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":"Who imports electrical panels in India?"}'
echo

echo "=== 5. Buyers of Indian exports ==="
curl -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":"Who buys electrical panels from India?"}'
echo

echo "=== 6. Import opportunity ==="
curl -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":"Which countries should India source electrical panels from?"}'
echo

echo "=== 7. Export opportunity ==="
curl -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":"Which countries should India target for exporting electrical panels?"}'
echo

echo "=== 8. Market analysis ==="
curl -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":"How are electrical panel imports into India trending?"}'
echo

echo "=== 9. Country comparison ==="
curl -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":"Compare Germany and United Arab Emirates for electrical panels to India"}'
echo

echo "=== 10. Explicit valid period ==="
curl -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":"Find suppliers of electrical panels to India","period_start":"2025-01-01","period_end":"2025-12-31"}'
echo

echo "=== NEGATIVE TESTS ==="

echo "=== 11. Empty query: expect HTTP 400 ==="
curl -i -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":""}'
echo

echo "=== 12. Whitespace query: expect HTTP 400 ==="
curl -i -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":"   "}'
echo

echo "=== 13. Missing query: expect HTTP 422 ==="
curl -i -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{}'
echo

echo "=== 14. Null query: expect HTTP 422 ==="
curl -i -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":null}'
echo

echo "=== 15. Numeric query: expect HTTP 422 ==="
curl -i -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":12345}'
echo

echo "=== 16. Unknown product: expect HTTP 400 ==="
curl -i -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":"Find suppliers of solar powered bananas"}'
echo

echo "=== 17. Supplier location query: expect HTTP 400 ==="
curl -i -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":"Find suppliers of electrical panels in India"}'
echo

echo "=== 18. Invalid start date: expect HTTP 422 ==="
curl -i -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":"Find suppliers of electrical panels to India","period_start":"not-a-date"}'
echo

echo "=== 19. Invalid end date: expect HTTP 422 ==="
curl -i -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":"Find suppliers of electrical panels to India","period_end":"not-a-date"}'
echo

echo "=== 20. Start after end: expect HTTP 400 ==="
curl -i -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":"Find suppliers of electrical panels to India","period_start":"2025-12-31","period_end":"2025-01-01"}'
echo

echo "=== 21. Same-country comparison: expect HTTP 400 ==="
curl -i -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":"Compare Germany and Germany for electrical panels"}'
echo

echo "=== 22. One-country comparison: expect HTTP 400 ==="
curl -i -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":"Compare Germany for electrical panels"}'
echo

echo "=== 23. Malformed JSON: expect HTTP 422 ==="
curl -i -sS -X POST "$BASE_URL/api/v1/trade/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query":"Find suppliers of electrical panels to India"'
echo
