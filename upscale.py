import cv2
import numpy as np
from cv2 import dnn_superres

_scaler = None

def _get_scaler():
    global _scaler
    if _scaler is None:
        _scaler = dnn_superres.DnnSuperResImpl_create()
        _scaler.readModel('EDSR_x2.pb')
        _scaler.setModel("edsr", 2)
    return _scaler

def upscale_image(image_bytes: bytes) -> bytes:
    """
    Принимает байты изображения, возвращает байты увеличенного изображения (PNG).
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Invalid image data")

    result = _get_scaler().upsample(img)

    success, buffer = cv2.imencode('.png', result)
    if not success:
        raise RuntimeError("Failed to encode image")

    return buffer.tobytes()