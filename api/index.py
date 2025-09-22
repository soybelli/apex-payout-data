import os
import sys
from pathlib import Path

# Add parent directory to path to import app
sys.path.append(str(Path(__file__).parent.parent))

from flask import Flask, render_template_string
import subprocess
import threading
import time
import requests

app = Flask(__name__)

# Streamlit process
streamlit_process = None

def start_streamlit():
    global streamlit_process
    if streamlit_process is None or streamlit_process.poll() is not None:
        # Start Streamlit in background
        streamlit_process = subprocess.Popen([
            'streamlit', 'run', '../app.py',
            '--server.port=8501',
            '--server.address=0.0.0.0',
            '--server.headless=true'
        ], cwd=os.path.dirname(__file__))

# Start Streamlit when module loads
start_streamlit()

@app.route('/')
def home():
    # Wait a moment for Streamlit to start
    time.sleep(2)
    
    # Try to proxy to Streamlit
    try:
        response = requests.get('http://localhost:8501', timeout=5)
        return response.text
    except:
        return """
        <html>
        <head><title>Apex Payouts Analytics</title></head>
        <body>
            <h1>Apex Payouts Analytics</h1>
            <p>Starting Streamlit app...</p>
            <p>If this page doesn't load, please check the logs.</p>
            <script>
                setTimeout(() => location.reload(), 3000);
            </script>
        </body>
        </html>
        """

@app.route('/health')
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
