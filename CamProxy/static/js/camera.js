/**
 * Camera Stream Management JavaScript
 * Handles camera stream viewing, status monitoring, and controls
 */

class CameraManager {
    constructor() {
        this.isStreaming = false;
        this.refreshInterval = null;
        this.statusInterval = null;
        this.currentStreamSource = 'proxy';
        
        this.initializeElements();
        this.bindEvents();
        this.startStatusMonitoring();
    }
    
    initializeElements() {
        this.streamImage = document.getElementById('camera-stream');
        this.streamPlaceholder = document.getElementById('stream-placeholder');
        this.toggleStreamBtn = document.getElementById('toggle-stream');
        this.refreshStatusBtn = document.getElementById('refresh-status');
        this.testCameraBtn = document.getElementById('test-camera');
        this.fullscreenBtn = document.getElementById('fullscreen-btn');
        this.streamSourceSelect = document.getElementById('stream-source');
        this.refreshRateSelect = document.getElementById('refresh-rate');
        this.cameraStatusElement = document.getElementById('camera-status');
        this.streamUrlElement = document.getElementById('stream-url');
        this.autoDetectNgrokBtn = document.getElementById('auto-detect-ngrok');
        this.registerNgrokBtn = document.getElementById('register-ngrok');
        this.clearNgrokBtn = document.getElementById('clear-ngrok');
        this.ngrokUrlInput = document.getElementById('ngrok-url-input');
        this.errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
    }
    
    bindEvents() {
        this.toggleStreamBtn?.addEventListener('click', () => this.toggleStream());
        this.refreshStatusBtn?.addEventListener('click', () => this.refreshStatus());
        this.testCameraBtn?.addEventListener('click', () => this.testCamera());
        this.fullscreenBtn?.addEventListener('click', () => this.toggleFullscreen());
        this.streamSourceSelect?.addEventListener('change', (e) => this.changeStreamSource(e.target.value));
        this.refreshRateSelect?.addEventListener('change', (e) => this.setRefreshRate(parseInt(e.target.value)));
        this.autoDetectNgrokBtn?.addEventListener('click', () => this.autoDetectNgrok());
        this.registerNgrokBtn?.addEventListener('click', () => this.registerNgrok());
        this.clearNgrokBtn?.addEventListener('click', () => this.clearNgrok());
        
        // Handle stream image errors
        this.streamImage?.addEventListener('error', () => this.handleStreamError());
        this.streamImage?.addEventListener('load', () => this.handleStreamLoad());
    }
    
    async toggleStream() {
        if (this.isStreaming) {
            this.stopStream();
        } else {
            await this.startStream();
        }
    }
    
    async startStream() {
        try {
            this.updateToggleButton('loading');
            
            const streamUrl = await this.getStreamUrl();
            if (!streamUrl) {
                throw new Error('No stream URL available');
            }
            
            this.streamImage.src = streamUrl;
            this.streamPlaceholder.classList.add('d-none');
            this.streamImage.classList.remove('d-none');
            
            this.isStreaming = true;
            this.updateToggleButton('stop');
            
            // Set up auto-refresh if enabled
            const refreshRate = parseInt(this.refreshRateSelect?.value || 0);
            if (refreshRate > 0) {
                this.setRefreshRate(refreshRate);
            }
            
        } catch (error) {
            console.error('Error starting stream:', error);
            this.showError(`Failed to start stream: ${error.message}`);
            this.updateToggleButton('start');
        }
    }
    
    stopStream() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        
        this.streamImage.src = '';
        this.streamImage.classList.add('d-none');
        this.streamPlaceholder.classList.remove('d-none');
        
        this.isStreaming = false;
        this.updateToggleButton('start');
    }
    
    async getStreamUrl() {
        switch (this.currentStreamSource) {
            case 'proxy':
                return '/stream_proxy';
            case 'local':
                return '/local_stream_proxy';
            case 'ngrok':
                // Get ngrok URL from server
                try {
                    const response = await fetch('/api/camera_status');
                    const data = await response.json();
                    return data.stream_url ? `${data.stream_url}/stream` : null;
                } catch (error) {
                    console.error('Error getting ngrok URL:', error);
                    return null;
                }
            default:
                return '/stream_proxy';
        }
    }
    
    changeStreamSource(source) {
        this.currentStreamSource = source;
        if (this.isStreaming) {
            // Restart stream with new source
            this.stopStream();
            setTimeout(() => this.startStream(), 500);
        }
    }
    
    setRefreshRate(seconds) {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        
        if (seconds > 0 && this.isStreaming) {
            this.refreshInterval = setInterval(() => {
                if (this.isStreaming) {
                    // Force refresh by adding timestamp
                    const currentSrc = this.streamImage.src;
                    const separator = currentSrc.includes('?') ? '&' : '?';
                    this.streamImage.src = `${currentSrc}${separator}t=${Date.now()}`;
                }
            }, seconds * 1000);
        }
    }
    
    async refreshStatus() {
        try {
            this.refreshStatusBtn.disabled = true;
            this.refreshStatusBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
            
            const response = await fetch('/api/camera_status');
            const data = await response.json();
            
            this.updateStatus(data.status, data.stream_url);
            
        } catch (error) {
            console.error('Error refreshing status:', error);
            this.showError('Failed to refresh camera status');
        } finally {
            this.refreshStatusBtn.disabled = false;
            this.refreshStatusBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh Status';
        }
    }
    
    async testCamera() {
        try {
            this.testCameraBtn.disabled = true;
            this.testCameraBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
            
            const response = await fetch('/api/test_camera');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showSuccess('Camera test successful! Camera is accessible.');
            } else {
                this.showError(`Camera test failed: ${data.message}`);
            }
            
        } catch (error) {
            console.error('Error testing camera:', error);
            this.showError('Failed to test camera connection');
        } finally {
            this.testCameraBtn.disabled = false;
            this.testCameraBtn.innerHTML = '<i class="fas fa-camera"></i> Test Camera';
        }
    }
    
    toggleFullscreen() {
        if (!this.streamImage.classList.contains('d-none')) {
            if (document.fullscreenElement) {
                document.exitFullscreen();
            } else {
                this.streamImage.requestFullscreen().catch(err => {
                    console.error('Error entering fullscreen:', err);
                });
            }
        }
    }
    
    handleStreamError() {
        console.error('Stream error occurred');
        this.streamImage.classList.add('d-none');
        this.streamPlaceholder.classList.remove('d-none');
        
        if (this.isStreaming) {
            // Try to reconnect after a delay
            setTimeout(() => {
                if (this.isStreaming) {
                    this.startStream();
                }
            }, 5000);
        }
    }
    
    handleStreamLoad() {
        console.log('Stream loaded successfully');
    }
    
    updateToggleButton(state) {
        if (!this.toggleStreamBtn) return;
        
        switch (state) {
            case 'start':
                this.toggleStreamBtn.innerHTML = '<i class="fas fa-play"></i> Start Stream';
                this.toggleStreamBtn.className = 'btn btn-sm btn-outline-primary me-2';
                this.toggleStreamBtn.disabled = false;
                break;
            case 'stop':
                this.toggleStreamBtn.innerHTML = '<i class="fas fa-stop"></i> Stop Stream';
                this.toggleStreamBtn.className = 'btn btn-sm btn-outline-danger me-2';
                this.toggleStreamBtn.disabled = false;
                break;
            case 'loading':
                this.toggleStreamBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
                this.toggleStreamBtn.disabled = true;
                break;
        }
    }
    
    updateStatus(status, streamUrl) {
        if (this.cameraStatusElement) {
            this.cameraStatusElement.textContent = status;
            this.cameraStatusElement.className = `badge ${this.getStatusClass(status)}`;
        }
        
        if (this.streamUrlElement) {
            this.streamUrlElement.textContent = streamUrl || 'Not available';
        }
    }
    
    getStatusClass(status) {
        switch (status) {
            case 'Connected': return 'bg-success';
            case 'Disconnected': return 'bg-danger';
            default: return 'bg-warning';
        }
    }
    
    startStatusMonitoring() {
        // Check status every 30 seconds
        this.statusInterval = setInterval(() => {
            this.refreshStatus();
        }, 30000);
    }
    
    showError(message) {
        document.getElementById('error-message').textContent = message;
        this.errorModal.show();
    }
    
    async autoDetectNgrok() {
        try {
            this.autoDetectNgrokBtn.disabled = true;
            this.autoDetectNgrokBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Detecting...';
            
            const response = await fetch('/api/auto_detect_ngrok');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showSuccess(`Ngrok tunnel detected: ${data.base_url}`);
                this.updateStatus('Connected via Ngrok', data.stream_url);
            } else {
                this.showError(`Auto-detection failed: ${data.message}`);
            }
            
        } catch (error) {
            console.error('Error auto-detecting ngrok:', error);
            this.showError('Failed to auto-detect ngrok tunnel');
        } finally {
            this.autoDetectNgrokBtn.disabled = false;
            this.autoDetectNgrokBtn.innerHTML = '<i class="fas fa-search"></i> Auto-Detect Ngrok';
        }
    }
    
    async registerNgrok() {
        const ngrokUrl = this.ngrokUrlInput?.value?.trim();
        
        if (!ngrokUrl) {
            this.showError('Please enter a valid ngrok URL');
            return;
        }
        
        try {
            this.registerNgrokBtn.disabled = true;
            this.registerNgrokBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Registering...';
            
            const response = await fetch('/api/register_ngrok', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ngrok_url: ngrokUrl
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showSuccess(`Ngrok URL registered: ${data.base_url}`);
                this.updateStatus('Connected via Ngrok', data.stream_url);
                this.ngrokUrlInput.value = '';
            } else {
                this.showError(`Registration failed: ${data.message}`);
            }
            
        } catch (error) {
            console.error('Error registering ngrok:', error);
            this.showError('Failed to register ngrok URL');
        } finally {
            this.registerNgrokBtn.disabled = false;
            this.registerNgrokBtn.innerHTML = '<i class="fas fa-plus"></i> Register';
        }
    }
    
    async clearNgrok() {
        try {
            const response = await fetch('/api/register_ngrok', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ngrok_url: ''
                })
            });
            
            this.showSuccess('Ngrok configuration cleared');
            this.updateStatus('Disconnected', null);
            
        } catch (error) {
            console.error('Error clearing ngrok:', error);
            this.showError('Failed to clear ngrok configuration');
        }
    }

    showSuccess(message) {
        // Create a temporary success alert
        const alert = document.createElement('div');
        alert.className = 'alert alert-success alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
        alert.style.zIndex = '9999';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 5000);
    }
    
    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
        }
    }
}

// Initialize camera manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.cameraManager = new CameraManager();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.cameraManager) {
        window.cameraManager.destroy();
    }
});
