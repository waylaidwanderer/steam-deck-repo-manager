import sys
import os
import platform

# Pre-import essentials
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer


def main():
    app = QApplication(sys.argv)

    # Use a raw QWidget for the splash screen
    splash = QWidget()
    splash.setWindowFlags(
        Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
    )
    splash.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
    splash.setStyleSheet("background-color: #0f172a;")
    splash.setFixedSize(400, 200)

    # Add Text
    layout = QVBoxLayout(splash)
    label = QLabel("Loading Steam Deck Repo Manager...")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet("color: #3b82f6; font-size: 16px; font-weight: bold;")
    layout.addWidget(label)

    # Center splash on primary screen
    screen_geo = app.primaryScreen().geometry()
    x = (screen_geo.width() - 400) // 2
    y = (screen_geo.height() - 200) // 2
    splash.move(x, y)

    splash.show()

    # Use a container to keep the window reference alive
    refs = []

    def load_application():
        # Heavy imports (Lazy Loaded)
        from src.gui.window import MainWindow

        window = MainWindow()
        window.show()

        splash.close()

        # Keep window reference alive
        refs.append(window)

    # Schedule loader to run AFTER the event loop starts
    QTimer.singleShot(50, load_application)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
