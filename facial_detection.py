import sys
import os
import shutil
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, 
                            QFileDialog, QVBoxLayout, QWidget, QMessageBox)
from PyQt6.QtCore import Qt
from cctv_module import CCTVConfigPage

class FileCopyWidget(QWidget):
    def __init__(self, source_file, cctv_page: CCTVConfigPage):
        super().__init__()
        
        # Store the source file path
        self.source_file = source_file
        self.cctv_page = cctv_page
        
        # Create central widget and layout
        layout = QVBoxLayout(self)
        
        # Create the button
        self.copy_button = QPushButton("Copy File")
        self.copy_button.setFixedSize(200, 50)
        self.copy_button.clicked.connect(self.copy_file)
        
        # Add button to layout and center it
        layout.addWidget(self.copy_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def copy_file(self):
        """Handle the button click event"""
        # If source file not provided at initialization, ask for it now
        if not any([(card.video_file_path != None) for card in self.cctv_page.room_cards.values()]):
            QMessageBox.warning(self, "No Rooms found for facial detections", "Facial Detection, Occurs when the Rooms have attached a video_file with them.")
            return
        
        # Ask where to save the file
        file_name = os.path.basename(self.source_file)
        destination, _ = QFileDialog.getSaveFileName(
            self, "Save File As", file_name, "All Files (*)")
        
        if destination:  # User selected a destination
            try:
                shutil.copy2(self.source_file, destination)
                QMessageBox.information(self, "Success", 
                                        f"File Saved successfully to {destination}")
            except:
                import traceback
                traceback.print_exc()