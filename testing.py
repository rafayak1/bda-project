import pytest
import json
import sys
import os
import jwt
import datetime
import bcrypt

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/..")) 

from app import app, users_db, mail

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_forgot_password_valid_email(client, mocker):
    mock_mail = mocker.patch("app.mail.send")

    response = client.post('/forgot-password', json={"email": "test@example.com"})

    assert response.status_code == 200
    assert "Password reset link sent" in response.json["message"]

    mock_mail.assert_called_once()

def test_forgot_password_invalid_email(client):
    response = client.post('/forgot-password', json={"email": "invalid@example.com"})

    assert response.status_code == 404
    assert "Email not found" in response.json["message"]

def test_reset_password_valid_token(client, mocker):
    secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")

    valid_token = jwt.encode(
        {"user_id": "user123", "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
        secret_key,
        algorithm="HS256"
    )

    users_db["test@example.com"]["reset_token"] = valid_token

    response = client.post('/reset-password', json={
        "token": valid_token,
        "newPassword": "newsecurepassword"
    })

    assert response.status_code == 200
    assert "Password updated successfully" in response.json["message"]

    assert bcrypt.checkpw("newsecurepassword".encode('utf-8'), users_db["test@example.com"]["password"].encode('utf-8'))

def test_reset_password_invalid_token(client):
    response = client.post('/reset-password', json={
        "token": "invalid_token",
        "newPassword": "newsecurepassword"
    })

    assert response.status_code == 400
    assert response.json["message"] in ["Invalid or expired token", "Invalid token"]