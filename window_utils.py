"""
window_utils.py

This file contains small helper functions for Tkinter window sizing.
"""


def get_screen_size(window):
    """Return the current screen size for a Tkinter window."""
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    return screen_width, screen_height


def fit_size_to_screen(window, width, height, margin=60):
    """Reduce a window size if it is larger than the screen."""
    screen_width, screen_height = get_screen_size(window)

    max_width = screen_width - margin
    max_height = screen_height - margin

    if max_width < 320:
        max_width = screen_width
    if max_height < 320:
        max_height = screen_height

    final_width = width
    final_height = height

    if final_width > max_width:
        final_width = max_width
    if final_height > max_height:
        final_height = max_height

    return int(final_width), int(final_height)


def center_window(window, width, height, margin=60):
    """Set a Tkinter window size and place it near the center of the screen."""
    final_width, final_height = fit_size_to_screen(window, width, height, margin)
    screen_width, screen_height = get_screen_size(window)

    x = int((screen_width - final_width) / 2)
    y = int((screen_height - final_height) / 2)

    if x < 0:
        x = 0
    if y < 0:
        y = 0

    window.geometry(f"{final_width}x{final_height}+{x}+{y}")
    return final_width, final_height
