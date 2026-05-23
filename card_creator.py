"""
card_creator.py

This file creates a simple CardLens profile and QR code.
The user enters profile details, chooses optional images, and the program
saves the result into local project files.
"""

import json
import shutil
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import qrcode

import config
import window_utils


class CardLensCreator:
    """Small Tkinter form for creating a new CardLens profile."""

    def __init__(self):
        """Prepare creator state before the Tkinter window is opened."""
        self.window = None
        self.entries = {}
        self.bio_text = None
        self.avatar_path = None
        self.avatar_label = None
        self.highlight_path = None
        self.highlight_label = None
        self.created_profile_id = None
        self.form_row = 0
        self.form_canvas = None
        self.form_window_id = None

    def show(self):
        """Open the creator window and return the new profile ID."""
        self.window = tk.Tk()
        self.window.title("Create My CardLens")
        window_utils.center_window(self.window, 640, 680)
        self.window.resizable(False, True)
        self.window.configure(bg=config.BG_GRADIENT_TOP)
        self.window.protocol("WM_DELETE_WINDOW", self._close_window)

        self._build_form()
        self.window.mainloop()
        return self.created_profile_id

    def _build_form(self):
        """Build the scrollable profile creation form."""
        tk.Label(
            self.window,
            text="Create My CardLens",
            font=(config.FONT_FAMILY, 22, "bold"),
            fg=config.TEXT_PRIMARY,
            bg=config.BG_GRADIENT_TOP,
        ).pack(pady=(20, 4))

        tk.Label(
            self.window,
            text="Enter basic profile details. A QR code will be generated automatically.",
            font=(config.FONT_FAMILY, 10),
            fg=config.TEXT_SECONDARY,
            bg=config.BG_GRADIENT_TOP,
            wraplength=540,
            justify="center",
        ).pack(pady=(0, 14))

        # The form uses a canvas so small screens can scroll through all fields.
        scroll_area = tk.Frame(self.window, bg=config.BG_GRADIENT_TOP)
        scroll_area.pack(fill="both", expand=True, padx=48)

        canvas = tk.Canvas(
            scroll_area,
            bg=config.BG_GRADIENT_TOP,
            highlightthickness=0,
        )
        scrollbar = tk.Scrollbar(
            scroll_area,
            orient="vertical",
            command=canvas.yview,
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        form = tk.Frame(canvas, bg=config.BG_GRADIENT_TOP)
        form.grid_columnconfigure(0, weight=1)

        self.form_canvas = canvas
        self.form_window_id = canvas.create_window(
            0,
            0,
            anchor="nw",
            window=form,
        )
        form.bind("<Configure>", self._update_scroll_region)
        canvas.bind("<Configure>", self._resize_form_window)
        self.window.bind("<MouseWheel>", self._on_mouse_wheel)

        self.form_row = 0

        self._add_entry(form, "first_name", "First Name")
        self._add_entry(form, "last_name", "Last Name")
        self._add_entry(form, "preferred_name", "Preferred Name")
        self._add_entry(form, "email", "Email")
        self._add_entry(form, "linkedin", "LinkedIn URL")
        self._add_entry(form, "tags", "Tags, separated by commas")
        self._add_entry(form, "showcase_description", "Showcase Description")

        tk.Label(
            form,
            text="Bio",
            font=(config.FONT_FAMILY, 10, "bold"),
            fg=config.TEXT_SECONDARY,
            bg=config.BG_GRADIENT_TOP,
            anchor="w",
        ).grid(row=self.form_row, column=0, sticky="w", pady=(8, 3))
        self.form_row += 1

        self.bio_text = tk.Text(
            form,
            height=4,
            width=44,
            bd=1,
            relief="solid",
            font=(config.FONT_FAMILY, 10),
            wrap="word",
        )
        self.bio_text.grid(row=self.form_row, column=0, sticky="we")
        self.form_row += 1

        avatar_row = tk.Frame(form, bg=config.BG_GRADIENT_TOP)
        avatar_row.grid(row=self.form_row, column=0, sticky="we", pady=(14, 0))
        self.form_row += 1

        # The selected avatar is copied into assets so the profile stays portable.
        tk.Button(
            avatar_row,
            text="Choose Avatar",
            font=(config.FONT_FAMILY, 10, "bold"),
            bg="#FFFFFF",
            fg=config.ACCENT_BLUE,
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self._choose_avatar,
        ).pack(side="left")

        self.avatar_label = tk.Label(
            avatar_row,
            text="No avatar selected",
            font=(config.FONT_FAMILY, 9),
            fg=config.TEXT_TERTIARY,
            bg=config.BG_GRADIENT_TOP,
        )
        self.avatar_label.pack(side="left", padx=(12, 0))

        highlight_row = tk.Frame(form, bg=config.BG_GRADIENT_TOP)
        highlight_row.grid(row=self.form_row, column=0, sticky="we", pady=(12, 0))
        self.form_row += 1

        # The showcase image is optional. If it is empty, the Showcase tab is skipped.
        tk.Button(
            highlight_row,
            text="Choose Showcase Image",
            font=(config.FONT_FAMILY, 10, "bold"),
            bg="#FFFFFF",
            fg=config.ACCENT_BLUE,
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self._choose_highlight,
        ).pack(side="left")

        self.highlight_label = tk.Label(
            highlight_row,
            text="No showcase selected",
            font=(config.FONT_FAMILY, 9),
            fg=config.TEXT_TERTIARY,
            bg=config.BG_GRADIENT_TOP,
        )
        self.highlight_label.pack(side="left", padx=(12, 0))

        button_row = tk.Frame(self.window, bg=config.BG_GRADIENT_TOP)
        button_row.pack(fill="x", padx=48, pady=(18, 28))

        tk.Button(
            button_row,
            text="Create CardLens",
            font=(config.FONT_FAMILY, 12, "bold"),
            bg=config.ACCENT_BLUE,
            fg="#FFFFFF",
            activebackground=config.ACCENT_BLUE_HOVER,
            activeforeground="#FFFFFF",
            bd=0,
            padx=18,
            pady=12,
            height=2,
            cursor="hand2",
            command=self._create_profile,
        ).pack(fill="x")

    def _add_entry(self, parent, key, label):
        """Add one labeled text entry to the creation form."""
        tk.Label(
            parent,
            text=label,
            font=(config.FONT_FAMILY, 10, "bold"),
            fg=config.TEXT_SECONDARY,
            bg=config.BG_GRADIENT_TOP,
            anchor="w",
        ).grid(row=self.form_row, column=0, sticky="w", pady=(4, 2))
        self.form_row += 1

        entry = tk.Entry(
            parent,
            width=44,
            bd=1,
            relief="solid",
            font=(config.FONT_FAMILY, 10),
        )
        entry.grid(row=self.form_row, column=0, sticky="we", ipady=5)
        self.form_row += 1
        self.entries[key] = entry

    def _update_scroll_region(self, event):
        """Update the scrollable area after the form size changes."""
        if self.form_canvas is None:
            return
        self.form_canvas.configure(scrollregion=self.form_canvas.bbox("all"))

    def _resize_form_window(self, event):
        """Keep the inner form width aligned with the canvas width."""
        if self.form_canvas is None:
            return
        if self.form_window_id is None:
            return

        new_width = event.width - 4
        self.form_canvas.itemconfigure(self.form_window_id, width=new_width)

    def _on_mouse_wheel(self, event):
        """Scroll the form when the user moves the mouse wheel."""
        if self.form_canvas is None:
            return

        scroll_amount = int(event.delta / 120)
        if scroll_amount == 0:
            return

        self.form_canvas.yview_scroll(-scroll_amount, "units")

    def _close_window(self):
        """Close the creator window safely."""
        if self.window is None:
            return

        self.window.unbind("<MouseWheel>")
        self.window.destroy()

    def _choose_avatar(self):
        """Let the user select an optional avatar image."""
        file_path = filedialog.askopenfilename(
            parent=self.window,
            title="Choose an avatar image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg"),
                ("All files", "*.*"),
            ],
        )
        if not file_path:
            return

        self.avatar_path = Path(file_path)
        if self.avatar_label is not None:
            self.avatar_label.configure(text=self.avatar_path.name)

    def _choose_highlight(self):
        """Let the user select an optional showcase image."""
        file_path = filedialog.askopenfilename(
            parent=self.window,
            title="Choose a showcase image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg"),
                ("All files", "*.*"),
            ],
        )
        if not file_path:
            return

        self.highlight_path = Path(file_path)
        if self.highlight_label is not None:
            self.highlight_label.configure(text=self.highlight_path.name)

    def _create_profile(self):
        """Validate input, create files, save JSON data, and close the form."""
        first_name = self._entry_value("first_name")
        last_name = self._entry_value("last_name")

        # A card needs a first and last name so the created profile is readable.
        if not first_name:
            messagebox.showerror("CardLens", "First Name is required.")
            return
        if not last_name:
            messagebox.showerror("CardLens", "Last Name is required.")
            return

        try:
            # These steps are grouped so file and JSON errors show one clear message.
            profiles = self._load_profiles()
            profile_id = self._next_profile_id(profiles)
            avatar_value = self._save_avatar(profile_id)
            highlight_value = self._save_highlight(profile_id)
            qr_path = self._create_qr_code(profile_id)
            profile = self._build_profile(profile_id, avatar_value, highlight_value)
            profiles[profile_id] = profile
            self._save_profiles(profiles)
        except OSError as exc:
            messagebox.showerror("CardLens", f"Could not create CardLens:\n{exc}")
            return

        self.created_profile_id = profile_id
        messagebox.showinfo(
            "CardLens",
            f"Created {profile_id}.\nQR code saved to:\n{qr_path}",
        )
        self._close_window()

    def _entry_value(self, key):
        """Return trimmed text from one entry field."""
        value = self.entries[key].get()
        return value.strip()

    def _bio_value(self):
        """Return trimmed text from the bio box."""
        if self.bio_text is None:
            return ""
        value = self.bio_text.get("1.0", "end")
        return value.strip()

    def _load_profiles(self):
        """Load existing profiles before adding a new one."""
        if not config.PROFILES_JSON.exists():
            return {}

        text = config.PROFILES_JSON.read_text(encoding="utf-8")
        if not text.strip():
            return {}

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise OSError("profiles.json is not valid JSON.") from exc

        if isinstance(data, dict):
            return data

        raise OSError("profiles.json must contain a dictionary of profiles.")

    def _save_profiles(self, profiles):
        """Write updated profile data to profiles.json."""
        config.PROFILES_JSON.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(profiles, indent=2, ensure_ascii=False)
        config.PROFILES_JSON.write_text(text, encoding="utf-8")

    def _next_profile_id(self, profiles):
        """Find the next available card ID such as card_004."""
        highest = 0
        for profile_id in profiles.keys():
            if not profile_id.startswith("card_"):
                continue

            number_text = profile_id.replace("card_", "", 1)
            if not number_text.isdigit():
                continue

            number = int(number_text)
            if number > highest:
                highest = number

        # Keeping IDs sequential makes generated files easier to find.
        next_number = highest + 1
        return f"card_{next_number:03d}"

    def _save_avatar(self, profile_id):
        """Copy the selected avatar into the project assets folder."""
        if self.avatar_path is None:
            return ""

        suffix = self.avatar_path.suffix.lower()
        if suffix not in config.SUPPORTED_IMAGE_FORMATS:
            raise OSError("Avatar must be a PNG or JPG image.")

        # copy2 keeps the original file metadata while copying the image.
        config.AVATARS_DIR.mkdir(parents=True, exist_ok=True)
        target = config.AVATARS_DIR / f"{profile_id}_avatar{suffix}"
        shutil.copy2(self.avatar_path, target)
        return self._relative_path(target)

    def _save_highlight(self, profile_id):
        """Copy the selected showcase image into the project assets folder."""
        if self.highlight_path is None:
            return ""

        suffix = self.highlight_path.suffix.lower()
        if suffix not in config.SUPPORTED_IMAGE_FORMATS:
            raise OSError("Showcase image must be a PNG or JPG image.")

        config.HIGHLIGHTS_DIR.mkdir(parents=True, exist_ok=True)
        target = config.HIGHLIGHTS_DIR / f"{profile_id}_highlight{suffix}"
        shutil.copy2(self.highlight_path, target)
        return self._relative_path(target)

    def _create_qr_code(self, profile_id):
        """Generate a QR code image that stores the CardLens profile ID."""
        config.QR_CODES_DIR.mkdir(parents=True, exist_ok=True)

        # The prefix lets the program tell CardLens QR codes from ordinary text.
        payload = f"{config.QR_PREFIX}{profile_id}"
        out_path = config.QR_CODES_DIR / f"{profile_id}.png"

        qr = qrcode.QRCode(
            version=2,
            # High error correction makes the QR code more reliable when printed.
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=12,
            border=4,
        )
        qr.add_data(payload)
        qr.make(fit=True)

        image = qr.make_image(fill_color="black", back_color="white")
        image = image.convert("RGB")
        image.save(out_path)
        return out_path

    def _build_profile(self, profile_id, avatar_value, highlight_value):
        """Build the JSON profile dictionary for the new card."""
        first_name = self._entry_value("first_name")
        last_name = self._entry_value("last_name")
        preferred_name = self._entry_value("preferred_name")
        bio = self._bio_value()
        if not bio:
            bio = "A CardLens profile created from the local builder."

        pages = [
            self._card_page(),
            {
                "id": "about",
                "type": "text",
                "heading": "About Me",
                "content": bio,
            },
        ]

        if highlight_value:
            # Only add the Showcase page when the user selected a highlight image.
            pages.append(
                {
                    "id": "moments",
                    "type": "moments",
                    "heading": "Showcase",
                    "image": highlight_value,
                    "caption": self._showcase_description(),
                }
            )

        pages.append(
            {
                "id": "guestbook",
                "type": "guestbook",
                "heading": "Guestbook",
            }
        )

        profile = {
            "profile_id": profile_id,
            "first_name": first_name,
            "last_name": last_name,
            "preferred_name": preferred_name,
            "title": "",
            "bio": bio,
            "tags": self._tags(),
            "avatar": avatar_value,
            "highlight_image": highlight_value,
            "pages": pages,
        }
        return profile

    def _card_page(self):
        """Build the profile page that stores contact links."""
        links = []

        email = self._entry_value("email")
        if email:
            # mailto links can be opened by the user's default email app.
            links.append(
                {
                    "label": "Email",
                    "value": email,
                    "url": f"mailto:{email}",
                }
            )

        linkedin = self._entry_value("linkedin")
        if linkedin:
            url = linkedin
            # Add https when the user types a simple LinkedIn address.
            if not url.startswith("http://"):
                if not url.startswith("https://"):
                    url = f"https://{url}"

            links.append(
                {
                    "label": "LinkedIn",
                    "value": linkedin,
                    "url": url,
                }
            )

        page = {
            "id": "card",
            "type": "card",
            "heading": "",
            "links": links,
        }
        return page

    def _tags(self):
        """Split comma separated tags into a clean list."""
        tags_text = self._entry_value("tags")
        tags = []
        for part in tags_text.split(","):
            tag = part.strip()
            if tag:
                tags.append(tag)
        return tags

    def _showcase_description(self):
        """Return the optional description for the Showcase page."""
        description = self._entry_value("showcase_description")
        if description:
            return description
        return "This image gives the scanned card a more personal visual layer."

    def _relative_path(self, path):
        """Store asset paths relative to the project folder when possible."""
        try:
            relative_path = path.relative_to(config.BASE_DIR)
            return relative_path.as_posix()
        except ValueError:
            return str(path)
