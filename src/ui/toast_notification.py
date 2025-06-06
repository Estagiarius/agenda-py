import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QGraphicsDropShadowEffect, QScreen
)
from PyQt6.QtCore import Qt, QTimer, QRect, QPoint, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QPalette, QMouseEvent

class ToastNotification(QWidget):
    def __init__(self, title: str, message: str, duration: int = 5000, parent: QWidget = None):
        super().__init__(parent)
        self.duration = duration

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool # Behaves like a tool window (doesn't take focus from main app as much)
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating) # Important: doesn't steal focus

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10) # Padding inside the toast

        # Title Label
        self.title_label = QLabel(title)
        self.title_label.setObjectName("ToastTitle") # For styling
        self.title_label.setStyleSheet("""
            QLabel#ToastTitle {
                font-weight: bold;
                font-size: 14px;
                color: #ffffff; /* White text */
            }
        """)

        # Message Label
        self.message_label = QLabel(message)
        self.message_label.setObjectName("ToastMessage")
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("""
            QLabel#ToastMessage {
                font-size: 12px;
                color: #f0f0f0; /* Light grey text */
            }
        """)

        layout.addWidget(self.title_label)
        layout.addWidget(self.message_label)

        # Styling the toast widget itself (background, border-radius)
        # Using QPalette for background to ensure WA_TranslucentBackground works well.
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0, 200)) # Semi-transparent black
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # Apply a border radius via stylesheet (may not work perfectly with WA_TranslucentBackground on all platforms)
        # A more robust way for rounded corners with transparency is to override paintEvent.
        # For simplicity, trying stylesheet first.
        self.setStyleSheet("""
            ToastNotification {
                border-radius: 8px;
            }
        """)
        # Note: True rounded corners with WA_TranslucentBackground might require custom painting.
        # The stylesheet border-radius might only affect children or not be visible.

        # Shadow (optional, can be heavy)
        # shadow = QGraphicsDropShadowEffect(self)
        # shadow.setBlurRadius(15)
        # shadow.setXOffset(0)
        # shadow.setYOffset(0)
        # shadow.setColor(QColor(0, 0, 0, 80))
        # self.setGraphicsEffect(shadow) # Apply to the widget itself

        # Dismiss Timer
        self.dismiss_timer = QTimer(self)
        self.dismiss_timer.setSingleShot(True)
        self.dismiss_timer.timeout.connect(self.close_toast)

        # Opacity animation (optional)
        self.animation = QPropertyAnimation(self, b"windowOpacity", self)
        self.animation.setDuration(300) # ms for fade-in/out
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)


    def show_toast(self):
        self.setWindowOpacity(0.0) # Start fully transparent for fade-in
        self.adjustSize() # Adjust size to content before positioning

        # Position toast (e.g., bottom-right of primary screen)
        primary_screen = QGuiApplication.primaryScreen()
        if not primary_screen: # Fallback if primaryScreen() is None
             screens = QGuiApplication.screens()
             if not screens: return # Should not happen
             primary_screen = screens[0]

        available_geometry = primary_screen.availableGeometry()

        # Calculate position: bottom-right corner
        margin = 20 # Margin from screen edges
        x = available_geometry.right() - self.width() - margin
        y = available_geometry.bottom() - self.height() - margin

        self.move(QPoint(x, y))
        self.show()

        # Start fade-in animation
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()

        self.dismiss_timer.start(self.duration)

    def close_toast(self):
        # Start fade-out animation
        self.animation.setStartValue(self.windowOpacity()) # Current opacity
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self._on_animation_finished) # Close after fade out
        self.animation.start()

    def _on_animation_finished(self):
        if self.windowOpacity() == 0.0: # Ensure it's the fade-out that finished
            self.close()
            self.deleteLater() # Important for cleanup

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dismiss_timer.stop() # Stop timer if clicked
            self.close_toast() # Start closing process
        super().mousePressEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Main window (dummy) to host the button
    main_widget = QWidget()
    main_widget.setGeometry(300, 300, 300, 200)
    main_widget.setWindowTitle("Test Toast Notifications")

    btn_layout = QVBoxLayout(main_widget)

    test_button = QPushButton("Show Toast")

    toast_count = 0
    def on_button_click():
        global toast_count
        toast_count += 1
        toast = ToastNotification(
            f"Test Toast {toast_count}!",
            "This is a sample toast notification message.\nIt should disappear automatically or on click.",
            duration=5000,
            parent=None # No parent, so it's a top-level window
        )
        toast.show_toast()

    test_button.clicked.connect(on_button_click)
    btn_layout.addWidget(test_button)

    main_widget.show()

    # Show a toast on startup for quick test
    # initial_toast = ToastNotification("Welcome!", "Application started.", duration=3000)
    # initial_toast.show_toast()

    sys.exit(app.exec())
