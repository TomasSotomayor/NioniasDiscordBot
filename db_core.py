import sqlite3

_conn = None

def get_conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect("database.db", check_same_thread=False)
        _conn.execute("PRAGMA foreign_keys = ON;")
    return _conn
