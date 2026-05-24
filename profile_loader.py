"""
profile_loader.py

This file loads profile data from profiles.json.
It also checks that each profile page uses a supported page type.
"""

import json

import config


VALID_PAGE_TYPES = ["card", "text", "moments", "contact", "guestbook"]


class ProfileLoader:
    """Reads profile data from a JSON file and looks up profiles by card ID."""

    def __init__(self, json_path=config.PROFILES_JSON):
        """Store the JSON path and load profiles immediately."""
        self.json_path = json_path
        self.profiles = {}
        self.load()

    def load(self):
        """Read profiles from JSON and validate the result."""
        if not self.json_path.exists():
            raise FileNotFoundError(f"Profiles file not found: {self.json_path}")

        with open(self.json_path, "r", encoding="utf-8") as file:
            try:
                self.profiles = json.load(file)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Profiles JSON is not valid: {self.json_path}") from exc

        if not isinstance(self.profiles, dict):
            raise ValueError("Profiles JSON must contain a dictionary of profiles.")

        self._validate()

    def _validate(self):
        """Check that each profile has pages with supported page types."""
        for card_id, profile in self.profiles.items():
            if not isinstance(profile, dict):
                raise ValueError(f"Profile '{card_id}' must be a dictionary.")

            profile_id = profile.get("profile_id")
            if profile_id != card_id:
                raise ValueError(f"Profile '{card_id}' has mismatched profile_id.")

            self._require_string(profile, "first_name", card_id)
            self._require_string(profile, "last_name", card_id)
            self._require_string(profile, "bio", card_id)

            pages = profile.get("pages")
            if not isinstance(pages, list):
                raise ValueError(f"Profile '{card_id}' must have a list of pages.")

            for page_number, page in enumerate(pages):
                if not isinstance(page, dict):
                    raise ValueError(
                        f"Profile '{card_id}', page {page_number}: page must be a dictionary."
                    )

                page_type = page.get("type")
                if page_type not in VALID_PAGE_TYPES:
                    raise ValueError(
                        f"Profile '{card_id}', page {page_number}: "
                        f"invalid type '{page_type}'."
                    )

                self._validate_page(card_id, page_number, page)

    def _require_string(self, data, key, card_id):
        """Check that one profile field is stored as text."""
        if not isinstance(data.get(key, ""), str):
            raise ValueError(f"Profile '{card_id}' field '{key}' must be text.")

    def _validate_page(self, card_id, page_number, page):
        """Check the basic shape of one profile page."""
        page_type = page.get("type")

        if page_type in ["card", "contact"]:
            links = page.get("links", [])
            if not isinstance(links, list):
                raise ValueError(
                    f"Profile '{card_id}', page {page_number}: links must be a list."
                )

            for link_number, link in enumerate(links):
                if not isinstance(link, dict):
                    raise ValueError(
                        f"Profile '{card_id}', page {page_number}, link {link_number}: "
                        "link must be a dictionary."
                    )

                for key in ["label", "value", "url"]:
                    if not isinstance(link.get(key, ""), str):
                        raise ValueError(
                            f"Profile '{card_id}', page {page_number}, link {link_number}: "
                            f"{key} must be text."
                        )

        if page_type == "text":
            if not isinstance(page.get("content", ""), str):
                raise ValueError(
                    f"Profile '{card_id}', page {page_number}: content must be text."
                )

        if page_type == "moments":
            if not isinstance(page.get("image", ""), str):
                raise ValueError(
                    f"Profile '{card_id}', page {page_number}: image must be text."
                )

    def get_profile(self, card_id):
        """Return one profile by card ID."""
        return self.profiles.get(card_id)

    def all_card_ids(self):
        """Return all saved card IDs."""
        return list(self.profiles.keys())

if __name__ == "__main__":
    # This block is only for checking profile loading from the terminal.
    loader = ProfileLoader()
    print("Loaded profiles:", loader.all_card_ids())
