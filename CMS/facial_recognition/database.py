"""
Author: Ansh Mathur
Github: github.com/Fakesum
Repo: github.com/Thinkodes/CMS
"""
import base64
import traceback
import os
from datetime import datetime
from ..utils import logger, cv2image_to_base64
from tinydb import TinyDB, Query
import face_recognition
import numpy as np

class FaceDatabase:
    def __init__(self, db_path='face_db.json'):
        self.db = TinyDB(db_path)
        self.face_table = self.db.table('faces')
        self.query = Query()
    
    def _encode_face(self, image, *args, **kwargs):
        encodings = face_recognition.face_encodings(image, *args, **kwargs)
        if len(encodings) == 0:
            return None
        return encodings[0]

    def add_face(self, image, unique_key, is_admin=False,room_access=[], name='', desc=''):
        """
        Store a face from CCTV footage with a unique identifier
        Returns True if successful, False otherwise
        """
        try:
            encodings = face_recognition.face_encodings(image)
            
            if not encodings:
                return False

            # Store in database
            self.face_table.insert({
                'unique_key': unique_key,
                "face_encoding": encodings[0].tolist(),
                "name": name,
                "desc": desc,
                "rooms_access": room_access,
                "admin": is_admin,
                'image_data': cv2image_to_base64(image),
                'timestamp': datetime.now().isoformat()
            })
            return True
            
        except Exception as e:
            logger.error(f"Error while adding faces to database: {traceback.format_exc()}")
            return False

    def find_match(self, encoding, tolerance=0.6):
        """
        Check if a face from CCTV footage exists in the database
        Returns matching record or None
        """
        try:
            # Get all stored faces
            records = self.face_table.all()
            
            # Convert stored encodings to numpy arrays
            stored_encodings = [np.array(record['face_encoding']) for record in records]
            
            # Find matches
            matches = face_recognition.compare_faces(
                stored_encodings, 
                encoding, 
                tolerance=tolerance
            )
            
            # Return first match with original data
            for match, record in zip(matches, records):
                if match:
                    return {
                        'unique_key': record['unique_key'],
                        'image': record['image_data'],
                        'timestamp': record['timestamp'],
                        "name": record["name"],
                        "desc": record["desc"],
                        "encoding": record["face_encoding"]
                    }
            return None
            
        except Exception as e:
            logger.error(f"Error while finding faces in database: {traceback.format_exc()}")
            return None
    
    def compare_face(self, face1, face2, tol=0.6):
        return face_recognition.compare_faces(face1, face2, tolerance=tol)[0]

    def get_face(self, unique_key):
        """Retrieve a face record by its unique key"""
        return self.face_table.get(self.query.unique_key == unique_key)

if "CMS_ACTIVE" in os.environ:
    face_database = FaceDatabase()