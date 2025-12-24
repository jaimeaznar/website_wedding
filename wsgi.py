# wsgi.py
import os
import sys
from dotenv import load_dotenv
load_dotenv()

print(f"Starting wsgi.py, PORT={os.getenv('PORT', 'NOT SET')}", flush=True)
sys.stdout.flush()

from app import create_app

print("Importing create_app done", flush=True)

app = create_app()

print("App created, ready for gunicorn", flush=True)
sys.stdout.flush()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)