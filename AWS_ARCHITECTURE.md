# HelloAPI AWS Architecture Diagram

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           INTERNET                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ HTTPS/HTTP
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    Route 53 (Optional)                              │
│                   Custom Domain: api.yourdomain.com                 │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│                Application Load Balancer (ALB)                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Listener: HTTP (80) / HTTPS (443)                           │  │
│  │  Target Group: helloapi-tg                                   │  │
│  │  Health Check: /api/users/                                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         AWS VPC                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │               ECS Cluster: helloapi-cluster                │    │
│  │  ┌──────────────────┐          ┌──────────────────┐        │    │
│  │  │  ECS Task (1)    │          │  ECS Task (2)    │        │    │
│  │  │                  │          │                  │        │    │
│  │  │  ┌────────────┐  │          │  ┌────────────┐  │        │    │
│  │  │  │ Container  │  │          │  │ Container  │  │        │    │
│  │  │  │            │  │          │  │            │  │        │    │
│  │  │  │  Django    │  │          │  │  Django    │  │        │    │
│  │  │  │  Gunicorn  │  │          │  │  Gunicorn  │  │        │    │
│  │  │  │  Port 8000 │  │          │  │  Port 8000 │  │        │    │
│  │  │  └────────────┘  │          │  └────────────┘  │        │    │
│  │  │                  │          │                  │        │    │
│  │  │  Fargate (0.5    │          │  Fargate (0.5   │        │    │
│  │  │  vCPU, 1GB RAM)  │          │  vCPU, 1GB RAM) │        │    │
│  │  └──────────────────┘          └──────────────────┘        │    │
│  │                                                             │    │
│  │              Auto-Scaling: 2-10 tasks                       │    │
│  └────────────────────────────────────────────────────────────┘    │
│                             │                                       │
│                             │                                       │
│                             ↓                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │              RDS PostgreSQL Database                       │    │
│  │  ┌──────────────────────────────────────────────────────┐  │    │
│  │  │  Instance: helloapi-db                               │  │    │
│  │  │  Engine: PostgreSQL 15.4                             │  │    │
│  │  │  Instance Type: db.t3.micro                          │  │    │
│  │  │  Storage: 20GB gp3                                   │  │    │
│  │  │  Database: my_database                               │  │    │
│  │  │  Multi-AZ: Optional                                  │  │    │
│  │  └──────────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                             ↑
                             │
                   ┌─────────┴──────────┐
                   │                    │
         ┌─────────▼─────────┐  ┌──────▼────────┐
         │ AWS Secrets       │  │  CloudWatch   │
         │ Manager           │  │  Logs         │
         │                   │  │               │
         │ - SECRET_KEY      │  │ - App Logs    │
         │ - DB Credentials  │  │ - Monitoring  │
         │ - DB Host         │  │ - Alarms      │
         └───────────────────┘  └───────────────┘
```

## Network Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           VPC (10.0.0.0/16)                         │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Public Subnet 1 (AZ-1)               10.0.1.0/24           │  │
│  │  ┌────────────────┐    ┌────────────────┐                   │  │
│  │  │  ALB           │    │  ECS Task 1    │                   │  │
│  │  │  (Part 1)      │    │  (with public  │                   │  │
│  │  │                │    │   IP if needed)│                   │  │
│  │  └────────────────┘    └────────────────┘                   │  │
│  │         │                      │                             │  │
│  │         │                      │                             │  │
│  └─────────┼──────────────────────┼─────────────────────────────┘  │
│            │                      │                                │
│            │                      │                                │
│  ┌─────────┼──────────────────────┼─────────────────────────────┐  │
│  │  Public Subnet 2 (AZ-2)        │      10.0.2.0/24           │  │
│  │  ┌──────▼──────────┐    ┌──────▼──────────┐                 │  │
│  │  │  ALB           │    │  ECS Task 2    │                   │  │
│  │  │  (Part 2)      │    │  (with public  │                   │  │
│  │  │                │    │   IP if needed)│                   │  │
│  │  └────────────────┘    └────────────────┘                   │  │
│  │                                │                             │  │
│  └────────────────────────────────┼─────────────────────────────┘  │
│                                   │                                │
│                                   │                                │
│  ┌────────────────────────────────┼─────────────────────────────┐  │
│  │  Private Subnet 1 (AZ-1)       │      10.0.11.0/24          │  │
│  │  ┌─────────────────────────────▼────────────────┐            │  │
│  │  │    RDS Instance (Multi-AZ if enabled)        │            │  │
│  │  │           Primary in AZ-1                    │            │  │
│  │  └──────────────────────────────────────────────┘            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Private Subnet 2 (AZ-2)               10.0.12.0/24          │  │
│  │  ┌──────────────────────────────────────────────┐            │  │
│  │  │    RDS Standby (Multi-AZ if enabled)         │            │  │
│  │  │           Standby in AZ-2                    │            │  │
│  │  └──────────────────────────────────────────────┘            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

Internet Gateway ←→ Public Subnets
Private Subnets ←→ NAT Gateway (if needed) ←→ Internet
```

## Security Groups

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Security Group Architecture                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐
│  helloapi-alb-sg    │
│  (ALB Security      │
│   Group)            │
│                     │
│  Inbound:           │
│  - 0.0.0.0/0:80     │ ← HTTP from anywhere
│  - 0.0.0.0/0:443    │ ← HTTPS from anywhere
│                     │
│  Outbound:          │
│  - ECS SG:8000      │ → To ECS tasks
└──────────┬──────────┘
           │
           │
           ↓
┌─────────────────────┐
│  helloapi-ecs-sg    │
│  (ECS Tasks         │
│   Security Group)   │
│                     │
│  Inbound:           │
│  - ALB SG:8000      │ ← From ALB only
│                     │
│  Outbound:          │
│  - RDS SG:5432      │ → To RDS
│  - 0.0.0.0/0:443    │ → HTTPS (for AWS APIs)
└──────────┬──────────┘
           │
           │
           ↓
┌─────────────────────┐
│  helloapi-rds-sg    │
│  (RDS Security      │
│   Group)            │
│                     │
│  Inbound:           │
│  - ECS SG:5432      │ ← From ECS tasks only
│                     │
│  Outbound:          │
│  - None needed      │
└─────────────────────┘
```

## Data Flow

### 1. Request Flow (READ)

```
User Browser
    │
    │ 1. HTTP GET /api/users/
    ↓
Application Load Balancer
    │
    │ 2. Route to healthy target
    ↓
ECS Task (Container)
    │
    │ 3. Gunicorn receives request
    ↓
Django Application
    │
    │ 4. Query database
    ↓
RDS PostgreSQL
    │
    │ 5. Return data
    ↓
Django Application
    │
    │ 6. Serialize to JSON
    ↓
ECS Task (Container)
    │
    │ 7. Return response
    ↓
Application Load Balancer
    │
    │ 8. Forward response
    ↓
User Browser
```

### 2. Write Flow (CREATE/UPDATE)

```
User Browser
    │
    │ 1. HTTP POST /api/users/
    │    {name: "John", email: "john@example.com"}
    ↓
Application Load Balancer
    │
    │ 2. Route to healthy target
    ↓
ECS Task (Container)
    │
    │ 3. Gunicorn receives request
    ↓
Django Application
    │
    │ 4. Validate data (serializer)
    │ 5. Create/update record
    ↓
RDS PostgreSQL
    │
    │ 6. Persist data
    │ 7. Return confirmation
    ↓
Django Application
    │
    │ 8. Serialize response
    ↓
ECS Task (Container)
    │
    │ 9. Return response (201 Created)
    ↓
Application Load Balancer
    │
    │ 10. Forward response
    ↓
User Browser
```

## Deployment Flow

```
Developer Machine
    │
    │ 1. Code changes
    ↓
Git Repository
    │
    │ 2. Build Docker image
    ↓
Docker Build
    │
    │ 3. Push to registry
    ↓
AWS ECR (Elastic Container Registry)
    │
    │ 4. Update task definition
    ↓
ECS Task Definition
    │
    │ 5. Update service
    ↓
ECS Service
    │
    │ 6. Rolling deployment
    ├─→ Stop old task 1
    │   Start new task 1
    │   Wait for health check
    │   
    ├─→ Stop old task 2
    │   Start new task 2
    │   Wait for health check
    ↓
Deployment Complete
```

## Auto-Scaling Behavior

```
Low Traffic:
┌─────────────────────────────────────┐
│ ALB → Task 1                        │
│     → Task 2 (minimum count)        │
└─────────────────────────────────────┘

Medium Traffic (CPU > 70%):
┌─────────────────────────────────────┐
│ ALB → Task 1                        │
│     → Task 2                        │
│     → Task 3 ← Scale out            │
│     → Task 4 ← Scale out            │
└─────────────────────────────────────┘

High Traffic (CPU > 70% sustained):
┌─────────────────────────────────────┐
│ ALB → Task 1                        │
│     → Task 2                        │
│     → Task 3                        │
│     → Task 4                        │
│     → Task 5                        │
│     → ...                           │
│     → Task 10 (maximum count)       │
└─────────────────────────────────────┘

Traffic Decreases (CPU < 70%):
┌─────────────────────────────────────┐
│ ALB → Task 1                        │
│     → Task 2                        │
│     → Task 3 ← Scale in (gradual)   │
└─────────────────────────────────────┘
```

## Health Check Flow

```
ALB Target Group
    │
    │ Every 30 seconds
    ↓
GET /api/users/
    │
    ↓
┌─────────────────────┐
│ ECS Task            │
│                     │
│ Status Code: 200    │ → Healthy (2 consecutive = healthy)
│ Timeout: 5s         │
│ Unhealthy: 3 fails  │ → Unhealthy (3 consecutive = unhealthy)
└─────────────────────┘
    │
    ↓
If Unhealthy:
    - Stop routing traffic
    - ECS starts new task
    - Old task is terminated
```

## Cost Breakdown

```
┌─────────────────────────────────────────────────────────────┐
│                    Monthly Cost Estimate                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  RDS db.t3.micro (1 instance)                               │
│  └─ 720 hours × $0.018/hour          = $12.96              │
│  └─ Storage: 20GB × $0.115/GB         = $2.30              │
│  └─ Backup: 20GB × $0.095/GB          = $1.90              │
│                                        ────────             │
│                                Total:   $17.16              │
│                                                             │
│  ECS Fargate (2 tasks, 0.5 vCPU, 1GB each)                  │
│  └─ vCPU: 720h × 1 vCPU × $0.04048    = $29.15             │
│  └─ Memory: 720h × 2GB × $0.004445    = $6.40              │
│                                        ────────             │
│                                Total:   $35.55              │
│                                                             │
│  Application Load Balancer                                  │
│  └─ 720 hours × $0.0225/hour          = $16.20             │
│  └─ LCU charges (light traffic)        = $5.00             │
│                                        ────────             │
│                                Total:   $21.20              │
│                                                             │
│  Data Transfer Out                                          │
│  └─ First 1GB free, then $0.09/GB      = $5.00             │
│                                                             │
│  CloudWatch Logs                                            │
│  └─ Ingestion + storage                = $2.00             │
│                                                             │
│  Secrets Manager                                            │
│  └─ 6 secrets × $0.40/secret/month     = $2.40             │
│                                                             │
│  ECR Storage                                                │
│  └─ ~500MB × $0.10/GB                  = $0.05             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  TOTAL ESTIMATED MONTHLY COST:        ~$83.36              │
└─────────────────────────────────────────────────────────────┘

Note: Actual costs may vary based on:
- Traffic volume
- Data transfer
- Additional features (backups, multi-AZ, etc.)
- Region differences
```

## Monitoring Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│                    CloudWatch Dashboard                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────┬─────────────────────────┐      │
│  │   ECS Service Metrics   │   ALB Metrics           │      │
│  │   - CPU Utilization     │   - Request Count       │      │
│  │   - Memory Utilization  │   - Target Response Time│      │
│  │   - Task Count          │   - Healthy Host Count  │      │
│  │   - Network In/Out      │   - 2XX/4XX/5XX Count   │      │
│  └─────────────────────────┴─────────────────────────┘      │
│                                                             │
│  ┌─────────────────────────┬─────────────────────────┐      │
│  │   RDS Metrics           │   Application Logs      │      │
│  │   - Database Connections│   - Error Rate          │      │
│  │   - Read/Write IOPS     │   - Request Rate        │      │
│  │   - CPU Utilization     │   - Response Time       │      │
│  │   - Free Storage        │   - Recent Errors       │      │
│  └─────────────────────────┴─────────────────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Summary

This architecture provides:

✅ **High Availability**: Multiple tasks across availability zones
✅ **Scalability**: Auto-scaling based on CPU utilization
✅ **Security**: VPC isolation, security groups, secrets management
✅ **Monitoring**: CloudWatch logs and metrics
✅ **Reliability**: Health checks and automatic task replacement
✅ **Cost-Effective**: ~$83/month for production-ready infrastructure
✅ **Managed Services**: AWS handles infrastructure maintenance

For detailed deployment instructions, see:
- `DEPLOYMENT_SUMMARY.md` - Quick overview
- `AWS_DEPLOYMENT_GUIDE.md` - Comprehensive guide
- `QUICK_DEPLOY.md` - Command reference
- `deploy-aws.sh` - Automated deployment

