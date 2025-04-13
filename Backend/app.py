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
import matplotlib
matplotlib.use('Agg')  

import matplotlib.pyplot as plt  
from io import StringIO
import sys
import black
import subprocess
import tempfile
import re
import logging
import ast



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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

firestore_client = firestore.Client()
storage_client = storage.Client()

def fetch_recent_chat_history(user_id, limit=10):
    try:
        history_ref = firestore_client.collection('users').document(user_id).collection('chat_history')
        query = history_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit).stream()
        history = [{"role": doc.to_dict()['role'], "content": doc.to_dict()['content']} for doc in reversed(list(query))]
        return history
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        return []
    
def append_to_chat_history(user_id, role, content):
    """Store the latest chat message in Firestore."""
    chat_ref = firestore_client.collection("users").document(user_id).collection("chat_history")
    chat_ref.add({
        "role": role,  # 'user' or 'assistant'
        "content": content,
        "timestamp": datetime.datetime.utcnow()
    })
def detect_undefined_names(code):
    """
    Use flake8 to detect undefined variables in the provided code.
    Returns a list of variable names that are used but not defined.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp_file:
        temp_file.write(code)
        temp_path = temp_file.name

    try:
        result = subprocess.run(
            ["flake8", "--select=F821", temp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        lines = result.stdout.strip().splitlines()
        undefined = []
        for line in lines:
            match = re.search(r"undefined name '(\w+)'", line)
            if match:
                undefined.append(match.group(1))
        return undefined
    finally:
        os.unlink(temp_path)

def clean_ai_code(raw_code: str):
    # Remove markdown code block (```python ... ```)
    code = re.sub(r"^```(?:python)?\s*", "", raw_code.strip(), flags=re.IGNORECASE)
    code = re.sub(r"\s*```$", "", code)

    # Strip stray backticks, labels, and whitespace
    code = code.strip("` \n")
    code = code.replace("python", "").strip()

    # Normalize imports (e.g., remove double spacing)
    code = re.sub(r"import\s*([a-zA-Z0-9_]+)", r"import \1", code)
    code = re.sub(r"from\s+([a-zA-Z0-9_.]+)\s+import\s+([a-zA-Z0-9_,\s]+)", r"from \1 import \2", code)

    # Clean each line
    lines = code.split('\n')
    stripped_lines = [line.strip() for line in lines if line.strip()]

    return '\n'.join(stripped_lines)

def is_likely_transformation(prompt: str):
    keywords = ['remove column', 'rename column', 'filter rows', 'drop', 'convert', 'fill', 'encode', 'impute', 
                'group by', 'pivot', 'merge', 'join', 'concat', 'stack', 'unstack', 'sort', 'sample', 
                'drop duplicates', 'replace', 'map', 'apply', 'query', 'columns', 'size', 'shape',
                'head', 'tail', 'info', 'value_counts', 'unique', 'isna', 'notna',
                'astype', 'to_datetime', 'to_numeric', 'to_string', 'to_csv', 'to_excel', 'to_json',
                'to_html', 'to_sql', 'to_dict', 'to_clipboard', 'to_feather', 'to_parquet', 'column', 
                'filter', 'remove', 'add', 'insert', 'update', 'change', 'modify', 'transform', 'create', 'rename', 'prepare']
    return any(kw in prompt.lower() for kw in keywords)

def format_code(code: str):
    try:
        return black.format_str(code, mode=black.FileMode())
    except Exception as e:
        print(f"Black formatting failed: {e}")
        return code  # fallback to original

def ensure_dataframe_has_id(df):
    if 'id' not in df.columns:
        df = df.copy()
        df.insert(0, 'id', range(1, len(df) + 1))  # Inject id column at start
    return df


def call_openrouter(prompt, df=None, mode="transform", history=None):
    history = history or []
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
            "You have been created by Rafay, Samiksha, Harsh and Mohit for their Big Data Architecture Course\n"
            "You're a data scientist. Return only executable pandas code to transform a DataFrame named df.\n"
            f"Here are the columns:\n{columns}\n\n"
            f"Here is a preview:\n{preview}"
        )
        user_prompt = f"Given this command: '{prompt}', write Python pandas code to perform this on a dataframe named df."

    else:  # mode == "chat"
        logger.info("in chat mode)")
        columns = df.columns.tolist() if df is not None else []
        print("Columns:", columns)
        preview = df.head(5).to_dict(orient='records') if df is not None else []
        system_prompt = (
            "Your name is BuffBot and you are made for students of University of Colorado Boulder\n"
            "You have been created by Rafay, Samiksha, Harsh and Mohit for their Big Data Architecture Course\n"
            "You're an intelligent and friendly data assistant. Help users with data-related questions, "
            "and feel free to chat casually. Be helpful and conversational.\n"
            f"Here are the columns:\n{columns}\n\n"
            f"Here is a preview:\n{preview}"
        )
        user_prompt = prompt
        
    messages = [
        {"role": "system", "content": system_prompt}
    ] + history + [  
        {"role": "user", "content": user_prompt}
    ]

    body = {
        "model": "openrouter/optimus-alpha",
        "temperature": 0.2,
        "messages": messages,
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
    response.raise_for_status()
    
    logger.info(f"OpenRouter response: {response.json()}")

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

@app.route('/buff-clean-options', methods=['GET'])
@token_required
def buff_clean_options():
    try:
        user_ref = firestore_client.collection('users').document(request.user_id)
        user_data = user_ref.get().to_dict()
        dataset_name = user_data.get('updated_dataset') or user_data.get('dataset')
        file_type = user_data.get('file_type', 'csv')
        delimiter = ',' if file_type == 'csv' else '\t'

        df = load_dataset(user_data['bucket'], dataset_name, delimiter=delimiter)

        return jsonify({
            "columns": df.columns.tolist(),
            "strategies": [
                "drop_na_rows",
                "fill_missing_with_mean",
                "fill_missing_with_median",
                "fill_missing_with_mode",
                "label_encode",
                "one_hot_encode"
            ]
        }), 200

    except Exception as e:
        print(f"Error in /buff-clean-options: {e}")
        return jsonify({"message": "Failed to fetch cleaning options"}), 500

@app.route('/buff-clean', methods=['POST'])
@token_required
def buff_clean():
    try:
        user_id = request.user_id
        data = request.get_json()
        selected_columns = data.get("columns")
        strategies = data.get("strategies", [])

        user_ref = firestore_client.collection('users').document(user_id)
        user_data = user_ref.get().to_dict()

        dataset_name = user_data.get('updated_dataset') or user_data.get('dataset')
        file_type = user_data.get('file_type', 'csv')
        delimiter = ',' if file_type == 'csv' else '\t'

        df = load_dataset(user_data['bucket'], dataset_name, delimiter=delimiter)

        # Create a working copy
        if selected_columns:
            df_subset = df[selected_columns].copy()
        else:
            df_subset = df.copy()

        transformation_summary = []

        for strategy in strategies:
            if strategy == "drop_na_rows":
                before_rows = df_subset.shape[0]
                df_subset = df_subset.dropna()
                after_rows = df_subset.shape[0]
                dropped = before_rows - after_rows
                transformation_summary.append(f"Dropped {dropped} rows with missing values.")

                # Sync full DataFrame by dropping same rows
                if not selected_columns:
                    df = df.loc[df_subset.index]
                else:
                    df = df.loc[df_subset.index]  # keep only common rows

            elif strategy == "fill_missing_with_mean":
                num_cols = df_subset.select_dtypes(include='number').columns
                if len(num_cols) > 0:
                    df_subset[num_cols] = df_subset[num_cols].fillna(df_subset[num_cols].mean())
                    transformation_summary.append("Filled missing numeric values with column means.")
                else:
                    transformation_summary.append("No numeric columns found for mean imputation.")

            elif strategy == "fill_missing_with_median":
                num_cols = df_subset.select_dtypes(include='number').columns
                if len(num_cols) > 0:
                    df_subset[num_cols] = df_subset[num_cols].fillna(df_subset[num_cols].median())
                    transformation_summary.append("Filled missing numeric values with column medians.")
                else:
                    transformation_summary.append("No numeric columns found for median imputation.")

            elif strategy == "fill_missing_with_mode":
                for col in df_subset.columns:
                    try:
                        mode = df_subset[col].mode()
                        if not mode.empty:
                            df_subset[col] = df_subset[col].fillna(mode[0])
                    except Exception as e:
                        print(f"Mode fill skipped for {col}: {e}")
                transformation_summary.append("Filled missing values using mode for each column.")

            elif strategy == "label_encode":
                from sklearn.preprocessing import LabelEncoder
                for col in df_subset.select_dtypes(include='object').columns:
                    try:
                        df_subset[col] = LabelEncoder().fit_transform(df_subset[col].astype(str))
                    except Exception as e:
                        print(f"Label encoding skipped for {col}: {e}")
                transformation_summary.append("Applied label encoding to categorical columns.")

            elif strategy == "one_hot_encode":
                try:
                    df_subset = pd.get_dummies(df_subset)
                    transformation_summary.append("Applied one-hot encoding on categorical columns.")
                except Exception as e:
                    transformation_summary.append(f"One-hot encoding failed: {e}")

        # Replace original columns with cleaned ones
        if selected_columns:
            for col in df_subset.columns:
                df[col] = df_subset[col]
        else:
            df = df_subset

        cleaned_name = f"buff_cleaned_{dataset_name}"
        save_dataset(user_data['bucket'], cleaned_name, df)
        user_ref.update({'updated_dataset': cleaned_name})

        blob = storage_client.get_bucket(user_data['bucket']).blob(cleaned_name)
        download_url = blob.generate_signed_url(expiration=datetime.timedelta(hours=1))

        return jsonify({
            "transformation_summary": "🧼 Buff Clean complete! Here's what I did:\n\n" + "\n".join([f"● {t}" for t in transformation_summary]),
            "download_url": download_url,
            "followup_message": "Would you like to continue using this cleaned dataset? Reply with `yes` or `no`."
        }), 200

    except Exception as e:
        print(f"Error in /buff-clean: {e}")
        return jsonify({"message": f"Buff Clean failed: {str(e)}"}), 500

@app.route('/buff-visualizer-options', methods=['GET'])
@token_required
def buff_visualizer_options():
    try:
        user_ref = firestore_client.collection('users').document(request.user_id)
        user_data = user_ref.get().to_dict()
        dataset_name = user_data.get('updated_dataset') or user_data.get('dataset')
        file_type = user_data.get('file_type', 'csv')
        delimiter = ',' if file_type == 'csv' else '\t'

        df = load_dataset(user_data['bucket'], dataset_name, delimiter=delimiter)

        numeric_columns = df.select_dtypes(include='number').columns.tolist()
        categorical_columns = df.select_dtypes(include='object').columns.tolist()

        return jsonify({
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
            "all_columns": df.columns.tolist()
        }), 200

    except Exception as e:
        print(f"Error in /buff-visualizer-options: {e}")
        return jsonify({"message": "Failed to load visualizer options."}), 500

@app.route('/buff-visualizer', methods=['POST'])
@token_required
def buff_visualizer():
    try:
        user_id = request.user_id
        data = request.get_json()
        chart_type = data.get("chart_type")  
        x_col = data.get("x")
        y_col = data.get("y", None)

        if not chart_type or not x_col:
            return jsonify({"message": "Missing chart type or x column"}), 400

        # Load dataset
        user_ref = firestore_client.collection('users').document(user_id)
        user_data = user_ref.get().to_dict()
        dataset_name = user_data.get('updated_dataset') or user_data.get('dataset')
        file_type = user_data.get('file_type', 'csv')
        delimiter = ',' if file_type == 'csv' else '\t'

        df = load_dataset(user_data['bucket'], dataset_name, delimiter=delimiter)

        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        plt.figure(figsize=(10, 6))

        if chart_type == 'bar':
            df[x_col].value_counts().plot(kind='bar')
        elif chart_type == 'line':
            if y_col:
                plt.plot(df[x_col], df[y_col])
            else:
                return jsonify({"message": "Y column required for line chart"}), 400
        elif chart_type == 'hist':
            df[x_col].plot(kind='hist', bins=20)
        elif chart_type == 'scatter':
            if y_col:
                df.plot(kind='scatter', x=x_col, y=y_col)
            else:
                return jsonify({"message": "Y column required for scatter plot"}), 400
        else:
            return jsonify({"message": "Unsupported chart type"}), 400

        plt.title(f"{chart_type.title()} Plot of {x_col}" + (f" vs {y_col}" if y_col else ""))
        plt.xlabel(x_col)
        if y_col:
            plt.ylabel(y_col)

        # Save and upload to GCS
        image_path = f"{user_id}_buff_visualizer.png"
        plt.tight_layout()
        plt.savefig(image_path)
        plt.close()

        bucket = storage_client.get_bucket(user_data['bucket'])
        blob = bucket.blob(image_path)
        blob.upload_from_filename(image_path)
        os.remove(image_path)

        image_url = blob.generate_signed_url(expiration=datetime.timedelta(hours=1))

        return jsonify({
            "message": f"Here's your {chart_type} chart!",
            "image_url": image_url
        }), 200

    except Exception as e:
        return jsonify({"message": f"Buff Visualizer failed: {str(e)}"}), 500

@app.route('/buff-trainer-options', methods=['GET'])
@token_required
def buff_trainer_options():
    try:
        user_ref = firestore_client.collection('users').document(request.user_id)
        user_data = user_ref.get().to_dict()
        dataset_name = user_data.get('updated_dataset') or user_data.get('dataset')
        file_type = user_data.get('file_type', 'csv')
        delimiter = ',' if file_type == 'csv' else '\t'

        df = load_dataset(user_data['bucket'], dataset_name, delimiter=delimiter)
        numeric_columns = df.select_dtypes(include='number').columns.tolist()

        return jsonify({
            "columns": df.columns.tolist(),
            "numeric_columns": numeric_columns,
            "models": ["Linear Regression", "Random Forest", "Decision Tree"]
        }), 200

    except Exception as e:
        print(f"Error in /buff-trainer-options: {e}")
        return jsonify({"message": "Failed to fetch training options"}), 500

@app.route('/buff-trainer', methods=['POST'])
@token_required
def buff_trainer():
    try:
        data = request.get_json()
        features = data.get('features')
        target = data.get('target')
        model_type = data.get('model_type')

        if not features or not target or not model_type:
            return jsonify({"message": "Missing features, target, or model type"}), 400

        user_ref = firestore_client.collection('users').document(request.user_id)
        user_data = user_ref.get().to_dict()
        dataset_name = user_data.get('updated_dataset') or user_data.get('dataset')
        file_type = user_data.get('file_type', 'csv')
        delimiter = ',' if file_type == 'csv' else '\t'

        df = load_dataset(user_data['bucket'], dataset_name, delimiter=delimiter)
        df = df.dropna(subset=features + [target])

        from sklearn.model_selection import train_test_split
        from sklearn.linear_model import LinearRegression
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.tree import DecisionTreeRegressor
        from sklearn.metrics import mean_squared_error, r2_score
        import pickle

        X = df[features]
        y = df[target]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        if model_type == "Linear Regression":
            model = LinearRegression()
        elif model_type == "Random Forest":
            model = RandomForestRegressor()
        elif model_type == "Decision Tree":
            model = DecisionTreeRegressor()
        else:
            return jsonify({"message": "Unsupported model type"}), 400

        model.fit(X_train, y_train)
        predictions = model.predict(X_test)

        mse = mean_squared_error(y_test, predictions)
        r2 = r2_score(y_test, predictions)

        # Save model to GCS
        model_file = f"{request.user_id}_trained_model.pkl"
        with open(model_file, 'wb') as f:
            pickle.dump(model, f)

        bucket = storage_client.get_bucket(user_data['bucket'])
        blob = bucket.blob(model_file)
        blob.upload_from_filename(model_file)
        os.remove(model_file)
        model_url = blob.generate_signed_url(expiration=datetime.timedelta(hours=1))

        return jsonify({
            "summary": f"📊 Model: {model_type}\n\nR² Score: {r2:.4f}\n\nMSE: {mse:.4f}",
            "download_url": model_url
        }), 200

    except Exception as e:
        print(f"Error in /buff-trainer: {e}")
        return jsonify({"message": "Training failed: " + str(e)}), 500

@app.route('/buff-insight', methods=['GET'])
@token_required
def buff_insight():
    try:
        user_ref = firestore_client.collection('users').document(request.user_id)
        user_data = user_ref.get().to_dict()
        dataset_name = user_data.get('updated_dataset') or user_data.get('dataset')
        file_type = user_data.get('file_type', 'csv')
        delimiter = ',' if file_type == 'csv' else '\t'

        df = load_dataset(user_data['bucket'], dataset_name, delimiter=delimiter)

        # Generate data summary components
        describe = df.describe(include='all').to_dict()
        correlation = df.corr(numeric_only=True).to_dict()
        columns = df.columns.tolist()
        preview = df.head(5).to_dict(orient='records')

        # Prepare context strings
        describe_str = json.dumps(describe, indent=2)
        correlation_str = json.dumps(correlation, indent=2)
        columns_str = ", ".join(columns)
        preview_str = json.dumps(preview, indent=2)

        # Updated prompt with full context
        ai_prompt = (
            f"Here is a summary of the dataset:\n\n"
            f"Columns: {columns_str}\n\n"
            f"First few rows:\n{preview_str}\n\n"
            f"Describe statistics:\n{describe_str}\n\n"
            f"Correlation matrix:\n{correlation_str}\n\n"
            "Now, generate a concise natural language summary of this dataset. "
            "Mention number of rows and columns, identify skewed or unusual distributions, "
            "strong correlations (r > 0.75), and any interesting trends. "
            "Make it helpful, friendly, and easy to understand."
            "Make sure the title of your summary is 'BuffInsight' and it is in markdown format."
            )

        explanation = call_openrouter(
            prompt=ai_prompt,
            df=df,
            mode="chat"  
        )
        
        logger.info(f"Generated Insight: {explanation}")

        return jsonify({
            "summary_markdown": explanation
        }), 200

    except Exception as e:
        print(f"Error in /buff-insight: {e}")
        return jsonify({"message": f"Buff Insight failed: {str(e)}"}), 500

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

        # Load user & dataset
        user_ref = firestore_client.collection('users').document(user_id)
        user_data = user_ref.get().to_dict()
        bucket_name = user_data.get('bucket')
        current_dataset = user_data.get('dataset')
        file_type = user_data.get('file_type', 'csv')
        if not current_dataset:
            return jsonify({"message": "No dataset found. Please upload a dataset first."}), 400

        if command.lower() == "yes":
            new_dataset = user_data.get('updated_dataset')
            if not new_dataset:
                return jsonify({"message": "No updated dataset found."}), 400
            bucket = storage_client.get_bucket(bucket_name)
            old_blob = bucket.blob(current_dataset)
            if old_blob.exists():
                old_blob.delete()
            user_ref.update({'dataset': new_dataset, 'updated_dataset': None})
            return jsonify({"message": "Using updated dataset."}), 200

        if command.lower() == "no":
            user_ref.update({'updated_dataset': None})
            user_data = user_ref.get().to_dict()
            return jsonify({"message": "Continuing with original dataset."}), 200

        dataset_to_use = user_data.get('updated_dataset') or current_dataset
        delimiter = ',' if file_type == 'csv' else '\t'
        df = load_dataset(bucket_name, dataset_to_use, delimiter=delimiter)
            
        lower_cmd = command.lower()

        # Descriptive command handlers
        if match_column_command(lower_cmd):
            cols = df.columns.tolist()
            return jsonify({"message": "Your dataset has the following columns:\n\n" + "\n".join([f"● {col}" for col in cols])}), 200
        elif match_preview_command(lower_cmd):
            return jsonify({"message": f"Here's a preview:\n\n{json.dumps(df.head(5).to_dict(orient='records'), indent=2)}"}), 200
        elif match_head_command(lower_cmd):
            return jsonify({"message": str(df.head().to_string(index=False))}), 200
        elif match_tail_command(lower_cmd):
            return jsonify({"message": str(df.tail().to_string(index=False))}), 200
        elif match_size_command(lower_cmd):
            return jsonify({"message": f"Dataset Dimensions: Rows: {df.shape[0]}, Columns: {df.shape[1]}"}), 200
        elif match_describe_command(lower_cmd):
            desc_df = df.describe().reset_index()
            return jsonify({
                "message": "Here's a statistical summary of your dataset.",
                "table": {
                    "columns": desc_df.columns.tolist(),
                    "rows": desc_df.fillna("").to_dict(orient='records')
                }
            }), 200
        elif lower_cmd == "commands":
            return jsonify({"message": "Here are the commands you can use:\n\n"
                                       "● remove column <column_name>\n"
                                       "● rename column <old_name> to <new_name>\n"
                                       "● filter rows where <condition>\n"
                                       "● columns\n"
                                       "● size\n"}), 200

        # Handle non-transformational queries (chat)
        if not is_likely_transformation(command):
            # Get recent chat history
            history_ref = firestore_client.collection("users").document(user_id).collection("chat_history")
            recent_messages = history_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(5).stream()

            history = []
            for doc in reversed(list(recent_messages)):
                entry = doc.to_dict()
                history.append({"role": entry["role"], "content": entry["content"]})

            # Append current user prompt
            history.append({"role": "user", "content": command})

            # Call OpenRouter with full context
            ai_response = call_openrouter(command, df=df, mode="chat", history=history)

            # Save the AI's reply and user prompt
            # append_to_chat_history(user_id, "user", command)
            # append_to_chat_history(user_id, "assistant", ai_response.strip())
            stripped = ai_response.strip()
            if any(stripped.startswith(p) for p in ['df.', 'df.describe', 'df.shape']):
                try:
                    local_vars = {'df': df.copy()}
                    result = eval(stripped, {}, local_vars)
                    if isinstance(result, (pd.DataFrame, pd.Series)):
                        return jsonify({"message": str(result.to_string())}), 200
                    return jsonify({"message": str(result)}), 200
                except Exception:
                    return jsonify({"message": ai_response}), 200
            return jsonify({"message": ai_response}), 200

        # === AI Transformation Code ===
        # Get recent chat history
        history_ref = firestore_client.collection("users").document(user_id).collection("chat_history")
        recent_messages = history_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(5).stream()

        history = []
        for doc in reversed(list(recent_messages)):
            entry = doc.to_dict()
            history.append({"role": entry["role"], "content": entry["content"]})

        # Append current user prompt
        history.append({"role": "user", "content": command})

        # Call OpenRouter with full context
        ai_code = call_openrouter(command, df=df, mode="transform", history=history)
        ai_code = clean_ai_code(ai_code)
        # ai_code = detect_undefined_names(ai_code)

        # Save the AI's reply and user prompt
        # append_to_chat_history(user_id, "user", command)
        # append_to_chat_history(user_id, "assistant", ai_code.strip())
        ai_code = ai_code.replace("plt.show()", "")
        print("AI GENERATED CODE:\n", ai_code)

        if any(keyword in ai_code for keyword in ["plt.", "df.plot", "df.plot.", "df.plot(", "sns.", "sns.scatterplot", "sns.lineplot", "sns.barplot"]):
            try:
                local_vars = {'df': df.copy()}
                exec(ai_code, {}, local_vars)

                image_path = "/tmp/figure.png"
                plt.savefig(image_path)
                plt.close()

                blob = storage_client.bucket(bucket_name).blob("figure.png")
                blob.upload_from_filename(image_path)
                image_url = blob.generate_signed_url(expiration=datetime.timedelta(hours=1))

                # 🧠 Ask AI to describe the chart
                plot_description_prompt = (
                    f"This code creates a visualization using matplotlib:\n\n{ai_code}\n\n"
                    "Please describe what this plot shows in 1-2 friendly and concise sentences, "
                    "assuming the DataFrame variable is `df`. Don’t include the code, just a natural description."
                )
                chart_caption = call_openrouter(plot_description_prompt, df, mode="chat")
                print("AI GENERATED CAPTION:\n", chart_caption)

                return jsonify({
                    "message": chart_caption.strip() or "Here's your visualization 📊",
                    "image_url": image_url,
                    "generated_code": ai_code
                }), 200

            except Exception as viz_err:
                return jsonify({
                    "message": f"Failed to generate visualization:\n\n{ai_code}\n\nError: {viz_err}"}
                ), 500

        if 'df =' in ai_code or 'df.' in ai_code or 'df[' in ai_code:
            try:
                local_vars = {'df': df.copy()}
                exec(ai_code, {}, local_vars)
                transformed_df = local_vars['df']
            except Exception as exec_err:
                return jsonify({
                    "message": f"AI generated code, but it failed to execute:\n\n{ai_code}\n\nError: {exec_err}"
                }), 500

            transformed_name = f"transformed_{current_dataset}"
            save_dataset(bucket_name, transformed_name, transformed_df)
            user_ref.update({'updated_dataset': transformed_name})

            blob = storage_client.get_bucket(bucket_name).blob(transformed_name)
            download_url = blob.generate_signed_url(expiration=datetime.timedelta(hours=1))

            return jsonify({
                "message": "Transformation applied successfully ✅",
                "download_url": download_url,
                "generated_code": ai_code,  # 👈 Add this line
                "followup_message": "Want to continue using this cleaned dataset? Reply with yes or no."
            }), 200

        return jsonify({"message": ai_code}), 200

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return jsonify({"message": f"AI API Error: {e.response.text}"}), 500
    except Exception as e:
        print(f"Error in transform_dataset: {e}")
        return jsonify({"message": f"Error: {str(e)}"}), 500

@app.route('/chat-history', methods=['GET'])
@token_required
def get_chat_history():
    try:
        history = fetch_recent_chat_history(request.user_id, limit=20)
        return jsonify({"history": history}), 200
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        return jsonify({"message": "Failed to retrieve chat history"}), 500

@app.route('/chat-history', methods=['POST'])
@token_required
def save_chat_message():
    try:
        user_id = request.user_id
        data = request.json
        role = data.get("role")
        content = data.get("content")
        if not role or not content:
            return jsonify({"message": "Role and content are required."}), 400

        history_ref = firestore_client.collection("users").document(user_id).collection("chat_history")
        history_ref.add({
            "role": role,
            "content": content,
            "timestamp": firestore.SERVER_TIMESTAMP
        })

        return jsonify({"message": "Message saved"}), 200
    except Exception as e:
        return jsonify({"message": f"Failed to save chat message: {str(e)}"}), 500

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

@app.route('/run-code', methods=['POST'])
@token_required
def run_custom_code():
    user_id = request.user_id
    code = request.json.get("code", "").strip()

    if not code:
        return jsonify({"message": "No code provided"}), 400
    code = format_code(code)
    # Detect missing symbols
    undefined_names = detect_undefined_names(code)

    # Add common imports for undefined names
    common_imports = {
        'pd': 'import pandas as pd',
        'np': 'import numpy as np',
        'plt': 'import matplotlib.pyplot as plt',
        'sns': 'import seaborn as sns',
        'train_test_split': 'from sklearn.model_selection import train_test_split',
        'LinearRegression': 'from sklearn.linear_model import LinearRegression',
        'RandomForestClassifier': 'from sklearn.ensemble import RandomForestClassifier',
        'StandardScaler': 'from sklearn.preprocessing import StandardScaler'
    }

    for symbol in undefined_names:
        if symbol in common_imports:
            code = f"{common_imports[symbol]}\n" + code

    # Fetch dataset info
    user_ref = firestore_client.collection('users').document(user_id)
    user_data = user_ref.get().to_dict()
    bucket_name = user_data.get('bucket')
    dataset_name = user_data.get('dataset')
    file_type = user_data.get('file_type', 'csv')
    delimiter = ',' if file_type == 'csv' else '\t'

    try:
        df = load_dataset(bucket_name, dataset_name, delimiter=delimiter)
        local_vars = {'df': df.copy()}
        response = {}  # ✅ Initialize early

        # Capture output
        output = StringIO()
        sys.stdout = output

        try:
            # Parse code to find if last node is an expression
            parsed = ast.parse(code)
            if isinstance(parsed.body[-1], ast.Expr):
                exec(
                    compile(ast.Module(body=parsed.body[:-1], type_ignores=[]), filename="<ast>", mode="exec"),
                    {},
                    local_vars
                )
                result = eval(
                    compile(ast.Expression(parsed.body[-1].value), filename="<ast>", mode="eval"),
                    {},
                    local_vars
                )
                if result is not None:
                    print(result)
                logger.info(code)

                plot_patterns = [
                    r"plt\s*\.",                        # matplotlib
                    r"df\s*(?:\[[^\]]+\]|\.\w+)?\s*\.plot\s*\(",
                    r"df\s*(?:\[[^\]]+\]|\.\w+)?\s*\.boxplot\s*\(",
                    r"df\s*(?:\[[^\]]+\]|\.\w+)?\s*\.hist\s*\(",
                    r"df\s*(?:\[[^\]]+\]|\.\w+)?\s*\.bar\s*\(",
                    r"df\s*(?:\[[^\]]+\]|\.\w+)?\s*\.pie\s*\(",
                    r"df\s*(?:\[[^\]]+\]|\.\w+)?\s*\.scatter\s*\(",
                    r"df\s*(?:\[[^\]]+\]|\.\w+)?\s*\.line\s*\(",
                ]

                plot_detected = any(re.search(pattern, code) for pattern in plot_patterns)

                # ✅ Save plot if code contains matplotlib
                if plot_detected:
                    logger.info("Plotting detected, saving figure...")
                    import matplotlib
                    matplotlib.use('Agg')
                    import matplotlib.pyplot as plt
                    import uuid

                    plt.tight_layout()
                    image_path = f"/tmp/plot_{uuid.uuid4().hex}.png"
                    plt.savefig(image_path)
                    plt.close()

                    blob = storage_client.bucket(bucket_name).blob(f"plots/{user_id}/{uuid.uuid4().hex}.png")
                    blob.upload_from_filename(image_path)
                    image_url = blob.generate_signed_url(expiration=datetime.timedelta(hours=1))

                    response["image_url"] = image_url
            else:
                exec(code, {}, local_vars)

        finally:
            sys.stdout = sys.__stdout__

        printed_output = output.getvalue().strip()
        response["message"] = printed_output or "Code executed successfully."

        result_df = local_vars.get('df')
        response["generated_code"] = code
        if isinstance(result_df, pd.DataFrame) and printed_output == "":
            result_df = ensure_dataframe_has_id(result_df)
            response["table"] = {
                "columns": result_df.columns.tolist(),
                "rows": result_df.fillna("").to_dict(orient='records')
            }

        return jsonify(response)

    except Exception as e:
        sys.stdout = sys.__stdout__  # Failsafe restore
        return jsonify({"message": f"Execution error: {str(e)}"}), 500
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
        df = ensure_dataframe_has_id(df)
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
