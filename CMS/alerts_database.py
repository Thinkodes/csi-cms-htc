"""
Author: Ansh Mathur
Github: github.com/Fakesum
Repo: github.com/Thinkodes/CMS
"""
from tinydb import TinyDB, Query
from datetime import datetime

class TinyDBAlertSystem:
    def __init__(self):
        # Initialize an in-memory TinyDB instance
        self.db = TinyDB("alerts.json")
        # Create tables for each alert type
        self.urgent_table = self.db.table('urgent')
        self.warnings_table = self.db.table('warnings')
        self.information_table = self.db.table('information')
        # Track the last inserted document ID for each table
        self.last_ids = {
            'urgent': None,
            'warnings': None,
            'information': None
        }

        self.to_be_autherized = []

    def register_urgent_alert(self, request):
        """Register a new urgent alert."""
        doc_id = self.urgent_table.insert({
            'message': request["message"],
            "timestamp": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
            "role": request["role"] if "role" in request else "all",
            "signatory":"unautherized",
            "autherized": False,
            "room_id": (request["room_id"] if "room_id" in request else None)})
        self.to_be_autherized.append(doc_id)
        self.last_ids['urgent'] = doc_id
    
    def get_unautherized(self, room_id=None):
        alerts = {}
        for unautherized_ids in self.to_be_autherized:
            doc = self.urgent_table.get(doc_id=unautherized_ids)
            if (room_id != None) and (doc["room_id"] != room_id):
                continue
            alerts[unautherized_ids] = doc
        
        return alerts

    def autherize(self, _id, signatory):
        self.urgent_table.update({"autherized": True, "signatory": signatory}, doc_ids=[_id])

    def register_warning_alert(self, request):
        """Register a new warning alert."""
        doc_id = self.warnings_table.insert({'message': request["message"], "timestamp": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"), "role": request["role"] if "role" in request else "all"})
        self.last_ids['warnings'] = doc_id

    def register_information_alert(self, request):
        """Register a new information alert."""
        doc_id = self.information_table.insert({'message': request["message"], "timestamp": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"), "role": request["role"] if "role" in request else "all"})
        self.last_ids['information'] = doc_id

    def get_newest_urgent_alert(self):
        """Retrieve the most recent urgent alert."""
        res = self._get_newest_alert('urgent')
        if res != None:
            return res["message"]

    def get_newest_warning_alert(self):
        """Retrieve the most recent warning alert."""
        res = self._get_newest_alert('warnings')
        if res != None:
            return res["message"]

    def get_newest_information_alert(self):
        """Retrieve the most recent information alert."""
        res = self._get_newest_alert('information')
        if res != None:
            return res["message"]

    def _get_newest_alert(self, alert_type):
        """Helper method to fetch the latest alert from a specified table."""
        last_id = self.last_ids[alert_type]
        if last_id is None:
            return None
        # Fetch the document using the tracked ID
        table = getattr(self, f'{alert_type}_table')
        doc = table.get(doc_id=last_id)
        if (doc != None) and (alert_type == "urgent") and (not doc["autherized"]):
            doc = None
        return doc if doc else None

import os
if "CMS_ACTIVE" in os.environ:
    alerts_database = TinyDBAlertSystem()