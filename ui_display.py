"""
ui_display.py

This file displays a recognized CardLens profile.
It uses standard Tkinter ttk widgets with the Azure ttk theme.
"""

import ctypes
import json
import sys
import tkinter as tk
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import ttk

from PIL import Image, ImageOps, ImageTk

import config
import window_utils


AZURE_THEME_FILE = config.ASSETS_DIR / "azure_ttk_theme" / "azure.tcl"


if sys.platform == "win32":
    # This improves text and image sharpness on high DPI Windows screens.
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


class ProfileDisplay:
    """Tkinter profile window shown after a card is recognized."""

    def __init__(self, root):
        """Prepare the profile display window and shared UI state."""
        self.root = root
        self.root.withdraw()
        self.root.title(config.WINDOW_TITLE)
        window_utils.center_window(self.root, 1200, 780)
        self.root.resizable(False, False)

        self.profile = None

        # Tkinter images disappear if Python garbage collects the image objects.
        self.image_refs = []
        self.status_text = tk.StringVar(value="")
        self.guestbook_text = None
        self.back_to_menu_requested = False
        self.guestbook_load_error = ""

        # These flags stop the first render reveal from playing again after updates.
        self.first_render = True
        self.active_tab_name = "Profile"
        self.profile_reveal_played = False

        self._load_theme()

    def _load_theme(self):
        """Load the Azure ttk theme if it is available."""
        if not AZURE_THEME_FILE.exists():
            return

        try:
            self.root.tk.call("source", str(AZURE_THEME_FILE))
            self.root.tk.call("set_theme", "light")
        except tk.TclError:
            return

    def show_profile(self, profile):
        """Store one profile and build the visible interface."""
        self.profile = profile
        self._build_ui()
        if self.first_render:
            self.first_render = False
            self.root.update_idletasks()

            # The window is shown only after layout is ready to reduce flicker.
            self.root.deiconify()
            self.root.lift()

    def _build_ui(self):
        """Rebuild the whole profile window from current profile data."""
        for child in self.root.winfo_children():
            # Rebuilding is simple and keeps tabs in sync after saving notes.
            child.destroy()

        self.image_refs = []
        self.guestbook_text = None

        outer = ttk.Frame(self.root, padding=24)
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 18))

        ttk.Label(
            header,
            text="CardLens",
            font=(config.FONT_FAMILY, 24, "bold"),
        ).pack(side="left")

        ttk.Button(
            header,
            text="Menu",
            command=self._back_to_menu,
        ).pack(side="right", pady=(6, 0))

        card = ttk.Frame(outer, style="Card.TFrame", padding=22)
        card.pack(fill="both", expand=True)

        # The notebook keeps the UI simple and easy to explain.
        notebook = ttk.Notebook(card)
        notebook.pack(fill="both", expand=True)
        tab_frames = {}

        profile_tab = ttk.Frame(notebook, padding=22)
        notebook.add(profile_tab, text="Profile")
        tab_frames["Profile"] = profile_tab
        self._build_profile_tab(profile_tab)

        about_page = self._page_by_type("text")
        if about_page is not None:
            about_tab = ttk.Frame(notebook, padding=22)
            notebook.add(about_tab, text="About")
            tab_frames["About"] = about_tab
            self._build_about_tab(about_tab, about_page)

        showcase_page = self._page_by_type("moments")
        if showcase_page is not None:
            showcase_tab = ttk.Frame(notebook, padding=22)
            notebook.add(showcase_tab, text="Showcase")
            tab_frames["Showcase"] = showcase_tab
            self._build_showcase_tab(showcase_tab, showcase_page)

        contact_page = self._page_by_type("contact")
        if contact_page is not None:
            contact_tab = ttk.Frame(notebook, padding=22)
            notebook.add(contact_tab, text="Contact")
            tab_frames["Contact"] = contact_tab
            self._build_contact_tab(contact_tab, contact_page)

        guestbook_page = self._page_by_type("guestbook")
        if guestbook_page is not None:
            guestbook_tab = ttk.Frame(notebook, padding=22)
            notebook.add(guestbook_tab, text="Guestbook")
            tab_frames["Guestbook"] = guestbook_tab
            self._build_guestbook_tab(guestbook_tab, guestbook_page)

        if self.active_tab_name in tab_frames:
            # After saving a guestbook note, the Guestbook tab stays selected.
            notebook.select(tab_frames[self.active_tab_name])

        def remember_tab(_event):
            selected_tab = notebook.select()
            if selected_tab:
                self.active_tab_name = notebook.tab(selected_tab, "text")

        notebook.bind("<<NotebookTabChanged>>", remember_tab)

        ttk.Label(
            outer,
            textvariable=self.status_text,
            font=(config.FONT_FAMILY, 9),
        ).pack(anchor="w", pady=(12, 0))

    def _build_profile_tab(self, parent):
        """Build the main profile tab with avatar, name, links, and actions."""
        parent.columnconfigure(1, weight=1)
        reveal_widgets = []

        avatar = self._load_image(self.profile.get("avatar", ""), 120, 120)
        if avatar:
            avatar_widget = ttk.Label(parent, image=avatar)
            avatar_widget.grid(
                row=0,
                column=0,
                rowspan=4,
                sticky="n",
                padx=(0, 28),
            )
        else:
            # Initials are used as a fallback when no avatar image exists.
            avatar_widget = tk.Frame(
                parent,
                width=120,
                height=120,
                bg=config.ACCENT_BLUE_LIGHT,
                bd=1,
                relief="solid",
            )
            avatar_widget.grid(row=0, column=0, rowspan=4, sticky="n", padx=(0, 28))
            avatar_widget.grid_propagate(False)
            tk.Label(
                avatar_widget,
                text=self._initials(),
                font=(config.FONT_FAMILY, 30, "bold"),
                fg=config.ACCENT_BLUE,
                bg=config.ACCENT_BLUE_LIGHT,
            ).place(relx=0.5, rely=0.5, anchor="center")
        reveal_widgets.append(avatar_widget)

        name_label = ttk.Label(
            parent,
            text=self._full_name(),
            font=(config.FONT_FAMILY, 28, "bold"),
        )
        name_label.grid(row=0, column=1, sticky="w")
        reveal_widgets.append(name_label)

        bio_label = ttk.Label(
            parent,
            text=self.profile.get("bio", ""),
            font=(config.FONT_FAMILY, 11),
            wraplength=580,
            justify="left",
        )
        bio_label.grid(row=1, column=1, sticky="w", pady=(10, 0))
        reveal_widgets.append(bio_label)

        tags = self.profile.get("tags", [])
        if tags:
            tags_frame = ttk.Frame(parent)
            tags_frame.grid(row=2, column=1, sticky="w", pady=(18, 8))
            reveal_widgets.append(tags_frame)

            for tag in tags:
                tk.Label(
                    tags_frame,
                    text=tag,
                    font=(config.FONT_FAMILY, 10, "bold"),
                    fg=config.ACCENT_BLUE,
                    bg=config.ACCENT_BLUE_LIGHT,
                    bd=1,
                    relief="solid",
                    padx=10,
                    pady=4,
                ).pack(side="left", padx=(0, 8))

        links_frame = ttk.Frame(parent)
        links_frame.grid(row=3, column=1, sticky="ew", pady=(18, 0))
        reveal_widgets.append(links_frame)

        links = self._profile_links()
        if not links:
            ttk.Label(links_frame, text="No contact links.").pack(anchor="w")

        for link in links:
            self._add_contact_button(links_frame, link)

        button_row = ttk.Frame(parent)
        button_row.grid(row=4, column=1, sticky="ew", pady=(22, 0))
        button_row.columnconfigure(0, weight=1)
        button_row.columnconfigure(1, weight=1)
        reveal_widgets.append(button_row)

        ttk.Button(
            button_row,
            text="Save Contact",
            style="Accent.TButton",
            command=self._save_contact,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ttk.Button(
            button_row,
            text="Menu",
            command=self._back_to_menu,
        ).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        if not self.profile_reveal_played:
            # This is the only small animation kept in the final UI.
            self.profile_reveal_played = True
            self._reveal_widgets(reveal_widgets)

    def _reveal_widgets(self, widgets):
        """Reveal the main profile widgets one by one with Tkinter after."""
        for widget in widgets:
            widget.grid_remove()

        def show_next(index):
            """Show one hidden widget and schedule the next one."""
            if index >= len(widgets):
                return
            if not self.root.winfo_exists():
                return

            widgets[index].grid()
            self.root.after(90, show_next, index + 1)

        self.root.after(120, show_next, 0)

    def _add_contact_button(self, parent, link):
        """Add one contact link button to the profile tab."""
        label = link.get("label", "Link")
        url = link.get("url", "")
        value = link.get("value", "")
        text = self._display_contact_label(label, value)
        icon = self._load_icon(label)

        button_options = {
            "text": text,
            "command": self._open_url_command(url),
        }

        if icon is not None:
            button_options["image"] = icon
            button_options["compound"] = "left"

        ttk.Button(parent, **button_options).pack(fill="x", pady=4)

    def _build_about_tab(self, parent, page):
        """Build the about tab from a text page."""
        heading = page.get("heading", "About Me")
        content = page.get("content", "")
        visual_value = page.get("visual", "")

        content_frame = ttk.Frame(parent)
        content_frame.pack(fill="both", expand=True)
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=0)
        content_frame.rowconfigure(0, weight=1)

        text_frame = ttk.Frame(content_frame)
        text_frame.grid(row=0, column=0, sticky="nw", padx=(0, 24))

        ttk.Label(
            text_frame,
            text=heading,
            font=(config.FONT_FAMILY, 24, "bold"),
        ).pack(anchor="w", pady=(0, 16))

        ttk.Label(
            text_frame,
            text=content,
            font=(config.FONT_FAMILY, 12),
            wraplength=740,
            justify="left",
        ).pack(anchor="w")

        visual = self._load_image(visual_value, 250, 250, crop=False)
        if visual:
            visual_frame = ttk.Frame(content_frame)
            visual_frame.grid(row=0, column=1, sticky="se")
            ttk.Label(visual_frame, image=visual).pack()

    def _build_showcase_tab(self, parent, page):
        """Build the showcase tab when a profile has a highlight image."""
        heading = page.get("heading", "Showcase")
        image_value = page.get("image", "")
        caption = page.get("caption", "")
        if not caption:
            caption = "This image gives the scanned card a more personal visual layer."

        ttk.Label(
            parent,
            text=heading,
            font=(config.FONT_FAMILY, 24, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        content = ttk.Frame(parent)
        content.pack(fill="both", expand=True, pady=(10, 0))
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=1)

        image_area = ttk.Frame(content)
        image_area.grid(row=0, column=0, sticky="nw", padx=(0, 24))

        image = self._load_image(image_value, 680, 330)
        if image:
            ttk.Label(image_area, image=image).pack(anchor="w")
        else:
            # This branch handles profiles that do not include a showcase image.
            empty = ttk.Frame(image_area, style="Card.TFrame", padding=40)
            empty.pack(fill="x")
            ttk.Label(
                empty,
                text="No showcase image.",
                font=(config.FONT_FAMILY, 13, "bold"),
            ).pack()

        info_panel = ttk.Frame(content, style="Card.TFrame", padding=18)
        info_panel.grid(row=0, column=1, sticky="new")

        ttk.Label(
            info_panel,
            text="Profile Highlight",
            font=(config.FONT_FAMILY, 13, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        ttk.Label(
            info_panel,
            text=caption,
            font=(config.FONT_FAMILY, 10),
            wraplength=250,
            justify="left",
        ).pack(anchor="w")

    def _build_contact_tab(self, parent, page):
        """Build the Contact tab for extra contact links."""
        heading = page.get("heading", "More Contacts")
        links = page.get("links", [])

        ttk.Label(
            parent,
            text=heading,
            font=(config.FONT_FAMILY, 24, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        ttk.Label(
            parent,
            text="Additional ways to connect with this profile.",
            font=(config.FONT_FAMILY, 11),
        ).pack(anchor="w", pady=(0, 18))

        link_frame = ttk.Frame(parent)
        link_frame.pack(fill="x", anchor="w")

        if not links:
            ttk.Label(
                link_frame,
                text="No extra contact links.",
                font=(config.FONT_FAMILY, 10),
            ).pack(anchor="w")
            return

        for link in links:
            self._add_contact_button(link_frame, link)

    def _build_guestbook_tab(self, parent, page):
        """Build the guestbook tab for reading and saving notes."""
        heading = page.get("heading", "Guestbook")

        ttk.Label(
            parent,
            text=heading,
            font=(config.FONT_FAMILY, 24, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        ttk.Label(
            parent,
            text="Leave a short note after viewing this card.",
            font=(config.FONT_FAMILY, 11),
        ).pack(anchor="w", pady=(0, 14))

        content_frame = ttk.Frame(parent)
        content_frame.pack(fill="both", expand=True)
        content_frame.columnconfigure(0, weight=3)
        content_frame.columnconfigure(1, weight=2)

        input_frame = ttk.Frame(content_frame)
        input_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 18))

        notes_frame = ttk.Frame(content_frame)
        notes_frame.grid(row=0, column=1, sticky="nsew")

        self.guestbook_text = tk.Text(
            input_frame,
            height=8,
            relief="solid",
            bd=1,
            font=(config.FONT_FAMILY, 10),
            wrap="word",
        )
        self.guestbook_text.pack(fill="x")

        ttk.Button(
            input_frame,
            text="Save Note",
            style="Accent.TButton",
            command=self._save_guestbook_note,
        ).pack(anchor="e", pady=(14, 0))

        saved_notes = self._load_guestbook_notes()

        # Notes are filtered so each profile only shows its own guestbook.
        ttk.Label(
            notes_frame,
            text=str(len(saved_notes)) + " saved notes for this profile",
            font=(config.FONT_FAMILY, 9),
        ).pack(anchor="w")

        self._draw_recent_notes(notes_frame, saved_notes)

    def _draw_recent_notes(self, parent, notes):
        """Draw the newest guestbook notes in the side panel."""
        if not notes:
            ttk.Label(
                parent,
                text="No notes yet.",
                font=(config.FONT_FAMILY, 10),
            ).pack(anchor="w", pady=(8, 0))
            return

        ttk.Label(
            parent,
            text="Recent notes",
            font=(config.FONT_FAMILY, 11, "bold"),
        ).pack(anchor="w", pady=(14, 6))

        recent_notes = notes[-3:]
        recent_notes.reverse()

        for note in recent_notes:
            message = str(note.get("message", "")).strip()
            created_at = str(note.get("created_at", "")).strip()

            if not message:
                continue

            note_frame = ttk.Frame(parent, style="Card.TFrame", padding=10)
            note_frame.pack(fill="x", pady=4)

            ttk.Label(
                note_frame,
                text=message,
                font=(config.FONT_FAMILY, 10),
                wraplength=320,
                justify="left",
            ).pack(anchor="w")

            if created_at:
                ttk.Label(
                    note_frame,
                    text=created_at,
                    font=(config.FONT_FAMILY, 8),
                ).pack(anchor="w", pady=(4, 0))

    def _load_image(self, value, width, height, crop=True):
        """Load and resize an image for Tkinter display."""
        if not value:
            return None

        path = Path(value)
        if not path.is_absolute():
            path = config.BASE_DIR / path

        if not path.exists():
            return None

        try:
            source = Image.open(path).convert("RGB")

            if crop:
                # ImageOps.fit crops and resizes while keeping a neat fixed size.
                fitted = ImageOps.fit(source, (width, height), method=Image.LANCZOS)
            else:
                # ImageOps.contain keeps the whole image visible without cropping.
                fitted = ImageOps.contain(source, (width, height), method=Image.LANCZOS)

            photo = ImageTk.PhotoImage(fitted)
        except OSError:
            return None

        self.image_refs.append(photo)
        return photo

    def _load_icon(self, label):
        """Load a small icon based on a contact label."""
        icon_name = self._icon_name(label)
        if not icon_name:
            return None

        path = config.ICONS_DIR / f"{icon_name}.png"
        if not path.exists():
            return None

        try:
            source = Image.open(path).convert("RGBA")
            icon_size = self._icon_size(label)
            source = ImageOps.contain(source, (icon_size, icon_size), method=Image.LANCZOS)
            photo = ImageTk.PhotoImage(source)
        except OSError:
            return None

        self.image_refs.append(photo)
        return photo

    def _icon_size(self, label):
        """Return a larger icon size for small social logos."""
        text = label.lower()
        if "tiktok" in text:
            return 30
        if "wechat" in text:
            return 30
        return 18

    def _display_contact_label(self, label, value=""):
        """Return the clean platform name shown on contact buttons."""
        text = label.lower()
        if "email" in text:
            if value:
                return value
            return "Email"
        if "wechat" in text:
            if value:
                return "WeChat ID: " + value
            return "WeChat"
        if "xiaohongshu" in text:
            return "Xiaohongshu"
        if "rednote" in text:
            return "Xiaohongshu"
        if "website" in text:
            return "Personal Website"
        return label

    def _icon_name(self, label):
        """Choose an icon file name from a contact label."""
        text = label.lower()
        if "github" in text:
            return "github"
        if "linkedin" in text:
            return "linkedin"
        if "instagram" in text:
            return "instagram"
        if "whatsapp" in text:
            return "whatsapp"
        if "tiktok" in text:
            return "tiktok"
        if "rednote" in text:
            return "rednote"
        if "xiaohongshu" in text:
            return "rednote"
        if "wechat" in text:
            return "wechat"
        if "email" in text:
            return "email"
        if "mail" in text:
            return "email"
        return ""

    def _profile_links(self):
        """Return contact links stored on the card page."""
        card_page = self._page_by_type("card")
        if card_page is None:
            return []
        return card_page.get("links", [])

    def _all_contact_links(self):
        """Return profile page links and extra Contact page links together."""
        links = []
        for link in self._profile_links():
            links.append(link)

        contact_page = self._page_by_type("contact")
        if contact_page is not None:
            for link in contact_page.get("links", []):
                links.append(link)

        return links

    def _page_by_type(self, page_type):
        """Find the first page with the requested page type."""
        pages = self.profile.get("pages", [])
        for page in pages:
            if page.get("type") == page_type:
                return page
        return None

    def _open_url_command(self, url):
        """Create a button command that opens a link in the browser."""
        def command():
            """Open the stored URL if it exists."""
            if url:
                webbrowser.open(url)

        return command

    def _back_to_menu(self):
        """Close the profile window and ask main.py to reopen the menu."""
        self.back_to_menu_requested = True
        self.root.destroy()

    def _save_contact(self):
        """Save the profile as a vCard and show the result in the status text."""
        try:
            out = self._write_vcard()
        except OSError as exc:
            self.status_text.set("Could not save contact: " + str(exc))
            return

        self.status_text.set("Saved contact to " + out.name)

    def _write_vcard(self):
        """Write a simple vCard file for the current profile."""
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            desktop = Path.home()

        first_name = self.profile.get("first_name", "profile")
        last_name = self.profile.get("last_name", "")
        file_name = (first_name + "_" + last_name).strip("_")
        file_name = self._safe_file_name(file_name)
        out = desktop / (file_name + ".vcf")
        out = self._unique_path(out)

        lines = [
            "BEGIN:VCARD",
            "VERSION:3.0",
            "N:" + self._vcard_escape(last_name) + ";" + self._vcard_escape(first_name) + ";;;",
            "FN:" + self._vcard_escape(self._full_name()),
            "NICKNAME:" + self._vcard_escape(self.profile.get("preferred_name", "")),
            "NOTE:" + self._vcard_escape(self.profile.get("bio", "")),
        ]

        for link in self._all_contact_links():
            value = link.get("value", "")
            url = link.get("url", "")
            if url.startswith("mailto:"):
                # vCard uses EMAIL for mail links and URL for web links.
                lines.append("EMAIL:" + self._vcard_escape(value))
            elif url:
                lines.append("URL:" + self._vcard_escape(url))

        lines.append("END:VCARD")
        out.write_text("\n".join(lines), encoding="utf-8")
        return out

    def _vcard_escape(self, text):
        """Escape simple vCard text values."""
        value = str(text)
        value = value.replace("\\", "\\\\")
        value = value.replace("\n", "\\n")
        value = value.replace(";", "\\;")
        value = value.replace(",", "\\,")
        return value

    def _unique_path(self, path):
        """Return a new path if the target file already exists."""
        if not path.exists():
            return path

        counter = 2
        while True:
            candidate = path.with_name(path.stem + "_" + str(counter) + path.suffix)
            if not candidate.exists():
                return candidate
            counter += 1

    def _safe_file_name(self, text):
        """Return a Windows safe file name for exported contact files."""
        safe_text = ""
        for character in text:
            if character.isalnum():
                safe_text = safe_text + character
            elif character in [" ", "_", "-"]:
                safe_text = safe_text + character
            else:
                safe_text = safe_text + "_"

        safe_text = safe_text.strip()
        if safe_text:
            return safe_text

        return "CardLens_contact"

    def _save_guestbook_note(self):
        """Save a guestbook note for the current profile."""
        if self.guestbook_text is None:
            return

        message = self.guestbook_text.get("1.0", "end").strip()
        if not message:
            self.status_text.set("Write a note first.")
            return

        notes = self._load_all_guestbook_notes()
        if notes is None:
            self.status_text.set(self.guestbook_load_error)
            return

        notes.append(
            {
                # profile_id keeps notes separate even if two profiles share a name.
                "profile_id": self._profile_key(),
                "profile": self._full_name(),
                "message": message,
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
        )

        try:
            config.GUESTBOOK_JSON.parent.mkdir(parents=True, exist_ok=True)
            text = json.dumps(notes, indent=2, ensure_ascii=False)
            config.GUESTBOOK_JSON.write_text(text, encoding="utf-8")
        except OSError as exc:
            self.status_text.set("Could not save note: " + str(exc))
            return

        self.guestbook_text.delete("1.0", "end")
        self.status_text.set("Note saved.")
        self.active_tab_name = "Guestbook"
        self._build_ui()

    def _load_all_guestbook_notes(self):
        """Load all notes from guestbook.json."""
        if not config.GUESTBOOK_JSON.exists():
            return []

        try:
            text = config.GUESTBOOK_JSON.read_text(encoding="utf-8")
            data = json.loads(text)
        except OSError as exc:
            self.guestbook_load_error = "Could not read guestbook.json: " + str(exc)
            return None
        except json.JSONDecodeError:
            self.guestbook_load_error = "guestbook.json is not valid JSON. Please fix it before saving notes."
            return None

        if isinstance(data, list):
            self.guestbook_load_error = ""
            return data

        self.guestbook_load_error = "guestbook.json must contain a list of notes."
        return None

    def _load_guestbook_notes(self):
        """Return only the guestbook notes for the current profile."""
        data = self._load_all_guestbook_notes()
        if data is None:
            return []

        notes = []
        current_profile_id = self._profile_key()
        current_name = self._full_name()

        for note in data:
            if not isinstance(note, dict):
                continue

            note_profile_id = str(note.get("profile_id", "")).strip()
            note_profile_name = str(note.get("profile", "")).strip()

            if note_profile_id:
                # New notes are matched by profile_id because it is stable.
                if note_profile_id == current_profile_id:
                    notes.append(note)
            elif note_profile_name == current_name:
                # This keeps older notes working if they only stored a name.
                notes.append(note)

        return notes

    def _full_name(self):
        """Return the full name for the current profile."""
        first_name = self.profile.get("first_name", "")
        last_name = self.profile.get("last_name", "")
        return (first_name + " " + last_name).strip()

    def _profile_key(self):
        """Return the stable key used for guestbook note ownership."""
        profile_id = str(self.profile.get("profile_id", "")).strip()
        if profile_id:
            return profile_id

        first_name = self.profile.get("first_name", "").strip().lower()
        last_name = self.profile.get("last_name", "").strip().lower()
        return (first_name + "_" + last_name).strip("_")

    def _initials(self):
        """Return initials for profiles without an avatar image."""
        first_name = self.profile.get("first_name", "")
        last_name = self.profile.get("last_name", "")

        text = ""
        if first_name:
            text = text + first_name[0].upper()
        if last_name:
            text = text + last_name[0].upper()
        if not text:
            text = "CL"

        return text


if __name__ == "__main__":
    # This block opens the demo profile when ui_display.py is run directly.
    from profile_loader import ProfileLoader

    loader = ProfileLoader()
    sample_profile = loader.get_profile("card_001")

    root = tk.Tk()
    app = ProfileDisplay(root)
    app.show_profile(sample_profile)
    root.mainloop()
