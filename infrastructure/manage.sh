#!/bin/bash

# Wedding Application - Management Script
# Helper script for managing the deployed application

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
STACK_NAME=${STACK_NAME:-"wedding-app"}
REGION=${AWS_REGION:-"us-east-1"}
CLUSTER_NAME="$STACK_NAME-cluster"

# Function to get cluster and service names
get_cluster_info() {
    CLUSTER_NAME=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`ECSClusterName`].OutputValue' \
        --output text 2>/dev/null || echo "$STACK_NAME-cluster")
}

# Function to view logs
view_logs() {
    local service=$1
    if [ -z "$service" ]; then
        echo "Usage: $0 logs {backend|frontend}"
        exit 1
    fi

    LOG_GROUP="/ecs/$STACK_NAME/$service"
    echo -e "${YELLOW}Tailing logs for $service...${NC}"
    echo "Press Ctrl+C to stop"
    echo ""
    aws logs tail "$LOG_GROUP" --follow --region $REGION
}

# Function to run database migrations
run_migrations() {
    get_cluster_info

    echo -e "${YELLOW}Getting backend task...${NC}"
    TASK_ARN=$(aws ecs list-tasks \
        --cluster $CLUSTER_NAME \
        --service-name "$STACK_NAME-backend" \
        --region $REGION \
        --query 'taskArns[0]' \
        --output text)

    if [ -z "$TASK_ARN" ] || [ "$TASK_ARN" == "None" ]; then
        echo -e "${RED}ERROR: No backend tasks running${NC}"
        exit 1
    fi

    echo -e "${YELLOW}Running migrations on task: $TASK_ARN${NC}"

    # Note: This requires ECS Exec to be enabled
    aws ecs execute-command \
        --cluster $CLUSTER_NAME \
        --task $TASK_ARN \
        --container backend \
        --interactive \
        --command "cd /app && alembic upgrade head" \
        --region $REGION
}

# Function to restart services
restart_service() {
    local service=$1
    if [ -z "$service" ]; then
        echo "Usage: $0 restart {backend|frontend|all}"
        exit 1
    fi

    get_cluster_info

    if [ "$service" == "all" ]; then
        services=("backend" "frontend")
    else
        services=("$service")
    fi

    for svc in "${services[@]}"; do
        echo -e "${YELLOW}Restarting $svc service...${NC}"
        aws ecs update-service \
            --cluster $CLUSTER_NAME \
            --service "$STACK_NAME-$svc" \
            --force-new-deployment \
            --region $REGION > /dev/null
        echo -e "${GREEN}✓ $svc restart initiated${NC}"
    done
}

# Function to scale services
scale_service() {
    local service=$1
    local count=$2

    if [ -z "$service" ] || [ -z "$count" ]; then
        echo "Usage: $0 scale {backend|frontend|all} COUNT"
        exit 1
    fi

    get_cluster_info

    if [ "$service" == "all" ]; then
        services=("backend" "frontend")
    else
        services=("$service")
    fi

    for svc in "${services[@]}"; do
        echo -e "${YELLOW}Scaling $svc to $count tasks...${NC}"
        aws ecs update-service \
            --cluster $CLUSTER_NAME \
            --service "$STACK_NAME-$svc" \
            --desired-count $count \
            --region $REGION > /dev/null
        echo -e "${GREEN}✓ $svc scaled to $count${NC}"
    done
}

# Function to show service status
service_status() {
    get_cluster_info

    echo -e "${YELLOW}Service Status:${NC}"
    echo ""

    for service in backend frontend; do
        echo -e "${GREEN}=== $service ===${NC}"
        aws ecs describe-services \
            --cluster $CLUSTER_NAME \
            --services "$STACK_NAME-$service" \
            --region $REGION \
            --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,Pending:pendingCount}' \
            --output table
        echo ""
    done
}

# Function to list tasks
list_tasks() {
    get_cluster_info

    echo -e "${YELLOW}Running Tasks:${NC}"
    echo ""

    TASK_ARNS=$(aws ecs list-tasks \
        --cluster $CLUSTER_NAME \
        --region $REGION \
        --query 'taskArns' \
        --output text)

    if [ -z "$TASK_ARNS" ]; then
        echo "No tasks running"
        return
    fi

    aws ecs describe-tasks \
        --cluster $CLUSTER_NAME \
        --tasks $TASK_ARNS \
        --region $REGION \
        --query 'tasks[*].{Task:taskArn,Status:lastStatus,Health:healthStatus,CPU:cpu,Memory:memory}' \
        --output table
}

# Function to exec into container
exec_container() {
    local service=$1
    if [ -z "$service" ]; then
        echo "Usage: $0 exec {backend|frontend}"
        exit 1
    fi

    get_cluster_info

    echo -e "${YELLOW}Getting $service task...${NC}"
    TASK_ARN=$(aws ecs list-tasks \
        --cluster $CLUSTER_NAME \
        --service-name "$STACK_NAME-$service" \
        --region $REGION \
        --query 'taskArns[0]' \
        --output text)

    if [ -z "$TASK_ARN" ] || [ "$TASK_ARN" == "None" ]; then
        echo -e "${RED}ERROR: No $service tasks running${NC}"
        exit 1
    fi

    echo -e "${YELLOW}Connecting to task: $TASK_ARN${NC}"
    aws ecs execute-command \
        --cluster $CLUSTER_NAME \
        --task $TASK_ARN \
        --container $service \
        --interactive \
        --command "/bin/bash" \
        --region $REGION
}

# Function to get database info
db_info() {
    echo -e "${YELLOW}Database Information:${NC}"

    DB_ENDPOINT=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
        --output text)

    DB_PORT=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`DatabasePort`].OutputValue' \
        --output text)

    echo ""
    echo "Endpoint: $DB_ENDPOINT"
    echo "Port: $DB_PORT"
    echo "Database: wedding"
    echo ""
    echo "To connect from ECS task:"
    echo "  $0 exec backend"
    echo "  Then run: psql -h $DB_ENDPOINT -U wedding -d wedding"
}

# Function to show stack outputs
show_outputs() {
    echo -e "${YELLOW}Stack Outputs:${NC}"
    aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
        --output table
}

# Function to delete stack
delete_stack() {
    echo -e "${RED}WARNING: This will delete all resources including the database!${NC}"
    echo -e "${YELLOW}A final snapshot will be created before deletion.${NC}"
    echo ""
    read -p "Are you sure you want to delete the stack? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        echo "Deletion cancelled"
        exit 0
    fi

    echo -e "${YELLOW}Deleting stack...${NC}"
    aws cloudformation delete-stack \
        --stack-name $STACK_NAME \
        --region $REGION

    echo "Waiting for stack deletion..."
    aws cloudformation wait stack-delete-complete \
        --stack-name $STACK_NAME \
        --region $REGION

    echo -e "${GREEN}✓ Stack deleted${NC}"
}

# Main command router
main() {
    case "${1}" in
        logs)
            view_logs "${2}"
            ;;
        migrations)
            run_migrations
            ;;
        restart)
            restart_service "${2}"
            ;;
        scale)
            scale_service "${2}" "${3}"
            ;;
        status)
            service_status
            ;;
        tasks)
            list_tasks
            ;;
        exec)
            exec_container "${2}"
            ;;
        db)
            db_info
            ;;
        outputs)
            show_outputs
            ;;
        delete)
            delete_stack
            ;;
        *)
            echo "Wedding Application - Management Script"
            echo ""
            echo "Usage: $0 COMMAND [OPTIONS]"
            echo ""
            echo "Commands:"
            echo "  logs {backend|frontend}        - Tail service logs"
            echo "  migrations                     - Run database migrations"
            echo "  restart {backend|frontend|all} - Restart service(s)"
            echo "  scale {backend|frontend|all} N - Scale service to N tasks"
            echo "  status                         - Show service status"
            echo "  tasks                          - List running tasks"
            echo "  exec {backend|frontend}        - Exec into container"
            echo "  db                             - Show database info"
            echo "  outputs                        - Show stack outputs"
            echo "  delete                         - Delete the stack"
            echo ""
            echo "Examples:"
            echo "  $0 logs backend"
            echo "  $0 restart all"
            echo "  $0 scale backend 2"
            echo "  $0 exec backend"
            exit 1
            ;;
    esac
}

main "$@"
