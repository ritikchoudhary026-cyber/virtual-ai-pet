"""Desktop pet frontend with mood animations, AI chatbot, and mode toggle.

Supports switching between offline (Phi-3), online (Nemotron 3.5), and auto modes.
"""

import sys
import time
from pathlib import Path

import requests
from pynput import keyboard
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget, QMenu, QDialog, QVBoxLayout,
    QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QComboBox,
)


API_URL = "http://localhost:8000"

# frontend/ is one directory below the project root where assets/ lives
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
GIFS = {
    "idle": ASSETS_DIR / "idle.gif",
    "working": ASSETS_DIR / "working.gif",
    "alert": ASSETS_DIR / "alert.gif",
    "moving": ASSETS_DIR / "moving.gif",
}

# How long after the last key press we keep the 'working' animation
KEYBOARD_IDLE_DELAY_SECONDS = 1

# Keep the desktop pet approximately the size of a dock/app icon
WINDOW_SIZE = 72
GIF_SIZE = 64

# Path to chat assets
CHAT_BG = ASSETS_DIR / "kittywallpaper.png"
AVATAR_IMG = ASSETS_DIR / "cat.png"


# ---------------------------------------------------------------------------
# Chat Window with mode toggle
# ---------------------------------------------------------------------------

class ChatWindow(QDialog):
    """Pixel-art styled chat dialog with offline/online mode selector."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Kuchu-Puchu Chat")
        self.setFixedSize(380, 540)
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowCloseButtonHint
        )

        bg_path = str(CHAT_BG) if CHAT_BG.is_file() else ""
        self.avatar_path = str(AVATAR_IMG) if AVATAR_IMG.is_file() else ""

        self.setStyleSheet(f"""
            ChatWindow {{
                background-image: url("{bg_path}");
                background-repeat: repeat;
                background-position: center;
                border: 4px solid #4a90d9;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Title bar
        title = QLabel("Kuchu-Puchu Chat")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-family: 'Courier New', monospace;
                font-size: 16px;
                font-weight: bold;
                letter-spacing: 2px;
                padding: 6px;
                background-color: rgba(30, 60, 120, 200);
                border: 3px solid #4a90d9;
            }
        """)
        layout.addWidget(title)

        # Mode selector row
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(4)

        mode_label = QLabel("MODE:")
        mode_label.setStyleSheet("""
            QLabel {
                color: #78b8ff;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                font-weight: bold;
                background-color: rgba(10, 15, 30, 200);
                padding: 4px 6px;
                border: 2px solid #4a90d9;
            }
        """)
        mode_layout.addWidget(mode_label)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["auto", "offline", "online"])
        self.mode_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(10, 15, 30, 220);
                color: #78b8ff;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                font-weight: bold;
                padding: 4px 8px;
                border: 2px solid #4a90d9;
            }
            QComboBox::drop-down {
                border: none;
                background-color: rgba(30, 60, 120, 220);
            }
            QComboBox QAbstractItemView {
                background-color: rgba(10, 15, 30, 240);
                color: #78b8ff;
                border: 2px solid #4a90d9;
                selection-background-color: #4a90d9;
                selection-color: #ffffff;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        mode_layout.addWidget(self.mode_combo, 1)

        # Mode status indicator
        self.mode_status = QLabel("READY")
        self.mode_status.setAlignment(Qt.AlignCenter)
        self.mode_status.setStyleSheet("""
            QLabel {
                color: #50fa7b;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                font-weight: bold;
                background-color: rgba(10, 15, 30, 200);
                padding: 4px 6px;
                border: 2px solid #50fa7b;
            }
        """)
        mode_layout.addWidget(self.mode_status)

        layout.addLayout(mode_layout)

        # Chat history area
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: rgba(10, 15, 30, 160);
                color: #000000;
                border: 3px solid #4a90d9;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                selection-background-color: #4a90d9;
            }
        """)
        layout.addWidget(self.chat_history)

        # Input row
        input_layout = QHBoxLayout()
        input_layout.setSpacing(4)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type here...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: rgba(10, 15, 30, 200);
                color: #ffffff;
                border: 3px solid #4a90d9;
                padding: 8px 10px;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                font-weight: bold;
            }
            QLineEdit:focus {
                border-color: #78b8ff;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)

        send_btn = QPushButton("SEND")
        send_btn.setFixedSize(60, 36)
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 60, 120, 220);
                color: #ffffff;
                border: 3px solid #4a90d9;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: rgba(74, 144, 217, 220);
            }
            QPushButton:pressed {
                background-color: rgba(20, 40, 80, 240);
            }
        """)
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)

        layout.addLayout(input_layout)

        # Welcome message
        self._append_bot("Hey! I am your Kuchu-Puchu!")

    def _msg_html(self, sender: str, avatar_html: str, text: str, is_bot: bool, mode_badge: str = "") -> str:
        """Build a pixel-art bordered message bubble in HTML."""
        border = "#4a90d9"
        bg = "rgba(15, 25, 60, 180)" if is_bot else "rgba(20, 50, 100, 180)"

        # Mode badge for bot messages
        badge_html = ""
        if mode_badge:
            badge_color = "#50fa7b" if mode_badge == "offline" else "#78b8ff"
            badge_html = (
                f'<span style="color:{badge_color}; font-size:9px; '
                f'font-family:Courier New,monospace; font-weight:bold; '
                f'padding:1px 4px; border:1px solid {badge_color}; '
                f'margin-left:6px;">{mode_badge.upper()}</span>'
            )

        return (
            f'<div style="margin:4px 0;">'
            f'<table cellpadding="0" cellspacing="0" style="border:2px solid {border}; '
            f'background-color:{bg}; width:100%; border-collapse:collapse;">'
            f'<tr>'
            f'<td style="padding:4px 6px; vertical-align:middle; width:34px;">{avatar_html}</td>'
            f'<td style="padding:4px 6px; vertical-align:middle;">'
            f'<span style="color:#4a90d9; font-family:Courier New,monospace; font-size:11px; '
            f'font-weight:bold;">{sender}</span>{badge_html}</td>'
            f'</tr>'
            f'<tr>'
            f'<td colspan="2" style="padding:4px 8px; border-top:1px solid {border};">'
            f'<span style="color:#ffffff; font-family:Courier New,monospace; '
            f'font-size:12px;">{text}</span></td>'
            f'</tr></table></div>'
        )

    def _append_bot(self, text: str, mode_badge: str = "") -> None:
        """Add a bot message to the chat history."""
        avatar = f'<img src="{self.avatar_path}" width="28" height="28">' if self.avatar_path else "PET"
        self.chat_history.append(self._msg_html("Kuchu-Puchu", avatar, text, is_bot=True, mode_badge=mode_badge))
        self._scroll_bottom()

    def _append_user(self, text: str) -> None:
        """Add a user message to the chat history."""
        avatar = '<span style="font-size:14px;">YOU</span>'
        self.chat_history.append(self._msg_html("You", avatar, text, is_bot=False))
        self._scroll_bottom()

    def _scroll_bottom(self) -> None:
        """Scroll chat history to the latest message."""
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _update_mode_status(self, mode_used: str) -> None:
        """Update the mode status indicator based on which engine was used."""
        if mode_used == "online":
            self.mode_status.setText("ONLINE")
            self.mode_status.setStyleSheet("""
                QLabel {
                    color: #78b8ff;
                    font-family: 'Courier New', monospace;
                    font-size: 10px;
                    font-weight: bold;
                    background-color: rgba(10, 15, 30, 200);
                    padding: 4px 6px;
                    border: 2px solid #78b8ff;
                }
            """)
        else:
            self.mode_status.setText("OFFLINE")
            self.mode_status.setStyleSheet("""
                QLabel {
                    color: #50fa7b;
                    font-family: 'Courier New', monospace;
                    font-size: 10px;
                    font-weight: bold;
                    background-color: rgba(10, 15, 30, 200);
                    padding: 4px 6px;
                    border: 2px solid #50fa7b;
                }
            """)

    def send_message(self) -> None:
        """Send the user's message to the backend and display the reply."""
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self._append_user(text)

        selected_mode = self.mode_combo.currentText()

        try:
            resp = requests.post(
                f"{API_URL}/chat",
                json={"message": text, "mode": selected_mode},
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data.get("response", "...")
            mode_used = data.get("mode_used", selected_mode)
        except Exception as e:
            reply = f"(Backend error: {e})"
            mode_used = "error"

        self._append_bot(reply, mode_badge=mode_used if mode_used != "error" else "")
        if mode_used != "error":
            self._update_mode_status(mode_used)


# ---------------------------------------------------------------------------
# Pet Window
# ---------------------------------------------------------------------------

class PetWindow(QWidget):
    """Transparent, always-on-top and draggable GIF window."""

    def __init__(self) -> None:
        super().__init__()
        self.current_mood: str | None = None
        self.movie: QMovie | None = None
        self.drag_offset = None
        self.chat_window: ChatWindow | None = None

        # Keyboard tracking
        self.last_keyboard_time = time.monotonic() - KEYBOARD_IDLE_DELAY_SECONDS
        self.keyboard_listener = keyboard.Listener(on_press=self._on_key_press)
        self.keyboard_listener.start()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(WINDOW_SIZE, WINDOW_SIZE)

        self.pet_label = QLabel("Connecting...", self)
        self.pet_label.setAlignment(Qt.AlignCenter)
        self.pet_label.setGeometry(self.rect())
        self.pet_label.setStyleSheet("color: white; font-size: 14px;")
        self.pet_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        # Poll backend every 2 seconds; fast timer checks keyboard/drag every 100ms
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._poll_backend)
        self._poll_backend()
        self.status_timer.start(2_000)

        self.activity_timer = QTimer(self)
        self.activity_timer.timeout.connect(self._update_mood)
        self.activity_timer.start(100)

        # Cached backend values
        self._backend_mood: str = "idle"
        self._backend_cpu: float = 0.0
        self._backend_mem: float = 0.0

    def _on_key_press(self, key) -> None:
        """Record the timestamp of the most recent key press."""
        self.last_keyboard_time = time.monotonic()

    def _poll_backend(self) -> None:
        """Fetch system status from the backend every 2 seconds."""
        try:
            response = requests.get(f"{API_URL}/status", timeout=1)
            response.raise_for_status()
            data = response.json()
            self._backend_mood = data.get("mood", "idle")
            self._backend_cpu = float(data.get("cpu", 0))
            self._backend_mem = float(data.get("memory", 0))
        except Exception as error:
            self.setToolTip(f"Backend disconnected; keeping last state. ({error})")
            if self.current_mood is None:
                self.pet_label.setText("Backend\ndisconnected")

    def _update_mood(self) -> None:
        """Decide the current mood based on keyboard activity and backend data."""
        recently_typing = (
            time.monotonic() - self.last_keyboard_time < KEYBOARD_IDLE_DELAY_SECONDS
        )
        is_dragging = self.drag_offset is not None

        if is_dragging:
            mood = "moving"
        elif recently_typing:
            mood = "working"
        else:
            mood = self._backend_mood

        self.set_mood(mood)
        activity = "typing" if recently_typing else "not typing"
        self.setToolTip(
            f"CPU: {self._backend_cpu:.1f}% | Memory: {self._backend_mem:.1f}% | "
            f"Keyboard: {activity} | Mood: {mood}"
        )

    def set_mood(self, mood: str) -> None:
        """Load and play the GIF belonging to the requested mood."""
        if mood == self.current_mood:
            return
        gif_path = GIFS.get(mood)
        if gif_path is None or not gif_path.is_file():
            self.pet_label.setMovie(None)
            name = gif_path.name if gif_path else mood
            self.pet_label.setText(f"Missing GIF:\n{name}")
            self.current_mood = mood
            return
        if self.movie is not None:
            self.movie.stop()
        self.movie = QMovie(str(gif_path))
        self.movie.setScaledSize(self.pet_label.size().boundedTo(
            self.pet_label.size()
        ).scaled(GIF_SIZE, GIF_SIZE, Qt.KeepAspectRatio))
        self.pet_label.setText("")
        self.pet_label.setMovie(self.movie)
        self.movie.start()
        self.current_mood = mood

    # ---- mouse drag ----

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.drag_offset = event.globalPos() - self.frameGeometry().topLeft()
            self._update_mood()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if self.drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.drag_offset = None
            self._update_mood()
            event.accept()

    # ---- right-click context menu ----

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1a1a2e;
                color: #ffffff;
                border: 2px solid #e94560;
                border-radius: 4px;
                padding: 4px;
                font-family: 'Courier New', monospace;
                font-size: 13px;
            }
            QMenu::item:selected {
                background-color: #e94560;
                color: #ffffff;
            }
        """)

        chat_action = menu.addAction(" Chat with Kuchu-Puchu")
        menu.addSeparator()
        quit_action = menu.addAction(" Quit Pet")

        action = menu.exec_(self.mapToGlobal(event.pos()))

        if action == chat_action:
            self._open_chat()
        elif action == quit_action:
            self.close()

    def _open_chat(self) -> None:
        """Open the chat window positioned above the pet."""
        if self.chat_window is None or not self.chat_window.isVisible():
            self.chat_window = ChatWindow(parent=None)
        # Position above the pet
        pet_pos = self.frameGeometry().topLeft()
        chat_x = pet_pos.x() - 140
        chat_y = pet_pos.y() - 470  # extra height for mode selector
        # Keep on screen
        screen = QApplication.primaryScreen().geometry()
        chat_x = max(0, min(chat_x, screen.width() - 340))
        chat_y = max(0, min(chat_y, screen.height() - 460))
        self.chat_window.move(chat_x, chat_y)
        self.chat_window.show()
        self.chat_window.raise_()
        self.chat_window.input_field.setFocus()

    def closeEvent(self, event) -> None:
        """Clean up keyboard listener and chat window on exit."""
        self.keyboard_listener.stop()
        if self.chat_window is not None:
            self.chat_window.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = PetWindow()
    pet.show()
    sys.exit(app.exec_())
