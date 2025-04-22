import sys
import requests
import cv2
import socket
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QWidget, QLabel, 
    QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, 
    QProgressBar, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (
    QPixmap, QImage, QFont, QIcon, QPainter, QColor, QPen, 
    QFontDatabase, QLinearGradient, QBrush
)

window = None

# Color scheme with pastel error colors
COLORS = {
    "primary": "#5D6ABD",
    "secondary": "#909ADB",
    "light": "#C1C9FF",
    "active": "#2F43B4",
    "text": "#2D3748",
    "text_light": "#718096",
    "background": "#F8FAFC",
    "error_bg": "#FFEEEE",
    "error_text": "#D32F2F",
    "error_border": "#FFCDD2",
    "success_bg": "#E8F5E9",
    "success_text": "#388E3C",
    "success_border": "#C8E6C9"
}

# System information
SYSTEM_INFO = {
    "project_name": "Crowd Management<br> System",
    "company_name": "Thinkode",
    "admin_email": "akshgarg13@gmail.com",
    "version": "1.0.0"
}

# User database with admin contact
USER_DB = {
    "admin": {
        "password": "admin123",
        "allowed_ips": ["192.168.1.100", "127.0.0.1"],
        "name": "Admin User",
        "email": SYSTEM_INFO["admin_email"],
        "role": "Administrator",
        "department": "IT Security",
        "avatar": "👨‍💼"
    },
    "user1": {
        "password": "pass123",
        "allowed_ips": ["192.168.1.101"],
        "name": "John Doe",
        "email": "john.doe@thinkode.com",
        "role": "Operator",
        "department": "Operations",
        "avatar": "👨‍💻"
    }
}

HOST = "http://localhost:8781"

PROGRESS_STEPS = ["Credentials", "Face ID", "IP Check", "Complete"]


class AnimatedLoader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update_angle)
        self._timer.start(30)
        self._pulse_animation = QPropertyAnimation(self, b"opacity")
        self._pulse_animation.setDuration(1000)
        self._pulse_animation.setStartValue(0.3)
        self._pulse_animation.setEndValue(1.0)
        self._pulse_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._pulse_animation.setLoopCount(-1)
        self._pulse_animation.start()

    def update_angle(self):
        self._angle = (self._angle + 12) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Gradient effect
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(COLORS["primary"]))
        gradient.setColorAt(1, QColor(COLORS["active"]))
        pen = QPen(QBrush(gradient), 4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # Draw animated arc
        painter.drawArc(10, 10, 40, 40, self._angle * 16, 270 * 16)
        
        # Center dot
        painter.setBrush(QBrush(QColor(COLORS["primary"])))
        painter.drawEllipse(28, 28, 4, 4)


class ModernButton(QPushButton):
    def __init__(self, text, parent=None, icon=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["primary"]};
                color: white;
                border: none;
                padding: 14px 28px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                min-width: 140px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["active"]};
            }}
            QPushButton:pressed {{
                background-color: {COLORS["active"]};
                padding: 13px 27px;
            }}
            QPushButton:disabled {{
                background-color: {COLORS["light"]};
                color: {COLORS["text_light"]};
            }}
        """)
        
        if icon:
            self.setIcon(icon)
            self.setIconSize(QSize(20, 20))


class BackButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(42, 42)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                border: 1px solid {COLORS["light"]};
                border-radius: 21px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["light"]};
            }}
        """)
        self.setText("←")
        self.setFont(QFont("Arial", 16))


class ErrorLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS["error_bg"]};
                color: {COLORS["error_text"]};
                border: 1px solid {COLORS["error_border"]};
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
            }}
        """)
        self.setWordWrap(True)
        self.setVisible(bool(text))


class SuccessLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS["success_bg"]};
                color: {COLORS["success_text"]};
                border: 1px solid {COLORS["success_border"]};
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
            }}
        """)
        self.setWordWrap(True)
        self.setVisible(bool(text))


class SystemInfoPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_info)
        self.timer.start(1000)
        self.update_info()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # System info
        self.datetime_label = QLabel()
        self.datetime_label.setStyleSheet(f"color: white; font-size: 12px;")
        
        self.ip_label = QLabel()
        self.ip_label.setStyleSheet(f"color: white; font-size: 12px;")
        
        self.version_label = QLabel(f"Version: {SYSTEM_INFO['version']}")
        self.version_label.setStyleSheet(f"color: white; font-size: 12px;")
        
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: rgba(255,255,255,0.2);")
        
        layout.addWidget(self.datetime_label)
        layout.addWidget(self.ip_label)
        layout.addWidget(separator)
        layout.addWidget(self.version_label)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def update_info(self):
        # Update datetime
        now = datetime.now()
        self.datetime_label.setText(now.strftime("%a, %b %d %Y\n%I:%M:%S %p"))
        
        # Update IP address
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            self.ip_label.setText(f"IP: {ip}")
        except:
            self.ip_label.setText("IP: 127.0.0.1")

class ProgressIndicator(QWidget):
    def __init__(self, current_step):
        super().__init__()
        self.current_step = current_step
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(10)
        
        # Steps
        steps_layout = QHBoxLayout()
        steps_layout.setContentsMargins(0, 0, 0, 0)
        steps_layout.setSpacing(10)
        
        for i, step in enumerate(PROGRESS_STEPS):
            # Step circle
            circle = QLabel()
            circle.setFixedSize(24, 24)
            circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if i < self.current_step:
                # Completed step
                circle.setStyleSheet(f"""
                    QLabel {{
                        background-color: {COLORS["success_text"]};
                        color: white;
                        border-radius: 12px;
                        font-size: 12px;
                    }}
                """)
                circle.setText("✓")
            elif i == self.current_step:
                # Current step
                circle.setStyleSheet(f"""
                    QLabel {{
                        background-color: {COLORS["primary"]};
                        color: white;
                        border-radius: 12px;
                        font-size: 12px;
                    }}
                """)
                circle.setText(str(i+1))
            else:
                # Future step
                circle.setStyleSheet(f"""
                    QLabel {{
                        background-color: {COLORS["light"]};
                        color: {COLORS["text_light"]};
                        border-radius: 12px;
                        font-size: 12px;
                    }}
                """)
                circle.setText(str(i+1))
            
            steps_layout.addWidget(circle, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, len(PROGRESS_STEPS)-1)
        self.progress_bar.setValue(self.current_step)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS["light"]};
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS["primary"]};
                border-radius: 2px;
            }}
        """)
        
        # Step labels
        labels_layout = QHBoxLayout()
        labels_layout.setContentsMargins(0, 0, 0, 0)
        labels_layout.setSpacing(10)
        
        for i, step in enumerate(PROGRESS_STEPS):
            label = QLabel(step)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"""
                QLabel {{
                    font-size: 11px;
                    color: {"#5D6ABD" if i == self.current_step else COLORS["text_light"]};
                    font-weight: {"bold" if i == self.current_step else "normal"};
                }}
            """)
            labels_layout.addWidget(label)
        
        layout.addLayout(steps_layout)
        layout.addWidget(self.progress_bar)
        layout.addLayout(labels_layout)
        self.setLayout(layout)

class Phase1Login(QWidget):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.error_label = ErrorLabel()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 30)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Welcome Back!")
        header.setStyleSheet(f"""
            QLabel {{
                font-size: 26px;
                font-weight: bold;
                color: {COLORS["text"]};
                margin-bottom: 5px;
            }}
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Subheader
        subheader = QLabel("Sign in to access the Crowd Management System")
        subheader.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {COLORS["text_light"]};
                margin-bottom: 20px;
            }}
        """)
        subheader.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Error message
        layout.addWidget(self.error_label)
        
        # Form
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 14px 16px;
                border: 1px solid {COLORS["light"]};
                border-radius: 8px;
                font-size: 14px;
                color: {COLORS["text"]};
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS["primary"]};
            }}
        """)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 14px 16px;
                border: 1px solid {COLORS["light"]};
                border-radius: 8px;
                font-size: 14px;
                color: {COLORS["text"]};
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS["primary"]};
            }}
        """)
        
        # Forgot password link
        forgot_password = QLabel("<a href='#' style='color: {0}; text-decoration: none'>Forgot password?</a>".format(COLORS["primary"]))
        forgot_password.setAlignment(Qt.AlignmentFlag.AlignRight)
        forgot_password.setOpenExternalLinks(False)
        forgot_password.linkActivated.connect(self.show_forgot_password)
        
        self.login_button = ModernButton("Continue")
        self.login_button.clicked.connect(self.authenticate)
        
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(forgot_password)
        form_layout.addWidget(self.login_button, 0, Qt.AlignmentFlag.AlignHCenter)
        
        # Progress
        self.progress = ProgressIndicator(0)
        
        layout.addWidget(header)
        layout.addWidget(subheader)
        layout.addLayout(form_layout)
        layout.addStretch()
        layout.addWidget(self.progress)
        
        self.setLayout(layout)
    
    def show_error(self, message):
        self.error_label.setText(f"⚠️ {message}")
        self.error_label.setVisible(True)
    
    def show_forgot_password(self):
        self.error_label.setText(f"📧 Please contact {SYSTEM_INFO['admin_email']} for password reset")
        self.error_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS["light"]};
                color: {COLORS["primary"]};
                border: 1px solid {COLORS["secondary"]};
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
            }}
        """)
        self.error_label.setVisible(True)
    
    def authenticate(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            self.show_error("Please enter both username and password")
            return
            
        if username in USER_DB and USER_DB[username]["password"] == password:
            self.error_label.setVisible(False)
            self.on_success(username)
        else:
            self.show_error("Invalid username or password")


class Phase2FaceRecognition(QWidget):
    def __init__(self, username, on_success, on_back):
        super().__init__()
        self.username = username
        self.on_success = on_success
        self.on_back = on_back
        self.camera = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.loader = AnimatedLoader()
        self.success_label = SuccessLabel()
        self.error_label = ErrorLabel()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 30)
        layout.setSpacing(20)
        
        # Back button
        back_button = BackButton()
        back_button.clicked.connect(self.on_back)
        
        # Header
        header = QLabel("Biometric Verification")
        header.setStyleSheet(f"""
            QLabel {{
                font-size: 26px;
                font-weight: bold;
                color: {COLORS["text"]};
                margin-bottom: 5px;
            }}
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Instructions
        instructions = QLabel("Please position your face in the frame")
        instructions.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {COLORS["text_light"]};
                margin-bottom: 20px;
            }}
        """)
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Status messages
        status_layout = QVBoxLayout()
        status_layout.setSpacing(10)
        status_layout.addWidget(self.success_label)
        status_layout.addWidget(self.error_label)
        
        # Camera feed container
        camera_container = QWidget()
        camera_container.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS["background"]};
                border-radius: 12px;
                border: 1px solid {COLORS["light"]};
            }}
        """)
        camera_layout = QVBoxLayout(camera_container)
        camera_layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        
        camera_layout.addWidget(self.image_label)
        
        # Button
        self.verify_button = ModernButton("Verify Face")
        self.verify_button.clicked.connect(self.verify_face)
        
        # Loader
        self.loader.setParent(self)
        self.loader.move(self.width()//2 - 30, self.height()//2 - 30)
        
        # Progress
        self.progress = ProgressIndicator(1)
        
        layout.addWidget(back_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(header)
        layout.addWidget(instructions)
        layout.addLayout(status_layout)
        layout.addWidget(camera_container, 1)
        layout.addWidget(self.verify_button, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
        layout.addWidget(self.progress)
        
        self.setLayout(layout)
        
        # Start camera feed
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)
    
    def resizeEvent(self, event):
        self.loader.move(self.width()//2 - 30, self.height()//2 - 30)
        super().resizeEvent(event)
    
    def update_frame(self):
        ret, frame = self.camera.read()
        if ret:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            self.image_label.setPixmap(pixmap.scaled(
                400, 300, 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
    
    def verify_face(self):
        self.loader.show()
        self.verify_button.setEnabled(False)
        self.error_label.setVisible(False)
        
        # Simulate face verification delay
        self.process_face_verification()
    
    def process_face_verification(self):
        self.loader.hide()
        self.verify_button.setEnabled(True)
        
        # For now, accept all faces
        self.success_label.setText("✅ Face recognized successfully!")
        self.success_label.setVisible(True)
        self.on_success()
        self.cleanup()
    
    def cleanup(self):
        self.timer.stop()
        self.camera.release()
        
    def closeEvent(self, event):
        self.cleanup()
        event.accept()


class Phase3IPVerification(QWidget):
    def __init__(self, username, on_success, on_back):
        super().__init__()
        self.username = username
        self.on_success = on_success
        self.on_back = on_back
        self.loader = AnimatedLoader()
        self.success_label = SuccessLabel()
        self.error_label = ErrorLabel()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 30)
        layout.setSpacing(20)
        
        # Back button
        back_button = BackButton()
        back_button.clicked.connect(self.on_back)
        
        # Header
        header = QLabel("Network Verification")
        header.setStyleSheet(f"""
            QLabel {{
                font-size: 26px;
                font-weight: bold;
                color: {COLORS["text"]};
                margin-bottom: 5px;
            }}
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Status messages
        status_layout = QVBoxLayout()
        status_layout.setSpacing(10)
        status_layout.addWidget(self.success_label)
        status_layout.addWidget(self.error_label)
        
        # IP info
        ip_frame = QFrame()
        ip_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS["background"]};
                border-radius: 12px;
                padding: 24px;
                border: 1px solid {COLORS["light"]};
            }}
        """)
        
        ip_layout = QVBoxLayout()
        ip_layout.setSpacing(12)
        
        ip_title = QLabel("Network Details")
        ip_title.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: bold;
                color: {COLORS["text"]};
            }}
        """)
        
        self.ip_label = QLabel()
        self.ip_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {COLORS["text_light"]};
            }}
        """)
        
        self.status_label = QLabel()
        self.status_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {COLORS["text_light"]};
            }}
        """)
        
        ip_layout.addWidget(ip_title)
        ip_layout.addWidget(self.ip_label)
        ip_layout.addWidget(self.status_label)
        ip_frame.setLayout(ip_layout)
        
        # Button
        self.verify_button = ModernButton("Verify Network")
        self.verify_button.clicked.connect(self.verify_ip)
        
        # Loader
        self.loader.setParent(self)
        self.loader.move(self.width()//2 - 30, self.height()//2 - 30)
        
        # Progress
        self.progress = ProgressIndicator(2)
        
        layout.addWidget(back_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(header)
        layout.addLayout(status_layout)
        layout.addWidget(ip_frame)
        layout.addWidget(self.verify_button, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
        layout.addWidget(self.progress)
        
        self.setLayout(layout)
        
        # Get current IP
        self.current_ip = self.get_ip_address()
        self.ip_label.setText(f"Detected IP Address: {self.current_ip}")
        self.status_label.setText("Status: Waiting for verification...")
    
    def resizeEvent(self, event):
        self.loader.move(self.width()//2 - 30, self.height()//2 - 30)
        super().resizeEvent(event)
    
    def get_ip_address(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def verify_ip(self):
        self.loader.show()
        self.verify_button.setEnabled(False)
        self.error_label.setVisible(False)
        
        # Simulate verification delay
        QTimer.singleShot(1500, self.process_ip_verification)
    
    def process_ip_verification(self):
        self.loader.hide()
        self.verify_button.setEnabled(True)
        try:
            response = requests.post(f"{HOST}/is-autherized", json={"ip": self.current_ip})
        except:
            response = requests.Response()
            response.status_code = 200

        if (response.status_code == 200 or True): # TODO: This is purely because I don't want to autherize everytime, really need an ADMIN UI Just to autherize IPs.
            self.success_label.setText("✅ Network verification successful!")
            self.success_label.setVisible(True)
            self.status_label.setText("Status: Verified successfully!")
            self.status_label.setStyleSheet(f"color: {COLORS['success_text']}; font-size: 14px; font-weight: 500;")
            QTimer.singleShot(1000, self.on_success)
        else:
            self.error_label.setText(f"⚠️ IP address {self.current_ip} not authorized for this account!")
            self.error_label.setVisible(True)
            self.status_label.setText(f"Status: IP address {self.current_ip} not authorized!")
            self.status_label.setStyleSheet("color: #E53E3E; font-size: 14px; font-weight: 500;")


class ProfileView(QWidget):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main container
        container = QWidget()
        container.setStyleSheet(f"background-color: {COLORS['background']};")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(50, 50, 50, 50)
        container_layout.setSpacing(0)
        
        # Success message
        success_msg = QLabel("Authentication Successful!")
        success_msg.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: bold;
                color: {COLORS["primary"]};
                margin-bottom: 30px;
                text-align: center;
            }}
        """)
        
        # Profile card
        profile_card = QFrame()
        profile_card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 16px;
                padding: 40px;
                border: 1px solid {COLORS["light"]};
            }}
        """)
        
        profile_layout = QHBoxLayout()
        profile_layout.setContentsMargins(0, 0, 0, 0)
        profile_layout.setSpacing(30)
        
        # Avatar
        avatar_container = QWidget()
        avatar_container.setFixedWidth(140)
        avatar_layout = QVBoxLayout(avatar_container)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        avatar_layout.setSpacing(20)
        
        avatar = QLabel(USER_DB[self.username]["avatar"])
        avatar.setStyleSheet(f"""
            QLabel {{
                font-size: 70px;
                padding: 35px;
                background-color: {COLORS["light"]};
                border-radius: 70px;
                color: {COLORS["primary"]};
            }}
        """)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedSize(140, 140)
        
        avatar_layout.addWidget(avatar, 0, Qt.AlignmentFlag.AlignHCenter)
        avatar_layout.addStretch()
        
        # Details
        details_layout = QVBoxLayout()
        details_layout.setSpacing(12)
        
        name = QLabel(USER_DB[self.username]["name"])
        name.setStyleSheet(f"""
            QLabel {{
                font-size: 28px;
                font-weight: bold;
                color: {COLORS["text"]};
            }}
        """)
        
        username_label = QLabel(f"@{self.username}")
        username_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                color: {COLORS["primary"]};
                margin-bottom: 24px;
            }}
        """)
        
        # Details grid
        grid_layout = QVBoxLayout()
        grid_layout.setSpacing(12)
        
        def create_detail_row(label, value):
            row = QHBoxLayout()
            row.setSpacing(15)
            
            lbl = QLabel(label)
            lbl.setStyleSheet(f"""
                QLabel {{
                    font-size: 15px;
                    color: {COLORS["text_light"]};
                    min-width: 120px;
                }}
            """)
            
            val = QLabel(value)
            val.setStyleSheet(f"""
                QLabel {{
                    font-size: 15px;
                    color: {COLORS["text"]};
                    font-weight: 500;
                }}
            """)
            
            row.addWidget(lbl)
            row.addWidget(val)
            row.addStretch()
            return row
        
        grid_layout.addLayout(create_detail_row("Email:", USER_DB[self.username]["email"]))
        grid_layout.addLayout(create_detail_row("Role:", USER_DB[self.username]["role"]))
        grid_layout.addLayout(create_detail_row("Department:", USER_DB[self.username]["department"]))
        grid_layout.addLayout(create_detail_row("Last Login:", datetime.now().strftime("%b %d, %Y at %I:%M %p")))
        
        details_layout.addWidget(name)
        details_layout.addWidget(username_label)
        details_layout.addLayout(grid_layout)
        details_layout.addStretch()
        
        profile_layout.addWidget(avatar_container)
        profile_layout.addLayout(details_layout)
        profile_card.setLayout(profile_layout)
        
        # Continue button
        continue_button = ModernButton("Continue to CMS Dashboard.")
        continue_button.clicked.connect(self.launch_main)

        
        # Progress (completed)
        self.progress = ProgressIndicator(3)
        
        container_layout.addWidget(success_msg)
        container_layout.addWidget(profile_card, 1)
        container_layout.addStretch()
        container_layout.addWidget(self.progress)
        container_layout.addWidget(continue_button, 0, Qt.AlignmentFlag.AlignHCenter)
        if USER_DB[self.username]["role"] == "Administrator":
            admin_button = ModernButton("Continue to Admin Dashboard")
            admin_button.clicked.connect(self.close) # TODO: MAKE THIS WORK.
        
        layout.addWidget(container)
        self.setLayout(layout)
    
    def launch_main(self):
        global window
        from main import MainWindow

        window.close()
        window = MainWindow()
        window.show()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowIcon(QIcon('icon.ico'))
        self.setWindowTitle(f"{SYSTEM_INFO['project_name']} - {SYSTEM_INFO['company_name']}")
        self.setFixedSize(1000, 750)
        
        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        
        # Main layout
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left decorative panel
        left_panel = QWidget()
        left_panel.setFixedWidth(350)
        left_panel.setStyleSheet(f"""
            background-color: {COLORS["primary"]};
            border-top-left-radius: 12px;
            border-bottom-left-radius: 12px;
        """)
        
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(40, 50, 40, 30)
        left_layout.setSpacing(30)
        
        # Logo in left panel
        logo = QLabel(SYSTEM_INFO["project_name"])
        logo.setStyleSheet(f"""
            QLabel {{
                font-size: 26px;
                font-weight: bold;
                color: white;
                margin-bottom: 10px;
            }}
        """)
        
        company = QLabel(SYSTEM_INFO["company_name"])
        company.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                color: rgba(255,255,255,0.8);
                margin-bottom: 40px;
            }}
        """)
        
        # Decorative text
        welcome = QLabel("Secure Authentication\nPortal\n\nby Thinkode")
        welcome.setStyleSheet("""
            QLabel {
                font-size: 32px;
                font-weight: bold;
                color: white;
                line-height: 1.4;
                margin-bottom: 40px;
            }
        """)
        welcome.setWordWrap(True)
        
        # System info panel at bottom
        self.system_info = SystemInfoPanel()
        
        left_layout.addWidget(logo)
        left_layout.addWidget(company)
        left_layout.addWidget(welcome)
        left_layout.addStretch()
        left_layout.addWidget(self.system_info)
        
        # Right panel (content)
        right_panel = QWidget()
        right_panel.setStyleSheet(f"""
            background-color: {COLORS["background"]};
            border-top-right-radius: 12px;
            border-bottom-right-radius: 12px;
        """)
        
        self.right_layout = QVBoxLayout(right_panel)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget for phases
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background: transparent;")
        
        # Initialize all phases
        self.phase1 = Phase1Login(self.on_phase1_success)
        self.stacked_widget.addWidget(self.phase1)
        
        # Start with phase 1
        self.stacked_widget.setCurrentWidget(self.phase1)
        
        # Add loader
        self.loader = AnimatedLoader()
        self.loader.setParent(right_panel)
        self.loader.hide()
        
        self.right_layout.addWidget(self.stacked_widget)
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
    
    def resizeEvent(self, event):
        self.loader.move(
            self.central_widget.width() - 350 + (self.width() - 350) // 2 - 30,
            self.height() // 2 - 30
        )
        super().resizeEvent(event)
    
    def show_loader(self):
        self.loader.move(
            self.central_widget.width() - 350 + (self.width() - 350) // 2 - 30,
            self.height() // 2 - 30
        )
        self.loader.show()
        self.stacked_widget.hide()
    
    def hide_loader(self):
        self.loader.hide()
        self.stacked_widget.show()
    
    def on_phase1_success(self, username):
        self.username = username
        self.show_loader()
        QTimer.singleShot(1000, lambda: self.show_phase(2))
    
    def on_phase2_success(self):
        self.show_loader()
        QTimer.singleShot(1000, lambda: self.show_phase(3))
    
    def on_phase3_success(self):
        self.show_loader()
        QTimer.singleShot(1000, lambda: self.show_phase(4))
    
    def show_phase(self, phase_num):
        self.hide_loader()
        
        if phase_num == 2:
            if not hasattr(self, 'phase2'):
                self.phase2 = Phase2FaceRecognition(
                    self.username, 
                    self.on_phase2_success,
                    lambda: self.stacked_widget.setCurrentWidget(self.phase1)
                )
                self.stacked_widget.addWidget(self.phase2)
            self.stacked_widget.setCurrentWidget(self.phase2)
        
        elif phase_num == 3:
            if not hasattr(self, 'phase3'):
                self.phase3 = Phase3IPVerification(
                    self.username,
                    self.on_phase3_success,
                    lambda: self.stacked_widget.setCurrentWidget(self.phase2)
                )
                self.stacked_widget.addWidget(self.phase3)
            self.stacked_widget.setCurrentWidget(self.phase3)
        
        elif phase_num == 4:
            if not hasattr(self, 'profile_view'):
                self.profile_view = ProfileView(self.username)
                self.stacked_widget.addWidget(self.profile_view)
            self.stacked_widget.setCurrentWidget(self.profile_view)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set a modern style
    app.setStyle("Fusion")
    
    # Load modern font
    font_id = QFontDatabase.addApplicationFont(":/fonts/segoeui.ttf")
    if font_id != -1:
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        app.setFont(QFont(font_family, 10))
    
    # Custom palette
    palette = app.palette()
    palette.setColor(palette.ColorRole.Window, QColor(COLORS["background"]))
    palette.setColor(palette.ColorRole.WindowText, QColor(COLORS["text"]))
    palette.setColor(palette.ColorRole.Base, QColor(COLORS["light"]))
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