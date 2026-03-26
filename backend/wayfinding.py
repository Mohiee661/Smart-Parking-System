import cv2
import pickle
import numpy as np
import os

VIDEO_PATH = "videos/parking_lot.mp4"
SLOTS_FILE = "backend/parking_slots.pkl"
ENTRANCE_FILE = "backend/entrance.pkl"
IMG_SIZE = 768

# Adjust paths if running from backend dir
if not os.path.exists(VIDEO_PATH) and os.path.exists("../videos/parking_lot.mp4"):
    VIDEO_PATH = "../videos/parking_lot.mp4"

def generate_wayfinding_image(slot_id):
    """
    Generates an image showing the path from Entrance to the specified Slot ID.
    Returns the encoded image bytes (JPEG).
    """
    
    # 1. Load Resources
    if not os.path.exists(ENTRANCE_FILE):
        return None  # Entrance not defined
    
    if not os.path.exists(SLOTS_FILE):
        return None
        
    with open(ENTRANCE_FILE, "rb") as f:
        entrance_point = pickle.load(f)
        
    with open(SLOTS_FILE, "rb") as f:
        parking_slots = pickle.load(f)
        
    # Check if slot_id is valid (1-based index)
    if slot_id < 1 or slot_id > len(parking_slots):
        return None
    
    # 2. Get Background Frame
    cap = cv2.VideoCapture(VIDEO_PATH)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        return None
        
    frame = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
    
    # 3. Calculate Target Slot Center
    # slot_id is 1-based, list is 0-based
    target_slot_poly = np.array(parking_slots[slot_id - 1], np.int32)
    
    M = cv2.moments(target_slot_poly)
    if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        slot_center = (cx, cy)
    else:
        # Fallback if area is zero (unlikely)
        slot_center = tuple(target_slot_poly[0])

    # 4. Draw Visualization
    overlay = frame.copy()
    
    # Dim the background to make the path pop
    # cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame) but let's just draw bright on top
    
    # Draw all slots faintly
    for i, slot in enumerate(parking_slots):
        poly = np.array(slot, np.int32)
        color = (200, 200, 200)
        thickness = 1
        if i + 1 == slot_id:
            color = (0, 255, 0) # Target slot Green
            thickness = 3
        
        cv2.polylines(frame, [poly], True, color, thickness)
        
    # Draw Entrance
    cv2.circle(frame, entrance_point, 12, (0, 0, 255), -1) # Red dot
    cv2.putText(frame, "ENTRANCE", (entrance_point[0] + 15, entrance_point[1]), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)
    
    # Draw Arrow from Entrance to Slot Center
    cv2.arrowedLine(frame, entrance_point, slot_center, (0, 255, 255), 4, cv2.LINE_AA, 0, 0.05)
    
    # Draw Target Label
    cv2.circle(frame, slot_center, 8, (0, 255, 0), -1)
    cv2.putText(frame, f"SLOT {slot_id}", (slot_center[0] - 40, slot_center[1] - 15), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)

    # 5. Encode to JPEG
    ret, buffer = cv2.imencode('.jpg', frame)
    if ret:
        return buffer.tobytes()
    else:
        return None
