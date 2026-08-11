"""Optional camera-based gate scanner, for sites without a USB HID
barcode scanner. Not used by default -- the primary v1 hardware path is
a USB scanner typing into the kiosk web page (see
app/templates/gate/scan_kiosk.html). Kept as a documented fallback
because a camera is far more sensitive to outdoor daylight, glare, rain
and cold, and adds a heavier dependency stack (OpenCV + pyzbar).

Requires: pip install -r requirements-dev.txt (opencv-python-headless, pyzbar)
Requires a system zbar library, e.g. `sudo apt install libzbar0`.

Usage:
    python scanner/camera_scan.py --url http://localhost:5000/gate/scan --camera 0
"""
import argparse
import time

import cv2
import requests
from pyzbar.pyzbar import decode


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:5000/gate/scan")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument(
        "--cooldown", type=float, default=2.0, help="seconds between posting the same code again"
    )
    args = parser.parse_args()

    capture = cv2.VideoCapture(args.camera)
    if not capture.isOpened():
        raise SystemExit(f"Kunde inte öppna kamera {args.camera}")

    last_sent = {}
    print(f"Läser QR-koder från kamera {args.camera}, skickar till {args.url}. Ctrl+C för att avsluta.")

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                time.sleep(0.2)
                continue

            for barcode in decode(frame):
                token = barcode.data.decode("utf-8", errors="ignore")
                now = time.monotonic()
                if now - last_sent.get(token, 0) < args.cooldown:
                    continue
                last_sent[token] = now
                try:
                    payload = {"token": token, "source": "gate-scanner-camera"}
                    response = requests.post(args.url, data=payload, timeout=5)
                    print(response.json())
                except requests.RequestException as exc:
                    print(f"Fel vid sändning: {exc}")

            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        capture.release()


if __name__ == "__main__":
    main()
