from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, 
    QGridLayout, QScrollArea, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget


class VectorMapCard(QFrame):
    """A custom widget representing a room's vector map video"""
    def __init__(self, demo_name, real_name, name, room_name="Room X", video_path=None):
        super().__init__()
        self.name = name
        self.room_name = room_name
        self.video_file_path = video_path
        self.demo_name = demo_name
        self.real_name = real_name
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedSize(320, 280)  # Match CCTV card size
        self.setStyleSheet("""
            VectorMapCard {
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
        
        # Video player widget
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(300, 180)  # Match CCTV card size
        self.video_widget.setStyleSheet("""
            background-color: #333333;
            border-radius: 4px;
        """)
        card_layout.addWidget(self.video_widget)
        
        # Media player
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)
        
        # Status bar
        self.status_bar = QLabel(f"No {self.name} configured" if not self.video_file_path else f"{self.name} loaded")
        self.status_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_bar.setStyleSheet("""
            font-size: 12px;
            color: #777777;
            background-color: #e6e6fa;
            padding: 5px;
            border-radius: 4px;
            margin-top: 5px;
        """)
        card_layout.addWidget(self.status_bar)
        
        # Load video if path was provided
        if self.video_file_path:
            
            self.load_video(self.video_file_path)
    
    def handle_media_status(self, status):
        """Handle media status changes for looping video"""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.media_player.setPosition(0)
            self.media_player.play()
    
    def load_video(self, video_path):
        """Load and play the video from the given path"""
        if self.demo_name in video_path:
            video_path = self.real_name
        self.video_file_path = video_path
        self.media_player.setSource(QUrl(video_path))
        self.media_player.play()
        
        # Update status
        import datetime
        self.status_bar.setText(f"{self.name} loaded at time {datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")}")
        self.status_bar.setStyleSheet("""
            font-size: 12px;
            color: #006400;
            background-color: #e6e6fa;
            padding: 5px;
            border-radius: 4px;
            margin-top: 5px;
        """)


class VectorMapsPage(QWidget):
    """Page for displaying vector maps of all rooms"""
    def __init__(self, cctv_page, demo_name, real_name, name):
        super().__init__()
        self.name = name
        self.cctv_page = cctv_page  # Reference to CCTV page to get video paths
        self.room_cards = {}  # Dictionary to store room cards by name
        self.demo_name = demo_name
        self.real_name = real_name
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet("background-color: #f8f9fa;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title for the Vector Maps page
        title = QLabel("Vector Maps")
        title.setStyleSheet("""
            font-size: 24px;
            color: #1a1a2e;
            font-weight: bold;
            margin-bottom: 15px;
        """)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("View vector map representations of room occupancy and movement patterns")
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
        self.no_rooms_message = QLabel("No rooms available. Please configure CCTV videos first.")
        self.no_rooms_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_rooms_message.setStyleSheet("""
            font-size: 16px;
            color: #777777;
            padding: 20px;
        """)
        self.no_rooms_message.setVisible(True)
        layout.addWidget(self.no_rooms_message)
        
        # Refresh button
        refresh_button = QPushButton("Refresh Vector Maps")
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #4cc9f0;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3db8df;
            }
        """)
        refresh_button.clicked.connect(self.refresh_vector_maps)
        layout.addWidget(refresh_button)
    
    def update_rooms(self, room_list):
        """Update the vector maps with rooms from layout page and videos from CCTV page"""
        # Check if we have rooms
        if not room_list:
            self.no_rooms_message.setVisible(True)
            return
        
        self.no_rooms_message.setVisible(False)
        
        # Clear existing room cards
        self.clear_room_grid()
        
        # Add vector map cards to grid for each room
        row, col = 0, 0
        max_cols = 3  # Match CCTV page's 3-column layout
        
        for room_name in room_list:
            # Get video path from CCTV page if available
            video_path = None
            if self.cctv_page and room_name in self.cctv_page.room_cards:
                video_path = self.cctv_page.room_cards[room_name].video_file_path
            
            vector_map_card = VectorMapCard(self.demo_name, self.real_name, self.name, room_name, video_path)
            self.room_grid.addWidget(vector_map_card, row, col)
            self.room_cards[room_name] = vector_map_card
            
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
    
    def refresh_vector_maps(self):
        """Refresh the vector maps display"""
        # In a real application, this would regenerate vector maps from current videos
        QMessageBox.information(self, "Info", "Vector maps refreshed with latest data")
        
        # For demonstration, just update the display
        if hasattr(self.cctv_page, 'room_cards'):
            for room_name, card in self.room_cards.items():
                if room_name in self.cctv_page.room_cards:
                    cctv_card = self.cctv_page.room_cards[room_name]
                    if cctv_card.video_file_path:
                        card.load_video(cctv_card.video_file_path)