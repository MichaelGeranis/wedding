# Quick Start Guide

Deploy your wedding application to AWS in 5 steps.

## Prerequisites

- AWS Account
- AWS CLI configured
- Docker installed
- Docker Hub account
- A domain you control (for the HTTPS certificate)

## Deployment Steps

### 1. Generate Secrets

```bash
cd backend
uv run python scripts/generate_secrets.py
```

Save the JWT_SECRET_KEY and ADMIN_PASSWORD_HASH outputs.

### 2. Get an HTTPS Certificate

Request an ACM certificate for your domain, in the region you deploy to, and validate it by DNS
(see DEPLOYMENT.md, Step 2). The stack will not deploy without one.

### 3. Configure Parameters

```bash
cd ../infrastructure
cp parameters.json.example parameters.json
nano parameters.json
```

Fill in:
- DBPassword (your secure password)
- JWTSecretKey (from step 1)
- AdminPasswordHash (from step 1)
- BackendImage (your-dockerhub-username/wedding-backend:latest)
- FrontendImage (your-dockerhub-username/wedding-frontend:latest)
- DomainName (e.g. wedding.yourdomain.com)
- CertificateArn (from step 2)

### 4. Deploy

```bash
./deploy.sh all
```

This takes 15-20 minutes. It will:
- Build and push Docker images
- Create AWS infrastructure
- Deploy your application

### 5. Run Migrations

```bash
./manage.sh migrations
```

## Done!

Get your application URL:

```bash
./manage.sh outputs
```

Visit the URL to see your wedding application!

## What's Next?

- Test the application
- Point your domain at the load balancer (`LoadBalancerURL` output)
- After the wedding: *Delete all guest data* in the admin panel, then `./manage.sh delete`
- Configure monitoring
- Review cost optimization tips

See DEPLOYMENT.md for detailed documentation.

## Common Commands

```bash
# View logs
./manage.sh logs backend

# Restart services
./manage.sh restart all

# Check status
./manage.sh status

# Stop services (save money)
./manage.sh scale all 0

# Start services
./manage.sh scale all 1
```

## Estimated Cost

~$45/month (see cost breakdown with `./cost-calculator.sh`)

## Need Help?

See DEPLOYMENT.md for troubleshooting and advanced topics.
