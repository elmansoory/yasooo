"""
حفظ وإدارة سجل تحليلات الفيديو لكل لاعب
Analysis History Manager — per-player session storage
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import streamlit as st


DB_PATH = 'skating_database.db'


def init_analysis_tables():
    """إنشاء جداول سجل التحليل إذا لم تكن موجودة"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS analysis_sessions (
            session_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id     INTEGER,
            session_date  TEXT NOT NULL,
            player_name   TEXT,
            session_note  TEXT,
            video_duration REAL DEFAULT 0,
            total_jumps   INTEGER DEFAULT 0,
            total_spins   INTEGER DEFAULT 0,
            total_errors  INTEGER DEFAULT 0,
            total_score   REAL DEFAULT 0,
            avg_goe       REAL DEFAULT 0,
            clean_jumps   INTEGER DEFAULT 0,
            errors_json   TEXT DEFAULT '[]',
            jumps_json    TEXT DEFAULT '[]',
            spins_json    TEXT DEFAULT '[]',
            report_json   TEXT DEFAULT '{}',
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_analysis(results: Dict, member_id: Optional[int] = None) -> int:
    """حفظ نتائج جلسة تحليل — يُرجع session_id"""
    init_analysis_tables()

    jumps = results.get('jumps', [])
    errors = results.get('errors', [])
    spins = results.get('spins', [])
    report = results.get('report', {})
    vi = results.get('video_info', {})

    total_score = results.get('total_score', 0.0)
    avg_goe = (
        sum(j.get('goe', 0) for j in jumps) / len(jumps)
        if jumps else 0.0
    )
    clean_jumps = sum(1 for j in jumps if j.get('is_clean', True))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO analysis_sessions
            (member_id, session_date, player_name, session_note,
             video_duration, total_jumps, total_spins, total_errors,
             total_score, avg_goe, clean_jumps,
             errors_json, jumps_json, spins_json, report_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        member_id,
        datetime.now().strftime('%Y-%m-%d'),
        results.get('player_name', ''),
        results.get('session_note', ''),
        vi.get('duration', 0),
        len(jumps),
        len(spins),
        len(errors),
        total_score,
        round(avg_goe, 2),
        clean_jumps,
        json.dumps(errors, ensure_ascii=False),
        json.dumps(jumps, ensure_ascii=False),
        json.dumps(spins, ensure_ascii=False),
        json.dumps(report, ensure_ascii=False),
    ))
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    return session_id


@st.cache_data(ttl=30)
def load_all_sessions() -> List[Dict]:
    """تحميل كل الجلسات مرتبة بالأحدث"""
    init_analysis_tables()
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT session_id, member_id, session_date, player_name,
                   session_note, video_duration, total_jumps, total_spins,
                   total_errors, total_score, avg_goe, clean_jumps
            FROM analysis_sessions
            ORDER BY session_date DESC, created_at DESC
        """)
        rows = c.fetchall()
        conn.close()
        cols = ['session_id', 'member_id', 'session_date', 'player_name',
                'session_note', 'video_duration', 'total_jumps', 'total_spins',
                'total_errors', 'total_score', 'avg_goe', 'clean_jumps']
        return [dict(zip(cols, r)) for r in rows]
    except Exception:
        return []


@st.cache_data(ttl=30)
def load_player_sessions(player_name: str) -> List[Dict]:
    """تحميل جلسات لاعب بعينه"""
    all_sessions = load_all_sessions()
    return [s for s in all_sessions if s.get('player_name') == player_name]


def load_session_detail(session_id: int) -> Optional[Dict]:
    """تحميل تفاصيل جلسة كاملة بما فيها JSON"""
    init_analysis_tables()
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM analysis_sessions WHERE session_id = ?", (session_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        cols = [d[0] for d in c.description] if c.description else []
        # re-open to get description
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM analysis_sessions WHERE session_id = ?", (session_id,))
        cols = [d[0] for d in c.description]
        row = c.fetchone()
        conn.close()
        result = dict(zip(cols, row))
        result['errors'] = json.loads(result.get('errors_json', '[]'))
        result['jumps'] = json.loads(result.get('jumps_json', '[]'))
        result['spins'] = json.loads(result.get('spins_json', '[]'))
        result['report'] = json.loads(result.get('report_json', '{}'))
        return result
    except Exception:
        return None


def invalidate_history_cache():
    load_all_sessions.clear()
    load_player_sessions.clear()


def get_player_names() -> List[str]:
    """قائمة أسماء اللاعبين الذين لديهم جلسات"""
    sessions = load_all_sessions()
    names = list({s['player_name'] for s in sessions if s.get('player_name')})
    return sorted(names)
