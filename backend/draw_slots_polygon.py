import cv2
import pickle
import numpy as np

VIDEO_PATH = "videos/parking_lot.mp4"
SLOTS_FILE = "backend/parking_slots.pkl"


cap = cv2.VideoCapture(VIDEO_PATH)
ret, frame = cap.read()
cap.release()

if not ret:
    print("❌ Failed to read video frame")
    exit()

IMG_SIZE = 768
frame = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))

parking_slots = []
current_polygon = []

def mouse_callback(event, x, y, flags, param):
    global current_polygon, parking_slots

    if event == cv2.EVENT_LBUTTONDOWN:
        current_polygon.append((x, y))
        print(f"Point added: {(x, y)}")

        if len(current_polygon) == 4:
            parking_slots.append(current_polygon.copy())
            print(f"Slot added: {current_polygon}")
            current_polygon.clear()

cv2.namedWindow("Draw Parking Slots (Polygon)")
cv2.setMouseCallback("Draw Parking Slots (Polygon)", mouse_callback)

while True:
    display = frame.copy()

    # Draw completed slots
    for slot in parking_slots:
        pts = np.array(slot, np.int32)
        cv2.polylines(display, [pts], True, (0, 255, 0), 2)

    # Draw current polygon being clicked
    if len(current_polygon) > 0:
        pts = np.array(current_polygon, np.int32)
        cv2.polylines(display, [pts], False, (255, 255, 0), 2)

    cv2.imshow("Draw Parking Slots (Polygon)", display)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("s"):
        with open(SLOTS_FILE, "wb") as f:
            pickle.dump(parking_slots, f)
        print(f"✅ Slots saved to {SLOTS_FILE}")
        break

    elif key == ord("q"):
        print("❌ Exiting without saving")
        break

cv2.destroyAllWindows()