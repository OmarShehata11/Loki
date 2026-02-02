#!/bin/bash
# Quick test script for IoT web interface
# This script performs basic connectivity and API tests

echo "=========================================="
echo "  IoT Web Interface - Quick Test"
echo "=========================================="
echo ""

BASE_URL="http://localhost:8080"
API_BASE="${BASE_URL}/api/iot"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Test function
test_endpoint() {
    local name=$1
    local method=$2
    local url=$3
    local expected_status=$4
    
    echo -n "Testing: $name... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}FAIL${NC} (HTTP $http_code, expected $expected_status)"
        echo "  Response: $body"
        ((FAILED++))
        return 1
    fi
}

# Check if server is running
echo "Checking if web server is running..."
if curl -s -f "$BASE_URL" > /dev/null; then
    echo -e "${GREEN}✓${NC} Web server is running"
else
    echo -e "${RED}✗${NC} Web server is not running!"
    echo "Please start the server with: ./start_web_server.sh"
    exit 1
fi

echo ""
echo "Running API tests..."
echo ""

# Test 1: MQTT Status
test_endpoint "MQTT Status" "GET" "${API_BASE}/mqtt/status" "200"

# Test 2: Get Devices
test_endpoint "Get Devices" "GET" "${API_BASE}/devices" "200"

# Test 3: Connect MQTT
test_endpoint "Connect MQTT" "POST" "${API_BASE}/mqtt/connect?host=127.0.0.1&port=1883" "200"

# Test 4: Get Device State (ESP32-1)
test_endpoint "Get ESP32-1 State" "GET" "${API_BASE}/devices/esp32-1/state" "200"

# Test 5: Get Device State (ESP32-2)
test_endpoint "Get ESP32-2 State" "GET" "${API_BASE}/devices/esp32-2/state" "200"

# Test 6: RGB Control (may fail if MQTT not connected, but should return proper error)
test_endpoint "RGB Control" "POST" "${API_BASE}/devices/esp32-2/rgb?color=%23FF0000&brightness=255&effect=solid" "200"

# Test 7: Buzzer Control
test_endpoint "Buzzer Control" "POST" "${API_BASE}/devices/esp32-1/buzzer?action=beep&duration=500" "200"

# Test 8: Alarm Control
test_endpoint "Alarm Control" "POST" "${API_BASE}/devices/esp32-1/alarm?action=test" "200"

echo ""
echo "=========================================="
echo "  Test Results"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${YELLOW}Some tests failed. Check MQTT broker and ESP32 connections.${NC}"
    exit 1
fi
