# GitHub Actions CI/CD Setup Guide

This guide will help you set up automatic deployment to AWS ECS using GitHub Actions.

---

## 🎯 What This CI/CD Pipeline Does

Every time you push code to the `main` branch:

1. ✅ **Builds** your Docker image for linux/amd64
2. ✅ **Pushes** the image to Amazon ECR
3. ✅ **Updates** the ECS task definition with the new image
4. ✅ **Deploys** to your ECS service
5. ✅ **Waits** for deployment to stabilize
6. ✅ **Reports** success or failure

---

## 📋 Prerequisites

- ✅ GitHub repository for your code
- ✅ AWS account with ECS cluster already set up
- ✅ AWS IAM user with appropriate permissions

---

## 🔐 Step 1: Create AWS IAM User for GitHub Actions

### 1.1 Create IAM User

```bash
aws iam create-user --user-name github-actions-helloapi
```

### 1.2 Create IAM Policy

Create a file `github-actions-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecs:DescribeServices",
        "ecs:DescribeTaskDefinition",
        "ecs:DescribeTasks",
        "ecs:ListTasks",
        "ecs:RegisterTaskDefinition",
        "ecs:UpdateService"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": [
        "arn:aws:iam::835745295392:role/ecsTaskExecutionRole",
        "arn:aws:iam::835745295392:role/ecsTaskRole"
      ]
    }
  ]
}
```

### 1.3 Attach Policy to User

```bash
# Create the policy
aws iam create-policy \
    --policy-name GitHubActionsECSDeployPolicy \
    --policy-document file://github-actions-policy.json

# Attach to user (replace ACCOUNT_ID with your AWS account ID)
aws iam attach-user-policy \
    --user-name github-actions-helloapi \
    --policy-arn arn:aws:iam::835745295392:policy/GitHubActionsECSDeployPolicy
```

### 1.4 Create Access Keys

```bash
aws iam create-access-key --user-name github-actions-helloapi
```

**Save the output!** You'll need:
- `AccessKeyId`
- `SecretAccessKey`

---

## 🔑 Step 2: Add Secrets to GitHub

### 2.1 Navigate to GitHub Repository Settings

1. Go to your GitHub repository
2. Click **Settings**
3. Click **Secrets and variables** → **Actions**
4. Click **New repository secret**

### 2.2 Add AWS Credentials

Add these two secrets:

**Secret 1:**
- Name: `AWS_ACCESS_KEY_ID`
- Value: `<Your AccessKeyId from Step 1.4>`

**Secret 2:**
- Name: `AWS_SECRET_ACCESS_KEY`
- Value: `<Your SecretAccessKey from Step 1.4>`

---

## 📁 Step 3: Commit the Workflow File

The workflow file is already created at `.github/workflows/deploy.yml`

```bash
git add .github/workflows/deploy.yml
git commit -m "Add GitHub Actions CI/CD pipeline"
git push origin main
```

---

## 🚀 Step 4: Test the Deployment

### Option 1: Push to Main Branch

```bash
# Make a small change
echo "# CI/CD Test" >> README.md

# Commit and push
git add README.md
git commit -m "Test CI/CD deployment"
git push origin main
```

### Option 2: Manual Trigger

1. Go to GitHub → **Actions** tab
2. Click on **Deploy to AWS ECS** workflow
3. Click **Run workflow**
4. Select branch and click **Run workflow**

---

## 📊 Step 5: Monitor the Deployment

### In GitHub:

1. Go to **Actions** tab
2. Click on the running workflow
3. Watch the deployment progress in real-time

### In AWS Console:

1. Go to **ECS** → **Clusters** → **helloapi-cluster**
2. Click on **helloapi-service**
3. Go to **Deployments** tab
4. Watch the deployment roll out

---

## 🔍 Workflow Breakdown

### Triggers

```yaml
on:
  push:
    branches:
      - main           # Auto-deploy on push to main
  workflow_dispatch:   # Manual trigger button
```

### Steps

1. **Checkout**: Gets your code from GitHub
2. **Configure AWS**: Authenticates with AWS using secrets
3. **Login to ECR**: Gets credentials for Docker registry
4. **Build & Push**: Builds image for AMD64 and pushes to ECR
5. **Update Task Definition**: Updates with new image ID
6. **Deploy**: Deploys to ECS and waits for stability

---

## 🛡️ Security Best Practices

### ✅ Do's:

- ✅ Use GitHub Secrets for AWS credentials
- ✅ Limit IAM permissions to minimum required
- ✅ Use specific IAM user for GitHub Actions
- ✅ Rotate access keys regularly
- ✅ Enable branch protection on `main`

### ❌ Don'ts:

- ❌ Never commit AWS credentials to git
- ❌ Don't use root AWS account credentials
- ❌ Don't give `*` permissions unless necessary
- ❌ Don't disable branch protection

---

## 🔧 Customization Options

### Deploy to Staging First

```yaml
on:
  push:
    branches:
      - main        # Production
      - develop     # Staging
```

### Add Tests Before Deploy

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: python manage.py test

  deploy:
    needs: test  # Only deploy if tests pass
    runs-on: ubuntu-latest
    # ... rest of deploy job
```

### Add Slack Notifications

```yaml
- name: Notify Slack
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Deploy Multiple Environments

```yaml
strategy:
  matrix:
    environment: [staging, production]
env:
  ECS_SERVICE: helloapi-service-${{ matrix.environment }}
```

---

## 🐛 Troubleshooting

### Error: "No basic auth credentials"

**Cause:** ECR login failed

**Solution:**
```bash
# Check IAM permissions
aws iam get-user-policy --user-name github-actions-helloapi --policy-name ECR-Access
```

### Error: "AccessDeniedException"

**Cause:** Missing IAM permissions

**Solution:** Add required permission to IAM policy

### Error: "Task definition does not exist"

**Cause:** Task definition file path wrong

**Solution:** Check `ECS_TASK_DEFINITION` path in workflow

### Deployment Takes Too Long

**Cause:** ECS service stability check timeout

**Solution:** 
```yaml
# Reduce wait time
wait-for-service-stability: false
```

Or increase timeout:
```yaml
timeout-minutes: 30
```

---

## 📈 Advanced Features

### 1. Blue/Green Deployment

```yaml
- name: Deploy with Blue/Green
  run: |
    aws ecs create-deployment \
      --cluster ${{ env.ECS_CLUSTER }} \
      --service ${{ env.ECS_SERVICE }} \
      --deployment-configuration "deploymentCircuitBreaker={enable=true,rollback=true}"
```

### 2. Automated Rollback

```yaml
- name: Check deployment health
  if: always()
  run: |
    # Check if deployment succeeded
    STATUS=$(aws ecs describe-services --cluster ${{ env.ECS_CLUSTER }} --services ${{ env.ECS_SERVICE }} --query 'services[0].deployments[0].rolloutState' --output text)
    if [ "$STATUS" != "COMPLETED" ]; then
      echo "Deployment failed, rolling back..."
      # Trigger rollback
      exit 1
    fi
```

### 3. Database Migrations

```yaml
- name: Run migrations
  run: |
    TASK_ARN=$(aws ecs run-task \
      --cluster ${{ env.ECS_CLUSTER }} \
      --task-definition ${{ env.ECS_TASK_DEFINITION }} \
      --overrides '{"containerOverrides":[{"name":"helloapi","command":["python","manage.py","migrate"]}]}' \
      --query 'tasks[0].taskArn' --output text)
    
    # Wait for migration task to complete
    aws ecs wait tasks-stopped --cluster ${{ env.ECS_CLUSTER }} --tasks $TASK_ARN
```

---

## 📝 Workflow Status Badge

Add this to your README.md:

```markdown
![Deploy Status](https://github.com/YOUR_USERNAME/helloApi/actions/workflows/deploy.yml/badge.svg)
```

Replace `YOUR_USERNAME` with your GitHub username.

---

## 🎯 Next Steps

1. ✅ Set up branch protection rules
2. ✅ Add automated tests
3. ✅ Configure deployment notifications
4. ✅ Set up staging environment
5. ✅ Enable deployment approvals for production

---

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS ECS Deploy Action](https://github.com/aws-actions/amazon-ecs-deploy-task-definition)
- [ECR Login Action](https://github.com/aws-actions/amazon-ecr-login)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)

---

## 🎉 Success Checklist

After setup, verify:

- [ ] GitHub Secrets are configured
- [ ] IAM user has correct permissions
- [ ] Workflow file is committed to repository
- [ ] First deployment completes successfully
- [ ] API responds at https://api.helloydz.com
- [ ] ECS service shows healthy tasks

---

**Your CI/CD pipeline is ready! Every push to main will now automatically deploy to production.** 🚀

