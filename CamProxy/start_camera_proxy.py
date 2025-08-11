#!/usr/bin/env python3
"""
Camera Proxy Starter Script
Helps start the camera proxy server and register ngrok URLs
"""
import subprocess
import time
import requests
import sys
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def start_proxy_server():
    """Start the camera proxy server"""
    print("Starting camera proxy server on port 8000...")
    process = subprocess.Popen([
        sys.executable, 'camera_proxy.py'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to start
    time.sleep(3)
    
    try:
        response = requests.get("http://localhost:8000/status", timeout=5)
        if response.status_code == 200:
            print("✓ Camera proxy server started successfully")
            return process
        else:
            print("✗ Camera proxy server failed to start properly")
            return None
    except Exception as e:
        print(f"✗ Error checking proxy server: {e}")
        return None

def register_ngrok_url(ngrok_url):
    """Register ngrok URL with the main app"""
    try:
        # Register with main Flask app
        response = requests.post("http://localhost:5000/api/register_ngrok", 
                               json={'ngrok_url': ngrok_url}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Ngrok URL registered with main app: {data.get('base_url')}")
        else:
            print(f"✗ Failed to register with main app: {response.text}")
            
        # Also register with proxy server
        proxy_url = ngrok_url
        if proxy_url.endswith('/stream'):
            proxy_url = proxy_url[:-7]
        if proxy_url.endswith('/'):
            proxy_url = proxy_url[:-1]
            
        response = requests.post("http://localhost:8000/set_external_url", 
                               json={'url': proxy_url}, timeout=5)
        
        if response.status_code == 200:
            print(f"✓ Ngrok URL registered with proxy server")
        else:
            print(f"✗ Failed to register with proxy server: {response.text}")
            
    except Exception as e:
        print(f"✗ Error registering ngrok URL: {e}")

def auto_detect_ngrok():
    """Auto-detect running ngrok tunnels"""
    try:
        response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            
            if not tunnels:
                print("No ngrok tunnels found")
                return None
                
            print("Found ngrok tunnels:")
            for i, tunnel in enumerate(tunnels):
                proto = tunnel.get('proto', 'unknown')
                public_url = tunnel.get('public_url', 'unknown')
                local_url = tunnel.get('config', {}).get('addr', 'unknown')
                print(f"  {i+1}. {proto.upper()}: {public_url} -> {local_url}")
            
            # Use the first HTTPS tunnel, or first tunnel if no HTTPS
            best_tunnel = None
            for tunnel in tunnels:
                if tunnel.get('proto') == 'https':
                    best_tunnel = tunnel
                    break
            
            if not best_tunnel and tunnels:
                best_tunnel = tunnels[0]
            
            if best_tunnel:
                public_url = best_tunnel.get('public_url')
                print(f"\nUsing: {public_url}")
                register_ngrok_url(public_url)
                return public_url
                
        else:
            print("Could not connect to ngrok API at http://127.0.0.1:4040")
            return None
            
    except Exception as e:
        print(f"Error detecting ngrok tunnels: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Camera Proxy Management Tool')
    parser.add_argument('--start-proxy', action='store_true', help='Start the camera proxy server')
    parser.add_argument('--register', type=str, help='Register a specific ngrok URL')
    parser.add_argument('--auto-detect', action='store_true', help='Auto-detect and register ngrok tunnels')
    parser.add_argument('--all', action='store_true', help='Start proxy and auto-detect ngrok')
    
    args = parser.parse_args()
    
    if args.all:
        # Start proxy server
        proxy_process = start_proxy_server()
        if proxy_process:
            print("\nAttempting to auto-detect ngrok tunnels...")
            time.sleep(2)
            auto_detect_ngrok()
            
            print("\n🎥 Camera proxy is running!")
            print("   Proxy server: http://localhost:8000")
            print("   Main app: http://localhost:5000")
            print("\nPress Ctrl+C to stop...")
            
            try:
                proxy_process.wait()
            except KeyboardInterrupt:
                print("\nStopping proxy server...")
                proxy_process.terminate()
        
    elif args.start_proxy:
        proxy_process = start_proxy_server()
        if proxy_process:
            print("\n🎥 Camera proxy is running on http://localhost:8000")
            print("Press Ctrl+C to stop...")
            try:
                proxy_process.wait()
            except KeyboardInterrupt:
                print("\nStopping proxy server...")
                proxy_process.terminate()
    
    elif args.register:
        register_ngrok_url(args.register)
    
    elif args.auto_detect:
        auto_detect_ngrok()
    
    else:
        print("Camera Proxy Management Tool")
        print("\nUsage:")
        print("  python start_camera_proxy.py --all              # Start proxy + auto-detect ngrok")
        print("  python start_camera_proxy.py --start-proxy      # Start proxy server only")
        print("  python start_camera_proxy.py --auto-detect      # Auto-detect ngrok tunnels")
        print("  python start_camera_proxy.py --register <url>   # Register specific ngrok URL")
        print("\nExample:")
        print("  python start_camera_proxy.py --register https://abc123.ngrok.io")

if __name__ == '__main__':
    main()