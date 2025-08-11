# Overview

UniSync is a comprehensive educational management system that combines user authentication, role-based access control, and real-time camera streaming capabilities. The system serves three distinct user roles (students, teachers, and administrators) with tailored dashboards and features. It integrates ESP32 camera hardware with dynamic ngrok tunnel support for live streaming functionality, making it suitable for classroom monitoring, attendance tracking, and educational surveillance applications.

## Recent Changes (August 11, 2025)

- **Enhanced Ngrok Integration**: Added automatic ngrok tunnel detection and registration system
- **Camera Proxy Improvements**: Enhanced camera proxy server with CORS support and external URL handling
- **Dynamic Stream Sources**: Implemented multiple stream source options (Auto/Local Proxy/Ngrok)
- **PostgreSQL Compatibility**: Fixed database compatibility issues by replacing AUTOINCREMENT with SERIAL syntax
- **Management Tools**: Added command-line tools for camera proxy management and ngrok registration
- **Real-time URL Registration**: Created API endpoints for instant ngrok URL registration and auto-detection

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Template Engine**: Flask-Jinja2 templating system with role-specific dashboard templates
- **UI Framework**: Bootstrap 5 with dark theme for consistent, responsive design
- **Client-side Logic**: Vanilla JavaScript for camera stream management and real-time interactions
- **Asset Organization**: Separate CSS and JavaScript files for camera functionality and styling

## Backend Architecture
- **Web Framework**: Flask with SQLAlchemy ORM for database operations
- **Authentication System**: Session-based authentication with role-based access control (RBAC)
- **Database Layer**: SQLite database with User model supporting multiple roles (student, teacher, admin)
- **Security Features**: Password hashing using Werkzeug security utilities, login decorators, and role-based route protection

## Camera Streaming System
- **Enhanced Proxy Architecture**: Dedicated camera proxy server with CORS support and external URL handling
- **Dynamic Ngrok Integration**: Automatic detection and registration of ngrok tunnels from local ngrok API
- **Multiple Stream Sources**: Support for Auto (proxy + fallback), Local Proxy, and direct Ngrok URL streaming
- **Real-time URL Management**: API endpoints for instant ngrok URL registration and status updates
- **Fallback System**: Automatic fallback between external ngrok URLs and direct ESP32 connection
- **Stream Processing**: Real-time video stream proxying with comprehensive error handling and status monitoring

## External Service Integration
- **Dynamic Ngrok Tunneling**: Automatic detection and registration of user-created ngrok tunnels
- **Camera Proxy Management**: Command-line tools for starting proxy servers and managing ngrok integration
- **Real-time Registration**: Instant ngrok URL registration through web interface and API endpoints
- **Process Management**: Enhanced subprocess handling for camera proxy and tunnel management
- **Environment Configuration**: Flexible environment variable support for ESP32 IP addresses and service URLs

## Data Storage Strategy
- **SQLite Database**: Local file-based database for user management and authentication
- **File Storage**: Dataset folder for storing uploaded files with configurable size limits
- **Session Management**: Flask session handling for user authentication state

## API Design
- **RESTful Endpoints**: JSON API endpoints for camera status updates and stream management
- **Stream Endpoints**: Dedicated routes for camera stream proxying and status checking
- **Authentication APIs**: Login, logout, and role-based access endpoints

# External Dependencies

## Core Web Framework
- **Flask**: Main web framework with SQLAlchemy extension for database operations
- **Flask-CORS**: CORS support for camera proxy server and cross-origin requests
- **Bootstrap 5**: Frontend CSS framework with dark theme styling
- **Font Awesome**: Icon library for UI elements

## Hardware Integration
- **ESP32 Camera Module**: External camera hardware accessible via local network
- **HTTP Communication**: Direct HTTP requests to ESP32 web server for stream access

## Development Tools
- **Ngrok**: Tunneling service for exposing local development servers
- **Subprocess Management**: Python subprocess module for running concurrent services

## Security Libraries
- **Werkzeug Security**: Password hashing and security utilities
- **Flask Sessions**: Built-in session management for user authentication

## Deployment Platform
- **Render**: Cloud deployment platform with YAML configuration support
- **Environment Variables**: Configuration management for production and development environments