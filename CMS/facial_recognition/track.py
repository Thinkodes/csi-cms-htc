"""
Author: Ansh Mathur
Github: github.com/Fakesum
Repo: github.com/Thinkodes/CMS
"""
import os
if "CMS_ACTIVE" in os.environ:
    from . import model
    from .database import face_database
from .segmentor import crop_yolo_detections
from ..utils import logger

def track_faces(frame):
    return model.track(frame,
        persist=True,  # For tracking between frames
        classes=[0],
        verbose=False,
    )[0]

def find_all_faces(frame):
    _results = [result.boxes.xywhn.detach().cpu().numpy().tolist() for result in model(frame)]
    results = []
    for res in _results:
        results.extend(res)
    
    images = crop_yolo_detections(frame, results)
    _results = []
    for i in range(len(results)):
        _results.append({"yolo_result": results[i], "encoding": face_database._encode_face(images[i])})
    return _results