from flask import Flask, jsonify
from flask_cors import CORS
import threading
import parking_occupancy
import reservation_manager

app = Flask(__name__)
CORS(app)  # Allow frontend to access backend

# -------------------------------------------------
# Initialize reservation database
# -------------------------------------------------
reservation_manager.init_db()

# -------------------------------------------------
# STATUS ENDPOINT (Detection + Reservation)
# -------------------------------------------------
@app.route("/status", methods=["GET"])
def get_status():
    """
    Returns final parking slot status
    (FREE / OCCUPIED / RESERVED)
    """
    # Remove expired reservations
    reservation_manager.release_expired_reservations()

    reserved_slots = reservation_manager.get_reserved_slots()
    slots = []

    for i, detection_status in enumerate(parking_occupancy.current_slot_status):
        slot_id = i + 1

        final_status = detection_status
        if slot_id in reserved_slots:
            final_status = "RESERVED"

        slots.append({
            "id": slot_id,
            "status": final_status
        })

    return jsonify({"slots": slots})


# -------------------------------------------------
# RESERVE SLOT ENDPOINT
# -------------------------------------------------
@app.route("/reserve/<int:slot_id>", methods=["POST"])
def reserve_slot(slot_id):
    """
    Reserve a FREE parking slot
    """
    reservation_manager.release_expired_reservations()

    # Safety check
    if slot_id < 1 or slot_id > len(parking_occupancy.current_slot_status):
        return jsonify({
            "success": False,
            "message": "Invalid slot ID"
        }), 400

    # Slot must be free according to detection
    if parking_occupancy.current_slot_status[slot_id - 1] != "FREE":
        return jsonify({
            "success": False,
            "message": "Slot is not free"
        }), 400

    success = reservation_manager.reserve_slot(slot_id)

    if success:
        return jsonify({
            "success": True,
            "message": f"Slot {slot_id} reserved successfully"
        })
    else:
        return jsonify({
            "success": False,
            "message": "Slot already reserved"
        }), 400


# -------------------------------------------------
# ROOT ENDPOINT
# -------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Smart Parking Backend is running",
        "endpoints": {
            "/status": "Get parking slot occupancy",
            "/reserve/<slot_id>": "Reserve a FREE parking slot"
        }
    })


# -------------------------------------------------
# MAIN
# -------------------------------------------------
if __name__ == "__main__":
    # Start parking detection logic in background thread
    backend_thread = threading.Thread(
        target=parking_occupancy.run,
        daemon=True
    )
    backend_thread.start()

    # Start Flask server
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )