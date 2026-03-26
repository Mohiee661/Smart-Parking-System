import sqlite3
import time
import os

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "reservations_v2.db")

PRICE_PER_HOUR = 20  # ₹20 per hour

# -------------------------------------------------
# INIT DATABASE
# -------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            slot_id INTEGER PRIMARY KEY,
            start_time INTEGER,
            end_time INTEGER,
            price_per_hour INTEGER,
            total_cost REAL,
            user_email TEXT
        )
    """)

    conn.commit()
    conn.close()


# -------------------------------------------------
# RESERVE SLOT WITH DURATION
# -------------------------------------------------
def reserve_slot(slot_id, duration_minutes, user_email):
    """
    duration_minutes: 30, 60, 90, 120
    user_email: email of the user booking the slot
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    now = int(time.time())
    duration_seconds = duration_minutes * 60
    end_time = now + duration_seconds

    total_cost = (PRICE_PER_HOUR * duration_minutes) / 60

    try:
        cur.execute("""
            INSERT INTO reservations
            (slot_id, start_time, end_time, price_per_hour, total_cost, user_email)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            slot_id,
            now,
            end_time,
            PRICE_PER_HOUR,
            total_cost,
            user_email
        ))

        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False

    conn.close()
    return success


# -------------------------------------------------
# RELEASE EXPIRED RESERVATIONS
# -------------------------------------------------
def release_expired_reservations():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    now = int(time.time())
    cur.execute(
        "DELETE FROM reservations WHERE end_time <= ?",
        (now,)
    )

    conn.commit()
    conn.close()


# -------------------------------------------------
# GET ALL ACTIVE RESERVATIONS
# -------------------------------------------------
def get_active_reservations():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT slot_id, start_time, end_time, total_cost, user_email
        FROM reservations
    """)

    rows = cur.fetchall()
    conn.close()

    reservations = []
    now = int(time.time())

    for slot_id, start, end, cost, email in rows:
        remaining = max(0, end - now)

        reservations.append({
            "slot_id": slot_id,
            "start_time": start,
            "end_time": end,
            "remaining_seconds": remaining,
            "total_cost": cost,
            "user_email": email
        })

    return reservations
# -------------------------------------------------
# CHECK IF SLOT IS RESERVED
# -------------------------------------------------
def is_reserved(slot_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "SELECT 1 FROM reservations WHERE slot_id = ?",
        (slot_id,)
    )

    result = cur.fetchone()
    conn.close()

    return result is not None
