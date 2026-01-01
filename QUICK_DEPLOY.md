# Quick Start: Deploy HelloAPI to AWS

This is a condensed version of the full deployment guide. For detailed explanations, see `AWS_DEPLOYMENT_GUIDE.md`.

## Prerequisites

```bash
# Install and configure AWS CLI
aws configure

# Verify installations
aws --version
docker --version
```

## Quick Deployment Steps

### 1. Set Environment Variables

```bash
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export VPC_ID="vpc-XXXXXXXXX"  # Your VPC ID
export SUBNET_1="subnet-XXXXXXXX"  # Public subnet in AZ 1
export SUBNET_2="subnet-YYYYYYYY"  # Public subnet in AZ 2
export DB_PASSWORD="YourSecurePassword123!"
export PROJECT_NAME="helloapi"
```

### 2. Create RDS Database

```bash
# Create DB subnet group
aws rds create-db-subnet-group \
    --db-subnet-group-name ${PROJECT_NAME}-db-subnet \
    --db-subnet-group-description "DB subnet for ${PROJECT_NAME}" \
    --subnet-ids $SUBNET_1 $SUBNET_2 \
    --region $AWS_REGION

# Create RDS security group
RDS_SG=$(aws ec2 create-security-group \
    --group-name ${PROJECT_NAME}-rds-sg \
    --description "RDS security group" \
    --vpc-id $VPC_ID \
    --region $AWS_REGION \
    --query 'GroupId' --output text)

# Create RDS instance
aws rds create-db-instance \
    --db-instance-identifier ${PROJECT_NAME}-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 15.4 \
    --master-username postgres \
    --master-user-password "$DB_PASSWORD" \
    --allocated-storage 20 \
    --storage-type gp3 \
    --db-name my_database \
    --vpc-security-group-ids $RDS_SG \
    --db-subnet-group-name ${PROJECT_NAME}-db-subnet \
    --backup-retention-period 7 \
    --no-publicly-accessible \
    --region $AWS_REGION

# Wait for RDS (takes 5-10 minutes)
aws rds wait db-instance-available --db-instance-identifier ${PROJECT_NAME}-db --region $AWS_REGION

# Get RDS endpoint
DB_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier ${PROJECT_NAME}-db \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text --region $AWS_REGION)

echo "RDS Endpoint: $DB_ENDPOINT"
```

### 3. Build and Push Docker Image

```bash
# Create ECR repository
aws ecr create-repository --repository-name $PROJECT_NAME --region $AWS_REGION

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Build and push
cd /Users/yduan/git/helloApi
docker build -t $PROJECT_NAME .
docker tag ${PROJECT_NAME}:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}:latest
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}:latest
```

### 4. Store Secrets

```bash
# Generate Django secret key
DJANGO_SECRET=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# Store all secrets
aws secretsmanager create-secret --name ${PROJECT_NAME}/django/SECRET_KEY --secret-string "$DJANGO_SECRET" --region $AWS_REGION
aws secretsmanager create-secret --name ${PROJECT_NAME}/db/NAME --secret-string "my_database" --region $AWS_REGION
aws secretsmanager create-secret --name ${PROJECT_NAME}/db/USER --secret-string "postgres" --region $AWS_REGION
aws secretsmanager create-secret --name ${PROJECT_NAME}/db/PASSWORD --secret-string "$DB_PASSWORD" --region $AWS_REGION
aws secretsmanager create-secret --name ${PROJECT_NAME}/db/HOST --secret-string "$DB_ENDPOINT" --region $AWS_REGION
aws secretsmanager create-secret --name ${PROJECT_NAME}/db/PORT --secret-string "5432" --region $AWS_REGION
```

### 5. Create IAM Roles

```bash
# Create trust policy
cat > ecs-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

# Create execution role
aws iam create-role --role-name ecsTaskExecutionRole --assume-role-policy-document file://ecs-trust-policy.json
aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Create secrets policy
cat > ecs-secrets-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["secretsmanager:GetSecretValue"],
    "Resource": ["arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:${PROJECT_NAME}/*"]
  }]
}
EOF

aws iam create-policy --policy-name ecsSecretsPolicy --policy-document file://ecs-secrets-policy.json
aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/ecsSecretsPolicy

# Create task role
aws iam create-role --role-name ecsTaskRole --assume-role-policy-document file://ecs-trust-policy.json
```

### 6. Set Up Load Balancer

```bash
# Create ALB security group
ALB_SG=$(aws ec2 create-security-group \
    --group-name ${PROJECT_NAME}-alb-sg \
    --description "ALB security group" \
    --vpc-id $VPC_ID \
    --region $AWS_REGION \
    --query 'GroupId' --output text)

aws ec2 authorize-security-group-ingress --group-id $ALB_SG --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $AWS_REGION

# Create target group
TG_ARN=$(aws elbv2 create-target-group \
    --name ${PROJECT_NAME}-tg \
    --protocol HTTP \
    --port 8000 \
    --vpc-id $VPC_ID \
    --target-type ip \
    --health-check-path /api/users/ \
    --region $AWS_REGION \
    --query 'TargetGroups[0].TargetGroupArn' --output text)

# Create ALB
ALB_ARN=$(aws elbv2 create-load-balancer \
    --name ${PROJECT_NAME}-alb \
    --subnets $SUBNET_1 $SUBNET_2 \
    --security-groups $ALB_SG \
    --scheme internet-facing \
    --region $AWS_REGION \
    --query 'LoadBalancers[0].LoadBalancerArn' --output text)

# Wait for ALB to be active
aws elbv2 wait load-balancer-available --load-balancer-arns $ALB_ARN --region $AWS_REGION

# Get ALB DNS
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --load-balancer-arns $ALB_ARN \
    --query 'LoadBalancers[0].DNSName' \
    --output text --region $AWS_REGION)

echo "ALB DNS: $ALB_DNS"

# Create listener
aws elbv2 create-listener \
    --load-balancer-arn $ALB_ARN \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=$TG_ARN \
    --region $AWS_REGION
```

### 7. Create ECS Resources

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name ${PROJECT_NAME}-cluster --region $AWS_REGION

# Create log group
aws logs create-log-group --log-group-name /ecs/${PROJECT_NAME} --region $AWS_REGION

# Create ECS security group
ECS_SG=$(aws ec2 create-security-group \
    --group-name ${PROJECT_NAME}-ecs-sg \
    --description "ECS security group" \
    --vpc-id $VPC_ID \
    --region $AWS_REGION \
    --query 'GroupId' --output text)

# Allow ALB -> ECS traffic
aws ec2 authorize-security-group-ingress \
    --group-id $ECS_SG \
    --protocol tcp \
    --port 8000 \
    --source-group $ALB_SG \
    --region $AWS_REGION

# Allow ECS -> RDS traffic
aws ec2 authorize-security-group-ingress \
    --group-id $RDS_SG \
    --protocol tcp \
    --port 5432 \
    --source-group $ECS_SG \
    --region $AWS_REGION
```

### 8. Update and Register Task Definition

```bash
# Get secret ARNs
SECRET_KEY_ARN=$(aws secretsmanager describe-secret --secret-id ${PROJECT_NAME}/django/SECRET_KEY --region $AWS_REGION --query 'ARN' --output text)
DB_NAME_ARN=$(aws secretsmanager describe-secret --secret-id ${PROJECT_NAME}/db/NAME --region $AWS_REGION --query 'ARN' --output text)
DB_USER_ARN=$(aws secretsmanager describe-secret --secret-id ${PROJECT_NAME}/db/USER --region $AWS_REGION --query 'ARN' --output text)
DB_PASSWORD_ARN=$(aws secretsmanager describe-secret --secret-id ${PROJECT_NAME}/db/PASSWORD --region $AWS_REGION --query 'ARN' --output text)
DB_HOST_ARN=$(aws secretsmanager describe-secret --secret-id ${PROJECT_NAME}/db/HOST --region $AWS_REGION --query 'ARN' --output text)
DB_PORT_ARN=$(aws secretsmanager describe-secret --secret-id ${PROJECT_NAME}/db/PORT --region $AWS_REGION --query 'ARN' --output text)

# Update task definition with actual values
sed -i.bak \
    -e "s|YOUR_ACCOUNT_ID|${AWS_ACCOUNT_ID}|g" \
    -e "s|YOUR_REGION|${AWS_REGION}|g" \
    -e "s|your-alb-dns-name.region.elb.amazonaws.com|${ALB_DNS}|g" \
    -e "s|arn:aws:secretsmanager:YOUR_REGION:YOUR_ACCOUNT_ID:secret:helloapi/django/SECRET_KEY-XXXXXX|${SECRET_KEY_ARN}|g" \
    -e "s|arn:aws:secretsmanager:YOUR_REGION:YOUR_ACCOUNT_ID:secret:helloapi/db/NAME-XXXXXX|${DB_NAME_ARN}|g" \
    -e "s|arn:aws:secretsmanager:YOUR_REGION:YOUR_ACCOUNT_ID:secret:helloapi/db/USER-XXXXXX|${DB_USER_ARN}|g" \
    -e "s|arn:aws:secretsmanager:YOUR_REGION:YOUR_ACCOUNT_ID:secret:helloapi/db/PASSWORD-XXXXXX|${DB_PASSWORD_ARN}|g" \
    -e "s|arn:aws:secretsmanager:YOUR_REGION:YOUR_ACCOUNT_ID:secret:helloapi/db/HOST-XXXXXX|${DB_HOST_ARN}|g" \
    -e "s|arn:aws:secretsmanager:YOUR_REGION:YOUR_ACCOUNT_ID:secret:helloapi/db/PORT-XXXXXX|${DB_PORT_ARN}|g" \
    ecs-task-definition.json

# Register task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json --region $AWS_REGION
```

### 9. Create ECS Service

```bash
# Create service
aws ecs create-service \
    --cluster ${PROJECT_NAME}-cluster \
    --service-name ${PROJECT_NAME}-service \
    --task-definition ${PROJECT_NAME}-task \
    --desired-count 2 \
    --launch-type FARGATE \
    --platform-version LATEST \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1,$SUBNET_2],securityGroups=[$ECS_SG],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=$TG_ARN,containerName=${PROJECT_NAME},containerPort=8000" \
    --health-check-grace-period-seconds 60 \
    --region $AWS_REGION

# Wait for service to stabilize (takes 2-3 minutes)
aws ecs wait services-stable \
    --cluster ${PROJECT_NAME}-cluster \
    --services ${PROJECT_NAME}-service \
    --region $AWS_REGION
```

### 10. Run Database Migrations

```bash
# Get running task ID
TASK_ID=$(aws ecs list-tasks \
    --cluster ${PROJECT_NAME}-cluster \
    --service-name ${PROJECT_NAME}-service \
    --query 'taskArns[0]' \
    --output text \
    --region $AWS_REGION | cut -d'/' -f3)

# Enable ECS Exec
aws ecs update-service \
    --cluster ${PROJECT_NAME}-cluster \
    --service ${PROJECT_NAME}-service \
    --enable-execute-command \
    --force-new-deployment \
    --region $AWS_REGION

# Wait for new task to start
sleep 60

# Get new task ID
TASK_ID=$(aws ecs list-tasks \
    --cluster ${PROJECT_NAME}-cluster \
    --service-name ${PROJECT_NAME}-service \
    --query 'taskArns[0]' \
    --output text \
    --region $AWS_REGION | cut -d'/' -f3)

# Run migrations (interactive - requires Session Manager plugin)
aws ecs execute-command \
    --cluster ${PROJECT_NAME}-cluster \
    --task $TASK_ID \
    --container ${PROJECT_NAME} \
    --interactive \
    --command "python manage.py migrate" \
    --region $AWS_REGION
```

### 11. Test Your Deployment

```bash
# Test the API
curl http://$ALB_DNS/api/users/

# Expected output: JSON response with users data
```

## Cleanup (When Done Testing)

```bash
# Delete ECS service
aws ecs update-service --cluster ${PROJECT_NAME}-cluster --service ${PROJECT_NAME}-service --desired-count 0 --region $AWS_REGION
aws ecs delete-service --cluster ${PROJECT_NAME}-cluster --service ${PROJECT_NAME}-service --force --region $AWS_REGION

# Delete ECS cluster
aws ecs delete-cluster --cluster ${PROJECT_NAME}-cluster --region $AWS_REGION

# Delete ALB
aws elbv2 delete-load-balancer --load-balancer-arn $ALB_ARN --region $AWS_REGION
aws elbv2 delete-target-group --target-group-arn $TG_ARN --region $AWS_REGION

# Delete RDS
aws rds delete-db-instance --db-instance-identifier ${PROJECT_NAME}-db --skip-final-snapshot --region $AWS_REGION

# Delete ECR repository
aws ecr delete-repository --repository-name $PROJECT_NAME --force --region $AWS_REGION

# Delete secrets
for secret in SECRET_KEY NAME USER PASSWORD HOST PORT; do
    aws secretsmanager delete-secret --secret-id ${PROJECT_NAME}/django/SECRET_KEY --force-delete-without-recovery --region $AWS_REGION 2>/dev/null
    aws secretsmanager delete-secret --secret-id ${PROJECT_NAME}/db/$secret --force-delete-without-recovery --region $AWS_REGION 2>/dev/null
done

# Delete security groups (wait a few minutes for resources to be deleted first)
aws ec2 delete-security-group --group-id $ECS_SG --region $AWS_REGION
aws ec2 delete-security-group --group-id $ALB_SG --region $AWS_REGION
aws ec2 delete-security-group --group-id $RDS_SG --region $AWS_REGION

# Delete IAM resources
aws iam detach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
aws iam detach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/ecsSecretsPolicy
aws iam delete-policy --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/ecsSecretsPolicy
aws iam delete-role --role-name ecsTaskExecutionRole
aws iam delete-role --role-name ecsTaskRole
```

## Monitoring

```bash
# View logs
aws logs tail /ecs/${PROJECT_NAME} --follow --region $AWS_REGION

# Check service status
aws ecs describe-services --cluster ${PROJECT_NAME}-cluster --services ${PROJECT_NAME}-service --region $AWS_REGION

# View tasks
aws ecs list-tasks --cluster ${PROJECT_NAME}-cluster --service-name ${PROJECT_NAME}-service --region $AWS_REGION
```

## Troubleshooting

1. **Tasks not starting**: Check CloudWatch logs
2. **Health checks failing**: Verify security groups and /api/users/ endpoint
3. **Can't connect to DB**: Check RDS security group allows ECS security group
4. **502/503 errors**: Check target group health in ALB console

---

For detailed explanations and advanced configurations, see `AWS_DEPLOYMENT_GUIDE.md`.

