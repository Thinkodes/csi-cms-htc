"""
Author: Ansh Mathur
Github: github.com/Fakesum
Repo: github.com/Thinkodes/CMS
"""
import os, datetime
import cv2
from loguru import logger
import speech_recognition as sr
import numpy as np
import io
from PIL import Image
import base64
import flask

def get_image_file(image = None):
    """get the image sent as json base64 format from the request
    MUST BE CALLED FROM WITHIN A FLASK REQUEST CALLBACK.

    Returns:
        numpy.ndarray: a cv2 image with colors.
    """
    if image == None:
        image = flask.request.json['image']
    image_file = base64.b64decode(image)
    image = Image.open(io.BytesIO(image_file))
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image_np = np.array(image)

    return image_np

def get_images_file() -> list[np.ndarray]:
    images = flask.request.json['images']
    results = []
    for image in images:
        image_file = base64.b64decode(image)
        image = Image.open(io.BytesIO(image_file))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        results.append( np.array(image))

    return results

def generate_log_file(log_dir="logs"):
    """Generate a log file with a name based on the current time."""
    os.makedirs(log_dir, exist_ok=True)
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_name = f"log_{current_time}.log"
    log_file_path = os.path.join(log_dir, log_file_name)
    with open(log_file_path, "w") as f:
        f.write("")  # Create an empty file
    return log_file_path

def cv2image_to_base64(image):
    _, buffer = cv2.imencode('.png', image)
    return base64.b64encode(buffer.tobytes()).decode()

def recognize_from_wav_bytes(wav_bytes):
    # Create a file-like object from bytes
    with io.BytesIO(wav_bytes) as wav_file:
        # Use SpeechRecognition to read the WAV file
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_file) as source:
            audio_data = recognizer.record(source)
            
            try:
                # Use Google Web Speech API (requires internet)
                text = recognizer.recognize_google(audio_data)
                return text
            except sr.UnknownValueError:
                return "Could not understand audio"
            except sr.RequestError:
                return "API unavailable"

logger_file = generate_log_file()
logger.add(logger_file, rotation="10 MB", level="DEBUG")

class DetectionPrompts:
    FIRE = "is there fire."
    STAMPEED = "is there a stampeed happening?"
    FALL = "is there a fall."
    SMOKE = "is there smoke?",
    VOILENCE = "is there voilence?",
    DANGER = "is there danger?"