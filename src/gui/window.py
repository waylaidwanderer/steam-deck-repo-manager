import sys
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QTabWidget,
    QScrollArea,
    QGridLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QDialog,
)
from PySide6.QtCore import Qt, QThread, Signal, QUrl, QObject
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from .theme import Theme
from .widgets import VideoCard, LibraryItem
from .details import DetailsView
from .toast import NotificationToast
from ..api import RepoAPI
from ..file_manager import FileManager
import tempfile
import os


class DataLoaderWorker(QThread):
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, api, force_refresh=False):
        super().__init__()
        self.api = api
        self.force_refresh = force_refresh

    def run(self):
        try:
            posts = self.api.get_all_posts(force_refresh=self.force_refresh)
            self.finished.emit(posts)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    PAGE_SIZE = 12

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steam Deck Repo Manager")
        self.resize(1280, 800)
        self.setMinimumSize(800, 600)
        self.setStyleSheet(Theme.get_stylesheet())

        self.api = RepoAPI()

        # Native Network Manager for fast downloads
        self.net_manager = QNetworkAccessManager(self)
        self.active_downloads = {}  # post_id -> reply

        # State
        self.all_posts = []
        self.filtered_posts_boot = []
        self.filtered_posts_suspend = []

        self.page_boot = 0
        self.page_suspend = 0

        self.card_map = {}

        self.init_ui()

        # Toast system
        self.toast = NotificationToast(self)

        # Start background loading
        self.start_loading()

    def resizeEvent(self, event):
        if self.centralWidget():
            width = self.width()
            height = self.height()

            # Optimized calculation for Steam Deck (1280x800)
            # Reserve space for Header, Tabs, Pagination Controls, and Footer area
            # Header (~60) + Tabs (~50) + Pagination (~40) + Margins (~20) = ~170px
            reserved_height = 180

            available_h = height - reserved_height
            available_w = width - 40

            # Card is now 290x270
            card_w = 290 + 20
            card_h = 270 + 10

            cols = max(1, available_w // card_w)
            rows = max(1, available_h // card_h)

            new_page_size = cols * rows

            if new_page_size != self.PAGE_SIZE and new_page_size > 0:
                self.PAGE_SIZE = new_page_size
                # Refresh view
                self.render_page("boot")
                self.render_page("suspend")

        super().resizeEvent(event)

    def init_ui(self):
        # Create StackedWidget as Central
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # --- View 0: Loading ---
        self.loading_view = QLabel("Loading...")
        self.loading_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_view.setStyleSheet(
            "font-size: 24px; color: #3b82f6; font-weight: bold;"
        )
        self.stack.addWidget(self.loading_view)

        # --- View 1: Main Content ---
        self.main_content = QWidget()
        main_layout = QVBoxLayout(self.main_content)
        # Use 0 margins on main layout to maximize space, we add margins inside components
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.stack.addWidget(self.main_content)

        # --- View 2: Details View ---
        self.details_view = DetailsView()
        self.details_view.back_clicked.connect(self.show_main_view)
        self.details_view.install_clicked.connect(self.start_install)
        self.stack.addWidget(self.details_view)

        # Header
        header_layout = QHBoxLayout()

        # Refresh Button (Left)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedWidth(100)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet("padding: 4px;")
        refresh_btn.clicked.connect(lambda: self.start_loading(force=True))
        header_layout.addWidget(refresh_btn)

        header_layout.addStretch()

        title = QLabel("Steam Deck Repo Manager")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #3b82f6;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search videos...")
        self.search_bar.setFixedWidth(300)
        self.search_bar.textChanged.connect(self.filter_posts)
        header_layout.addWidget(self.search_bar)

        main_layout.addLayout(header_layout)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.tabBar().setCursor(Qt.CursorShape.PointingHandCursor)
        self.tab_boot = QWidget()
        self.tab_suspend = QWidget()
        self.tab_library = QWidget()

        self.tabs.addTab(self.tab_boot, "Boot Videos")
        self.tabs.addTab(self.tab_suspend, "Suspend Videos")
        self.tabs.addTab(self.tab_library, "Installed")
        self.tabs.currentChanged.connect(self.on_tab_changed)

        main_layout.addWidget(self.tabs)

        # Setup Layouts
        self.boot_layout, self.boot_container = self.create_grid_area(self.tab_boot)
        self.suspend_layout, self.suspend_container = self.create_grid_area(
            self.tab_suspend
        )
        self.library_layout, self.library_container = self.create_list_area(
            self.tab_library
        )

        # Add pagination controls
        self.add_pagination_controls(self.tab_boot, "boot")
        self.add_pagination_controls(self.tab_suspend, "suspend")

    def create_list_area(self, parent_widget):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"background-color: {Theme.SLATE_900}; border: none;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(container)

        parent_layout = QVBoxLayout(parent_widget)
        parent_layout.setContentsMargins(0, 0, 0, 0)
        parent_layout.addWidget(scroll)

        return layout, container

    def on_tab_changed(self, index):
        # Index 2 is Library
        if index == 2:
            self.render_library()

    def create_grid_area(self, parent_widget):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        # Remove border and background to be clean
        scroll.setStyleSheet(f"background-color: {Theme.SLATE_900}; border: none;")
        scroll.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        layout = QGridLayout(container)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)
        # CENTER THE GRID CONTENT
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        scroll.setWidget(container)

        parent_layout = QVBoxLayout(parent_widget)
        parent_layout.setContentsMargins(0, 5, 0, 0)
        parent_layout.addWidget(scroll)

        return layout, container

    def add_pagination_controls(self, parent_widget, type_key):
        # Create a container widget for styling
        container = QWidget()
        container.setObjectName("PaginationBar")
        container.setStyleSheet("""
            QWidget#PaginationBar {
                background-color: #1e293b;
                border-top: 1px solid #334155;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }
        """)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(20, 10, 20, 10)

        prev_btn = QPushButton("Previous")
        prev_btn.setFixedWidth(120)
        prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        prev_btn.setStyleSheet("padding: 6px;")
        prev_btn.clicked.connect(lambda: self.change_page(type_key, -1))

        next_btn = QPushButton("Next")
        next_btn.setFixedWidth(120)
        next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        next_btn.setStyleSheet("padding: 6px;")
        next_btn.clicked.connect(lambda: self.change_page(type_key, 1))

        # Center the buttons with some spacing
        layout.addStretch()
        layout.addWidget(prev_btn)
        layout.addSpacing(20)
        layout.addWidget(next_btn)
        layout.addStretch()

        # Add to the parent layout (after the scroll area)
        parent_widget.layout().addWidget(container)

    def start_loading(self, force=False):
        if not force:
            self.stack.setCurrentIndex(0)  # Show loading screen only on first load
        else:
            self.toast.show_message("Refreshing data...")

        self.loader = DataLoaderWorker(self.api, force_refresh=force)
        self.loader.finished.connect(self.on_data_loaded)
        self.loader.error.connect(self.on_load_error)
        self.loader.start()

    def on_data_loaded(self, posts):
        self.all_posts = posts
        self.filter_posts(self.search_bar.text())  # Apply current filter
        self.stack.setCurrentIndex(1)  # Show content
        self.toast.show_message(f"Loaded {len(posts)} videos", duration=2000)

    def on_load_error(self, error_msg):
        self.stack.setCurrentIndex(1)  # Go back to content even on error
        self.toast.show_message(f"Error: {error_msg}", duration=5000, is_error=True)

    def filter_posts(self, text):
        text = text.lower()

        # Filter raw data
        self.filtered_posts_boot = [
            p
            for p in self.all_posts
            if p.get("type") == "boot_video" and text in p.get("title", "").lower()
        ]
        self.filtered_posts_suspend = [
            p
            for p in self.all_posts
            if p.get("type") != "boot_video" and text in p.get("title", "").lower()
        ]

        # Reset pages
        self.page_boot = 0
        self.page_suspend = 0

        self.render_page("boot")
        self.render_page("suspend")

    def change_page(self, type_key, delta):
        if type_key == "boot":
            new_page = self.page_boot + delta
            max_pages = max(0, (len(self.filtered_posts_boot) - 1) // self.PAGE_SIZE)
            if 0 <= new_page <= max_pages:
                self.page_boot = new_page
                self.render_page("boot")
        else:
            new_page = self.page_suspend + delta
            max_pages = max(0, (len(self.filtered_posts_suspend) - 1) // self.PAGE_SIZE)
            if 0 <= new_page <= max_pages:
                self.page_suspend = new_page
                self.render_page("suspend")

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def render_page(self, type_key):
        if type_key == "boot":
            posts = self.filtered_posts_boot
            page = self.page_boot
            layout = self.boot_layout
        else:
            posts = self.filtered_posts_suspend
            page = self.page_suspend
            layout = self.suspend_layout

        self.clear_layout(layout)

        start = page * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        page_items = posts[start:end]

        row, col = 0, 0
        cols_per_row = 4

        for post in page_items:
            card = VideoCard(post)
            card.install_clicked.connect(self.start_install)
            card.details_clicked.connect(self.show_details)
            self.card_map[post["id"]] = card  # Update map for current view

            layout.addWidget(card, row, col)
            col += 1
            if col >= cols_per_row:
                col = 0
                row += 1

    def show_main_view(self):
        self.stack.setCurrentIndex(1)

    def show_details(self, post_data):
        self.details_view.load_post(post_data)
        self.stack.setCurrentIndex(2)  # Switch to details view

    # --- Native Networking Install Implementation ---

    def start_install(self, post_data):
        post_id = post_data["id"]

        # Prevent multiple downloads for the same video
        if post_id in self.active_downloads:
            return

        download_url = f"{self.api.BASE_URL}/post/download/{post_id}"

        # Create temp file immediately
        fd, temp_path = tempfile.mkstemp(suffix=".webm")
        os.close(
            fd
        )  # Close file handle so QNetworkReply can write to it via standard IO or buffer

        request = QNetworkRequest(QUrl(download_url))

        reply = self.net_manager.get(request)

        # Store state for this download
        self.active_downloads[post_id] = {
            "reply": reply,
            "file": open(temp_path, "wb"),  # Keep file open for writing
            "temp_path": temp_path,
            "post_data": post_data,
            "thumb_path": None,  # Will fill later
        }

        reply.downloadProgress.connect(
            lambda r, t, pid=post_id: self.on_download_progress(pid, r, t)
        )
        reply.finished.connect(lambda pid=post_id: self.on_download_finished(pid))
        reply.errorOccurred.connect(
            lambda err, pid=post_id: self.on_download_error(pid, err)
        )

    def on_download_progress(self, post_id, received, total):
        if post_id not in self.active_downloads:
            return

        data = self.active_downloads[post_id]

        # Write chunks to file
        reply = data["reply"]
        if reply.bytesAvailable():
            chunk = reply.readAll()
            data["file"].write(chunk)

        # Update UI
        if total > 0:
            percent = int((received / total) * 100)
            self.update_progress(post_id, percent)

    def on_download_finished(self, post_id):
        if post_id not in self.active_downloads:
            return

        data = self.active_downloads[post_id]
        reply = data["reply"]

        # Check for redirects manually (robust method)
        redirect_url = reply.attribute(
            QNetworkRequest.Attribute.RedirectionTargetAttribute
        )
        if redirect_url:
            print(f"Handling Redirect to {redirect_url}")
            new_url = reply.url().resolved(redirect_url)

            # Restart request with new URL
            reply.deleteLater()

            new_request = QNetworkRequest(new_url)
            new_reply = self.net_manager.get(new_request)

            # Update state with new reply
            data["reply"] = new_reply

            # Reconnect signals
            new_reply.downloadProgress.connect(
                lambda r, t, pid=post_id: self.on_download_progress(pid, r, t)
            )
            new_reply.finished.connect(
                lambda pid=post_id: self.on_download_finished(pid)
            )
            new_reply.errorOccurred.connect(
                lambda err, pid=post_id: self.on_download_error(pid, err)
            )
            return

        # Not a redirect, proceed
        # Flush remaining bytes
        if reply.bytesAvailable():
            chunk = reply.readAll()
            data["file"].write(chunk)

        data["file"].close()
        reply.deleteLater()

        if reply.error() != QNetworkReply.NetworkError.NoError:
            # Error handled by signal (or not? errorOccurred is usually enough)
            # We cleanup if error wasn't handled already
            return

        # Success - Now download thumbnail (if needed)
        post_data = data["post_data"]
        thumb_url = post_data.get("thumbnail")

        if thumb_url:
            self.download_thumbnail(post_id, thumb_url, data["temp_path"])
        else:
            self.finalize_install(post_id, data["temp_path"], None)

    def download_thumbnail(self, post_id, url, video_temp_path):
        request = QNetworkRequest(QUrl(url))
        reply = self.net_manager.get(request)

        # Create temp file for thumb
        fd, thumb_path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)

        # Attach to active_downloads to track it
        self.active_downloads[post_id]["thumb_reply"] = reply
        self.active_downloads[post_id]["thumb_path"] = thumb_path

        reply.finished.connect(lambda: self.on_thumb_finished(post_id))

    def on_thumb_finished(self, post_id):
        if post_id not in self.active_downloads:
            return

        data = self.active_downloads[post_id]
        reply = data["thumb_reply"]
        thumb_path = data["thumb_path"]

        if reply.error() == QNetworkReply.NetworkError.NoError:
            with open(thumb_path, "wb") as f:
                f.write(reply.readAll())
        else:
            # Failed to download thumb, ignore
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
            thumb_path = None

        reply.deleteLater()

        # Finish everything
        self.finalize_install(post_id, data["temp_path"], thumb_path)

    def on_download_error(self, post_id, error_code):
        if post_id in self.active_downloads:
            data = self.active_downloads[post_id]
            data["file"].close()
            if os.path.exists(data["temp_path"]):
                os.remove(data["temp_path"])

            error_str = data["reply"].errorString()
            self.toast.show_message(
                f"Download Error: {error_str}", is_error=True, duration=5000
            )

            # Reset UI
            if post_id in self.card_map:
                try:
                    self.card_map[post_id].reset_state()
                except:
                    pass

            del self.active_downloads[post_id]

    def finalize_install(self, post_id, temp_path, thumb_path):
        if post_id not in self.active_downloads:
            return

        post_data = self.active_downloads[post_id]["post_data"]
        del self.active_downloads[post_id]

        # Call original finish logic
        self.finish_install_logic(post_data, temp_path, thumb_path)

    def update_progress(self, post_id, value):
        if post_id in self.card_map:
            # Only update if widget is currently visible/exist in map
            try:
                self.card_map[post_id].set_progress(value)
            except RuntimeError:
                pass

    def finish_install_logic(self, post_data, temp_path, thumb_path):
        slug = post_data.get("slug", "unknown")
        ptype = post_data.get("type")
        post_id = post_data.get("id")

        success = False
        msg = ""

        # Pass thumb_path if it exists and is not empty string
        t_path = thumb_path if thumb_path else None

        if ptype == "boot_video":
            success, msg = FileManager.install_boot_video(
                temp_path, slug, post_data, t_path
            )
        else:
            success, msg = FileManager.install_suspend_video(
                temp_path, post_data, t_path
            )

        if os.path.exists(temp_path):
            os.remove(temp_path)

        # Cleanup temp thumb if it exists
        if t_path and os.path.exists(t_path):
            os.remove(t_path)

        if post_id in self.card_map:
            try:
                self.card_map[post_id].reset_state()
            except RuntimeError:
                pass

        if success:
            self.toast.show_message(msg)
        else:
            self.toast.show_message(msg, is_error=True)

    def render_library(self):
        self.clear_layout(self.library_layout)

        files = FileManager.get_installed_files()

        if not files:
            lbl = QLabel("No videos installed yet.")
            lbl.setStyleSheet("color: #94a3b8; font-size: 16px; padding: 20px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.library_layout.addWidget(lbl)
            return

        for f in files:
            item = LibraryItem(f)
            item.delete_clicked.connect(self.on_delete_file)
            self.library_layout.addWidget(item)

    def on_delete_file(self, filename):
        success, msg = FileManager.delete_file(filename)
        if success:
            self.toast.show_message(msg)
            self.render_library()  # Refresh list
        else:
            self.toast.show_message(msg, is_error=True)
