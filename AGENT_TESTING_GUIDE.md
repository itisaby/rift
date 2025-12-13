# Agent Testing Guide

Complete guide to testing Monitor, Diagnostic, and Remediation agents from the frontend.

## Quick Access

**New Agent Testing Page:** http://localhost:3000/agents

Or click the **"TEST AGENTS"** button in the dashboard navigation.

---

## Testing Methods

### Method 1: Using the Agent Testing Page (Recommended)

1. **Navigate to Agent Testing Page**
   - Go to http://localhost:3000/agents
   - Or click "TEST AGENTS" button in dashboard

2. **Step 1: Run Monitor Agent**
   - Click **"Run Detection"** button
   - Waits for infrastructure scan to complete
   - Shows detected incidents
   - Auto-fills the first incident ID

3. **Step 2: Run Diagnostic Agent**
   - Incident ID is pre-filled from Step 1
   - Click **"Run Diagnosis"** button
   - Shows AI-powered root cause analysis
   - Displays confidence score and recommendations

4. **Step 3: Run Remediation Agent**
   - Two options:
     - **Manual Approve**: Review the fix before execution
     - **Auto-Approve**: Automatically execute the fix
   - ⚠️ Warning: Makes actual infrastructure changes!

---

### Method 2: Using Demo Failure Injection

If you don't have real infrastructure issues:

1. **Go to Dashboard** (http://localhost:3000)

2. **Click "DEMO FAILURE" button** (red button, top right)
   - Creates a simulated CPU failure incident
   - Shows success alert with incident details

3. **Navigate to Incidents Page** (http://localhost:3000/incidents)
   - See the injected incident in the list
   - Click on it to view details

4. **Get Incident ID**
   - Copy the incident ID from the URL or page
   - Go to http://localhost:3000/agents
   - Paste the ID and run diagnosis/remediation

---

### Method 3: Using API Directly (Advanced)

#### 1. Monitor Agent - Detect Incidents

```bash
curl -X POST http://localhost:8000/incidents/detect \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "detected_incidents": 3,
  "incidents": [
    {
      "id": "incident-uuid-here",
      "resource_name": "web-server-1",
      "severity": "HIGH",
      "metric": "CPU_USAGE",
      "current_value": 95.0,
      "threshold_value": 80.0
    }
  ]
}
```

#### 2. Diagnostic Agent - Analyze Root Cause

```bash
curl -X POST http://localhost:8000/incidents/diagnose \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "YOUR_INCIDENT_ID_HERE"
  }'
```

**Response:**
```json
{
  "diagnosis": {
    "id": "diagnosis-uuid",
    "root_cause": "High CPU usage due to inefficient query",
    "root_cause_category": "performance",
    "confidence": 0.92,
    "reasoning": "Analysis shows...",
    "recommendations": [
      "Optimize database queries",
      "Add query caching"
    ]
  }
}
```

#### 3. Remediation Agent - Fix the Issue

```bash
curl -X POST http://localhost:8000/incidents/remediate \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "YOUR_INCIDENT_ID_HERE",
    "auto_approve": true
  }'
```

**Response:**
```json
{
  "result": {
    "id": "remediation-uuid",
    "status": "SUCCESS",
    "success": true,
    "action_taken": "Scaled CPU resources",
    "duration": 45,
    "verification_passed": true
  }
}
```

---

## Complete End-to-End Workflow

### Scenario: Test Full Agent Pipeline

1. **Inject Demo Failure**
   ```bash
   curl -X POST http://localhost:8000/demo/inject-failure \
     -H "Content-Type: application/json" \
     -d '{
       "failure_type": "cpu",
       "target": "test-server",
       "duration": 300
     }'
   ```

2. **Detect the Incident**
   - Frontend: Go to http://localhost:3000/agents → Click "Run Detection"
   - API: `POST /incidents/detect`

3. **Diagnose Root Cause**
   - Frontend: Click "Run Diagnosis"
   - API: `POST /incidents/diagnose` with incident_id

4. **Execute Remediation**
   - Frontend: Click "Manual Approve" or "Auto-Approve"
   - API: `POST /incidents/remediate` with incident_id and auto_approve flag

5. **Verify Results**
   - Check incident detail page: http://localhost:3000/incidents/{incident_id}
   - Verify incident status changed to "RESOLVED"
   - Check remediation logs

---

## Agent Testing Page Features

### Monitor Agent Card
- **Button**: "Run Detection"
- **Shows**:
  - Number of incidents found
  - List of detected incidents (up to 2)
  - Success/failure status
- **Auto-fills**: First incident ID for next steps

### Diagnostic Agent Card
- **Button**: "Run Diagnosis"
- **Requires**: Incident ID (auto-filled or manual)
- **Shows**:
  - Confidence score (percentage)
  - Root cause summary
  - Success/failure status

### Remediation Agent Card
- **Buttons**:
  - "Manual Approve" - Review before execution
  - "Auto-Approve" - Automatic execution
- **Requires**: Incident ID
- **Shows**:
  - Remediation status
  - Action taken
  - Success/failure status

---

## Testing Checklist

### ✅ Before Testing

- [ ] Backend is running (`python main.py`)
- [ ] Frontend is running (`npm run dev`)
- [ ] All 3 agents show as healthy (3/3 on dashboard)
- [ ] Have DigitalOcean API token configured
- [ ] Prometheus is accessible (for real monitoring)

### ✅ Test Scenarios

**Scenario 1: Demo Incident (No Real Infrastructure)**
- [ ] Inject demo failure from dashboard
- [ ] Navigate to agents page
- [ ] Run monitor → Should find injected incident
- [ ] Run diagnosis → Should show AI analysis
- [ ] Run remediation (manual) → Should show fix plan

**Scenario 2: Real Infrastructure Monitoring**
- [ ] Have tagged resources in DigitalOcean (`tag: rift`)
- [ ] Run monitor agent detection
- [ ] Verify real incidents are detected
- [ ] Diagnose real issues
- [ ] Test remediation (be careful!)

**Scenario 3: Manual Incident ID**
- [ ] Get incident ID from incidents page
- [ ] Paste into agent testing page
- [ ] Run diagnosis and remediation directly

---

## Expected Response Times

| Agent | Typical Response Time |
|-------|----------------------|
| Monitor Agent | 2-5 seconds |
| Diagnostic Agent | 5-10 seconds (AI processing) |
| Remediation Agent | 30-60 seconds (Terraform execution) |

---

## Troubleshooting

### Issue: "No incidents detected"

**Solution:**
1. Inject a demo failure first
2. Or ensure you have DigitalOcean resources tagged with `rift`
3. Check Prometheus is accessible

### Issue: "Incident ID required"

**Solution:**
1. Run Monitor Agent first
2. Or manually enter an incident ID from incidents page
3. Check incident ID is valid UUID format

### Issue: Diagnostic Agent fails

**Possible causes:**
- Incident doesn't exist
- Agent not initialized
- Knowledge base not configured

**Solution:**
- Check backend logs
- Verify incident exists: `GET /incidents/{incident_id}`
- Ensure `DIAGNOSTIC_AGENT_KEY` and `KNOWLEDGE_BASE_ID` are set

### Issue: Remediation fails

**Possible causes:**
- No diagnosis available for incident
- Terraform not configured
- Invalid action plan

**Solution:**
- Run diagnosis first
- Check Terraform is installed
- Review backend logs for detailed errors

---

## Safety Notes

⚠️ **Important Safety Information:**

1. **Remediation Makes Real Changes**
   - The remediation agent will execute actual Terraform changes
   - It can scale resources, restart services, modify configurations
   - Always use "Manual Approve" first to review the plan

2. **Cost Implications**
   - Scaling up resources costs money
   - Review estimated costs in diagnosis before remediation
   - Set `MAX_COST_AUTO_APPROVE` in backend `.env` to limit auto-approvals

3. **Testing Environment**
   - Use demo mode (`DEMO_MODE=true`) for testing
   - Test with non-production resources first
   - Tag test resources separately

4. **Rollback Capability**
   - Remediation agent creates rollback plans
   - State is backed up before changes
   - Can manually rollback via Terraform if needed

---

## Advanced: Testing with Real Infrastructure

### Prerequisites

1. **DigitalOcean Resources**
   - Create test droplets
   - Tag them with `rift` tag
   - Ensure they have metrics enabled

2. **Prometheus Setup**
   - Configure Prometheus to scrape your droplets
   - Verify metrics are being collected
   - Update `PROMETHEUS_URL` in `.env`

3. **Simulate Real Issues**
   ```bash
   # SSH into a test droplet
   ssh root@your-droplet-ip

   # Simulate high CPU
   stress-ng --cpu 8 --timeout 300s

   # Simulate high memory
   stress-ng --vm 1 --vm-bytes 2G --timeout 300s

   # Simulate disk usage
   dd if=/dev/zero of=/tmp/test bs=1G count=10
   ```

4. **Test Detection**
   - Wait 30 seconds for Prometheus to scrape metrics
   - Run monitor agent
   - Should detect the simulated issues

---

## Integration with Autonomous Mode

When `AUTO_REMEDIATION_ENABLED=true` in backend `.env`:

1. Monitor agent runs automatically every 30 seconds
2. Incidents are auto-diagnosed when detected
3. High-confidence fixes are auto-remediated (if confidence > `CONFIDENCE_THRESHOLD`)
4. Low-cost fixes are auto-approved (if cost < `MAX_COST_AUTO_APPROVE`)

**Test autonomous mode:**
1. Set `AUTO_REMEDIATION_ENABLED=true` in `.env`
2. Restart backend
3. Inject demo failure
4. Wait and watch - system should auto-detect, diagnose, and fix

---

## Monitoring Agent Execution

### View Real-Time Logs

**Backend logs:**
```bash
tail -f /Users/arnabmaity/Infra/backend/logs/rift.log
```

**Frontend console:**
- Open browser DevTools (F12)
- Console tab
- See agent execution logs in real-time

### WebSocket Events

When agents complete:
- `incident_detected` - Monitor found issues
- `diagnosis_complete` - Diagnostic finished
- `remediation_complete` - Fix executed

Dashboard auto-refreshes on these events!

---

## API Endpoints Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/incidents/detect` | POST | Run monitor agent |
| `/incidents/diagnose` | POST | Run diagnostic agent |
| `/incidents/remediate` | POST | Run remediation agent |
| `/incidents` | GET | List all incidents |
| `/incidents/{id}` | GET | Get incident details |
| `/agents/health` | GET | Check agent status |
| `/demo/inject-failure` | POST | Create test incident |

---

## Next Steps

After successful testing:

1. **Configure Real Monitoring**
   - Set up production Prometheus
   - Tag production resources
   - Enable autonomous mode

2. **Customize Agent Behavior**
   - Adjust thresholds in monitor agent
   - Configure confidence threshold
   - Set cost limits for auto-approval

3. **Review and Learn**
   - Check knowledge base entries
   - Review remediation logs
   - Analyze what worked/what didn't

4. **Scale Up**
   - Add more cloud providers (AWS, Azure, GCP)
   - Increase monitoring frequency
   - Add custom remediation actions

---

## Success Criteria

Your agent testing is successful when:

✅ Monitor agent detects incidents (real or demo)
✅ Diagnostic agent provides root cause with >70% confidence
✅ Remediation agent successfully executes fixes
✅ Incidents transition: DETECTED → DIAGNOSED → RESOLVED
✅ All operations complete without errors
✅ WebSocket shows real-time updates

Happy testing! 🚀
