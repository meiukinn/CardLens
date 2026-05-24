"""
main.py

This file starts the CardLens program.
It controls the main menu, command line modes, profile recognition, profile
creation, and profile deletion.
"""

import argparse
import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import config
import window_utils
from card_creator import CardLensCreator
from card_recognition import CardRecognizer
from profile_loader import ProfileLoader
from ui_display import ProfileDisplay


def parse_args():
    """Read optional command line arguments for non menu use."""
    parser = argparse.ArgumentParser(description="CardLens dynamic profile display")
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--image", type=Path, default=None)
    input_group.add_argument("--webcam", action="store_true")
    input_group.add_argument("--create", action="store_true")
    input_group.add_argument("--delete", action="store_true")
    return parser.parse_args()


def _has_cli_input(args):
    """Check whether the user already selected an action from the command line."""
    if args.image:
        return True
    if args.webcam:
        return True
    if args.create:
        return True
    if args.delete:
        return True
    return False


def _make_args(image=None, webcam=False, create=False, delete=False):
    """Create an argument object that matches argparse results."""
    return argparse.Namespace(
        image=image,
        webcam=webcam,
        create=create,
        delete=delete,
    )


def _choose_input_interactively():
    """Show the first menu and return the action chosen by the user."""
    selection = {"args": None}

    # This small menu is used when the user runs python main.py.
    chooser = tk.Tk()
    chooser.title("CardLens")
    window_utils.center_window(chooser, 460, 520)
    chooser.resizable(False, False)
    chooser.configure(bg=config.BG_GRADIENT_TOP)
    chooser.attributes("-topmost", True)

    def stop_topmost():
        """Stop forcing the chooser window above other windows."""
        chooser.attributes("-topmost", False)

    chooser.after(600, stop_topmost)

    tk.Label(
        chooser,
        text="CardLens",
        font=(config.FONT_FAMILY, 23, "bold"),
        fg=config.TEXT_PRIMARY,
        bg=config.BG_GRADIENT_TOP,
    ).pack(pady=(22, 4))
    tk.Label(
        chooser,
        text="Choose how to recognize, create, or manage a profile",
        font=(config.FONT_FAMILY, 10),
        fg=config.TEXT_SECONDARY,
        bg=config.BG_GRADIENT_TOP,
        wraplength=340,
        justify="center",
    ).pack(pady=(0, 14))

    button_frame = tk.Frame(chooser, bg=config.BG_GRADIENT_TOP)
    button_frame.pack(fill="x", padx=72)

    def finish(args):
        """Save the selected action and close the menu window."""
        selection["args"] = args
        chooser.destroy()

    def choose_file():
        """Let the user choose a card image from the local computer."""
        path = filedialog.askopenfilename(
            parent=chooser,
            initialdir=config.DEMO_CARDS_DIR,
            title="Choose a CardLens card image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg"),
                ("All files", "*.*"),
            ],
        )
        if path:
            finish(_make_args(image=Path(path)))

    def use_webcam():
        """Start QR recognition from the webcam."""
        finish(_make_args(webcam=True))

    def create_cardlens():
        """Open the local profile creator."""
        finish(_make_args(create=True))

    def delete_card():
        """Open the local profile deletion screen."""
        finish(_make_args(delete=True))

    button_style = {
        # The same style is reused so the menu buttons look consistent.
        "font": (config.FONT_FAMILY, 11, "bold"),
        "width": 26,
        "height": 1,
        "bd": 0,
        "padx": 12,
        "pady": 10,
        "cursor": "hand2",
    }

    tk.Button(
        button_frame,
        text="Choose Image File",
        command=choose_file,
        bg=config.ACCENT_BLUE,
        fg="#FFFFFF",
        activebackground=config.ACCENT_BLUE_HOVER,
        activeforeground="#FFFFFF",
        **button_style,
    ).pack(fill="x", pady=5)
    tk.Button(
        button_frame,
        text="Use Webcam",
        command=use_webcam,
        bg="#FFFFFF",
        fg=config.ACCENT_BLUE,
        activebackground=config.ACCENT_BLUE_LIGHT,
        activeforeground=config.ACCENT_BLUE,
        **button_style,
    ).pack(fill="x", pady=5)
    tk.Button(
        button_frame,
        text="Create My CardLens",
        command=create_cardlens,
        bg="#FFFFFF",
        fg=config.ACCENT_BLUE,
        activebackground=config.ACCENT_BLUE_LIGHT,
        activeforeground=config.ACCENT_BLUE,
        **button_style,
    ).pack(fill="x", pady=5)
    tk.Button(
        button_frame,
        text="Delete Card",
        command=delete_card,
        bg="#FFFFFF",
        fg="#B42318",
        activebackground="#FEE4E2",
        activeforeground="#B42318",
        **button_style,
    ).pack(fill="x", pady=5)

    tk.Label(
        chooser,
        text="Webcam mode opens an OpenCV preview window.",
        font=(config.FONT_FAMILY, 9),
        fg=config.TEXT_TERTIARY,
        bg=config.BG_GRADIENT_TOP,
    ).pack(pady=(12, 0))

    chooser.protocol("WM_DELETE_WINDOW", chooser.destroy)
    chooser.mainloop()
    return selection["args"]


def _resolve_input_image(path):
    """Convert a relative image path into a project based absolute path."""
    if path.is_absolute():
        return path
    return config.BASE_DIR / path


def _recognize_card(args, recognizer):
    """Recognize a card ID from either webcam mode or image mode."""
    if args.webcam:
        # Webcam mode returns after success, cancellation, timeout, or error.
        print("Starting webcam. Hold a registered card up to the camera.")
        return recognizer.recognize_from_webcam()

    if args.image:
        image_path = _resolve_input_image(args.image)
    else:
        messagebox.showerror("CardLens", "No image selected.")
        return None

    if not image_path.exists():
        message = f"Card image not found:\n{image_path}"
        print(f"[Error] {message}")
        messagebox.showerror("CardLens", message)
        return None

    print(f"Recognizing card from image: {image_path}")
    return recognizer.recognize_from_image(image_path)


def _open_profile_ui(profile):
    """Open the profile display window for one loaded profile."""
    root = tk.Tk()
    app = ProfileDisplay(root)
    app.show_profile(profile)
    root.mainloop()
    return app.back_to_menu_requested


def _create_profile_flow():
    """Create a new profile and open it after successful creation."""
    creator = CardLensCreator()
    profile_id = creator.show()
    if profile_id is None:
        print("Profile creation cancelled.")
        return "menu"

    try:
        loader = ProfileLoader()
    except (FileNotFoundError, ValueError) as exc:
        print(f"[Fatal] {exc}")
        messagebox.showerror("CardLens", str(exc))
        return "menu"

    profile = loader.get_profile(profile_id)
    if profile is None:
        message = f"Created profile '{profile_id}' could not be loaded."
        print(f"[Fatal] {message}")
        messagebox.showerror("CardLens", message)
        return "menu"

    back_to_menu = _open_profile_ui(profile)
    if back_to_menu:
        return "menu"
    return "exit"


def _recognize_profile_flow(args):
    """Recognize a card, load its profile, and open the profile UI."""
    try:
        loader = ProfileLoader()
    except (FileNotFoundError, ValueError) as exc:
        print(f"[Fatal] {exc}")
        messagebox.showerror("CardLens", str(exc))
        return "menu"

    recognizer = CardRecognizer()
    card_id = _recognize_card(args, recognizer)
    if card_id is None:
        # Cancelled webcam scanning should return to the menu without an error popup.
        if args.webcam and recognizer.last_status == "cancelled":
            print("Webcam scan cancelled.")
            return "menu"

        print("No CardLens QR code recognized.")
        messagebox.showerror("CardLens", "No CardLens QR code recognized.")
        return "menu"

    print(f"Recognized card: {card_id}")
    profile = loader.get_profile(card_id)
    if profile is None:
        print(f"No profile registered for card '{card_id}'.")
        messagebox.showerror("CardLens", f"No profile registered for card '{card_id}'.")
        return "menu"

    back_to_menu = _open_profile_ui(profile)
    if back_to_menu:
        return "menu"
    return "exit"


def _load_profiles_data():
    """Load raw profile data for the delete screen."""
    if not config.PROFILES_JSON.exists():
        return {}

    try:
        text = config.PROFILES_JSON.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"[Error] Could not read profiles.json: {exc}")
        messagebox.showerror("CardLens", "Could not read profiles.json.")
        return {}

    if not text.strip():
        return {}

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        messagebox.showerror("CardLens", "profiles.json is not valid JSON.")
        return {}

    if isinstance(data, dict):
        return data

    messagebox.showerror("CardLens", "profiles.json must contain a dictionary of profiles.")
    return {}


def _save_profiles_data(profiles):
    """Save raw profile data after a profile is deleted."""
    try:
        config.PROFILES_JSON.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(profiles, indent=2, ensure_ascii=False)
        config.PROFILES_JSON.write_text(text, encoding="utf-8")
    except OSError as exc:
        print(f"[Error] Could not save profiles.json: {exc}")
        messagebox.showerror("CardLens", "Could not save profiles.json.")
        return False

    return True


def _profile_display_name(profile):
    """Build a readable profile name for menus and messages."""
    first_name = profile.get("first_name", "")
    last_name = profile.get("last_name", "")
    name = f"{first_name} {last_name}".strip()
    if name:
        return name

    preferred_name = profile.get("preferred_name", "")
    if preferred_name:
        return preferred_name

    return "Unnamed Profile"


def _delete_file(path):
    """Delete one file if it exists."""
    if not path.exists():
        return

    try:
        path.unlink()
    except OSError as exc:
        print(f"[Delete] Could not delete {path}: {exc}")


def _delete_profile_files(profile_id):
    """Delete generated files that belong to one local profile."""
    _delete_file(config.QR_CODES_DIR / f"{profile_id}.png")
    _delete_file(config.DEMO_CARDS_DIR / f"{profile_id}_qr_front.png")

    for path in config.AVATARS_DIR.glob(f"{profile_id}_avatar.*"):
        _delete_file(path)

    for path in config.HIGHLIGHTS_DIR.glob(f"{profile_id}_highlight.*"):
        _delete_file(path)

    for path in config.ABOUT_VISUALS_DIR.glob(f"{profile_id}_about_visual.*"):
        _delete_file(path)


def _delete_guestbook_notes(profile_id, profile_name):
    """Remove guestbook notes that belong to the deleted profile."""
    if not config.GUESTBOOK_JSON.exists():
        return True

    try:
        text = config.GUESTBOOK_JSON.read_text(encoding="utf-8")
        data = json.loads(text)
    except OSError as exc:
        print(f"[Delete] Could not read guestbook.json: {exc}")
        messagebox.showerror("CardLens", "Could not read guestbook.json.")
        return False
    except json.JSONDecodeError:
        return True

    if not isinstance(data, list):
        return True

    kept_notes = []
    for note in data:
        if not isinstance(note, dict):
            continue

        # New notes use profile_id. Old notes can still be matched by profile name.
        note_profile_id = str(note.get("profile_id", "")).strip()
        note_profile_name = str(note.get("profile", "")).strip()

        delete_this_note = False
        if note_profile_id == profile_id:
            delete_this_note = True
        elif not note_profile_id and note_profile_name == profile_name:
            delete_this_note = True

        if not delete_this_note:
            kept_notes.append(note)

    try:
        text = json.dumps(kept_notes, indent=2, ensure_ascii=False)
        config.GUESTBOOK_JSON.write_text(text, encoding="utf-8")
    except OSError as exc:
        print(f"[Delete] Could not save guestbook.json: {exc}")
        messagebox.showerror("CardLens", "Could not save guestbook.json.")
        return False

    return True


def _delete_profile_by_id(profile_id):
    """Delete one profile from JSON and remove its generated local files."""
    profiles = _load_profiles_data()
    if profile_id not in profiles:
        messagebox.showerror("CardLens", f"Profile '{profile_id}' was not found.")
        return False

    profile = profiles[profile_id]
    profile_name = _profile_display_name(profile)
    del profiles[profile_id]
    saved_profiles = _save_profiles_data(profiles)
    if not saved_profiles:
        return False

    _delete_profile_files(profile_id)
    cleaned_notes = _delete_guestbook_notes(profile_id, profile_name)
    if not cleaned_notes:
        messagebox.showwarning(
            "CardLens",
            "The profile was deleted, but guestbook cleanup failed.",
        )

    return True


def _delete_card_flow():
    """Show a small window for selecting and deleting a local profile."""
    profiles = _load_profiles_data()
    if not profiles:
        messagebox.showinfo("CardLens", "No saved cards to delete.")
        return "menu"

    card_ids = []
    for card_id in profiles.keys():
        card_ids.append(card_id)
    card_ids.sort()

    window = tk.Tk()
    window.title("Delete Card")
    window_utils.center_window(window, 460, 500)
    window.resizable(False, False)
    window.configure(bg=config.BG_GRADIENT_TOP)

    tk.Label(
        window,
        text="Delete Card",
        font=(config.FONT_FAMILY, 21, "bold"),
        fg=config.TEXT_PRIMARY,
        bg=config.BG_GRADIENT_TOP,
    ).pack(pady=(22, 4))
    tk.Label(
        window,
        text="Select a CardLens profile to remove from this computer.",
        font=(config.FONT_FAMILY, 10),
        fg=config.TEXT_SECONDARY,
        bg=config.BG_GRADIENT_TOP,
        wraplength=360,
        justify="center",
    ).pack(pady=(0, 14))

    listbox = tk.Listbox(
        window,
        height=8,
        font=(config.FONT_FAMILY, 11),
        bd=0,
        highlightthickness=1,
        highlightbackground=config.CARD_BORDER,
        selectbackground=config.ACCENT_BLUE,
        selectforeground="#FFFFFF",
    )
    listbox.pack(fill="x", padx=42)

    for card_id in card_ids:
        profile = profiles[card_id]
        label = f"{card_id} - {_profile_display_name(profile)}"
        listbox.insert(tk.END, label)

    button_row = tk.Frame(window, bg=config.BG_GRADIENT_TOP)
    button_row.pack(fill="x", padx=42, pady=18)

    def cancel():
        """Close the delete window without deleting anything."""
        window.destroy()

    def delete_selected():
        """Delete the selected profile after user confirmation."""
        selected = listbox.curselection()
        if not selected:
            messagebox.showerror("CardLens", "Select a card first.")
            return

        index = selected[0]
        profile_id = card_ids[index]
        profile_name = _profile_display_name(profiles[profile_id])
        confirmed = messagebox.askyesno(
            "CardLens",
            f"Delete {profile_id} - {profile_name}?\nThis removes its QR code and local files.",
            parent=window,
        )
        if not confirmed:
            return

        deleted = _delete_profile_by_id(profile_id)
        if deleted:
            messagebox.showinfo("CardLens", f"Deleted {profile_id}.", parent=window)
            window.destroy()

    def double_click_delete(_event):
        """Allow double click as a shortcut for the delete button."""
        delete_selected()

    listbox.bind("<Double-Button-1>", double_click_delete)

    tk.Button(
        button_row,
        text="Cancel",
        command=cancel,
        font=(config.FONT_FAMILY, 10, "bold"),
        bg="#FFFFFF",
        fg=config.ACCENT_BLUE,
        bd=0,
        padx=16,
        pady=9,
        cursor="hand2",
    ).pack(side="left", fill="x", expand=True, padx=(0, 8))
    tk.Button(
        button_row,
        text="Delete",
        command=delete_selected,
        font=(config.FONT_FAMILY, 10, "bold"),
        bg="#B42318",
        fg="#FFFFFF",
        activebackground="#912018",
        activeforeground="#FFFFFF",
        bd=0,
        padx=16,
        pady=9,
        cursor="hand2",
    ).pack(side="left", fill="x", expand=True, padx=(8, 0))

    window.mainloop()
    return "menu"


def _run_action(args):
    """Run one selected action and return whether the menu should reopen."""
    if args.delete:
        return _delete_card_flow()
    if args.create:
        return _create_profile_flow()
    return _recognize_profile_flow(args)


def main():
    """Program entry point."""
    args = parse_args()
    if _has_cli_input(args):
        # Command line mode runs once. The menu is only used when no CLI action is given.
        result = _run_action(args)
        if result == "exit":
            return 0

    while True:
        # The menu reopens after actions that return "menu".
        selected_args = _choose_input_interactively()
        if selected_args is None:
            print("No input selected.")
            return 0

        result = _run_action(selected_args)
        if result == "exit":
            return 0


if __name__ == "__main__":
    sys.exit(main())
