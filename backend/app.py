from flask import Flask, jsonify, request, redirect, session, send_from_directory
from flask_cors import CORS
import threading
import parking_occupancy as parking_occupancy
import reservation_manager
import os

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

    return send_from_directory(FRONTEND_DIR, "user.html")

# -------------------------------------------------
# ADMIN PORTAL (PROTECTED)
# -------------------------------------------------
@app.route("/admin")
def admin_portal():
    if not session.get("logged_in") or session.get("role") != "admin":
        return redirect("/login.html")

    return send_from_directory(FRONTEND_DIR, "admin.html")

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
    for i, detection_status in enumerate(parking_occupancy.current_slot_status):
        slot_id = i + 1

        final_status = detection_status
        remaining = None
        cost = None

        if slot_id in reservation_map:
            final_status = "RESERVED"
            remaining = reservation_map[slot_id]["remaining_seconds"]
            cost = reservation_map[slot_id]["total_cost"]

        slots.append({
            "id": slot_id,
            "status": final_status,
            "remaining_seconds": remaining,
            "total_cost": cost
        })

    return jsonify({"slots": slots})

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

    if duration not in [30, 60, 90, 120]:
        return jsonify({
            "success": False,
            "message": "Invalid duration"
        }), 400

    if parking_occupancy.current_slot_status[slot_id - 1] != "FREE":
        return jsonify({
            "success": False,
            "message": "Slot is not free"
        }), 400

    success = reservation_manager.reserve_slot(slot_id, duration)

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
# ROOT
# -------------------------------------------------
@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")

# -------------------------------------------------
# MAIN
# -------------------------------------------------
import webbrowser
from threading import Timer

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