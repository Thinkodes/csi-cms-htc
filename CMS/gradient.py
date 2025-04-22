"""
Author: Ansh Mathur
Github: github.com/Fakesum
Repo: github.com/Thinkodes/CMS
"""
import time
from ultralytics import YOLO
from .utils import logger
import numpy as np
import logging
import cv2
import os

logger.info("LOADING YOLO...")

# This is not particularly intensive, so load it regardless I guess. Causes much less problems.
if "CMS_ACTIVE" in os.environ:
    model = YOLO("yolo11n.pt")  # Specify 'cuda' to use GPU

# #redirect YOLO Logging
def __bootstrap_yolo():

    # Configure YOLO's logger to use your custom logger
    yolo_logger = logging.getLogger("ultralytics")

    # Remove existing handlers from YOLO's logger
    for handler in yolo_logger.handlers.copy():
        yolo_logger.removeHandler(handler)

    # Prevent YOLO's logs from propagating to the root logger
    yolo_logger.propagate = False

    # Create a handler to forward YOLO's logs to your logger
    class ForwardingHandler(logging.Handler):
        def emit(self, record):
            logger.log(record.levelname.upper(), record.getMessage())

    yolo_logger.addHandler(ForwardingHandler())

__bootstrap_yolo()

def create_gradient(image_np, conf=0.5, scale_factor=0.01, _kernel_size=500):
    st = time.time()

    logger.info("Calculating Gradient.")

    height, width, _ = image_np.shape

    # Detect people using YOLOv8
    results = model(image_np)
    points = []
    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()
        confidences = result.boxes.conf.cpu().numpy()
        class_ids = result.boxes.cls.cpu().numpy()

        for i in range(len(boxes)):
            if confidences[i] > conf and class_ids[i] == 0:  # Class 0 for person
                x1, y1, x2, y2 = boxes[i]
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                points.append((center_x, center_y))

    # Create density map
    scaled_width = int(width * scale_factor)
    scaled_height = int(height * scale_factor)
    density_map = np.zeros((scaled_height, scaled_width), dtype=np.float32)

    # Accumulate points
    for x, y in points:
        scaled_x = int(x * scale_factor)
        scaled_y = int(y * scale_factor)
        if 0 <= scaled_x < scaled_width and 0 <= scaled_y < scaled_height:
            density_map[scaled_y, scaled_x] += 1

    # Apply Gaussian blur
    kernel_size = int(_kernel_size * scale_factor)
    kernel_size = kernel_size + 1 if kernel_size % 2 == 0 else kernel_size
    blurred = cv2.GaussianBlur(density_map, (kernel_size, kernel_size), 0)

    # Resize back to original dimensions
    density_map = cv2.resize(blurred, (width, height), interpolation=cv2.INTER_LINEAR)

    # Normalize and invert
    density_map = cv2.normalize(density_map, None, 255, 0, cv2.NORM_MINMAX)
    density_map = np.uint8(density_map)
    
    import os

    # some weirdness where cv2 is activing differently depending on the 
    if os.name == 'nt':
        density_map = cv2.bitwise_not(density_map)

    heatmap = cv2.applyColorMap(density_map, cv2.COLORMAP_JET)
    
    logger.info("Gradient processing completed successfully")

    logger.debug(f"Time Taken for Gradient: {time.time() - st}")

    return heatmap