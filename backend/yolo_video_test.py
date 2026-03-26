import cv2
import torch
from ultralytics import YOLO

# -------- CONFIG --------
VIDEO_PATH = "/Users/vijaykumarbk/Desktop/smart-parking/videos/parking_lot.mp4"
CONF_THRESHOLD = 0.3
IMG_SIZE = 768          # VERY IMPORTANT
MAX_DET = 30            # LIMIT detections
# ------------------------

device = "mps" if torch.backends.mps.is_available() else "cpu"
print("Using device:", device)

model = YOLO("yolov8n.pt")
model.to(device)

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("❌ Cannot open video")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Resize frame (HUGE speed improvement)
    frame_resized = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))

    # Run YOLO (vehicle classes only)
    results = model(
        frame_resized,
        conf=CONF_THRESHOLD,
        imgsz=IMG_SIZE,
        max_det=MAX_DET,
        classes=[2, 3, 5, 7],  # car, motorcycle, bus, truck
        verbose=False
    )

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = box.conf[0]

            cv2.rectangle(
                frame_resized,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame_resized,
                f"vehicle {conf:.2f}",
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )

    cv2.imshow("YOLOv8 Vehicle Detection (Optimized)", frame_resized)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()