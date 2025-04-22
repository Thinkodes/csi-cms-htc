"""
Author: Ansh Mathur
Github: github.com/Fakesum
Repo: github.com/Thinkodes/CMS
"""
import cv2
import numpy as np
import os

from ..utils import logger
if "CMS_ACTIVE" in os.environ:
    from . import model

def crop_yolo_detections(image, detections):
    """
    Crop individual detections from an image based on YOLO output
    
    Args:
        image: Input image (numpy array)
        detections: List of YOLO detections in format [x_center, y_center, width, height]
    
    Returns:
        List of cropped images for each detection
    """
    cropped_images = []
    img_height, img_width = image.shape[:2]
    
    for det in detections:
        # YOLO format: [x_center, y_center, width, height] (normalized 0-1)
        x_center, y_center, w, h = det
        
        # Convert from normalized coordinates to pixel coordinates
        x_center *= img_width
        y_center *= img_height
        w *= img_width
        h *= img_height
        
        # Calculate bounding box coordinates
        x1 = int(x_center - w/2)
        y1 = int(y_center - h/2)
        x2 = int(x_center + w/2)
        y2 = int(y_center + h/2)
        
        # Ensure coordinates are within image bounds
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(img_width - 1, x2)
        y2 = min(img_height - 1, y2)
        
        # Crop and save the detection
        cropped = image[y1:y2, x1:x2]
        cropped_images.append(cropped)
    
    return cropped_images

def segment_faces_from_image(image):
    _results = [result.boxes.xywhn.detach().cpu().numpy().tolist() for result in model(image)]
    results = []
    for res in _results:
        results.extend(res)
    images = crop_yolo_detections(image, results)
    return images, results