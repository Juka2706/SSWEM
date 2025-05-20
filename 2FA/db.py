import sqlite3

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        otp_secret TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT username, password, otp_secret FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return result

def add_user(username, password, otp_secret):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO users VALUES (?, ?, ?)", (username, password, otp_secret))
    conn.commit()
    conn.close()
