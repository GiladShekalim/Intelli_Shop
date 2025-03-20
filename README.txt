# MongoDB Coupon Management

A Python project for managing coupon data using MongoDB, including JSON validation and data insertion.

## Working with GIT - Cloning, Branching, Committing

1. **Clone the Repository**
   ```bash
   cd C:\Users\YourUsername\Desktop\YourNewFolder
   git clone https://github.com/YourUsername/YourRepo.git
   ```

2. **Creating a New Branch**
   ```bash
   # Create and switch to a new branch:
   git checkout -b new-feature-branch
   ```

3. **Making Changes**
   Make your desired changes to the project files.

4. **Committing Changes**
   ```bash
   # Stage your changes:
   git add .
   ```
   ```bash
   # Commit your changes:
   git commit -m "Add short detail on what is being committed here"
   ```

5. **Pushing Changes to the Remote Repository**
   Do once:
   ```bash
   ssh-keygen -t rsa -b 4096 -C "youremail@example.com"
   cat ~/.ssh/id_rsa.pub
   # Copy string to GitHub > Setting > SSH > New SSH Key
   ```

   ```bash
   git push -u origin new-feature-branch
   ```

## Quick Start

1. **Setup Environment**
   ```bash
   # Deactivate the current virtual environment if any:
   deactivate

   # Remove the existing virtual environment if any:
   rm -rf venv

   # Ensure you have the necessary tools installed:
   sudo apt update
   sudo apt install python3-venv python3-pip

   # Create a new virtual environment using the full path to python3:
   /usr/bin/python3 -m venv venv

   # Activate the new virtual environment:
   source venv/bin/activate

   # Upgrade pip within the virtual environment:
   pip install --upgrade pip

   # Install the requirements:
   pip install -r requirements.txt
   ```

2. **Run the Project**
   ```bash
   python MongoSetup.py
   ```

## Files
- `MongoSetup.py` - Main script for managing MongoDB operations.
- `OfferList.json` - Sample JSON data for coupons.
- `scheme_definitions.py` - JSON schema definitions for coupon validation.
- `requirements.txt` - Dependencies required for the project.
- `test_import.py` - Script to test module imports.

## Packages Used
- pymongo (4.5.0)
- jsonschema (4.19.0)

## Features
✓ Connect to MongoDB
✓ Validate JSON data against a schema
✓ Insert and retrieve data from MongoDB
✓ Error handling (logging-next)
