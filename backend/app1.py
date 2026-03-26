from flask import Flask, jsonify, request, redirect, session, send_from_directory
from flask_cors import CORS
import threading
import parking_occupancy
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
# SERVE MAIN DASHBOARD
# -------------------------------------------------
@app.route("/dashboard")
def dashboard():
    return send_from_directory(FRONTEND_DIR, "index.html")

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

        if session["role"] == "admin":
            return redirect("/admin")
        else:
            return redirect("/user")

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

    return send_from_directory(FRONTEND_DIR, "index.html")

# -------------------------------------------------
# ADMIN PORTAL (PROTECTED)
# -------------------------------------------------
@app.route("/admin")
def admin_portal():
    if not session.get("logged_in") or session.get("role") != "admin":
        return redirect("/login.html")

    return """
    <h2>Owner Dashboard</h2>
    <p>Welcome, ADMIN</p>
    <p>This dashboard will show analytics and revenue.</p>
    <a href="/logout">Logout</a>
    """

# -------------------------------------------------
# STATUS ENDPOINT (Detection + Reservation)
# -------------------------------------------------
@app.route("/status", methods=["GET"])
def get_status():
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
# RESERVE SLOT (USER ONLY)
# -------------------------------------------------
@app.route("/reserve/<int:slot_id>", methods=["POST"])
def reserve_slot(slot_id):
    if not session.get("logged_in") or session.get("role") != "user":
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 403

    reservation_manager.release_expired_reservations()

    if slot_id < 1 or slot_id > len(parking_occupancy.current_slot_status):
        return jsonify({
            "success": False,
            "message": "Invalid slot ID"
        }), 400

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
# ROOT
# -------------------------------------------------
@app.route("/")
def home():
    return redirect("/login.html")

# -------------------------------------------------
# MAIN
# -------------------------------------------------
if __name__ == "__main__":
    backend_thread = threading.Thread(
        target=parking_occupancy.run,
        daemon=True
    )
    backend_thread.start()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )