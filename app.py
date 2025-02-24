from flask import Flask, request, jsonify
import os
import jwt
import datetime
from flask_mail import Mail, Message
from dotenv import load_dotenv
import bcrypt  

app = Flask(__name__)
load_dotenv()

app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise ValueError("SECRET_KEY is not set. Please ensure it's in your .env file.")

app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT", 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")

mail = Mail(app)

users_db = {
    "test@example.com": {
        "id": "user123",
        "email": "test@example.com",
        "password": bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "reset_token": None  # Reset token will be stored temporarily
    }
}

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email')

    user = users_db.get(email)
    if not user:
        return jsonify({"message": "Email not found"}), 404
    
    reset_token = jwt.encode(
        {"user_id": user["id"], "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
        app.secret_key, algorithm="HS256"
    )

    users_db[email]["reset_token"] = reset_token

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
        return jsonify({"message": "Password reset link sent to your email"}), 200
    except Exception as e:
        return jsonify({"error": "Failed to send email", "details": str(e)}), 500
    
@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    token = data.get('token')
    new_password = data.get('newPassword')

    if not token or not new_password:
        return jsonify({"message": "Token and new password are required"}), 400

    try:
        decoded_token = jwt.decode(token, app.secret_key, algorithms=["HS256"])
        user_id = decoded_token['user_id']

        user = next((u for u in users_db.values() if u["id"] == user_id), None)

        if not user or user["reset_token"] != token:
            return jsonify({"message": "Invalid or expired token"}), 400

        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        user["password"] = hashed_password
        user["reset_token"] = None  

        return jsonify({"message": "Password updated successfully"}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token has expired"}), 400
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 400
    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)

    
