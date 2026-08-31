#!/usr/bin/env bash
set -u

cd /home/magesh/02_Projects/project_trade_opportunity/backend || exit 1

echo "=============================================="
echo "Trade Opportunity Explorer - Backend Tests"
echo "=============================================="
echo

echo "=== 1. Structured TradeQuery validation ==="
python -m tests.integration.test_trade_query_validation
status=$?

if [ "$status" -ne 0 ]; then
    echo
    echo "STRUCTURED VALIDATION TESTS FAILED"
    exit "$status"
fi

echo
echo "=== 2. Existing API integration tests ==="
python -m tests.integration.test_trade_api
status=$?

if [ "$status" -ne 0 ]; then
    echo
    echo "API INTEGRATION TESTS FAILED"
    exit "$status"
fi

echo
echo "=============================================="
echo "BACKEND VALIDATION CHECK PASSED"
echo "=============================================="
