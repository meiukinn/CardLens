"""
card_recognition.py

This file contains the QR recognition logic for CardLens.
The QR code stores a profile ID such as CARDLENS:card_001.
After decoding, the profile ID is used to load the matching profile.
"""

from pathlib import Path
import time

import cv2

import config


class CardRecognizer:
    """Recognizes a CardLens profile ID from a QR code."""

    def __init__(self):
        """Create the OpenCV QR detector and store the last scan result."""
        self.detector = cv2.QRCodeDetector()
        self.last_payload = ""
        self.last_status = ""

    def recognize_from_image(self, image_path):
        """Read a still image and try to find a CardLens QR code."""
        if not image_path.exists():
            print(f"[Error] Image not found: {image_path}")
            return None

        image = cv2.imread(str(image_path))
        if image is None:
            print(f"[Error] Could not read image: {image_path}")
            return None

        profile_id = self._decode_qr(image)
        if profile_id:
            self.last_status = "recognized"
        else:
            self.last_status = "not_found"

        return profile_id

    def recognize_from_webcam(self):
        """Open the webcam and scan frames until a QR code is found or cancelled."""
        self.last_status = ""

        # OpenCV reads webcam frames through VideoCapture.
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

        if not cap.isOpened():
            print("[Error] Could not open webcam.")
            self.last_status = "error"
            return None

        found_id = None
        window_name = "CardLens - press Q or Esc to quit"
        start_time = time.monotonic()

        try:
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

            while True:
                # Read one frame and try to decode a QR code from it.
                ok, frame = cap.read()
                if not ok:
                    print("[Error] Could not read webcam frame.")
                    self.last_status = "error"
                    break

                profile_id = self._decode_qr(frame)
                if profile_id:
                    label = f"Detected: {profile_id}"
                else:
                    label = "Looking for a CardLens QR code..."

                # The text overlay gives the user live feedback during scanning.
                cv2.putText(
                    frame,
                    label,
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (0, 255, 0),
                    2,
                )
                cv2.putText(
                    frame,
                    "Press Q / Esc or close this window to cancel",
                    (10, 62),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (0, 255, 0),
                    1,
                )
                cv2.imshow(window_name, frame)

                if profile_id is not None:
                    found_id = profile_id
                    self.last_status = "recognized"
                    cv2.waitKey(config.WEBCAM_DETECTION_PAUSE_MS)
                    break

                key = cv2.waitKey(20) & 0xFF
                if key in (ord("q"), 27):
                    self.last_status = "cancelled"
                    break

                try:
                    # This lets the user close the OpenCV window directly.
                    visible = cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE)
                    if visible < 1:
                        self.last_status = "cancelled"
                        break
                except cv2.error:
                    self.last_status = "cancelled"
                    break

                elapsed_time = time.monotonic() - start_time
                if elapsed_time > config.WEBCAM_TIMEOUT_SECONDS:
                    print("[Info] Webcam scan timed out.")
                    self.last_status = "timeout"
                    break
        except cv2.error as exc:
            print(f"[Error] Webcam display failed: {exc}")
            self.last_status = "error"
        finally:
            cap.release()
            try:
                cv2.destroyAllWindows()
            except cv2.error:
                pass

        return found_id

    def _decode_qr(self, image):
        """Try multiple image versions and return the first valid profile ID."""
        candidates = self._qr_candidates(image)
        for candidate in candidates:
            payload = self._decode_candidate(candidate)
            if payload:
                self.last_payload = payload
                return self._profile_id_from_payload(payload)

        self.last_payload = ""
        return None

    def _decode_candidate(self, image):
        """Decode one image candidate with OpenCV QR detection."""
        payload, points, straight_qrcode = self.detector.detectAndDecode(image)
        payload = payload.strip()
        if payload:
            return payload

        try:
            ok, decoded_info, points, straight_qrcode = self.detector.detectAndDecodeMulti(image)
        except cv2.error:
            return ""

        if not ok:
            return ""

        for item in decoded_info:
            item = item.strip()
            if item:
                return item

        return ""

    def _qr_candidates(self, image):
        """Create QR detection candidates to improve recognition reliability."""
        if len(image.shape) == 3:
            # QR detection works better on grayscale because color is not needed.
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # CLAHE improves local contrast when the card is under uneven lighting.
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)

        # A small blur reduces camera noise before thresholding.
        blurred = cv2.GaussianBlur(clahe, (3, 3), 0)

        # Adaptive thresholding helps when the QR code is dark in some areas.
        threshold = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            3,
        )

        # Each candidate handles a different lighting or contrast problem.
        base_candidates = [image, gray, clahe, threshold]
        all_candidates = []
        for candidate in base_candidates:
            for scale in config.QR_DETECTION_SCALES:
                if scale == 1.0:
                    all_candidates.append(candidate)
                else:
                    # Enlarged candidates can help OpenCV read small QR codes.
                    resized = cv2.resize(
                        candidate,
                        None,
                        fx=scale,
                        fy=scale,
                        interpolation=cv2.INTER_CUBIC,
                    )
                    all_candidates.append(resized)

        return all_candidates

    def _profile_id_from_payload(self, payload):
        """Convert a QR payload into the plain profile ID used in profiles.json."""
        payload = payload.strip()
        if payload.startswith(config.QR_PREFIX):
            payload = payload[len(config.QR_PREFIX):].strip()

        if payload:
            return payload

        return None


if __name__ == "__main__":
    # This block is only for quick manual testing of QR recognition.
    recognizer = CardRecognizer()
    if config.DEFAULT_DEMO_IMAGE.exists():
        result = recognizer.recognize_from_image(config.DEFAULT_DEMO_IMAGE)
        print("Default demo result:", result)
    else:
        print("No default demo image found.")
