"""
run_check.py

This file runs a small pre-submission check for CardLens.
It checks local files, demo QR recognition, and basic profile rendering.
It does not test the webcam because webcam behavior depends on the computer.
"""

import tkinter as tk
from pathlib import Path

import config
from card_recognition import CardRecognizer
from profile_loader import ProfileLoader
from ui_display import ProfileDisplay


def check_file(path, label):
    """Check whether a required file exists."""
    if path.exists():
        print("[OK]", label, path)
        return True

    print("[Missing]", label, path)
    return False


def check_profiles():
    """Load profile data and make sure at least one profile exists."""
    loader = ProfileLoader()
    card_ids = loader.all_card_ids()
    if not card_ids:
        raise ValueError("No profiles were found.")

    print("[OK] Loaded profiles:", ", ".join(card_ids))
    return loader


def check_recognition_image(loader):
    """Check that included QR images can be recognized."""
    recognizer = CardRecognizer()
    mismatches = []

    for card_id in loader.all_card_ids():
        qr_path = config.QR_CODES_DIR / f"{card_id}.png"
        if not qr_path.exists():
            continue

        result = recognizer.recognize_from_image(qr_path)
        if result != card_id:
            mismatches.append(f"{qr_path} recognized as {result}")

    if mismatches:
        for item in mismatches:
            print("[Mismatch]", item)
        raise ValueError("Some QR codes do not match their profile IDs.")

    print("[OK] All profile QR codes match their profile IDs.")

    recognized_id = ""

    for demo_path in sorted(config.DEMO_CARDS_DIR.glob("*_qr_front.png")):
        result = recognizer.recognize_from_image(demo_path)
        expected = demo_path.name.replace("_qr_front.png", "")
        if result != expected:
            raise ValueError(f"Demo image {demo_path.name} recognized as {result}.")
        print("[OK] Demo card image recognized:", demo_path.name, "=>", result)
        if not recognized_id:
            recognized_id = result

    if recognized_id:
        return recognized_id

    raise ValueError("No included QR or demo image could be recognized.")


def check_profile_assets(loader):
    """Check QR codes and image assets referenced by every saved profile."""
    missing = []

    for card_id in loader.all_card_ids():
        qr_path = config.QR_CODES_DIR / f"{card_id}.png"
        if not qr_path.exists():
            missing.append(f"missing QR code for {card_id}: {qr_path}")

        profile = loader.get_profile(card_id)
        if profile is None:
            continue

        for key in ["avatar", "highlight_image"]:
            _check_profile_asset(profile.get(key, ""), card_id, key, missing)

        for page in profile.get("pages", []):
            for key in ["image", "visual"]:
                _check_profile_asset(page.get(key, ""), card_id, key, missing)

    if missing:
        for item in missing:
            print("[Missing]", item)
        raise FileNotFoundError("Some profile assets are missing.")

    print("[OK] All profile QR codes and image assets exist.")


def _check_profile_asset(value, card_id, key, missing):
    """Add one missing asset message when a stored path does not exist."""
    if not value:
        return

    path = Path(value)
    if not path.is_absolute():
        path = config.BASE_DIR / path

    if not path.exists():
        missing.append(f"{card_id} {key}: {path}")


def check_profile_window(profile):
    """Open and render the profile window once."""
    root = tk.Tk()
    app = ProfileDisplay(root)
    app.show_profile(profile)
    root.update_idletasks()
    root.update()
    print("[OK] Profile window rendered:", app._full_name())
    root.destroy()


def main():
    """Run all pre-submission checks in order."""
    check_file(config.PROFILES_JSON, "profiles JSON")
    check_file(config.ASSETS_DIR / "azure_ttk_theme" / "LICENSE", "Azure ttk license")

    loader = check_profiles()
    check_profile_assets(loader)
    card_id = check_recognition_image(loader)

    profile = loader.get_profile(card_id)
    if profile is None:
        raise ValueError("Recognized card has no matching profile.")

    check_profile_window(profile)
    print("[OK] CardLens pre-submission check completed.")


if __name__ == "__main__":
    main()
