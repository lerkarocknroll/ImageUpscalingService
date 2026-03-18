import pytest
import os
import tempfile
from unittest.mock import patch
from app import app as flask_app

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with tempfile.TemporaryDirectory() as tmpdir:
        flask_app.config['PROCESSED_DIR'] = tmpdir
        with patch('app.upscale_task') as mock_task:
            yield flask_app.test_client()

def test_upscale_no_file(client):
    rv = client.post('/upscale')
    assert rv.status_code == 400
    assert b'No file part' in rv.data

def test_upscale_empty_file(client):
    data = {'file': (b'', 'test.jpg')}
    rv = client.post('/upscale', data=data, content_type='multipart/form-data')
    assert rv.status_code == 400
    assert b'No selected file' in rv.data

def test_upscale_success(client, mocker):
    mock_async = mocker.patch('app.upscale_task.apply_async')
    mock_async.return_value.id = '123'
    data = {'file': (b'fake image', 'test.jpg')}
    rv = client.post('/upscale', data=data, content_type='multipart/form-data')
    assert rv.status_code == 202
    assert rv.get_json()['task_id'] == '123'

def test_get_task_pending(client):
    with patch('app.upscale_task.AsyncResult') as mock_result:
        mock_result.return_value.state = 'PENDING'
        rv = client.get('/tasks/123')
        assert rv.status_code == 200
        assert rv.get_json()['state'] == 'PENDING'

def test_get_task_success(client):
    with patch('app.upscale_task.AsyncResult') as mock_result:
        mock_result.return_value.state = 'SUCCESS'
        mock_result.return_value.result = '123.png'
        rv = client.get('/tasks/123')
        assert rv.status_code == 200
        json_data = rv.get_json()
        assert json_data['state'] == 'SUCCESS'
        assert json_data['result_url'] == '/processed/123.png'

def test_get_processed_file(client):
    processed_dir = flask_app.config['PROCESSED_DIR']
    filename = 'test.png'
    filepath = os.path.join(processed_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(b'test')
    rv = client.get(f'/processed/{filename}')
    assert rv.status_code == 200
    assert rv.data == b'test'

def test_get_processed_file_not_found(client):
    rv = client.get('/processed/nonexistent.png')
    assert rv.status_code == 404