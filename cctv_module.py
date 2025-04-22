import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGridLayout, QScrollArea, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon

class VideoCard(QFrame):
    """A custom widget representing a room's video feed configuration"""
    video_configured = pyqtSignal(str, str)  # Signal: room_name, video_path
    
    def __init__(self, room_name="Room X"):
        super().__init__()
        self.room_name = room_name
        self.video_file_path = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedSize(320, 240)
        self.setStyleSheet("""
            VideoCard {
                background-color: #f0f8ff;  /* Light blue background */
                border: 1px solid #cccccc;  /* Simple gray border */
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
        
        # Container widget for camera button to ensure center alignment
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        
        # Camera button
        self.camera_button = QPushButton()
        self.camera_button.setFixedSize(80, 80)
        
        # Set default icon - for unconfigured state
        icon_path = "camera_icon.png"
        icon2_path = "video_icon.png"  # Path for the configured state icon
        
        # Set initial icon or fallback style
        if os.path.exists(icon_path):
            self.camera_button.setIcon(QIcon(icon_path))
            self.camera_button.setIconSize(QSize(60, 60))
        else:
            # Fallback styling if icon not found
            self.camera_button.setStyleSheet("""
                QPushButton {
                    background-color: #bbadf0;
                    border-radius: 40px;
                    border: 2px solid #9683ec;
                }
                QPushButton:hover {
                    background-color: #a394e0;
                }
            """)
        
        self.camera_button.clicked.connect(self.upload_video)
        
        # Center align the button
        button_layout.addStretch(1)
        button_layout.addWidget(self.camera_button)
        button_layout.addStretch(1)
        
        card_layout.addWidget(button_container)
        
        # Configure text
        self.config_label = QLabel("Press to configure your\nCCTV video frame")
        self.config_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.config_label.setStyleSheet("""
            font-size: 14px;
            color: #555555;
            margin-top: 5px;
        """)
        card_layout.addWidget(self.config_label)
        
        # Status bar
        self.status_bar = QLabel("Video not configured")
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
    
    def upload_video(self):
        """Handle video file selection and update UI"""
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Video files (*.mp4 *.avi *.mov *.wmv *.mkv)")
        file_dialog.setViewMode(QFileDialog.ViewMode.List)
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.video_file_path = selected_files[0]
                file_name = os.path.basename(self.video_file_path)
                
                # Update status message
                self.status_bar.setText(f"Video: {file_name}")
                self.status_bar.setStyleSheet("""
                    font-size: 12px;
                    color: #006400;  /* Dark green for success */
                    background-color: #e6e6fa;
                    padding: 5px;
                    border-radius: 4px;
                    margin-top: 5px;
                """)
                
                # Update label text
                self.config_label.setText("Video feed configured")
                
                # Change icon to video_icon if exists, otherwise change button style
                icon2_path = "video_icon.png"
                if os.path.exists(icon2_path):
                    self.camera_button.setIcon(QIcon(icon2_path))
                    self.camera_button.setIconSize(QSize(60, 60))
                else:
                    # Fallback: change button color to indicate configured state
                    self.camera_button.setStyleSheet("""
                        QPushButton {
                            background-color: #90ee90;  /* Light green for success */
                            border-radius: 40px;
                            border: 2px solid #32cd32;
                        }
                        QPushButton:hover {
                            background-color: #7ccd7c;
                        }
                    """)
                
                # Emit signal that video was configured
                self.video_configured.emit(self.room_name, self.video_file_path)


class CCTVConfigPage(QWidget):
    """Page for configuring CCTV cameras for different rooms"""
    def __init__(self):
        super().__init__()
        self.room_cards: dict[str, VideoCard] = {}  # Dictionary to store room cards by name
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet("background-color: #f8f9fa;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title for the CCTV configuration page
        title = QLabel("CCTV Configuration")
        title.setStyleSheet("""
            font-size: 24px;
            color: #1a1a2e;
            font-weight: bold;
            margin-bottom: 15px;
        """)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("Configure video feeds for rooms defined in the Layout Map")
        instructions.setStyleSheet("""
            font-size: 14px;
            color: #555555;
            margin-bottom: 20px;
        """)
        layout.addWidget(instructions)
        
        # Create a scroll area for the grid to handle many rooms
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
        self.no_rooms_message = QLabel("No rooms available. Please define rooms in the Layout Map first.")
        self.no_rooms_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_rooms_message.setStyleSheet("""
            font-size: 16px;
            color: #777777;
            padding: 20px;
        """)
        self.no_rooms_message.setVisible(True)
        layout.addWidget(self.no_rooms_message)
        
        # Button to refresh room list (for development/testing)
        refresh_button = QPushButton("Refresh Room List")
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
        refresh_button.clicked.connect(self.refresh_from_layout)
        layout.addWidget(refresh_button)
    
    def update_rooms(self, room_list):
        """Update the room grid with rooms from layout page"""
        # Check if we have rooms
        if not room_list:
            self.no_rooms_message.setVisible(True)
            return
        
        self.no_rooms_message.setVisible(False)
        
        # Clear existing room cards
        self.clear_room_grid()
        
        # Add video cards to grid for each room
        row, col = 0, 0
        max_cols = 3  # Number of columns in the grid
        
        for room_name in room_list:
            video_card = VideoCard(room_name)
            video_card.video_configured.connect(self.on_video_configured)
            self.room_grid.addWidget(video_card, row, col)
            self.room_cards[room_name] = video_card
            
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
        
        # Clear the dictionary
        self.room_cards.clear()
    
    def refresh_from_layout(self):
        """This is a development function to trigger a refresh"""
        # In a real application, this would likely come from a signal
        # For now, we'll just update with some sample rooms
        self.update_rooms([
            "Reception", "Main Entrance", "Corridor A", 
            "Office 101", "Conference Room", "Parking Area"
        ])
    
    def on_video_configured(self, room_name, video_path):
        """Handle when a video is configured for a room"""
        print(f"Video configured for {room_name}: {video_path}")
        # In a real application, you might want to store this configuration
        # or notify other parts of the application