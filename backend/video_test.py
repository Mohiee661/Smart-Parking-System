import cv2

VIDEO_PATH = "/Users/vijaykumarbk/Desktop/smart-parking/videos/parking_lot.mp4"
cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("❌ Error: Cannot open video file")
    exit()

# Get video properties
fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

print(f"✅ Video loaded successfully")
print(f"FPS: {fps}")
print(f"Resolution: {width} x {height}")

while True:
    ret, frame = cap.read()

    if not ret:
        print("✅ End of video reached")
        break

    cv2.imshow("Parking Video Test", frame)

    # Press 'q' to quit early
    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()