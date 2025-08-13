#!/bin/bash

# pgAdmin Utility Script
# Provides easy commands for managing pgAdmin container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PGADMIN_URL="http://localhost:5050"
PGADMIN_EMAIL="admin@admin.com"
PGADMIN_PASSWORD="admin123"
CONTAINER_NAME="multitenant-pgadmin"

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to check if pgAdmin is running
check_pgadmin_status() {
    if docker ps | grep -q $CONTAINER_NAME; then
        return 0
    else
        return 1
    fi
}

# Function to start pgAdmin
start_pgadmin() {
    print_info "Starting pgAdmin..."

    if check_pgadmin_status; then
        print_warning "pgAdmin is already running"
    else
        docker-compose up -d pgadmin
        print_success "pgAdmin started successfully"
        print_info "Waiting for pgAdmin to be ready..."
        sleep 5
    fi

    print_info "pgAdmin URL: ${BLUE}${PGADMIN_URL}${NC}"
    print_info "Email: ${BLUE}${PGADMIN_EMAIL}${NC}"
    print_info "Password: ${BLUE}${PGADMIN_PASSWORD}${NC}"
}

# Function to stop pgAdmin
stop_pgadmin() {
    print_info "Stopping pgAdmin..."

    if check_pgadmin_status; then
        docker-compose stop pgadmin
        print_success "pgAdmin stopped successfully"
    else
        print_warning "pgAdmin is not running"
    fi
}

# Function to restart pgAdmin
restart_pgadmin() {
    print_info "Restarting pgAdmin..."
    stop_pgadmin
    sleep 2
    start_pgadmin
}

# Function to view pgAdmin logs
view_logs() {
    print_info "Showing pgAdmin logs..."
    docker-compose logs -f pgadmin
}

# Function to reset pgAdmin (clear all data)
reset_pgadmin() {
    print_warning "This will delete all pgAdmin configurations and saved queries!"
    read -p "Are you sure? (y/N): " confirm

    if [[ $confirm == [yY] ]]; then
        print_info "Resetting pgAdmin..."

        # Stop container
        if check_pgadmin_status; then
            docker-compose stop pgadmin
        fi

        # Remove volume
        docker volume rm travel_system_pgadmin_data 2>/dev/null || true

        # Start fresh
        docker-compose up -d pgadmin
        print_success "pgAdmin has been reset"

        print_info "pgAdmin URL: ${BLUE}${PGADMIN_URL}${NC}"
        print_info "Email: ${BLUE}${PGADMIN_EMAIL}${NC}"
        print_info "Password: ${BLUE}${PGADMIN_PASSWORD}${NC}"
    else
        print_info "Reset cancelled"
    fi
}

# Function to open pgAdmin in browser
open_browser() {
    print_info "Opening pgAdmin in browser..."

    # Check if pgAdmin is running
    if ! check_pgadmin_status; then
        print_warning "pgAdmin is not running. Starting it now..."
        start_pgadmin
    fi

    # Detect OS and open browser
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open $PGADMIN_URL
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v xdg-open &> /dev/null; then
            xdg-open $PGADMIN_URL
        else
            print_warning "Could not open browser automatically. Please navigate to: ${BLUE}${PGADMIN_URL}${NC}"
        fi
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        # Windows
        start $PGADMIN_URL
    else
        print_warning "Could not detect OS. Please navigate to: ${BLUE}${PGADMIN_URL}${NC}"
    fi
}

# Function to show pgAdmin status
show_status() {
    print_info "Checking pgAdmin status..."

    if check_pgadmin_status; then
        print_success "pgAdmin is running"

        # Show container details
        docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

        echo ""
        print_info "Access details:"
        print_info "  URL: ${BLUE}${PGADMIN_URL}${NC}"
        print_info "  Email: ${BLUE}${PGADMIN_EMAIL}${NC}"
        print_info "  Password: ${BLUE}${PGADMIN_PASSWORD}${NC}"
    else
        print_error "pgAdmin is not running"
        print_info "Use './pgadmin.sh start' to start pgAdmin"
    fi
}

# Function to backup pgAdmin configuration
backup_config() {
    print_info "Backing up pgAdmin configuration..."

    # Create backup directory
    BACKUP_DIR="./backups/pgadmin"
    mkdir -p $BACKUP_DIR

    # Generate timestamp
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="${BACKUP_DIR}/pgadmin_backup_${TIMESTAMP}.tar.gz"

    # Create backup
    docker run --rm \
        -v travel_system_pgadmin_data:/data \
        -v $(pwd)/${BACKUP_DIR}:/backup \
        alpine tar czf /backup/pgadmin_backup_${TIMESTAMP}.tar.gz -C /data .

    print_success "Backup created: ${BACKUP_FILE}"
}

# Function to restore pgAdmin configuration
restore_config() {
    if [ -z "$1" ]; then
        print_error "Please provide a backup file path"
        print_info "Usage: ./pgadmin.sh restore <backup_file>"
        return 1
    fi

    if [ ! -f "$1" ]; then
        print_error "Backup file not found: $1"
        return 1
    fi

    print_warning "This will replace current pgAdmin configuration!"
    read -p "Are you sure? (y/N): " confirm

    if [[ $confirm == [yY] ]]; then
        print_info "Restoring pgAdmin configuration..."

        # Stop container
        if check_pgadmin_status; then
            docker-compose stop pgadmin
        fi

        # Clear existing data
        docker volume rm travel_system_pgadmin_data 2>/dev/null || true
        docker volume create travel_system_pgadmin_data

        # Restore backup
        docker run --rm \
            -v travel_system_pgadmin_data:/data \
            -v $(realpath $1):/backup.tar.gz \
            alpine tar xzf /backup.tar.gz -C /data

        # Start pgAdmin
        docker-compose up -d pgadmin

        print_success "Configuration restored successfully"
    else
        print_info "Restore cancelled"
    fi
}

# Function to show help
show_help() {
    echo "pgAdmin Utility Script"
    echo ""
    echo "Usage: ./pgadmin.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start       Start pgAdmin container"
    echo "  stop        Stop pgAdmin container"
    echo "  restart     Restart pgAdmin container"
    echo "  status      Show pgAdmin status"
    echo "  logs        View pgAdmin logs"
    echo "  open        Open pgAdmin in browser"
    echo "  reset       Reset pgAdmin (delete all data)"
    echo "  backup      Backup pgAdmin configuration"
    echo "  restore     Restore pgAdmin configuration from backup"
    echo "  help        Show this help message"
    echo ""
    echo "Access Information:"
    echo "  URL:      ${PGADMIN_URL}"
    echo "  Email:    ${PGADMIN_EMAIL}"
    echo "  Password: ${PGADMIN_PASSWORD}"
}

# Main script logic
case "${1:-}" in
    start)
        start_pgadmin
        ;;
    stop)
        stop_pgadmin
        ;;
    restart)
        restart_pgadmin
        ;;
    status)
        show_status
        ;;
    logs)
        view_logs
        ;;
    open)
        open_browser
        ;;
    reset)
        reset_pgadmin
        ;;
    backup)
        backup_config
        ;;
    restore)
        restore_config "$2"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        if [ -n "$1" ]; then
            print_error "Unknown command: $1"
            echo ""
        fi
        show_help
        exit 1
        ;;
esac
