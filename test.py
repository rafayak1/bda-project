from flask import Flask, request, jsonify
import bcrypt
import jwt
import datetime

app = Flask(__name__)
app.secret_key = "MY_KEY"

# Dummy user storage
users = {}

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    name, email, password = data.get('name'), data.get('email'), data.get('password')

    if email in users:
        return jsonify({"message": "User already exists"}), 400

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    users[email] = {
        'name': name,
        'password': hashed_password
    }
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email, password = data.get('email'), data.get('password')

    user = users.get(email)
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
        token = jwt.encode(
            {"email": email, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
            app.secret_key, algorithm="HS256"
        )
        return jsonify({"message": "Login successful", "token": token}), 200

    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/logout', methods=['POST'])
def logout():
    return jsonify({"message": "Logged out successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)
