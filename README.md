# IntelliShop

IntelliShop is a web application that provides an intuitive e-commerce platform. Built with Django and MongoDB, it offers the foundation for online shopping experiences with AI-enhanced data personalization.

## Quick Start Guide

### Setting Up Environment Variables

Before running the application, you need to set up your environment variables:

1. Create a `.env` file in the project root directory with the following template:
   ```
   # MongoDB Configuration
   MONGODB_URI=mongodb+srv://username:password@yourcluster.mongodb.net/?retryWrites=true&w=majority
   MONGODB_NAME=YourDatabaseName

   # Django Settings
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   
   # Groq API (for AI enhancement)
   GROQ_API_KEY=<your_api_key_here>
   ```

2. Replace the placeholder values with your actual MongoDB credentials and desired settings.

### Running the Application

The application includes an interactive setup menu that guides you through different initialization options:

```bash
git clone https://github.com/yourusername/intellishop.git
cd intellishop
```

### 2. Environment Setup

Follow the "Setting Up Environment Variables" section above to create your `.env` file.

### 3. Run the Setup Script

Run the interactive setup menu and select your preferred installation option:

```bash
./intelliShop.sh
```

This will display a menu with the following options:
1. **Setup only** - Basic application setup
2. **Setup -> data validation and insert** -> Setup and populate with sample data
3. **Setup -> AI enhancement -> data validation and insert** -> Setup with AI-enhanced product data

Access the application at http://localhost:8000 after setup completes.

## Features

- Product catalog with categories
- MongoDB integration for scalable data storage
- Responsive design for desktop and mobile devices
- User authentication and account management
- AI-powered discount data enhancement
- JSON-formatted product enhancements
- Field extraction and categorization

## Technologies Used

- **Backend**: Django, Python 3
- **Database**: MongoDB
- **Frontend**: HTML, CSS, JavaScript
- **AI Integration**: Groq Chat API
- **Deployment**: WSL (Windows Subsystem for Linux)

## Prerequisites

- Python 3.8 or higher
- Access to a MongoDB database (Atlas URI)
- Groq API key (for AI enhancement features)

## AI Enhancement Features

The application includes AI-powered enhancement for discount data using the Groq Chat API:

- Support for Hebrew text in discount objects
- Comprehensive error handling with retries
- Detailed processing summary
- Automatic environment setup

The enhancement process:
- Reads discount objects from data directory
- Processes each object through Groq's API
- Saves enhanced objects to data directory
