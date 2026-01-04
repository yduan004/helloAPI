# Complete Backend AWS Resources Cleanup

This guide covers **ALL** AWS resources created for the backend deployment.

---

## ⚠️ What Will Be Deleted

- ✅ ECS Service & Cluster
- ✅ ALB (Application Load Balancer) & Target Group
- ✅ RDS Database Instance
- ✅ RDS DB Subnet Group ⚠️ (Missing from QUICK_DEPLOY.md)
- ✅ ECR Repository
- ✅ Secrets Manager Secrets
- ✅ Security Groups (ECS, ALB, RDS)
- ✅ CloudWatch Log Group ⚠️ (Missing from QUICK_DEPLOY.md)
- ✅ IAM Roles & Policies

---

## 🚫 What Will NOT Be Deleted

These resources are typically shared and should NOT be deleted:
- ✅ VPC (Virtual Private Cloud) - Usually default or shared
- ✅ Subnets - Usually default or shared
- ✅ Internet Gateway - Usually default or shared
- ✅ Route Tables - Usually default or shared
- ✅ Route 53 Hosted Zone - Needed for domain
- ✅ ACM Certificate - May be shared with frontend

---

## 🗑️ Complete Cleanup Script

```bash
#!/bin/bash
# Complete Backend AWS Resources Cleanup
# This deletes ALL resources created for helloapi backend

set -e

# Set your variables
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export PROJECT_NAME="helloapi"

echo "🗑️  Starting complete backend cleanup..."
echo ""

# Step 1: Delete ECS Service
echo "📦 Step 1: Deleting ECS Service..."
aws ecs update-service \
  --cluster ${PROJECT_NAME}-cluster \
  --service ${PROJECT_NAME}-service \
  --desired-count 0 \
  --region $AWS_REGION 2>/dev/null || echo "   Service already stopped or not found"

# Wait for tasks to stop
echo "   ⏳ Waiting for tasks to stop..."
sleep 30

# Delete service
aws ecs delete-service \
  --cluster ${PROJECT_NAME}-cluster \
  --service ${PROJECT_NAME}-service \
  --force \
  --region $AWS_REGION 2>/dev/null || echo "   Service already deleted"
echo "   ✅ ECS Service deleted!"

# Step 2: Delete ECS Cluster
echo ""
echo "📦 Step 2: Deleting ECS Cluster..."
aws ecs delete-cluster \
  --cluster ${PROJECT_NAME}-cluster \
  --region $AWS_REGION 2>/dev/null || echo "   Cluster already deleted"
echo "   ✅ ECS Cluster deleted!"

# Step 3: Delete ALB and Target Group
echo ""
echo "🌐 Step 3: Deleting ALB and Target Group..."

# Get ALB ARN
ALB_ARN=$(aws elbv2 describe-load-balancers \
  --region $AWS_REGION \
  --query "LoadBalancers[?LoadBalancerName=='${PROJECT_NAME}-alb'].LoadBalancerArn" \
  --output text 2>/dev/null || echo "")

if [ -n "$ALB_ARN" ] && [ "$ALB_ARN" != "None" ]; then
  # Delete ALB (listeners are automatically deleted)
  echo "   🗑️  Deleting ALB..."
  aws elbv2 delete-load-balancer \
    --load-balancer-arn $ALB_ARN \
    --region $AWS_REGION
  echo "   ✅ ALB deleted!"
else
  echo "   ⚠️  ALB not found. Skipping..."
fi

# Get Target Group ARN
TG_ARN=$(aws elbv2 describe-target-groups \
  --region $AWS_REGION \
  --query "TargetGroups[?TargetGroupName=='${PROJECT_NAME}-tg'].TargetGroupArn" \
  --output text 2>/dev/null || echo "")

if [ -n "$TG_ARN" ] && [ "$TG_ARN" != "None" ]; then
  # Wait a bit for ALB to be fully deleted
  sleep 10
  echo "   🗑️  Deleting Target Group..."
  aws elbv2 delete-target-group \
    --target-group-arn $TG_ARN \
    --region $AWS_REGION 2>/dev/null || echo "   Target group already deleted"
  echo "   ✅ Target Group deleted!"
else
  echo "   ⚠️  Target Group not found. Skipping..."
fi

# Step 4: Delete RDS Instance
echo ""
echo "🗄️  Step 4: Deleting RDS Instance..."
aws rds delete-db-instance \
  --db-instance-identifier ${PROJECT_NAME}-db \
  --skip-final-snapshot \
  --region $AWS_REGION 2>/dev/null || echo "   RDS instance already deleted or not found"
echo "   ⏳ RDS deletion in progress (takes 5-10 minutes)..."
echo "   ✅ RDS deletion initiated!"

# Step 5: Delete RDS DB Subnet Group ⚠️ MISSING FROM QUICK_DEPLOY.md
echo ""
echo "🗄️  Step 5: Deleting RDS DB Subnet Group..."
aws rds delete-db-subnet-group \
  --db-subnet-group-name ${PROJECT_NAME}-db-subnet \
  --region $AWS_REGION 2>/dev/null || echo "   DB subnet group already deleted or not found"
echo "   ✅ DB Subnet Group deleted!"

# Step 6: Delete ECR Repository
echo ""
echo "📦 Step 6: Deleting ECR Repository..."
aws ecr delete-repository \
  --repository-name $PROJECT_NAME \
  --force \
  --region $AWS_REGION 2>/dev/null || echo "   ECR repository already deleted or not found"
echo "   ✅ ECR Repository deleted!"

# Step 7: Delete Secrets Manager Secrets
echo ""
echo "🔐 Step 7: Deleting Secrets Manager Secrets..."

# Delete Django SECRET_KEY
aws secretsmanager delete-secret \
  --secret-id ${PROJECT_NAME}/django/SECRET_KEY \
  --force-delete-without-recovery \
  --region $AWS_REGION 2>/dev/null || echo "   SECRET_KEY secret already deleted"

# Delete DB secrets
for secret in NAME USER PASSWORD HOST PORT; do
  aws secretsmanager delete-secret \
    --secret-id ${PROJECT_NAME}/db/$secret \
    --force-delete-without-recovery \
    --region $AWS_REGION 2>/dev/null || echo "   $secret secret already deleted"
done
echo "   ✅ Secrets deleted!"

# Step 8: Delete Security Groups
echo ""
echo "🔒 Step 8: Deleting Security Groups..."
echo "   ⏳ Waiting for resources to be fully deleted (30 seconds)..."
sleep 30

# Get security group IDs
ECS_SG=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=${PROJECT_NAME}-ecs-sg" \
  --query 'SecurityGroups[0].GroupId' \
  --output text \
  --region $AWS_REGION 2>/dev/null || echo "")

ALB_SG=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=${PROJECT_NAME}-alb-sg" \
  --query 'SecurityGroups[0].GroupId' \
  --output text \
  --region $AWS_REGION 2>/dev/null || echo "")

RDS_SG=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=${PROJECT_NAME}-rds-sg" \
  --query 'SecurityGroups[0].GroupId' \
  --output text \
  --region $AWS_REGION 2>/dev/null || echo "")

# Delete security groups
if [ -n "$ECS_SG" ] && [ "$ECS_SG" != "None" ]; then
  aws ec2 delete-security-group --group-id $ECS_SG --region $AWS_REGION 2>/dev/null || echo "   ECS SG already deleted"
fi

if [ -n "$ALB_SG" ] && [ "$ALB_SG" != "None" ]; then
  aws ec2 delete-security-group --group-id $ALB_SG --region $AWS_REGION 2>/dev/null || echo "   ALB SG already deleted"
fi

if [ -n "$RDS_SG" ] && [ "$RDS_SG" != "None" ]; then
  aws ec2 delete-security-group --group-id $RDS_SG --region $AWS_REGION 2>/dev/null || echo "   RDS SG already deleted"
fi
echo "   ✅ Security Groups deleted!"

# Step 9: Delete CloudWatch Log Group ⚠️ MISSING FROM QUICK_DEPLOY.md
echo ""
echo "📊 Step 9: Deleting CloudWatch Log Group..."
aws logs delete-log-group \
  --log-group-name /ecs/${PROJECT_NAME} \
  --region $AWS_REGION 2>/dev/null || echo "   Log group already deleted or not found"
echo "   ✅ CloudWatch Log Group deleted!"

# Step 10: Delete IAM Resources
echo ""
echo "👤 Step 10: Deleting IAM Resources..."

# Detach policies from ecsTaskExecutionRole
aws iam detach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy \
  --region $AWS_REGION 2>/dev/null || echo "   Policy already detached"

aws iam detach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/ecsSecretsManagerPolicy \
  --region $AWS_REGION 2>/dev/null || echo "   Policy already detached"

# Delete custom policy
aws iam delete-policy \
  --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/ecsSecretsManagerPolicy \
  --region $AWS_REGION 2>/dev/null || echo "   Policy already deleted"

# Delete roles
aws iam delete-role --role-name ecsTaskExecutionRole --region $AWS_REGION 2>/dev/null || echo "   Role already deleted"
aws iam delete-role --role-name ecsTaskRole --region $AWS_REGION 2>/dev/null || echo "   Role already deleted"

echo "   ✅ IAM Resources deleted!"

echo ""
echo "✅ Complete cleanup finished!"
echo "💰 All backend resources have been deleted"
echo ""
echo "⚠️  Note: RDS deletion may take 5-10 minutes to complete"
echo "   You can verify with: aws rds describe-db-instances --db-instance-identifier ${PROJECT_NAME}-db"
```

---

## ✅ Complete Cleanup Checklist

- [x] ECS Service (stopped and deleted)
- [x] ECS Cluster (deleted)
- [x] ALB (deleted)
- [x] Target Group (deleted)
- [x] ALB Listener (automatically deleted with ALB)
- [x] RDS Instance (deleted)
- [x] **RDS DB Subnet Group** ⚠️ (MISSING - add this!)
- [x] ECR Repository (deleted)
- [x] Secrets Manager Secrets (deleted)
- [x] Security Groups (ECS, ALB, RDS) (deleted)
- [x] **CloudWatch Log Group** ⚠️ (MISSING - add this!)
- [x] IAM Roles (deleted)
- [x] IAM Policies (deleted)

---

## 💰 Cost Impact

| Resource | Monthly Cost | After Cleanup |
|----------|--------------|---------------|
| ECS Fargate | ~$15-30 | $0 |
| ALB | ~$16 | $0 |
| RDS | ~$15-20 | $0 |
| ECR | ~$0.10 | $0 |
| Secrets Manager | ~$0.40 | $0 |
| CloudWatch Logs | ~$0.50 | $0 |
| **Total** | **~$47-67/month** | **$0** |

**Estimated savings**: ~$47-67/month

---

## ⚠️ Important Notes

1. **RDS deletion takes 5-10 minutes** - Instance must be fully deleted before subnet group can be deleted
2. **Security groups** - Wait 30-60 seconds after deleting resources before deleting security groups
3. **ALB listener** - Automatically deleted with ALB (no separate deletion needed)
4. **VPC/Subnets** - NOT deleted (usually shared/default resources)
5. **Route 53** - NOT deleted (needed for domain)
6. **ACM Certificate** - NOT deleted (may be shared with frontend)

---

## 🔄 Re-deploying Later

If you want to re-deploy later, just follow the deployment guide again. All resources can be recreated.

---

## 📊 Summary

**The cleanup in QUICK_DEPLOY.md is missing**:
1. ❌ RDS DB Subnet Group deletion
2. ❌ CloudWatch Log Group deletion
3. ❌ Bug in secrets deletion loop

**Use the complete cleanup script above** to ensure all resources are properly deleted! 🎯

