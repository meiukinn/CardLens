"""
run_check.py

This file runs a small pre-submission check for CardLens.
It checks local files, demo QR recognition, and basic profile rendering.
It does not test the webcam because webcam behavior depends on the computer.
"""

import tkinter as tk

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


def check_default_qr():
    """Check that the included demo card image can be recognized."""
    recognizer = CardRecognizer()
    result = recognizer.recognize_from_image(config.DEFAULT_DEMO_IMAGE)
    if not result:
        raise ValueError("Default demo image could not be recognized.")

    print("[OK] Default QR recognized:", result)
    return result


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
    check_file(config.DEFAULT_DEMO_IMAGE, "default demo image")
    check_file(config.ASSETS_DIR / "azure_ttk_theme" / "LICENSE", "Azure ttk license")

    loader = check_profiles()
    card_id = check_default_qr()

    profile = loader.get_profile(card_id)
    if profile is None:
        raise ValueError("Recognized card has no matching profile.")

    check_profile_window(profile)
    print("[OK] CardLens pre-submission check completed.")


if __name__ == "__main__":
    main()
