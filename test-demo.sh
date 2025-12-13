#!/bin/bash

# 🎬 Rift Demo Test Script
# Quick validation of all demo components

set -e

API_URL="http://localhost:8000"
PROMETHEUS_URL="http://104.236.4.131:9090"

echo "🎯 Rift Demo Pre-Flight Check"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "Testing $name... "
    
    response_code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$response_code" -eq "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} ($response_code)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (got $response_code, expected $expected_code)"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "📡 Infrastructure Health Checks"
echo "--------------------------------"

# 1. Backend API
test_endpoint "Backend API" "$API_URL/status"

# 2. Frontend (if running)
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    test_endpoint "Frontend" "http://localhost:3000"
else
    echo -e "${YELLOW}⚠ Frontend not running (optional)${NC}"
fi

# 3. Prometheus
test_endpoint "Prometheus" "$PROMETHEUS_URL/-/healthy"

echo ""
echo "🤖 AI Agents Check"
echo "--------------------------------"

# 4. Agents Status
agents_response=$(curl -s "$API_URL/agents")
if echo "$agents_response" | grep -q "Monitor Agent"; then
    echo -e "${GREEN}✓ Monitor Agent${NC} registered"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Monitor Agent${NC} not found"
    ((TESTS_FAILED++))
fi

if echo "$agents_response" | grep -q "Diagnostic Agent"; then
    echo -e "${GREEN}✓ Diagnostic Agent${NC} registered"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Diagnostic Agent${NC} not found"
    ((TESTS_FAILED++))
fi

if echo "$agents_response" | grep -q "Remediation Agent"; then
    echo -e "${GREEN}✓ Remediation Agent${NC} registered"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Remediation Agent${NC} not found"
    ((TESTS_FAILED++))
fi

if echo "$agents_response" | grep -q "Provisioner Agent"; then
    echo -e "${GREEN}✓ Provisioner Agent${NC} registered"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Provisioner Agent${NC} not found"
    ((TESTS_FAILED++))
fi

echo ""
echo "📊 Metrics Collection Check"
echo "--------------------------------"

# 5. Prometheus Metrics
metrics_response=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=up")
if echo "$metrics_response" | grep -q '"status":"success"'; then
    metric_count=$(echo "$metrics_response" | grep -o '"value"' | wc -l)
    echo -e "${GREEN}✓ Prometheus Metrics${NC} ($metric_count active targets)"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Prometheus Metrics${NC} not available"
    ((TESTS_FAILED++))
fi

# 6. Check specific droplets
for droplet in "104.236.4.131:9100" "134.209.37.250:9100" "174.138.62.125:9100"; do
    if curl -s "$PROMETHEUS_URL/api/v1/query?query=up{instance=\"$droplet\"}" | grep -q '"1"'; then
        echo -e "${GREEN}✓ Droplet $droplet${NC} is being monitored"
        ((TESTS_PASSED++))
    else
        echo -e "${YELLOW}⚠ Droplet $droplet${NC} metrics not found"
        ((TESTS_FAILED++))
    fi
done

echo ""
echo "🧪 Demo Functionality Check"
echo "--------------------------------"

# 7. Demo Mode Enabled
if curl -s "$API_URL/status" | grep -q '"demo_mode":true'; then
    echo -e "${GREEN}✓ Demo Mode${NC} enabled"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ Demo Mode${NC} disabled (enable in .env)"
    ((TESTS_FAILED++))
fi

# 8. Test Demo Injection Endpoint
echo -n "Testing incident injection... "
inject_response=$(curl -s -X POST "$API_URL/demo/inject-failure" \
    -H "Content-Type: application/json" \
    -d '{"resource_name":"demo-web-app","failure_type":"high_cpu"}' 2>&1)

if echo "$inject_response" | grep -q '"success":true' || echo "$inject_response" | grep -q 'incident_id'; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((TESTS_PASSED++))
    
    # Extract incident ID
    incident_id=$(echo "$inject_response" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
    if [ -n "$incident_id" ]; then
        echo "  Created incident: $incident_id"
    fi
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  Response: $inject_response"
    ((TESTS_FAILED++))
fi

echo ""
echo "================================"
echo "📈 Test Results Summary"
echo "================================"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All systems ready for demo!${NC}"
    echo ""
    echo "🎬 Demo is ready to present!"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend: http://localhost:8000"
    echo "   Prometheus: http://104.236.4.131:9090"
    echo ""
    echo "📖 See JUDGE_DEMO_SCRIPT.md for presentation guide"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please fix before demo.${NC}"
    exit 1
fi
