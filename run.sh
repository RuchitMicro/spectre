#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 <project_name> <project_path> [preset]"
    exit 1
}

# Function to handle errors
handle_error() {
    echo "Error: $1"
    exit 1
}

# Check if project name and path are provided
if [ -z "$1" ] || [ -z "$2" ]; then
    usage
fi

PROJECT_NAME=$1
PROJECT_PATH=$2
PRESET=$3

# Update package list and install necessary packages
echo "Updating package list..."
sudo apt-get update || handle_error "Failed to update package list."

echo "Installing Python3 and virtualenv..."
sudo apt-get install -y python3 python3-venv python3-pip || handle_error "Failed to install Python3 and virtualenv."

# Create project directory
mkdir -p $PROJECT_PATH/$PROJECT_NAME || handle_error "Failed to create project directory."
cd $PROJECT_PATH/$PROJECT_NAME || handle_error "Failed to change directory to project path."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv || handle_error "Failed to create virtual environment."

# Activate virtual environment
source venv/bin/activate || handle_error "Failed to activate virtual environment."

# Upgrade pip and install Django
echo "Upgrading pip and installing Django..."
pip install --upgrade pip || handle_error "Failed to upgrade pip."
pip install django || handle_error "Failed to install Django."

# Create Django project
echo "Creating Django project..."
django-admin startproject $PROJECT_NAME . || handle_error "Failed to create Django project."

# Check for preset and create the app with boilerplate files
if [ -n "$PRESET" ]; then
    echo "Applying $PRESET preset..."
    django-admin startapp $PRESET || handle_error "Failed to create Django app."

    # Copy boilerplate files from the preset folder
    PRESET_DIR="$(dirname $0)/presets/$PRESET"
    APP_DIR="$PRESET"

    if [ -d "$PRESET_DIR" ]; then
        echo "Copying boilerplate files from preset..."
        cp -r $PRESET_DIR/* $APP_DIR/ || handle_error "Failed to copy boilerplate files."
    else
        handle_error "Preset directory $PRESET_DIR does not exist."
    fi
else
    echo "No preset specified. Skipping preset application."
fi

# Deactivate virtual environment
deactivate || handle_error "Failed to deactivate virtual environment."

echo "Django project $PROJECT_NAME created successfully in $PROJECT_PATH!"
echo "To activate the virtual environment, use: source $PROJECT_PATH/$PROJECT_NAME/venv/bin/activate"



