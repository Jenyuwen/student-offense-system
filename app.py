from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# ================= DATABASE =================
def connect_db():
    return sqlite3.connect("/data/database.db")

def init_db():
    conn = connect_db()
    cur = conn.cursor()

    # OFFENSE TABLE
    cur.execute('''
    CREATE TABLE IF NOT EXISTS offenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        student_name TEXT,
        offense TEXT,
        date TEXT
    )
    ''')

    # ADMIN TABLE
    cur.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    ''')

    # DEFAULT ADMIN (only inserts once)
    cur.execute("SELECT * FROM admins WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ("admin", "admin123"))

    conn.commit()
    conn.close()

init_db()

# ================= ROUTES =================

# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = connect_db()
        cur = conn.cursor()

        # 👑 ADMIN LOGIN
        cur.execute("SELECT * FROM admins WHERE username=? AND password=?", (username, password))
        admin = cur.fetchone()

        if admin:
            session["admin"] = username
            conn.close()
            return redirect("/admin-dashboard")

        # 👤 USER LOGIN
        session["user"] = username
        conn.close()
        return redirect("/dashboard")

    return render_template("login.html")


# USER DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html", name=session["user"])


# ADMIN DASHBOARD
@app.route("/admin-dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/")

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM offenses")
    records = cur.fetchall()
    total = len(records)

    conn.close()

    return render_template("admin_dashboard.html", records=records, total=total)


# ADD RECORD
@app.route("/add", methods=["POST"])
def add():
    if "user" not in session:
        return redirect("/")

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO offenses (username, student_name, offense, date)
    VALUES (?, ?, ?, ?)
    """, (
        session["user"],
        request.form["student_name"],
        request.form["offense"],
        request.form["date"]
    ))

    conn.commit()
    conn.close()

    return redirect("/records")


# RECORDS VIEW
@app.route("/records")
def records():
    conn = connect_db()
    cur = conn.cursor()

    # 👑 ADMIN → ALL
    if "admin" in session:
        cur.execute("SELECT * FROM offenses")

    # 👤 USER → OWN ONLY
    elif "user" in session:
        cur.execute("SELECT * FROM offenses WHERE username=?", (session["user"],))

    else:
        return redirect("/")

    records = cur.fetchall()
    conn.close()

    return render_template("records.html", records=records)


# LOGOUT
@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("admin", None)
    return redirect("/")


# RUN
if __name__ == "__main__":
    app.run()