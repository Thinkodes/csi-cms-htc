"""
Author: Ansh Mathur
Github: github.com/Fakesum
Repo: github.com/Thinkodes/CMS
"""
import traceback
from datetime import datetime
import threading
import time
import os

if "CMS_ACTIVE" in os.environ:
    from .facial_recognition.database import face_database
    from .gradient import model, create_gradient
    from .florence import florence_endpoint
from .facial_recognition.track import track_faces, find_all_faces
from collections import defaultdict
from .utils import logger, cv2image_to_base64, DetectionPrompts

class Room:
    PAST_FRAMES = 24

    def __init__(self, room_id, room_name, room_capacity, is_exit):
        self._id = room_id
        self.room_capacity = room_capacity
        self.room_name = room_name
        self.past_frames: list = []

        self.people = []

        self.connected_roomids = []

        self.is_exit = is_exit

        self._run_frame_detection = False
        self._processing_frame = False

        self.alive = True
        self.frame_detection_thread = threading.Thread(target=self.run_frame_detection, daemon=True)
        self.frame_detection_thread.start()
    
    def _florence_endpoint(self, prompts):
        """Find the number of people in the room with the help
        of florence VQA features.

        Returns:
            int: number of people in the room.
        """
        if len(self.past_frames) == 0:
            return None
        try:
            result = florence_endpoint(self.past_frames[-1], prompts)
        except:
            logger.error(f"Error: {traceback.format_exc()}")
            return None # noqa, this has the same return as if 
            # there was no frame. but it can also be caused by quirky responses by florence.
        
        return result

    def population(self):
        try:
            return int(self._florence_endpoint(["how many people?"])[0])
        except:
            logger.error("Florence gave a non numerical response when asked about the number of people in the room.")
            return None
    
    def density(self):
        return self.population()/self.room_capacity
    
    def vector_map(self):
        track_history = defaultdict(lambda: [])
        
        frame = None
        for i in range(min([self.PAST_FRAMES, len(self.past_frames)])):

            frame = self.past_frames[i]

            # Run YOLO tracking
            results = model.track(frame, persist=True, tracker="bytetrack.yaml", classes=[0])  # 0 = person class

            if results[0].boxes.id is not None:
                boxes = results[0].boxes.xywh.cpu()
                track_ids = results[0].boxes.id.int().cpu().tolist()

                for box, track_id in zip(boxes, track_ids):
                    x, y, w, h = box
                    center = (float(x), float(y))
                    
                    # Store trajectory
                    track = track_history[track_id]
                    track.append(center)
                    if len(track) > 30:  # Limit trajectory length
                        track.pop(0)


        logger.debug(f"Calculated Track History: {track_history}, for room: {self.__repr__()}")
        return dict(track_history)

    def clean_old_data(self):
        self.past_frames = self.past_frames[len(self.past_frames)-self.PAST_FRAMES:]

    def _check_for_autherization(self, tol=0.6):
        unautherized_faces = []
        frame = self.past_frames[-1]
        for face in find_all_faces(frame):
            encoding = face["encoding"]
            if encoding == None:
                unautherized_faces.append({"autherized": False, "state": 0, "reason": "Unclear", "detection": face["yolo_result"]})
                continue
            record = face_database.find_match(encoding, tol)

            # if a record was not found or if the access was not autherized.
            if (record == None) or ((not record["admin"]) and (not self._id in record["rooms_access"])):
                unautherized_faces.append({"autherized": False,"state": 1, "reason": "Unautherized person.", "detection": face["yolo_result"]})
                continue
            else:
                unautherized_faces.append({"autherized": True,"state": 2, "reason": "Autherized", "detection": face["yolo_result"]})
        return unautherized_faces, frame
    
    
    def connect_room(self, conn_room_id):
        self.connected_roomids.append(conn_room_id)
    
    def append_frame(self, frame):
        self.past_frames.append(frame)
        self.clean_old_data()

        self._run_frame_detection = True

    def run_frame_detection(self):
        """
        Processes YOLO face detection results and identifies individuals using facial recognition.
        
        Args:
            yolo_track_results (ultralytics.yolo.engine.results.Results): YOLO detection results object
        
        Returns:
            list: Names of recognized individuals or 'unregistered' for unknown faces
        """

        while True:
            if not self._run_frame_detection:
                time.sleep(3)
                continue

            if not self.alive:
                return
            logger.info(f"Starting Processing of room: {self.__repr__()}")

            frame = self.past_frames[-1]
            
            self._processing_frame = True

            self.people = []

            track_res = track_faces(frame)
            
            for box in track_res.boxes.xyxy.cpu().numpy():
                
                x1, y1, x2, y2 = box

                face_location = (y1, x2, y2, x1)
                
                face_encodings = face_database._encode_face(frame, [face_location])
                
                if isinstance(face_encodings,type(None)):
                    logger.warning("Face Not detected by facial recognition, but detected by yolo.")
                    continue
                    
                current_encoding = face_encodings[0]
                
                current_person = face_database.find_match(current_encoding)
                if current_person == None:
                    current_person = {
                        'unique_key': "unautherized",
                        'image': frame,
                        'timestamp': datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
                        "name": "unautherized",
                        "desc": "unautherized",
                        "encoding": current_encoding,
                    }
                
                self.people.append(current_person)
            
            self._processing_frame = False
            self._run_frame_detection = False

            logger.info(f"Finished Processing of room: {self.__repr__()}")
    
    def danger_checks(self):
        prompts = [DetectionPrompts.FIRE,
                   DetectionPrompts.STAMPEED,
                   DetectionPrompts.FALL,
                   DetectionPrompts.SMOKE,
                   DetectionPrompts.VOILENCE,
                   DetectionPrompts.DANGER,
                   ]
        res = self._florence_endpoint(prompts)
        res = {prompts[i]: res[i] for i in range(len(res))}
        logger.debug(f"Result of checking danger: {res}")
        return res

    def _create_gradient(self, kernel_size, scale_factor):
        return cv2image_to_base64(create_gradient(self.past_frames[-1], kernel_size=kernel_size, scale_factor=scale_factor))
    
    def remove(self):
        while self._processing_frame:
            time.sleep(1)
        self.alive = False

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Room(_id = {self._id}, room_capacity={self.room_capacity}, room_name={self.room_name}, c_past_frames={len(self.past_frames)}, connected_roomids={self.connected_roomids}, is_exit={self.is_exit})"