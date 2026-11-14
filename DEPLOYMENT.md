# Wedding Application - AWS Deployment Guide

Complete guide for deploying the Wedding Application to AWS using CloudFormation, ECS Fargate, and RDS PostgreSQL.

## Cost Estimate: ~$45/month

- **RDS PostgreSQL** (db.t4g.micro, single AZ): ~$13/month
- **ECS Fargate** (2 tasks @ 0.25 vCPU, 512 MB): ~$10/month
- **Application Load Balancer**: ~$16/month
- **Data Transfer & Other**: ~$5/month

## Prerequisites

### 1. AWS Account Setup

```bash
# Install AWS CLI
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS credentials
aws configure
# Enter your Access Key ID, Secret Access Key, default region (us-east-1), and output format (json)
```

### 2. Docker Setup

```bash
# Install Docker Desktop (macOS/Windows)
# Or install Docker Engine (Linux)

# Verify installation
docker --version

# Login to Docker Hub
docker login
```

### 3. Required Tools

```bash
# Install jq (for JSON processing)
# macOS
brew install jq

# Linux
sudo apt-get install jq
```

## Step-by-Step Deployment

### Step 1: Generate Secrets

```bash
cd backend

# Run the secrets generation script
uv run python scripts/generate_secrets.py

# You'll be prompted to enter an admin password
# The script will output:
# - JWT_SECRET_KEY (64-character hex string)
# - ADMIN_PASSWORD_HASH (bcrypt hash)

# SAVE THESE VALUES - you'll need them in the next step
```

### Step 2: Get an HTTPS Certificate

The stack refuses to deploy without one: guests' names, phone numbers and dietary needs, and the admin password,
must not cross the internet unencrypted. You need a domain you control.

```bash
# Use the region you deploy the stack to (deploy.sh's REGION), not us-east-1 unless that is it
aws acm request-certificate \
  --domain-name wedding.yourdomain.com \
  --validation-method DNS \
  --region YOUR_STACK_REGION
```

Add the CNAME record ACM shows to your domain's DNS, wait until the certificate's status is `ISSUED`, and note its
ARN for the next step. After deploying, point the domain at the load balancer (see [HTTPS and your
domain](#https-and-your-domain)).

For a throwaway test stack with no real guests you may instead set `AllowPlainHttp` to `true` and leave
`CertificateArn` and `DomainName` empty.

### Step 3: Create Parameters File

```bash
cd ../infrastructure

# Copy the example parameters file
cp parameters.json.example parameters.json

# Edit parameters.json with your values
nano parameters.json
```

Update the following values in `parameters.json`:

```json
[
  {
    "ParameterKey": "Environment",
    "ParameterValue": "production"
  },
  {
    "ParameterKey": "DBUsername",
    "ParameterValue": "wedding"
  },
  {
    "ParameterKey": "DBPassword",
    "ParameterValue": "YOUR_SECURE_DB_PASSWORD_HERE"
  },
  {
    "ParameterKey": "JWTSecretKey",
    "ParameterValue": "PASTE_JWT_SECRET_FROM_STEP_1"
  },
  {
    "ParameterKey": "AdminPasswordHash",
    "ParameterValue": "PASTE_ADMIN_HASH_FROM_STEP_1"
  },
  {
    "ParameterKey": "BackendImage",
    "ParameterValue": "your-dockerhub-username/wedding-backend:latest"
  },
  {
    "ParameterKey": "FrontendImage",
    "ParameterValue": "your-dockerhub-username/wedding-frontend:latest"
  },
  {
    "ParameterKey": "DomainName",
    "ParameterValue": "wedding.yourdomain.com"
  },
  {
    "ParameterKey": "CertificateArn",
    "ParameterValue": "arn:aws:acm:REGION:ACCOUNT_ID:certificate/CERTIFICATE_ID"
  }
]
```

**IMPORTANT**: Replace `your-dockerhub-username` with your actual Docker Hub username.

`DBPassword` may not contain quotes, backslashes, `@`, `/` or spaces, and `AdminPasswordHash` must be the bcrypt
hash from step 1: the stack rejects anything else. Secrets go into one AWS Secrets Manager secret (`STACK/app`), not
into the ECS task definition.

### Step 4: Deploy Using Helper Script

The easiest way to deploy is using the provided deployment script:

```bash
cd infrastructure

# Deploy everything (build images + deploy stack)
./deploy.sh all
```

This will:
1. Build Docker images for backend and frontend
2. Push images to Docker Hub
3. Validate the CloudFormation template
4. Create/update the CloudFormation stack
5. Wait for deployment to complete (~15-20 minutes)
6. Display the application URL

### Step 5: Run Database Migrations

After the stack is deployed, you need to initialize the database:

```bash
# Run migrations
./manage.sh migrations
```

This will connect to a running backend container and execute `alembic upgrade head`.

### Step 6: Verify Deployment

```bash
# Check service status
./manage.sh status

# View logs
./manage.sh logs backend
./manage.sh logs frontend

# Get application URL
./manage.sh outputs
```

Visit the application URL shown in the outputs to verify it's working.

## Manual Deployment (Alternative)

If you prefer to deploy manually:

### Build and Push Images

```bash
# Build backend
cd backend
docker build -t your-dockerhub-username/wedding-backend:latest .
docker push your-dockerhub-username/wedding-backend:latest

# Build frontend
cd ../frontend
docker build -t your-dockerhub-username/wedding-frontend:latest .
docker push your-dockerhub-username/wedding-frontend:latest
```

### Deploy CloudFormation Stack

```bash
cd infrastructure

# Validate template
aws cloudformation validate-template \
  --template-body file://cloudformation-stack.yaml

# Create stack
aws cloudformation create-stack \
  --stack-name wedding-app \
  --template-body file://cloudformation-stack.yaml \
  --parameters file://parameters.json \
  --capabilities CAPABILITY_IAM \
  --region us-east-1

# Wait for completion
aws cloudformation wait stack-create-complete \
  --stack-name wedding-app \
  --region us-east-1

# Get outputs
aws cloudformation describe-stacks \
  --stack-name wedding-app \
  --query 'Stacks[0].Outputs' \
  --output table
```

## Management Commands

The `manage.sh` script provides helpful commands for managing your deployment:

```bash
# View service logs
./manage.sh logs backend
./manage.sh logs frontend

# Run database migrations
./manage.sh migrations

# Restart services
./manage.sh restart backend
./manage.sh restart frontend
./manage.sh restart all

# Scale services
./manage.sh scale backend 2    # Scale backend to 2 tasks
./manage.sh scale all 0         # Stop all services (cost savings)

# Service status
./manage.sh status

# List running tasks
./manage.sh tasks

# Execute into container
./manage.sh exec backend

# Database info
./manage.sh db

# Stack outputs
./manage.sh outputs

# Delete stack
./manage.sh delete
```

## Updating the Application

### Update Code

```bash
# 1. Make your code changes
# 2. Build and push new images
./deploy.sh images

# 3. Restart services to use new images
./manage.sh restart all
```

### Update Infrastructure

```bash
# 1. Edit cloudformation-stack.yaml
# 2. Deploy changes
./deploy.sh deploy
```

## Cost Optimization

### Reduce Costs During Low-Traffic Periods

```bash
# Stop services at night (saves ~$10/month)
./manage.sh scale all 0

# Start services in the morning
./manage.sh scale all 1
```

You could automate this with cron or AWS EventBridge.

### Switch to Smaller Instance

The template uses the smallest available instances:
- RDS: db.t4g.micro (ARM-based, cheapest)
- ECS: 0.25 vCPU, 512 MB (smallest Fargate size)

### Enable Aurora Serverless v2 (Advanced)

For very sporadic usage, consider Aurora Serverless v2 which auto-pauses:
- Minimum cost when paused: $0
- Active cost: Similar to db.t4g.micro
- Requires template modification

## Monitoring and Logs

### CloudWatch Logs

```bash
# Tail logs in real-time
./manage.sh logs backend

# Or use AWS CLI directly
aws logs tail /ecs/wedding-app/backend --follow
```

### CloudWatch Metrics

Visit AWS Console → CloudWatch → Metrics to view:
- ECS task CPU/memory usage
- RDS CPU/connections
- ALB request count/latency

### Set Up Alarms (Optional)

Create CloudWatch alarms for:
- High CPU usage (>80%)
- High memory usage (>80%)
- Database connections (>80% of max)
- ALB 5XX errors

## HTTPS and your domain

With `CertificateArn` set, the load balancer serves the site on 443 (TLS 1.2 and 1.3 only) and redirects port 80
to HTTPS. Once the stack is up, create a DNS record for `DomainName` pointing at the load balancer: a Route 53
alias A record, or a CNAME to the `LoadBalancerURL` output's host name at another DNS provider.

## Upgrading a stack created before HTTPS and encryption

Earlier versions of this template stored the database unencrypted. RDS cannot encrypt an existing instance in
place, so updating such a stack **replaces the database with a new, empty, encrypted one**. The template now keeps a
snapshot of the old instance when it is replaced, but that snapshot is not restored into the new one. To keep your
guests' data:

1. Export everything from the admin panel (all RSVPs CSV, and the invitation list CSV).
2. Update the stack with the new parameters (`CertificateArn`, `DomainName`).
3. Run the migrations, then import the invitation list CSV again. Guests who already answered need to RSVP again,
   or you restore the old snapshot into a temporary instance and copy the `rsvps` table across.
4. Delete the old instance's snapshot once you no longer need it: it still holds the unencrypted data.

The database also moves from PostgreSQL 16.3, which RDS no longer offers for new instances, to 18, the version
the Docker setup uses.

## Guest data and privacy

- **Logs** hold no guest names, phone numbers, emails, dietary needs or messages, and QR code tokens are redacted
  from access logs. CloudWatch keeps logs for 7 days.
- **Admin emails** say only who answered and how many are coming. Details stay in the admin panel.
- **QR codes** stop working after the invitation's RSVP deadline.
- **After the wedding**, use *Delete all guest data* at the bottom of the admin panel, then delete the stack
  (`./manage.sh delete`) and its final database snapshot. The RSVP page tells guests their answers are deleted
  after the wedding, so do it.

## Backup and Restore

### Database Backups

Automated backups are off (`BackupRetentionPeriod: 0`) to stay in the free tier. Take manual snapshots before risky
changes, and delete them after the wedding: they contain guest data.

To create a manual snapshot:

```bash
aws rds create-db-snapshot \
  --db-instance-identifier wedding-app-db \
  --db-snapshot-identifier wedding-manual-snapshot-$(date +%Y%m%d)
```

### Restore from Snapshot

```bash
# List snapshots
aws rds describe-db-snapshots \
  --db-instance-identifier wedding-app-db

# Restore (creates new instance)
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier wedding-app-db-restored \
  --db-snapshot-identifier your-snapshot-id
```

## Troubleshooting

### Tasks Not Starting

```bash
# Check service events
aws ecs describe-services \
  --cluster wedding-app-cluster \
  --services wedding-app-backend \
  --query 'services[0].events[:5]'

# Check task logs
./manage.sh logs backend
```

### Database Connection Issues

```bash
# 1. Get database endpoint
./manage.sh db

# 2. Verify security group allows ECS tasks to connect
# 3. Check DATABASE_URL environment variable in task definition
# 4. Test connection from ECS task
./manage.sh exec backend
psql -h DB_ENDPOINT -U wedding -d wedding
```

### High Costs

```bash
# Check current costs
aws ce get-cost-and-usage \
  --time-period Start=2025-12-01,End=2025-12-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE

# Main cost drivers:
# - ALB (~$16/month, required)
# - RDS (~$13/month, can't go lower)
# - ECS Fargate (~$5/task/month)
# - Data transfer (variable)
```

### Application Not Accessible

```bash
# 1. Check ALB health checks
aws elbv2 describe-target-health \
  --target-group-arn TARGET_GROUP_ARN

# 2. Check security groups
# Ensure ALB security group allows 80/443 from 0.0.0.0/0
# Ensure ECS security group allows traffic from ALB security group

# 3. Check route table
# Ensure public subnets have route to Internet Gateway
```

## Security Best Practices

1. **HTTPS**: Required by the template (see Step 2)
2. **Rotate Secrets**: Regularly update database password and JWT secret
3. **Enable GuardDuty**: Threat detection (~$1/month)
4. **Enable CloudTrail**: API audit logging
5. **Restrict Database**: Move to private subnet (requires NAT Gateway)
6. **Enable WAF**: Web Application Firewall for ALB (~$5/month)
7. **Encryption at rest**: The database is encrypted (`StorageEncrypted`), and secrets live in Secrets Manager

## Cleanup

To completely remove all resources:

```bash
./manage.sh delete
```

This will:
1. Create a final RDS snapshot
2. Delete all ECS services and tasks
3. Delete the load balancer
4. Delete the database (after snapshot)
5. Delete the VPC and networking
6. Delete CloudWatch log groups

**Note**: The final snapshot is retained. To delete it:

```bash
aws rds delete-db-snapshot --db-snapshot-identifier final-snapshot-id
```

## Support and Resources

- **AWS Documentation**: https://docs.aws.amazon.com/
- **CloudFormation Reference**: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/
- **ECS Best Practices**: https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/
- **RDS Best Practices**: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/

## Next Steps

1. ✅ Deploy the application
2. ✅ Run database migrations
3. ✅ Test all endpoints
4. Point your domain at the load balancer
5. Configure monitoring and alarms
7. Set up CI/CD pipeline (GitHub Actions, etc.)
7. Enable backups and disaster recovery plan
