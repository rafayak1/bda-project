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
import json
import requests
import re


# Initialize Flask app
app = Flask(__name__)

CORS(app, supports_credentials=True, origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173"
])
# CORS(app, supports_credentials=True, resources={r"/signup": {"origins": "http://localhost:5173"}})
# CORS(app, supports_credentials=True, resources={r"/login": {"origins": "http://localhost:5173"}})
# CORS(app, supports_credentials=True, resources={r"/forgot-password": {"origins": "http://localhost:5173"}})
# CORS(app, supports_credentials=True, resources={r"/reset-password": {"origins": "http://localhost:5173"}})
# CORS(app, supports_credentials=True, resources={r"/upload": {"origins": "http://localhost:5173"}})
# CORS(app, supports_credentials=True, resources={r"/transform": {"origins": "http://localhost:5173"}})
# CORS(app, supports_credentials=True, resources={r"/dataset-status": {"origins": "http://localhost:5173"}})
# CORS(app, supports_credentials=True, resources={r"/preview": {"origins": "http://localhost:5173"}})

load_dotenv()
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise ValueError("SECRET_KEY is not set. Please ensure it's in your .env file.")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp-key.json"
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

firestore_client = firestore.Client()
storage_client = storage.Client()

def is_likely_transformation(prompt: str) -> bool:
    keywords = ['remove column', 'rename column', 'filter rows', 'drop', 'convert', 'fill', 'encode', 'impute', 
                'group by', 'pivot', 'merge', 'join', 'concat', 'stack', 'unstack', 'sort', 'sample', 
                'drop duplicates', 'replace', 'map', 'apply', 'query', 'columns', 'size', 'shape',
                'head', 'tail', 'describe', 'info', 'value_counts', 'unique', 'isna', 'notna',
                'astype', 'to_datetime', 'to_numeric', 'to_string', 'to_csv', 'to_excel', 'to_json',
                'to_html', 'to_sql', 'to_dict', 'to_clipboard', 'to_feather', 'to_parquet', 'column']
    return any(kw in prompt.lower() for kw in keywords)

import requests
import os
import json

def call_openrouter(prompt, df=None, mode="transform"):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("Missing OpenRouter API key")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    if mode == "transform":
        # Add dataset context if provided
        columns = df.columns.tolist() if df is not None else []
        preview = df.head(5).to_dict(orient='records') if df is not None else []

        system_prompt = (
            "Your name is BuffBot and you are made for students of University of Colorado Boulder\n"
            "You have been created by Rafay, Samiksha, Harsh and Mohit for their Big Data Analytics Course\n"
            "You're a data scientist. Return only executable pandas code to transform a DataFrame named df.\n"
            f"Here are the columns:\n{columns}\n\n"
            f"Here is a preview:\n{preview}"
        )
        user_prompt = f"Given this command: '{prompt}', write Python pandas code to perform this on a dataframe named df."

    else:  # mode == "chat"
        columns = df.columns.tolist() if df is not None else []
        print("Columns:", columns)
        preview = df.head(5).to_dict(orient='records') if df is not None else []
        system_prompt = (
            "Your name is BuffBot and you are made for students of University of Colorado Boulder\n"
            "You have been created by Rafay, Samiksha, Harsh and Mohit for their Big Data Analytics Course\n"
            "You're an intelligent and friendly data assistant. Help users with data-related questions, "
            "and feel free to chat casually. Be helpful and conversational.\n"
            f"Here are the columns:\n{columns}\n\n"
            f"Here is a preview:\n{preview}"
        )
        user_prompt = prompt

    body = {
        "model": "openrouter/quasar-alpha",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }

    print("SENDING REQUEST:\n", json.dumps(body, indent=2))
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
    response.raise_for_status()

    result = response.json()
    return result['choices'][0]['message']['content']


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
        'id': user_id,
        'updated_dataset': None
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
        'id': user_id,
        'updated_dataset': None
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

    return jsonify({"message": "Email exists", "user_id": user_id}), 200


@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    user_id = data.get('user_id')
    new_password = data.get('newPassword')

    if not user_id or not new_password:
        return jsonify({"message": "User ID and new password are required"}), 400

    user_ref = firestore_client.collection('users').document(user_id)
    user_data = user_ref.get().to_dict()

    if not user_data:
        return jsonify({"message": "User not found"}), 404

    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user_ref.update({ "password": hashed_password })

    return jsonify({"message": "Password updated successfully"}), 200

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
                user_ref.update({
                    'dataset': filename,
                    'file_type': 'csv',
                    'updated_dataset': None  # Clear transformed version
                })
            except Exception as e:
                return jsonify({"message": f"File uploaded, but CSV validation failed: {str(e)}"}), 400
        else:
            user_ref.update({
            'dataset': filename,
            'file_type': 'other',
            'updated_dataset': None  # Clear transformed version
        })

        return jsonify({"message": "File uploaded successfully", "filename": filename}), 201

    except Exception as e:
        print(f"Error uploading file: {e}")
        return jsonify({"message": f"Failed to upload file: {str(e)}"}), 500
    

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200
def clean_ai_code(raw_code: str):
    code = re.sub(r"^```(?:python)?\s*", "", raw_code.strip(), flags=re.IGNORECASE)
    code = re.sub(r"\s*```$", "", code)
    return code.strip()
def match_column_command(cmd):
    patterns = [
        r"^(what|show|list|give|tell).*(column|columns)",
        r"^columns$"
    ]
    return any(re.search(p, cmd) for p in patterns)

def match_preview_command(cmd):
    return any(kw in cmd for kw in ["preview", "first rows", "top rows"])

def match_head_command(cmd):
    return cmd.strip() in ["head", "show rows", "show top rows"]

def match_tail_command(cmd):
    return cmd.strip() in ["tail", "show last rows"]

def match_size_command(cmd):
    return cmd.strip() in ["size", "shape", "what is the size", "how many rows"]

def match_describe_command(cmd):
    return cmd.strip() in ["describe", "info", "summary", "data summary"]

@app.route('/transform', methods=['POST'])
@token_required
def transform_dataset():
    try:
        user_id = request.user_id
        data = request.json
        command = data.get("command", "").strip()

        print(f"Received command: {command}")
        if not command:
            return jsonify({"message": "No command provided"}), 400

        # Fetch dataset info
        user_ref = firestore_client.collection('users').document(user_id)
        user_data = user_ref.get().to_dict()
        bucket_name = user_data.get('bucket')
        current_dataset = user_data.get('dataset')
        file_type = user_data.get('file_type', 'csv')

        if not current_dataset:
            return jsonify({"message": "No dataset found. Please upload a dataset first."}), 400

        # Handle dataset switching
        if command.lower() == "yes":
            new_dataset_name = user_data.get('updated_dataset')
            if not new_dataset_name:
                return jsonify({"message": "No updated dataset found. Please apply a transformation first."}), 400

            try:
                bucket = storage_client.get_bucket(bucket_name)
                old_blob = bucket.blob(current_dataset)
                if old_blob.exists():
                    old_blob.delete()
                user_ref.update({'dataset': new_dataset_name, 'updated_dataset': None})
                return jsonify({"message": "Using updated dataset for further transformations."}), 200
            except Exception as e:
                return jsonify({"message": f"Failed to switch dataset: {e}"}), 500

        if command.lower() == "no":
            user_ref.update({'updated_dataset': None})
            user_data = user_ref.get().to_dict()  # <-- important to reload dataset info
            return jsonify({"message": "Continuing with original dataset."}), 2000

        # Load the dataset
        # Check if user said no to updated dataset previously
        use_updated = user_data.get('updated_dataset') and command.lower() != "no"
        dataset_to_use = user_data.get('updated_dataset') if use_updated else current_dataset
        delimiter = ',' if file_type == 'csv' else '\t'
        df = load_dataset(bucket_name, dataset_to_use, delimiter=delimiter)

        # Smart descriptive command checks
        lower_cmd = command.lower()

        # Descriptive command handlers
        if match_column_command(lower_cmd):
            cols = df.columns.tolist()
            return jsonify({"message": "Your dataset has the following columns:\n\n" + "\n".join([f"● {col}" for col in cols])}), 200
        elif match_preview_command(lower_cmd):
            return jsonify({"message": f"Here's a preview of your dataset:\n\n{json.dumps(df.head(5).to_dict(orient='records'), indent=2)}"}), 200
        elif match_head_command(lower_cmd):
            return jsonify({"message": str(df.head().to_string(index=False))}), 200
        elif match_tail_command(lower_cmd):
            return jsonify({"message": str(df.tail().to_string(index=False))}), 200
        elif match_size_command(lower_cmd):
            return jsonify({"message": f"Dataset Dimensions: Rows: {df.shape[0]}, Columns: {df.shape[1]}"}), 200
        elif match_describe_command(lower_cmd):
            return jsonify({"message": str(df.describe(include='all').to_string())}), 200
        elif lower_cmd == "commands":
            return jsonify({"message": "Here are the commands you can use:\n\n"
                                       "● remove column <column_name>\n"
                                       "● rename column <old_name> to <new_name>\n"
                                       "● filter rows where <condition>\n"
                                       "● columns\n"
                                       "● size\n"}), 200

        # # === AI Chat (not a transformation) ===
        # if not is_likely_transformation(command):
        #     ai_response = call_openrouter(command, df, mode="chat")
        #     return jsonify({"message": ai_response}), 200

        # # === AI Code Generation ===
        # ai_code = call_openrouter(command, df, mode="transform")
        # cleaned_code = clean_ai_code(ai_code)
        # print("AI GENERATED CODE:\n", cleaned_code)

        # if not ai_code.strip() or ai_code.strip().startswith("#"):
        #     return jsonify({"message": f"Sorry, I couldn't generate code for that command:\n\n{ai_code}"}), 200

        # # Execute generated code safely
        # try:
        #     local_vars = {'df': df.copy()}
        #     exec(cleaned_code, {}, local_vars)
        #     transformed_df = local_vars['df']
        # except Exception as exec_err:
        #     return jsonify({"message": f"Failed to execute AI code:\n\n{ai_code}\n\nError: {exec_err}"}), 500

        # # Save transformed version
        # transformed_name = f"transformed_{current_dataset}"
        # save_dataset(bucket_name, transformed_name, transformed_df)
        # user_ref.update({'updated_dataset': transformed_name})

        # blob = storage_client.get_bucket(bucket_name).blob(transformed_name)
        # download_url = blob.generate_signed_url(expiration=datetime.timedelta(hours=1))

        # return jsonify({
        #     "message": "Transformation applied successfully.",
        #     "download_url": download_url,
        #     "followup_message": "Do you want to use this updated dataset for further transformations? Reply with yes or no."
        # }), 200
        # 1. Ask OpenRouter for code regardless of tone
                # 0. Check if the AI response is clearly casual (no code) — like "thanks"
        if not is_likely_transformation(command):
            ai_response = call_openrouter(command, df, mode="chat")
            if not any(keyword in ai_response.lower() for keyword in ['df =', 'df.', 'df[']):
                return jsonify({"message": ai_response}), 200
        ai_code = call_openrouter(command, df, mode="transform")
        ai_code = ai_code.strip()
        if ai_code.startswith("```"):
            ai_code = ai_code.strip("`")  # removes all backticks
            ai_code = ai_code.replace("python", "", 1).strip()
        print("AI GENERATED CODE:\n", ai_code)

        # 2. Check if AI returned runnable code
        if 'df =' in ai_code or 'df.' in ai_code or 'df[':  # optional filter
            try:
                local_vars = {'df': df.copy()}
                exec(ai_code, {}, local_vars)
                transformed_df = local_vars['df']
            except Exception as exec_err:
                return jsonify({
                    "message": f"AI generated code, but it failed to execute:\n\n{ai_code}\n\nError: {exec_err}"
                }), 500

            # Save & return dataset
            transformed_name = f"transformed_{current_dataset}"
            save_dataset(bucket_name, transformed_name, transformed_df)
            user_ref.update({'updated_dataset': transformed_name})

            blob = storage_client.get_bucket(bucket_name).blob(transformed_name)
            download_url = blob.generate_signed_url(expiration=datetime.timedelta(hours=1))

            return jsonify({
                "message": "Transformation applied successfully ✅",
                "download_url": download_url,
                "followup_message": "Want to continue using this cleaned dataset? Reply with yes or no."
            }), 200

        # 3. If no code was found or no transformation occurred
        return jsonify({"message": ai_code}), 200

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return jsonify({"message": f"AI API Error: {e.response.text}"}), 500
    except Exception as e:
        print(f"Error in transform_dataset: {e}")
        return jsonify({"message": f"Error: {str(e)}"}), 500


# def apply_predefined_transformation(df, command):
    """
    Apply supported transformations to the dataframe.
    """
    # Normalize column names for robust matching
    column_map = {col.strip().lower(): col for col in df.columns}
    if command.startswith("remove column"):
        column = command.split("remove column")[-1].strip().lower()
        if column in column_map:
            df = df.drop(columns=[column_map[column]])
        else:
            raise ValueError(f"Column '{column}' does not exist in the dataset.")
    elif command.startswith("rename column"):
        parts = command.split("rename column")[-1].strip().split("to")
        if len(parts) == 2:
            old_name, new_name = parts[0].strip().lower(), parts[1].strip()
            if old_name in column_map:
                df = df.rename(columns={column_map[old_name]: new_name})
            else:
                raise ValueError(f"Column '{parts[0].strip()}' does not exist in the dataset.")
        else:
            raise ValueError("Invalid rename command. Use 'rename column <old_name> to <new_name>'.")
    elif command.startswith("filter rows where"):
        condition = command.split("filter rows where")[-1].strip()
        try:
            df = df.query(condition)
        except Exception as e:
            raise ValueError(f"Error in filter condition: {e}")
    else:
        raise ValueError("Unsupported command.")
    
    return df

#Dataset-status
@app.route('/dataset-status', methods=['GET'])
@token_required
def dataset_status():
    try:
        user_ref = firestore_client.collection('users').document(request.user_id)
        user_data = user_ref.get().to_dict()

        if not user_data:
            return jsonify({"datasetExists": False, "name": None}), 200

        return jsonify({
            "datasetExists": bool(user_data.get('dataset')),
            "name": user_data.get('name'),
        }), 200
    except Exception as e:
        print(f"Error in dataset_status: {e}")
        return jsonify({"message": f"Failed to check dataset status."}), 500

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
    
@app.route('/preview', methods=['GET'])
@token_required
def preview_dataset():
    try:
        user_ref = firestore_client.collection('users').document(request.user_id)
        user_data = user_ref.get().to_dict()

        dataset_name = user_data.get('updated_dataset') or user_data.get('dataset')
        if not dataset_name:
            return jsonify({"message": "No dataset found"}), 404

        file_type = user_data.get('file_type', 'csv')
        delimiter = ',' if file_type == 'csv' else '\t'

        df = load_dataset(user_data['bucket'], dataset_name, delimiter=delimiter)
        preview_data = df.head(100)
        return jsonify({
            "columns": preview_data.columns.tolist(),
            "rows": preview_data.fillna("").to_dict(orient='records')
        }), 200
    except Exception as e:
        print(f"Error in /preview: {e}")
        return jsonify({"message": f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
