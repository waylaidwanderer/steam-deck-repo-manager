import sys
import os
from src.api import RepoAPI
from src.file_manager import FileManager
from src.config import Config
from pathlib import Path
import shutil


def test_core():
    print("--- Testing API ---")
    api = RepoAPI()
    try:
        posts = api.get_all_posts()
        print(f"SUCCESS: Fetched {len(posts)} posts.")
        if len(posts) > 0:
            print(f"Sample: {posts[0]['title']} (Type: {posts[0].get('type')})")

            # Test Download URL generation
            sample_id = posts[0].get("id")
            print(f"Sample ID from API: {sample_id}")

            # Specific test for user provided ID
            test_id = "ENb0E"
            print(f"Testing download URL resolution for ID {test_id}...")

            url = api.get_download_url(test_id)
            if url:
                print(f"SUCCESS: Resolved URL for {test_id}: {url}")
            else:
                print(f"FAILURE: Could not resolve URL for {test_id}")
    except Exception as e:
        print(f"FAILED API Test: {e}")

    print("\n--- Testing FileManager ---")

    # Mock Config path
    test_dir = Path("./test_steam_root")
    test_movies_dir = test_dir / "config" / "uioverrides" / "movies"

    # Backup original method
    original_get_path = Config.get_install_path

    # Monkeypatch
    Config.get_install_path = lambda: test_movies_dir

    print(f"Test Install Path: {test_movies_dir}")

    # Create dummy file
    dummy_src = Path("dummy_video.webm")
    dummy_src.write_text("fake video content")

    try:
        # Test Boot Video Install
        success, msg = FileManager.install_boot_video(dummy_src, "test-boot-slug")
        print(f"Boot Install: {'SUCCESS' if success else 'FAIL'} - {msg}")

        expected_boot = test_movies_dir / "test-boot-slug.webm"
        if expected_boot.exists():
            print("Verified: Boot video file exists.")
        else:
            print("Error: Boot video file missing.")

        # Test Suspend Video Install
        success, msg = FileManager.install_suspend_video(dummy_src)
        print(f"Suspend Install 1: {'SUCCESS' if success else 'FAIL'} - {msg}")

        expected_suspend = test_movies_dir / "deck-suspend-animation.webm"
        if expected_suspend.exists():
            print("Verified: Suspend video file exists.")

        # Test Backup Logic (Install again)
        success, msg = FileManager.install_suspend_video(dummy_src)
        print(f"Suspend Install 2 (Backup): {'SUCCESS' if success else 'FAIL'} - {msg}")

        expected_backup = test_movies_dir / "deck-suspend-animation.webm.bak"
        if expected_backup.exists():
            print("Verified: Backup file exists.")
        else:
            print("Error: Backup file missing.")

    except Exception as e:
        print(f"FAILED FileManager Test: {e}")
    finally:
        # Cleanup
        if dummy_src.exists():
            dummy_src.unlink()

        if test_dir.exists():
            shutil.rmtree(test_dir)

        # Restore original method
        Config.get_install_path = original_get_path


if __name__ == "__main__":
    test_core()
