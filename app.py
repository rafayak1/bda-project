from flask import Flask, request, jsonify
import os
import jwt
import datetime
from flask_mail import Mail, Message
from dotenv import load_dotenv
import bcrypt
import re
import uuid
from google.cloud import storage

# Initialize Flask app
app = Flask(__name__)
load_dotenv()

app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise ValueError("SECRET_KEY is not set. Please ensure it's in your .env file.")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp-key.json"

# Configure Flask-Mail
app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT", 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")

mail = Mail(app)

storage_client = storage.Client()

# Simulated User Database (Replace with actual DB later)
users_db = {}

def sanitize_bucket_name(name):
    """Sanitizes bucket names to be GCP-compliant."""
    unique_id = str(uuid.uuid4())[:8]  
    sanitized_name = re.sub(r'[^a-z0-9-]', '-', name.lower().strip('-'))[:55]  
    return f"{sanitized_name}-{unique_id}"

def signup(data):
    """Registers a new user and creates a Google Cloud Storage bucket for them."""
    name, email, password = data.get('name'), data.get('email'), data.get('password')

    if email in users_db:
        return {"message": "User already exists"}, 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    bucket_name = sanitize_bucket_name(f"{name}-bucket")

    user_id = str(uuid.uuid4())
    users_db[email] = {
        "id": user_id,
        "name": name,
        "email": email,
        "password": hashed_password,
        "bucket": bucket_name
    }

    try:
        bucket = storage_client.create_bucket(bucket_name)
        bucket.storage_class = "STANDARD"
        bucket.update()
    except Exception as e:
        return {"message": f"Failed to create bucket: {e}"}, 500

    return {"message": "User registered successfully", "bucket": bucket_name}, 201

def login(data):
    """Logs in a user and returns a JWT token."""
    email, password = data.get('email'), data.get('password')

    user = users_db.get(email)
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return {"message": "Invalid credentials"}, 401

    token = jwt.encode(
        {"user_id": user["id"], "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
        app.secret_key, algorithm="HS256"
    )

    return {"message": "Login successful", "token": token}, 200

def forgot_password(data):
    """Handles forgot password and sends reset link via email."""
    email = data.get('email')

    user = users_db.get(email)
    if not user:
        return {"message": "Email not found"}, 404

    reset_token = jwt.encode(
        {"user_id": user["id"], "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
        app.secret_key, algorithm="HS256"
    )

    users_db[email]["reset_token"] = reset_token
    frontend_url = f"http://localhost:3000/reset-password?token={reset_token}"

    msg = Message("Password Reset Request",
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[email])
    msg.body = f"""
    Click the link below to reset your password:
    {frontend_url}
    
    If you did not request this, please ignore this email.
    This link expires in 1 hour.
    """

    try:
        mail.send(msg)
        return {"message": "Password reset link sent to your email"}, 200
    except Exception as e:
        return {"error": "Failed to send email", "details": str(e)}, 500

def reset_password(data):
    """Handles password reset using a valid token."""
    token = data.get('token')
    new_password = data.get('newPassword')

    if not token or not new_password:
        return {"message": "Token and new password are required"}, 400

    try:
        decoded_token = jwt.decode(token, app.secret_key, algorithms=["HS256"])
        user_id = decoded_token['user_id']

        user = next((u for u in users_db.values() if u["id"] == user_id), None)
        if not user or user["reset_token"] != token:
            return {"message": "Invalid or expired token"}, 400

        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        user["password"] = hashed_password
        user["reset_token"] = None  

        return {"message": "Password updated successfully"}, 200

    except jwt.ExpiredSignatureError:
        return {"message": "Token has expired"}, 400
    except jwt.InvalidTokenError:
        return {"message": "Invalid token"}, 400
    except Exception as e:
        return {"message": f"An error occurred: {str(e)}"}, 500

@app.route('/signup', methods=['POST'])
def signup_route():
    return jsonify(*signup(request.json))

@app.route('/login', methods=['POST'])
def login_route():
    return jsonify(*login(request.json))

@app.route('/forgot-password', methods=['POST'])
def forgot_password_route():
    return jsonify(*forgot_password(request.json))

@app.route('/reset-password', methods=['POST'])
def reset_password_route():
    return jsonify(*reset_password(request.json))

if __name__ == '__main__':
    app.run(debug=True)