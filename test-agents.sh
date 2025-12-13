#!/bin/bash

# Rift Agent Testing Script
# Automates the process of testing Monitor, Diagnostic, and Remediation agents

set -e

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
DROPLET_IP="${DROPLET_IP:-}"
STRESS_DURATION="${STRESS_DURATION:-300}"  # 5 minutes default

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_step() {
    echo -e "${PURPLE}➤ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check if backend is running
    if curl -s "$API_URL/health" > /dev/null 2>&1; then
        print_success "Backend is running at $API_URL"
    else
        print_error "Backend is not running at $API_URL"
        echo "Please start the backend: cd backend && python main.py"
        exit 1
    fi

    # Check if doctl is installed
    if command -v doctl &> /dev/null; then
        print_success "DigitalOcean CLI (doctl) is installed"
    else
        print_error "doctl is not installed"
        echo "Install it: https://docs.digitalocean.com/reference/doctl/how-to/install/"
        exit 1
    fi

    # Check if jq is installed
    if command -v jq &> /dev/null; then
        print_success "jq is installed"
    else
        print_info "jq is not installed (optional, but recommended)"
        echo "Install it: brew install jq (macOS) or apt install jq (Linux)"
    fi
}

# Step 1: Inject demo failure
inject_demo_failure() {
    print_header "Step 1: Injecting Demo Failure"

    print_step "Creating simulated CPU failure..."

    RESPONSE=$(curl -s -X POST "$API_URL/demo/inject-failure" \
        -H "Content-Type: application/json" \
        -d '{
            "failure_type": "cpu",
            "target": "demo-server",
            "duration": 300
        }')

    if echo "$RESPONSE" | grep -q "success"; then
        INCIDENT_ID=$(echo "$RESPONSE" | jq -r '.incident_id' 2>/dev/null || echo "$RESPONSE" | grep -o '"incident_id":"[^"]*' | cut -d'"' -f4)
        print_success "Demo failure injected!"
        print_info "Incident ID: $INCIDENT_ID"
        echo "$INCIDENT_ID" > /tmp/rift_incident_id.txt
    else
        print_error "Failed to inject demo failure"
        echo "$RESPONSE"
        exit 1
    fi
}

# Step 2: Run monitor agent
run_monitor_agent() {
    print_header "Step 2: Running Monitor Agent"

    print_step "Scanning infrastructure for incidents..."

    RESPONSE=$(curl -s -X POST "$API_URL/incidents/detect" \
        -H "Content-Type: application/json")

    if command -v jq &> /dev/null; then
        INCIDENT_COUNT=$(echo "$RESPONSE" | jq '.detected_incidents' 2>/dev/null || echo "0")
        print_success "Monitor Agent completed!"
        print_info "Detected $INCIDENT_COUNT incident(s)"

        # Get first incident ID if available
        FIRST_INCIDENT=$(echo "$RESPONSE" | jq -r '.incidents[0].id' 2>/dev/null || echo "")
        if [ -n "$FIRST_INCIDENT" ] && [ "$FIRST_INCIDENT" != "null" ]; then
            echo "$FIRST_INCIDENT" > /tmp/rift_incident_id.txt
            print_info "Selected incident: $FIRST_INCIDENT"
        fi
    else
        print_success "Monitor Agent completed!"
        echo "$RESPONSE"
    fi
}

# Step 3: Run diagnostic agent
run_diagnostic_agent() {
    print_header "Step 3: Running Diagnostic Agent"

    if [ ! -f /tmp/rift_incident_id.txt ]; then
        print_error "No incident ID found. Run monitor agent first."
        exit 1
    fi

    INCIDENT_ID=$(cat /tmp/rift_incident_id.txt)
    print_step "Diagnosing incident: $INCIDENT_ID"

    RESPONSE=$(curl -s -X POST "$API_URL/incidents/diagnose" \
        -H "Content-Type: application/json" \
        -d "{\"incident_id\": \"$INCIDENT_ID\"}")

    if command -v jq &> /dev/null; then
        ROOT_CAUSE=$(echo "$RESPONSE" | jq -r '.diagnosis.root_cause' 2>/dev/null || echo "Unknown")
        CONFIDENCE=$(echo "$RESPONSE" | jq -r '.diagnosis.confidence' 2>/dev/null || echo "0")

        print_success "Diagnostic Agent completed!"
        print_info "Root Cause: $ROOT_CAUSE"
        print_info "Confidence: $(echo "$CONFIDENCE * 100" | bc 2>/dev/null || echo "$CONFIDENCE")%"
    else
        print_success "Diagnostic Agent completed!"
        echo "$RESPONSE"
    fi
}

# Step 4: Run remediation agent
run_remediation_agent() {
    print_header "Step 4: Running Remediation Agent"

    if [ ! -f /tmp/rift_incident_id.txt ]; then
        print_error "No incident ID found. Run monitor and diagnostic agents first."
        exit 1
    fi

    INCIDENT_ID=$(cat /tmp/rift_incident_id.txt)

    # Ask for confirmation
    echo -e "${YELLOW}⚠️  This will execute actual remediation!${NC}"
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Remediation cancelled."
        exit 0
    fi

    print_step "Executing remediation for incident: $INCIDENT_ID"

    RESPONSE=$(curl -s -X POST "$API_URL/incidents/remediate" \
        -H "Content-Type: application/json" \
        -d "{\"incident_id\": \"$INCIDENT_ID\", \"auto_approve\": true}")

    if command -v jq &> /dev/null; then
        STATUS=$(echo "$RESPONSE" | jq -r '.result.status' 2>/dev/null || echo "Unknown")
        SUCCESS=$(echo "$RESPONSE" | jq -r '.result.success' 2>/dev/null || echo "false")
        ACTION=$(echo "$RESPONSE" | jq -r '.result.action_taken' 2>/dev/null || echo "Unknown")

        if [ "$SUCCESS" = "true" ]; then
            print_success "Remediation Agent completed!"
        else
            print_error "Remediation failed!"
        fi
        print_info "Status: $STATUS"
        print_info "Action: $ACTION"
    else
        print_success "Remediation Agent completed!"
        echo "$RESPONSE"
    fi
}

# Step 5: Simulate real droplet failure
simulate_droplet_failure() {
    print_header "Step 5: Simulating Real Droplet Failure"

    if [ -z "$DROPLET_IP" ]; then
        print_error "DROPLET_IP not set"
        echo "Usage: DROPLET_IP=<ip> $0 simulate"
        exit 1
    fi

    print_step "Connecting to droplet at $DROPLET_IP..."

    # Check if stress-ng is installed
    print_step "Checking if stress-ng is installed..."
    if ssh root@$DROPLET_IP "command -v stress-ng" &> /dev/null; then
        print_success "stress-ng is installed"
    else
        print_info "Installing stress-ng on droplet..."
        ssh root@$DROPLET_IP "apt update && apt install -y stress-ng"
    fi

    # Start stress test
    print_step "Starting CPU stress test (${STRESS_DURATION}s)..."
    ssh root@$DROPLET_IP "nohup stress-ng --cpu 1 --cpu-load 95 --timeout ${STRESS_DURATION}s > /dev/null 2>&1 &"

    print_success "Stress test started!"
    print_info "Wait 30-60 seconds for Prometheus to scrape metrics"
    print_info "Then run: $0 monitor"
}

# View incident details
view_incident() {
    print_header "Viewing Incident Details"

    if [ ! -f /tmp/rift_incident_id.txt ]; then
        print_error "No incident ID found"
        exit 1
    fi

    INCIDENT_ID=$(cat /tmp/rift_incident_id.txt)
    print_step "Fetching details for incident: $INCIDENT_ID"

    RESPONSE=$(curl -s "$API_URL/incidents/$INCIDENT_ID")

    if command -v jq &> /dev/null; then
        echo "$RESPONSE" | jq .
    else
        echo "$RESPONSE"
    fi
}

# Full workflow
run_full_workflow() {
    print_header "Running Full Agent Workflow"

    inject_demo_failure
    sleep 2

    run_monitor_agent
    sleep 2

    run_diagnostic_agent
    sleep 2

    run_remediation_agent

    print_header "Workflow Complete!"
    print_success "All agents executed successfully"
    print_info "View details at: http://localhost:3000/agents"
}

# Cleanup
cleanup() {
    print_header "Cleanup"

    if [ -f /tmp/rift_incident_id.txt ]; then
        rm /tmp/rift_incident_id.txt
        print_success "Cleaned up temporary files"
    fi

    if [ -n "$DROPLET_IP" ]; then
        print_step "Stopping stress test on droplet..."
        ssh root@$DROPLET_IP "pkill stress-ng" 2>/dev/null || true
        print_success "Stress test stopped"
    fi
}

# Main menu
show_menu() {
    echo -e "\n${BLUE}Rift Agent Testing Script${NC}\n"
    echo "1) Check Prerequisites"
    echo "2) Inject Demo Failure"
    echo "3) Run Monitor Agent"
    echo "4) Run Diagnostic Agent"
    echo "5) Run Remediation Agent"
    echo "6) Run Full Workflow (All Steps)"
    echo "7) Simulate Real Droplet Failure"
    echo "8) View Incident Details"
    echo "9) Cleanup"
    echo "0) Exit"
    echo
}

# Main script
main() {
    case "${1:-menu}" in
        check)
            check_prerequisites
            ;;
        inject)
            inject_demo_failure
            ;;
        monitor)
            run_monitor_agent
            ;;
        diagnose)
            run_diagnostic_agent
            ;;
        remediate)
            run_remediation_agent
            ;;
        full)
            run_full_workflow
            ;;
        simulate)
            simulate_droplet_failure
            ;;
        view)
            view_incident
            ;;
        cleanup)
            cleanup
            ;;
        menu)
            while true; do
                show_menu
                read -p "Select option: " choice
                case $choice in
                    1) check_prerequisites ;;
                    2) inject_demo_failure ;;
                    3) run_monitor_agent ;;
                    4) run_diagnostic_agent ;;
                    5) run_remediation_agent ;;
                    6) run_full_workflow ;;
                    7) simulate_droplet_failure ;;
                    8) view_incident ;;
                    9) cleanup ;;
                    0) exit 0 ;;
                    *) print_error "Invalid option" ;;
                esac
                echo
                read -p "Press Enter to continue..."
            done
            ;;
        *)
            echo "Usage: $0 {check|inject|monitor|diagnose|remediate|full|simulate|view|cleanup|menu}"
            echo
            echo "Examples:"
            echo "  $0 check                    # Check prerequisites"
            echo "  $0 full                     # Run complete workflow"
            echo "  DROPLET_IP=1.2.3.4 $0 simulate  # Simulate real failure"
            echo "  $0 menu                     # Interactive menu"
            exit 1
            ;;
    esac
}

main "$@"
