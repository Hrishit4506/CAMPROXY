# UniSync Camera System Setup Guide

## Quick Start for Ngrok Integration

### Method 1: Automatic Setup (Recommended)
```bash
# Start everything automatically
python start_camera_proxy.py --all
```

### Method 2: Manual Setup
```bash
# Step 1: Start the camera proxy server
python start_camera_proxy.py --start-proxy

# Step 2: In another terminal, start your ngrok tunnel (from your machine)
ngrok http 8081  # Or your ESP32 camera port

# Step 3: Register the ngrok URL
python start_camera_proxy.py --register https://abc123.ngrok.io
```

### Method 3: Web Interface
1. Open UniSync web app at http://localhost:5000
2. Login and go to Camera Stream page
3. Click "Auto-Detect Ngrok" button
4. Or manually enter your ngrok URL and click "Register"

## How It Works

### System Architecture
```
Your ESP32 Camera (192.168.29.115:81)
    ↓
Ngrok Tunnel (your machine) → https://abc123.ngrok.io
    ↓
Camera Proxy Server (localhost:8000) ← Handles CORS and streaming
    ↓
UniSync Main App (localhost:5000) ← Web interface
```

### Stream Sources Available
1. **Auto (Proxy + Fallback)** - Tries ngrok first, falls back to direct ESP32
2. **Local Proxy** - Uses localhost:8000 proxy server only
3. **Ngrok URL** - Uses registered ngrok tunnel directly

## Workflow for New Ngrok Tunnels

When you start a new ngrok tunnel on your machine:

### Option A: Auto-Detection
1. Start ngrok on your machine: `ngrok http 81` (or your camera port)
2. In the web app, click "Auto-Detect Ngrok"
3. The system will find and register your tunnel automatically

### Option B: Manual Registration
1. Copy your ngrok URL (e.g., https://abc123.ngrok.io)
2. In the web app, paste it in the "Manual Ngrok URL" field
3. Click "Register"

### Option C: Command Line
```bash
# Register directly via command line
python start_camera_proxy.py --register https://abc123.ngrok.io
```

## Troubleshooting

### Camera Stream Not Working
1. **Check ESP32 Connection**: Make sure your ESP32 is on and accessible at 192.168.29.115:81
2. **Verify Ngrok Tunnel**: Test your ngrok URL in a browser first
3. **Restart Proxy**: Stop and restart the camera proxy server
4. **Clear and Re-register**: Use "Clear Ngrok" button and register again

### Common Issues

#### "Stream Error Occurred"
- Your ESP32 camera is offline or unreachable
- Network connectivity issues
- Wrong IP address configured

#### "Auto-Detection Failed"
- Ngrok is not running on your machine
- Ngrok API not accessible at localhost:4040
- No active tunnels found

#### "Registration Failed"
- Invalid ngrok URL format
- Network connection issues
- Proxy server not running

### Testing Steps
1. **Test ESP32 Direct**: Visit http://192.168.29.115:81 in browser
2. **Test Ngrok URL**: Visit your ngrok URL in browser
3. **Test Proxy Server**: Visit http://localhost:8000 in browser
4. **Test Main App**: Visit http://localhost:5000 and try camera page

## Technical Details

### Camera Proxy Features
- CORS headers for web app compatibility
- Automatic fallback between external and local sources
- Real-time status monitoring
- Support for multiple stream sources

### API Endpoints
- `POST /api/register_ngrok` - Register ngrok URL
- `GET /api/auto_detect_ngrok` - Auto-detect running tunnels
- `GET /api/camera_status` - Get current camera status
- `POST /set_external_url` - Set external URL for proxy (localhost:8000)

### Environment Variables
- `ESP32_IP` - Your ESP32 camera IP (default: 192.168.29.115)

## Advanced Usage

### Running on Different Ports
```bash
# If your ESP32 uses a different port
export ESP32_IP=192.168.1.100
python start_camera_proxy.py --all
```

### Multiple Camera Support
The system is designed to handle one camera at a time. For multiple cameras, you would need to run separate proxy instances on different ports.

### Deployment Considerations
- The proxy server runs on localhost:8000
- Main app runs on localhost:5000
- Ngrok tunnels are created from your local machine
- CORS is enabled for cross-origin requests