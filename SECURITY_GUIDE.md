# Security Guide - HelloAPI AWS Deployment

## 🔒 Security Overview

This guide covers security best practices for your Django API deployed on AWS ECS.

---

## 📊 Current Security Status

### ✅ What's Already Secured:

1. **RDS Database**
   - ✅ Not publicly accessible
   - ✅ In private subnet with security group
   - ✅ Credentials stored in AWS Secrets Manager
   - ✅ Encryption at rest enabled

2. **ECS Tasks**
   - ✅ Running in Fargate (isolated compute)
   - ✅ IAM roles with least privilege
   - ✅ Secrets pulled from Secrets Manager
   - ✅ Container security groups configured

3. **Application**
   - ✅ Django security middleware enabled
   - ✅ CORS configured
   - ✅ SQL injection protection (Django ORM)
   - ✅ XSS protection headers

### ⚠️ Current Security Gaps:

1. **No HTTPS/SSL Certificate** - API runs on HTTP only
2. **ALB has public access** - No WAF or rate limiting
3. **No domain name** - Using raw AWS DNS
4. **Cookie security disabled** - Due to no HTTPS
5. **No authentication** - API is publicly accessible

---

## 🎯 Priority Security Improvements

### Priority 1: Enable HTTPS (Critical)

#### **Step 1: Get a Domain Name**

You need a domain to get an SSL certificate. Options:
- Buy from Route 53: ~$12/year for .com
- Buy from Namecheap, GoDaddy, etc.
- Use existing domain

#### **Step 2: Request SSL Certificate from ACM**

```bash
# Request certificate (use your domain)
aws acm request-certificate \
    --domain-name api.yourdomain.com \
    --validation-method DNS \
    --region us-east-1
```

#### **Step 3: Validate Certificate**

1. Go to AWS Console → Certificate Manager
2. Click on your certificate
3. Create CNAME records in your DNS provider
4. Wait for validation (~5-30 minutes)

#### **Step 4: Add HTTPS Listener to ALB**

```bash
# Get your ALB ARN
ALB_ARN=$(aws elbv2 describe-load-balancers \
    --names helloapi-alb \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text \
    --region us-east-1)

# Get certificate ARN (after validation)
CERT_ARN=$(aws acm list-certificates \
    --query 'CertificateSummaryList[0].CertificateArn' \
    --output text \
    --region us-east-1)

# Add HTTPS listener
aws elbv2 create-listener \
    --load-balancer-arn $ALB_ARN \
    --protocol HTTPS \
    --port 443 \
    --certificates CertificateArn=$CERT_ARN \
    --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-east-1:835745295392:targetgroup/helloapi-tg/cc76b43576030698 \
    --region us-east-1
```

#### **Step 5: Redirect HTTP to HTTPS**

```bash
# Get HTTP listener ARN
HTTP_LISTENER_ARN=$(aws elbv2 describe-listeners \
    --load-balancer-arn $ALB_ARN \
    --query 'Listeners[?Port==`80`].ListenerArn' \
    --output text \
    --region us-east-1)

# Modify to redirect
aws elbv2 modify-listener \
    --listener-arn $HTTP_LISTENER_ARN \
    --default-actions Type=redirect,RedirectConfig="{Protocol=HTTPS,Port=443,StatusCode=HTTP_301}" \
    --region us-east-1
```

#### **Step 6: Update Django Settings**

In `ecs-task-definition.json`, change:
```json
{
  "name": "SECURE_SSL_REDIRECT",
  "value": "True"
}
```

Then redeploy.

---

### Priority 2: Add API Authentication

#### **Option 1: Token Authentication (Simple)**

1. **Install Django REST Framework Token Auth:**

Add to `requirements.txt`:
```
djangorestframework-simplejwt==5.3.1
```

2. **Update settings.py:**

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

3. **Add token endpoints to urls.py:**

```python
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),
    # ... existing urls
]
```

4. **Usage:**

```bash
# Get token
curl -X POST https://api.yourdomain.com/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'

# Use token
curl https://api.yourdomain.com/api/users/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### **Option 2: API Key Authentication (For External Clients)**

Create a custom middleware for API keys stored in Secrets Manager.

---

### Priority 3: Add Rate Limiting

#### **Option 1: Django Ratelimit (Application Level)**

```bash
pip install django-ratelimit
```

In `users/views.py`:
```python
from django_ratelimit.decorators import ratelimit

class UserViewSet(viewsets.ModelViewSet):
    @ratelimit(key='ip', rate='100/h', method='GET')
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
```

#### **Option 2: AWS WAF (Infrastructure Level)**

```bash
# Create WAF rate limit rule
aws wafv2 create-web-acl \
    --name helloapi-waf \
    --scope REGIONAL \
    --default-action Allow={} \
    --rules file://waf-rules.json \
    --region us-east-1

# Associate with ALB
aws wafv2 associate-web-acl \
    --web-acl-arn YOUR_WAF_ARN \
    --resource-arn $ALB_ARN \
    --region us-east-1
```

---

### Priority 4: Database Security

#### **Enable RDS Encryption**

If not already enabled:
```bash
# Create encrypted snapshot
aws rds create-db-snapshot \
    --db-instance-identifier helloapi-db \
    --db-snapshot-identifier helloapi-snapshot \
    --region us-east-1

# Copy with encryption
aws rds copy-db-snapshot \
    --source-db-snapshot-identifier helloapi-snapshot \
    --target-db-snapshot-identifier helloapi-encrypted \
    --kms-key-id alias/aws/rds \
    --region us-east-1

# Restore from encrypted snapshot
# ... (downtime required)
```

#### **Enable Automated Backups**

Already configured with `--backup-retention-period 7`

#### **Enable Performance Insights**

```bash
aws rds modify-db-instance \
    --db-instance-identifier helloapi-db \
    --enable-performance-insights \
    --performance-insights-retention-period 7 \
    --region us-east-1
```

---

### Priority 5: Network Security

#### **Enable VPC Flow Logs**

```bash
# Create CloudWatch log group
aws logs create-log-group \
    --log-group-name /aws/vpc/helloapi \
    --region us-east-1

# Create IAM role for flow logs
# ... (role creation)

# Enable flow logs
aws ec2 create-flow-logs \
    --resource-type VPC \
    --resource-ids YOUR_VPC_ID \
    --traffic-type ALL \
    --log-destination-type cloud-watch-logs \
    --log-group-name /aws/vpc/helloapi \
    --region us-east-1
```

#### **Review Security Group Rules**

Current security groups:
- **ALB SG**: Allow 80, 443 from 0.0.0.0/0
- **ECS SG**: Allow 8000 from ALB SG only
- **RDS SG**: Allow 5432 from ECS SG only

**Recommendation:** This is already well-configured! ✅

---

## 🔐 Secrets Management

### Current Setup: ✅

- Database credentials in Secrets Manager
- Django SECRET_KEY in Secrets Manager
- IAM role for ECS to access secrets

### Improvements:

#### **Rotate Secrets Automatically**

```bash
# Enable rotation for DB password
aws secretsmanager rotate-secret \
    --secret-id helloapi/db/PASSWORD \
    --rotation-lambda-arn YOUR_LAMBDA_ARN \
    --rotation-rules AutomaticallyAfterDays=90 \
    --region us-east-1
```

#### **Use Secrets for More Settings**

Move these to Secrets Manager:
- CORS_ALLOWED_ORIGINS
- ALLOWED_HOSTS
- Third-party API keys

---

## 📝 Security Checklist

### Before Production:

- [ ] HTTPS/SSL certificate configured
- [ ] HTTP redirects to HTTPS
- [ ] Authentication enabled
- [ ] Rate limiting configured
- [ ] CORS properly restricted (not `*`)
- [ ] `DEBUG = False` in production
- [ ] Strong `SECRET_KEY` (not default)
- [ ] Database not publicly accessible
- [ ] RDS encrypted at rest
- [ ] Automated backups enabled
- [ ] CloudWatch logs enabled
- [ ] Security groups follow least privilege
- [ ] IAM roles follow least privilege
- [ ] Secrets in Secrets Manager (not environment variables)

### Nice to Have:

- [ ] AWS WAF enabled
- [ ] CloudFront CDN in front of ALB
- [ ] Multi-AZ deployment for RDS
- [ ] Auto-scaling configured
- [ ] Monitoring and alerting setup
- [ ] Penetration testing performed
- [ ] Security audit completed

---

## 🚨 Common Security Mistakes to Avoid

1. **❌ Never commit secrets to Git**
   - Use Secrets Manager or environment variables
   - Check `.gitignore` includes sensitive files

2. **❌ Never use `ALLOWED_HOSTS = ['*']`**
   - Specify exact domains

3. **❌ Never disable CSRF protection**
   - Keep `CSRF_COOKIE_SECURE = True` in production

4. **❌ Never expose database publicly**
   - Always use private subnets

5. **❌ Never use default passwords**
   - Change RDS master password
   - Rotate regularly

6. **❌ Never disable security middleware**
   - Keep all Django security settings enabled

7. **❌ Never log sensitive data**
   - Sanitize logs before sending to CloudWatch

---

## 📊 Security Monitoring

### Enable AWS Security Hub

```bash
aws securityhub enable-security-hub --region us-east-1
```

### Enable GuardDuty

```bash
aws guardduty create-detector \
    --enable \
    --region us-east-1
```

### Enable CloudTrail

```bash
aws cloudtrail create-trail \
    --name helloapi-trail \
    --s3-bucket-name your-cloudtrail-bucket \
    --region us-east-1

aws cloudtrail start-logging \
    --name helloapi-trail \
    --region us-east-1
```

### CloudWatch Alarms

```bash
# Alert on failed login attempts
aws cloudwatch put-metric-alarm \
    --alarm-name helloapi-failed-logins \
    --alarm-description "Alert on failed login attempts" \
    --metric-name FailedLoginCount \
    --namespace CustomMetrics \
    --statistic Sum \
    --period 300 \
    --evaluation-periods 1 \
    --threshold 10 \
    --comparison-operator GreaterThanThreshold \
    --region us-east-1
```

---

## 🔍 Security Testing

### Test HTTPS

```bash
# Check SSL certificate
openssl s_client -connect api.yourdomain.com:443 -servername api.yourdomain.com

# Test SSL rating
curl https://www.ssllabs.com/ssltest/analyze.html?d=api.yourdomain.com
```

### Test Security Headers

```bash
curl -I https://api.yourdomain.com/api/users/

# Should see:
# - Strict-Transport-Security
# - X-Content-Type-Options: nosniff
# - X-Frame-Options: DENY
# - Referrer-Policy
# - Cross-Origin-Opener-Policy
```

### Test Authentication

```bash
# Should fail without token
curl https://api.yourdomain.com/api/users/
# Response: 401 Unauthorized

# Should succeed with token
curl https://api.yourdomain.com/api/users/ \
  -H "Authorization: Bearer YOUR_TOKEN"
# Response: 200 OK
```

### Penetration Testing Tools

- **OWASP ZAP**: Web application security scanner
- **Burp Suite**: Security testing tool
- **nmap**: Network scanner
- **sqlmap**: SQL injection tester

---

## 💰 Security Cost Estimate

| Service | Monthly Cost | Notes |
|---------|-------------|-------|
| ACM Certificate | **FREE** | SSL/TLS certificates |
| AWS WAF | ~$10-30 | Based on rules and requests |
| GuardDuty | ~$5-20 | Based on log volume |
| Security Hub | ~$5-15 | Based on checks |
| CloudTrail | ~$2-10 | First trail free, S3 storage |
| Secrets Manager | ~$1-5 | $0.40/secret/month + API calls |
| **Total** | **~$23-80/month** | For full security stack |

---

## 📚 Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security Docs](https://docs.djangoproject.com/en/stable/topics/security/)
- [AWS Security Best Practices](https://aws.amazon.com/architecture/security-identity-compliance/)
- [CIS AWS Benchmarks](https://www.cisecurity.org/benchmark/amazon_web_services)

---

## 🎯 Recommended Next Steps

1. **Immediate (This Week):**
   - Get domain name
   - Request SSL certificate
   - Enable HTTPS on ALB

2. **Short Term (This Month):**
   - Implement authentication
   - Add rate limiting
   - Enable CloudWatch alarms

3. **Long Term (Next Quarter):**
   - Enable AWS WAF
   - Set up Security Hub
   - Perform security audit
   - Implement automated secret rotation

---

**Security is an ongoing process, not a one-time task. Review and update regularly!** 🔒

