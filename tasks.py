import os
from celery import Celery
from upscale import upscale_image

app = Celery('tasks', broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
             backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

PROCESSED_DIR = 'processed'

@app.task(bind=True)
def upscale_task(self, image_bytes: bytes, task_id: str):
    try:
        result_bytes = upscale_image(image_bytes)
        filename = f"{task_id}.png"
        filepath = os.path.join(PROCESSED_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(result_bytes)
        return filename
    except Exception as e:
        self.update_state(state='FAILURE', meta=str(e))
        raise