from flask import Flask, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from google.cloud import firestore, storage
import os
from dotenv import load_dotenv
import re
import pandas as pd
from io import BytesIO
import jwt
import datetime
from functools import wraps
from flask_cors import CORS
import uuid
import bcrypt  
from flask_mail import Mail, Message  

# Initialize Flask app
app = Flask(__name__)

#CORS(app, supports_credentials=True, origins="http://localhost:5173/")
CORS(app, supports_credentials=True, resources={r"/signup": {"origins": "http://localhost:5173"}})
CORS(app, supports_credentials=True, resources={r"/login": {"origins": "http://localhost:5173"}})
CORS(app, supports_credentials=True, resources={r"/forgot-password": {"origins": "http://localhost:5173"}})
CORS(app, supports_credentials=True, resources={r"/upload": {"origins": "http://localhost:5173"}})

load_dotenv()
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise ValueError("SECRET_KEY is not set. Please ensure it's in your .env file.")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp-key.json"
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True

app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT", 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")

mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

firestore_client = firestore.Client()
storage_client = storage.Client()

def sanitize_bucket_name(name):
    unique_id = str(uuid.uuid4())[:8]  
    sanitized_name = re.sub(r'[^a-z0-9-]', '-', name.lower().strip('-'))[:55]  
    return f"{sanitized_name}-{unique_id}"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"message": "Token is missing"}), 401

        try:
            token = token.split(" ")[1]  
            data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
            request.user_id = data['user_id'] 
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Token is invalid"}), 401
        except Exception as e:
            return jsonify({"message": f"An error occurred: {str(e)}"}), 401

        return f(*args, **kwargs)

    return decorated

class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email
        
    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    user_doc = firestore_client.collection('users').document(user_id).get()
    if user_doc.exists:
        data = user_doc.to_dict()
        return User(id=user_id, email=data['email'])
    return None

@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"message": "User is not authenticated"}), 401

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    print(data)
    name, email, password = data.get('name'), data.get('email'), data.get('password')

    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return jsonify({"message": "Invalid email format. Please provide a valid email address."}), 400

    users_ref = firestore_client.collection('users')
    existing_user = users_ref.where('email', '==', email).get()
    if existing_user:
        return jsonify({"message": "User already exists"}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    sanitized_bucket_name = sanitize_bucket_name(f"{name}-bucket")

    user_doc = users_ref.document()
    user_id = user_doc.id
    user_doc.set({
        'name': name,
        'email': email,
        'password': hashed_password.decode('utf-8'), 
        'bucket': sanitized_bucket_name,
        'id': user_id
    })

    try:
        bucket = storage_client.create_bucket(sanitized_bucket_name)
        bucket.storage_class = "STANDARD"
        bucket.update()
        print(f"{sanitized_bucket_name} created.")
    except Exception as e:
        print(f"Error creating bucket: {e}")
        return jsonify({"message": "Failed to create bucket"}), 500

    return jsonify({"message": "User registered successfully", "bucket": sanitized_bucket_name}), 201

@app.route('/google-signup', methods=['POST'])
def google_signup():
    data = request.json
    print(data)
    
    name, email, uid = data.get('name'), data.get('email'), data.get('uid')

    if not name or not email or not uid:
        return jsonify({"message": "Missing required fields"}), 400

    # Validate email format
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return jsonify({"message": "Invalid email format"}), 400

    users_ref = firestore_client.collection('users')
    existing_user = users_ref.where('email', '==', email).get()
    if existing_user:
        return jsonify({"message": "User already exists"}), 400

    sanitized_bucket_name = sanitize_bucket_name(f"{name}-bucket")

    user_doc = users_ref.document()
    user_id = user_doc.id
    user_doc.set({
        'name': name,
        'email': email,
        'auth_provider': 'google',
        'uid': uid,
        'bucket': sanitized_bucket_name,
        'id': user_id
    })

    try:
        bucket = storage_client.create_bucket(sanitized_bucket_name)
        bucket.storage_class = "STANDARD"
        bucket.update()
        print(f"{sanitized_bucket_name} created.")
    except Exception as e:
        print(f"Error creating bucket: {e}")
        return jsonify({"message": "Failed to create bucket"}), 500

    return jsonify({"message": "Google user registered successfully", "bucket": sanitized_bucket_name}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    print(data)
    email, password = data.get('email'), data.get('password')
    
    user_doc = firestore_client.collection('users').where('email', '==', email).get()
    if user_doc:
        user_data = user_doc[0].to_dict()
        
        if bcrypt.checkpw(password.encode('utf-8'), user_data['password'].encode('utf-8')):
            token = jwt.encode(
                {"user_id": user_doc[0].id, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
                app.secret_key, algorithm="HS256"
            )
            return jsonify({"message": "Login successful", "token": token}), 200
        else:
            return jsonify({"message": "Invalid credentials"}), 401

    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email')

    users_ref = firestore_client.collection('users')
    user_docs = users_ref.where('email', '==', email).get()

    if not user_docs:
        return jsonify({"message": "Email not found"}), 404

    user_doc = user_docs[0]
    user_id = user_doc.id

    reset_token = jwt.encode(
        {"user_id": user_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
        app.secret_key, algorithm="HS256"
    )

    users_ref.document(user_id).update({
        "reset_token": reset_token,
        "reset_token_expiry": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    })

    frontend_url = "http://localhost:3000/reset-password?token=" + reset_token 

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

        user_ref = firestore_client.collection('users').document(user_id)
        user_data = user_ref.get().to_dict()

        if not user_data or 'reset_token' not in user_data or user_data['reset_token'] != token:
            return jsonify({"message": "Invalid or expired token"}), 400

        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

        user_ref.update({
            "password": hashed_password.decode('utf-8'),
            "reset_token": None  # Remove reset token after use
        })

        return jsonify({"message": "Password updated successfully"}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token has expired"}), 400
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 400
    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

# @app.route('/upload', methods=['POST'])
# @token_required
# def upload_dataset():
#     # if 'file' not in request.files or 'file_type' not in request.form:
#     #     return jsonify({"message": "File and file type are required"}), 400

#     file, file_type = request.files['file'], request.form.get('file_type').lower()
#     user_ref = firestore_client.collection('users').document(request.user_id)
#     user_data = user_ref.get().to_dict()
#     user_bucket_name = user_data.get('bucket')

#     if not user_bucket_name:
#         return jsonify({"message": "User bucket not found"}), 400

#     filename = file.filename
#     try:
#         # Check if a dataset already exists
#         existing_dataset = user_data.get('dataset')
#         bucket = storage_client.get_bucket(user_bucket_name)

#         # If an existing dataset exists, delete it
#         if existing_dataset:
#             existing_blob = bucket.blob(existing_dataset)
#             if existing_blob.exists():
#                 existing_blob.delete()
#                 print(f"Deleted existing dataset: {existing_dataset}")

#         # Upload the new dataset
#         blob = bucket.blob(filename)
#         blob.upload_from_file(file)
#         print(f"Uploaded new dataset: {filename}")

#         # Verify the dataset structure
#         file_path = f"/tmp/{filename}"
#         blob.download_to_filename(file_path)
#         delimiter = ',' if file_type == 'csv' else '\t'
#         pd.read_csv(file_path, delimiter=delimiter, nrows=5)

#         # Update Firestore with the new dataset information
#         user_ref.update({'dataset': filename, 'file_type': file_type})
#         return jsonify({"message": "File uploaded successfully", "dataset": filename}), 201

#     except Exception as e:
#         print(f"Error uploading file: {e}")
#         return jsonify({"message": f"Failed to upload dataset: {e}"}), 500

@app.route('/upload', methods=['POST'])
@token_required
def upload_dataset():
    print(request.files)
    if 'file' not in request.files:
        return jsonify({"message": "File is required"}), 400

    file = request.files['file']
    filename = file.filename

    if not filename:
        return jsonify({"message": "Filename is missing"}), 400

    user_ref = firestore_client.collection('users').document(request.user_id)
    user_data = user_ref.get().to_dict()
    user_bucket_name = user_data.get('bucket')

    if not user_bucket_name:
        return jsonify({"message": "User bucket not found"}), 400

    try:
        bucket = storage_client.get_bucket(user_bucket_name)

        # Delete existing dataset if present
        existing_dataset = user_data.get('dataset')
        if existing_dataset:
            existing_blob = bucket.blob(existing_dataset)
            if existing_blob.exists():
                existing_blob.delete()
                print(f"Deleted existing dataset: {existing_dataset}")

        # Upload the new file
        blob = bucket.blob(filename)
        blob.upload_from_file(file)
        print(f"Uploaded file: {filename}")

        # Handle CSV-specific validation
        if filename.lower().endswith('.csv'):
            file_path = f"/tmp/{filename}"
            blob.download_to_filename(file_path)
            try:
                pd.read_csv(file_path, nrows=5)  # validate structure
                user_ref.update({'dataset': filename, 'file_type': 'csv'})
            except Exception as e:
                return jsonify({"message": f"File uploaded, but CSV validation failed: {str(e)}"}), 400
        else:
            user_ref.update({'dataset': filename, 'file_type': 'other'})

        return jsonify({"message": "File uploaded successfully", "filename": filename}), 201

    except Exception as e:
        print(f"Error uploading file: {e}")
        return jsonify({"message": f"Failed to upload file: {str(e)}"}), 500
    

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200

# Transformation endpoint
@app.route('/transform', methods=['POST'])
@token_required
def transform_dataset():
    """
    Perform transformations or provide metadata about the dataset based on user commands.
    """
    try:
        # Retrieve request data
        user_id = request.user_id
        data = request.json
        command = data.get("command")
        if not command:
            return jsonify({"message": "No command provided"}), 400

        # Retrieve dataset information
        user_ref = firestore_client.collection('users').document(user_id)
        user_data = user_ref.get().to_dict()
        bucket_name = user_data.get('bucket')
        current_dataset = user_data.get('dataset')
        file_type = user_data.get('file_type', 'csv')

        if not current_dataset:
            return jsonify({"message": "No dataset found. Please upload a dataset first."}), 400

        if command.lower() == "yes":
            # Switch to the updated dataset
            new_dataset_name = user_data.get('updated_dataset')
            if not new_dataset_name:
                return jsonify({"message": "No updated dataset found. Please apply a transformation first."}), 400

            # Set the updated dataset as the current dataset and delete the old one
            try:
                bucket = storage_client.get_bucket(bucket_name)
                old_blob = bucket.blob(current_dataset)
                if old_blob.exists():
                    old_blob.delete()  # Delete old dataset
                    print(f"Deleted old dataset: {current_dataset}")

                # Update Firestore with the new dataset information
                user_ref.update({'dataset': new_dataset_name, 'updated_dataset': None})
                return jsonify({"message": "Using updated dataset for further transformations."}), 200
            except Exception as e:
                return jsonify({"message": f"Failed to switch to updated dataset: {e}"}), 500

        if command.lower() == "no":
            return jsonify({"message": "Continuing with the original dataset for transformations."}), 200

        # Load the dataset
        dataset_to_use = user_data.get('updated_dataset') if user_data.get('updated_dataset') else current_dataset
        delimiter = ',' if file_type == 'csv' else '\t'
        df = load_dataset(bucket_name, dataset_to_use, delimiter=delimiter)

        # Handle metadata commands
        if command.lower() == "columns":
            column_list = df.columns.tolist()
            pretty_columns = "\n".join([f"● {col}" for col in column_list])
            return jsonify({"message": f"Dataset Columns:\n{pretty_columns}"}), 200

        if command.lower() == "size":
            dimensions = f"Rows: {df.shape[0]}, Columns: {df.shape[1]}"
            return jsonify({"message": f"Dataset Dimensions:\n{dimensions}"}), 200

        # Apply transformations
        try:
            transformed_df = apply_predefined_transformation(df, command)
            transformed_dataset_name = f"transformed_{current_dataset}"
            save_dataset(bucket_name, transformed_dataset_name, transformed_df)

            # Update Firestore with the new transformed dataset
            user_ref.update({'updated_dataset': transformed_dataset_name})

            # Generate download link
            bucket = storage_client.get_bucket(bucket_name)
            blob = bucket.blob(transformed_dataset_name)
            download_url = blob.generate_signed_url(expiration=datetime.timedelta(hours=1))

            return jsonify({
                "message": "Transformation applied successfully.",
                "download_url": download_url,
                "followup_message": "Do you want to use this updated dataset for further transformations? Reply with yes or no."
            }), 200

        except ValueError as ve:
            supported_commands = (
                "Unsupported command.\n\n"
                "Supported Commands:\n"
                "● remove column <column_name>\n"
                "  Example: remove column Age\n"
                "● rename column <old_name> to <new_name>\n"
                "  Example: rename column Age to Years\n"
                "● filter rows where <condition>\n"
                "  Example: filter rows where Age > 25\n"
                "● columns\n"
                "  Example: columns (to list all column names)\n"
                "● size\n"
                "  Example: size (to get the dataset dimensions)\n"
                "● change dataset\n"
            "  Example: change dataset (to upload or replace your dataset)\n"
            )
            return jsonify({"message": f"{ve}\n\n{supported_commands}"}), 400

    except Exception as e:
        print(f"Error in transform_dataset: {e}")
        return jsonify({"message": f"Error: {str(e)}"}), 500


def apply_predefined_transformation(df, command):
    """
    Apply supported transformations to the dataframe.
    """
    supported_commands = ""
    if command.startswith("remove column"):
        column = command.split("remove column")[-1].strip()
        if column in df.columns:
            df = df.drop(columns=[column])
        else:
            raise ValueError(f"Column '{column}' does not exist in the dataset.")
    elif command.startswith("rename column"):
        parts = command.split("rename column")[-1].strip().split("to")
        if len(parts) == 2:
            old_name, new_name = parts[0].strip(), parts[1].strip()
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})
            else:
                raise ValueError(f"Column '{old_name}' does not exist in the dataset.")
        else:
            raise ValueError("Invalid rename command. Use 'rename column <old_name> to <new_name>'.")
    elif command.startswith("filter rows where"):
        condition = command.split("filter rows where")[-1].strip()
        try:
            df = df.query(condition)
        except Exception as e:
            raise ValueError(f"Error in filter condition: {e}")
    else:
        raise ValueError(supported_commands)
    # return df
    if command.startswith("remove column"):
        column = command.split("remove column")[-1].strip()
        if column in df.columns:
            df = df.drop(columns=[column])
        else:
            raise ValueError(f"Column '{column}' does not exist in the dataset.")
    elif command.startswith("rename column"):
        parts = command.split("rename column")[-1].strip().split("to")
        if len(parts) == 2:
            old_name, new_name = parts[0].strip(), parts[1].strip()
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})
            else:
                raise ValueError(f"Column '{old_name}' does not exist in the dataset.")
        else:
            raise ValueError("Invalid rename command. Use rename column <old_name> to <new_name>.")
    elif command.startswith("filter rows where"):
        condition = command.split("filter rows where")[-1].strip()
        try:
            df = df.query(condition)
        except Exception as e:
            raise ValueError(f"Error in filter condition: {e}")
    else:
        raise ValueError(supported_commands)
    return df

@app.route('/replace-dataset', methods=['POST'])
@token_required
def replace_dataset():
    if 'file' not in request.files or 'file_type' not in request.form:
        return jsonify({"message": "File and file type are required"}), 400

    file, file_type = request.files['file'], request.form.get('file_type').lower()
    user_ref = firestore_client.collection('users').document(request.user_id)
    user_data = user_ref.get().to_dict()
    user_bucket_name = user_data.get('bucket')

    if not user_bucket_name:
        return jsonify({"message": "User bucket not found"}), 400

    filename = file.filename
    try:
        bucket = storage_client.get_bucket(user_bucket_name)

        existing_dataset = user_data.get('dataset')
        if existing_dataset:
            bucket.blob(existing_dataset).delete()

        blob = bucket.blob(filename)
        blob.upload_from_file(file)
        file_path = f"/tmp/{filename}"
        blob.download_to_filename(file_path)

        delimiter = ',' if file_type == 'csv' else '\t'
        pd.read_csv(file_path, delimiter=delimiter, nrows=5)

        user_ref.update({'dataset': filename, 'file_type': file_type})

        return jsonify({"message": "Dataset replaced successfully!"}), 200

    except Exception as e:
        print(f"Error replacing dataset: {e}")
        return jsonify({"message": f"Failed to replace dataset: {e}"}), 500


@app.route('/chat', methods=['GET'])
@token_required
def chat_welcome():
    """
    Welcome message for the chat. Includes a description and the list of supported commands.
    """
    try:
        welcome_message = (
            "Welcome to Intelligent Service! Upload your dataset and perform transformations effortlessly.\n\n"
            "Supported Commands:\n"
            "● remove column <column_name>\n"
            "  Example: remove column Age\n"
            "● rename column <old_name> to <new_name>\n"
            "  Example: rename column Age to Years\n"
            "● filter rows where <condition>\n"
            "  Example: filter rows where Age > 25\n"
            "● columns\n"
            "  Example: columns (to list all column names)\n"
            "● size\n"
            "  Example: size (to get the dataset dimensions)\n"
            "● change dataset\n"
            "  Example: change dataset (to upload or replace your dataset)\n"
        )
        return jsonify({"message": welcome_message}), 200
    except Exception as e:
        print(f"Error in chat_welcome: {e}")
        return jsonify({"message": f"Error: {str(e)}"}), 500

def load_dataset(bucket_name, dataset_name, delimiter=','):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(dataset_name)
    file_path = f"/tmp/{dataset_name}"
    blob.download_to_filename(file_path)
    return pd.read_csv(file_path, delimiter=delimiter)

def save_dataset(bucket_name, dataset_name, dataframe):
    bucket = storage_client.bucket(bucket_name)
    file_path = f"/tmp/{dataset_name}"
    dataframe.to_csv(file_path, index=False)
    blob = bucket.blob(dataset_name)
    blob.upload_from_filename(file_path)

if __name__ == '__main__':
    app.run(debug=True)
