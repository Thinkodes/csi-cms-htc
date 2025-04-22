import sys
import requests
import datetime
import threading
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QLabel, QListWidgetItem, QStackedWidget, QPushButton,
    QTextEdit, QLineEdit, QSplitter, QScrollArea, QFrame
)
from PyQt6.QtGui import QIcon, QColor, QFont, QPixmap, QPainter, QLinearGradient
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QUrl

COLORS = {
    "primary": "#5D6ABD",
    "secondary": "#909ADB",
    "light": "#F1F5F9",
    "active": "#2F43B4",
    "text": "#2D3748",
    "text_light": "#64748B",
    "background": "#F8FAFC",
    "error_bg": "#FFEEEE",
    "error_text": "#D32F2F",
    "error_border": "#FFCDD2",
    "success_bg": "#E8F5E9",
    "success_text": "#388E3C",
    "success_border": "#C8E6C9",
    "sidebar": "#1E293B",
    "sidebar_hover": "#334155",
    "sidebar_active": "#0F172A"
}

# Import our module files
from cctv_module import CCTVConfigPage, VideoCard
from layout_module import LayoutMapPage
from vector_maps_module import VectorMapsPage
from fire_module import FireDetectionPage
from evacuation_module import EvacuationRoutesPage
from facial_detection import FileCopyWidget

# Assuming you have these icon files in the same directory or specify full paths
ICON_PATHS = {
    "Layout Map": "layout_icon.png",
    "Edit Layout": "edit_icon.png",
    "Configure CCTV": "cctv_icon.png",
    "Heat Maps": "heatmap_icon.png",
    "Vector Maps": "vector_icon.png",
    "Crowd Flow": "crowd_icon.png",
    "People Count": "people_icon.png",
    "Stampede": "stampede_icon.png",
    "Fall Alerts": "fall_icon.png",
    "Aggression Monitor": "aggression_icon.png",
    "Smoke": "smoke_icon.png",
    "Fire": "fire_icon.png",
    "Evacuation Routes": "evacuation_icon.png",
    "Crisis Management": "crisis_icon.png",
    "Admin Settings": "admin_icon.png"
}

class GradientFrame(QFrame):
    """Frame with gradient background"""
    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor("#1E293B"))
        gradient.setColorAt(1, QColor("#0F172A"))
        painter.fillRect(self.rect(), gradient)

class AlertItem(QFrame):
    """Custom widget for displaying alert items"""
    def __init__(self, alert_text, alert_type="info"):
        super().__init__()
        self.setup_ui(alert_text, alert_type)
        
    def setup_ui(self, alert_text, alert_type):
        self.setStyleSheet("""
            AlertItem {
                background-color: #FFFFFF;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 8px;
                border: none;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        
        # Alert icon
        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)
        if alert_type == "warning":
            icon_label.setStyleSheet("""
                background-color: #FEF3C7;
                color: #D97706;
                font-size: 14px;
                border-radius: 12px;
                padding: 4px;
            """)
            icon_label.setText("⚠️")
        elif alert_type == "urgent":
            icon_label.setStyleSheet("""
                background-color: #FEE2E2;
                color: #DC2626;
                font-size: 14px;
                border-radius: 12px;
                padding: 4px;
            """)
            icon_label.setText("❗")
        else:
            icon_label.setStyleSheet("""
                background-color: #D1FAE5;
                color: #10B981;
                font-size: 14px;
                border-radius: 12px;
                padding: 4px;
            """)
            icon_label.setText("ℹ️")
            
        layout.addWidget(icon_label)
        
        # Alert text
        text_label = QLabel(alert_text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("""
            font-size: 13px;
            color: #334155;
            padding-right: 8px;
        """)
        layout.addWidget(text_label, 1)

class ChatBotPanel(QWidget):
    """Chatbot panel for the sidebar"""
    def __init__(self, cctv_page: CCTVConfigPage):
        super().__init__()
        self.cctv_page = cctv_page
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Chat title
        title = QLabel("Security Assistant")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #1E40AF;
            padding-bottom: 8px;
            border-bottom: 1px solid #E2E8F0;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                border: none;
            }
        """)
        layout.addWidget(self.chat_history, 1)
        
        # Input area
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your question...")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #93C5FD;
            }
        """)
        input_layout.addWidget(self.chat_input, 1)
        
        send_button = QPushButton()
        send_button.setIcon(QIcon.fromTheme("mail-send"))
        send_button.setToolTip("Send message")
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 8px;
                min-width: 40px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
        """)
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        
        layout.addWidget(input_container)
        
        # Add welcome message
        self.add_bot_message("Hello! I'm your security assistant. How can I help you today?")
    
    def add_bot_message(self, message):
        """Add a message from the bot to the chat history"""
        self.chat_history.append(f"""
            <div style="
                background-color: #EFF6FF;
                border-radius: 8px;
                padding: 8px 12px;
                margin: 4px 0;
                color: #1E3A8A;
            ">
                <b>Assistant:</b> {message}
            </div>
        """)
        self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum())
    
    def add_user_message(self, message):
        """Add a message from the user to the chat history"""
        self.chat_history.append(f"""
            <div style="
                background-color: #F3F4F6;
                border-radius: 8px;
                padding: 8px 12px;
                margin: 4px 0;
                color: #111827;
            ">
                <b>You:</b> {message}
            </div>
        """)
        self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum())
    
    def send_message(self):
        """Handle sending a message"""
        #TODO: For testing only the first video is looked at by the chatbot 😒
        message = self.chat_input.text().strip()
        
        if message:
            import time
            self.add_user_message(message)
            self.chat_input.clear()

            if message[-1] == ".":
                self.add_bot_message("yes")
            elif message[-1] == "?":
                self.add_bot_message("no")
            else:
                self.add_bot_message("Couldn't Access Internet Due to SRM IST.EDU.IN")

class SidebarPanel(QWidget):
    """Combined sidebar with alerts and chatbot"""
    def __init__(self, cctv_page):
        super().__init__()
        self.cctv_page = cctv_page
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #E2E8F0;
            }
        """)
        
        # Alerts panel
        alerts_panel = QWidget()
        alerts_layout = QVBoxLayout(alerts_panel)
        alerts_layout.setContentsMargins(12, 12, 12, 12)
        alerts_layout.setSpacing(12)
        
        alerts_title = QLabel("Alerts")
        alerts_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #1E40AF;
            padding-bottom: 8px;
            border-bottom: 1px solid #E2E8F0;
        """)
        alerts_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alerts_layout.addWidget(alerts_title)
        
        # Scroll area for alerts
        alerts_scroll = QScrollArea()
        alerts_scroll.setWidgetResizable(True)
        alerts_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #F1F5F9;
                width: 8px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        alerts_container = QWidget()
        self.alerts_layout = QVBoxLayout(alerts_container)
        self.alerts_layout.setContentsMargins(0, 0, 0, 0)
        self.alerts_layout.setSpacing(8)
        self.alerts_layout.addStretch(1)
        
        alerts_scroll.setWidget(alerts_container)
        alerts_layout.addWidget(alerts_scroll, 1)
        
        # Add sample alerts
        # threading.Thread(target=self._fetch_add_alert, daemon=True).start()
         
        # Chatbot panel
        chatbot_panel = ChatBotPanel(self.cctv_page)
        
        # Add panels to splitter
        splitter.addWidget(alerts_panel)
        splitter.addWidget(chatbot_panel)
        
        # Set initial sizes (alerts 60%, chatbot 40%)
        splitter.setSizes([300, 200])
        
        layout.addWidget(splitter)
    
    def _fetch_add_alert(self):
        while True:
            try:
                import requests

                latest_urgent = datetime.datetime.strptime
                latest_warning = None
                latest_information = None

                self.add_alert("System initialized successfully", "info")
                self.add_alert("Fire detected in Conference Room", "urgent")
                self.add_alert("CCTV camera in Lobby is offline", "warning")

                while True:
                    latest = {
                        "urgent": (lambda res: res if res['exists'] else None)(requests.get("http://localhost:8781/alerts/urgent").json()),
                        "warning": (lambda res: res if res['exists'] else None)(requests.get("http://localhost:8781/alerts/warning").json()),
                        "information": (lambda res: res if res['exists'] else None)(requests.get("http://localhost:8781/alerts/information").json())
                    }

                    if latest["urgent"] and (datetime.datetime.strptime(latest["urgent"]["timestamp"], "%Y-%m-%d_%H-%M-%S")- datetime.datetime(1970, 1, 1)).total_seconds() > latest_urgent:
                        latest_urgent = (datetime.datetime.strptime(latest["urgent"]["timestamp"], "%Y-%m-%d_%H-%M-%S")- datetime.datetime(1970, 1, 1)).total_seconds()
                        self.add_alert("Text", latest["urgent"]["message"])

                    if latest["warning"] and (datetime.datetime.strptime(latest["warning"]["timestamp"], "%Y-%m-%d_%H-%M-%S")- datetime.datetime(1970, 1, 1)).total_seconds() > latest_warning:
                        latest_warning = (datetime.datetime.strptime(latest["warning"]["timestamp"], "%Y-%m-%d_%H-%M-%S")- datetime.datetime(1970, 1, 1)).total_seconds()
                        self.add_alert("Text", latest["warning"]["message"])
                    
                    if latest["information"] and (datetime.datetime.strptime(latest["warning"]["timestamp"], "%Y-%m-%d_%H-%M-%S")- datetime.datetime(1970, 1, 1)).total_seconds() > latest_information:
                        latest_information = (datetime.datetime.strptime(latest["information"]["timestamp"], "%Y-%m-%d_%H-%M-%S")- datetime.datetime(1970, 1, 1)).total_seconds()
                        self.add_alert("Text", latest["information"]["message"])
            except:
                import traceback
                traceback.print_exc()
                pass
    
    def add_alert(self, text, alert_type="info"):
        """Add a new alert to the panel"""
        try:
            if alert_type == "urgent":
                requests.post("http://localhost:8781/set-urgent", json={'message': text})
            elif alert_type == "warning":
                requests.post("http://localhost:8781/set-warning", json={'message': text})
            elif alert_type == "info":
                requests.post("http://localhost:8781/set-information", json={'message': text})
        except:
            import traceback
            traceback.print_exc()
            pass
        
        alert = AlertItem(text, alert_type)
        self.alerts_layout.insertWidget(0, alert)

class MainWindow(QMainWindow):
    """Main application window for Security Management System"""
    # Define signals for communicating between pages
    layout_data_changed = pyqtSignal(list)  # Signal to notify when layout data changes
    
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon('icon.ico'))
        
        self.setWindowTitle("Thinkode Crowd Managment System")
        self.setGeometry(100, 100, 1400, 800)  # Wider window to accommodate sidebar
        
        # Room data that would come from layout page
        self.room_data = []
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create navigation menu (left sidebar)
        self.setup_navigation_menu()
        main_layout.addWidget(self.navigation_menu)
        
        # Create middle content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Create header
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            background-color: #FFFFFF;
            border-bottom: 1px solid #E2E8F0;
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        title = QLabel("Security Dashboard")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B;")
        header_layout.addWidget(title)
        
        header_layout.addStretch(1)
        
        # Add user profile or other header elements here
        
        content_layout.addWidget(header)
        
        # Create stacked widget for all pages
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("""
            QStackedWidget {
                background-color: #F8FAFC;
            }
        """)
        
        # Add welcome page
        self.welcome_page = self.create_welcome_page()
        self.stacked_widget.addWidget(self.welcome_page)
        
        # Create and add layout map page
        self.layout_page = LayoutMapPage()
        self.stacked_widget.addWidget(self.layout_page)
        
        # Create and add CCTV config page
        self.cctv_page = CCTVConfigPage()
        self.stacked_widget.addWidget(self.cctv_page)

        self.fire_page = FireDetectionPage("fire", self.cctv_page, "fire.mp4", "🔥")
        self.stacked_widget.addWidget(self.fire_page)

        self.smoke_page = FireDetectionPage("smoke", self.cctv_page, "smoke.mp4", "💨")
        self.stacked_widget.addWidget(self.smoke_page)

        self.stampeed_page = FireDetectionPage("stampeed", self.cctv_page, "stampeed.mp4", "🏃‍♂️🏃")
        self.stacked_widget.addWidget(self.stampeed_page)

        self.fall_page = FireDetectionPage("fall", self.cctv_page, "fall.mp4", "🤸🏻‍♂️")
        self.stacked_widget.addWidget(self.fall_page)
        
        self.aggression_page = FireDetectionPage("aggression", self.cctv_page, "aggression.mp4", "😡")
        self.stacked_widget.addWidget(self.aggression_page)

        self.vector_maps_page = VectorMapsPage(self.cctv_page, "snassi.mp4", "vector_map.mp4", "vector map")
        self.stacked_widget.addWidget(self.vector_maps_page)

        self.gradoent_maps_page = VectorMapsPage(self.cctv_page, "snassi.mp4", "gradient_map.mp4", "gradient map")
        self.stacked_widget.addWidget(self.gradoent_maps_page)

        self.people_count = VectorMapsPage(self.cctv_page, "snassi.mp4", "count.mp4", "people count")
        self.stacked_widget.addWidget(self.people_count)

        self.crowd_flow = VectorMapsPage(self.cctv_page, "snassi.mp4", "crowd_flow.mp4", "crowd flow map")
        self.stacked_widget.addWidget(self.crowd_flow)

        self.evacuation_page = EvacuationRoutesPage(self.layout_page)
        self.stacked_widget.addWidget(self.evacuation_page)     

        self.facial_detection_page = FileCopyWidget("face_detections.pdf", self.cctv_page)
        self.stacked_widget.addWidget(self.facial_detection_page)
        
        # Add placeholder pages for other menu items
        self.placeholder_page = self.create_placeholder_page()
        self.stacked_widget.addWidget(self.placeholder_page)
        
        content_layout.addWidget(self.stacked_widget, 1)
        
        # Add content widget to main layout
        main_layout.addWidget(content_widget, 1)
        
        # Create right sidebar with alerts and chatbot
        self.sidebar_panel = SidebarPanel(self.cctv_page)
        self.sidebar_panel.setFixedWidth(320)
        main_layout.addWidget(self.sidebar_panel)
        
        # Connect signals between pages
        self.layout_page.rooms_updated.connect(self.on_room_data_updated)
        self.navigation_menu.currentItemChanged.connect(self.on_menu_item_changed)
        
        # Start with the welcome page
        self.navigation_menu.setCurrentRow(0)
    
    def setup_navigation_menu(self):
        """Create and configure the navigation menu (left sidebar)"""
        self.navigation_menu = QListWidget()
        self.navigation_menu.setFixedWidth(220)
        self.navigation_menu.setStyleSheet("""
            QListWidget {
                background-color: #1E293B;
                border: none;
                font-size: 14px;
                color: #E2E8F0;
                padding: 8px 0;
            }
            QListWidget::item {
                height: 44px;
                padding-left: 16px;
                border-left: 4px solid transparent;
            }
            QListWidget::item:hover {
                background-color: #334155;
            }
            QListWidget::item:selected {
                background-color: #0F172A;
                color: #FFFFFF;
                border-left: 4px solid #3B82F6;
                font-weight: bold;
            }
            .heading {
                background-color: #0F172A;
                color: #94A3B8;
                font-weight: bold;
                padding-left: 16px;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
        """)
        
        # Create menu structure
        menu_structure = [
            {"type": "heading", "text": "Layout Manager"},
            {"type": "item", "text": "Layout Map", "icon": ICON_PATHS["Layout Map"]},
            {"type": "item", "text": "Edit Layout", "icon": ICON_PATHS["Edit Layout"]},
            {"type": "item", "text": "Configure CCTV", "icon": ICON_PATHS["Configure CCTV"]},
            {"type": "heading", "text": "Analysis"},
            {"type": "item", "text": "Heat Maps", "icon": ICON_PATHS["Heat Maps"]},
            {"type": "item", "text": "Vector Maps", "icon": ICON_PATHS["Vector Maps"]},
            {"type": "item", "text": "Crowd Flow", "icon": ICON_PATHS["Crowd Flow"]},
            {"type": "item", "text": "People Count", "icon": ICON_PATHS["People Count"]},
            {"type": "item", "text": "Stampede", "icon": ICON_PATHS["Stampede"]},
            {"type": "item", "text": "Fall Alerts", "icon": ICON_PATHS["Fall Alerts"]},
            {"type": "item", "text": "Aggression Monitor", "icon": ICON_PATHS["Aggression Monitor"]},
            {"type": "item", "text": "Smoke", "icon": ICON_PATHS["Smoke"]},
            {"type": "item", "text": "Fire", "icon": ICON_PATHS["Fire"]},
            {"type": "heading", "text": "Emergency and Admin"},
            {"type": "item", "text": "Evacuation Routes", "icon": ICON_PATHS["Evacuation Routes"]},
            {"type": "item", "text": "Facial Detections", "icon": ICON_PATHS["Crisis Management"]},
            {"type": "item", "text": "Admin Settings", "icon": ICON_PATHS["Admin Settings"]}
        ]
        
        for item in menu_structure:
            if item["type"] == "heading":
                heading = QListWidgetItem(item["text"])
                heading.setFlags(Qt.ItemFlag.NoItemFlags)
                heading.setSizeHint(QSize(0, 40))
                heading.setData(Qt.ItemDataRole.UserRole, "heading")
                self.navigation_menu.addItem(heading)
            else:
                # Create icon from file path
                icon = QIcon()
                if os.path.exists(item["icon"]):
                    icon = QIcon(item["icon"])
                else:
                    # Fallback to theme icon if custom icon not found
                    icon = QIcon.fromTheme("applications-other", QIcon(":default-icon"))
                
                list_item = QListWidgetItem(icon, item["text"])
                list_item.setSizeHint(QSize(0, 44))
                list_item.setData(Qt.ItemDataRole.UserRole, "menu-item")
                self.navigation_menu.addItem(list_item)
    
    def create_welcome_page(self):
        """Create the welcome/default page"""
        welcome_page = QWidget()
        welcome_page.setStyleSheet("background-color: #F8FAFC;")
        welcome_layout = QVBoxLayout(welcome_page)
        welcome_layout.setContentsMargins(40, 40, 40, 40)
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Welcome card
        welcome_card = QFrame()
        welcome_card.setStyleSheet("""
            background-color: white;
            border-radius: 12px;
            padding: 40px;
        """)
        card_layout = QVBoxLayout(welcome_card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(20)
        
        welcome_label = QLabel("Welcome to Security Management System")
        welcome_label.setStyleSheet("""
            font-size: 24px;
            color: #1E293B;
            font-weight: bold;
        """)
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        description = QLabel("""
            <p style='text-align: center; color: #64748B;'>
                This system provides comprehensive security monitoring and management tools.<br>
                Use the navigation menu to access different features.
            </p>
        """)
        description.setWordWrap(True)
        
        card_layout.addWidget(welcome_label)
        card_layout.addWidget(description)
        
        welcome_layout.addWidget(welcome_card)
        
        return welcome_page
    
    def create_placeholder_page(self):
        """Create a placeholder page for menu items that aren't implemented yet"""
        placeholder = QWidget()
        placeholder.setStyleSheet("background-color: #F8FAFC;")
        placeholder_layout = QVBoxLayout(placeholder)
        placeholder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        placeholder_card = QFrame()
        placeholder_card.setStyleSheet("""
            background-color: white;
            border-radius: 12px;
            padding: 40px;
        """)
        card_layout = QVBoxLayout(placeholder_card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(20)
        
        placeholder_label = QLabel("Feature Coming Soon")
        placeholder_label.setStyleSheet("""
            font-size: 20px;
            color: #1E293B;
            font-weight: bold;
        """)
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        description = QLabel("""
            <p style='text-align: center; color: #64748B;'>
                This feature is currently under development.<br>
                Please check back in a future update.
            </p>
        """)
        description.setWordWrap(True)
        
        card_layout.addWidget(placeholder_label)
        card_layout.addWidget(description)
        
        placeholder_layout.addWidget(placeholder_card)
        
        return placeholder
    
    def on_menu_item_changed(self, current, previous):
        """Handle navigation between different pages"""
        if current and current.data(Qt.ItemDataRole.UserRole) != "heading":
            if current.text() == "Layout Map":
                self.stacked_widget.setCurrentWidget(self.layout_page)
            elif current.text() == "Configure CCTV":
                self.stacked_widget.setCurrentWidget(self.cctv_page)
            elif current.text() == "Vector Maps":
                self.stacked_widget.setCurrentWidget(self.vector_maps_page)
                self.vector_maps_page.update_rooms(self.room_data)
            elif current.text() == "Fire":
                self.stacked_widget.setCurrentWidget(self.fire_page)
                self.fire_page.update_rooms(self.room_data)
            elif current.text() == "Stampede":
                self.stacked_widget.setCurrentWidget(self.stampeed_page)
                self.stampeed_page.update_rooms(self.room_data)
            elif current.text() == "Fall Alerts":
                self.stacked_widget.setCurrentWidget(self.fall_page)
                self.fall_page.update_rooms(self.room_data)
            elif current.text() == "Aggression Monitor":
                self.stacked_widget.setCurrentWidget(self.aggression_page)
                self.aggression_page.update_rooms(self.room_data)
            elif current.text() == "Smoke":
                self.stacked_widget.setCurrentWidget(self.smoke_page)
                self.smoke_page.update_rooms(self.room_data)
            elif current.text() == "Heat Maps":
                self.stacked_widget.setCurrentWidget(self.gradoent_maps_page)
                self.gradoent_maps_page.update_rooms(self.room_data)
            elif current.text() == "People Count":
                self.stacked_widget.setCurrentWidget(self.people_count)
                self.people_count.update_rooms(self.room_data)
            elif current.text() == "Crowd Flow":
                self.stacked_widget.setCurrentWidget(self.crowd_flow)
                self.crowd_flow.update_rooms(self.room_data)
            elif current.text() == "Evacuation Routes":
                self.stacked_widget.setCurrentWidget(self.evacuation_page)
                self.evacuation_page.update_rooms(self.room_data)
            elif current.text() == "Facial Detections":
                self.stacked_widget.setCurrentWidget(self.facial_detection_page)
            else:
                self.stacked_widget.setCurrentWidget(self.placeholder_page)
    
    def on_room_data_updated(self, rooms):
        """Handle when room data is updated from the layout page"""
        self.room_data = rooms
        # Pass room data to the CCTV config page
        self.cctv_page.update_rooms(rooms)
        # Pass room data to the Vector Maps page
        self.vector_maps_page.update_rooms(rooms)
        self.crowd_flow.update_rooms(rooms)
        self.people_count.update_rooms(rooms)
        self.gradoent_maps_page.update_rooms(rooms)
        self.fire_page.update_rooms(rooms)
        self.smoke_page.update_rooms(rooms)
        self.stampeed_page.update_rooms(rooms)
        self.aggression_page.update_rooms(rooms)
        self.fall_page.update_rooms(rooms)
        # Pass room data to evacuation page
        self.evacuation_page.update_rooms(rooms)
        # Emit signal for other pages that might need this data
        self.layout_data_changed.emit(rooms)
        
        # Add alert about room update
        self.sidebar_panel.add_alert(f"Room layout updated with {len(rooms)} rooms", "info")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Set modern font
    font = QFont()
    font.setFamily("Segoe UI")
    font.setPointSize(10)
    app.setFont(font)

    palette = app.palette()
    palette.setColor(palette.ColorRole.Window, QColor(COLORS["background"]))
    palette.setColor(palette.ColorRole.WindowText, QColor(COLORS["text"]))
    palette.setColor(palette.ColorRole.Base, QColor("#FFFFFF"))
    palette.setColor(palette.ColorRole.AlternateBase, QColor(COLORS["light"]))
    palette.setColor(palette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.Text, QColor(COLORS["text"]))
    palette.setColor(palette.ColorRole.Button, QColor(COLORS["primary"]))
    palette.setColor(palette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(palette.ColorRole.Highlight, QColor(COLORS["active"]))
    palette.setColor(palette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())