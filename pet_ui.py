"""Phase 1: a draggable desktop pet that reacts to local system usage.

Put idle.gif, working.gif, and alert.gif in the assets folder next to this file.
"""

import sys
import time
from pathlib import Path

import psutil
from pynput import keyboard
from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QMenu
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist


# This makes asset paths work no matter which folder you run Python from.
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
GIFS = {
    "idle": ASSETS_DIR / "idle.gif",
    "working": ASSETS_DIR / "working.gif",
    "alert": ASSETS_DIR / "alert.gif",
    "moving": ASSETS_DIR / "moving.gif",
}

def get_sound_path(mood: str) -> Path | None:
    for ext in [".mp3", ".wav"]:
        path = ASSETS_DIR / f"{mood}{ext}"
        if path.is_file():
            return path
    return None

# Keep the desktop pet approximately the size of a dock/app icon.
WINDOW_SIZE = 72
GIF_SIZE = 64
# After the most recent key press, keep the working animation for a short
# time. Trackpad and mouse activity intentionally do not count.
KEYBOARD_IDLE_DELAY_SECONDS = 1


def choose_mood(cpu: float, memory: float, recently_typing: bool, is_dragging: bool = False) -> str:
    """Choose a mood from system pressure first, then user input activity."""
    if is_dragging:
        return "moving"
    # Alert remains a useful safety state when the computer is overloaded.
    if cpu >= 80 or memory >= 90:
        return "alert"
    # Normal CPU/RAM usage does not make the pet work. It works only just
    # after a keyboard press; trackpad and mouse usage are ignored.
    if recently_typing:
        return "working"
    return "idle"


class PetWindow(QWidget):
    """Small transparent window that displays one animated GIF at a time."""

    def __init__(self) -> None:
        super().__init__()
        self.current_mood: str | None = None
        self.movie: QMovie | None = None
        self.player = QMediaPlayer()
        self.player.setVolume(10)
        self.playlist = QMediaPlaylist()
        self.player.setPlaylist(self.playlist)
        self.drag_offset = None
        # Start as idle; this time is deliberately older than the delay.
        self.last_keyboard_time = time.monotonic() - KEYBOARD_IDLE_DELAY_SECONDS
        self.cpu = 0.0
        self.memory = 0.0

        # Remove the title bar, keep the window above other applications,
        # and avoid showing it in the taskbar (Qt.Tool).
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(WINDOW_SIZE, WINDOW_SIZE)

        self.pet_label = QLabel("Loading pet…", self)
        self.pet_label.setAlignment(Qt.AlignCenter)
        self.pet_label.setGeometry(self.rect())
        self.pet_label.setStyleSheet("color: white; font-size: 14px;")
        # Let this parent widget receive drag mouse events over the GIF too.
        self.pet_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        # Prime psutil's CPU sampler. The next non-blocking reading is useful.
        psutil.cpu_percent(interval=None)

        # Receive keyboard events even while another app is in front.
        # There is no mouse/trackpad listener, by design.
        self.keyboard_listener = keyboard.Listener(on_press=self.record_key_press)
        self.keyboard_listener.start()

        # Resource values only need refreshing every two seconds.
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.refresh_system_status)
        # This lightweight timer checks the three-second typing delay often
        # enough that the GIF changes almost exactly on time.
        self.activity_timer = QTimer(self)
        self.activity_timer.timeout.connect(self.update_pet_mood)
        self.activity_timer.start(100)

        self.refresh_system_status()
        self.update_pet_status()  # Show a state immediately at startup.
        self.status_timer.start(2_000)  # 2,000 milliseconds = 2 seconds.

    def refresh_system_status(self) -> None:
        """Read CPU/RAM once every two seconds, then refresh the mood."""
        self.cpu = psutil.cpu_percent(interval=None)
        self.memory = psutil.virtual_memory().percent
        self.update_pet_mood()

    def update_pet_mood(self) -> None:
        """Choose the GIF from cached system status and recent key activity."""
        recently_typing = (
            time.monotonic() - self.last_keyboard_time
            < KEYBOARD_IDLE_DELAY_SECONDS
        )
        is_dragging = self.drag_offset is not None
        mood = choose_mood(self.cpu, self.memory, recently_typing, is_dragging)
        self.set_mood(mood)
        activity = "typing" if recently_typing else "not typing"
        self.setToolTip(
            f"CPU: {self.cpu:.1f}% | Memory: {self.memory:.1f}% | "
            f"Keyboard: {activity} | Mood: {mood}"
        )

    def update_pet_status(self) -> None:
        """Compatibility helper used during startup."""
        self.update_pet_mood()

    def record_key_press(self, key) -> None:
        """Record a key press. Repeated typing keeps resetting the 3-second wait."""
        self.last_keyboard_time = time.monotonic()

    def set_mood(self, mood: str) -> None:
        """Replace the QMovie only when the mood actually changes."""
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
        # Scale the complete GIF into a compact icon-sized area.  This avoids
        # the large original GIF overflowing/cropping inside the small window.
        self.movie.setScaledSize(self.pet_label.size().boundedTo(
            self.pet_label.size()
        ).scaled(GIF_SIZE, GIF_SIZE, Qt.KeepAspectRatio))
        self.pet_label.setText("")
        self.pet_label.setMovie(self.movie)
        self.movie.start()
        self.current_mood = mood

        sound_path = get_sound_path(mood)
        self.playlist.clear()
        if sound_path:
            self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(str(sound_path))))
            if mood in ["moving", "working"]:
                self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
            else:
                self.playlist.setPlaybackMode(QMediaPlaylist.CurrentItemOnce)
            self.player.play()
        else:
            self.player.stop()

    def mousePressEvent(self, event) -> None:
        """Remember where the user grabbed the pet with the left mouse button."""
        if event.button() == Qt.LeftButton:
            self.drag_offset = event.globalPos() - self.frameGeometry().topLeft()
            self.update_pet_mood()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        """Move the frameless window while the left button is held down."""
        if self.drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        """Finish a drag operation."""
        if event.button() == Qt.LeftButton:
            self.drag_offset = None
            self.update_pet_mood()
            event.accept()

    def contextMenuEvent(self, event) -> None:
        """Allow closing the pet using a right-click menu."""
        menu = QMenu(self)
        quit_action = menu.addAction("Quit Pet")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == quit_action:
            self.close()

    def closeEvent(self, event) -> None:
        """Stop background input listeners when the pet is closed."""
        self.keyboard_listener.stop()
        self.player.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = PetWindow()
    pet.show()
    sys.exit(app.exec_())
