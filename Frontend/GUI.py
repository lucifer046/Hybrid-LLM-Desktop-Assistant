# ===========================================================================================================
#                                         GUI.py (Graphical User Interface)
# ===========================================================================================================
# This module defines the complete frontend of the application using PyQt5.
# It includes the main window, a custom top bar, chat interface, and a home screen with an interactive assistant.
# It communicates with the backend via file I/O operations (Status files in 'Frontend/Files').

from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget, QLineEdit, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QSizePolicy, QGraphicsDropShadowEffect)
from PyQt5.QtGui import QIcon, QPainter, QMovie, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat
from PyQt5.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPoint
from dotenv import dotenv_values
import sys
import os 

# -------------------------------------------------------------------------------------------------------
#                                         Global Configurations
# -------------------------------------------------------------------------------------------------------
# Load environment variables (Assistant Name, API Keys, etc.) from the .env file.
env_vars = dotenv_values(".env")
AssistantName = env_vars.get("AssistantName")

# Paths for file-based communication and assets
current_dir = os.getcwd()
old_chat_message = ""
TempDirPath = rf"{current_dir}\Frontend\Files"       # Folder for data transfer (.data files)
GraphicsDirPath = rf"{current_dir}\Frontend\Graphics" # Folder for UI images and GIFs

# Automatically create directories if they don't exist
os.makedirs(TempDirPath, exist_ok=True)
os.makedirs(GraphicsDirPath, exist_ok=True)

# -------------------------------------------------------------------------------------------------------
#                                         Helper Functions
# -------------------------------------------------------------------------------------------------------

def AnswerModifier(answer):
    """
    Cleans up the assistant's response by removing empty lines.
    This ensures a neat display in the chat window.
    """
    lines = answer.split("\n")
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = "\n".join(non_empty_lines)
    return modified_answer

def QueryModifier(query):
    """
    Formats the user's query for better readability and grammar.
    - Converts to lowercase for checking.
    - Adds a question mark if it's a question (starts with 'what', 'how', etc.).
    - Adds a period if it's a statement.
    - Capitalizes the first letter.
    """
    new_query = query.lower().strip()
    query_words = new_query.split()
    question_words = ["what", "where", "when", "why", "how", "who", "which", "whom", "whose", "can you", "what's", "where's", "when's", "why's", "how's", "who's", "which's", "whom's", "whose's"]

    # Check if the query starts with a question word
    if any(word in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query = new_query + "?"
    else:
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query = new_query + "."
    return new_query.capitalize()

# --- File I/O for Backend Communication ---
# These functions read/write small text files to signal state changes (e.g., Mic On/Off).

def SetMicrophoneStatus(Command):
    """Writes 'True' or 'False' to Mic.data to control the backend microphone listener."""
    with open(rf"{TempDirPath}\Mic.data", "w", encoding="utf-8") as file:
        file.write(Command)

def GetMicrophoneStatus():
    """Reads the current microphone status from Mic.data."""
    try:
        with open(rf"{TempDirPath}\Mic.data", "r", encoding="utf-8") as file:
            Status = file.read().strip()
        return Status
    except FileNotFoundError:
        with open(rf"{TempDirPath}\Mic.data", "w", encoding="utf-8") as file:
            file.write("False")
        return "False"

def SetAssistantStatus(Status):
    """Writes the current status of the Assistant (e.g., 'Listening...', 'Thinking...') to Status.data."""
    with open(rf"{TempDirPath}\Status.data", "w", encoding="utf-8") as file:
        file.write(Status)
        
def GetAssistantStatus():
    """Reads the Assistant's status."""
    try:
        with open(rf"{TempDirPath}\Status.data", "r", encoding="utf-8") as file:
            Status = file.read()
        return Status
    except FileNotFoundError:
        with open(rf"{TempDirPath}\Status.data", "w", encoding="utf-8") as file:
            file.write("Available...")
        return "Available..."

def MicButtonInitiated():
    """Triggered when the UI Mic button is clicked to START listening."""
    SetMicrophoneStatus("False")

def MicButtonClosed():
    """Triggered when the UI Mic button is clicked to STOP listening."""
    SetMicrophoneStatus("True")

def GraphicsDirectoryPath(Filename):
    """Returns the absolute path to a graphics file."""
    path = rf'{GraphicsDirPath}\{Filename}'
    return path

def TempDirectoryPath(Filename):
    """Returns the absolute path to a temp data file."""
    path = rf'{TempDirPath}\{Filename}'
    return path 

def ShowTextToScreen(Text):
    """Writes text to Responses.data so the GUI can display it."""
    with open(rf"{TempDirPath}\Responses.data", "w", encoding="utf-8") as f:
        f.write(Text)

# -------------------------------------------------------------------------------------------------------
#                                         Custom Widgets
# -------------------------------------------------------------------------------------------------------

class StyledButton(QPushButton):
    """
    A custom QPushButton with:
    - Transparent background
    - Rounded corners
    - Hover effects (light cyan glow)
    - Optional icon support
    - Drop shadow for a 'neon' feel
    """
    def __init__(self, text, icon_path=None, parent=None):
        super(StyledButton, self).__init__(text, parent)
        if icon_path:
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(24, 24))
        
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px;
                font-family: 'Segoe UI';
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(0, 243, 255, 0.15);
                border: 1px solid rgba(0, 243, 255, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(0, 243, 255, 0.3);
            }
        """)
        
        # Add glow effect
        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(15)
        self.glow.setColor(QColor(0, 243, 255, 150))
        self.glow.setOffset(0, 0)
        self.glow.setEnabled(False)
        self.setGraphicsEffect(self.glow)

    def enterEvent(self, event):
        self.glow.setEnabled(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.glow.setEnabled(False)
        super().leaveEvent(event)

# -------------------------------------------------------------------------------------------------------
#                                         Chat Screen (Message UI)
# -------------------------------------------------------------------------------------------------------

class ChatSection(QWidget):
    """
    The main area for displaying the conversation history and a cleaner text input field.
    """
    def __init__(self):
        super(ChatSection, self).__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 20) 
        layout.setSpacing(15)

        # 1. Chat History Area (Read-only TextEdit)
        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
        self.chat_text_edit.setFrameStyle(QFrame.NoFrame)
        self.chat_text_edit.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 0.5); 
                border-radius: 20px;
                padding: 20px;
                color: #e0e0e0;
                font-family: 'Consolas', 'Segoe UI', sans-serif;
                font-size: 16px;
                border: 1px solid rgba(0, 243, 255, 0.3);
            }
        """)
        
        # Styled Scrollbar for the Chat Area
        self.chat_text_edit.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: rgba(0, 0, 0, 0.2);
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #00f3ff;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        layout.addWidget(self.chat_text_edit)

        # 2. Status Row (Assistant Status + Small GIF)
        status_layout = QHBoxLayout()
        status_layout.setAlignment(Qt.AlignRight)

        self.label = QLabel("")
        self.label.setStyleSheet("color: #00f3ff; font-size: 16px; font-weight: bold; margin-right: 15px;")
        status_layout.addWidget(self.label)

        self.gif_label = QLabel()
        self.gif_label.setStyleSheet("border: none; background: transparent;")
        try:
            movie = QMovie(rf"{GraphicsDirPath}\Jarvis.gif")
            movie.setScaledSize(QSize(120, 80)) 
            self.gif_label.setMovie(movie)
            movie.start()
        except:
             self.gif_label.setText("AI Active")

        status_layout.addWidget(self.gif_label)
        layout.addLayout(status_layout)

        # 3. Input Area (Text Field + Send Button)
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 10, 0, 0)
        input_layout.setSpacing(10)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter command here...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: rgba(10, 10, 10, 0.8);
                color: white;
                border: 2px solid #00f3ff;
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 16px;
                font-family: 'Segoe UI';
            }
            QLineEdit:focus {
                border: 2px solid #ffffff;
                background-color: rgba(20, 20, 20, 0.9);
                selection-background-color: #00f3ff;
            }
        """)
        self.input_field.returnPressed.connect(self.sendMessage) # Send on Enter

        self.send_button = QPushButton()
        self.send_button.setFixedSize(50, 50)
        self.send_button.setIcon(QIcon(rf"{GraphicsDirPath}\Send.png"))
        self.send_button.setIconSize(QSize(24, 24))
        self.send_button.setCursor(Qt.PointingHandCursor)
        self.send_button.clicked.connect(self.sendMessage)
        self.send_button.setStyleSheet("""
            QPushButton {
                 background-color: rgba(0, 243, 255, 0.2);
                 border-radius: 25px;
                 border: 1px solid #00f3ff;
            }
            QPushButton:hover {
                 background-color: rgba(0, 243, 255, 0.5);
                 border: 2px solid white;
            }
            QPushButton:pressed {
                 background-color: #00f3ff;
            }
        """)
        
        # Add glow to send button
        self.send_glow = QGraphicsDropShadowEffect(self.send_button)
        self.send_glow.setBlurRadius(20)
        self.send_glow.setColor(QColor(0, 243, 255, 100))
        self.send_button.setGraphicsEffect(self.send_glow)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)

        self.setStyleSheet("background-color: #121212;") 
        
        # 4. Timers for Live Updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)     # Check for new chat messages
        self.timer.timeout.connect(self.SpeechRecogText)  # Check for status updates
        self.timer.start(100) 

    def loadMessages(self):
        """
        Polls the 'Responses.data' file for new messages from the backend.
        If the content has changed, it updates the chat window.
        """
        global old_chat_message
        try:
            with open(rf'{TempDirPath}\Responses.data', 'r', encoding='utf-8') as file:
                messages = file.read()
            if messages and messages != old_chat_message:
                self.addMessage(message=messages)
                old_chat_message = messages
        except FileNotFoundError:
            # Check if file exists, if not create it
            with open(rf'{TempDirPath}\Responses.data', 'w', encoding='utf-8') as file:
                file.write("")
            pass

    def SpeechRecogText(self):
        """Reads status updates (e.g. 'Listening...') and updates the label."""
        try:
            with open(rf'{TempDirPath}\Status.data', 'r', encoding='utf-8') as file:
                messages = file.read()
            self.label.setText(messages)
        except Exception:
            pass

    def addMessage(self, message):
        """
        Parses raw text from the backend and splits it into bubbles.
        It assumes messages are formatted like "User: Hello" or "JARVIS: Hi".
        """
        lines = message.split('\n')
        current_message = ""
        current_sender = None
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Identify sender
            if ":" in line:
                possible_sender, content = line.split(":", 1)
                possible_sender = possible_sender.strip()
                
                # Check against known names or generic roles
                if possible_sender == AssistantName or "Assistant" in possible_sender:
                    if current_message:
                        self.createBubble(current_sender, current_message)
                    current_sender = "Assistant"
                    current_message = content.strip()
                    continue
                elif possible_sender == env_vars.get("Username", "User") or "User" in possible_sender or "You" in possible_sender:
                    if current_message:
                        self.createBubble(current_sender, current_message)
                    current_sender = "User"
                    current_message = content.strip()
                    continue
            
            # If no new sender detected, append to current message
            if current_message:
                current_message += "\n" + line
            else:
                current_message = line
                # Default to Assistant if undefined (e.g. system msg)
                if not current_sender: current_sender = "Assistant" 

        # Add the last accumulated message
        if current_message:
            self.createBubble(current_sender, current_message)

    def createBubble(self, sender, text):
        """
        Inserts a styled HTML chat bubble into the QTextEdit.
        Different styles for 'User' (Right aligned) and 'Assistant' (Left aligned).
        """
        cursor = self.chat_text_edit.textCursor()
        # Convert newlines to HTML breaks
        text = text.replace("\n", "<br>")
        
        if sender == "User":
             alignment = "right"
             # Neon Cyan for User (WhatsApp 'Green' equivalent)
             bg_color = "rgba(0, 200, 200, 0.3)" 
             border_color = "#00f3ff"
             text_color = "white"
             # Tail on bottom-right (more rounded)
             border_radius = "25px 25px 0px 25px"
             margin_left = "20%" # Push layout to right
             margin_right = "0px"
        else:
             alignment = "left"
             # Dark Grey for Assistant (WhatsApp 'White' equivalent in Dark Mode)
             bg_color = "rgba(40, 40, 40, 0.8)"
             border_color = "rgba(0, 243, 255, 0.2)" 
             text_color = "#e0e0e0"
             # Tail on bottom-left (more rounded)
             border_radius = "25px 25px 25px 0px"
             margin_left = "0px"
             margin_right = "20%" # Push layout to left

        html = f"""
        <div style="width: 100%; text-align: {alignment}; margin-bottom: 10px;">
            <div style="
                display: inline-block; 
                background-color: {bg_color}; 
                color: {text_color};
                padding: 15px 20px; 
                border-radius: {border_radius}; 
                border: 1px solid {border_color};
                margin-left: {margin_left};
                margin-right: {margin_right};
                font-family: 'Segoe UI';
                font-size: 18px; 
                text-align: left;
            ">
                {text}
            </div>
        </div>
        """
        cursor.movePosition(cursor.End)
        cursor.insertHtml(html)
        self.chat_text_edit.setTextCursor(cursor)
        self.chat_text_edit.verticalScrollBar().setValue(self.chat_text_edit.verticalScrollBar().maximum())

    def sendMessage(self):
        """Reads input field and writes command to 'UserInput.data' for backend processing."""
        text = self.input_field.text().strip()
        if text:
            try:
                with open(rf"{TempDirPath}\UserInput.data", "w", encoding="utf-8") as f:
                     f.write(text)
                self.input_field.clear()
            except Exception as e:
                print(f"Error sending message: {e}")


# -------------------------------------------------------------------------------------------------------
#                                         Initial Home Screen
# -------------------------------------------------------------------------------------------------------

class InitialScreen(QWidget):
    """
    The landing page of the application.
    Features:
    - Fullscreen background GIF (Jarvis style).
    - Large Microphone icon that toggles listening state.
    - Status label showing initializing status.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # 1. Background GIF
        self.bg_label = QLabel(self)
        self.bg_label.resize(screen_width, screen_height)
        self.bg_label.setStyleSheet("background-color: black;")
        self.bg_label.setAlignment(Qt.AlignCenter)  # Center the content
        
        try:
             movie = QMovie(GraphicsDirPath + r'\Jarvis.gif')
             
             # Smart Scaling logic to handle different screen resolutions
             movie.jumpToFrame(0)
             gif_size = movie.currentImage().size()
             
             if gif_size.isValid():
                 # Calculate scaling to COVER the screen (AspectFill)
                 w_ratio = screen_width / gif_size.width()
                 h_ratio = screen_height / gif_size.height()
                 scale_factor = max(w_ratio, h_ratio)
                 
                 new_width = int(gif_size.width() * scale_factor)
                 new_height = int(gif_size.height() * scale_factor)
                 
                 movie.setScaledSize(QSize(new_width, new_height))
             else:
                 # Fallback if size invalid
                 movie.setScaledSize(QSize(screen_width, screen_height))

             self.bg_label.setMovie(movie)
             movie.start()
             self.bg_label.lower() 
        except Exception as e:
            print(f"Error loading GIF: {e}")
            pass

        # 2. Mic Icon with Glow Effect
        self.icon_label = QLabel()
        self.load_icon(GraphicsDirPath + r'\Mic_on.png', 150, 150) # Slightly smaller for better fit
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        # Using QGraphicsDropShadowEffect for glowing effect on icon
        glow = QGraphicsDropShadowEffect(self.icon_label)
        glow.setBlurRadius(60) # Increased blur for "projection" feel
        glow.setColor(QColor(0, 243, 255, 180))
        glow.setOffset(0,0)
        self.icon_label.setGraphicsEffect(glow)

        self.icon_label.setStyleSheet("""
            background: transparent;
            opacity: 0.9; 
        """)
        
        self.icon_label.setCursor(Qt.PointingHandCursor)
        self.icon_label.mousePressEvent = self.toggle_icon # Click handler
        self.toggled = True
        MicButtonInitiated() # Initialize status to match icon

        # 3. Status Label
        self.label = QLabel("Initializing Systems...")
        self.label.setStyleSheet("""
            color: #00f3ff; 
            font-size: 32px; 
            font-family: 'Segoe UI'; 
            font-weight: bold; 
            letter-spacing: 2px;
            background: transparent;
        """)
        self.label.setAlignment(Qt.AlignCenter)
        
        # Status Label Glow
        label_glow = QGraphicsDropShadowEffect(self.label)
        label_glow.setBlurRadius(20)
        label_glow.setColor(QColor(0, 243, 255, 150))
        label_glow.setOffset(0,0)
        self.label.setGraphicsEffect(label_glow)

        self.layout.addStretch()
        self.layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
        self.layout.addSpacing(30)
        self.layout.addWidget(self.label, alignment=Qt.AlignCenter)
        self.layout.addStretch()

        self.setStyleSheet("background-color: black;") 
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(100)

    def SpeechRecogText(self):
        """Reads mic status to update the label text."""
        try:
            with open(TempDirPath + r'\Status.data', 'r', encoding='utf-8') as file:
                messages = file.read()
                self.label.setText(messages)
        except Exception:
            pass

    def load_icon(self, path, width=60, height=60):
        """Helper to load and scale icons efficiently."""
        pixmap = QPixmap(path)
        new_pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.icon_label.setPixmap(new_pixmap)
        self.icon_label.setFixedSize(width, height)

    def toggle_icon(self, event=None):
        """Toggles the Mic icon on/off and calls the corresponding file I/O functions."""
        if self.toggled:
            self.load_icon(GraphicsDirPath + r'\Mic_on.png', 150, 150)
            MicButtonInitiated()
        else:
            self.load_icon(GraphicsDirPath + r'\Mic_off.png', 150, 150)
            MicButtonClosed()
        self.toggled = not self.toggled


class MessageScreen(QWidget):
    """
    Wrapper widget for the ChatSection to be used in the StackedWidget.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        chat_section = ChatSection()
        layout.addWidget(chat_section)
        self.setLayout(layout)
        self.setStyleSheet("background-color: #121212;")


# -------------------------------------------------------------------------------------------------------
#                                         Custom Title Bar
# -------------------------------------------------------------------------------------------------------

class CustomTopBar(QWidget):
    """
    A custom frameless title bar with:
    - Navigation buttons (HOME, CHAT)
    - Window controls (Minimize, Maximize, Close)
    - Drag functionality to move the window.
    """
    def __init__(self, parent, stacked_widget):
        super().__init__(parent)
        self.stacked_widget = stacked_widget
        self.initUI()

    def initUI(self):
        self.setFixedHeight(80) 
        self.oldPos = None # Initialize draggable hook
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignRight)
        layout.setContentsMargins(30, 15, 30, 15)
        layout.setSpacing(20)

        # Style sheet
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(5, 5, 5, 0.9);
                border-bottom: 2px solid rgba(0, 243, 255, 0.2);
            }
        """)

        # Navigation Buttons
        home_btn = StyledButton("  HOME", rf'{GraphicsDirPath}\Home.png')
        home_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        msg_btn = StyledButton("  CHAT", rf'{GraphicsDirPath}\Message.png')
        msg_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        # Window Controls
        min_btn = StyledButton("", rf'{GraphicsDirPath}\Minimize.png')
        min_btn.clicked.connect(self.minimizeWindow)
        min_btn.setFixedSize(50, 50)

        self.max_btn = StyledButton("", rf'{GraphicsDirPath}\Maximize.png')
        self.max_btn.clicked.connect(self.maximizeWindow)
        self.max_btn.setFixedSize(50, 50)

        close_btn = StyledButton("", rf'{GraphicsDirPath}\Close.png')
        close_btn.clicked.connect(self.closeWindow)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 68, 68, 0.8);
            }
        """)
        close_btn.setFixedSize(50, 50)

        layout.addWidget(home_btn)
        layout.addWidget(msg_btn)
        
        # Spacer
        layout.addSpacing(40)
        
        layout.addWidget(min_btn)
        layout.addWidget(self.max_btn)
        layout.addWidget(close_btn)

    def minimizeWindow(self):
        self.window().showMinimized()

    def maximizeWindow(self):
        if self.window().isMaximized():
            self.window().showNormal()
            self.max_btn.setIcon(QIcon(rf'{GraphicsDirPath}\Maximize.png'))
        else:
            self.window().showMaximized()
            self.max_btn.setIcon(QIcon(rf'{GraphicsDirPath}\Restore.png')) 

    def closeWindow(self):
        self.window().close()

    # Window Drag Logic
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.oldPos:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.window().move(self.window().x() + delta.x(), self.window().y() + delta.y())
            self.oldPos = event.globalPos()
            
    def mouseReleaseEvent(self, event):
        self.oldPos = None

    def paintEvent(self, event):
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)


# -------------------------------------------------------------------------------------------------------
#                                         Main Application Window
# -------------------------------------------------------------------------------------------------------

from PyQt5.QtWidgets import QStyle, QStyleOption, QSizeGrip

class MainWindow(QMainWindow):
    """
    The main shell of the application.
    - Frameless window
    - Manages the 'StackedWidget' (Home vs Chat)
    - Adds the CustomTopBar
    - Includes a size grip for resizing the frameless window.
    """
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground) 
        self.initUI()

    def initUI(self):
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        
        self.setGeometry(0, 0, screen_width, screen_height)
        
        # Central container (Transparent with border)
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("""
            QWidget#CentralWidget {
                background-color: #050505; 
                border-radius: 15px; 
                border: 2px solid rgba(0, 243, 255, 0.1);
            }
        """)
        self.central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(self.central_widget)
        
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.stacked_widget = QStackedWidget()
        initial_screen = InitialScreen()
        message_screen = MessageScreen()
        self.stacked_widget.addWidget(initial_screen)
        self.stacked_widget.addWidget(message_screen)

        self.top_bar = CustomTopBar(self, self.stacked_widget)
        
        main_layout.addWidget(self.top_bar)
        main_layout.addWidget(self.stacked_widget)
        
        # Resizing Grips (Bottom-Right)
        self.sizegrip = QSizeGrip(self)
        self.sizegrip.setStyleSheet("width: 20px; height: 20px; margin: 0px; padding: 0px;")

    def resizeEvent(self, event):
        rect = self.rect()
        self.sizegrip.move(rect.right() - self.sizegrip.width(), rect.bottom() - self.sizegrip.height())
        super().resizeEvent(event)


def GraphicalUserInterface():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    GraphicalUserInterface()