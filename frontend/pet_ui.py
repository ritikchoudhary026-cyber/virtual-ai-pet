"""Phase 2: a desktop pet that gets its mood from the local FastAPI backend."""

import sys
from pathlib import Path

import requests
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QApplication, QLabel, QWidget


API_URL = "http://localhost:8000/status"
# frontend is one directory below the project root, where assets lives.
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
GIFS = {
    "idle": ASSETS_DIR / "idle.gif",
    "working": ASSETS_DIR / "working.gif",
    "alert": ASSETS_DIR / "alert.gif",
}

# Keep the desktop pet approximately the size of a dock/app icon.
WINDOW_SIZE = 56
GIF_SIZE = 48


class PetWindow(QWidget):
    """Transparent, always-on-top and draggable GIF window."""

    def __init__(self) -> None:
        super().__init__()
        self.current_mood: str | None = None
        self.movie: QMovie | None = None
        self.drag_offset = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(WINDOW_SIZE, WINDOW_SIZE)

        self.pet_label = QLabel("Connecting to PetAI…", self)
        self.pet_label.setAlignment(Qt.AlignCenter)
        self.pet_label.setGeometry(self.rect())
        self.pet_label.setStyleSheet("color: white; font-size: 14px;")
        # Let this parent widget receive drag mouse events over the GIF too.
        self.pet_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.fetch_status)
        self.fetch_status()
        self.status_timer.start(2_000)

    def fetch_status(self) -> None:
        """Request status from FastAPI; preserve the last animation on errors."""
        try:
            response = requests.get(API_URL, timeout=1)
            response.raise_for_status()
            data = response.json()
            mood = data.get("mood")
            if mood not in GIFS:
                raise ValueError("The backend returned an unknown mood.")
            self.set_mood(mood)
            self.setToolTip(
                f"CPU: {float(data['cpu']):.1f}% | Memory: {float(data['memory']):.1f}%"
            )
        except (requests.RequestException, ValueError, KeyError, TypeError) as error:
            # Do not replace the last successful GIF with an error screen.
            # The tooltip makes the problem visible without interrupting the pet.
            self.setToolTip(f"Backend disconnected; keeping last state. ({error})")
            if self.current_mood is None:
                self.pet_label.setText("Backend\ndisconnected")

    def set_mood(self, mood: str) -> None:
        """Load and play the GIF belonging to the requested mood."""
        if mood == self.current_mood:
            return
        gif_path = GIFS[mood]
        if not gif_path.is_file():
            self.pet_label.setMovie(None)
            self.pet_label.setText(f"Missing GIF:\n{gif_path.name}")
            self.current_mood = mood
            return
        if self.movie is not None:
            self.movie.stop()
        self.movie = QMovie(str(gif_path))
        # Scale the full GIF into the compact label, preserving its ratio.
        self.movie.setScaledSize(self.pet_label.size().boundedTo(
            self.pet_label.size()
        ).scaled(GIF_SIZE, GIF_SIZE, Qt.KeepAspectRatio))
        self.pet_label.setText("")
        self.pet_label.setMovie(self.movie)
        self.movie.start()
        self.current_mood = mood

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.drag_offset = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if self.drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.drag_offset = None
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = PetWindow()
    pet.show()
    sys.exit(app.exec_())
