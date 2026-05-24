"""
config.py

This file stores shared settings for the CardLens project.
Keeping these values in one file makes the rest of the program easier to edit.
"""

from pathlib import Path


# Project paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"

PROFILES_JSON = DATA_DIR / "profiles.json"
GUESTBOOK_JSON = DATA_DIR / "guestbook.json"

DEMO_CARDS_DIR = ASSETS_DIR / "demo_cards"
DEFAULT_DEMO_IMAGE = DEMO_CARDS_DIR / "card_001_qr_front.png"
QR_CODES_DIR = ASSETS_DIR / "qr_codes"
AVATARS_DIR = ASSETS_DIR / "avatars"
HIGHLIGHTS_DIR = ASSETS_DIR / "highlights"
ICONS_DIR = ASSETS_DIR / "icons"
ABOUT_VISUALS_DIR = ASSETS_DIR / "about_visuals"


# Window title
WINDOW_TITLE = "CardLens"


# Shared UI colors
BG_GRADIENT_TOP = "#F8FBFF"
CARD_BORDER = "#E5E7EB"

TEXT_PRIMARY = "#111827"
TEXT_SECONDARY = "#6B7280"
TEXT_TERTIARY = "#9CA3AF"

ACCENT_BLUE = "#007AFF"
ACCENT_BLUE_HOVER = "#0051D5"
ACCENT_BLUE_LIGHT = "#EAF3FF"


# Shared font family
FONT_FAMILY = "Segoe UI"


# Webcam settings
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
WEBCAM_PREVIEW_WAIT_MS = 10
WEBCAM_SCAN_EVERY_FRAMES = 3


# QR recognition settings
SUPPORTED_IMAGE_FORMATS = [".png", ".jpg", ".jpeg"]
QR_PREFIX = "CARDLENS:"
QR_DETECTION_SCALES = [1.0, 1.5, 2.0, 3.0]
WEBCAM_DETECTION_PAUSE_MS = 800
WEBCAM_TIMEOUT_SECONDS = 60


if __name__ == "__main__":
    # This block helps check paths when running config.py directly.
    print("=== CardLens Config ===")
    print(f"BASE_DIR:             {BASE_DIR}")
    print(f"PROFILES_JSON exists: {PROFILES_JSON.exists()}")
    print(f"DEMO_CARDS exists:    {DEMO_CARDS_DIR.exists()}")
    print(f"QR_CODES exists:      {QR_CODES_DIR.exists()}")
    print(f"AVATARS exists:       {AVATARS_DIR.exists()}")
    print(f"HIGHLIGHTS exists:    {HIGHLIGHTS_DIR.exists()}")
    print(f"ICONS exists:         {ICONS_DIR.exists()}")
    print(f"ABOUT_VISUALS exists: {ABOUT_VISUALS_DIR.exists()}")
