from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGridLayout, QScrollArea, QFrame, QMessageBox, QGraphicsView,
    QGraphicsScene, QGraphicsPathItem, QGraphicsEllipseItem
)
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainterPath, QPen, QColor, QBrush, QPainter
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget


class EvacuationRouteCard(QFrame):
    """A custom widget representing a room's evacuation route"""
    def __init__(self, room_name, exit_route, parent=None):
        super().__init__(parent)
        self.room_name = room_name
        self.exit_route = exit_route  # List of room names to exit
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedSize(350, 300)
        self.setStyleSheet("""
            EvacuationRouteCard {
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
        
        # Route visualization
        self.route_view = QGraphicsView()
        self.route_view.setMinimumSize(300, 200)
        self.route_view.setStyleSheet("""
            background-color: #ffffff;
            border-radius: 4px;
        """)
        self.route_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        card_layout.addWidget(self.route_view)
        
        # Route description
        self.route_label = QLabel()
        self.route_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.route_label.setStyleSheet("""
            font-size: 14px;
            color: #555555;
            margin-top: 5px;
        """)
        card_layout.addWidget(self.route_label)
        
        # Update the route display
        self.update_route()
    
    def update_route(self):
        """Update the visualization of the evacuation route"""
        scene = QGraphicsScene()
        scene.setSceneRect(0, 0, 280, 180)
        
        if not self.exit_route:
            self.route_label.setText("No evacuation route available")
            self.route_view.setScene(scene)
            return
            
        # Create path visualization
        path = QPainterPath()
        points = []
        
        # Calculate positions for each point in the route
        num_points = len(self.exit_route)
        for i, room in enumerate(self.exit_route):
            x = 40 + i * (200 / max(1, num_points - 1))
            y = 90
            points.append(QPointF(x, y))
            
            # Add room name label
            text = scene.addText(room)
            text.setPos(x - text.boundingRect().width()/2, y + 20)
        
        # Create the path
        path.moveTo(points[0])
        for point in points[1:]:
            path.lineTo(point)
        
        # Add path to scene
        path_item = QGraphicsPathItem(path)
        pen = QPen(QColor("#FF4500"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        path_item.setPen(pen)
        scene.addItem(path_item)
        
        # Add start and end markers
        start_circle = QGraphicsEllipseItem(QRectF(points[0].x()-8, points[0].y()-8, 16, 16))
        start_circle.setBrush(QBrush(QColor("#4CAF50")))  # Green for start
        scene.addItem(start_circle)
        
        end_circle = QGraphicsEllipseItem(QRectF(points[-1].x()-8, points[-1].y()-8, 16, 16))
        end_circle.setBrush(QBrush(QColor("#FF4500")))  # Orange-red for exit
        scene.addItem(end_circle)
        
        # Add direction arrow at the end
        arrow_path = QPainterPath()
        arrow_path.moveTo(points[-1].x() - 10, points[-1].y() - 5)
        arrow_path.lineTo(points[-1].x(), points[-1].y())
        arrow_path.lineTo(points[-1].x() - 10, points[-1].y() + 5)
        arrow_item = QGraphicsPathItem(arrow_path)
        arrow_item.setBrush(QBrush(QColor("#FF4500")))
        scene.addItem(arrow_item)
        
        # Update route description
        route_text = " → ".join(self.exit_route)
        self.route_label.setText(f"Evacuation route: {route_text}")
        
        self.route_view.setScene(scene)


class EvacuationRoutesPage(QWidget):
    """Page for displaying and managing evacuation routes"""
    def __init__(self, layout_page=None):
        super().__init__()
        self.layout_page = layout_page  # Reference to layout page for room data
        self.room_routes = {}  # Dictionary mapping rooms to their evacuation routes
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet("background-color: #f8f9fa;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title for the Evacuation Routes page
        title = QLabel("Evacuation Routes")
        title.setStyleSheet("""
            font-size: 24px;
            color: #1a1a2e;
            font-weight: bold;
            margin-bottom: 15px;
        """)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("View and manage evacuation routes for each room in the building")
        instructions.setStyleSheet("""
            font-size: 14px;
            color: #555555;
            margin-bottom: 20px;
        """)
        layout.addWidget(instructions)
        
        # Button container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        
        # Calculate routes button
        self.calculate_button = QPushButton("Calculate All Routes")
        self.calculate_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3e8e41;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.calculate_button.clicked.connect(self.calculate_all_routes)
        button_layout.addWidget(self.calculate_button)
        
        # Emergency button
        self.emergency_button = QPushButton("EMERGENCY MODE")
        self.emergency_button.setStyleSheet("""
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
        self.emergency_button.clicked.connect(self.activate_emergency_mode)
        button_layout.addWidget(self.emergency_button)
        
        layout.addWidget(button_container)
        
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
        self.no_rooms_message = QLabel("No rooms available. Please define rooms in the Layout Map first.")
        self.no_rooms_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_rooms_message.setStyleSheet("""
            font-size: 16px;
            color: #777777;
            padding: 20px;
        """)
        self.no_rooms_message.setVisible(True)
        layout.addWidget(self.no_rooms_message)
    
    def update_rooms(self, room_list):
        """Update the evacuation routes with rooms from layout page"""
        # Check if we have rooms
        if not room_list:
            self.no_rooms_message.setVisible(True)
            self.calculate_button.setEnabled(False)
            return
        
        self.no_rooms_message.setVisible(False)
        self.calculate_button.setEnabled(True)
        
        # Clear existing room cards
        self.clear_room_grid()
        
        # Add evacuation route cards to grid for each room
        row, col = 0, 0
        max_cols = 2  # Fewer columns since these cards are wider
        
        for room_name in room_list:
            # Get pre-calculated route or empty list
            route = self.room_routes.get(room_name, [])
            
            route_card = EvacuationRouteCard(room_name, route)
            self.room_grid.addWidget(route_card, row, col)
            
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
    
    def calculate_all_routes(self):
        """Calculate evacuation routes for all rooms"""
        if not hasattr(self.layout_page, 'rooms') or not self.layout_page.rooms:
            QMessageBox.warning(self, "Warning", "No rooms available to calculate routes")
            return
        
        if not hasattr(self.layout_page, 'connections') or not self.layout_page.connections:
            QMessageBox.warning(self, "Warning", "No connections between rooms defined")
            return
        import requests
        exits = requests.get("http://localhost:8781/room/get-exit-rooms").json()["exits"]
        
        if not exits:
            QMessageBox.warning(self, "Warning", "No exit rooms defined in layout")
            return

        import requests
        self.room_routes = requests.get("http://localhost:8781/room/get-all-escape-routes").json()
        
        for room in self.layout_page.rooms:
            if room in exits:
                self.room_routes[room] = [room]  # Exit is already at exit
            else:
                # Simple demo route - just go directly to first exit
                self.room_routes[room] = [room, exits[0]]
        
        # Update the display
        self.update_rooms(self.layout_page.rooms)
        QMessageBox.information(self, "Success", "Evacuation routes calculated for all rooms")
    
    def activate_emergency_mode(self):
        """Activate emergency mode - flash screen and show all routes clearly"""
        # In a real app, this would trigger alarms, notifications, etc.
        # For this demo, we'll just highlight all routes
        
        # Flash the background
        self.setStyleSheet("background-color: #FFEEEE;")
        
        # Show emergency message
        QMessageBox.warning(self, "EMERGENCY", 
                          "EVACUATION ALERT ACTIVATED!\n\n" +
                          "Please follow the displayed evacuation routes to the nearest exit.")
        
        # Reset background after a delay
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self.setStyleSheet("background-color: #f8f9fa;"))