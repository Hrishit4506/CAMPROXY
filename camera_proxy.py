"""
ESP32 Camera Proxy Server
Runs on port 8000 to avoid conflicts with main Flask app
Handles both local ESP32 and remote ngrok URLs
"""
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import requests
import logging
import os
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

ESP32_IP = os.environ.get("ESP32_IP", "192.168.29.115")
EXTERNAL_STREAM_URL = None  # For ngrok or other external URLs

@app.route('/stream')
def stream():
    """Proxy the camera stream from ESP32 or external URL"""
    global EXTERNAL_STREAM_URL
    
    try:
        # Try external stream URL first (ngrok)
        if EXTERNAL_STREAM_URL:
            try:
                logging.info(f"Proxying external stream from: {EXTERNAL_STREAM_URL}")
                response = requests.get(EXTERNAL_STREAM_URL, stream=True, timeout=10, 
                                      headers={'User-Agent': 'UniSync-Camera-Proxy/1.0'})
                
                def generate():
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            yield chunk
                
                return Response(
                    generate(),
                    content_type=response.headers.get('Content-Type', 'multipart/x-mixed-replace; boundary=frame'),
                    headers={
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type',
                        'Cache-Control': 'no-cache'
                    }
                )
            except Exception as e:
                logging.warning(f"External stream failed: {e}, falling back to local ESP32")
        
        # Fallback to local ESP32
        stream_url = f"http://{ESP32_IP}:81/stream"
        logging.info(f"Proxying local stream from: {stream_url}")
        
        response = requests.get(stream_url, stream=True, timeout=10)
        
        def generate():
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk
        
        return Response(
            generate(),
            content_type=response.headers.get('Content-Type', 'multipart/x-mixed-replace; boundary=frame'),
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Cache-Control': 'no-cache'
            }
        )
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Stream error: {e}")
        return Response(f"Stream unavailable: {str(e)}", status=503)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return Response(f"Server error: {str(e)}", status=500)

@app.route('/set_external_url', methods=['POST'])
def set_external_url():
    """Set external stream URL (for ngrok)"""
    global EXTERNAL_STREAM_URL
    
    try:
        data = request.get_json()
        url = data.get('url') if data else None
        
        if url:
            # Clean up URL - remove trailing /stream if present
            if url.endswith('/stream'):
                url = url[:-7]
            EXTERNAL_STREAM_URL = f"{url}/stream"
            logging.info(f"External stream URL set to: {EXTERNAL_STREAM_URL}")
            return jsonify({'status': 'success', 'external_url': EXTERNAL_STREAM_URL})
        else:
            EXTERNAL_STREAM_URL = None
            logging.info("External stream URL cleared")
            return jsonify({'status': 'success', 'external_url': None})
            
    except Exception as e:
        logging.error(f"Error setting external URL: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/status')
def status():
    """Check camera status and configuration"""
    global EXTERNAL_STREAM_URL
    
    status_info = {
        'esp32_ip': ESP32_IP,
        'external_url': EXTERNAL_STREAM_URL,
        'timestamp': time.time()
    }
    
    # Check local ESP32
    try:
        response = requests.get(f"http://{ESP32_IP}:81/", timeout=5)
        status_info['esp32_status'] = 'online'
        status_info['esp32_response_code'] = response.status_code
    except requests.exceptions.RequestException as e:
        status_info['esp32_status'] = 'offline'
        status_info['esp32_error'] = str(e)
    
    # Check external URL if set
    if EXTERNAL_STREAM_URL:
        try:
            response = requests.get(EXTERNAL_STREAM_URL, timeout=5)
            status_info['external_status'] = 'online'
            status_info['external_response_code'] = response.status_code
        except requests.exceptions.RequestException as e:
            status_info['external_status'] = 'offline'
            status_info['external_error'] = str(e)
    
    return jsonify(status_info)

@app.route('/')
def home():
    """Simple test page for the proxy"""
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ESP32 Camera Proxy</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            img {{ max-width: 100%; border: 2px solid #ccc; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ESP32 Camera Proxy</h1>
            <p>ESP32 IP: {ESP32_IP}</p>
            <p><a href="/status">Check Status</a> | <a href="/stream">View Stream</a></p>
            
            <h2>Live Stream</h2>
            <img src="/stream" alt="ESP32 Camera Stream" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgZmlsbD0iI2Y4ZjlmYSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM2Yzc1N2QiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5DYW1lcmEgVW5hdmFpbGFibGU8L3RleHQ+PC9zdmc+';">
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    logging.info(f"Starting ESP32 Camera Proxy for IP: {ESP32_IP}")
    app.run(host='0.0.0.0', port=8000, debug=True)
