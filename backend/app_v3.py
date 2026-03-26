from flask import Flask, jsonify, request, redirect, session, send_from_directory, Response
from flask_cors import CORS
import threading
import parking_occupancy_v2 as parking_occupancy  # Use v2 occupancy logic
import reservation_manager_v2 as reservation_manager # Use v2 reservation logic
import wayfinding
import os
import webbrowser
from threading import Timer

# -------------------------------------------------
# PATH SETUP
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "../frontend")

# -------------------------------------------------
# APP SETUP
# -------------------------------------------------
app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=""
)

# Allow serving assets from frontend/assets
@app.route('/assets/<path:path>')
def send_assets(path):
    return send_from_directory(os.path.join(FRONTEND_DIR, 'assets'), path)

app.secret_key = "smart-parking-secret-key"
CORS(app)

# -------------------------------------------------
# STATIC USERS (DEMO AUTH)
# -------------------------------------------------
USERS = {
    "user@parking.com": {
        "password": "user123",
        "role": "user"
    },
    "admin@parking.com": {
        "password": "admin123",
        "role": "admin"
    }
}

# -------------------------------------------------
# INITIALIZE RESERVATION DATABASE
# -------------------------------------------------
reservation_manager.init_db()

# -------------------------------------------------
# SERVE LOGIN PAGE
# -------------------------------------------------
@app.route("/login.html")
def login_page():
    return send_from_directory(FRONTEND_DIR, "login.html")

# -------------------------------------------------
# LOGIN
# -------------------------------------------------
@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")

    if email in USERS and USERS[email]["password"] == password:
        session["logged_in"] = True
        session["email"] = email
        session["role"] = USERS[email]["role"]

        return redirect("/admin" if USERS[email]["role"] == "admin" else "/user")

    return """
    <h3>Invalid email or password</h3>
    <a href="/login.html">Go back to login</a>
    """, 401

# -------------------------------------------------
# LOGOUT
# -------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login.html")

# -------------------------------------------------
# USER PORTAL (PROTECTED)
# -------------------------------------------------
@app.route("/user")
def user_portal():
    if not session.get("logged_in") or session.get("role") != "user":
        return redirect("/login.html")

    return send_from_directory(FRONTEND_DIR, "user_v3.html")

# -------------------------------------------------
# ADMIN PORTAL (PROTECTED)
# -------------------------------------------------
@app.route("/admin")
def admin_portal():
    if not session.get("logged_in") or session.get("role") != "admin":
        return redirect("/login.html")

    return send_from_directory(FRONTEND_DIR, "admin_v2.html")

# -------------------------------------------------
# STATUS ENDPOINT (WITH TIMER + BILLING)
# -------------------------------------------------
@app.route("/status", methods=["GET"])
def get_status():
    reservation_manager.release_expired_reservations()
    active_reservations = reservation_manager.get_active_reservations()

    # Map slot_id -> reservation data
    reservation_map = {
        r["slot_id"]: r for r in active_reservations
    }

    slots = []
    # Ensure current_slot_status is populated
    if not parking_occupancy.current_slot_status:
         # Fallback if empty (e.g. CV not started yet)
         # Assuming we know num_slots from somewhere or just empty
         pass

    for i, detection_status in enumerate(parking_occupancy.current_slot_status):
        slot_id = i + 1

        final_status = detection_status
        remaining = None
        cost = None
        user_email = None

        if slot_id in reservation_map:
            if detection_status == "OCCUPIED":
                 final_status = "RESERVED_OCCUPIED" 
            else:
                 final_status = "RESERVED"
                 
            remaining = reservation_map[slot_id]["remaining_seconds"]
            cost = reservation_map[slot_id]["total_cost"]
            user_email = reservation_map[slot_id]["user_email"]

        slots.append({
            "id": slot_id,
            "status": final_status,
            "remaining_seconds": remaining,
            "total_cost": cost,
            "user_email": user_email
        })

    return jsonify({
        "slots": slots,
        "current_user": session.get("email")
    })

# -------------------------------------------------
# RESERVE SLOT (USER ONLY, WITH DURATION)
# -------------------------------------------------
@app.route("/reserve/<int:slot_id>", methods=["POST"])
def reserve_slot(slot_id):
    if not session.get("logged_in") or session.get("role") != "user":
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 403

    data = request.get_json()
    duration = data.get("duration")
    user_email = session.get("email")

    if duration not in [30, 60, 90, 120]:
        return jsonify({
            "success": False,
            "message": "Invalid duration"
        }), 400

    if parking_occupancy.current_slot_status[slot_id - 1] != "FREE":
         # Allow reserving if it's already reserved by THIS user? No, simplicity first.
         # But wait, if occupancy says "FREE", we can reserve.
         # We also need to check if it's already reserved in DB (handled by reserve_slot return False)
        pass

    # Check occupancy
    if parking_occupancy.current_slot_status[slot_id - 1] != "FREE":
         return jsonify({
            "success": False,
            "message": "Slot is physically occupied"
        }), 400

    success = reservation_manager.reserve_slot(slot_id, duration, user_email)

    if success:
        return jsonify({
            "success": True,
            "message": f"Slot {slot_id} reserved for {duration} minutes"
        })
    else:
        return jsonify({
            "success": False,
            "message": "Slot already reserved"
        }), 400

# -------------------------------------------------
# WAYFINDING ENDPOINT
# -------------------------------------------------
@app.route("/wayfinding/<int:slot_id>")
def get_wayfinding(slot_id):
    # Security: Allow if logged in? Or public?
    # Better to allow only if logged in + has reservation?
    # For demo, just check logged in.
    if not session.get("logged_in"):
        return "Unauthorized", 403
    
    # Optional: Check if user actually owns the reservation for this slot
    # But for demo simplicity, allow viewing any slot path
    
    image_bytes = wayfinding.generate_wayfinding_image(slot_id)
    
    if image_bytes:
        return Response(image_bytes, mimetype='image/jpeg')
    else:
        return "Not found or error generating image", 404

# -------------------------------------------------
# ROOT
# -------------------------------------------------
@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")

# -------------------------------------------------
# MAIN
# -------------------------------------------------
if __name__ == "__main__":
    # Auto-open browser
    Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:5001")).start()

    # Run Flask in a daemon thread so CV can run in main thread (required for GUI)
    flask_thread = threading.Thread(
        target=lambda: app.run(
            host="0.0.0.0",
            port=5001,
            debug=False,
            use_reloader=False
        ),
        daemon=True
    )
    flask_thread.start()

    # Run CV loop in main thread
    parking_occupancy.run()
