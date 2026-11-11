#!/bin/bash

# Wedding Application - AWS Cost Calculator
# Estimates monthly costs for the deployment

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AWS Cost Calculator${NC}"
echo -e "${BLUE}Wedding Application Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Default values
BACKEND_TASKS=1
FRONTEND_TASKS=1
CPU_SIZE=0.25
MEMORY_SIZE=0.5
HOURS_PER_MONTH=730
REGION="us-east-1"

# Pricing (approximate, as of 2025)
# ECS Fargate pricing (per vCPU-hour and per GB-hour)
FARGATE_CPU_PRICE=0.04048  # per vCPU-hour
FARGATE_MEMORY_PRICE=0.004445  # per GB-hour

# RDS pricing
RDS_T4G_MICRO_HOURLY=0.018  # db.t4g.micro

# ALB pricing
ALB_HOURLY=0.0225
ALB_LCU=0.008  # per LCU-hour (assuming 1 LCU for small app)

# Data transfer (very approximate)
DATA_TRANSFER_GB=10
DATA_TRANSFER_PRICE_PER_GB=0.09

# Calculate ECS costs
TOTAL_TASKS=$((BACKEND_TASKS + FRONTEND_TASKS))
ECS_CPU_COST=$(echo "$TOTAL_TASKS * $CPU_SIZE * $FARGATE_CPU_PRICE * $HOURS_PER_MONTH" | bc -l)
ECS_MEMORY_COST=$(echo "$TOTAL_TASKS * $MEMORY_SIZE * $FARGATE_MEMORY_PRICE * $HOURS_PER_MONTH" | bc -l)
ECS_TOTAL=$(echo "$ECS_CPU_COST + $ECS_MEMORY_COST" | bc -l)

# Calculate RDS costs
RDS_TOTAL=$(echo "$RDS_T4G_MICRO_HOURLY * $HOURS_PER_MONTH" | bc -l)

# Calculate ALB costs
ALB_TOTAL=$(echo "($ALB_HOURLY + $ALB_LCU) * $HOURS_PER_MONTH" | bc -l)

# Calculate data transfer
DATA_TRANSFER_TOTAL=$(echo "$DATA_TRANSFER_GB * $DATA_TRANSFER_PRICE_PER_GB" | bc -l)

# Calculate total
TOTAL=$(echo "$ECS_TOTAL + $RDS_TOTAL + $ALB_TOTAL + $DATA_TRANSFER_TOTAL" | bc -l)

# Display breakdown
echo -e "${YELLOW}Configuration:${NC}"
echo "  Backend tasks: $BACKEND_TASKS (${CPU_SIZE} vCPU, ${MEMORY_SIZE} GB)"
echo "  Frontend tasks: $FRONTEND_TASKS (${CPU_SIZE} vCPU, ${MEMORY_SIZE} GB)"
echo "  RDS instance: db.t4g.micro (single AZ)"
echo "  Region: $REGION"
echo ""

echo -e "${YELLOW}Monthly Cost Breakdown:${NC}"
printf "  %-30s \$%6.2f\n" "ECS Fargate (CPU)" "$ECS_CPU_COST"
printf "  %-30s \$%6.2f\n" "ECS Fargate (Memory)" "$ECS_MEMORY_COST"
printf "  %-30s ${GREEN}\$%6.2f${NC}\n" "ECS Fargate Total" "$ECS_TOTAL"
echo ""
printf "  %-30s ${GREEN}\$%6.2f${NC}\n" "RDS PostgreSQL (db.t4g.micro)" "$RDS_TOTAL"
echo ""
printf "  %-30s \$%6.2f\n" "Application Load Balancer" "$ALB_TOTAL"
echo ""
printf "  %-30s \$%6.2f\n" "Data Transfer (~${DATA_TRANSFER_GB}GB)" "$DATA_TRANSFER_TOTAL"
echo ""
echo -e "${BLUE}========================================${NC}"
printf "${GREEN}Estimated Monthly Total: \$%.2f${NC}\n" "$TOTAL"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}Cost Optimization Tips:${NC}"
echo ""
echo "1. ${GREEN}Scale to zero during off-hours${NC}"
printf "   Savings: \$%.2f/month\n" "$(echo "$ECS_TOTAL * 0.5" | bc -l)"
echo "   Command: ./manage.sh scale all 0"
echo ""

echo "2. ${GREEN}Use spot tasks (requires EC2 launch type)${NC}"
printf "   Savings: \$%.2f/month\n" "$(echo "$ECS_TOTAL * 0.7" | bc -l)"
echo "   Note: Requires CloudFormation template changes"
echo ""

echo "3. ${GREEN}Enable Aurora Serverless v2 auto-pause${NC}"
printf "   Savings: \$%.2f/month (when paused 50%% of time)\n" "$(echo "$RDS_TOTAL * 0.5" | bc -l)"
echo "   Note: Requires template changes"
echo ""

echo "4. ${GREEN}Use CloudFront for caching${NC}"
echo "   Savings: Reduces ALB and data transfer costs"
echo "   Added cost: ~\$1-2/month for CloudFront"
echo ""

echo -e "${YELLOW}Notes:${NC}"
echo "- Prices are approximate and vary by region"
echo "- Actual costs may vary based on usage patterns"
echo "- Data transfer costs depend on traffic volume"
echo "- First year AWS Free Tier may reduce costs"
echo "- Add ~\$0.50/month for CloudWatch Logs retention"
echo ""

# Cost comparison with alternatives
echo -e "${YELLOW}Cost Comparison with Alternatives:${NC}"
echo ""
printf "  %-30s \$%6.2f/month\n" "Current (ECS Fargate + RDS)" "$TOTAL"
printf "  %-30s \$%6.2f/month\n" "AWS Lightsail (2GB)" "10.00"
printf "  %-30s \$%6.2f/month\n" "AWS Lightsail (4GB)" "20.00"
printf "  %-30s \$%6.2f/month\n" "DigitalOcean Droplet (2GB)" "12.00"
printf "  %-30s \$%6.2f/month\n" "Heroku (Hobby tier)" "7.00"
printf "  %-30s \$%6.2f/month\n" "Heroku (Standard)" "25.00"
echo ""

echo -e "${BLUE}Note: This calculator provides estimates only.${NC}"
echo -e "${BLUE}Use AWS Cost Explorer for actual costs.${NC}"
