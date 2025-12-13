# Multi-Cloud Infrastructure Provisioning Guide
## AWS + DigitalOcean Support

---

## Cloud Provider Selection

The AI will automatically detect which cloud provider to use based on keywords in your request:

### AWS Keywords:
- "AWS", "Amazon", "EC2", "RDS", "S3", "ElastiCache", "ALB", "ELB"
- Specific AWS services: "Lambda", "DynamoDB", "CloudFront", "Route53"

### DigitalOcean Keywords:
- "DigitalOcean", "DO", "droplet", "spaces"

### Multi-Cloud:
- "Deploy on both clouds"
- "Use AWS for X and DigitalOcean for Y"

---

## AWS Terraform Configuration

### Required AWS Provider Block:
```hcl
terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region     = var.aws_region
  access_key = var.aws_access_key_id
  secret_key = var.aws_secret_access_key
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "aws_access_key_id" {
  description = "AWS access key ID"
  type        = string
  sensitive   = true
}

variable "aws_secret_access_key" {
  description = "AWS secret access key"
  type        = string
  sensitive   = true
}
```

---

## AWS Resource Types

### 1. EC2 Instances (Compute)

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"  # Ubuntu 22.04 LTS
  instance_type = "t3.medium"
  
  vpc_security_group_ids = [aws_security_group.web.id]
  subnet_id              = aws_subnet.public.id
  
  user_data = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y nginx
  EOF
  
  tags = {
    Name        = "web-server"
    Environment = var.environment
  }
  
  monitoring = true
  
  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }
}

output "ec2_instance_id" {
  value = aws_instance.web.id
}

output "ec2_public_ip" {
  value = aws_instance.web.public_ip
}
```

**Instance Types:**
- `t3.micro` - 2 vCPU, 1GB RAM (~$8/month)
- `t3.small` - 2 vCPU, 2GB RAM (~$16/month)
- `t3.medium` - 2 vCPU, 4GB RAM (~$33/month)
- `t3.large` - 2 vCPU, 8GB RAM (~$66/month)

**AMIs (Ubuntu 22.04 LTS):**
- `us-east-1`: ami-0c55b159cbfafe1f0
- `us-west-2`: ami-0ceecbb0f30a902a6
- `eu-west-1`: ami-0d2a4a5d69e46ea0b

### 2. RDS Databases

```hcl
resource "aws_db_instance" "postgres" {
  identifier        = "postgres-db"
  engine            = "postgres"
  engine_version    = "16.1"
  instance_class    = "db.t3.medium"
  allocated_storage = 20
  
  db_name  = "appdb"
  username = "dbadmin"
  password = var.db_password  # Should be passed securely
  
  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  multi_az               = true
  storage_encrypted      = true
  
  skip_final_snapshot    = false
  final_snapshot_identifier = "postgres-final-snapshot"
  
  tags = {
    Name        = "postgres-database"
    Environment = var.environment
  }
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.endpoint
}

output "rds_port" {
  value = aws_db_instance.postgres.port
}

output "connection_string" {
  value     = "postgresql://dbadmin:${var.db_password}@${aws_db_instance.postgres.endpoint}/${aws_db_instance.postgres.db_name}"
  sensitive = true
}
```

**Supported Engines:**
- `postgres` - PostgreSQL (versions: 13, 14, 15, 16)
- `mysql` - MySQL (versions: 5.7, 8.0)
- `mariadb` - MariaDB
- Custom engines available

**Instance Classes:**
- `db.t3.micro` - 2 vCPU, 1GB (~$15/month)
- `db.t3.small` - 2 vCPU, 2GB (~$30/month)
- `db.t3.medium` - 2 vCPU, 4GB (~$60/month)
- `db.t3.large` - 2 vCPU, 8GB (~$120/month)

### 3. Application Load Balancer

```hcl
resource "aws_lb" "app" {
  name               = "app-loadbalancer"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
  
  enable_deletion_protection = false
  
  tags = {
    Name        = "app-loadbalancer"
    Environment = var.environment
  }
}

resource "aws_lb_target_group" "app" {
  name     = "app-targets"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
  
  health_check {
    enabled             = true
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/"
    protocol            = "HTTP"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.app.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

resource "aws_lb_target_group_attachment" "app" {
  count            = length(aws_instance.web)
  target_group_arn = aws_lb_target_group.app.arn
  target_id        = aws_instance.web[count.index].id
  port             = 80
}

output "alb_dns_name" {
  value = aws_lb.app.dns_name
}

output "alb_url" {
  value = "http://${aws_lb.app.dns_name}"
}
```

### 4. VPC and Security Groups

```hcl
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "main-vpc"
  }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  
  tags = {
    Name = "public-subnet-${count.index + 1}"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = {
    Name = "main-igw"
  }
}

resource "aws_security_group" "web" {
  name        = "web-sg"
  description = "Security group for web servers"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "web-security-group"
  }
}

output "vpc_id" {
  value = aws_vpc.main.id
}
```

---

## Multi-Cloud Example: Node.js App with AWS RDS

```hcl
# AWS Provider
terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region     = var.aws_region
  access_key = var.aws_access_key_id
  secret_key = var.aws_secret_access_key
}

provider "digitalocean" {
  token = var.do_token
}

# DigitalOcean Droplet for Node.js app
resource "digitalocean_droplet" "nodejs_app" {
  name   = "nodejs-webapp"
  size   = "s-2vcpu-4gb"
  image  = "ubuntu-22-04-x64"
  region = "nyc3"
  
  user_data = <<-EOF
    #!/bin/bash
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
    npm install -g pm2
  EOF
}

# AWS RDS PostgreSQL database
resource "aws_db_instance" "postgres" {
  identifier           = "postgres-db"
  engine               = "postgres"
  engine_version       = "16.1"
  instance_class       = "db.t3.medium"
  allocated_storage    = 20
  publicly_accessible  = true  # Allow DO droplet to connect
  
  db_name  = "appdb"
  username = "dbadmin"
  password = var.db_password
  
  skip_final_snapshot = true
}

output "droplet_ip" {
  value = digitalocean_droplet.nodejs_app.ipv4_address
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.endpoint
}

output "connection_string" {
  value     = "postgresql://dbadmin:${var.db_password}@${aws_db_instance.postgres.endpoint}/appdb"
  sensitive = true
}
```

---

## Cost Comparison Table

| Service | DigitalOcean | AWS |
|---------|--------------|-----|
| **2 vCPU, 4GB VM** | $24/month | $33/month (t3.medium) |
| **PostgreSQL 2 vCPU, 4GB** | $60/month | $60/month (db.t3.medium) |
| **Load Balancer** | $12/month | $16/month (ALB) |
| **100GB Storage** | $10/month | $10/month (EBS gp3) |

**Total Example Stack:**
- **DigitalOcean**: ~$106/month
- **AWS**: ~$119/month

---

## Best Practices

### AWS-Specific:
1. **Always use VPC** for network isolation
2. **Enable CloudWatch monitoring** for all resources
3. **Use Multi-AZ** for production databases
4. **Enable encryption** for RDS and EBS volumes
5. **Use IAM roles** instead of access keys when possible
6. **Tag all resources** for cost tracking

### Multi-Cloud:
1. **Use consistent naming** across providers
2. **Centralize secrets management** (AWS Secrets Manager or DO API)
3. **Monitor from single dashboard** (Rift platform)
4. **Plan for cross-cloud networking** (VPN or public endpoints)
5. **Test failover scenarios** between clouds

---

## Natural Language Examples

### AWS Deployments:
```
"Deploy Node.js application on AWS EC2 with RDS PostgreSQL"
"Create load-balanced web app on AWS with 3 instances"
"Set up AWS RDS MySQL database with read replicas"
"Deploy Redis cache on AWS ElastiCache"
```

### DigitalOcean Deployments:
```
"Create droplet on DigitalOcean for Python app"
"Deploy MongoDB on DigitalOcean with managed database"
"Set up load balancer on DO with 2 droplets"
```

### Multi-Cloud:
```
"Deploy frontend on DigitalOcean and database on AWS RDS"
"Create API server on AWS and cache on DigitalOcean"
"Set up multi-region with DO in NYC and AWS in us-west-2"
```

---

This guide is maintained by Rift Platform. Always verify costs in AWS/DO consoles.
