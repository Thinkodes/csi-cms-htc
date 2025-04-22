from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGridLayout, QScrollArea, QFrame, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, QByteArray, QIODevice, QBuffer, QUrl
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget

class FireDetectionWorker(QThread):
    """Worker thread for making API requests without freezing the UI"""
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, cctv_page, demo_file):
        super().__init__()
        self.cctv_page = cctv_page
        self.demo_file = demo_file
        
    def run(self):
        self.result_ready.emit({"result": True if self.demo_file in list(self.cctv_page.room_cards.values())[0].video_file_path else False})
    
    def check_for_detection_mp4(self):
        """Check CCTV room cards for detection files to determine status"""
        result = {"result": False, "confidence": 0.0, "rooms": {}}
        
        detection_detected = False
        detection_rooms = []
        
        # Check each room for detection file
        for room_name, room_card in self.cctv_page.items():
            if hasattr(room_card, 'video_file_path') and room_card.video_file_path:
                is_detected = self.demo_file.lower() in room_card.video_file_path.lower()
                confidence = 0.95 if is_detected else 0.05
                
                # Add to room-specific results
                result["rooms"][room_name] = {
                    "detection_detected": is_detected,
                    "confidence": confidence
                }
                
                if is_detected:
                    detection_detected = True
                    detection_rooms.append(room_name)
        
        # Set overall result
        result["result"] = detection_detected
        result["confidence"] = 0.95 if detection_detected else 0.05
        
        if detection_detected:
            result["message"] = f"{self.name} detected in: {', '.join(detection_rooms)}"
        else:
            result["message"] = f"No {self.name.lower()} detected in any room"
            
        return result


class FireDetectionCard(QFrame):
    """A custom widget representing a room's detection status with improved video player"""
    def __init__(self, room_name, cctv_page, demo_file, avatar, i, detection_name):
        super().__init__()
        self.i = i
        self.room_name = room_name
        self.detection_detected = False  # Default to no detection
        self.confidence = 0.0  # Detection confidence
        self.demo_file = demo_file
        self.cctv_page = cctv_page
        self.avatar = avatar
        self.detection_name = detection_name
        self.setup_ui()
        
    def setup_ui(self):
        self.setMinimumSize(400, 350)  # More flexible sizing
        self.setStyleSheet("""
            FireDetectionCard {
                background-color: #f0f8ff;
                border: 1px solid #cccccc;
                border-radius: 8px;
            }
        """)
        
        # Main layout for the card
        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(10, 10, 10, 10)
        card_layout.setSpacing(8)
        
        # Room name header
        room_label = QLabel(self.room_name)
        room_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #1a1a2e;
            padding-bottom: 5px;
        """)
        room_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(room_label)
        
        # Video container with scroll area
        video_scroll = QScrollArea()
        video_scroll.setWidgetResizable(True)
        video_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #333333;
                border-radius: 4px;
            }
        """)
        
        video_container = QWidget()
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(380, 240)  # Base size
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        video_layout.addWidget(self.video_widget, 0, Qt.AlignmentFlag.AlignCenter)
        video_scroll.setWidget(video_container)
        card_layout.addWidget(video_scroll, 1)  # Add stretch factor
        
        # Media player setup
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)
        
        # Load and play video if available
        if self.cctv_page and hasattr(self.cctv_page, 'room_cards'):
            room_cards = list(self.cctv_page.room_cards.values())
            if room_cards and hasattr(room_cards[self.i], 'video_file_path') and room_cards[self.i].video_file_path:
                self.media_player.setSource(QUrl(room_cards[self.i].video_file_path))
                self.media_player.play()
        
        # Detection status indicator
        self.status_indicator = QLabel(f"No {self.detection_name} Detected")
        self.status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_indicator.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #006400;  /* Dark green for no detection */
            background-color: #e6e6fa;
            padding: 8px;
            border-radius: 4px;
            margin-top: 5px;
        """)
        card_layout.addWidget(self.status_indicator)
        
        # Confidence indicator
        self.confidence_indicator = QLabel("Confidence: 0%")
        self.confidence_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.confidence_indicator.setStyleSheet("""
            font-size: 14px;
            color: #555555;
            margin-top: 5px;
        """)
        card_layout.addWidget(self.confidence_indicator)
        
        # Update display based on initial status
        self.update_display()
        
    def handle_media_status(self, status):
        """Handle media status changes for looping video"""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.media_player.setPosition(0)
            self.media_player.play()
    
    def update_display(self):
        """Update the display based on detection status"""
        if self.detection_detected:
            self.status_indicator.setText(f"{self.detection_name.upper()} DETECTED!")
            self.status_indicator.setStyleSheet("""
                font-size: 16px;
                font-weight: bold;
                color: #8B0000;  /* Dark red for detection */
                background-color: #FFA07A;  /* Light salmon background */
                padding: 8px;
                border-radius: 4px;
                margin-top: 5px;
            """)
        else:
            self.status_indicator.setText(f"No {self.detection_name} Detected")
            self.status_indicator.setStyleSheet("""
                font-size: 16px;
                font-weight: bold;
                color: #006400;  /* Dark green */
                background-color: #e6e6fa;
                padding: 8px;
                border-radius: 4px;
                margin-top: 5px;
            """)
            
        # Update confidence display
        self.confidence_indicator.setText(f"Confidence: {int(self.confidence * 100)}%")
    
    def set_detection_status(self, detected, confidence=0.0):
        """Set the detection status and update display"""
        self.detection_detected = detected
        self.confidence = confidence
        self.update_display()
    
    def resizeEvent(self, event):
        """Handle resize events to maintain proper video proportions"""
        super().resizeEvent(event)
        # You can add additional resize logic here if neededs

class FireDetectionPage(QWidget):
    """Page for displaying detection status of all rooms"""
    def __init__(self, name, cctv_page, demo_file, avatar):
        super().__init__()
        self.name = name
        self.cctv_page = cctv_page
        self.room_cards = {}  # Dictionary to store room cards by name
        self.worker_thread = None  # Store the worker thread
        self.demo_file = demo_file
        self.avatar = avatar
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet("background-color: #f8f9fa;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title for the Detection page
        title = QLabel(f"{self.name} Detection")
        title.setStyleSheet("""
            font-size: 24px;
            color: #1a1a2e;
            font-weight: bold;
            margin-bottom: 15px;
        """)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(f"Monitor {self.name.lower()} detection status across all rooms")
        instructions.setStyleSheet("""
            font-size: 14px;
            color: #555555;
            margin-bottom: 20px;
        """)
        layout.addWidget(instructions)
        
        # Create a scroll area for the grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Container widget for the grid
        self.grid_container = QWidget()
        self.room_grid = QGridLayout(self.grid_container)
        self.room_grid.setContentsMargins(0, 0, 0, 0)
        self.room_grid.setSpacing(15)
        
        self.scroll_area.setWidget(self.grid_container)
        layout.addWidget(self.scroll_area)
        
        # Message for when no rooms are available
        self.no_rooms_message = QLabel("No rooms available. Please configure rooms first.")
        self.no_rooms_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_rooms_message.setStyleSheet("""
            font-size: 16px;
            color: #777777;
            padding: 20px;
        """)
        self.no_rooms_message.setVisible(True)
        layout.addWidget(self.no_rooms_message)
        
        # Status indicator
        self.detection_status = QLabel(f"Ready for {self.name.lower()} detection")
        self.detection_status.setStyleSheet("""
            font-size: 14px;
            color: #555555;
            margin: 10px 0;
        """)
        self.detection_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.detection_status)
        
        # Button container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        
        # Detect button
        detect_button = QPushButton("Detect")
        detect_button.setStyleSheet("""
            QPushButton {
                background-color: #FF4500;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E03E00;
            }
        """)
        detect_button.clicked.connect(self.detect)
        button_layout.addWidget(detect_button)
        
        layout.addWidget(button_container)
    
    def update_rooms(self, room_list):
        """Update the detection cards with rooms from layout page"""
        # Check if we have rooms
        if not room_list:
            self.no_rooms_message.setVisible(True)
            return
        
        self.no_rooms_message.setVisible(False)
        
        # Clear existing room cards
        self.clear_room_grid()
        
        # Add detection cards to grid for each room
        row, col = 0, 0
        max_cols = 2  # Reduced to 2 columns for better video display
        
        for i, room_name in enumerate(room_list):
            detection_card = FireDetectionCard(room_name, self.cctv_page, self.demo_file, self.avatar, i, self.name)
            self.room_grid.addWidget(detection_card, row, col)
            self.room_cards[room_name] = detection_card
            
            # Update grid position
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def clear_room_grid(self):
        """Clear all items from the room grid"""
        # Remove all widgets from the grid
        while self.room_grid.count():
            item = self.room_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Clear the room cards dictionary
        self.room_cards.clear()
    
    def refresh_detection_status(self):
        """Refresh the detection status for all rooms"""
        if not self.room_cards:
            QMessageBox.warning(self, "Warning", "No rooms available to refresh")
            return
            
        # Reset all rooms to no detection
        for room_name, card in self.room_cards.items():
            card.set_detection_status(False, 0.0)
            
        self.detection_status.setText(f"{self.name} detection status reset")
    
    def detect(self):
        """Detect by checking CCTV room cards for specific files"""
        if not self.room_cards:
            QMessageBox.warning(self, "Warning", "No rooms available for detection")
            return
        
        try:
            self.detection_status.setText(f"Checking for {self.name.lower()}...")
            
            # Create worker thread for detection
            self.worker_thread = FireDetectionWorker(self.cctv_page, self.demo_file)
            self.worker_thread.result_ready.connect(self.handle_detection_results)
            self.worker_thread.error_occurred.connect(self.handle_detection_error)
            self.worker_thread.start()
            
        except Exception as e:
            self.detection_status.setText(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to check for {self.name.lower()}: {str(e)}")
    
    def handle_detection_results(self, results):
        """Handle results from detection"""
        try:
            self.detection_status.setText(f"{self.name} detection complete")
            
            # Check if we have room-specific results
            if 'rooms' in results:
                # Update each room's detection status
                for room_name, room_data in results['rooms'].items():
                    if room_name in self.room_cards:
                        self.room_cards[room_name].set_detection_status(
                            room_data.get('detection_detected', False),
                            room_data.get('confidence', 0.0)
                        )
                
                # Check if any room has detection
                any_detected = any(room_data.get('detection_detected', False) for room_data in results['rooms'].values())
                if any_detected:
                    detected_rooms = [room_name for room_name, room_data in results['rooms'].items() 
                                 if room_data.get('detection_detected', False)]
                    self.detection_status.setText(f"{self.name} detected in: {', '.join(detected_rooms)}")
                else:
                    self.detection_status.setText(f"No {self.name.lower()} detected in any room")
            
            # Handle general results
            elif 'result' in results:
                if results['result']:
                    # Find rooms that reported detection
                    if 'message' in results:
                        self.detection_status.setText(results['message'])
                    else:
                        self.detection_status.setText(f"{self.name} detected!")
                    
                    # If no specific room information, pick a random room to show detection
                    import random
                    detected_rooms = []
                    
                    for room_name, card in self.room_cards.items():
                        # Check if we have CCTV page with room cards
                        if (self.cctv_page and hasattr(self.cctv_page, 'room_cards') and 
                            room_name in self.cctv_page.room_cards):
                            cctv_card = self.cctv_page.room_cards[room_name]
                            if (hasattr(cctv_card, 'video_file_path') and 
                                cctv_card.video_file_path and 
                                self.demo_file.lower() in cctv_card.video_file_path.lower()):
                                detected_rooms.append(room_name)
                                card.set_detection_status(True, results.get('confidence', 0.95))
                            else:
                                card.set_detection_status(False, 0.05)
                        else:
                            # If we can't check CCTV, just pick one random room
                            if not detected_rooms:
                                detected_room = random.choice(list(self.room_cards.keys()))
                                detected_rooms = [detected_room]
                                
                            is_detected_room = room_name in detected_rooms
                            card.set_detection_status(is_detected_room, 
                                               0.95 if is_detected_room else 0.05)
                else:
                    # No detection detected
                    for card in self.room_cards.values():
                        card.set_detection_status(False, results.get('confidence', 0.05))
                    self.detection_status.setText(f"No {self.name.lower()} detected in any room")
            else:
                QMessageBox.warning(self, "Warning", "Invalid response format from detection")
                
        except Exception as e:
            self.detection_status.setText(f"Error processing results: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to process detection results: {str(e)}")
    
    def handle_detection_error(self, error_message):
        """Handle API request errors"""
        self.detection_status.setText(f"Error: {error_message}")
        QMessageBox.critical(self, "API Error", error_message)