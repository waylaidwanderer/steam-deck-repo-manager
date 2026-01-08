import json
import os
import platform
from pathlib import Path


class Config:
    CONFIG_DIR = Path.home() / ".config" / "steam-deck-repo-manager"
    CONFIG_FILE = CONFIG_DIR / "config.json"

    DEFAULT_CONFIG = {"install_path": ""}

    @staticmethod
    def _get_default_install_path():
        # Check for env var override
        env_path = os.environ.get("SDRM_INSTALL_PATH")
        if env_path:
            return str(Path(env_path).resolve())

        # Check for actual Steam Deck
        deck_path = Path("/home/deck/.steam/root/config/uioverrides/movies")
        if (
            platform.system() == "Linux" and deck_path.parent.parent.exists()
        ):  # Check up to config/uioverrides/
            return str(deck_path)

        # Fallback for Windows/Testing (Documents folder)
        # This makes it easy for the user to find the downloaded files on Windows
        docs_path = Path.home() / "Documents" / "SteamDeckRepoManager" / "movies"
        return str(docs_path)

    @classmethod
    def load(cls):
        if not cls.CONFIG_FILE.exists():
            return cls.save(cls.DEFAULT_CONFIG)

        try:
            with open(cls.CONFIG_FILE, "r") as f:
                config = json.load(f)

            # If path is missing, fill it with default
            if not config.get("install_path"):
                config["install_path"] = cls._get_default_install_path()
                cls.save(config)

            return config
        except Exception as e:
            print(f"Error loading config: {e}. Using defaults.")
            default = cls.DEFAULT_CONFIG.copy()
            default["install_path"] = cls._get_default_install_path()
            return default

    @classmethod
    def save(cls, config):
        if not cls.CONFIG_DIR.exists():
            cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # Ensure path is set before saving
        if not config.get("install_path"):
            config["install_path"] = cls._get_default_install_path()

        with open(cls.CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        return config

    @classmethod
    def get_install_path(cls):
        config = cls.load()
        path_str = config.get("install_path")
        if not path_str:
            # Should not happen if load() works correctly, but safe fallback
            return Path(cls._get_default_install_path())
        return Path(path_str)
