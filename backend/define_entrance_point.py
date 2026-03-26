import cv2
import pickle
import os

VIDEO_PATH = "videos/parking_lot.mp4"
ENTRANCE_FILE = "backend/entrance.pkl"

if not os.path.exists(VIDEO_PATH) and os.path.exists("../videos/parking_lot.mp4"):
    VIDEO_PATH = "../videos/parking_lot.mp4"

cap = cv2.VideoCapture(VIDEO_PATH)
ret, frame = cap.read()
cap.release()

if not ret:
    print("❌ Failed to read video frame")
    exit()

IMG_SIZE = 768
frame = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))

entrance_point = None

def mouse_callback(event, x, y, flags, param):
    global entrance_point

    if event == cv2.EVENT_LBUTTONDOWN:
        entrance_point = (x, y)
        print(f"Entrance set to: {entrance_point}")

cv2.namedWindow("Define Entrance Point")
cv2.setMouseCallback("Define Entrance Point", mouse_callback)

print("Click on the image to set the entrance point.")
print("Press 's' to save and exit.")
print("Press 'q' to quit without saving.")

while True:
    display = frame.copy()

    if entrance_point:
        # Draw the entrance point
        cv2.circle(display, entrance_point, 10, (0, 0, 255), -1)
        cv2.putText(display, "ENTRANCE", (entrance_point[0] + 15, entrance_point[1]), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("Define Entrance Point", display)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("s"):
        if entrance_point:
            with open(ENTRANCE_FILE, "wb") as f:
                pickle.dump(entrance_point, f)
            print(f"✅ Entrance point saved to {ENTRANCE_FILE}")
        else:
            print("⚠️ No entrance point selected!")
        break

    elif key == ord("q"):
        print("❌ Exiting without saving")
        break

cv2.destroyAllWindows()
