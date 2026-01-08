import json
import urllib.request
import urllib.error
from pathlib import Path


class RepoAPI:
    BASE_URL = "https://steamdeckrepo.com"
    API_URL = f"{BASE_URL}/api"
    CACHE_DIR = Path.home() / ".cache" / "steam-deck-repo-manager"
    CACHE_FILE = CACHE_DIR / "posts.json"
    HEADERS = {"User-Agent": "SteamDeckRepoManager/1.0 (Linux; SteamOS) python-urllib"}

    def __init__(self):
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        if not self.CACHE_DIR.exists():
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _make_request(self, url):
        req = urllib.request.Request(url, headers=self.HEADERS)
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read()

    def get_all_posts(self, force_refresh=False):
        """
        Fetch all posts from the API or local cache.
        """
        data = None
        network_error = None

        # 1. Try Network (if forced or cache missing)
        if force_refresh or not self.CACHE_FILE.exists():
            try:
                json_bytes = self._make_request(f"{self.API_URL}/posts/all")
                data = json.loads(json_bytes)

                # Save to cache
                with open(self.CACHE_FILE, "w") as f:
                    json.dump(data, f)

            except Exception as e:
                network_error = e

        # 2. Try Cache (if we don't have data yet)
        if data is None and self.CACHE_FILE.exists():
            try:
                with open(self.CACHE_FILE, "r") as f:
                    data = json.load(f)
            except Exception:
                # If cache is corrupt, ignore it
                pass

        # 3. Final decision
        if data is not None:
            return data.get("posts", [])

        # If we are here: No data from network, no data from cache.
        if network_error:
            raise network_error

        return []

    def get_download_url(self, post_id):
        """
        Returns the direct download URL by following the redirect.
        """
        url = f"{self.BASE_URL}/post/download/{post_id}"
        try:
            req = urllib.request.Request(url, headers=self.HEADERS, method="HEAD")
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.geturl()
        except Exception:
            # Fallback to GET if HEAD fails
            try:
                req = urllib.request.Request(url, headers=self.HEADERS)
                with urllib.request.urlopen(req, timeout=30) as response:
                    return response.geturl()
            except Exception:
                return None
