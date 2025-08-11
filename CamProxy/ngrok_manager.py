"""
Ngrok Manager for ESP32 Camera Stream
Handles ngrok tunnel creation and URL management
"""
import subprocess
import time
import requests
import logging
import os
import json
from threading import Thread

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class NgrokManager:
    def __init__(self):
        self.ESP32_IP = os.environ.get("ESP32_IP", "192.168.29.115")
        self.LOCAL_UPDATE_URL = "http://localhost:5000/api/update_camera_stream"
        self.RENDER_UPDATE_URL = "https://unisync-pimy.onrender.com/api/update_camera_stream"
        
        self.proxy_process = None
        self.ngrok_process = None
        self.public_url = None
        self.is_running = False
    
    def start_proxy_server(self):
        """Start the camera proxy server"""
        try:
            logging.info("Starting camera proxy server...")
            self.proxy_process = subprocess.Popen([
                'python', 'camera_proxy.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            time.sleep(3)  # Give Flask time to start
            
            # Test if proxy is running
            response = requests.get("http://localhost:8000/status", timeout=5)
            if response.status_code == 200:
                logging.info("Camera proxy server started successfully")
                return True
            else:
                logging.error("Camera proxy server failed to start properly")
                return False
                
        except Exception as e:
            logging.error(f"Error starting proxy server: {e}")
            return False
    
    def start_ngrok_tunnel(self):
        """Start ngrok tunnel for the proxy server"""
        try:
            logging.info("Starting ngrok tunnel...")
            self.ngrok_process = subprocess.Popen([
                'ngrok', 'http', '8000', '--log=stdout'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            time.sleep(6)  # Give ngrok time to start
            
            # Get public URL
            return self.get_public_url()
            
        except Exception as e:
            logging.error(f"Error starting ngrok tunnel: {e}")
            return False
    
    def get_public_url(self):
        """Get the public ngrok URL"""
        try:
            tunnel_info = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=10).json()
            
            if tunnel_info.get('tunnels'):
                self.public_url = tunnel_info['tunnels'][0]['public_url']
                logging.info(f"Public URL obtained: {self.public_url}")
                return True
            else:
                logging.error("No ngrok tunnels found")
                return False
                
        except Exception as e:
            logging.error(f"Error getting ngrok URL: {e}")
            return False
    
    def update_flask_app(self):
        """Send public stream URL to Flask app"""
        if not self.public_url:
            logging.error("No public URL available to send")
            return False
        
        stream_url = f"{self.public_url}/stream"
        
        try:
            # Try local first
            try:
                response = requests.post(
                    self.LOCAL_UPDATE_URL, 
                    json={"stream_url": stream_url},
                    timeout=10
                )
                
                if response.status_code == 200:
                    logging.info(f"Local Flask app updated successfully: {response.text}")
                    return True
                else:
                    logging.warning(f"Local Flask app responded with status {response.status_code}")
                    
            except requests.exceptions.RequestException:
                logging.info("Local Flask app not accessible, trying Render...")
            
            # Try Render deployment
            response = requests.post(
                self.RENDER_UPDATE_URL, 
                json={"stream_url": stream_url},
                timeout=15
            )
            
            if response.status_code == 200:
                logging.info(f"Render app updated successfully: {response.text}")
                return True
            else:
                logging.error(f"Render app responded with status {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"Error updating Flask app: {e}")
            return False
    
    def monitor_connection(self):
        """Monitor camera connection and restart if needed"""
        while self.is_running:
            try:
                # Check ESP32 camera
                response = requests.get(f"http://{self.ESP32_IP}:81/", timeout=5)
                if response.status_code != 200:
                    logging.warning("ESP32 camera not responding properly")
                
                # Check proxy server
                response = requests.get("http://localhost:8000/status", timeout=5)
                if response.status_code != 200:
                    logging.warning("Proxy server not responding")
                    
                # Check ngrok tunnel
                response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
                if not response.json().get('tunnels'):
                    logging.warning("Ngrok tunnel not active")
                
            except Exception as e:
                logging.error(f"Connection monitoring error: {e}")
            
            time.sleep(30)  # Check every 30 seconds
    
    def start(self):
        """Start the complete camera streaming setup"""
        logging.info("Starting NgrokManager...")
        
        # Start proxy server
        if not self.start_proxy_server():
            logging.error("Failed to start proxy server")
            return False
        
        # Start ngrok tunnel
        if not self.start_ngrok_tunnel():
            logging.error("Failed to start ngrok tunnel")
            return False
        
        # Update Flask app with stream URL
        if not self.update_flask_app():
            logging.error("Failed to update Flask app")
            return False
        
        # Start monitoring
        self.is_running = True
        monitor_thread = Thread(target=self.monitor_connection, daemon=True)
        monitor_thread.start()
        
        logging.info("NgrokManager started successfully")
        return True
    
    def stop(self):
        """Stop all processes"""
        self.is_running = False
        
        if self.proxy_process:
            self.proxy_process.terminate()
            logging.info("Proxy server stopped")
        
        if self.ngrok_process:
            self.ngrok_process.terminate()
            logging.info("Ngrok tunnel stopped")

def main():
    """Main function to run the ngrok manager"""
    manager = NgrokManager()
    
    try:
        if manager.start():
            logging.info("ESP32 Camera streaming setup complete!")
            logging.info(f"Public stream URL: {manager.public_url}/stream")
            
            # Keep running
            while True:
                time.sleep(60)
                
        else:
            logging.error("Failed to start camera streaming setup")
            
    except KeyboardInterrupt:
        logging.info("Shutting down...")
        manager.stop()
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        manager.stop()

if __name__ == '__main__':
    main()
