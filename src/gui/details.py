from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QScrollArea,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QPixmap, QDesktopServices
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


class DetailsView(QWidget):
    # Signals to communicate with MainWindow
    back_clicked = Signal()
    install_clicked = Signal(dict)  # Passes post_data back

    def __init__(self, parent=None):
        super().__init__(parent)
        self.post_data = {}

        # Root layout: Horizontal Split
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # --- LEFT SIDE: Video/Preview (65% width) ---
        left_container = QWidget()
        left_container.setStyleSheet("background-color: #020617;")
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Video Widget
        self.video_widget = QVideoWidget()
        self.video_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        left_layout.addWidget(self.video_widget)

        # Media Player Setup
        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        self.player.setLoops(QMediaPlayer.Loops.Infinite)  # Loop by default

        # Thumbnail Overlay (initially visible, hidden when video plays)
        self.thumb_label = QLabel(self.video_widget)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setScaledContents(True)
        self.thumb_label.setStyleSheet("background-color: #020617;")
        # Note: We'll resize thumb_label in resizeEvent to cover video_widget

        root_layout.addWidget(left_container, stretch=65)

        # --- RIGHT SIDE: Info (35% width) ---
        right_container = QWidget()
        right_container.setStyleSheet("background-color: #0f172a;")
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(15)

        # 1. Back Button
        self.back_btn = QPushButton("← Back")
        self.back_btn.setFixedSize(100, 36)
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #f1f5f9;
                border: 1px solid #475569;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                padding: 4px;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        self.back_btn.clicked.connect(self.on_back)
        right_layout.addWidget(self.back_btn)

        # 2. Title
        self.title_label = QLabel()
        self.title_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #f1f5f9;"
        )
        self.title_label.setWordWrap(True)
        right_layout.addWidget(self.title_label)

        # 3. Meta Info
        self.meta_label = QLabel()
        self.meta_label.setStyleSheet("font-size: 14px; color: #cbd5e1;")
        self.meta_label.setWordWrap(True)
        right_layout.addWidget(self.meta_label)

        # 4. Description (Scrollable Text)
        self.desc_scroll = QScrollArea()
        self.desc_scroll.setWidgetResizable(True)
        self.desc_scroll.setStyleSheet("background: transparent; border: none;")
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        self.desc_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self.desc_label.setStyleSheet(
            "font-size: 14px; color: #94a3b8; line-height: 1.4;"
        )
        self.desc_scroll.setWidget(self.desc_label)
        right_layout.addWidget(self.desc_scroll)

        # 5. Spacer
        # right_layout.addStretch()

        # 6. Install Button
        self.install_btn = QPushButton("Install Video")
        self.install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.install_btn.setFixedHeight(50)
        self.install_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 18px;
                padding: 4px;
            }
            QPushButton:hover { background-color: #2563eb; }
        """)
        self.install_btn.clicked.connect(
            lambda: self.install_clicked.emit(self.post_data)
        )
        right_layout.addWidget(self.install_btn)

        root_layout.addWidget(right_container, stretch=35)

        # Network for thumbnail
        self.net_manager = QNetworkAccessManager(self)
        self.net_manager.finished.connect(self.on_image_loaded)

    def load_post(self, post_data):
        self.post_data = post_data

        # Populate Info
        self.title_label.setText(post_data.get("title", "Untitled"))

        user_data = post_data.get("user", {})
        author = user_data.get("steam_name", "Unknown")
        downloads = post_data.get("downloads", 0)
        likes = post_data.get("likes", 0)
        self.meta_label.setText(
            f"By <b>{author}</b><br>{downloads} Downloads • {likes} Likes"
        )

        self.desc_label.setText(post_data.get("content", "No description provided."))

        # Video Logic
        video_url = post_data.get("video")
        # Fallback to preview if main video missing? Usually video is present.

        if video_url:
            self.player.setSource(QUrl(video_url))
            self.player.play()
            self.thumb_label.hide()
        else:
            self.player.stop()
            self.thumb_label.show()

        # Load Thumbnail (as fallback/poster)
        self.thumb_label.setText("Loading Preview...")
        self.thumb_label.setPixmap(QPixmap())
        if post_data.get("thumbnail"):
            self.net_manager.get(QNetworkRequest(QUrl(post_data["thumbnail"])))

    def on_image_loaded(self, reply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            self.thumb_label.setPixmap(pixmap)
            # Center and scale thumb_label to fill video area
            self.resize_thumbnail()
        reply.deleteLater()

    def resizeEvent(self, event):
        self.resize_thumbnail()
        super().resizeEvent(event)

    def resize_thumbnail(self):
        if hasattr(self, "video_widget") and hasattr(self, "thumb_label"):
            self.thumb_label.resize(self.video_widget.size())

    def on_back(self):
        self.player.stop()
        self.back_clicked.emit()
