#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}     pgAdmin Connection Information${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if containers are running
PGADMIN_STATUS=$(docker ps --filter "name=multitenant-pgadmin" --format "{{.Status}}" 2>/dev/null)
POSTGRES_STATUS=$(docker ps --filter "name=multitenant-postgres" --format "{{.Status}}" 2>/dev/null)

if [ -z "$PGADMIN_STATUS" ]; then
    echo -e "${RED}❌ pgAdmin container is not running${NC}"
    echo -e "${YELLOW}   Run: docker-compose up -d pgadmin${NC}"
else
    echo -e "${GREEN}✅ pgAdmin is running${NC}"
    echo -e "   Status: $PGADMIN_STATUS"
fi

if [ -z "$POSTGRES_STATUS" ]; then
    echo -e "${RED}❌ PostgreSQL container is not running${NC}"
    echo -e "${YELLOW}   Run: docker-compose up -d postgres${NC}"
else
    echo -e "${GREEN}✅ PostgreSQL is running${NC}"
    echo -e "   Status: $POSTGRES_STATUS"
fi

echo ""
echo -e "${BLUE}pgAdmin Web Interface:${NC}"
echo -e "  URL: ${GREEN}http://localhost:5050${NC}"
echo -e "  Email: ${GREEN}admin@admin.com${NC}"
echo -e "  Password: ${GREEN}admin123${NC}"

echo ""
echo -e "${BLUE}PostgreSQL Connection (from pgAdmin):${NC}"
echo -e "  Host: ${GREEN}postgres${NC} (internal Docker network)"
echo -e "  Port: ${GREEN}5432${NC}"
echo -e "  Database: ${GREEN}multitenant_db${NC}"
echo -e "  Username: ${GREEN}postgres${NC}"
echo -e "  Password: ${GREEN}postgres123${NC}"

echo ""
echo -e "${BLUE}PostgreSQL Connection (from host):${NC}"
echo -e "  Host: ${GREEN}localhost${NC}"
echo -e "  Port: ${GREEN}5432${NC}"
echo -e "  Database: ${GREEN}multitenant_db${NC}"
echo -e "  Username: ${GREEN}postgres${NC}"
echo -e "  Password: ${GREEN}postgres123${NC}"

echo ""
echo -e "${BLUE}================================================${NC}"

# Test connection if both containers are running
if [ -n "$PGADMIN_STATUS" ] && [ -n "$POSTGRES_STATUS" ]; then
    echo ""
    echo -e "${BLUE}Testing database connection...${NC}"

    # Test PostgreSQL connection
    docker exec multitenant-postgres psql -U postgres -d multitenant_db -c "SELECT 1;" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PostgreSQL connection successful${NC}"
    else
        echo -e "${RED}❌ PostgreSQL connection failed${NC}"
    fi

    # Test pgAdmin web interface
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5050 2>/dev/null)
    if [ "$HTTP_STATUS" == "302" ] || [ "$HTTP_STATUS" == "200" ]; then
        echo -e "${GREEN}✅ pgAdmin web interface is accessible${NC}"
        echo ""
        echo -e "${GREEN}🌐 Open pgAdmin: http://localhost:5050${NC}"
    else
        echo -e "${RED}❌ pgAdmin web interface is not accessible (HTTP $HTTP_STATUS)${NC}"
    fi
fi

echo ""
echo -e "${BLUE}Troubleshooting Commands:${NC}"
echo -e "  View pgAdmin logs: ${YELLOW}docker logs multitenant-pgadmin${NC}"
echo -e "  View PostgreSQL logs: ${YELLOW}docker logs multitenant-postgres${NC}"
echo -e "  Restart pgAdmin: ${YELLOW}docker restart multitenant-pgadmin${NC}"
echo -e "  Restart PostgreSQL: ${YELLOW}docker restart multitenant-postgres${NC}"
echo -e "  Recreate containers: ${YELLOW}docker-compose up -d --force-recreate pgadmin postgres${NC}"
echo ""
