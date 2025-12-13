# Rift Incident Response Runbooks

## High CPU Usage

### Symptoms
- CPU usage consistently above 80%
- Application slowness
- Request timeouts
- Load average high

### Diagnosis Steps
1. Check process list: `top` or `htop`
2. Identify CPU-hungry processes
3. Review application logs
4. Check for infinite loops or blocking operations
5. Analyze traffic patterns

### Common Causes
- **Undersized Droplet**: Workload exceeds capacity
- **Runaway Process**: Bug causing excessive CPU
- **Traffic Spike**: Legitimate increase in load
- **Inefficient Code**: Poor algorithm performance
- **Crypto Mining**: Security breach

### Resolution Options

**Option 1: Scale Up (Recommended for sustained load)**
- Action: Resize droplet to larger size
- Downtime: ~2-5 minutes
- Cost: Varies by size (e.g., +$12/mo for s-1vcpu-1gb → s-2vcpu-2gb)
- Rollback: Can resize back down
- Confidence: High if traffic/workload is legitimate

**Option 2: Restart Service**
- Action: Restart application/service
- Downtime: ~10-30 seconds
- Cost: $0
- Rollback: N/A
- Confidence: Medium (only if runaway process)

**Option 3: Enable Auto-scaling**
- Action: Configure Kubernetes HPA or similar
- Downtime: None
- Cost: Variable based on load
- Rollback: Disable auto-scaling
- Confidence: High for variable workload

**Option 4: Optimize Code**
- Action: Fix inefficient code
- Downtime: Deployment window
- Cost: Developer time
- Rollback: Redeploy previous version
- Confidence: High if specific bottleneck identified

### Terraform Config (Resize)
```hcl
resource "digitalocean_droplet" "web" {
  name   = "web-app"
  size   = "s-2vcpu-2gb"  # Changed from s-1vcpu-1gb
  image  = "ubuntu-24-04-x64"
  region = "nyc3"
}
```

---

## High Memory Usage

### Symptoms
- Memory usage above 90%
- Swap usage high
- Out of memory errors
- Process killed by OOM

### Diagnosis Steps
1. Check memory usage: `free -m`
2. Identify memory-hungry processes: `ps aux --sort=-%mem | head`
3. Check for memory leaks
4. Review application logs
5. Analyze connection pools

### Common Causes
- **Memory Leak**: Application not freeing memory
- **Too Many Connections**: Database/cache connections
- **Large Datasets**: Loading too much data into memory
- **Undersized Droplet**: Insufficient RAM for workload
- **Cache Bloat**: In-memory cache growing unbounded

### Resolution Options

**Option 1: Scale Up Memory**
- Action: Resize to droplet with more RAM
- Downtime: ~2-5 minutes
- Confidence: High for legitimate workload

**Option 2: Restart Service**
- Action: Restart leaking service
- Downtime: ~10-30 seconds
- Confidence: Medium (temporary fix)

**Option 3: Add Swap Space**
- Action: Configure swap file
- Downtime: None
- Cost: $0 (uses disk)
- Confidence: Low (performance impact)

**Option 4: Optimize Application**
- Action: Fix memory leak or reduce memory usage
- Confidence: High if leak identified

---

## Disk Full

### Symptoms
- Disk usage above 90%
- "No space left on device" errors
- Application cannot write logs
- Database writes failing

### Diagnosis Steps
1. Check disk usage: `df -h`
2. Find large files: `du -sh /* | sort -rh | head -10`
3. Check log rotation
4. Identify unused files
5. Review temporary files

### Common Causes
- **Log Files**: Logs not being rotated
- **Temporary Files**: /tmp not being cleaned
- **Database Growth**: Data accumulation
- **Backup Files**: Old backups not deleted
- **Application Data**: Uploaded files, caches

### Resolution Options

**Option 1: Clean Up Logs**
- Action: Delete old logs, configure rotation
- Downtime: None
- Cost: $0
- Commands:
  ```bash
  journalctl --vacuum-time=7d
  rm -f /var/log/*.gz
  find /var/log -mtime +30 -delete
  ```
- Confidence: High if logs are the issue

**Option 2: Add Volume**
- Action: Attach DigitalOcean Volume
- Downtime: None (attach while running)
- Cost: $10/month per 100GB
- Confidence: High for data growth

**Option 3: Resize Droplet**
- Action: Resize to larger disk size
- Downtime: ~2-5 minutes
- Confidence: Medium (more expensive than volume)

**Option 4: Clean Database**
- Action: Archive/delete old records
- Downtime: None (during maintenance window)
- Confidence: High if database is large

### Terraform Config (Add Volume)
```hcl
resource "digitalocean_volume" "data" {
  region      = "nyc3"
  name        = "web-app-data"
  size        = 100
  description = "Additional storage for web-app"
}

resource "digitalocean_volume_attachment" "data" {
  droplet_id = digitalocean_droplet.web.id
  volume_id  = digitalocean_volume.data.id
}
```

---

## Service Down / Crashed

### Symptoms
- Service not responding
- Health checks failing
- 502/503 errors
- Process not running

### Diagnosis Steps
1. Check service status: `systemctl status <service>`
2. Review service logs: `journalctl -u <service> -n 100`
3. Check for crashes in dmesg
4. Verify configuration files
5. Test manual start

### Common Causes
- **Configuration Error**: Bad config causing crash
- **Dependency Failure**: Database/cache unavailable
- **Resource Exhaustion**: OOM, disk full
- **Code Bug**: Application error
- **Port Conflict**: Port already in use

### Resolution Options

**Option 1: Restart Service**
- Action: `systemctl restart <service>`
- Downtime: ~10-30 seconds
- Cost: $0
- Confidence: High for transient issues

**Option 2: Fix Configuration**
- Action: Correct config file, reload
- Downtime: ~10 seconds
- Confidence: High if config error found

**Option 3: Rollback Deployment**
- Action: Deploy previous version
- Downtime: ~1-5 minutes
- Confidence: High if recent deployment

**Option 4: Resize Resources**
- Action: Scale up if resource constraint
- Downtime: ~2-5 minutes
- Confidence: Medium

---

## High Network I/O

### Symptoms
- Network bandwidth saturated
- Slow API responses
- Download/upload timeouts
- High network costs

### Diagnosis Steps
1. Check network usage: `iftop` or `nethogs`
2. Identify heavy connections: `ss -tunap`
3. Review bandwidth graphs in DO console
4. Check for DDoS
5. Analyze application traffic patterns

### Common Causes
- **Large File Transfers**: Backup, uploads
- **API Abuse**: Excessive requests
- **DDoS Attack**: Malicious traffic
- **Data Sync**: Replication, CDN sync
- **Misconfiguration**: Infinite retry loops

### Resolution Options

**Option 1: Rate Limiting**
- Action: Configure rate limits
- Downtime: None
- Confidence: High for API abuse

**Option 2: CDN/Caching**
- Action: Use Spaces CDN
- Downtime: None
- Cost: CDN bandwidth costs
- Confidence: High for static content

**Option 3: Firewall Rules**
- Action: Block malicious IPs
- Downtime: None
- Confidence: High for attacks

**Option 4: Optimize Transfers**
- Action: Compress, batch, schedule
- Confidence: Medium

---

## Database Performance Issues

### Symptoms
- Slow query execution
- Connection timeouts
- High database CPU/memory
- Lock contention

### Diagnosis Steps
1. Check slow query log
2. Review connection pool settings
3. Analyze query execution plans
4. Check for missing indexes
5. Review table statistics

### Common Causes
- **Missing Indexes**: Full table scans
- **Too Many Connections**: Pool exhaustion
- **Large Queries**: Inefficient JOINs
- **Lock Contention**: Long transactions
- **Undersized Database**: Insufficient resources

### Resolution Options

**Option 1: Add Indexes**
- Action: Create missing indexes
- Downtime: None (online index creation)
- Confidence: High if specific query identified

**Option 2: Scale Database**
- Action: Resize DO Managed Database
- Downtime: Brief (managed by DO)
- Cost: Varies by size
- Confidence: High for resource constraints

**Option 3: Optimize Queries**
- Action: Rewrite inefficient queries
- Confidence: High

**Option 4: Add Read Replicas**
- Action: Create read replicas
- Cost: Additional database instances
- Confidence: High for read-heavy workload

---

## Cost Estimates

### Droplet Resizing Costs (Monthly)
- s-1vcpu-1gb → s-2vcpu-2gb: +$12/mo
- s-2vcpu-2gb → s-4vcpu-8gb: +$36/mo
- s-4vcpu-8gb → s-8vcpu-16gb: +$96/mo

### Volume Costs
- 100GB Volume: $10/mo
- 500GB Volume: $50/mo

### Database Scaling
- db-s-1vcpu-1gb → db-s-2vcpu-4gb: +$30/mo
- db-s-2vcpu-4gb → db-s-4vcpu-8gb: +$60/mo

### Operational Costs
- Service restart: $0
- Configuration change: $0
- Log cleanup: $0

---

## Safety Considerations

### Always Safe Actions (Auto-approve)
- Service restart
- Log cleanup (old logs)
- Configuration reload
- Rate limit changes
- Firewall rule additions

### Require Approval
- Droplet resize (>$50/mo cost increase)
- Volume attachment
- Droplet deletion
- Database scaling
- Infrastructure destruction

### Never Auto-approve
- Delete operations
- Terminate commands
- Force operations
- Production data deletion

---

## Rollback Procedures

### Droplet Resize Rollback
1. Take snapshot before resize
2. Resize back to original size if needed
3. Restore from snapshot if issues

### Volume Attachment Rollback
1. Unmount volume
2. Detach volume
3. Delete volume if necessary

### Configuration Rollback
1. Keep backup of original config
2. Restore from backup
3. Reload service

### Deployment Rollback
1. Identify previous stable version
2. Deploy previous version
3. Verify functionality
4. Monitor for issues

---

## Success Metrics

Track these metrics for continuous improvement:

- **Mean Time to Detect (MTTD)**: How fast we detect issues
- **Mean Time to Diagnose (MTTD)**: How fast we identify root cause
- **Mean Time to Resolve (MTTR)**: How fast we fix issues
- **Resolution Success Rate**: % of successful automatic fixes
- **Cost per Incident**: Average cost of remediation
- **False Positive Rate**: % of incorrect detections

Target KPIs:
- MTTD: <60 seconds
- MTTD: <120 seconds
- MTTR: <300 seconds
- Success Rate: >90%
- False Positives: <5%
