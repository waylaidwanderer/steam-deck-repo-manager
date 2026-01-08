from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QProgressBar,
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QPixmap, QDesktopServices
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply


class VideoCard(QFrame):
    install_clicked = Signal(object)
    details_clicked = Signal(object)

    def __init__(self, post_data, parent=None):
        super().__init__(parent)
        self.post_data = post_data

        self.setObjectName("VideoCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # INLINE STYLE to force the border and background
        self.setStyleSheet("""
            QFrame#VideoCard {
                background-color: #1e293b;
                border: 2px solid #475569; /* Slate 600 */
                border-radius: 12px;
            }
            QFrame#VideoCard:hover {
                background-color: #334155; /* Slate 700 */
                border: 2px solid #3b82f6; /* Blue 500 */
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Optimize size for 1280x800 grid (Steam Deck)
        self.setFixedSize(290, 290)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)

        # Thumbnail
        self.thumb_label = QLabel()
        self.thumb_label.setFixedHeight(140)
        self.thumb_label.setStyleSheet(
            "background-color: #020617; border-radius: 6px; border: none;"
        )
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setText("Loading...")
        self.thumb_label.setScaledContents(True)
        layout.addWidget(self.thumb_label)

        # Title
        title_text = post_data.get("title", "Untitled")
        self.title_label = QLabel(title_text)
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #f1f5f9; background: transparent; border: none;"
        )
        self.title_label.setFixedHeight(40)
        self.title_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        layout.addWidget(self.title_label)

        # Meta Row (Author + Stats)
        meta_layout = QHBoxLayout()
        meta_layout.setContentsMargins(0, 0, 0, 0)

        # Author (Truncated)
        user_data = post_data.get("user", {})
        author_text = user_data.get("steam_name", "Unknown")
        self.author_label = QLabel(f"By {author_text}")
        self.author_label.setStyleSheet(
            "color: #94a3b8; font-size: 11px; background: transparent; border: none;"
        )
        meta_layout.addWidget(self.author_label)

        meta_layout.addStretch()

        # Stats (Downloads) - Assuming 'downloads' key exists
        downloads = post_data.get("downloads", 0)
        self.stats_label = QLabel(f"{downloads} DLs")
        self.stats_label.setStyleSheet(
            "color: #94a3b8; font-size: 11px; background: transparent; border: none;"
        )
        meta_layout.addWidget(self.stats_label)

        layout.addLayout(meta_layout)

        # Spacer
        layout.addStretch(1)

        # Buttons Row
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(4)

        # Details Button
        self.details_btn = QPushButton("Info")
        self.details_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.details_btn.setFixedHeight(30)
        self.details_btn.setFixedWidth(60)
        self.details_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                padding: 4px;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        self.details_btn.clicked.connect(self.on_details)
        btn_layout.addWidget(self.details_btn)

        # Install Button
        self.install_btn = QPushButton("Install")
        self.install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.install_btn.setFixedHeight(30)
        self.install_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 4px;
            }
            QPushButton:hover { background-color: #2563eb; }
        """)
        self.install_btn.clicked.connect(self.on_install)
        btn_layout.addWidget(self.install_btn)

        layout.addLayout(btn_layout)

        # Progress Bar (Hidden initially)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setFixedHeight(8)
        self.progress.setVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar { border: none; background: #334155; border-radius: 4px; }
            QProgressBar::chunk { background: #3b82f6; border-radius: 4px; }
        """)
        layout.addWidget(self.progress)

        # Load Image
        self.net_manager = QNetworkAccessManager(self)
        self.net_manager.finished.connect(self.on_image_loaded)
        if post_data.get("thumbnail"):
            self.net_manager.get(QNetworkRequest(QUrl(post_data["thumbnail"])))

    def on_image_loaded(self, reply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            self.thumb_label.setText("")
            self.thumb_label.setPixmap(pixmap)
        else:
            self.thumb_label.setText("No Image")
        reply.deleteLater()

    def on_install(self):
        self.install_clicked.emit(self.post_data)
        self.install_btn.setVisible(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)

    def on_details(self):
        self.details_clicked.emit(self.post_data)

    def mousePressEvent(self, event):
        # Trigger details view on click, but respect child widget events
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_details()
        super().mousePressEvent(event)

    def set_progress(self, value):
        self.progress.setValue(value)

    def reset_state(self):
        self.install_btn.setVisible(True)
        self.progress.setVisible(False)
        self.install_btn.setText("Installed!")
        self.install_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 4px;
            }
            QPushButton:hover { background-color: #16a34a; }
        """)


class LibraryItem(QFrame):
    delete_clicked = Signal(str)  # Emits filename

    def __init__(self, file_data, parent=None):
        super().__init__(parent)
        self.file_data = file_data
        meta = file_data.get("meta", {})

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 8px;
                border: 1px solid #334155;
            }
            QFrame:hover {
                background-color: #334155;
                border: 1px solid #475569;
            }
        """)
        self.setFixedHeight(80)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 15, 5)
        layout.setSpacing(15)

        # Thumbnail
        thumb_label = QLabel()
        thumb_label.setFixedSize(100, 60)
        thumb_label.setStyleSheet(
            "background-color: #020617; border-radius: 4px; border: none;"
        )
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if meta.get("local_thumbnail"):
            pixmap = QPixmap(meta["local_thumbnail"])
            thumb_label.setPixmap(
                pixmap.scaled(
                    100,
                    60,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            thumb_label.setText("No Image")
            thumb_label.setStyleSheet(
                "color: #475569; font-size: 10px; background-color: #0f172a; border-radius: 4px;"
            )

        layout.addWidget(thumb_label)

        # Info Column
        info_container = QWidget()
        info_container.setStyleSheet("background: transparent; border: none;")
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 5, 0, 5)
        info_layout.setSpacing(2)

        # Title (Fallback to filename if no meta)
        display_title = meta.get("title", file_data["filename"])
        name_label = QLabel(display_title)
        name_label.setStyleSheet(
            "color: #f1f5f9; font-size: 14px; font-weight: bold; background: transparent; border: none;"
        )
        info_layout.addWidget(name_label)

        # Author / Filename fallback
        sub_text = (
            f"By {meta.get('user', {}).get('steam_name', 'Unknown')}"
            if meta.get("title")
            else file_data["filename"]
        )
        author_label = QLabel(sub_text)
        author_label.setStyleSheet(
            "color: #94a3b8; font-size: 11px; background: transparent; border: none;"
        )
        info_layout.addWidget(author_label)

        info_layout.addStretch()
        layout.addWidget(info_container)

        layout.addStretch()

        # Type Indicator
        vtype = file_data.get("type", "boot")
        type_color = (
            "#3b82f6" if vtype == "boot" else "#f59e0b"
        )  # Blue for boot, Amber for suspend
        type_label = QLabel(vtype.upper())
        type_label.setStyleSheet(
            f"color: {type_color}; font-weight: bold; font-size: 10px; background: transparent; border: none;"
        )
        layout.addWidget(type_label)

        # Size
        size_label = QLabel(f"{file_data['size_mb']} MB")
        size_label.setStyleSheet(
            "color: #94a3b8; font-size: 12px; background: transparent; border: none;"
        )
        layout.addWidget(size_label)

        layout.addSpacing(10)

        # Delete Button Container (StackLayout or just hiding/showing)
        self.btn_container = QWidget()
        self.btn_container.setStyleSheet("background: transparent;")
        self.btn_layout = QHBoxLayout(self.btn_container)
        self.btn_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Delete Button (Normal)
        self.del_btn = QPushButton("Delete")
        self.del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.del_btn.setFixedWidth(80)
        self.del_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                padding: 4px;
            }
            QPushButton:hover { background-color: #dc2626; }
        """)
        self.del_btn.clicked.connect(self.show_confirm)
        self.btn_layout.addWidget(self.del_btn)

        # 2. Confirm Button (Hidden)
        self.confirm_btn = QPushButton("Sure?")
        self.confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_btn.setFixedWidth(60)
        self.confirm_btn.setVisible(False)
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #b91c1c;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                padding: 4px;
            }
            QPushButton:hover { background-color: #991b1b; }
        """)
        self.confirm_btn.clicked.connect(self.do_delete)
        self.btn_layout.addWidget(self.confirm_btn)

        # 3. Cancel Button (Hidden)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setFixedWidth(60)
        self.cancel_btn.setVisible(False)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #475569;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                padding: 4px;
            }
            QPushButton:hover { background-color: #64748b; }
        """)
        self.cancel_btn.clicked.connect(self.reset_delete)
        self.btn_layout.addWidget(self.cancel_btn)

        layout.addWidget(self.btn_container)

    def show_confirm(self):
        self.del_btn.setVisible(False)
        self.confirm_btn.setVisible(True)
        self.cancel_btn.setVisible(True)

    def reset_delete(self):
        self.del_btn.setVisible(True)
        self.confirm_btn.setVisible(False)
        self.cancel_btn.setVisible(False)

    def do_delete(self):
        self.delete_clicked.emit(self.file_data["filename"])

    def on_delete(self):
        # Deprecated logic, keeping for interface compatibility if needed
        pass
