import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app as flask_app
from unittest.mock import patch, MagicMock
import io
import json
import pandas as pd

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

@pytest.fixture
def headers():
    return {
        'Authorization': 'Bearer dummy-token'
    }

@pytest.fixture(autouse=True)
def mock_jwt_decode():
    with patch('app.jwt.decode') as mock_decode:
        mock_decode.return_value = {'user_id': 'user123'}
        yield

@pytest.fixture(autouse=True)
def mock_gcs():
    with patch('app.storage_client') as mock_storage:
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.exists.return_value = True
        mock_blob.download_to_filename.return_value = None
        mock_blob.upload_from_filename.return_value = None
        mock_blob.generate_signed_url.return_value = "https://fake-url.com/fake.csv"

        mock_bucket.blob.return_value = mock_blob
        mock_storage.get_bucket.return_value = mock_bucket
        mock_storage.bucket.return_value = mock_bucket
        yield

def test_signup(client):
    with patch('app.firestore_client') as mock_firestore:
        mock_users = mock_firestore.collection.return_value
        mock_users.where.return_value.get.return_value = []
        mock_users.document.return_value.id = 'user123'
        response = client.post('/signup', json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword"
        })
        assert response.status_code == 201

def test_login(client):
    with patch('app.firestore_client') as mock_firestore:
        mock_user = {
            'email': 'test@example.com',
            'password': '$2b$12$NQ...hashed'  
        }
        mock_user_doc = MagicMock()
        mock_user_doc.id = "user123"
        mock_user_doc.to_dict.return_value = mock_user

        mock_users = mock_firestore.collection.return_value
        mock_users.where.return_value.get.return_value = [mock_user_doc]

        with patch('app.bcrypt.checkpw', return_value=True):
            response = client.post('/login', json={
                "email": "test@example.com",
                "password": "securepassword"
            })
            assert response.status_code == 200
            assert 'token' in response.json

def test_dataset_status(client, headers):
    with patch('app.firestore_client') as mock_firestore:
        user_doc = MagicMock()
        user_doc.to_dict.return_value = {'dataset': 'test.csv', 'name': 'Test User'}
        mock_firestore.collection.return_value.document.return_value.get.return_value = user_doc
        response = client.get('/dataset-status', headers=headers)
        assert response.status_code == 200
        assert response.json['datasetExists'] is True

def test_preview_dataset(client, headers):
    real_df = pd.DataFrame({"col1": ["a", "b"], "col2": ["c", "d"]})

    with patch('app.load_dataset', return_value=real_df):
        with patch('app.firestore_client') as mock_firestore:
            user_doc = MagicMock()
            user_doc.to_dict.return_value = {
                'bucket': 'bucket',
                'dataset': 'file.csv',
                'file_type': 'csv'
            }
            mock_firestore.collection.return_value.document.return_value.get.return_value = user_doc

            response = client.get('/preview', headers=headers)
            assert response.status_code == 200
            assert "columns" in response.json
            assert "rows" in response.json

def test_transform_command(client, headers):
    with patch('app.firestore_client') as mock_firestore, \
         patch('app.load_dataset') as mock_load, \
         patch('app.call_openrouter') as mock_openrouter:

        mock_df = MagicMock()
        mock_df.columns.tolist.return_value = ['Name', 'Age']
        mock_df.head.return_value.to_dict.return_value = [{"Name": "Alice", "Age": 25}]
        mock_df.head.return_value.to_string.return_value = "Name Age\nAlice 25"
        mock_df.describe.return_value.reset_index.return_value.fillna.return_value.to_dict.return_value = [{"col": "val"}]
        mock_df.shape = (100, 5)

        mock_user = MagicMock()
        mock_user.to_dict.return_value = {
            'dataset': 'data.csv',
            'file_type': 'csv',
            'bucket': 'bucket',
            'updated_dataset': None
        }

        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_user
        mock_load.return_value = mock_df
        mock_openrouter.return_value = "df.shape"

        response = client.post('/transform', headers=headers, json={"command": "shape"})
        assert response.status_code == 200
        assert "message" in response.json

def test_buff_insight(client, headers):
    with patch('app.firestore_client') as mock_firestore, \
         patch('app.load_dataset') as mock_load, \
         patch('app.call_openrouter') as mock_ai:

        mock_df = MagicMock()
        mock_df.describe.return_value.to_dict.return_value = {}
        mock_df.corr.return_value.to_dict.return_value = {}
        mock_df.columns.tolist.return_value = ['col1']
        mock_df.head.return_value.to_dict.return_value = [{"col1": "val"}]

        mock_user = MagicMock()
        mock_user.to_dict.return_value = {
            'dataset': 'file.csv',
            'file_type': 'csv',
            'bucket': 'bucket'
        }

        mock_ai.return_value = "### BuffInsight\n\nThis is a summary."
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_user
        mock_load.return_value = mock_df

        response = client.get('/buff-insight', headers=headers)
        assert response.status_code == 200
        assert "summary_markdown" in response.json

def test_chat_history_get(client, headers):
    with patch('app.fetch_recent_chat_history', return_value=[
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]):
        response = client.get('/chat-history', headers=headers)
        assert response.status_code == 200
        assert "history" in response.json

def test_chat_history_post(client, headers):
    with patch('app.firestore_client') as mock_firestore:
        response = client.post('/chat-history', headers=headers, json={
            "role": "user",
            "content": "Test message"
        })
        assert response.status_code == 200

def test_welcome_message(client, headers):
    response = client.get('/chat', headers=headers)
    assert response.status_code == 200
    assert "Welcome" in response.json['message']
    
def test_transform_yes_command(client, headers):
    with patch('app.firestore_client') as mock_firestore, \
         patch('app.storage_client') as mock_storage:

        user_doc = MagicMock()
        user_doc.to_dict.return_value = {
            'dataset': 'original.csv',
            'updated_dataset': 'transformed.csv',
            'bucket': 'bucket'
        }

        mock_blob = MagicMock()
        mock_blob.exists.return_value = True
        mock_storage.get_bucket.return_value.blob.return_value = mock_blob

        mock_firestore.collection.return_value.document.return_value.get.return_value = user_doc

        response = client.post('/transform', headers=headers, json={"command": "yes"})
        assert response.status_code == 200
        assert "Using updated dataset" in response.json["message"]

def test_upload_dataset_csv_validation_failure(client, headers):
    broken_csv = io.BytesIO(b'invalid,data\n123')  
    broken_csv.name = 'bad.csv'

    with patch('app.firestore_client') as mock_firestore, \
         patch('app.storage_client') as mock_storage, \
         patch('pandas.read_csv', side_effect=Exception("CSV error")):

        user_doc = MagicMock()
        user_doc.to_dict.return_value = {'bucket': 'bucket'}
        mock_firestore.collection.return_value.document.return_value.get.return_value = user_doc

        response = client.post('/upload', data={'file': (broken_csv, broken_csv.name)}, headers=headers, content_type='multipart/form-data')
        assert response.status_code == 400
        assert "CSV validation failed" in response.json['message']
        
def test_buff_clean_options(client, headers):
    with patch('app.firestore_client') as mock_firestore, \
         patch('app.load_dataset') as mock_loader:

        mock_df = pd.DataFrame({
            'A': [1, 2, None],
            'B': ['x', None, 'z']
        })
        mock_loader.return_value = mock_df

        mock_user = MagicMock()
        mock_user.to_dict.return_value = {
            'bucket': 'bucket',
            'dataset': 'file.csv',
            'file_type': 'csv',
            'updated_dataset': None
        }
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_user

        response = client.get('/buff-clean-options', headers=headers)
        assert response.status_code == 200
        assert 'columns' in response.json
        assert 'strategies' in response.json
        
def test_run_custom_code_success(client, headers):
    with patch('app.firestore_client') as mock_firestore, \
         patch('app.load_dataset') as mock_loader:

        mock_df = pd.DataFrame({"A": [1, 2, 3]})
        mock_loader.return_value = mock_df

        mock_user = MagicMock()
        mock_user.to_dict.return_value = {
            'bucket': 'bucket',
            'dataset': 'data.csv',
            'file_type': 'csv'
        }
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_user

        response = client.post('/run-code', headers=headers, json={"code": "print(df.head())"})
        assert response.status_code == 200
        assert "message" in response.json
        
def test_buff_trainer_options(client, headers):
    with patch('app.firestore_client') as mock_firestore, \
         patch('app.load_dataset') as mock_loader:

        mock_df = pd.DataFrame({"feature": [1, 2], "target": [3, 4]})
        mock_loader.return_value = mock_df

        mock_user = MagicMock()
        mock_user.to_dict.return_value = {
            'bucket': 'bucket',
            'dataset': 'data.csv',
            'file_type': 'csv'
        }
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_user

        response = client.get('/buff-trainer-options', headers=headers)
        assert response.status_code == 200
        assert 'columns' in response.json
        assert 'models' in response.json
        
def test_invalid_token(client):
    response = client.get('/dataset-status', headers={'Authorization': 'Bearer invalid.token.here'})
    assert response.status_code == 401
    assert "invalid" in response.json["message"].lower()
    
def test_upload_unsupported_file_type(client, headers):
    data = {
        'file': (io.BytesIO(b"some content"), 'data.unsupported')
    }
    with patch('app.firestore_client') as mock_firestore:
        mock_user = MagicMock()
        mock_user.to_dict.return_value = {
            'bucket': 'bucket',
            'dataset': None
        }
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_user

        response = client.post('/upload', data=data, headers=headers, content_type='multipart/form-data')
        assert response.status_code == 201
        assert "File uploaded successfully" in response.json['message']
        
def test_ai_code_execution_error(client, headers):
    with patch('app.firestore_client') as mock_firestore, \
         patch('app.load_dataset') as mock_load, \
         patch('app.call_openrouter', return_value='df = df.non_existent_method()'):

        mock_df = pd.DataFrame({"col1": [1, 2]})
        mock_user = MagicMock()
        mock_user.to_dict.return_value = {
            'dataset': 'data.csv',
            'file_type': 'csv',
            'bucket': 'bucket',
            'updated_dataset': None
        }

        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_user
        mock_load.return_value = mock_df

        response = client.post('/transform', headers=headers, json={"command": "trigger ai error"})
        assert response.status_code == 500
        assert "failed to execute" in response.json["message"].lower()