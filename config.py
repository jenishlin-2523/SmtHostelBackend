# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB URI
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# JWT secret key
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key")

# Frontend URL (for CORS) — update this in Render env vars after Vercel deploy
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://smthostelmanagement.vercel.app")
