import sqlite3
import json
import os
from datetime import datetime, timedelta
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_app_path

BASE_DIR = get_app_path()
DB_PATH = os.path.join(BASE_DIR, "experiments_history.db")

def init_db():
    """Создает таблицу history и удаляет старые записи при запуске."""
    os.makedirs(BASE_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            params TEXT,
            results TEXT
        )
    ''')
    conn.commit()
    conn.close()
    
    cleanup_old_records()

def cleanup_old_records():
    """Удаляет записи, которые старше 14 дней."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cutoff = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('DELETE FROM history WHERE timestamp < ?', (cutoff,))
            
        conn.commit()
        conn.close()
    except Exception:
        pass

def add_record(params, results):
    """Сохраняет эксперимент в базу данных."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    params_json = json.dumps(params)
    results_json = json.dumps(results)
    
    cursor.execute('INSERT INTO history (timestamp, params, results) VALUES (?, ?, ?)',
                   (timestamp, params_json, results_json))
    conn.commit()
    conn.close()

def get_all_records():
    """Возвращает все записи, отсортированные от новых к старым."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, timestamp, params, results FROM history ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    
    records = []
    for row in rows:
        try:
            records.append({
                'id': row[0],
                'timestamp': row[1],
                'params': json.loads(row[2]),
                'results': json.loads(row[3])
            })
        except json.JSONDecodeError:
            continue
    return records

def delete_last_minutes(minutes):
    """Удаляет записи за последние N минут."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cutoff = (datetime.now() - timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('DELETE FROM history WHERE timestamp >= ?', (cutoff,))
    conn.commit()
    conn.close()

def delete_all():
    """Полная очистка истории."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM history')
    conn.commit()
    conn.close()