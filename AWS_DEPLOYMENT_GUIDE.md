# AWS Deployment Guide for HelloAPI

This guide walks you through deploying your Django API to AWS using ECS (Elastic Container Service) and RDS (Relational Database Service).

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Step 1: Set Up AWS RDS PostgreSQL](#step-1-set-up-aws-rds-postgresql)
- [Step 2: Build and Push Docker Image to ECR](#step-2-build-and-push-docker-image-to-ecr)
- [Step 3: Set Up AWS Secrets Manager](#step-3-set-up-aws-secrets-manager)
- [Step 4: Configure ECS Cluster and Service](#step-4-configure-ecs-cluster-and-service)
- [Step 5: Set Up Application Load Balancer](#step-5-set-up-application-load-balancer)
- [Step 6: Configure Security Groups](#step-6-configure-security-groups)
- [Step 7: Deploy Your Application](#step-7-deploy-your-application)
- [Step 8: Run Database Migrations](#step-8-run-database-migrations)
- [Post-Deployment](#post-deployment)
- [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
- [Cost Estimation](#cost-estimation)

## 🏗 Architecture Overview

```
Internet
   ↓
Application Load Balancer (ALB)
   ↓
ECS Fargate Service (Auto-scaling)
   ↓
Docker Container (Django + Gunicorn)
   ↓
RDS PostgreSQL Database
```

**Components:**
- **VPC**: Virtual Private Cloud for network isolation
- **ALB**: Routes traffic to ECS tasks
- **ECS Fargate**: Serverless container orchestration
- **ECR**: Docker image registry
- **RDS**: Managed PostgreSQL database
- **Secrets Manager**: Secure credential storage
- **CloudWatch**: Logging and monitoring

## 📚 Prerequisites

Before you begin, ensure you have:

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, Region, and output format
   ```
3. **Docker** installed locally
4. **Git** (already have this)
5. **Python 3.11+** (already have this)

Verify installations:
```bash
aws --version
docker --version
python --version
```

## Step 1: Set Up AWS RDS PostgreSQL

### 1.1 Create RDS Subnet Group

```bash
# Create a DB subnet group (requires at least 2 subnets in different AZs)
aws rds create-db-subnet-group \
    --db-subnet-group-name helloapi-db-subnet-group \
    --db-subnet-group-description "Subnet group for HelloAPI RDS" \
    --subnet-ids subnet-XXXXXXXX subnet-YYYYYYYY \
    --region us-east-1
```

**Note:** Replace `subnet-XXXXXXXX` and `subnet-YYYYYYYY` with your actual subnet IDs from your VPC. You can find these in the VPC console.

### 1.2 Create Security Group for RDS

```bash
# Create security group for RDS
aws ec2 create-security-group \
    --group-name helloapi-rds-sg \
    --description "Security group for HelloAPI RDS" \
    --vpc-id vpc-XXXXXXXXX \
    --region us-east-1

# Note the SecurityGroupId from the output (e.g., sg-XXXXXXXXX)

# Allow PostgreSQL access from ECS tasks (we'll update this later)
aws ec2 authorize-security-group-ingress \
    --group-id sg-XXXXXXXXX \
    --protocol tcp \
    --port 5432 \
    --source-group sg-YYYYYYYY \
    --region us-east-1
```

### 1.3 Create RDS PostgreSQL Instance

```bash
# Create RDS instance
aws rds create-db-instance \
    --db-instance-identifier helloapi-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 15.4 \
    --master-username postgres \
    --master-user-password "YourSecurePassword123!" \
    --allocated-storage 2 \
    --storage-type gp3 \
    --db-name my_database \
    --vpc-security-group-ids sg-08d612ebb547281a0 \
    --db-subnet-group-name helloapi-db-subnet-group \
    --backup-retention-period 7 \
    --no-publicly-accessible \
    --region us-east-1

# Wait for the instance to be available (this takes 5-10 minutes)
aws rds wait db-instance-available \
    --db-instance-identifier helloapi-db \
    --region us-east-1

# Get the endpoint
aws rds describe-db-instances \
    --db-instance-identifier helloapi-db \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text \
    --region us-east-1
```

**Save the endpoint URL** - it will look like: `helloapi-db.xxxxxxxxx.us-east-1.rds.amazonaws.com`

### 1.4 Initialize the Database Schema

Before deploying, you need to create the `users` table in your RDS instance. You can do this by:

1. **Using a bastion host** or **AWS Systems Manager Session Manager** to connect to RDS
2. **Or temporarily making RDS publicly accessible** (not recommended for production):

```bash
# Temporarily modify RDS to be publicly accessible (for initial setup only)
aws rds modify-db-instance \
    --db-instance-identifier helloapi-db \
    --publicly-accessible \
    --apply-immediately \
    --region us-east-1

# Wait for modification to complete
aws rds wait db-instance-available \
    --db-instance-identifier helloapi-db \
    --region us-east-1

# Update security group to allow your IP
aws ec2 authorize-security-group-ingress \
    --group-id sg-XXXXXXXXX \
    --protocol tcp \
    --port 5432 \
    --cidr YOUR_IP_ADDRESS/32 \
    --region us-east-1

# Connect using psql
psql -h helloapi-db.xxxxxxxxx.us-east-1.rds.amazonaws.com \
     -U postgres \
     -d my_database

# After connecting, your Django migrations will create the tables automatically
# Or you can manually create the table:
# CREATE TABLE users (
#     id SERIAL PRIMARY KEY,
#     name VARCHAR(255) NOT NULL,
#     email VARCHAR(254) UNIQUE NOT NULL,
#     is_active BOOLEAN DEFAULT TRUE NOT NULL
# );

# Exit psql
\q

# Make RDS private again (IMPORTANT!)
aws rds modify-db-instance \
    --db-instance-identifier helloapi-db \
    --no-publicly-accessible \
    --apply-immediately \
    --region us-east-1

# Remove public access from security group
aws ec2 revoke-security-group-ingress \
    --group-id sg-XXXXXXXXX \
    --protocol tcp \
    --port 5432 \
    --cidr YOUR_IP_ADDRESS/32 \
    --region us-east-1
```

## Step 2: Build and Push Docker Image to ECR

### 2.1 Create ECR Repository

```bash
# Create ECR repository
aws ecr create-repository \
    --repository-name helloapi \
    --region us-east-1

# Note the repositoryUri from the output
```

### 2.2 Build and Push Docker Image

```bash
# Navigate to your project directory
cd /Users/yduan/git/helloApi

# Get ECR login credentials
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build the Docker image
docker build -t helloapi .

# Tag the image
docker tag helloapi:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/helloapi:latest

# Push to ECR
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/helloapi:latest
```

**Replace `YOUR_ACCOUNT_ID`** with your AWS account ID. Find it with:
```bash
aws sts get-caller-identity --query Account --output text
```

### 2.3 Test Docker Image Locally (Optional)

```bash
# Test with docker-compose first
docker-compose up -d

# Check if it's working
curl http://localhost:8000/api/users/

# Stop
docker-compose down
```

## Step 3: Set Up AWS Secrets Manager

Store sensitive credentials securely:

```bash
# Create Django SECRET_KEY
aws secretsmanager create-secret \
    --name helloapi/django/SECRET_KEY \
    --secret-string "$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')" \
    --region us-east-1

# Store database credentials
aws secretsmanager create-secret \
    --name helloapi/db/NAME \
    --secret-string "my_database" \
    --region us-east-1

aws secretsmanager create-secret \
    --name helloapi/db/USER \
    --secret-string "postgres" \
    --region us-east-1

aws secretsmanager create-secret \
    --name helloapi/db/PASSWORD \
    --secret-string "YourSecurePassword123!" \
    --region us-east-1

aws secretsmanager create-secret \
    --name helloapi/db/HOST \
    --secret-string "helloapi-db.xxxxxxxxx.us-east-1.rds.amazonaws.com" \
    --region us-east-1

aws secretsmanager create-secret \
    --name helloapi/db/PORT \
    --secret-string "5432" \
    --region us-east-1
```

**Note the ARNs** of each secret - you'll need them for the ECS task definition.

## Step 4: Configure ECS Cluster and Service

### 4.1 Create ECS Cluster

```bash
# Create ECS cluster
aws ecs create-cluster \
    --cluster-name helloapi-cluster \
    --region us-east-1
```

### 4.2 Create IAM Roles

**ECS Task Execution Role** (allows ECS to pull images and read secrets):

```bash
# Create trust policy file
cat > ecs-task-execution-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
    --role-name ecsTaskExecutionRole \
    --assume-role-policy-document file://ecs-task-execution-trust-policy.json

# Attach AWS managed policy
aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Create custom policy for Secrets Manager access
cat > ecs-secrets-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT_ID:secret:helloapi/*"
      ]
    }
  ]
}
EOF

# Create and attach the policy
aws iam create-policy \
    --policy-name ecsSecretsManagerPolicy \
    --policy-document file://ecs-secrets-policy.json

aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/ecsSecretsManagerPolicy
```

**ECS Task Role** (allows your application to access AWS services):

```bash
# Create task role
aws iam create-role \
    --role-name ecsTaskRole \
    --assume-role-policy-document file://ecs-task-execution-trust-policy.json

# Add any additional policies your app needs (CloudWatch Logs, S3, etc.)
```

### 4.3 Create CloudWatch Log Group

```bash
# Create log group
aws logs create-log-group \
    --log-group-name /ecs/helloapi \
    --region us-east-1
```

### 4.4 Register ECS Task Definition

First, update the `ecs-task-definition.json` file with your values:
- Replace `YOUR_ACCOUNT_ID` with your AWS account ID
- Replace `YOUR_REGION` with your region (e.g., us-east-1)
- Update the SECRET ARNs with the actual ARNs from Step 3
- Update `ALLOWED_HOSTS` with your ALB DNS name (you'll get this after creating the ALB)

```bash
# Register the task definition
aws ecs register-task-definition \
    --cli-input-json file://ecs-task-definition.json \
    --region us-east-1
```

## Step 5: Set Up Application Load Balancer

### 5.1 Create Security Group for ALB

```bash
# Create security group for ALB
aws ec2 create-security-group \
    --group-name helloapi-alb-sg \
    --description "Security group for HelloAPI ALB" \
    --vpc-id vpc-XXXXXXXXX \
    --region us-east-1

# Note the SecurityGroupId (e.g., sg-ZZZZZZZZZ)

# Allow HTTP traffic from anywhere
aws ec2 authorize-security-group-ingress \
    --group-id sg-ZZZZZZZZZ \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region us-east-1

# Allow HTTPS traffic from anywhere (if using SSL)
aws ec2 authorize-security-group-ingress \
    --group-id sg-ZZZZZZZZZ \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0 \
    --region us-east-1
```

### 5.2 Create Target Group

```bash
# Create target group
aws elbv2 create-target-group \
    --name helloapi-tg \
    --protocol HTTP \
    --port 8000 \
    --vpc-id vpc-XXXXXXXXX \
    --target-type ip \
    --health-check-enabled \
    --health-check-path /api/users/ \
    --health-check-interval-seconds 30 \
    --health-check-timeout-seconds 5 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 3 \
    --region us-east-1

# Note the TargetGroupArn from the output
```

### 5.3 Create Application Load Balancer

```bash
# Create ALB (requires at least 2 subnets in different AZs)
aws elbv2 create-load-balancer \
    --name helloapi-alb \
    --subnets subnet-XXXXXXXX subnet-YYYYYYYY \
    --security-groups sg-ZZZZZZZZZ \
    --scheme internet-facing \
    --type application \
    --ip-address-type ipv4 \
    --region us-east-1

# Note the LoadBalancerArn and DNSName from the output
```

### 5.4 Create Listener

```bash
# Create listener (HTTP)
aws elbv2 create-listener \
    --load-balancer-arn arn:aws:elasticloadbalancing:us-east-1:YOUR_ACCOUNT_ID:loadbalancer/app/helloapi-alb/XXXX \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-east-1:YOUR_ACCOUNT_ID:targetgroup/helloapi-tg/YYYY \
    --region us-east-1
```

**For HTTPS** (recommended for production):
1. Request an SSL certificate from AWS Certificate Manager (ACM)
2. Create an HTTPS listener on port 443
3. Optionally, create a redirect rule from HTTP to HTTPS

## Step 6: Configure Security Groups

### 6.1 Create Security Group for ECS Tasks

```bash
# Create security group for ECS tasks
aws ec2 create-security-group \
    --group-name helloapi-ecs-sg \
    --description "Security group for HelloAPI ECS tasks" \
    --vpc-id vpc-XXXXXXXXX \
    --region us-east-1

# Note the SecurityGroupId (e.g., sg-YYYYYYYY)

# Allow traffic from ALB
aws ec2 authorize-security-group-ingress \
    --group-id sg-YYYYYYYY \
    --protocol tcp \
    --port 8000 \
    --source-group sg-ZZZZZZZZZ \
    --region us-east-1

# Allow outbound traffic (for downloading packages, accessing RDS, etc.)
aws ec2 authorize-security-group-egress \
    --group-id sg-YYYYYYYY \
    --protocol -1 \
    --cidr 0.0.0.0/0 \
    --region us-east-1
```

### 6.2 Update RDS Security Group

Now update the RDS security group to allow traffic from ECS tasks:

```bash
# Allow PostgreSQL access from ECS tasks
aws ec2 authorize-security-group-ingress \
    --group-id sg-XXXXXXXXX \
    --protocol tcp \
    --port 5432 \
    --source-group sg-YYYYYYYY \
    --region us-east-1
```

## Step 7: Deploy Your Application

### 7.1 Create ECS Service

```bash
# Create ECS service
aws ecs create-service \
    --cluster helloapi-cluster \
    --service-name helloapi-service \
    --task-definition helloapi-task \
    --desired-count 2 \
    --launch-type FARGATE \
    --platform-version LATEST \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-XXXXXXXX,subnet-YYYYYYYY],securityGroups=[sg-YYYYYYYY],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:YOUR_ACCOUNT_ID:targetgroup/helloapi-tg/YYYY,containerName=helloapi,containerPort=8000" \
    --health-check-grace-period-seconds 60 \
    --region us-east-1
```

### 7.2 Enable Auto Scaling (Optional but Recommended)

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --scalable-dimension ecs:service:DesiredCount \
    --resource-id service/helloapi-cluster/helloapi-service \
    --min-capacity 2 \
    --max-capacity 10 \
    --region us-east-1

# Create scaling policy based on CPU utilization
aws application-autoscaling put-scaling-policy \
    --service-namespace ecs \
    --scalable-dimension ecs:service:DesiredCount \
    --resource-id service/helloapi-cluster/helloapi-service \
    --policy-name cpu-scaling-policy \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration file://scaling-policy.json \
    --region us-east-1
```

Create `scaling-policy.json`:
```json
{
  "TargetValue": 70.0,
  "PredefinedMetricSpecification": {
    "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
  },
  "ScaleInCooldown": 300,
  "ScaleOutCooldown": 60
}
```

## Step 8: Run Database Migrations

You need to run Django migrations to create the database tables. You can do this by:

### Option 1: Using ECS Exec (Recommended)

```bash
# First, update your ECS service to enable ECS Exec
aws ecs update-service \
    --cluster helloapi-cluster \
    --service helloapi-service \
    --enable-execute-command \
    --region us-east-1

# Get a running task ID
TASK_ID=$(aws ecs list-tasks \
    --cluster helloapi-cluster \
    --service-name helloapi-service \
    --query 'taskArns[0]' \
    --output text \
    --region us-east-1 | cut -d'/' -f3)

# Execute commands in the container
aws ecs execute-command \
    --cluster helloapi-cluster \
    --task $TASK_ID \
    --container helloapi \
    --interactive \
    --command "/bin/bash" \
    --region us-east-1

# Once inside the container, run migrations
python manage.py migrate

# Create a superuser (optional)
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --no-input

# Exit the container
exit
```

### Option 2: Create a One-Off Task

Create a separate task definition for migrations and run it as a one-off task.

## Post-Deployment

### Update ALLOWED_HOSTS

After your ALB is created, update your ECS task definition with the correct `ALLOWED_HOSTS`:

```bash
# Get your ALB DNS name
aws elbv2 describe-load-balancers \
    --names helloapi-alb \
    --query 'LoadBalancers[0].DNSName' \
    --output text \
    --region us-east-1

# Update ecs-task-definition.json with this DNS name
# Then register a new task definition revision
aws ecs register-task-definition \
    --cli-input-json file://ecs-task-definition.json \
    --region us-east-1

# Update the service to use the new task definition
aws ecs update-service \
    --cluster helloapi-cluster \
    --service helloapi-service \
    --task-definition helloapi-task \
    --force-new-deployment \
    --region us-east-1
```

### Set Up Custom Domain (Optional)

1. **Register a domain** or use an existing one
2. **Create a hosted zone** in Route 53
3. **Create an A record** (Alias) pointing to your ALB
4. **Request an SSL certificate** from ACM for your domain
5. **Add HTTPS listener** to your ALB using the certificate
6. **Update ALLOWED_HOSTS** and **CORS_ALLOWED_ORIGINS** in your task definition

### Test Your Deployment

```bash
# Get your ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --names helloapi-alb \
    --query 'LoadBalancers[0].DNSName' \
    --output text \
    --region us-east-1)

# Test the API
curl http://$ALB_DNS/api/users/

# You should get a JSON response with your users
```

## Monitoring and Troubleshooting

### CloudWatch Logs

View logs in CloudWatch:

```bash
# View recent logs
aws logs tail /ecs/helloapi --follow --region us-east-1
```

Or use the AWS Console:
1. Go to CloudWatch → Log groups
2. Select `/ecs/helloapi`
3. View log streams

### ECS Service Events

```bash
# Check service events
aws ecs describe-services \
    --cluster helloapi-cluster \
    --services helloapi-service \
    --query 'services[0].events[:10]' \
    --region us-east-1
```

### Task Status

```bash
# List running tasks
aws ecs list-tasks \
    --cluster helloapi-cluster \
    --service-name helloapi-service \
    --region us-east-1

# Describe a specific task
aws ecs describe-tasks \
    --cluster helloapi-cluster \
    --tasks TASK_ARN \
    --region us-east-1
```

### Common Issues

**Issue 1: Tasks fail to start**
- Check CloudWatch logs for error messages
- Verify IAM roles have correct permissions
- Ensure security groups allow necessary traffic
- Verify secrets are configured correctly

**Issue 2: Health checks failing**
- Check that health check path (`/api/users/`) is accessible
- Verify security groups allow traffic from ALB to ECS tasks
- Check CloudWatch logs for application errors
- Ensure database connection is working

**Issue 3: Database connection errors**
- Verify RDS security group allows traffic from ECS security group
- Check that database credentials in Secrets Manager are correct
- Ensure RDS instance is in the same VPC as ECS tasks
- Verify subnet routing allows communication

## Cost Estimation

Approximate monthly costs (US East region):

- **RDS db.t3.micro**: ~$15-20/month
- **ECS Fargate** (2 tasks, 0.5 vCPU, 1GB RAM): ~$30-35/month
- **Application Load Balancer**: ~$20-25/month
- **Data Transfer**: Varies based on traffic
- **CloudWatch Logs**: Minimal (~$1-5/month)
- **Secrets Manager**: ~$0.40/secret/month = ~$2.40/month

**Total: ~$68-87/month**

### Cost Optimization Tips

1. **Use Reserved Capacity** for predictable workloads
2. **Set up auto-scaling** to scale down during low traffic
3. **Use Fargate Spot** for non-critical workloads (up to 70% savings)
4. **Enable RDS auto-pause** for dev/staging environments
5. **Compress and archive old CloudWatch logs**
6. **Use ALB request-based pricing** instead of fixed

## Security Best Practices

1. **Never commit secrets** to Git
2. **Use AWS Secrets Manager** for all credentials
3. **Enable encryption at rest** for RDS
4. **Use HTTPS** (SSL/TLS) for all traffic
5. **Implement WAF rules** for additional security
6. **Enable VPC Flow Logs** for network monitoring
7. **Regularly update** Docker images and dependencies
8. **Use least privilege** IAM policies
9. **Enable AWS GuardDuty** for threat detection
10. **Set up CloudTrail** for audit logging

## CI/CD Integration (Bonus)

To automate deployments, you can use GitHub Actions, AWS CodePipeline, or GitLab CI/CD. Here's a basic GitHub Actions example:

```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS ECS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build, tag, and push image to Amazon ECR
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: helloapi
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
      
      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster helloapi-cluster \
            --service helloapi-service \
            --force-new-deployment \
            --region us-east-1
```

## Rollback Procedure

If something goes wrong:

```bash
# List previous task definition revisions
aws ecs list-task-definitions \
    --family-prefix helloapi-task \
    --sort DESC \
    --region us-east-1

# Update service to use a previous revision
aws ecs update-service \
    --cluster helloapi-cluster \
    --service helloapi-service \
    --task-definition helloapi-task:PREVIOUS_REVISION \
    --force-new-deployment \
    --region us-east-1
```

## Useful Commands Reference

```bash
# View service details
aws ecs describe-services --cluster helloapi-cluster --services helloapi-service --region us-east-1

# View tasks
aws ecs list-tasks --cluster helloapi-cluster --service-name helloapi-service --region us-east-1

# Force new deployment (useful after updating secrets or environment variables)
aws ecs update-service --cluster helloapi-cluster --service helloapi-service --force-new-deployment --region us-east-1

# Scale service
aws ecs update-service --cluster helloapi-cluster --service helloapi-service --desired-count 3 --region us-east-1

# View logs
aws logs tail /ecs/helloapi --follow --region us-east-1

# Check RDS status
aws rds describe-db-instances --db-instance-identifier helloapi-db --region us-east-1
```

## Next Steps

1. Set up monitoring and alerting in CloudWatch
2. Configure auto-scaling policies
3. Implement CI/CD pipeline
4. Set up custom domain with Route 53
5. Add SSL certificate for HTTPS
6. Implement database backups and disaster recovery
7. Set up staging environment
8. Configure CloudFront for CDN (if serving static files)
9. Implement rate limiting and WAF rules
10. Set up cost alerts and budgets

## Support and Resources

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [AWS RDS Documentation](https://docs.aws.amazon.com/rds/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

---

**Happy Deploying! 🚀**

For questions or issues, refer to the troubleshooting section or check AWS CloudWatch logs.

