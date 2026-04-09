# routes/auth_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from database.mongo import users_collection
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

auth_bp = Blueprint("auth", __name__)

ALLOWED_ROLES = ["student", "warden", "security"]  # Only these roles are allowed

# -------------------- Registration --------------------
@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json(force=True)
        username = data.get("username", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        role = data.get("role", "student").strip().lower()  # default role: student

        # Validate input
        if not username or not email or not password:
            return jsonify({"msg": "All fields are required"}), 400

        # Validate role
        if role not in ALLOWED_ROLES:
            return jsonify({"msg": f"Role must be one of {ALLOWED_ROLES}"}), 400

        # Check if user already exists
        if users_collection.find_one({"email": email}):
            return jsonify({"msg": "Email already exists"}), 400

        # Hash password and save user
        hashed_password = generate_password_hash(password)
        users_collection.insert_one({
            "username": username,
            "email": email,
            "password": hashed_password,
            "role": role
        })

        return jsonify({"msg": "User registered successfully"}), 201

    except Exception as e:
        return jsonify({"msg": "Error during registration", "error": str(e)}), 500


# -------------------- Login --------------------
# routes/auth_routes.py

@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(force=True)
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not email or not password:
            return jsonify({"msg": "Email and password required"}), 400

        user = users_collection.find_one({"email": email})
        if not user:
            return jsonify({"msg": "User not found"}), 404

        if not check_password_hash(user["password"], password):
            return jsonify({"msg": "Invalid credentials"}), 401

        role = user.get("role", "student")

        access_token = create_access_token(
            identity=str(user["_id"]),
            additional_claims={"role": role},
            expires_delta=timedelta(hours=1)
        )

        # UPDATED: We now send the full user object including the username
        return jsonify({
            "msg": "Login successful",
            "access_token": access_token,
            "role": role,
            "user": {
                "username": user.get("username", "Unknown"),
                "email": user.get("email"),
                "role": role
            }
        }), 200

    except Exception as e:
        return jsonify({"msg": "Error during login", "error": str(e)}), 500