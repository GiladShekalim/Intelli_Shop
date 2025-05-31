#!/bin/bash

# IntelliShop Project Menu
# This script provides a menu to run different setup options for IntelliShop

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to display the menu
show_menu() {
    #clear
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}       IntelliShop Setup Menu        ${NC}"
    echo -e "${BLUE}======================================${NC}"
    echo -e "${GREEN}1.${NC} Setup and start server"
    echo -e "${GREEN}2.${NC} Setup and start server -> data validation and insert"
    echo -e "${GREEN}3.${NC} Setup and start server -> AI enhancement -> data validation and insert"
    echo -e "${GREEN}4.${NC} X Setup -> Data Scraping -> AI enhancement -> data validation and insert"
    echo -e "${BLUE}======================================${NC}"
    echo -e "${YELLOW}q.${NC} Quit"
    echo -e "${BLUE}======================================${NC}"
    echo ""
    echo -e "Enter your choice: "
}

# Function to handle menu selection
handle_menu() {
    local choice
    read -r choice
    case $choice in
        1)
            echo -e "${GREEN}Starting server...${NC}"
            ./build.sh
            ;;
        2)
            echo -e "${GREEN}Updating database with sample data...${NC}"
            ./build.sh 1
            ;;
        3)
            echo -e "${GREEN}Running AI enhancement and updating database...${NC}"
            ./build.sh 2
            ;;
        q|Q) 
            echo -e "${GREEN}Exiting. Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option. Please try again.${NC}"
            sleep 2
            show_menu
            handle_menu
            ;;
    esac
}

# Verify script existence before making executable
if [ ! -f "build.sh" ]; then
    echo -e "${RED}Error: build.sh not found in exes directory${NC}"
    exit 1
fi

# Make the script executable
chmod +x build.sh
if [ -f "mysite/enhance_data.sh" ]; then
    chmod +x mysite/enhance_data.sh
fi

# Display menu and handle selection
show_menu
handle_menu
