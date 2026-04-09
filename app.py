from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS



from config import JWT_SECRET_KEY, FRONTEND_URL
from routes.auth_routes import auth_bp
from routes.outpass_routes import outpass_bp
import sys, os

# Ensure backend folder is in Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_app():
    app = Flask(__name__)

    # JWT config
    app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600

    # Initialize JWT
    jwt = JWTManager(app)

    # Enable CORS using FRONTEND_URL from config.py
    CORS(app, resources={r"/*": {"origins": FRONTEND_URL}})

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(outpass_bp, url_prefix="/outpass")

    @app.route("/")
    def home():
        return "Backend is running!"

    return app

# Create app instance
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
