import os
import uuid
from flask import Flask, request, jsonify, send_file
from celery import Celery
from tasks import upscale_task

app = Flask(__name__)

app.config['CELERY_BROKER_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

PROCESSED_DIR = 'processed'
os.makedirs(PROCESSED_DIR, exist_ok=True)

@app.route('/upscale', methods=['POST'])
def upscale():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    image_bytes = file.read()
    task_id = str(uuid.uuid4())
    upscale_task.apply_async(args=[image_bytes, task_id], task_id=task_id)
    return jsonify({'task_id': task_id}), 202

@app.route('/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    task = upscale_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {'state': task.state, 'status': 'Task is pending...'}
    elif task.state == 'SUCCESS':
        response = {'state': task.state, 'result_url': f'/processed/{task.result}'}
    else:
        response = {'state': task.state, 'status': str(task.info) if task.info else 'Error'}
    return jsonify(response)

@app.route('/processed/<filename>', methods=['GET'])
def get_processed_file(filename):
    safe_path = os.path.join(PROCESSED_DIR, filename)
    if not os.path.exists(safe_path):
        return jsonify({'error': 'File not found'}), 404
    return send_file(safe_path, as_attachment=True, download_name=filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)