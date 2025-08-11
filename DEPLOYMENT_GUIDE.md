# UniSync Deployment Guide for Replit

## 🚀 Ready for Deployment!

Your UniSync app is now configured for global deployment with camera streaming capabilities.

## How It Works After Deployment

### 🌐 Global Access
- **App URL**: Your deployed app will be accessible globally at `https://your-app.replit.app`
- **User Management**: All role-based features (admin/teacher/student dashboards) work globally
- **Database**: Uses Replit's PostgreSQL database for production reliability

### 📹 Camera Streaming (On-Demand)
- **Local to Global**: Create ngrok tunnels from your machine when you want to stream
- **Instant Registration**: Use the web interface to register new ngrok URLs instantly
- **No Local Dependencies**: The deployed app doesn't need local proxy servers

## Deployment Steps

### 1. Deploy to Replit
Click the **Deploy** button in your Replit workspace:
- Choose **Autoscale** deployment type
- Resource configuration: 
  - CPU: 0.25 vCPU (sufficient for web app)
  - RAM: 0.5 GB (adequate for Flask + database)
- Run command: `gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app`

### 2. Set Environment Variables (Optional)
In your deployment settings, you can configure:
- `SESSION_SECRET`: A secure secret key for sessions (auto-generated if not set)
- `ESP32_IP`: Your ESP32 camera IP (default: 192.168.29.115)

### 3. First Login
After deployment:
- Visit your deployed app URL
- Login with: 
  - Username: `admin`
  - Password: `admin123`
- **Important**: Change the admin password immediately!

## Using Camera Streaming After Deployment

### When You Want to Stream Your Camera:

1. **Start Ngrok on Your Machine**:
   ```bash
   ngrok http 81  # Or your ESP32 camera port
   ```

2. **Register the URL**:
   - Copy your ngrok URL (e.g., `https://abc123.ngrok.io`)
   - Go to Camera Stream page in your deployed app
   - Paste the URL in "Manual Ngrok URL" field
   - Click "Register"

3. **Start Streaming**:
   - Click "Start Stream" 
   - Your local camera now streams through the global app!

### Features That Work Globally:
✅ User authentication and role management  
✅ Attendance marking and tracking  
✅ Student dashboard and statistics  
✅ Admin user management  
✅ File uploads and management  
✅ Camera stream interface  

### Features That Need Local Setup:
📍 Camera streaming (requires ngrok tunnel from your machine)  
📍 Auto-detection (works locally only)  

## Benefits of This Architecture

### 🌍 Global Accessibility
- Access your UniSync system from anywhere
- Students and teachers can log in remotely
- Persistent data storage in the cloud

### 🎥 Flexible Camera Control
- Stream your camera only when needed
- No permanent camera hardware required on server
- Easy to switch between different camera sources

### 🔒 Security
- Role-based access control works globally
- Camera streams only when you actively create tunnels
- Database secured by Replit's infrastructure

## Troubleshooting After Deployment

### If Camera Streaming Doesn't Work:
1. **Check Ngrok URL**: Verify it works in a browser first
2. **URL Format**: Ensure you're using the base URL (without /stream)
3. **Re-register**: Clear and re-register the ngrok URL
4. **ESP32 Status**: Check your ESP32 camera is online

### If App Won't Load:
1. **Check Deployment Logs**: Look for errors in the deployment console
2. **Database Connection**: Verify PostgreSQL database is properly connected
3. **Resource Limits**: Ensure your deployment has sufficient CPU/RAM

## What's Different in Deployed Version

- **No Local Proxy**: The camera proxy server isn't needed
- **Direct Ngrok**: Streams directly from registered ngrok URLs
- **PostgreSQL**: Uses cloud database instead of local SQLite
- **Global Session Management**: User sessions work across the internet

Your app is now ready to serve users globally while maintaining the flexibility to stream your local camera on demand!