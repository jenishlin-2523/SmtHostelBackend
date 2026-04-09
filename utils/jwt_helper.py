import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from extensions import db

SECRET_KEY = os.getenv("JWT_SECRET", "secret123")

def generate_jwt(user_id, role):
    payload = {
        "user_id": str(user_id),
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=2)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def token_required(allowed_roles=[]):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = request.headers.get("Authorization")
            if not token:
                return jsonify({"error": "Token is missing"}), 401

            if "Bearer " in token:
                token = token.split(" ")[1]

            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401

            if allowed_roles and payload["role"] not in allowed_roles:
                return jsonify({"error": "Unauthorized role"}), 403

            request.user = payload
            return f(*args, **kwargs)
        return wrapper
    return decorator
