from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve


class NotificationToast(QWidget):
    """
    A non-blocking notification toast that slides up from the bottom.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setMinimumWidth(300)
        self.setMaximumWidth(800)

        self.setStyleSheet("background: transparent; border: none;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)

        self.label = QLabel("Notification")
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        # Initial state: hidden (transparent)
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        self.hide()

        # Animations
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.Type.OutQuad)

        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(300)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.setEasingCurve(QEasingCurve.Type.InQuad)
        self.fade_out.finished.connect(self.hide)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_toast)

    def show_message(self, message, duration=3000, is_error=False):
        self.label.setText(message)
        if is_error:
            self.setStyleSheet("""
                QWidget#Toast {
                    background-color: #450a0a; /* Dark Red */
                    border: 1px solid #ef4444;
                    border-radius: 8px;
                }
                QLabel { color: #fecaca; font-size: 16px; padding: 4px; background: transparent; border: none; }
            """)
        else:
            self.setStyleSheet("""
                QWidget#Toast {
                    background-color: #1e293b; /* Slate 800 */
                    border: 1px solid #334155; /* Slate 700 */
                    border-radius: 8px;
                }
                QLabel { color: #f1f5f9; font-size: 16px; padding: 4px; background: transparent; border: none; }
            """)

        self.adjustSize()  # Ensure size is recalculated for new text/style
        self.show()
        self.raise_()

        # Center horizontally at the bottom
        parent = self.parentWidget()
        if parent:
            geo = parent.geometry()
            x = (geo.width() - self.width()) // 2
            y = geo.height() - self.height() - 80
            self.move(x, y)

        self.fade_in.start()
        self.timer.start(duration)

    def hide_toast(self):
        self.fade_out.start()
