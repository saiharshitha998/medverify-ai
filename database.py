"""
MediVerify AI - SQLite Database Handler
=======================================
Stores verification history, aggregates statistics for analytics dashboard,
and manages SQLite interactions.
"""

import sqlite3
import os
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'mediverify.db')

def get_connection():
    """Returns a connection to the SQLite database with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables and seeds initial realistic history if empty."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verification_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_name TEXT NOT NULL,
            batch_number TEXT NOT NULL,
            manufacturer TEXT NOT NULL,
            mfg_date TEXT,
            exp_date TEXT,
            result TEXT NOT NULL,
            explanation TEXT,
            confidence REAL DEFAULT 95.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

    # Seed with representative records if table is empty for an immediate rich demo
    cursor.execute('SELECT COUNT(*) FROM verification_history')
    count = cursor.fetchone()[0]

    if count == 0:
        seed_records = [
            ("Paracetamol 650mg", "CIP20491", "Cipla Ltd", "2024-01-15", "2027-01-14", "Verified", 
             "Matches authorized registered formulation; batch prefix CIP and standard 36-month shelf life verified.", 99.2, "2026-11-20 10:15:00"),
            ("Augmentin 625 Duo", "GSK18402", "GlaxoSmithKline", "2024-03-10", "2026-03-09", "Verified", 
             "Official license holder and standard 24-month stability match confirmed.", 98.7, "2026-11-21 11:42:00"),
            ("Dolo 650mg", "XYZ99201", "Micro Labs Ltd", "2024-05-01", "2027-05-01", "Suspicious", 
             "Batch prefix mismatch: Expected prefix MIC for Micro Labs Ltd, found XYZ.", 94.5, "2026-11-21 14:20:00"),
            ("Azithral 500mg", "ALM33921", "Cipla Ltd", "2024-02-12", "2027-02-11", "Suspicious", 
             "Manufacturer mismatch: Azithral 500mg is officially registered to Alembic Pharmaceuticals, not Cipla Ltd.", 96.0, "2026-11-22 09:05:00"),
            ("FakeCure 100mg", "FK00192", "GenericPharma", "2024-06-01", "2026-06-01", "Not Found", 
             "Medicine name not found in the authorized pharmaceutical reference database.", 95.0, "2026-11-22 16:30:00"),
            ("Glycomet 500mg", "USV44820", "USV Private Limited", "2024-04-18", "2027-04-17", "Verified", 
             "Formulation, batch syntax, and 36-month shelf life parameters strictly compliant.", 99.0, "2026-11-23 11:10:00"),
            ("Pan 40mg", "ALK67123", "Alkem Laboratories", "2024-01-20", "2023-01-20", "Suspicious", 
             "Chronological anomaly: Expiry date precedes manufacturing date.", 99.5, "2026-11-23 15:45:00"),
            ("Shelcal 500", "TOR91823", "Torrent Pharmaceuticals", "2024-07-01", "2026-07-01", "Verified", 
             "Matches official reference entry and authorized packaging syntax.", 98.5, "2026-11-24 08:30:00"),
            ("Limcee 500mg", "ABB10925", "Abbott India Ltd", "2024-05-15", "2035-05-15", "Suspicious", 
             "Excessive shelf-life detected (132 months); violates 60-month maximum regulatory ceiling.", 97.2, "2026-11-24 13:20:00"),
            ("Unlisted Antibiotic", "MED7721", "Global Health Care", "2024-02-01", "2026-02-01", "Not Found", 
             "Medicine formulation not recognized in the approved national catalog.", 95.0, "2026-11-24 14:50:00")
        ]

        for r in seed_records:
            cursor.execute('''
                INSERT INTO verification_history 
                (medicine_name, batch_number, manufacturer, mfg_date, exp_date, result, explanation, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', r)
        conn.commit()

    conn.close()

def add_verification_record(medicine_name, batch_number, manufacturer, mfg_date, exp_date, result, explanation, confidence=95.0):
    """Inserts a new verification event into SQLite history."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO verification_history 
        (medicine_name, batch_number, manufacturer, mfg_date, exp_date, result, explanation, confidence, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
    ''', (medicine_name, batch_number, manufacturer, mfg_date, exp_date, result, explanation, confidence))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return record_id

def get_history(limit=50, filter_result=None, search_query=None):
    """Retrieves verification logs with optional filters."""
    conn = get_connection()
    cursor = conn.cursor()

    query = 'SELECT * FROM verification_history WHERE 1=1'
    params = []

    if filter_result and filter_result.lower() != 'all':
        query += ' AND result = ?'
        params.append(filter_result)

    if search_query:
        query += ' AND (medicine_name LIKE ? OR batch_number LIKE ? OR manufacturer LIKE ?)'
        like_str = f"%{search_query}%"
        params.extend([like_str, like_str, like_str])

    query += ' ORDER BY created_at DESC LIMIT ?'
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    history = [dict(row) for row in rows]
    conn.close()
    return history

def get_stats():
    """Calculates overall statistics for dashboard cards."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM verification_history')
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM verification_history WHERE result = 'Verified'")
    verified = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM verification_history WHERE result = 'Suspicious'")
    suspicious = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM verification_history WHERE result = 'Not Found'")
    not_found = cursor.fetchone()[0]

    conn.close()

    verified_pct = round((verified / total * 100), 1) if total > 0 else 0.0
    suspicious_pct = round((suspicious / total * 100), 1) if total > 0 else 0.0

    return {
        'total': total,
        'verified': verified,
        'suspicious': suspicious,
        'not_found': not_found,
        'verified_pct': verified_pct,
        'suspicious_pct': suspicious_pct
    }

def get_chart_data():
    """Generates grouped data for Chart.js rendering."""
    conn = get_connection()
    cursor = conn.cursor()

    # Verdict distribution
    cursor.execute('''
        SELECT result, COUNT(*) as count 
        FROM verification_history 
        GROUP BY result
    ''')
    verdict_rows = cursor.fetchall()
    verdict_dict = {'Verified': 0, 'Suspicious': 0, 'Not Found': 0}
    for row in verdict_rows:
        if row['result'] in verdict_dict:
            verdict_dict[row['result']] = row['count']

    # Top manufacturers tested
    cursor.execute('''
        SELECT manufacturer, COUNT(*) as count 
        FROM verification_history 
        GROUP BY manufacturer 
        ORDER BY count DESC 
        LIMIT 6
    ''')
    mfg_rows = cursor.fetchall()
    mfg_labels = [row['manufacturer'] for row in mfg_rows]
    mfg_counts = [row['count'] for row in mfg_rows]

    # Recent timeline breakdown
    cursor.execute('''
        SELECT substr(created_at, 1, 10) as v_date, result, COUNT(*) as count
        FROM verification_history
        GROUP BY v_date, result
        ORDER BY v_date ASC
    ''')
    timeline_rows = cursor.fetchall()
    timeline_dates = sorted(list(set(row['v_date'] for row in timeline_rows)))
    
    # Organize timeline counts per verdict
    verified_timeline = []
    suspicious_timeline = []
    not_found_timeline = []
    for d in timeline_dates:
        v_count = sum(r['count'] for r in timeline_rows if r['v_date'] == d and r['result'] == 'Verified')
        s_count = sum(r['count'] for r in timeline_rows if r['v_date'] == d and r['result'] == 'Suspicious')
        nf_count = sum(r['count'] for r in timeline_rows if r['v_date'] == d and r['result'] == 'Not Found')
        verified_timeline.append(v_count)
        suspicious_timeline.append(s_count)
        not_found_timeline.append(nf_count)

    conn.close()

    return {
        'verdicts': verdict_dict,
        'top_manufacturers': {
            'labels': mfg_labels,
            'counts': mfg_counts
        },
        'timeline': {
            'dates': timeline_dates,
            'verified': verified_timeline,
            'suspicious': suspicious_timeline,
            'not_found': not_found_timeline
        }
    }

def clear_all_history():
    """Clears history table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM verification_history')
    conn.commit()
    conn.close()
