import cv2
import pickle
import numpy as np
import torch
from ultralytics import YOLO

# =========================================================
# GLOBAL STATE (used by Flask)
# =========================================================
current_slot_status = []

# =========================================================
# CONFIG
# =========================================================
VIDEO_PATH = "videos/parking_lot.mp4"
SLOTS_FILE = "backend/parking_slots.pkl"

IMG_SIZE = 768
CONF_THRESHOLD = 0.3
MAX_DET = 30
OVERLAP_THRESHOLD = 0.15

SMOOTHING_FRAMES = 15   # temporal memory
# =========================================================


def polygon_intersection_area(poly1, poly2):
    """
    Returns intersection area between two convex polygons
    """
    poly1 = poly1.astype(np.int32)
    poly2 = poly2.astype(np.int32)
    area, _ = cv2.intersectConvexConvex(poly1, poly2)
    return area


# =========================================================
# LOAD PARKING SLOTS
# =========================================================
with open(SLOTS_FILE, "rb") as f:
    parking_slots = pickle.load(f)

num_slots = len(parking_slots)
print(f"Loaded {num_slots} parking slots")

# Temporal memory per slot
slot_memory = [0] * num_slots

# =========================================================
# DEVICE & MODEL
# =========================================================
device = "mps" if torch.backends.mps.is_available() else "cpu"
print("Using device:", device)

model = YOLO("yolov8n.pt")
model.to(device)

# =========================================================
# VIDEO CAPTURE
# =========================================================
cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    print("❌ Cannot open video")
    exit()


# =========================================================
# MAIN LOOP (CALLED BY FLASK)
# =========================================================
def run():
    global current_slot_status

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))

        # Track detections in this frame
        detected_this_frame = [False] * num_slots

        # YOLO inference (cars only)
        results = model(
            frame,
            conf=CONF_THRESHOLD,
            imgsz=IMG_SIZE,
            max_det=MAX_DET,
            classes=[2],  # car
            verbose=False
        )

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                # Draw car bounding box (debug)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)

                # Convert car box to polygon
                car_polygon = np.array([
                    [x1, y1],
                    [x2, y1],
                    [x2, y2],
                    [x1, y2]
                ], np.int32)

                # Check overlap with parking slots
                for i, slot in enumerate(parking_slots):
                    slot_polygon = np.array(slot, np.int32)

                    inter_area = polygon_intersection_area(
                        car_polygon, slot_polygon
                    )
                    slot_area = cv2.contourArea(slot_polygon)

                    if slot_area > 0 and (inter_area / slot_area) >= OVERLAP_THRESHOLD:
                        detected_this_frame[i] = True

        # =================================================
        # TEMPORAL SMOOTHING
        # =================================================
        for i in range(num_slots):
            if detected_this_frame[i]:
                slot_memory[i] = SMOOTHING_FRAMES
            else:
                slot_memory[i] = max(0, slot_memory[i] - 1)

        slot_status = [
            "OCCUPIED" if slot_memory[i] > 0 else "FREE"
            for i in range(num_slots)
        ]

        # 🔑 Update shared state for Flask
        current_slot_status = slot_status.copy()

        # =================================================
        # VISUALIZATION
        # =================================================
        for i, slot in enumerate(parking_slots):
            polygon = np.array(slot, np.int32)
            color = (0, 255, 0) if slot_status[i] == "FREE" else (0, 0, 255)

            cv2.polylines(frame, [polygon], True, color, 2)

            cx = int(np.mean(polygon[:, 0]))
            cy = int(np.mean(polygon[:, 1]))

            cv2.putText(
                frame,
                f"Slot {i+1}: {slot_status[i]}",
                (cx - 40, cy),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                color,
                2
            )

        cv2.imshow("Smart Parking – Backend", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()