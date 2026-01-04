# CI/CD Quick Reference

## 🚀 Quick Setup (5 Minutes)

### 1. Create IAM User
```bash
aws iam create-user --user-name github-actions-helloapi

aws iam create-policy \
    --policy-name GitHubActionsECSDeployPolicy \
    --policy-document file://github-actions-policy.json

aws iam attach-user-policy \
    --user-name github-actions-helloapi \
    --policy-arn arn:aws:iam::835745295392:policy/GitHubActionsECSDeployPolicy

aws iam create-access-key --user-name github-actions-helloapi
```

### 2. Add GitHub Secrets
Go to: **GitHub Repo → Settings → Secrets → Actions → New secret**

- `AWS_ACCESS_KEY_ID`: From step 1
- `AWS_SECRET_ACCESS_KEY`: From step 1

### 3. Push to GitHub
```bash
git add .github/workflows/deploy.yml
git commit -m "Add CI/CD pipeline"
git push origin main
```

---

## 📊 Monitor Deployment

### GitHub
```
https://github.com/YOUR_USERNAME/helloApi/actions
```

### AWS Console
```
https://console.aws.amazon.com/ecs/v2/clusters/helloapi-cluster/services/helloapi-service
```

### API Status
```bash
curl https://api.helloydz.com/api/users/
```

---

## 🔧 Common Commands

### Manual Trigger
```bash
# Using GitHub CLI
gh workflow run deploy.yml

# Or via GitHub UI: Actions → Deploy to AWS ECS → Run workflow
```

### Check Workflow Status
```bash
gh run list --workflow=deploy.yml
gh run view <RUN_ID> --log
```

### Rollback
```bash
# Via AWS CLI
aws ecs update-service \
    --cluster helloapi-cluster \
    --service helloapi-service \
    --task-definition helloapi-task:PREVIOUS_REVISION \
    --force-new-deployment \
    --region us-east-1
```

---

## 🐛 Troubleshooting

### Check Workflow Logs
1. GitHub → Actions → Click failed workflow
2. Click on failed job
3. Expand step to see error

### Check ECS Deployment
```bash
aws ecs describe-services \
    --cluster helloapi-cluster \
    --services helloapi-service \
    --region us-east-1
```

### Check Task Logs
```bash
aws logs tail /ecs/helloapi --follow --region us-east-1
```

---

## 📝 Workflow File Location
```
.github/workflows/deploy.yml
```

## 🔐 Required Secrets
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

## 🎯 Deployment Trigger
- Push to `main` branch
- Manual via GitHub Actions UI

---

## ✅ Success Checklist
- [ ] IAM user created with correct permissions
- [ ] GitHub secrets configured
- [ ] Workflow file in repository
- [ ] First deployment successful
- [ ] API responding correctly

---

**Need help?** Check `CICD_SETUP_GUIDE.md` for detailed instructions.

