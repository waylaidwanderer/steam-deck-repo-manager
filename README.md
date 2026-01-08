# Steam Deck Repo Manager

A standalone GUI application for browsing, previewing, and installing boot videos and suspend animations from [SteamDeckRepo.com](https://steamdeckrepo.com).

## Features

*   **Native UI:** Designed for the Steam Deck's 1280x800 resolution with touch-friendly controls.
*   **Video Previews:** Instantly preview boot and suspend videos before installing.
*   **One-Click Install:** Automatically downloads and places files in the correct SteamOS directories (`~/.steam/root/config/uioverrides/movies/`).
*   **Search & Filter:** Quickly find specific videos or filter by category (Boot vs. Suspend).

## Requirements

*   **Steam Deck** (SteamOS) or Linux Desktop
*   Python 3.11+
*   `uv` (Recommended) or `pip`

## Running on Steam Deck (Desktop Mode)

The easiest way to run the manager right now is using `uv`, a fast Python package manager.

### 1. Install `uv`
Open **Konsole** and run:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone the Repository
```bash
git clone https://github.com/YourUsername/steam-deck-repo-manager.git
cd steam-deck-repo-manager
```

### 3. Run the App
```bash
uv run python -m src.main
```

`uv` will automatically set up the environment and install all necessary dependencies (PySide6, httpx, etc.) on the first run.

## Installation (Flatpak)

*Coming Soon!* We are working on a Flatpak release to make installation even easier via the Discover store.

## Development

If you want to contribute or modify the app:

1.  **Project Structure:**
    *   `src/main.py`: Entry point.
    *   `src/gui/`: UI components (Window, Widgets, Details View).
    *   `src/api.py`: API client for SteamDeckRepo.
    *   `src/file_manager.py`: Logic for installing video files.

2.  **Setup Git Hooks (Important):**
    This project uses Conventional Commits. Run this command to enforce message formatting:
    ```bash
    git config core.hooksPath scripts/git-hooks
    ```

3.  **Run Tests:**
    ```bash
    uv run src/test_headless.py
    ```

## License

MIT License