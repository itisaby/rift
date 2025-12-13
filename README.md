# 🌌 Rift

> **Rift through operational complexity**

Autonomous infrastructure orchestration powered by DigitalOcean Gradient AI + Model Context Protocol

**Opening rifts to create, closing rifts to fix - all at machine speed.**

[![Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://rift.demo)
[![Built with DigitalOcean](https://img.shields.io/badge/Built%20with-DigitalOcean-0080FF)](https://www.digitalocean.com)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## 📋 Table of Contents

- [What is Rift?](#what-is-rift)
- [Project Structure](#project-structure)
- [Frontend Setup](#frontend-setup)
- [Backend Setup](#backend-setup)
- [Running the Complete System](#running-the-complete-system)
- [Design System](#design-system)
- [Demo Guide](#demo-guide)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)

---

## 🎯 What is Rift?

Rift is an AI-powered infrastructure orchestrator that **autonomously detects, diagnoses, and fixes infrastructure issues** using multi-agent systems and the Model Context Protocol (MCP).

### The Problem

- DevOps engineers spend **40% of their time** on routine infrastructure incidents
- Average incident response time: **2-4 hours**
- Manual fixes are error-prone and inconsistent
- On-call fatigue leads to burnout

### The Solution

FixBot uses three specialized AI agents:

1. **Monitor Agent** - Detects issues in seconds via DigitalOcean MCP + Prometheus
2. **Diagnostic Agent** - Uses RAG to analyze root causes from knowledge base
3. **Remediation Agent** - Fixes problems automatically via Terraform + MCP

**Result:** Incident response time reduced from hours to **~90 seconds**, fully autonomous.

---

## 📁 Project Structure

```
fixbot/
│
├── frontend/                    # 🎨 Next.js Dashboard (Pre-built)
│   ├── app/
│   │   ├── page.tsx            # Main dashboard
│   │   ├── layout.tsx          # Root layout
│   │   ├── globals.css         # Dark punk theme styles
│   │   └── favicon.ico
│   │
│   ├── components/
│   │   ├── ui/                 # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   └── badge.tsx
│   │   │
│   │   ├── StatusCard.tsx      # Agent status display
│   │   ├── IncidentFeed.tsx    # Real-time event stream
│   │   ├── AgentStatus.tsx     # Agent health monitor
│   │   ├── MetricsChart.tsx    # System metrics visualization
│   │   ├── TraceViewer.tsx     # AI decision traceability
│   │   └── Terminal.tsx        # Terminal-style output
│   │
│   ├── lib/
│   │   ├── api.ts              # Backend API client
│   │   ├── websocket.ts        # WebSocket connection
│   │   └── utils.ts            # Utility functions
│   │
│   ├── public/
│   │   └── fixbot-logo.svg
│   │
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts      # Dark punk theme
│   ├── next.config.js
│   ├── .env.local              # Configure this!
│   └── README.md
│
└── backend/                     # 🔧 Python Backend (Build this!)
    ├── agents/
    │   ├── base_agent.py       # Base agent class
    │   ├── monitor_agent.py    # Monitoring logic
    │   ├── diagnostic_agent.py # Diagnosis with RAG
    │   └── remediation_agent.py # Auto-remediation
    │
    ├── mcp_clients/
    │   ├── do_mcp.py           # DigitalOcean MCP
    │   ├── terraform_mcp.py    # Terraform MCP
    │   └── prometheus_mcp.py   # Custom Prometheus MCP
    │
    ├── orchestrator/
    │   └── coordinator.py      # Agent coordination
    │
    ├── models/
    │   └── incident.py         # Pydantic models
    │
    ├── terraform/
    │   ├── main.tf
    │   └── modules/
    │
    ├── demo/
    │   └── failure_injection.py # Demo scenarios
    │
    ├── knowledge-base/
    │   ├── do-docs.md
    │   ├── runbooks.md
    │   └── past-incidents.json
    │
    ├── main.py                 # FastAPI backend
    ├── requirements.txt
    ├── .env                    # Configure this!
    └── README.md
```

### Directory Responsibilities

**Frontend (`fixbot/frontend/`):**

- ✅ **Pre-built and ready to use** - Just run `npm install` and configure `.env.local`
- Next.js 14+ with App Router
- Real-time dashboard with WebSocket updates
- **Dark Punk Professional Theme** - Cyberpunk aesthetics meets Bloomberg Terminal
- TypeScript + Tailwind CSS + shadcn/ui
- Minimal configuration needed

**Backend (`fixbot/backend/`):**

- ⚠️ **You build this during the hackathon**
- Python FastAPI application
- AI agents (Monitor, Diagnostic, Remediation)
- MCP server integrations
- WebSocket server for real-time updates
- Infrastructure as Code (Terraform)

---

## 🎨 Frontend Setup

The frontend is **pre-built** with a professional dark punk theme. You just need to install and configure it.

### Prerequisites

- Node.js 18+ and npm 9+
- A running backend API (see Backend Setup)

### Quick Start

```bash
# Navigate to frontend directory
cd fixbot/frontend

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env.local
```

Edit `.env.local`:

```bash
# Backend API endpoint
NEXT_PUBLIC_API_URL=http://localhost:8000

# WebSocket endpoint
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

```bash
# Run development server
npm run dev

# Open browser
open http://localhost:3000
```

### Frontend Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Components:** shadcn/ui
- **State:** React Hooks
- **Real-time:** WebSocket client
- **API Client:** Fetch API with error handling

---

## 🔧 Backend Setup

The backend is what you'll build during the hackathon.

### Prerequisites

- Python 3.11+
- DigitalOcean account with API token
- Gradient AI Platform access
- Terraform installed
- Docker (for MCP servers)

### Quick Start

```bash
# Navigate to backend directory
cd fixbot/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

Edit `.env`:

```bash
# DigitalOcean
DO_API_TOKEN=your_do_token_here
DO_SPACES_KEY=your_spaces_key
DO_SPACES_SECRET=your_spaces_secret

# Gradient AI
GRADIENT_AI_API_KEY=your_gradient_key
MONITOR_AGENT_ID=agent_xxx
DIAGNOSTIC_AGENT_ID=agent_yyy
REMEDIATION_AGENT_ID=agent_zzz

# MCP Servers
DO_MCP_URL=http://localhost:3000
TERRAFORM_MCP_URL=http://localhost:3001
PROMETHEUS_URL=http://your-prometheus:9090
```

```bash
# Start MCP servers (in separate terminals)
# See MCP Integration section in full guide

# Run FastAPI backend
python main.py

# Backend should start on http://localhost:8000
```

### Backend Tech Stack

- **Framework:** FastAPI
- **AI Platform:** DigitalOcean Gradient AI
- **Protocol:** Model Context Protocol (MCP)
- **IaC:** Terraform
- **Monitoring:** Prometheus
- **Language:** Python 3.11+

---

## 🚀 Running the Complete System

### Development Mode

**Terminal 1: Backend API**

```bash
cd fixbot/backend
source venv/bin/activate
python main.py
# Runs on http://localhost:8000
```

**Terminal 2: Frontend Dashboard**

```bash
cd fixbot/frontend
npm run dev
# Runs on http://localhost:3000
```

**Terminal 3: Monitor Logs (Optional)**

```bash
cd fixbot/backend
tail -f logs/fixbot.log
```

### Verify Everything Works

```bash
# Check backend health
curl http://localhost:8000/agents/health

# Check frontend loads
curl http://localhost:3000

# Open dashboard in browser
open http://localhost:3000  # macOS
xdg-open http://localhost:3000  # Linux
```

You should see:

- ✅ All three agent status cards showing "Active" with green indicators
- ✅ System metrics displaying normal values
- ✅ Live connection indicator showing "Connected"
- ✅ Empty incident feed (no incidents yet)

---

## 🎨 Design System (Dark Punk Professional Theme)

### Theme Philosophy

**"Professional Cyberpunk"** - The aesthetic of a high-tech operations center. Think: **Blade Runner meets Bloomberg Terminal**. Dark, sleek, with neon accents that convey urgency and precision.

### Color Palette

```css
/* Background & Surfaces */
--background: #0a0e17; /* Deep space black */
--surface: #111827; /* Card/panel background */
--surface-elevated: #1f2937; /* Elevated elements */

/* Brand Colors (Neon Accents) */
--primary: #00ff9f; /* Neon green - success/active */
--secondary: #00d4ff; /* Cyber blue - info */
--accent: #ff00ff; /* Neon magenta - alerts */

/* Status Colors */
--success: #00ff9f; /* Neon green */
--warning: #ffaa00; /* Electric amber */
--danger: #ff3366; /* Hot pink red */

/* Text */
--text-primary: #e5e7eb; /* Almost white */
--text-secondary: #9ca3af; /* Muted gray */
--text-muted: #6b7280; /* Very muted */

/* Borders */
--border: #1f2937; /* Subtle borders */
--border-bright: #374151; /* Highlighted borders */
```

### Typography

**Fonts:**

- **Headers:** `"JetBrains Mono"` or `"Space Mono"` (monospace, technical feel)
- **Body:** `"Inter"` or `"DM Sans"` (clean, readable)
- **Code/Terminal:** `"Fira Code"` or `"Cascadia Code"` (with ligatures)

**Guidelines:**

- Use **UPPERCASE** for labels and status indicators
- Use **monospace** for anything technical (IDs, timestamps, metrics)
- Use **medium-large sizes** for important info (remember: projector demo!)
- Use **color** to convey meaning (green = good, red = critical, blue = info)

### Component Examples

#### Status Card (Agent Display)

```tsx
<Card className="bg-[#111827] border border-[#1f2937] hover:border-[#00ff9f] transition-all">
  <div className="flex items-center gap-3">
    {/* Active indicator - pulsing green dot */}
    <div className="h-2 w-2 rounded-full bg-[#00ff9f] animate-pulse" />

    {/* Agent name - monospace, uppercase, neon green */}
    <span className="text-[#00ff9f] font-mono uppercase tracking-wider">
      Monitor Agent
    </span>
  </div>

  {/* Status info - secondary text */}
  <div className="mt-2 text-[#9ca3af] text-sm">
    Status: Active • Last check: 2s ago
  </div>
</Card>
```

#### Terminal/Console Output

```tsx
<div className="bg-black border border-[#00ff9f] rounded p-4 font-mono">
  <div className="flex gap-2 text-[#00ff9f]">
    <span className="text-[#00ff9f]">●</span>
    <span>14:32:15 | FixBot detected high CPU (95%)</span>
  </div>
  <div className="flex gap-2 text-[#00d4ff]">
    <span className="text-[#00d4ff]">●</span>
    <span>14:32:18 | Analyzing root cause...</span>
  </div>
  <div className="flex gap-2 text-[#00ff9f]">
    <span className="text-[#00ff9f]">●</span>
    <span>14:33:45 | ✅ RESOLVED - Droplet resized</span>
  </div>
</div>
```

#### Metrics Display

```tsx
<div className="space-y-2">
  <div className="flex justify-between text-sm">
    <span className="text-[#9ca3af]">CPU Usage</span>
    <span className="text-[#00ff9f] font-mono">42%</span>
  </div>

  {/* Progress bar with gradient */}
  <div className="h-2 bg-[#1f2937] rounded-full overflow-hidden">
    <div
      className="h-full bg-gradient-to-r from-[#00ff9f] to-[#00d4ff]"
      style={{ width: "42%" }}
    />
  </div>
</div>
```

### Animation Guidelines

**Use sparingly and professionally:**

```css
/* Pulse for active states */
@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

/* Glow effect on hover */
.hover-glow:hover {
  box-shadow: 0 0 20px rgba(0, 255, 159, 0.3);
}

/* Subtle scan line (optional) */
@keyframes scan {
  0% {
    transform: translateY(-100%);
  }
  100% {
    transform: translateY(100%);
  }
}
```

**DO:**

- ✅ Pulse indicators for active/live states
- ✅ Smooth transitions (0.2-0.3s)
- ✅ Hover effects (glow, border color change)
- ✅ Fade in/out for notifications

**DON'T:**

- ❌ Excessive animations
- ❌ Constant movement
- ❌ Distracting effects during demo
- ❌ Flashy transitions

### Layout Principles

**Dashboard Grid (Desktop):**

```
┌─────────────────────────────────────────────────┐
│  🤖 FixBot                        [●] LIVE     │
├─────────────────────────────────────────────────┤
│                                                 │
│  [Monitor]  [Diagnostic]  [Remediation]        │  ← Agent status cards
│                                                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  📊 System Metrics                              │  ← Metrics display
│  CPU | Memory | Disk                            │
│                                                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  🔴 Live: Incident Timeline                     │  ← Real-time feed
│  [Scrolling event stream...]                    │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Spacing:**

- Use `gap-4` (1rem) or `gap-6` (1.5rem) between elements
- Generous padding inside cards: `p-6` or `p-8`
- Consistent margins: `my-4` or `my-6`

---

## 🎬 Demo Guide

### Pre-Demo Checklist

**5 minutes before demo:**

1. **Start Backend:**

   ```bash
   cd fixbot/backend && python main.py
   ```

2. **Start Frontend:**

   ```bash
   cd fixbot/frontend && npm run dev
   ```

3. **Open Dashboard:**

   ```bash
   open http://localhost:3000
   ```

4. **Verify Status:**

   - All agents show green "Active"
   - System metrics display normally
   - Live indicator shows "Connected"

5. **Prepare Failure Injection:**
   ```bash
   cd fixbot/backend/demo
   # Have terminal ready with injection command
   ```

### Demo Script (7 Minutes)

**[0:00-0:30] Hook + Dashboard Intro**

```
YOU: "Infrastructure breaks. That's a fact of life.

But what if you had a bot that fixed things automatically -
before they wake up your on-call engineer at 3 AM?

That's FixBot."

[Show dashboard on screen - point to it]

"This is FixBot's operations center.
Three AI agents monitoring our infrastructure 24/7."
```

**[0:30-1:00] Architecture Walkthrough**

```
[Point to each agent card]

YOU: "Three specialized agents:

Monitor Agent - detects issues via DigitalOcean MCP and Prometheus
Diagnostic Agent - uses RAG to analyze root causes
Remediation Agent - fixes problems automatically via Terraform

All powered by DigitalOcean Gradient AI with Model Context Protocol."
```

**[1:00-4:00] Live Demo: CPU Spike**

```bash
# Run in terminal (don't show this to judges, just run it)
python failure_injection.py --inject cpu --target web-app
```

```
[FOCUS ON DASHBOARD - this is the star]

YOU: "Let me trigger a real incident. I'm overloading our web server..."

[Dashboard comes alive:]
- Monitor Agent: Status changes to "⚠ DETECTING..."
- Incident feed starts scrolling:
  "14:32:15 | 🔴 ALERT: High CPU detected (95%)"

[CPU metric bar turns red, shows 95%]

YOU: "Three seconds. FixBot detected it."

[Diagnostic Agent activates:]
  "14:32:18 | 🔍 Analyzing root cause..."
  "14:32:22 | 💡 Root cause: Undersized droplet"
  "14:32:22 | 📋 Recommended: Resize to s-2vcpu-4gb"

YOU: "Now it's using RAG - querying our knowledge base of past incidents,
DigitalOcean documentation, best practices..."

[Remediation Agent executes:]
  "14:32:25 | 🔧 Executing: Terraform resize"
  "14:32:30 | ⚙️  Applying infrastructure changes..."
  "14:33:45 | ✅ RESOLVED: Droplet resized"

[CPU drops to 42%, turns green]
[All agents return to "Active" status]

YOU: "90 seconds total. From detection to resolution.
Completely autonomous. No human intervention."

[Pause for impact]
```

**[4:00-5:00] Show Traceability**

```
[Click on resolved incident in feed]
[Opens trace viewer panel]

YOU: "Here's what makes this special - full traceability.

[Point to trace view showing:]
- Input metrics and system state
- RAG retrieval results from knowledge base
- Decision logic and confidence scores
- Terraform config generated
- Success validation

"Every decision the AI makes is auditable.
This isn't a black box. You can see exactly why FixBot chose this solution."
```

**[5:00-6:00] Quick Second Demo (If Time)**

```bash
python failure_injection.py --inject disk --target api-server
```

```
YOU: "One more. Disk full on API server..."

[Faster walkthrough on dashboard]
- Detect (5s)
- Diagnose (15s)
- Attach new volume (45s)
- Resolved

YOU: "Same pattern. Different problem. Fixed automatically."
```

**[6:00-7:00] Closing**

```
[Return to clean dashboard - all green]

YOU: "FixBot - the infrastructure fixer that never sleeps.

Key features:
• Detects issues in seconds using DigitalOcean MCP
• Diagnoses with AI-powered RAG
• Fixes automatically via Terraform
• Full traceability of every decision
• Built entirely on DigitalOcean Gradient AI

This is the future of infrastructure management.
No more 3 AM wake-up calls.
No more manual emergency fixes.
Just autonomous, intelligent infrastructure.

Questions?"

[Confident smile, pause]
```

### Demo Tips

**DO:**

- ✅ Keep dashboard fullscreen during demo
- ✅ Speak slowly and clearly
- ✅ Pause after key points for impact
- ✅ Point to screen elements as you explain
- ✅ Show enthusiasm - this is cool tech!
- ✅ Have backup video if live demo fails

**DON'T:**

- ❌ Switch between terminal and browser constantly
- ❌ Rush through the demo
- ❌ Get lost in technical details
- ❌ Apologize for delays (they're normal)
- ❌ Turn your back to audience

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                           │
│                  (Next.js Dashboard)                         │
│                                                              │
│  • Dark Punk Professional Theme                              │
│  • Real-time WebSocket Updates                               │
│  • Agent Status Monitoring                                   │
│  • Incident Timeline                                         │
│  • Decision Traceability                                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ WebSocket + REST API
                 │
┌────────────────▼────────────────────────────────────────────┐
│                  FASTAPI BACKEND                             │
│                  (Orchestrator)                              │
│                                                              │
│  Endpoints:                                                  │
│  • POST /incidents/detect                                    │
│  • POST /incidents/diagnose                                  │
│  • POST /incidents/remediate                                 │
│  • GET /status                                               │
│  • GET /agents/health                                        │
│  • WS /ws (WebSocket for real-time)                          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Agent API Calls
                 │
┌────────────────▼────────────────────────────────────────────┐
│         DIGITALOCEAN GRADIENT AI PLATFORM                    │
│              (Multi-Agent System)                            │
│                                                              │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────┐       │
│  │ MONITOR  │──│ DIAGNOSTIC   │──│ REMEDIATION    │       │
│  │ AGENT    │  │ AGENT        │  │ AGENT          │       │
│  │          │  │              │  │                │       │
│  │ • Detect │  │ • RAG Query  │  │ • Terraform    │       │
│  │ • Alert  │  │ • Analyze    │  │ • DO API       │       │
│  │ • Triage │  │ • Recommend  │  │ • Validate     │       │
│  └────┬─────┘  └──────┬───────┘  └────────┬───────┘       │
│       │               │                    │                │
│       └───────────────┼────────────────────┘                │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │         KNOWLEDGE BASE (RAG)                         │  │
│  │  • DO Documentation (auto-indexed)                   │  │
│  │  • Runbooks & Best Practices                         │  │
│  │  • Past Incident History                             │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                 │
                 │ MCP Protocol
                 │
┌────────────────▼────────────────────────────────────────────┐
│              MCP SERVERS                                     │
│                                                              │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ DigitalOcean    │  │ Terraform    │  │ Prometheus   │  │
│  │ MCP Server      │  │ MCP Server   │  │ MCP (Custom) │  │
│  │                 │  │              │  │              │  │
│  │ • Droplets      │  │ • Validate   │  │ • Query      │  │
│  │ • Monitoring    │  │ • Plan       │  │ • Alerts     │  │
│  │ • Spaces        │  │ • Apply      │  │ • Metrics    │  │
│  │ • Kubernetes    │  │ • State      │  │              │  │
│  └─────────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Frontend

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript 5+
- **Styling:** Tailwind CSS 3.4
- **Components:** shadcn/ui
- **State Management:** React Hooks (useState, useEffect, useContext)
- **Real-time:** WebSocket API
- **HTTP Client:** Fetch API
- **Build Tool:** Next.js built-in (Turbopack)

### Backend

- **Framework:** FastAPI 0.109+
- **Language:** Python 3.11+
- **AI Platform:** DigitalOcean Gradient AI
  - Multi-agent system
  - RAG (Retrieval-Augmented Generation)
  - Function calling
  - Agent evaluations
  - Traceability
- **Protocol:** Model Context Protocol (MCP)
- **Infrastructure:** Terraform 1.6+
- **Monitoring:** Prometheus
- **State Management:** DO Spaces (S3-compatible)
- **WebSocket:** FastAPI WebSocket support

### Infrastructure

- **Cloud:** DigitalOcean
  - Droplets (compute)
  - Spaces (object storage)
  - Managed Kubernetes (optional)
  - Monitoring (built-in)
- **IaC:** Terraform with DO provider
- **Orchestration:** FastAPI + asyncio
- **Monitoring:** Prometheus + node_exporter

---

## 🎯 Key Features

### ✅ Already Implemented (Frontend)

- Real-time dashboard with WebSocket
- Dark punk professional theme
- Agent status monitoring
- Live incident feed
- System metrics visualization
- Decision traceability viewer
- Responsive layout (desktop-focused)

### 🔨 To Implement (Backend - Your Job!)

- [ ] Monitor Agent with DO MCP integration
- [ ] Diagnostic Agent with RAG
- [ ] Remediation Agent with Terraform
- [ ] FastAPI orchestrator
- [ ] WebSocket server for real-time updates
- [ ] MCP client implementations
- [ ] Knowledge base setup
- [ ] Demo failure injection scripts
- [ ] Agent evaluations

---

## 📦 Quick Commands Reference

### Frontend

```bash
# Install
npm install

# Dev mode
npm run dev

# Build
npm run build

# Production
npm start

# Type check
npm run type-check

# Lint
npm run lint
```

### Backend

```bash
# Install
pip install -r requirements.txt

# Run dev
python main.py

# Run with reload
uvicorn main:app --reload

# Run tests
pytest tests/

# Type check
mypy .
```

---

## 🐛 Troubleshooting

### Frontend won't connect to backend

- Check `.env.local` has correct `NEXT_PUBLIC_API_URL`
- Verify backend is running on expected port
- Check CORS settings in FastAPI backend
- Look for errors in browser console (F12)

### WebSocket connection fails

- Check `NEXT_PUBLIC_WS_URL` in `.env.local`
- Verify WebSocket endpoint exists in backend
- Check firewall/proxy settings
- Test with: `wscat -c ws://localhost:8000/ws`

### Dark theme not applying

- Clear browser cache
- Check `globals.css` is imported in `layout.tsx`
- Verify Tailwind is processing CSS correctly
- Run `npm run dev` with clean cache

### Agents not responding

- Check Gradient AI API keys in backend `.env`
- Verify agent IDs are correct
- Test agent endpoints individually
- Check Gradient AI dashboard for errors

---

## 📝 License

MIT License - see LICENSE file for details

---

## 🏆 Built For

**MLH + DigitalOcean AI Hackathon NYC**  
December 12-13, 2025

---

## 👥 Team

Built with ❤️ and ☕ by [Your Name]

---

## 🔗 Links

- [DigitalOcean Gradient AI](https://www.digitalocean.com/products/gradient-ai)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Terraform DigitalOcean Provider](https://registry.terraform.io/providers/digitalocean/digitalocean/latest/docs)

---

**Questions? Found a bug? Want to contribute?**  
Open an issue or PR on GitHub!

🤖 **FixBot - Breaking things? We fix them before you notice.** 🤖
