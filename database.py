# database.py
import json
import os

DB_FILE = "database.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"stats": {}, "ranks": {}, "locks": {}, "history": {}}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
