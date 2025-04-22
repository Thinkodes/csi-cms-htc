"""
Author: Ansh Mathur
Github: github.com/Fakesum
Repo: github.com/Thinkodes/CMS
"""
import os

if "CMS_ACTIVE" in os.environ:
    if not os.path.exists("face-detection.pt"):
        from huggingface_hub import hf_hub_download
        
        downloaded_file = hf_hub_download(repo_id="AdamCodd/YOLOv11n-face-detection", filename="model.pt", local_dir=".", local_dir_use_symlinks=False)
        os.rename(downloaded_file, os.path.join(os.getcwd(), "face-detection.pt"))

    from ultralytics import YOLO

    model = YOLO("face-detection.pt")