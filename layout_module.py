from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGridLayout, QScrollArea, QFrame, QDialog, QDialogButtonBox,
    QFormLayout, QLineEdit, QSpinBox, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

class RoomConnectionDialog(QDialog):
    """Dialog for adding a new connection between rooms"""
    def __init__(self, room_names, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Connection")
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.connection_name = QLineEdit()
        form_layout.addRow("Connection Name:", self.connection_name)
        
        self.room1_combo = QComboBox()
        self.room1_combo.addItems(room_names)
        form_layout.addRow("First Room:", self.room1_combo)
        
        self.room2_combo = QComboBox()
        self.room2_combo.addItems(room_names)
        form_layout.addRow("Second Room:", self.room2_combo)
        
        layout.addLayout(form_layout)
        
        # Add dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                     QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def validate_and_accept(self):
        """Validate inputs before accepting"""
        if not self.connection_name.text().strip():
            QMessageBox.warning(self, "Warning", "Connection name cannot be empty")
            return
            
        if self.room1_combo.currentText() == self.room2_combo.currentText():
            QMessageBox.warning(self, "Warning", "Cannot connect a room to itself")
            return
        
        import requests
        requests.post("http://localhost:8781/room/add-connection", json={"room_id":self.room1_combo.currentText(), "connected_rooms": [self.room2_combo.currentText()]}).raise_for_status()
        self.accept()

class RoomDialog(QDialog):
    """Dialog for adding a new room"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Room")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.room_name = QLineEdit()
        form_layout.addRow("Room Name:", self.room_name)
        
        self.length_spin = QSpinBox()
        self.length_spin.setRange(1, 1000)
        self.length_spin.setValue(10)
        self.length_spin.setSuffix(" m")
        form_layout.addRow("Length:", self.length_spin)
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 1000)
        self.width_spin.setValue(10)
        self.width_spin.setSuffix(" m")
        form_layout.addRow("Width:", self.width_spin)
        
        self.capacity_spin = QSpinBox()
        self.capacity_spin.setRange(1, 10000)
        self.capacity_spin.setValue(50)
        form_layout.addRow("Capacity:", self.capacity_spin)
        
        self.is_exit_check = QComboBox()
        self.is_exit_check.addItems(["No", "Yes"])
        form_layout.addRow("Is Exit:", self.is_exit_check)
        
        layout.addLayout(form_layout)
        
        # Add dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                     QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def validate_and_accept(self):
        """Validate inputs before accepting"""
        if not self.room_name.text().strip():
            QMessageBox.warning(self, "Warning", "Room name cannot be empty")
            return
        import requests
        
        requests.post(f"http://localhost:8781/room/create/{self.room_name.text().strip()}", json={"name": self.room_name.text().strip(), "capacity": 100000, "exit": self.is_exit_check.currentText() == "Yes"}).raise_for_status()
        
        self.accept()

class DeleteDialog(QDialog):
    """Dialog for deleting rooms or connections"""
    def __init__(self, items, item_type="room", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Delete {item_type.capitalize()}")
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout(self)
        
        label = QLabel(f"Select {item_type} to delete:")
        layout.addWidget(label)
        
        self.item_combo = QComboBox()
        self.item_combo.addItems(items)
        layout.addWidget(self.item_combo)
        
        # Add dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                     QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

class LayoutCard(QFrame):
    """Base card for layout management actions"""
    def __init__(self, title, description, icon_name, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 200)
        self.setStyleSheet("""
            LayoutCard {
                background-color: #f0f8ff;
                border: 1px solid #cccccc;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #1a1a2e;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            font-size: 14px;
            color: #555555;
        """)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        self.action_button = QPushButton(QIcon.fromTheme(icon_name), "Select")
        self.action_button.setStyleSheet("""
            QPushButton {
                background-color: #4cc9f0;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3db8df;
            }
        """)
        layout.addWidget(self.action_button, 0, Qt.AlignmentFlag.AlignCenter)

class LayoutMapPage(QWidget):
    """Page for managing room layout and connections"""
    rooms_updated = pyqtSignal(list)  # Signal emitted when rooms are updated
    
    def __init__(self):
        super().__init__()
        self.rooms = []  # List of room names
        self.connections = []  # List of connections (dicts with name, room1, room2)
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet("background-color: #f8f9fa;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title for the Layout Map page
        title = QLabel("Layout Map Manager")
        title.setStyleSheet("""
            font-size: 24px;
            color: #1a1a2e;
            font-weight: bold;
            margin-bottom: 15px;
        """)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("Manage the building layout by adding rooms and connections between them")
        instructions.setStyleSheet("""
            font-size: 14px;
            color: #555555;
            margin-bottom: 20px;
        """)
        layout.addWidget(instructions)
        
        # Cards container
        cards_container = QWidget()
        cards_layout = QHBoxLayout(cards_container)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(20)
        
        # Add Room card
        self.add_room_card = LayoutCard(
            "Add Room", 
            "Define a new room with dimensions and capacity", 
            "list-add"
        )
        self.add_room_card.action_button.clicked.connect(self.add_room)
        cards_layout.addWidget(self.add_room_card)
        
        # Add Connection card
        self.add_connection_card = LayoutCard(
            "Add Connection", 
            "Create a pathway between two existing rooms", 
            "insert-link"
        )
        self.add_connection_card.action_button.clicked.connect(self.add_connection)
        cards_layout.addWidget(self.add_connection_card)
        
        # Delete Item card
        self.delete_item_card = LayoutCard(
            "Delete Item", 
            "Remove a room or connection from the layout", 
            "edit-delete"
        )
        self.delete_item_card.action_button.clicked.connect(self.delete_item)
        cards_layout.addWidget(self.delete_item_card)
        
        layout.addWidget(cards_container)
        
        # Current layout display section
        layout.addSpacing(20)
        section_label = QLabel("Current Layout Configuration")
        section_label.setStyleSheet("""
            font-size: 18px;
            color: #1a1a2e;
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 10px;
        """)
        layout.addWidget(section_label)
        
        # Scroll area for layout details
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Container for layout details
        self.details_container = QWidget()
        self.details_layout = QVBoxLayout(self.details_container)
        self.details_layout.setContentsMargins(0, 0, 0, 0)
        self.details_layout.setSpacing(10)
        
        scroll_area.setWidget(self.details_container)
        layout.addWidget(scroll_area, 1)
        
        # Initial update of layout details
        self.update_layout_details()
    
    def add_room(self):
        """Handle adding a new room"""
        dialog = RoomDialog(self)
        if dialog.exec():
            room_name = dialog.room_name.text().strip()
            room_details = {
                'name': room_name,
                'length': dialog.length_spin.value(),
                'width': dialog.width_spin.value(),
                'capacity': dialog.capacity_spin.value(),
                'is_exit': dialog.is_exit_check.currentText() == "Yes"
            }
            
            # Add to rooms list and update UI
            self.rooms.append(room_name)
            self.update_layout()
            
            QMessageBox.information(self, "Success", f"Room '{room_name}' added successfully")
    
    def add_connection(self):
        """Handle adding a new connection between rooms"""
        if len(self.rooms) < 2:
            QMessageBox.warning(self, "Warning", "You need at least 2 rooms to create a connection")
            return
            
        dialog = RoomConnectionDialog(self.rooms, self)
        if dialog.exec():
            connection_name = dialog.connection_name.text().strip()
            connection_details = {
                'name': connection_name,
                'room1': dialog.room1_combo.currentText(),
                'room2': dialog.room2_combo.currentText()
            }
            
            # Add to connections list and update UI
            self.connections.append(connection_details)
            self.update_layout()
            
            QMessageBox.information(self, "Success", 
                f"Connection '{connection_name}' between {connection_details['room1']} and {connection_details['room2']} added successfully")
    
    def delete_item(self):
        """Handle deleting a room or connection"""
        if not self.rooms and not self.connections:
            QMessageBox.warning(self, "Warning", "There are no items to delete")
            return
            
        # Create list of deletable items
        items = []
        item_types = []
        
        for room in self.rooms:
            items.append(f"Room: {room}")
            item_types.append("room")
            
        for conn in self.connections:
            items.append(f"Connection: {conn['name']} ({conn['room1']} ↔ {conn['room2']})")
            item_types.append("connection")
        
        dialog = DeleteDialog(items, "item", self)
        if dialog.exec():
            selected_index = dialog.item_combo.currentIndex()
            item_type = item_types[selected_index]
            
            if item_type == "room":
                room_name = self.rooms[selected_index]
                # Remove any connections involving this room
                self.connections = [conn for conn in self.connections 
                                  if conn['room1'] != room_name and conn['room2'] != room_name]
                # Remove the room
                del self.rooms[selected_index]
            else:
                # Adjust index for connections (after rooms)
                conn_index = selected_index - len(self.rooms)
                del self.connections[conn_index]
            
            self.update_layout()
            QMessageBox.information(self, "Success", "Item deleted successfully")
    
    def update_layout(self):
        """Update the layout display and emit signal for other pages"""
        self.update_layout_details()
        self.rooms_updated.emit(self.rooms)
    
    def update_layout_details(self):
        """Update the layout details display"""
        # Clear existing details
        while self.details_layout.count():
            item = self.details_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add rooms section
        if not self.rooms:
            empty_label = QLabel("No rooms defined yet. Add rooms to get started.")
            empty_label.setStyleSheet("color: #777777; font-style: italic;")
            self.details_layout.addWidget(empty_label)
            return
        
        rooms_label = QLabel("Rooms:")
        rooms_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.details_layout.addWidget(rooms_label)
        
        for room in self.rooms:
            room_label = QLabel(f"• {room}")
            room_label.setStyleSheet("margin-left: 10px;")
            self.details_layout.addWidget(room_label)
        
        # Add connections section if any exist
        if self.connections:
            connections_label = QLabel("\nConnections:")
            connections_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 10px;")
            self.details_layout.addWidget(connections_label)
            
            for conn in self.connections:
                conn_label = QLabel(f"• {conn['name']}: {conn['room1']} ↔ {conn['room2']}")
                conn_label.setStyleSheet("margin-left: 10px;")
                self.details_layout.addWidget(conn_label)
        
        self.details_layout.addStretch()