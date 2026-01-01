#!/bin/bash

# AWS ECS Deployment Script for HelloAPI
# This script automates the deployment of HelloAPI to AWS ECS with RDS

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
print_step() {
    echo -e "${GREEN}==>${NC} $1"
}

print_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

# Check prerequisites
print_step "Checking prerequisites..."
command -v aws >/dev/null 2>&1 || { print_error "AWS CLI is not installed. Aborting."; exit 1; }
command -v docker >/dev/null 2>&1 || { print_error "Docker is not installed. Aborting."; exit 1; }
command -v python >/dev/null 2>&1 || { print_error "Python is not installed. Aborting."; exit 1; }

# Get configuration
echo ""
echo "=========================================="
echo "  HelloAPI AWS Deployment Configuration"
echo "=========================================="
echo ""

read -p "Enter AWS Region (default: us-east-1): " AWS_REGION
AWS_REGION=${AWS_REGION:-us-east-1}

read -p "Enter VPC ID: " VPC_ID
if [ -z "$VPC_ID" ]; then
    print_error "VPC ID is required"
    exit 1
fi

read -p "Enter Subnet 1 ID (public, AZ 1): " SUBNET_1
if [ -z "$SUBNET_1" ]; then
    print_error "Subnet 1 is required"
    exit 1
fi

read -p "Enter Subnet 2 ID (public, AZ 2): " SUBNET_2
if [ -z "$SUBNET_2" ]; then
    print_error "Subnet 2 is required"
    exit 1
fi

read -sp "Enter RDS Master Password: " DB_PASSWORD
echo ""
if [ -z "$DB_PASSWORD" ]; then
    print_error "Database password is required"
    exit 1
fi

read -p "Enter Project Name (default: helloapi): " PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-helloapi}

# Get AWS Account ID
print_step "Getting AWS Account ID..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account ID: $AWS_ACCOUNT_ID"

# Confirmation
echo ""
echo "=========================================="
echo "  Deployment Configuration Summary"
echo "=========================================="
echo "Region: $AWS_REGION"
echo "VPC: $VPC_ID"
echo "Subnet 1: $SUBNET_1"
echo "Subnet 2: $SUBNET_2"
echo "Project Name: $PROJECT_NAME"
echo "Account ID: $AWS_ACCOUNT_ID"
echo "=========================================="
echo ""
read -p "Proceed with deployment? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

# Start deployment
echo ""
print_step "Starting deployment..."

# 1. Create RDS resources
print_step "Creating RDS database..."

aws rds create-db-subnet-group \
    --db-subnet-group-name ${PROJECT_NAME}-db-subnet \
    --db-subnet-group-description "DB subnet for ${PROJECT_NAME}" \
    --subnet-ids $SUBNET_1 $SUBNET_2 \
    --region $AWS_REGION 2>/dev/null || print_warning "DB subnet group may already exist"

RDS_SG=$(aws ec2 create-security-group \
    --group-name ${PROJECT_NAME}-rds-sg \
    --description "RDS security group for ${PROJECT_NAME}" \
    --vpc-id $VPC_ID \
    --region $AWS_REGION \
    --query 'GroupId' --output text 2>/dev/null || aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=${PROJECT_NAME}-rds-sg" "Name=vpc-id,Values=$VPC_ID" \
    --query 'SecurityGroups[0].GroupId' --output text --region $AWS_REGION)

echo "RDS Security Group: $RDS_SG"

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
    --region $AWS_REGION 2>/dev/null || print_warning "RDS instance may already exist"

print_step "Waiting for RDS to become available (this takes 5-10 minutes)..."
aws rds wait db-instance-available --db-instance-identifier ${PROJECT_NAME}-db --region $AWS_REGION

DB_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier ${PROJECT_NAME}-db \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text --region $AWS_REGION)

echo "RDS Endpoint: $DB_ENDPOINT"

# 2. Build and push Docker image
print_step "Creating ECR repository..."
aws ecr create-repository --repository-name $PROJECT_NAME --region $AWS_REGION 2>/dev/null || print_warning "ECR repository may already exist"

print_step "Building Docker image..."
docker build -t $PROJECT_NAME .

print_step "Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

print_step "Pushing image to ECR..."
docker tag ${PROJECT_NAME}:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}:latest
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}:latest

# 3. Store secrets
print_step "Storing secrets in AWS Secrets Manager..."
DJANGO_SECRET=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

for secret in "django/SECRET_KEY:$DJANGO_SECRET" "db/NAME:my_database" "db/USER:postgres" "db/PASSWORD:$DB_PASSWORD" "db/HOST:$DB_ENDPOINT" "db/PORT:5432"; do
    secret_name="${PROJECT_NAME}/${secret%%:*}"
    secret_value="${secret#*:}"
    aws secretsmanager create-secret --name "$secret_name" --secret-string "$secret_value" --region $AWS_REGION 2>/dev/null || \
    aws secretsmanager update-secret --secret-id "$secret_name" --secret-string "$secret_value" --region $AWS_REGION
done

# 4. Create IAM roles
print_step "Creating IAM roles..."

cat > /tmp/ecs-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

aws iam create-role --role-name ecsTaskExecutionRole --assume-role-policy-document file:///tmp/ecs-trust-policy.json 2>/dev/null || print_warning "Role may already exist"
aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy 2>/dev/null || true

cat > /tmp/ecs-secrets-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["secretsmanager:GetSecretValue"],
    "Resource": ["arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:${PROJECT_NAME}/*"]
  }]
}
EOF

aws iam create-policy --policy-name ecsSecretsPolicy --policy-document file:///tmp/ecs-secrets-policy.json 2>/dev/null || print_warning "Policy may already exist"
aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/ecsSecretsPolicy 2>/dev/null || true

aws iam create-role --role-name ecsTaskRole --assume-role-policy-document file:///tmp/ecs-trust-policy.json 2>/dev/null || print_warning "Role may already exist"

# 5. Create ALB
print_step "Creating Application Load Balancer..."

ALB_SG=$(aws ec2 create-security-group \
    --group-name ${PROJECT_NAME}-alb-sg \
    --description "ALB security group for ${PROJECT_NAME}" \
    --vpc-id $VPC_ID \
    --region $AWS_REGION \
    --query 'GroupId' --output text 2>/dev/null || aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=${PROJECT_NAME}-alb-sg" "Name=vpc-id,Values=$VPC_ID" \
    --query 'SecurityGroups[0].GroupId' --output text --region $AWS_REGION)

aws ec2 authorize-security-group-ingress --group-id $ALB_SG --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $AWS_REGION 2>/dev/null || true

TG_ARN=$(aws elbv2 create-target-group \
    --name ${PROJECT_NAME}-tg \
    --protocol HTTP \
    --port 8000 \
    --vpc-id $VPC_ID \
    --target-type ip \
    --health-check-path /api/users/ \
    --region $AWS_REGION \
    --query 'TargetGroups[0].TargetGroupArn' --output text 2>/dev/null || aws elbv2 describe-target-groups \
    --names ${PROJECT_NAME}-tg \
    --query 'TargetGroups[0].TargetGroupArn' --output text --region $AWS_REGION)

ALB_ARN=$(aws elbv2 create-load-balancer \
    --name ${PROJECT_NAME}-alb \
    --subnets $SUBNET_1 $SUBNET_2 \
    --security-groups $ALB_SG \
    --scheme internet-facing \
    --region $AWS_REGION \
    --query 'LoadBalancers[0].LoadBalancerArn' --output text 2>/dev/null || aws elbv2 describe-load-balancers \
    --names ${PROJECT_NAME}-alb \
    --query 'LoadBalancers[0].LoadBalancerArn' --output text --region $AWS_REGION)

print_step "Waiting for ALB to become active..."
aws elbv2 wait load-balancer-available --load-balancer-arns $ALB_ARN --region $AWS_REGION

ALB_DNS=$(aws elbv2 describe-load-balancers \
    --load-balancer-arns $ALB_ARN \
    --query 'LoadBalancers[0].DNSName' \
    --output text --region $AWS_REGION)

aws elbv2 create-listener \
    --load-balancer-arn $ALB_ARN \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=$TG_ARN \
    --region $AWS_REGION 2>/dev/null || print_warning "Listener may already exist"

# 6. Create ECS resources
print_step "Creating ECS cluster and service..."

aws ecs create-cluster --cluster-name ${PROJECT_NAME}-cluster --region $AWS_REGION 2>/dev/null || print_warning "Cluster may already exist"
aws logs create-log-group --log-group-name /ecs/${PROJECT_NAME} --region $AWS_REGION 2>/dev/null || print_warning "Log group may already exist"

ECS_SG=$(aws ec2 create-security-group \
    --group-name ${PROJECT_NAME}-ecs-sg \
    --description "ECS security group for ${PROJECT_NAME}" \
    --vpc-id $VPC_ID \
    --region $AWS_REGION \
    --query 'GroupId' --output text 2>/dev/null || aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=${PROJECT_NAME}-ecs-sg" "Name=vpc-id,Values=$VPC_ID" \
    --query 'SecurityGroups[0].GroupId' --output text --region $AWS_REGION)

aws ec2 authorize-security-group-ingress --group-id $ECS_SG --protocol tcp --port 8000 --source-group $ALB_SG --region $AWS_REGION 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $RDS_SG --protocol tcp --port 5432 --source-group $ECS_SG --region $AWS_REGION 2>/dev/null || true

# 7. Update and register task definition
print_step "Registering ECS task definition..."

# Get secret ARNs
SECRET_KEY_ARN=$(aws secretsmanager describe-secret --secret-id ${PROJECT_NAME}/django/SECRET_KEY --region $AWS_REGION --query 'ARN' --output text)
DB_NAME_ARN=$(aws secretsmanager describe-secret --secret-id ${PROJECT_NAME}/db/NAME --region $AWS_REGION --query 'ARN' --output text)
DB_USER_ARN=$(aws secretsmanager describe-secret --secret-id ${PROJECT_NAME}/db/USER --region $AWS_REGION --query 'ARN' --output text)
DB_PASSWORD_ARN=$(aws secretsmanager describe-secret --secret-id ${PROJECT_NAME}/db/PASSWORD --region $AWS_REGION --query 'ARN' --output text)
DB_HOST_ARN=$(aws secretsmanager describe-secret --secret-id ${PROJECT_NAME}/db/HOST --region $AWS_REGION --query 'ARN' --output text)
DB_PORT_ARN=$(aws secretsmanager describe-secret --secret-id ${PROJECT_NAME}/db/PORT --region $AWS_REGION --query 'ARN' --output text)

# Create temporary task definition
sed \
    -e "s|YOUR_ACCOUNT_ID|${AWS_ACCOUNT_ID}|g" \
    -e "s|YOUR_REGION|${AWS_REGION}|g" \
    -e "s|your-alb-dns-name.region.elb.amazonaws.com|${ALB_DNS}|g" \
    -e "s|arn:aws:secretsmanager:YOUR_REGION:YOUR_ACCOUNT_ID:secret:helloapi/django/SECRET_KEY-XXXXXX|${SECRET_KEY_ARN}|g" \
    -e "s|arn:aws:secretsmanager:YOUR_REGION:YOUR_ACCOUNT_ID:secret:helloapi/db/NAME-XXXXXX|${DB_NAME_ARN}|g" \
    -e "s|arn:aws:secretsmanager:YOUR_REGION:YOUR_ACCOUNT_ID:secret:helloapi/db/USER-XXXXXX|${DB_USER_ARN}|g" \
    -e "s|arn:aws:secretsmanager:YOUR_REGION:YOUR_ACCOUNT_ID:secret:helloapi/db/PASSWORD-XXXXXX|${DB_PASSWORD_ARN}|g" \
    -e "s|arn:aws:secretsmanager:YOUR_REGION:YOUR_ACCOUNT_ID:secret:helloapi/db/HOST-XXXXXX|${DB_HOST_ARN}|g" \
    -e "s|arn:aws:secretsmanager:YOUR_REGION:YOUR_ACCOUNT_ID:secret:helloapi/db/PORT-XXXXXX|${DB_PORT_ARN}|g" \
    ecs-task-definition.json > /tmp/ecs-task-definition-updated.json

aws ecs register-task-definition --cli-input-json file:///tmp/ecs-task-definition-updated.json --region $AWS_REGION

# 8. Create ECS service
print_step "Creating ECS service..."

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
    --region $AWS_REGION 2>/dev/null || print_warning "Service may already exist - updating instead"

if [ $? -ne 0 ]; then
    aws ecs update-service \
        --cluster ${PROJECT_NAME}-cluster \
        --service ${PROJECT_NAME}-service \
        --force-new-deployment \
        --region $AWS_REGION
fi

print_step "Waiting for service to stabilize (this may take 2-3 minutes)..."
aws ecs wait services-stable --cluster ${PROJECT_NAME}-cluster --services ${PROJECT_NAME}-service --region $AWS_REGION

# Cleanup temp files
rm -f /tmp/ecs-trust-policy.json /tmp/ecs-secrets-policy.json /tmp/ecs-task-definition-updated.json

# Done!
echo ""
echo "=========================================="
echo -e "${GREEN}  Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "Your API is now available at:"
echo "  http://$ALB_DNS/api/users/"
echo ""
echo "Next steps:"
echo "  1. Run database migrations using ECS Exec"
echo "  2. Test your API endpoint"
echo "  3. Set up a custom domain (optional)"
echo "  4. Add SSL certificate for HTTPS (recommended)"
echo ""
echo "To view logs:"
echo "  aws logs tail /ecs/${PROJECT_NAME} --follow --region $AWS_REGION"
echo ""
echo "To run migrations:"
echo "  See the 'Run Database Migrations' section in AWS_DEPLOYMENT_GUIDE.md"
echo ""
echo "=========================================="

