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
from PIL import Image

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
        self.about_visual_path = None
        self.about_visual_button = None
        self.about_visual_label = None
        self.about_visual_var = None
        self.created_profile_id = None
        self.form_row = 0
        self.form_canvas = None
        self.form_window_id = None
        self.main_contact_vars = {}
        self.tooltip_window = None

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

        self._add_section_heading(form, "Profile Page")
        self._add_entry(form, "first_name", "First Name")
        self._add_entry(form, "last_name", "Last Name")
        self._add_entry(form, "preferred_name", "Preferred Name")
        self._add_entry(form, "tags", "Tags, separated by commas")
        self._add_avatar_picker(form)

        self._add_section_heading(form, "Contact Links")
        self._add_contact_entry(form, "email", "Email", show_info=True)
        self._add_contact_entry(form, "linkedin", "LinkedIn Username")
        self._add_contact_entry(form, "github", "GitHub Username")
        self._add_contact_entry(form, "instagram", "Instagram Username")
        self._add_contact_entry(
            form,
            "whatsapp",
            "WhatsApp Number",
            tip_text="Enter country code and phone number.\nExample: 61412345678",
        )
        self._add_contact_entry(form, "wechat", "WeChat ID")
        self._add_contact_entry(form, "tiktok", "TikTok URL")
        self._add_contact_entry(form, "rednote", "Xiaohongshu URL")
        self._add_contact_entry(form, "website", "Personal Website URL")

        self._add_section_heading(form, "About Page")
        self._add_bio_box(form)
        self._add_about_visual_picker(form)

        self._add_section_heading(form, "Showcase Page")
        self._add_entry(form, "showcase_description", "Showcase Description")
        self._add_highlight_picker(form)

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

    def _add_section_heading(self, parent, text):
        """Add a clear section title to the creator form."""
        tk.Label(
            parent,
            text=text,
            font=(config.FONT_FAMILY, 14, "bold"),
            fg=config.TEXT_PRIMARY,
            bg=config.BG_GRADIENT_TOP,
            anchor="w",
        ).grid(row=self.form_row, column=0, sticky="w", pady=(18, 6))
        self.form_row += 1

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

    def _add_bio_box(self, parent):
        """Add the About Me text box."""
        tk.Label(
            parent,
            text="Bio",
            font=(config.FONT_FAMILY, 10, "bold"),
            fg=config.TEXT_SECONDARY,
            bg=config.BG_GRADIENT_TOP,
            anchor="w",
        ).grid(row=self.form_row, column=0, sticky="w", pady=(8, 3))
        self.form_row += 1

        self.bio_text = tk.Text(
            parent,
            height=4,
            width=44,
            bd=1,
            relief="solid",
            font=(config.FONT_FAMILY, 10),
            wrap="word",
        )
        self.bio_text.grid(row=self.form_row, column=0, sticky="we")
        self.form_row += 1

    def _add_avatar_picker(self, parent):
        """Add the optional avatar picker for the Profile page."""
        avatar_row = tk.Frame(parent, bg=config.BG_GRADIENT_TOP)
        avatar_row.grid(row=self.form_row, column=0, sticky="we", pady=(10, 0))
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

    def _add_about_visual_picker(self, parent):
        """Add the optional About page visual picker."""
        tk.Label(
            parent,
            text="About Visual",
            font=(config.FONT_FAMILY, 10, "bold"),
            fg=config.TEXT_SECONDARY,
            bg=config.BG_GRADIENT_TOP,
            anchor="w",
        ).grid(row=self.form_row, column=0, sticky="w", pady=(10, 3))
        self.form_row += 1

        visual_row = tk.Frame(parent, bg=config.BG_GRADIENT_TOP)
        visual_row.grid(row=self.form_row, column=0, sticky="we")
        self.form_row += 1

        self.about_visual_var = tk.StringVar(value="None")
        choices = ["None", "Default 1", "Default 2", "Default 3", "Custom Icon"]
        tk.OptionMenu(
            visual_row,
            self.about_visual_var,
            *choices,
            command=self._on_about_visual_choice,
        ).pack(side="left")

        self.about_visual_button = tk.Button(
            visual_row,
            text="Choose File",
            font=(config.FONT_FAMILY, 10, "bold"),
            bg="#FFFFFF",
            fg=config.ACCENT_BLUE,
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self._choose_about_visual,
        )

        self.about_visual_label = tk.Label(
            visual_row,
            text="No custom icon selected",
            font=(config.FONT_FAMILY, 9),
            fg=config.TEXT_TERTIARY,
            bg=config.BG_GRADIENT_TOP,
        )
        self._on_about_visual_choice("None")

    def _on_about_visual_choice(self, choice):
        """Only show the file picker when the user chooses a custom icon."""
        if self.about_visual_button is None:
            return
        if self.about_visual_label is None:
            return

        if choice == "Custom Icon":
            self.about_visual_button.pack(side="left", padx=(10, 0))
            self.about_visual_label.pack(side="left", padx=(12, 0))
            return

        self.about_visual_button.pack_forget()
        self.about_visual_label.pack_forget()

    def _add_highlight_picker(self, parent):
        """Add the optional Showcase image picker."""
        highlight_row = tk.Frame(parent, bg=config.BG_GRADIENT_TOP)
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

    def _add_contact_entry(self, parent, key, label, show_info=False, tip_text=""):
        """Add one contact entry with a main contact checkbox."""
        label_row = tk.Frame(parent, bg=config.BG_GRADIENT_TOP)
        label_row.grid(row=self.form_row, column=0, sticky="we", pady=(4, 2))
        self.form_row += 1

        tk.Label(
            label_row,
            text=label,
            font=(config.FONT_FAMILY, 10, "bold"),
            fg=config.TEXT_SECONDARY,
            bg=config.BG_GRADIENT_TOP,
            anchor="w",
        ).pack(side="left")

        if show_info:
            info_label = tk.Label(
                label_row,
                text="i",
                font=(config.FONT_FAMILY, 9, "bold"),
                fg="#FFFFFF",
                bg=config.ACCENT_BLUE,
                width=2,
                cursor="question_arrow",
            )
            info_label.pack(side="left", padx=(8, 0))
            info_label.bind("<Enter>", self._show_main_contact_tip)
            info_label.bind("<Leave>", self._hide_main_contact_tip)

        if tip_text:
            tip_label = tk.Label(
                label_row,
                text="i",
                font=(config.FONT_FAMILY, 9, "bold"),
                fg="#FFFFFF",
                bg=config.ACCENT_BLUE,
                width=2,
                cursor="question_arrow",
            )
            tip_label.pack(side="left", padx=(8, 0))
            tip_label.bind("<Enter>", lambda event, text=tip_text: self._show_custom_tip(event, text))
            tip_label.bind("<Leave>", self._hide_main_contact_tip)

        row = tk.Frame(parent, bg=config.BG_GRADIENT_TOP)
        row.grid(row=self.form_row, column=0, sticky="we")
        row.grid_columnconfigure(0, weight=1)
        self.form_row += 1

        entry = tk.Entry(
            row,
            width=38,
            bd=1,
            relief="solid",
            font=(config.FONT_FAMILY, 10),
        )
        entry.grid(row=0, column=0, sticky="we", ipady=5)
        self.entries[key] = entry

        var = tk.BooleanVar(value=False)
        self.main_contact_vars[key] = var

        checkbox = tk.Checkbutton(
            row,
            text="Main",
            variable=var,
            command=lambda k=key: self._check_main_contact_limit(k),
            font=(config.FONT_FAMILY, 9),
            fg=config.TEXT_SECONDARY,
            bg=config.BG_GRADIENT_TOP,
            activebackground=config.BG_GRADIENT_TOP,
            cursor="hand2",
        )
        checkbox.grid(row=0, column=1, sticky="e", padx=(8, 0))

        if show_info:
            checkbox.bind("<Enter>", self._show_main_contact_tip)
            checkbox.bind("<Leave>", self._hide_main_contact_tip)

    def _show_main_contact_tip(self, event):
        """Show a small explanation for the main contact checkbox."""
        message = (
            "Tick up to 3 contacts to show on the Profile page.\n"
            "Other contacts will appear in the Contact tab."
        )
        self._show_custom_tip(event, message)

    def _show_custom_tip(self, event, message):
        """Show a small tooltip with custom text."""
        if self.tooltip_window is not None:
            return

        self.tooltip_window = tk.Toplevel(self.window)
        self.tooltip_window.overrideredirect(True)
        self.tooltip_window.attributes("-topmost", True)

        x = event.widget.winfo_rootx() + 22
        y = event.widget.winfo_rooty() + 22
        self.tooltip_window.geometry(f"+{x}+{y}")

        tk.Label(
            self.tooltip_window,
            text=message,
            font=(config.FONT_FAMILY, 9),
            fg=config.TEXT_PRIMARY,
            bg="#FFFFFF",
            bd=1,
            relief="solid",
            padx=8,
            pady=6,
            justify="left",
        ).pack()

    def _hide_main_contact_tip(self, _event):
        """Hide the main contact explanation tooltip."""
        if self.tooltip_window is not None:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def _check_main_contact_limit(self, key):
        """Prevent the user from choosing more than three main contacts."""
        selected_count = 0
        for var in self.main_contact_vars.values():
            if var.get():
                selected_count += 1

        if selected_count <= 3:
            return

        self.main_contact_vars[key].set(False)
        messagebox.showinfo(
            "CardLens",
            "Choose up to 3 main contacts for the Profile page.",
            parent=self.window,
        )

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

    def _choose_about_visual(self):
        """Let the user select a custom About page icon image."""
        file_path = filedialog.askopenfilename(
            parent=self.window,
            title="Choose an About page visual image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg"),
                ("All files", "*.*"),
            ],
        )
        if not file_path:
            return

        self.about_visual_path = Path(file_path)
        if self.about_visual_var is not None:
            self.about_visual_var.set("Custom Icon")
            self._on_about_visual_choice("Custom Icon")
        if self.about_visual_label is not None:
            self.about_visual_label.configure(text=self.about_visual_path.name)

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
            about_visual_value = self._save_about_visual(profile_id)
            highlight_value = self._save_highlight(profile_id)
            qr_path = self._create_qr_code(profile_id)
            profile = self._build_profile(profile_id, avatar_value, highlight_value, about_visual_value)
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
        self._validate_image_file(self.avatar_path, "Avatar")

        # copy2 keeps the original file metadata while copying the image.
        config.AVATARS_DIR.mkdir(parents=True, exist_ok=True)
        target = config.AVATARS_DIR / f"{profile_id}_avatar{suffix}"
        shutil.copy2(self.avatar_path, target)
        return self._relative_path(target)

    def _save_about_visual(self, profile_id):
        """Return the About page visual path or copy a custom icon image."""
        choice = "None"
        if self.about_visual_var is not None:
            choice = self.about_visual_var.get()

        default_visuals = {
            "Default 1": config.ABOUT_VISUALS_DIR / "default_1.png",
            "Default 2": config.ABOUT_VISUALS_DIR / "default_2.png",
            "Default 3": config.ABOUT_VISUALS_DIR / "default_3.png",
        }

        if choice in default_visuals:
            return self._relative_path(default_visuals[choice])

        if choice != "Custom Icon":
            return ""

        if self.about_visual_path is None:
            return ""

        suffix = self.about_visual_path.suffix.lower()
        if suffix not in config.SUPPORTED_IMAGE_FORMATS:
            raise OSError("About visual must be a PNG or JPG image.")
        self._validate_image_file(self.about_visual_path, "About visual")

        config.ABOUT_VISUALS_DIR.mkdir(parents=True, exist_ok=True)
        target = config.ABOUT_VISUALS_DIR / f"{profile_id}_about_visual{suffix}"
        shutil.copy2(self.about_visual_path, target)
        return self._relative_path(target)

    def _save_highlight(self, profile_id):
        """Copy the selected showcase image into the project assets folder."""
        if self.highlight_path is None:
            return ""

        suffix = self.highlight_path.suffix.lower()
        if suffix not in config.SUPPORTED_IMAGE_FORMATS:
            raise OSError("Showcase image must be a PNG or JPG image.")
        self._validate_image_file(self.highlight_path, "Showcase image")

        config.HIGHLIGHTS_DIR.mkdir(parents=True, exist_ok=True)
        target = config.HIGHLIGHTS_DIR / f"{profile_id}_highlight{suffix}"
        shutil.copy2(self.highlight_path, target)
        return self._relative_path(target)

    def _validate_image_file(self, path, label):
        """Check that the selected image can actually be opened by Pillow."""
        try:
            with Image.open(path) as image:
                image.verify()
        except OSError as exc:
            raise OSError(label + " is not a readable image file.") from exc

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

    def _build_profile(self, profile_id, avatar_value, highlight_value, about_visual_value=""):
        """Build the JSON profile dictionary for the new card."""
        first_name = self._entry_value("first_name")
        last_name = self._entry_value("last_name")
        preferred_name = self._entry_value("preferred_name")
        bio = self._bio_value()
        if not bio:
            bio = "A CardLens profile created from the local builder."

        all_links = self._all_contact_links()
        profile_links = self._profile_contact_links(all_links)
        extra_links = []
        for link in all_links:
            if link not in profile_links:
                extra_links.append(link)

        pages = [
            self._card_page(profile_links),
            self._about_page(bio, about_visual_value),
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

        if extra_links:
            pages.append(
                {
                    "id": "contact",
                    "type": "contact",
                    "heading": "More Contacts",
                    "links": extra_links,
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

    def _card_page(self, links):
        """Build the profile page that stores contact links."""
        page = {
            "id": "card",
            "type": "card",
            "heading": "",
            "links": links,
        }
        return page

    def _about_page(self, bio, about_visual_value):
        """Build the About page data with an optional visual image."""
        page = {
            "id": "about",
            "type": "text",
            "heading": "About Me",
            "content": bio,
        }
        if about_visual_value:
            page["visual"] = about_visual_value
        return page

    def _all_contact_links(self):
        """Build all contact links entered in the creator form."""
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

        self._add_account_link(links, "LinkedIn", "linkedin", "https://www.linkedin.com/in/")
        self._add_account_link(links, "GitHub", "github", "https://github.com/")
        self._add_account_link(links, "Instagram", "instagram", "https://www.instagram.com/", suffix="/")
        self._add_whatsapp_link(links)
        self._add_plain_link(links, "WeChat", "wechat")
        self._add_www_url_link(links, "TikTok", "tiktok")
        self._add_www_url_link(links, "Xiaohongshu", "rednote")
        self._add_url_link(links, "Personal Website", "website")
        return links

    def _add_url_link(self, links, label, key):
        """Add a URL contact link when the matching field is filled."""
        value = self._entry_value(key)
        if not value:
            return

        links.append(
            {
                "label": label,
                "value": value,
                "url": self._normal_url(value),
            }
        )

    def _add_www_url_link(self, links, label, key):
        """Add a URL contact link and prefer https://www when it is missing."""
        value = self._entry_value(key)
        if not value:
            return

        links.append(
            {
                "label": label,
                "value": value,
                "url": self._normal_www_url(value),
            }
        )

    def _add_account_link(self, links, label, key, base_url, suffix=""):
        """Add a social link from a username or a full URL."""
        value = self._entry_value(key)
        if not value:
            return

        url = self._account_url(value, base_url, suffix)
        links.append(
            {
                "label": label,
                "value": value,
                "url": url,
            }
        )

    def _add_whatsapp_link(self, links):
        """Add a WhatsApp link from an international phone number."""
        value = self._entry_value("whatsapp")
        if not value:
            return

        digits = ""
        for character in value:
            if character.isdigit():
                digits = digits + character

        url = ""
        if digits:
            url = "https://wa.me/" + digits

        links.append(
            {
                "label": "WhatsApp",
                "value": value,
                "url": url,
            }
        )

    def _add_plain_link(self, links, label, key):
        """Add a contact value that does not need a clickable URL."""
        value = self._entry_value(key)
        if not value:
            return

        links.append(
            {
                "label": label,
                "value": value,
                "url": "",
            }
        )

    def _normal_url(self, value):
        """Add https to a link when the user did not type a scheme."""
        url = value.strip()
        if url.startswith("http://"):
            return url
        if url.startswith("https://"):
            return url
        return "https://" + url

    def _normal_www_url(self, value):
        """Add https://www. to a platform URL when the user leaves it out."""
        url = value.strip()
        if url.startswith("http://"):
            return url
        if url.startswith("https://"):
            return url
        if url.startswith("www."):
            return "https://" + url
        return "https://www." + url

    def _account_url(self, value, base_url, suffix=""):
        """Build a platform URL from a username unless the user entered a full URL."""
        account = value.strip()
        if account.startswith("http://"):
            return account
        if account.startswith("https://"):
            return account

        account = account.lstrip("@")

        return base_url + account + suffix

    def _profile_contact_links(self, all_links):
        """Select up to three links to show on the main Profile page."""
        selected_links = []
        requested_labels = self._main_contact_labels()

        for requested_label in requested_labels:
            for link in all_links:
                if link in selected_links:
                    continue
                if self._label_matches(link.get("label", ""), requested_label):
                    selected_links.append(link)
                    break
            if len(selected_links) == 3:
                return selected_links

        for link in all_links:
            if link not in selected_links:
                # If the user did not choose enough main contacts, use the first filled contacts in form order.
                selected_links.append(link)
            if len(selected_links) == 3:
                break

        return selected_links

    def _main_contact_labels(self):
        """Read the selected main contact labels from the checkboxes."""
        labels = []

        contact_order = [
            ("email", "email"),
            ("linkedin", "linkedin"),
            ("github", "github"),
            ("instagram", "instagram"),
            ("whatsapp", "whatsapp"),
            ("wechat", "wechat"),
            ("tiktok", "tiktok"),
            ("rednote", "xiaohongshu"),
            ("website", "personal website"),
        ]

        for key, label in contact_order:
            var = self.main_contact_vars.get(key)
            if var is not None:
                if var.get():
                    labels.append(label)
            if len(labels) == 3:
                break

        return labels

    def _label_matches(self, actual_label, requested_label):
        """Match contact labels without requiring exact capitalization."""
        actual = actual_label.strip().lower()
        requested = requested_label.strip().lower()
        if actual == requested:
            return True
        if requested in actual:
            return True
        if actual in requested:
            return True
        if actual == "xiaohongshu" and "rednote" in requested:
            return True
        if actual == "personal website" and requested == "website":
            return True
        return False

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
