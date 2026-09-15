import sqlite3
import os

# مسار قاعدة البيانات: src/config/db.py -> ../../data/munjiz.db
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, 'munjiz.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # يخلي كل صف يتصرف مثل dict (باسم العمود)
    return conn
