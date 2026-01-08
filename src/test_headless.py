import sys
import os

# Set platform to offscreen to avoid display errors
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from src.gui.window import MainWindow
from src.api import RepoAPI


def test_app():
    print("Initializing QApplication (Offscreen)...")
    app = QApplication(sys.argv)

    print("Testing API logic separately first...")
    api = RepoAPI()
    posts = api.get_all_posts()
    print(f"API fetched {len(posts)} posts.")

    if len(posts) > 0:
        print(f"Sample Post: {posts[0]['title']}")

    print("Initializing MainWindow...")
    window = MainWindow()

    # Manually inject data to test rendering logic synchronously
    print("Injecting data into MainWindow...")
    window.on_data_loaded(posts)

    # Check if data was filtered
    boot_count = len(window.filtered_posts_boot)
    suspend_count = len(window.filtered_posts_suspend)

    # Check if widgets were created (Grid Layout items)
    # Note: Layout count includes items, but we paginate.
    # Current page size is 12, so we expect at most 12 items in the layout.
    layout_items = window.boot_layout.count()

    print(f"GUI Data: {boot_count} boot posts, {suspend_count} suspend posts.")
    print(f"GUI Layout Items (Page 1): {layout_items}")

    if boot_count + suspend_count > 0 and layout_items > 0:
        print("SUCCESS: App initialized and populated data.")
    else:
        print(
            "WARNING: App initialized but no data found (maybe API failed or cache empty)."
        )


if __name__ == "__main__":
    test_app()
