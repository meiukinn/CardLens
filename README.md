<div align="center">

# CardLens

### QR-based physical card recognition for digital profile display

CardLens is a Python desktop prototype that reads a QR code from a physical card design, loads the matching profile from local JSON data, and displays it as a clean interactive profile card.

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/UI-Tkinter%20%2B%20ttk-0B6EFD)
![OpenCV](https://img.shields.io/badge/OpenCV-QR%20Detection-5C3EE8?logo=opencv&logoColor=white)
![Pillow](https://img.shields.io/badge/Images-Pillow-2B6CB0)
![Theme](https://img.shields.io/badge/Theme-Azure%20ttk%20(MIT)-111827)

<img src="assets/demo_cards/cardlens_product_showcase_v10.png" alt="CardLens product showcase" width="920">

</div>

---

## Overview

CardLens connects a printed card with a richer digital profile.

The current prototype uses a QR code as the recognition marker. This keeps the demo stable for classroom testing because it works with either a webcam or an image file, without requiring special lighting or a printed card to be available.

```text
Card image or webcam frame
        |
        v
OpenCV QR recognition
        |
        v
profile_id
        |
        v
data/profiles.json
        |
        v
Tkinter profile display
```

## What It Does

- Scans a CardLens QR code from an image file or webcam.
- Opens the matching profile from `data/profiles.json`.
- Displays profile information in a tabbed Tkinter UI.
- Lets a user create a new CardLens profile.
- Generates a QR code for the new profile.
- Supports an optional About page visual from built-in choices or a custom icon image.
- Supports an optional showcase image and showcase description.
- Supports optional extra contact links such as GitHub, Instagram, WhatsApp, WeChat, TikTok, Xiaohongshu, and personal websites.
- Adds a Contact tab automatically when a profile has more than three contact links.
- Lets a user save contact details as a `.vcf` vCard.
- Saves guestbook notes per profile in `data/guestbook.json`.
- Lets a user delete saved local profiles.
- Reveals the main profile content with a small Tkinter `after()` animation.

## Quick Start

Install the required libraries:

```bash
pip install -r requirements.txt
```

Run the interactive menu:

```bash
python main.py
```

Run the project check before submission:

```bash
python run_check.py
```

## Run Modes

Interactive menu:

```bash
python main.py
```

Recognize a card from an image:

```bash
python main.py --image assets/demo_cards/card_001_qr_front.png
```

Other included demo card images:

```bash
python main.py --image assets/demo_cards/card_003_qr_front.png
python main.py --image assets/demo_cards/card_004_qr_front.png
```

Recognize a card from webcam:

```bash
python main.py --webcam
```

Create a new CardLens profile:

```bash
python main.py --create
```

Delete a saved local profile:

```bash
python main.py --delete
```

## Main Features

### QR Recognition

CardLens uses OpenCV's `QRCodeDetector` to read a profile ID from a QR code on the card. The payload must be a CardLens ID such as `CARDLENS:card_001` or `card_001`, so ordinary website QR codes are not treated as profile IDs.

### Profile Creation

Creator mode lets the user enter profile details, choose an optional avatar, choose an optional About page visual, choose an optional showcase image, write an optional showcase description, add optional contact accounts, and generate a new QR code. The QR code can then be added to a self-designed physical business card.

If a user enters more than three contact links, the creator keeps up to three main links on the Profile tab and places the remaining links on a Contact tab. Each contact field has a Main checkbox so the user can choose which contacts appear first.

For most social platforms, users can enter short account names instead of full URLs. For example, entering `kinn.meiu` in the Instagram field becomes an Instagram profile link internally, while the UI only shows the platform name. TikTok and Xiaohongshu use URL fields, and the program adds `https://www.` if the user leaves it out.

### Digital Profile UI

The recognized profile opens in a Tkinter window using standard `ttk` widgets and the Azure ttk theme. The profile includes:

- Profile tab
- About tab
- Optional Showcase tab
- Optional Contact tab
- Guestbook tab

The main profile tab uses a small reveal animation made with Tkinter's `after()` method. This keeps the animation simple and reliable.

### Guestbook

Each profile has its own saved notes. Notes are stored locally in `data/guestbook.json` and displayed in the Guestbook tab.

### Contact Export

The Save Contact button exports basic contact details as a `.vcf` file. This can be opened by common contact apps.

## Project Structure

```text
CardLens/
+-- main.py
+-- card_creator.py
+-- card_recognition.py
+-- profile_loader.py
+-- ui_display.py
+-- window_utils.py
+-- config.py
+-- run_check.py
+-- requirements.txt
+-- README.md
+-- data/
|   +-- profiles.json
|   +-- guestbook.json
+-- assets/
|   +-- azure_ttk_theme/
|   +-- demo_cards/
|   +-- qr_codes/
|   +-- avatars/
|   +-- about_visuals/
|   +-- highlights/
|   +-- icons/
```

## Technical Highlights

- `Tkinter` and `ttk` for the desktop interface.
- `OpenCV` for QR code recognition from images and webcam frames.
- `Pillow` for loading and resizing profile images.
- `qrcode` for generating profile QR codes.
- `JSON` for storing profile data and guestbook notes.
- Object-oriented structure for recognition and UI display classes.
- Lightweight UI animation with Tkinter `after()`.
- Basic error handling for missing files, invalid JSON, unknown profile IDs, and webcam cancellation.

## Advanced Concepts Used

This project applies several programming concepts from COMP9001:

- GUI event handling
- File input and output
- JSON data storage
- Image processing
- Third-party library integration
- Functions and classes
- Simple animation timing with Tkinter `after()`
- Validation and error handling

## Scope Adjustment

The original concept described recognizing a predefined physical card. In this submitted prototype, the recognition is implemented through an embedded QR code on the card design.

This is an intentional scope choice. QR recognition is more reliable for a short classroom demo and allows tutors to test the project using either the included demo image or their own webcam.

Future versions could replace or extend the QR marker with visual card-art recognition, such as a custom logo marker or ring-code pattern.

## Known Limitations

- QR detection requires a clear and readable QR code.
- Webcam results depend on camera quality, lighting, and distance.
- The prototype recognizes the QR marker, not the full printed card artwork.
- Profiles must exist in `data/profiles.json` before they can be opened.
- Data is stored locally and is not synced online.

## Credits

CardLens application code, profile creation, QR recognition flow, JSON storage, and profile UI logic were implemented for this project.

This project uses the open-source Azure ttk theme by rdbende under the MIT License. The theme files are stored in `assets/azure_ttk_theme/`.

## Author

Zhiheng Jin  
COMP9001 Final Project
