"""
Vercel Serverless Function Entrypoint
Routes all incoming HTTP requests to the FastAPI application instance.
"""
import os
import sys

# Ensure backend root directory is in the Python search path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app

# Vercel's @vercel/python runtime will pick up 'app' as the ASGI application
