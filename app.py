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

