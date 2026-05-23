"""
profile_loader.py

This file loads profile data from profiles.json.
It also checks that each profile page uses a supported page type.
"""

import json

import config


VALID_PAGE_TYPES = ["card", "text", "moments", "guestbook"]


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
            if "pages" not in profile:
                raise ValueError(f"Profile '{card_id}' has no 'pages' field.")

            for page_number, page in enumerate(profile["pages"]):
                page_type = page.get("type")
                if page_type not in VALID_PAGE_TYPES:
                    raise ValueError(
                        f"Profile '{card_id}', page {page_number}: "
                        f"invalid type '{page_type}'."
                    )

    def get_profile(self, card_id):
        """Return one profile by card ID."""
        return self.profiles.get(card_id)

    def all_card_ids(self):
        """Return all saved card IDs."""
        return list(self.profiles.keys())

    def get_display_name(self, card_id):
        """Return the best display name for one profile."""
        profile = self.get_profile(card_id)
        if not profile:
            return ""

        display_name = profile.get("display_name")
        if display_name:
            return display_name

        preferred_name = profile.get("preferred_name")
        if preferred_name:
            return preferred_name

        first_name = profile.get("first_name", "")
        last_name = profile.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip()
        return full_name


if __name__ == "__main__":
    # This block is only for checking profile loading from the terminal.
    loader = ProfileLoader()
    print("Loaded profiles:", loader.all_card_ids())
