# Deployment Guide

## Frontend Deployment - Vercel

### Prerequisites
- GitHub repository connected
- Vercel account (free tier works)

### Steps:

1. **Push to GitHub** (already done ✓)

2. **Deploy to Vercel:**
   ```bash
   # Install Vercel CLI (optional)
   npm i -g vercel
   
   # From frontend directory
   cd frontend
   vercel
   ```

   Or use Vercel Dashboard:
   - Go to https://vercel.com
   - Click "Add New Project"
   - Import your GitHub repo: `itisaby/rift`
   - Select `frontend` as root directory
   - Framework Preset: **Next.js** (auto-detected)
   - Click "Deploy"

3. **Environment Variables:**
   Add in Vercel Dashboard → Settings → Environment Variables:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.com
   ```

4. **Build Settings** (auto-configured):
   - Build Command: `npm run build`
   - Output Directory: `.next`
   - Install Command: `npm install`

### Expected Result:
- URL: `https://rift-[random].vercel.app`
- Auto-deploys on every `git push` to main
- Free SSL certificate
- Global CDN

---

## Backend Deployment - DigitalOcean

You have **two options**:

### Option A: DigitalOcean App Platform (Recommended - Easier)

**Pros:** Managed, auto-scaling, built-in monitoring, easier setup
**Cons:** More expensive ($5-12/month)

#### Steps:

1. **Create App:**
   - Go to DigitalOcean Dashboard → Apps
   - Click "Create App"
   - Connect GitHub repo: `itisaby/rift`
   - Select branch: `main`

2. **Configure App:**
   - **Source Directory:** `backend`
   - **Type:** Web Service
   - **Environment:** Python 3.11+
   - **Build Command:** `pip install -r requirements.txt`
   - **Run Command:** `uvicorn main:app --host 0.0.0.0 --port 8080`
   - **HTTP Port:** 8080

3. **Environment Variables:**
   Add all from your `.env`:
   ```
   DIGITALOCEAN_API_TOKEN=your_token
   PROMETHEUS_URL=http://104.236.4.131:9090
   CONTROL_PLANE_IP=104.236.4.131
   SSH_KEY_ID=52635372
   MONITOR_AGENT_ENDPOINT=your_gradient_endpoint
   MONITOR_AGENT_KEY=your_key
   MONITOR_AGENT_ID=your_id
   DIAGNOSTIC_AGENT_ENDPOINT=...
   DIAGNOSTIC_AGENT_KEY=...
   DIAGNOSTIC_AGENT_ID=...
   REMEDIATION_AGENT_ENDPOINT=...
   REMEDIATION_AGENT_KEY=...
   REMEDIATION_AGENT_ID=...
   PROVISIONER_AGENT_ENDPOINT=...
   PROVISIONER_AGENT_KEY=...
   PROVISIONER_AGENT_ID=...
   KNOWLEDGE_BASE_ID=your_kb_id
   CONFIDENCE_THRESHOLD=0.85
   AUTO_REMEDIATION_ENABLED=true
   MAX_COST_AUTO_APPROVE=50.0
   ```

4. **Add SSH Key:**
   - In App Settings → "Advanced" → Add your `id_ed25519_do_rift` private key as a secret
   - Mount it to `/root/.ssh/id_ed25519_do_rift`

5. **Deploy:**
   - Click "Create Resources"
   - Wait 5-10 minutes for deployment

**Result:** Your backend will be at `https://your-app-name.ondigitalocean.app`

---

### Option B: DigitalOcean Droplet (Manual - More Control)

**Pros:** Cheaper ($4-6/month), full control
**Cons:** Manual setup, need to manage updates

#### Steps:

1. **Create Droplet:**
   ```bash
   # Via doctl CLI
   doctl compute droplet create rift-backend \
     --image ubuntu-22-04-x64 \
     --size s-1vcpu-1gb \
     --region nyc1 \
     --ssh-keys $(doctl compute ssh-key list --format ID --no-header) \
     --tag-names rift
   ```

2. **SSH into Droplet:**
   ```bash
   ssh root@YOUR_DROPLET_IP
   ```

3. **Setup Backend:**
   ```bash
   # Update system
   apt update && apt upgrade -y
   
   # Install Python 3.11
   apt install -y python3.11 python3.11-venv python3-pip git
   
   # Clone repo
   git clone https://github.com/itisaby/rift.git
   cd rift/backend
   
   # Create virtual environment
   python3.11 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Copy SSH key
   mkdir -p ~/.ssh
   # Copy your id_ed25519_do_rift to ~/.ssh/
   chmod 600 ~/.ssh/id_ed25519_do_rift
   
   # Create .env file
   nano .env
   # Paste all your environment variables
   ```

4. **Create Systemd Service:**
   ```bash
   nano /etc/systemd/system/rift-backend.service
   ```
   
   Add:
   ```ini
   [Unit]
   Description=Rift Backend API
   After=network.target
   
   [Service]
   Type=simple
   User=root
   WorkingDirectory=/root/rift/backend
   Environment="PATH=/root/rift/backend/venv/bin"
   ExecStart=/root/rift/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   Enable and start:
   ```bash
   systemctl daemon-reload
   systemctl enable rift-backend
   systemctl start rift-backend
   systemctl status rift-backend
   ```

5. **Setup Nginx Reverse Proxy:**
   ```bash
   apt install -y nginx certbot python3-certbot-nginx
   
   nano /etc/nginx/sites-available/rift-backend
   ```
   
   Add:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;  # Or use IP
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
   
   Enable:
   ```bash
   ln -s /etc/nginx/sites-available/rift-backend /etc/nginx/sites-enabled/
   nginx -t
   systemctl restart nginx
   ```

6. **Setup SSL (if using domain):**
   ```bash
   certbot --nginx -d your-domain.com
   ```

**Result:** Your backend will be at `http://YOUR_DROPLET_IP` or `https://your-domain.com`

---

## Update Frontend with Backend URL

After deploying backend, update Vercel environment variable:

```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

Then redeploy frontend in Vercel dashboard.

---

## CORS Configuration

Update `backend/main.py` to allow Vercel frontend:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://rift-*.vercel.app",  # Add your Vercel URL
        "https://your-custom-domain.com"  # If you have one
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Testing Deployment

1. **Test Backend:**
   ```bash
   curl https://your-backend-url.com/health
   ```

2. **Test Frontend:**
   - Visit `https://your-app.vercel.app`
   - Try creating a project
   - Check browser console for API connection

---

## Recommended: Option A (App Platform)

For hackathon/demo purposes, I recommend **App Platform** because:
- ✅ Faster setup (15 minutes vs 1 hour)
- ✅ Auto-scaling and monitoring
- ✅ Automatic SSL certificates
- ✅ Easy rollbacks
- ✅ Logs and metrics built-in
- ✅ No server management

You can always migrate to a droplet later if needed!

---

## Cost Estimate

- **Vercel Frontend:** $0 (free tier)
- **DO App Platform:** $5-12/month
- **DO Droplet:** $4-6/month
- **Existing Infrastructure:** ~$20/month (4 droplets)

**Total:** ~$25-32/month

---

## Quick Deploy Commands

```bash
# Deploy Frontend to Vercel
cd frontend
vercel --prod

# Create Backend App (using doctl)
doctl apps create --spec .do/app.yaml

# Or manually via Dashboard
# https://cloud.digitalocean.com/apps/new
```

Would you like me to create the `.do/app.yaml` configuration file for DigitalOcean App Platform deployment?
