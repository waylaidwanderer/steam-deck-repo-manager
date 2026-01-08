import os
import shutil
import json
from pathlib import Path
from src.config import Config


class FileManager:
    @staticmethod
    def ensure_directories():
        """Creates the install directory if it doesn't exist."""
        path = Config.get_install_path()
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                # Create hidden metadata directory
                (path / ".manager").mkdir(exist_ok=True)
                print(f"Created directory: {path}")
            except OSError as e:
                print(f"Error creating directory: {e}")

        # Ensure metadata dir exists even if parent existed
        (path / ".manager").mkdir(exist_ok=True)
        return path

    @staticmethod
    def _save_metadata(slug, post_data, local_thumb_path=None):
        """Saves metadata and moves local thumbnail to .manager directory."""
        try:
            meta_dir = Config.get_install_path() / ".manager"

            # Save JSON
            with open(meta_dir / f"{slug}.json", "w") as f:
                json.dump(post_data, f)

            # Move Thumbnail if provided
            if local_thumb_path and os.path.exists(local_thumb_path):
                dest_thumb = meta_dir / f"{slug}.jpg"
                if dest_thumb.exists():
                    dest_thumb.unlink()
                shutil.move(local_thumb_path, dest_thumb)

        except Exception as e:
            print(f"Metadata save failed: {e}")

    @staticmethod
    def install_boot_video(source_path, slug, post_data=None, thumb_path=None):
        """
        Installs a boot video to {install_path}/{slug}.webm.
        """
        target_dir = FileManager.ensure_directories()
        dest_filename = f"{slug}.webm"
        dest_path = target_dir / dest_filename

        try:
            shutil.copy2(source_path, dest_path)
            if post_data:
                FileManager._save_metadata(slug, post_data, thumb_path)

            print(f"Installed boot video to: {dest_path}")
            return True, f"Installed to {dest_path}"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def install_suspend_video(source_path, post_data=None, thumb_path=None):
        """
        Installs a suspend video to {install_path}/deck-suspend-animation.webm.
        Backs up existing file if present.
        """
        target_dir = FileManager.ensure_directories()
        target_name = "deck-suspend-animation.webm"
        dest_path = target_dir / target_name

        if dest_path.exists():
            backup_path = dest_path.with_suffix(".webm.bak")
            try:
                shutil.move(str(dest_path), str(backup_path))
                print(f"Backed up existing suspend video to {backup_path}")
            except Exception as e:
                print(f"Backup failed: {e}")

        try:
            shutil.copy2(source_path, dest_path)
            if post_data:
                # Use fixed slug 'suspend' for the active suspend video metadata
                FileManager._save_metadata("suspend", post_data, thumb_path)

            print(f"Installed suspend video to: {dest_path}")
            return True, f"Installed to {dest_path} (backup created)"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_installed_files():
        """
        Returns a list of installed .webm files in the overrides directory.
        Returns a list of dicts: {'filename': str, 'path': Path, 'type': 'boot'|'suspend', 'meta': dict}
        """
        path = Config.get_install_path()
        meta_dir = path / ".manager"

        if not path.exists():
            return []

        files = []
        try:
            for item in path.glob("*.webm"):
                if item.name == "deck-suspend-animation.webm":
                    vtype = "suspend"
                    slug = "suspend"
                else:
                    vtype = "boot"
                    slug = item.stem  # filename without extension

                # Try to load metadata
                meta = {}
                meta_file = meta_dir / f"{slug}.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, "r") as f:
                            meta = json.load(f)
                        # Add local thumbnail path if exists
                        thumb_path = meta_dir / f"{slug}.jpg"
                        if thumb_path.exists():
                            meta["local_thumbnail"] = str(thumb_path)
                    except:
                        pass

                files.append(
                    {
                        "filename": item.name,
                        "path": item,
                        "type": vtype,
                        "size_mb": round(item.stat().st_size / (1024 * 1024), 2),
                        "meta": meta,
                    }
                )
        except Exception as e:
            print(f"Error listing files: {e}")

        return sorted(files, key=lambda x: x["filename"])

    @staticmethod
    def delete_file(filename):
        """Deletes a file and its metadata from the install directory."""
        path = Config.get_install_path()
        file_path = path / filename
        meta_dir = path / ".manager"

        try:
            if file_path.exists():
                file_path.unlink()

                # Determine slug for metadata deletion
                if filename == "deck-suspend-animation.webm":
                    slug = "suspend"
                else:
                    slug = Path(filename).stem

                # Delete metadata files
                for ext in [".json", ".jpg"]:
                    meta_file = meta_dir / f"{slug}{ext}"
                    if meta_file.exists():
                        try:
                            meta_file.unlink()
                        except:
                            pass

                print(f"Deleted {path}")
                return True, f"Deleted {filename}"
            else:
                return False, "File not found"
        except Exception as e:
            return False, str(e)
