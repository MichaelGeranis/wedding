#!/bin/bash

# Wedding Application - AWS Deployment Script
# This script helps deploy the application to AWS using CloudFormation and ECR

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME=${STACK_NAME:-"wedding-app"}
REGION=${AWS_REGION:-"us-east-1"}
PARAMETERS_FILE="parameters.json"

# Get AWS Account ID
get_account_id() {
    aws sts get-caller-identity --query Account --output text
}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Wedding Application - AWS Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI is not installed${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker is not installed${NC}"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo -e "${RED}ERROR: jq is not installed${NC}"
    exit 1
fi

if [ ! -f "$PARAMETERS_FILE" ]; then
    echo -e "${RED}ERROR: $PARAMETERS_FILE not found${NC}"
    echo "Please create parameters.json with your configuration"
    exit 1
fi

# Verify AWS credentials
echo -e "${YELLOW}Verifying AWS credentials...${NC}"
AWS_ACCOUNT_ID=$(get_account_id)
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}ERROR: Could not get AWS Account ID. Check your AWS credentials.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AWS Account ID: $AWS_ACCOUNT_ID${NC}"
echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# ECR repository names
BACKEND_REPO="${STACK_NAME}-backend"
FRONTEND_REPO="${STACK_NAME}-frontend"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

# Function to create ECR repository if it doesn't exist
create_ecr_repo() {
    local repo_name=$1
    echo -e "${YELLOW}Checking ECR repository: $repo_name${NC}"

    if aws ecr describe-repositories --repository-names "$repo_name" --region "$REGION" &> /dev/null; then
        echo -e "${GREEN}✓ Repository $repo_name already exists${NC}"
    else
        echo "Creating ECR repository: $repo_name"
        aws ecr create-repository \
            --repository-name "$repo_name" \
            --region "$REGION" \
            --image-scanning-configuration scanOnPush=false \
            --tags Key=Project,Value=wedding-app > /dev/null
        echo -e "${GREEN}✓ Repository $repo_name created${NC}"
    fi
}

# Function to login to ECR
ecr_login() {
    echo -e "${YELLOW}Logging into ECR...${NC}"
    aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"
    echo -e "${GREEN}✓ ECR login successful${NC}"
    echo ""
}

# Function to build and push Docker images to ECR
build_and_push_images() {
    echo -e "${YELLOW}Building and pushing Docker images to ECR...${NC}"

    BACKEND_IMAGE="${ECR_REGISTRY}/${BACKEND_REPO}:latest"
    FRONTEND_IMAGE="${ECR_REGISTRY}/${FRONTEND_REPO}:latest"

    echo "Backend image: $BACKEND_IMAGE"
    echo "Frontend image: $FRONTEND_IMAGE"
    echo ""

    # Use relative /api path since ALB routes /api/* to backend
    # This works because the frontend and API are served from the same ALB
    API_URL="/api"
    echo "Using API URL for frontend build: $API_URL (relative path for ALB routing)"
    echo ""

    # Build backend (for linux/amd64 - required by AWS Fargate)
    echo -e "${YELLOW}Building backend...${NC}"
    cd ../backend
    docker build --platform linux/amd64 -t "$BACKEND_IMAGE" .
    docker push "$BACKEND_IMAGE"
    echo -e "${GREEN}✓ Backend image pushed to ECR${NC}"
    echo ""

    # Build frontend with API URL build arg (for linux/amd64 - required by AWS Fargate)
    echo -e "${YELLOW}Building frontend...${NC}"
    cd ../frontend
    docker build \
        --platform linux/amd64 \
        --build-arg VITE_API_BASE_URL="${API_URL}" \
        -t "$FRONTEND_IMAGE" .
    docker push "$FRONTEND_IMAGE"
    echo -e "${GREEN}✓ Frontend image pushed to ECR${NC}"

    cd ../infrastructure
    echo ""
}

# Function to validate CloudFormation template
validate_template() {
    echo -e "${YELLOW}Validating CloudFormation template...${NC}"
    aws cloudformation validate-template \
        --template-body file://cloudformation-stack.yaml \
        --region "$REGION" > /dev/null
    echo -e "${GREEN}✓ Template is valid${NC}"
    echo ""
}

# Function to deploy stack
deploy_stack() {
    echo -e "${YELLOW}Deploying CloudFormation stack...${NC}"

    # Check if stack exists
    if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &> /dev/null; then
        echo "Stack exists, updating..."

        # Try to update, but handle "no updates" gracefully
        set +e
        UPDATE_OUTPUT=$(aws cloudformation update-stack \
            --stack-name "$STACK_NAME" \
            --template-body file://cloudformation-stack.yaml \
            --parameters file://$PARAMETERS_FILE \
            --capabilities CAPABILITY_IAM \
            --region "$REGION" 2>&1)
        UPDATE_RESULT=$?
        set -e

        if [ $UPDATE_RESULT -ne 0 ]; then
            if echo "$UPDATE_OUTPUT" | grep -q "No updates are to be performed"; then
                echo -e "${GREEN}✓ No stack updates needed${NC}"
            else
                echo -e "${RED}ERROR: $UPDATE_OUTPUT${NC}"
                exit 1
            fi
        else
            echo "Waiting for stack update to complete..."
            aws cloudformation wait stack-update-complete \
                --stack-name "$STACK_NAME" \
                --region "$REGION"
            echo -e "${GREEN}✓ Stack update complete${NC}"
        fi
    else
        echo "Creating new stack..."
        aws cloudformation create-stack \
            --stack-name "$STACK_NAME" \
            --template-body file://cloudformation-stack.yaml \
            --parameters file://$PARAMETERS_FILE \
            --capabilities CAPABILITY_IAM \
            --region "$REGION"

        echo "Waiting for stack creation to complete (this may take 15-20 minutes)..."
        aws cloudformation wait stack-create-complete \
            --stack-name "$STACK_NAME" \
            --region "$REGION"
        echo -e "${GREEN}✓ Stack creation complete${NC}"
    fi
    echo ""
}

# Function to force ECS service update (to pull new images)
update_ecs_services() {
    echo -e "${YELLOW}Updating ECS services to use new images...${NC}"

    CLUSTER_NAME="${STACK_NAME}-cluster"

    # Update backend service
    echo "Updating backend service..."
    aws ecs update-service \
        --cluster "$CLUSTER_NAME" \
        --service "${STACK_NAME}-backend" \
        --force-new-deployment \
        --region "$REGION" > /dev/null

    # Update frontend service
    echo "Updating frontend service..."
    aws ecs update-service \
        --cluster "$CLUSTER_NAME" \
        --service "${STACK_NAME}-frontend" \
        --force-new-deployment \
        --region "$REGION" > /dev/null

    echo -e "${GREEN}✓ ECS services updated${NC}"
    echo ""
}

# Function to run database migrations
run_migrations() {
    echo -e "${YELLOW}Running database migrations...${NC}"

    CLUSTER_NAME="${STACK_NAME}-cluster"

    # Get the backend task definition ARN
    TASK_DEF=$(aws ecs describe-services \
        --cluster "$CLUSTER_NAME" \
        --services "${STACK_NAME}-backend" \
        --region "$REGION" \
        --query 'services[0].taskDefinition' \
        --output text)

    # Get VPC configuration from the running service
    SUBNETS=$(aws ecs describe-services \
        --cluster "$CLUSTER_NAME" \
        --services "${STACK_NAME}-backend" \
        --region "$REGION" \
        --query 'services[0].networkConfiguration.awsvpcConfiguration.subnets' \
        --output text | tr '\t' ',')

    SECURITY_GROUPS=$(aws ecs describe-services \
        --cluster "$CLUSTER_NAME" \
        --services "${STACK_NAME}-backend" \
        --region "$REGION" \
        --query 'services[0].networkConfiguration.awsvpcConfiguration.securityGroups' \
        --output text | tr '\t' ',')

    echo "Running migration task..."
    TASK_ARN=$(aws ecs run-task \
        --cluster "$CLUSTER_NAME" \
        --task-definition "$TASK_DEF" \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUPS],assignPublicIp=ENABLED}" \
        --overrides '{
            "containerOverrides": [{
                "name": "backend",
                "command": ["python", "/app/scripts/init_db.py"]
            }]
        }' \
        --region "$REGION" \
        --query 'tasks[0].taskArn' \
        --output text)

    echo "Migration task started: $TASK_ARN"
    echo "Waiting for task to complete..."

    aws ecs wait tasks-stopped \
        --cluster "$CLUSTER_NAME" \
        --tasks "$TASK_ARN" \
        --region "$REGION"

    # Check exit code
    EXIT_CODE=$(aws ecs describe-tasks \
        --cluster "$CLUSTER_NAME" \
        --tasks "$TASK_ARN" \
        --region "$REGION" \
        --query 'tasks[0].containers[0].exitCode' \
        --output text)

    if [ "$EXIT_CODE" == "0" ]; then
        echo -e "${GREEN}✓ Database migrations completed successfully${NC}"
    else
        echo -e "${RED}✗ Migration task failed with exit code: $EXIT_CODE${NC}"
        echo "Check CloudWatch logs for details:"
        echo "  aws logs tail /ecs/${STACK_NAME}/backend --follow"
        exit 1
    fi
    echo ""
}

# Function to run Alembic migrations
run_alembic() {
    local ALEMBIC_CMD="${1:-upgrade head}"
    echo -e "${YELLOW}Running Alembic: $ALEMBIC_CMD${NC}"

    CLUSTER_NAME="${STACK_NAME}-cluster"

    # Get the backend task definition ARN
    TASK_DEF=$(aws ecs describe-services \
        --cluster "$CLUSTER_NAME" \
        --services "${STACK_NAME}-backend" \
        --region "$REGION" \
        --query 'services[0].taskDefinition' \
        --output text)

    # Get VPC configuration from the running service
    SUBNETS=$(aws ecs describe-services \
        --cluster "$CLUSTER_NAME" \
        --services "${STACK_NAME}-backend" \
        --region "$REGION" \
        --query 'services[0].networkConfiguration.awsvpcConfiguration.subnets' \
        --output text | tr '\t' ',')

    SECURITY_GROUPS=$(aws ecs describe-services \
        --cluster "$CLUSTER_NAME" \
        --services "${STACK_NAME}-backend" \
        --region "$REGION" \
        --query 'services[0].networkConfiguration.awsvpcConfiguration.securityGroups' \
        --output text | tr '\t' ',')

    echo "Running Alembic task..."
    TASK_ARN=$(aws ecs run-task \
        --cluster "$CLUSTER_NAME" \
        --task-definition "$TASK_DEF" \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUPS],assignPublicIp=ENABLED}" \
        --overrides "{
            \"containerOverrides\": [{
                \"name\": \"backend\",
                \"command\": [\"sh\", \"-c\", \"alembic $ALEMBIC_CMD\"]
            }]
        }" \
        --region "$REGION" \
        --query 'tasks[0].taskArn' \
        --output text)

    echo "Alembic task started: $TASK_ARN"
    echo "Waiting for task to complete..."

    aws ecs wait tasks-stopped \
        --cluster "$CLUSTER_NAME" \
        --tasks "$TASK_ARN" \
        --region "$REGION"

    # Check exit code
    EXIT_CODE=$(aws ecs describe-tasks \
        --cluster "$CLUSTER_NAME" \
        --tasks "$TASK_ARN" \
        --region "$REGION" \
        --query 'tasks[0].containers[0].exitCode' \
        --output text)

    if [ "$EXIT_CODE" == "0" ]; then
        echo -e "${GREEN}✓ Alembic command completed successfully${NC}"
    else
        echo -e "${RED}✗ Alembic task failed with exit code: $EXIT_CODE${NC}"
        echo "Check CloudWatch logs for details:"
        echo "  aws logs tail /ecs/${STACK_NAME}/backend --follow"
        exit 1
    fi
    echo ""
}

# Function to run SQL command
run_sql() {
    local SQL_QUERY="$1"
    echo -e "${YELLOW}Running SQL query...${NC}"

    CLUSTER_NAME="${STACK_NAME}-cluster"

    # Get the backend task definition ARN
    TASK_DEF=$(aws ecs describe-services \
        --cluster "$CLUSTER_NAME" \
        --services "${STACK_NAME}-backend" \
        --region "$REGION" \
        --query 'services[0].taskDefinition' \
        --output text)

    # Get VPC configuration from the running service
    SUBNETS=$(aws ecs describe-services \
        --cluster "$CLUSTER_NAME" \
        --services "${STACK_NAME}-backend" \
        --region "$REGION" \
        --query 'services[0].networkConfiguration.awsvpcConfiguration.subnets' \
        --output text | tr '\t' ',')

    SECURITY_GROUPS=$(aws ecs describe-services \
        --cluster "$CLUSTER_NAME" \
        --services "${STACK_NAME}-backend" \
        --region "$REGION" \
        --query 'services[0].networkConfiguration.awsvpcConfiguration.securityGroups' \
        --output text | tr '\t' ',')

    # Build shell command that runs Python with the SQL
    # Escape single quotes in SQL for shell
    SQL_ESCAPED="${SQL_QUERY//\'/\'\\\'\'}"

    SHELL_CMD="pip install -q psycopg2-binary && python -c \"
import os
from sqlalchemy import create_engine, text
url = os.environ['DATABASE_URL'].replace('+asyncpg', '')
engine = create_engine(url)
conn = engine.connect()
result = conn.execute(text('''$SQL_ESCAPED'''))
if result.returns_rows:
    for row in result:
        print(dict(row._mapping))
else:
    print(f'Rows affected: {result.rowcount}')
conn.commit()
conn.close()
\""

    # Escape for JSON
    SHELL_CMD_ESCAPED=$(echo "$SHELL_CMD" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')

    echo "Running SQL task..."
    TASK_ARN=$(aws ecs run-task \
        --cluster "$CLUSTER_NAME" \
        --task-definition "$TASK_DEF" \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUPS],assignPublicIp=ENABLED}" \
        --overrides "{
            \"containerOverrides\": [{
                \"name\": \"backend\",
                \"command\": [\"sh\", \"-c\", $SHELL_CMD_ESCAPED]
            }]
        }" \
        --region "$REGION" \
        --query 'tasks[0].taskArn' \
        --output text)

    echo "SQL task started: $TASK_ARN"
    echo "Waiting for task to complete..."

    aws ecs wait tasks-stopped \
        --cluster "$CLUSTER_NAME" \
        --tasks "$TASK_ARN" \
        --region "$REGION"

    # Check exit code
    EXIT_CODE=$(aws ecs describe-tasks \
        --cluster "$CLUSTER_NAME" \
        --tasks "$TASK_ARN" \
        --region "$REGION" \
        --query 'tasks[0].containers[0].exitCode' \
        --output text)

    echo ""
    echo -e "${YELLOW}Check logs for query output:${NC}"
    echo "  aws logs tail /ecs/${STACK_NAME}/backend --since 5m"

    if [ "$EXIT_CODE" == "0" ]; then
        echo -e "${GREEN}✓ SQL command completed successfully${NC}"
    else
        echo -e "${RED}✗ SQL task failed with exit code: $EXIT_CODE${NC}"
    fi
    echo ""
}

# Function to show outputs
show_outputs() {
    echo -e "${YELLOW}Stack Outputs:${NC}"
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
        --output table
    echo ""

    # Get ALB URL
    ALB_URL=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' \
        --output text)

    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "Application URL: ${GREEN}$ALB_URL${NC}"
    echo -e "Admin Panel: ${GREEN}$ALB_URL/admin${NC}"
    echo -e "API Health: ${GREEN}$ALB_URL/api/health${NC}"
    echo ""
    echo -e "${YELLOW}ECR Repositories:${NC}"
    echo -e "Backend: ${GREEN}${ECR_REGISTRY}/${BACKEND_REPO}${NC}"
    echo -e "Frontend: ${GREEN}${ECR_REGISTRY}/${FRONTEND_REPO}${NC}"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "1. Wait a few minutes for ECS tasks to become healthy"
    echo "2. Test the application at the URL above"
    echo "3. Check ECS task logs if there are issues:"
    echo "   aws logs tail /ecs/${STACK_NAME}/backend --follow"
    echo ""
}

# Main execution
main() {
    case "${1:-all}" in
        ecr)
            # Create ECR repos only
            create_ecr_repo "$BACKEND_REPO"
            create_ecr_repo "$FRONTEND_REPO"
            ;;
        images)
            # Build and push images only
            ecr_login
            build_and_push_images
            ;;
        validate)
            validate_template
            ;;
        deploy)
            # Deploy stack only (assumes images are built)
            validate_template
            deploy_stack
            show_outputs
            ;;
        update)
            # Update images and force ECS deployment
            ecr_login
            build_and_push_images
            update_ecs_services
            show_outputs
            ;;
        all)
            # Full deployment
            create_ecr_repo "$BACKEND_REPO"
            create_ecr_repo "$FRONTEND_REPO"
            ecr_login
            build_and_push_images
            validate_template
            deploy_stack
            update_ecs_services
            show_outputs
            ;;
        outputs)
            show_outputs
            ;;
        migrate)
            run_migrations
            ;;
        alembic)
            run_alembic "${2:-upgrade head}"
            ;;
        stamp)
            run_alembic "stamp ${2:-f4cab136eec2}"
            ;;
        sql)
            if [ -z "$2" ]; then
                echo "Usage: $0 sql \"SQL QUERY\""
                echo "Example: $0 sql \"SELECT * FROM invitations\""
                exit 1
            fi
            run_sql "$2"
            ;;
        *)
            echo "Usage: $0 {all|ecr|images|validate|deploy|update|migrate|alembic|stamp|sql|outputs}"
            echo ""
            echo "Commands:"
            echo "  all           - Full deployment: create ECR repos, build/push images, deploy stack (default)"
            echo "  ecr           - Only create ECR repositories"
            echo "  images        - Only build and push Docker images to ECR"
            echo "  validate      - Only validate CloudFormation template"
            echo "  deploy        - Only deploy CloudFormation stack (assumes images exist)"
            echo "  update        - Rebuild images and force ECS service update"
            echo "  migrate       - Run database migrations (create tables and seed data)"
            echo "  alembic [cmd] - Run Alembic command (default: upgrade head)"
            echo "  stamp [rev]   - Stamp database with revision (for fixing migration state)"
            echo "  sql \"query\"   - Run SQL query against the database"
            echo "  outputs       - Show stack outputs"
            exit 1
            ;;
    esac
}

main "$@"
