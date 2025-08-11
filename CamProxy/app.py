import os
import logging
import requests
import threading
import time
from functools import wraps
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    # Fix for newer SQLAlchemy versions
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///instance/User.db'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'dataset'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize the app with the extension
db.init_app(app)

# Global variables for camera stream management
current_stream_url = None
camera_status = "Disconnected"
esp32_ip = os.environ.get("ESP32_IP", "192.168.29.115")
# For deployment, the proxy won't be available locally
local_proxy_url = "http://localhost:8000"
is_deployed = os.environ.get("REPL_ID") is not None  # Check if running on Replit

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            user = User.query.get(session['user_id'])
            if not user or user.role != role:
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Camera status monitoring
def monitor_camera_status():
    global camera_status
    while True:
        try:
            response = requests.get(f"http://{esp32_ip}:81/", timeout=5)
            if response.status_code == 200:
                camera_status = "Connected"
            else:
                camera_status = "Error"
        except requests.exceptions.RequestException:
            camera_status = "Disconnected"
        except Exception as e:
            logging.error(f"Camera monitoring error: {e}")
            camera_status = "Error"
        time.sleep(30)  # Check every 30 seconds

# Start camera monitoring in background
camera_monitor_thread = threading.Thread(target=monitor_camera_status, daemon=True)
camera_monitor_thread.start()

# Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    if user.role == 'admin':
        users = User.query.all()
        stats = {
            'total_users': len(users),
            'admins': len([u for u in users if u.role == 'admin']),
            'teachers': len([u for u in users if u.role == 'teacher']),
            'students': len([u for u in users if u.role == 'student'])
        }
        return render_template('admin_dashboard.html', user=user, users=users, stats=stats, camera_status=camera_status)
    elif user.role == 'teacher':
        students = User.query.filter_by(role='student').all()
        return render_template('teacher_dashboard.html', user=user, students=students, camera_status=camera_status)
    else:
        return render_template('student_dashboard.html', user=user, camera_status=camera_status)

@app.route('/admin/create_user', methods=['GET', 'POST'])
@role_required('admin')
def create_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('create_user'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'error')
            return redirect(url_for('create_user'))
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User()
        new_user.username = username
        new_user.email = email
        new_user.password_hash = hashed_password
        new_user.role = role
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Create dataset folder
            user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
            os.makedirs(user_folder, exist_ok=True)
            
            # Create attendance table for the user
            create_attendance_table(username)
            
            flash(f'User {username} created successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'error')
    
    return render_template('create_user.html')

@app.route('/teacher/mark_attendance', methods=['GET', 'POST'])
@role_required('teacher')
def mark_attendance():
    students = User.query.filter_by(role='student').all()
    
    if request.method == 'POST':
        student_username = request.form['student']
        status = request.form['status']
        date = request.form['date']
        
        try:
            # Insert attendance record
            table_name = f"attendance_{student_username}"
            query = f"""
                INSERT INTO {table_name} (date, status, created_at)
                VALUES (:date, :status, :created_at)
            """
            db.session.execute(db.text(query), {
                'date': date, 
                'status': status, 
                'created_at': datetime.utcnow()
            })
            db.session.commit()
            
            flash(f'Attendance marked for {student_username}', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error marking attendance: {str(e)}', 'error')
    
    return render_template('mark_attendance.html', students=students)

@app.route('/camera')
@login_required
def camera_stream():
    """Camera stream viewing page"""
    user = User.query.get(session['user_id'])
    return render_template('camera_stream.html', user=user, 
                         stream_url=current_stream_url, 
                         camera_status=camera_status)

@app.route('/api/camera_status')
@login_required
def api_camera_status():
    """API endpoint to get current camera status"""
    return jsonify({
        'status': camera_status,
        'stream_url': current_stream_url,
        'esp32_ip': esp32_ip
    })

@app.route('/api/update_camera_stream', methods=['POST'])
def update_camera_stream():
    """API endpoint to update camera stream URL from ngrok proxy"""
    global current_stream_url, camera_status
    
    try:
        data = request.get_json()
        if data and 'stream_url' in data:
            current_stream_url = data['stream_url']
            camera_status = "Connected via Ngrok"
            logging.info(f"Camera stream URL updated: {current_stream_url}")
            return jsonify({'status': 'success', 'message': 'Stream URL updated', 'url': current_stream_url})
        else:
            return jsonify({'status': 'error', 'message': 'Invalid data'}), 400
    except Exception as e:
        logging.error(f"Error updating camera stream: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/register_ngrok', methods=['POST'])
def register_ngrok():
    """Register a new ngrok URL for the camera stream"""
    global current_stream_url, camera_status
    
    try:
        data = request.get_json()
        ngrok_url = data.get('ngrok_url') if data else None
        
        if not ngrok_url:
            # Clear ngrok URL
            current_stream_url = None
            camera_status = "Disconnected"
            
            # Clear from proxy server too (only if not deployed)
            if not is_deployed:
                try:
                    requests.post(f"{local_proxy_url}/set_external_url", 
                                 json={'url': None}, timeout=5)
                except:
                    pass
            
            return jsonify({'status': 'success', 'message': 'Ngrok URL cleared'})
        
        # Clean up the URL and set the stream endpoint
        if ngrok_url.endswith('/'):
            ngrok_url = ngrok_url[:-1]
        if ngrok_url.endswith('/stream'):
            ngrok_url = ngrok_url[:-7]
        
        current_stream_url = f"{ngrok_url}/stream"
        camera_status = "Connected via Ngrok"
        
        # Update the proxy server with the external URL (only if not deployed)
        if not is_deployed:
            try:
                proxy_response = requests.post(f"{local_proxy_url}/set_external_url", 
                                             json={'url': ngrok_url}, timeout=5)
                if proxy_response.status_code != 200:
                    logging.warning("Failed to update proxy server with external URL")
            except Exception as e:
                logging.warning(f"Could not reach proxy server: {e}")
        
        logging.info(f"Ngrok URL registered: {current_stream_url}")
        return jsonify({
            'status': 'success', 
            'message': 'Ngrok URL registered successfully',
            'stream_url': current_stream_url,
            'base_url': ngrok_url
        })
        
    except Exception as e:
        logging.error(f"Error registering ngrok URL: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/auto_detect_ngrok', methods=['GET'])
@login_required
def auto_detect_ngrok():
    """Automatically detect ngrok tunnel from local ngrok API"""
    if is_deployed:
        return jsonify({
            'status': 'error', 
            'message': 'Auto-detection only works in local development. Please register your ngrok URL manually.'
        })
    
    try:
        # Try to get ngrok tunnels from local ngrok API
        response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            
            for tunnel in tunnels:
                if tunnel.get('proto') == 'https':  # Prefer HTTPS
                    public_url = tunnel.get('public_url')
                    if public_url:
                        # Register this URL
                        global current_stream_url, camera_status
                        
                        # Clean up URL
                        if public_url.endswith('/'):
                            public_url = public_url[:-1]
                        
                        current_stream_url = f"{public_url}/stream"
                        camera_status = "Connected via Ngrok"
                        
                        # Update the proxy server with the external URL
                        try:
                            proxy_response = requests.post(f"{local_proxy_url}/set_external_url", 
                                                         json={'url': public_url}, timeout=5)
                            if proxy_response.status_code != 200:
                                logging.warning("Failed to update proxy server with external URL")
                        except Exception as e:
                            logging.warning(f"Could not reach proxy server: {e}")
                        
                        logging.info(f"Auto-detected ngrok URL: {current_stream_url}")
                        return jsonify({
                            'status': 'success',
                            'message': 'Ngrok tunnel auto-detected',
                            'stream_url': current_stream_url,
                            'base_url': public_url
                        })
            
            return jsonify({'status': 'error', 'message': 'No suitable ngrok tunnels found'})
        else:
            return jsonify({'status': 'error', 'message': 'Could not connect to ngrok API'})
            
    except requests.exceptions.RequestException as e:
        return jsonify({'status': 'error', 'message': f'Ngrok API connection failed: {str(e)}'})
    except Exception as e:
        logging.error(f"Error auto-detecting ngrok: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/test_camera')
@login_required
def test_camera():
    """Test camera connectivity with multiple methods"""
    results = {}
    
    # Test local proxy first
    try:
        response = requests.get(f"{local_proxy_url}/status", timeout=3)
        if response.status_code == 200:
            results['local_proxy'] = {'status': 'success', 'message': 'Local proxy accessible'}
        else:
            results['local_proxy'] = {'status': 'error', 'message': f'Local proxy returned status {response.status_code}'}
    except requests.exceptions.RequestException as e:
        results['local_proxy'] = {'status': 'error', 'message': f'Local proxy failed: {str(e)}'}
    
    # Test direct ESP32 connection
    try:
        response = requests.get(f"http://{esp32_ip}:81/", timeout=3)
        if response.status_code == 200:
            results['esp32_direct'] = {'status': 'success', 'message': 'ESP32 camera accessible'}
        else:
            results['esp32_direct'] = {'status': 'error', 'message': f'ESP32 returned status {response.status_code}'}
    except requests.exceptions.RequestException as e:
        results['esp32_direct'] = {'status': 'error', 'message': f'ESP32 connection failed: {str(e)}'}
    
    # Test ngrok URL if available
    if current_stream_url:
        try:
            test_url = current_stream_url.replace('/stream', '/status') if '/stream' in current_stream_url else f"{current_stream_url}/status"
            response = requests.get(test_url, timeout=5)
            results['ngrok'] = {'status': 'success' if response.status_code == 200 else 'error', 
                              'message': f'Ngrok tunnel accessible (status: {response.status_code})'}
        except requests.exceptions.RequestException as e:
            results['ngrok'] = {'status': 'error', 'message': f'Ngrok tunnel failed: {str(e)}'}
    else:
        results['ngrok'] = {'status': 'error', 'message': 'No ngrok URL configured'}
    
    return jsonify(results)

@app.route('/stream_proxy')
@login_required
def stream_proxy():
    """Proxy camera stream with multiple fallback options"""
    global current_stream_url
    
    try:
        def generate():
            # If we have a registered ngrok URL, use it
            if current_stream_url:
                try:
                    logging.info(f"Trying registered stream: {current_stream_url}")
                    response = requests.get(current_stream_url, stream=True, timeout=10,
                                          headers={'User-Agent': 'UniSync-Camera-Stream/1.0'})
                    if response.status_code == 200:
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                yield chunk
                        return
                except Exception as e:
                    logging.warning(f"Registered stream failed: {e}")
            
            # Try local proxy only if not deployed
            if not is_deployed:
                try:
                    stream_url = f"{local_proxy_url}/stream"
                    logging.info(f"Trying local proxy stream: {stream_url}")
                    response = requests.get(stream_url, stream=True, timeout=5)
                    if response.status_code == 200:
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                yield chunk
                        return
                except Exception as e:
                    logging.warning(f"Local proxy failed: {e}")
            
            # Fallback to direct ESP32 (only works locally)
            if not is_deployed:
                try:
                    stream_url = f"http://{esp32_ip}:81/stream"
                    logging.info(f"Trying direct ESP32 stream: {stream_url}")
                    response = requests.get(stream_url, stream=True, timeout=5)
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            yield chunk
                    return
                except Exception as e:
                    logging.error(f"Direct ESP32 failed: {e}")
            
            # No stream available
            yield b"--frame\r\nContent-Type: text/plain\r\n\r\nNo camera stream available. Please register an ngrok URL.\r\n"
        
        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame',
                       headers={
                           'Access-Control-Allow-Origin': '*',
                           'Cache-Control': 'no-cache'
                       })
    except Exception as e:
        logging.error(f"Stream proxy error: {e}")
        return Response(f"Stream error: {str(e)}", status=500)

@app.route('/local_stream_proxy')
@login_required 
def local_stream_proxy():
    """Proxy stream from local camera proxy server"""
    try:
        def generate():
            stream_url = f"{local_proxy_url}/stream"
            response = requests.get(stream_url, stream=True, timeout=10)
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk
        
        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        logging.error(f"Local stream proxy error: {e}")
        return Response(f"Local stream error: {str(e)}", status=500)

def create_attendance_table(username):
    """Create attendance table for a user"""
    table_name = f"attendance_{username}"
    query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            date DATE NOT NULL,
            time_in TIME,
            time_out TIME,
            status VARCHAR(20) DEFAULT 'present',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    db.session.execute(db.text(query))
    db.session.commit()

# Initialize database
def init_database():
    """Initialize database tables and create admin user"""
    with app.app_context():
        try:
            db.create_all()
            logging.info("Database tables created successfully")
            
            # Create admin user if not exists
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    email='admin@unisync.edu',
                    password_hash=generate_password_hash('admin123'),
                    role='admin'
                )
                db.session.add(admin_user)
                db.session.commit()
                logging.info("Admin user created: admin/admin123")
            else:
                logging.info("Admin user already exists")
                
            # Create upload folder if it doesn't exist
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            logging.info("Upload folder initialized")
            
        except Exception as e:
            logging.error(f"Error initializing database: {e}")

# Initialize on startup
init_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
