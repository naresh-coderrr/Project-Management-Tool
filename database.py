# database.py
import sqlite3
import os

DB_FILE = "portfolio_chat_history.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sheet_name TEXT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_chat_message(sheet_name, role, content):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chat_logs (sheet_name, role, content)
        VALUES (?, ?, ?)
    ''', (sheet_name, role, content))
    conn.commit()
    conn.close()

def load_chat_history(sheet_name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT role, content FROM chat_logs 
        WHERE sheet_name = ? 
        ORDER BY timestamp ASC
    ''', (sheet_name,))
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in rows]

# Initialize DB structure on load
init_db()