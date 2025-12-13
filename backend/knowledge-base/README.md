# Rift Knowledge Base

This directory contains documents for the RAG (Retrieval Augmented Generation) knowledge base used by the Diagnostic Agent.

## Contents

Upload these documents to your DigitalOcean Gradient AI Knowledge Base:

### 1. DigitalOcean Documentation (`do-docs.md`)
- Droplet management
- Resizing procedures
- Monitoring best practices
- Common issues and solutions

### 2. Incident Runbooks (`runbooks.md`)
- High CPU troubleshooting
- Memory pressure handling
- Disk space management
- Network issues
- Service recovery procedures

### 3. Past Incidents (`past-incidents.json`)
- Historical incident examples
- Resolution patterns
- Success rates
- Cost data

## Setup Instructions

1. **Create Knowledge Base in Gradient AI Console**
   ```
   Name: rift-knowledge
   Description: Infrastructure troubleshooting knowledge base
   Auto-indexing: Enabled
   ```

2. **Upload Documents**
   - Upload all `.md` and `.json` files from this directory
   - Wait for indexing to complete
   - Test with sample queries

3. **Save Knowledge Base ID**
   - Copy the Knowledge Base ID
   - Add to `.env` file: `KNOWLEDGE_BASE_ID=kb_xxxxx`

4. **Attach to Diagnostic Agent**
   - In Gradient AI Console, go to Diagnostic Agent settings
   - Attach the knowledge base
   - Test integration

## Sample Queries

Test your knowledge base with these queries:

```
"How to troubleshoot high CPU on a droplet?"
"What are the steps to resize a droplet safely?"
"Common causes of disk full issues"
"Best practices for memory management"
"How to handle service crashes"
```

## Adding New Content

As Rift resolves incidents, consider adding:
- New incident patterns
- Successful resolutions
- Cost optimizations
- Performance tunings

Update the knowledge base regularly for better accuracy!
