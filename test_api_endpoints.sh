#!/bin/bash
# Test all critical API endpoints

echo "Testing Loki IDS API Endpoints..."
echo "=================================="
echo ""

BASE_URL="http://localhost:8080"

test_endpoint() {
    local endpoint=$1
    local name=$2

    echo -n "Testing $name... "
    response=$(curl -s -w "\n%{http_code}" --max-time 5 "$BASE_URL$endpoint" 2>&1)
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)

    if [ "$http_code" = "200" ]; then
        echo "✓ OK (200)"
        echo "   Response: ${body:0:100}"
    elif [ -z "$http_code" ] || [ "$http_code" = "000" ]; then
        echo "✗ FAILED - No response (timeout or connection refused)"
    else
        echo "✗ FAILED - HTTP $http_code"
        echo "   Response: ${body:0:100}"
    fi
    echo ""
}

# Test critical endpoints used by the dashboard
test_endpoint "/api/stats" "Stats endpoint"
test_endpoint "/api/system/status" "System status"
test_endpoint "/api/alerts?page=1&page_size=10" "Alerts endpoint"
test_endpoint "/api/system/health" "Health check"
test_endpoint "/api/signatures?page=1&page_size=5" "Signatures endpoint"

echo "=================================="
echo "Test complete!"