"""
ترقيات قاعدة البيانات - تُنفَّذ تلقائياً عند بدء التطبيق
Idempotent schema migrations. Safe to run on existing or fresh databases.
"""
import sqlite3

DB_PATH = "skating_database.db"

_EVALUATIONS = """
CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    evaluation_date TEXT NOT NULL,
    evaluation_type TEXT DEFAULT 'training',
    tes REAL DEFAULT 0,
    pcs REAL DEFAULT 0,
    total_score REAL DEFAULT 0,
    jump_success_rate REAL,
    elements_count INTEGER DEFAULT 0,
    falls_count INTEGER DEFAULT 0,
    deductions REAL DEFAULT 0,
    coach TEXT,
    notes TEXT,
    source TEXT DEFAULT 'manual',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members (id) ON DELETE CASCADE
)
"""

_COMPETITIONS = """
CREATE TABLE IF NOT EXISTS competitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    comp_date TEXT,
    location TEXT,
    level TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
"""

_COMPETITION_ENTRIES = """
CREATE TABLE IF NOT EXISTS competition_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    segment TEXT DEFAULT 'free',
    rank INTEGER,
    score REAL,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (competition_id, member_id, segment),
    FOREIGN KEY (competition_id) REFERENCES competitions (id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES members (id) ON DELETE CASCADE
)
"""

_SCHEDULE = """
CREATE TABLE IF NOT EXISTS schedule_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    day_of_week INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    coach TEXT,
    level TEXT,
    location TEXT,
    capacity INTEGER,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
"""

_PARENT_ACCESS = """
CREATE TABLE IF NOT EXISTS parent_access (
    member_id INTEGER PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    active INTEGER DEFAULT 1,
    last_viewed_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members (id) ON DELETE CASCADE
)
"""

_TABLES = [_EVALUATIONS, _COMPETITIONS, _COMPETITION_ENTRIES, _SCHEDULE, _PARENT_ACCESS]

_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_eval_member_date ON evaluations(member_id, evaluation_date)",
    "CREATE INDEX IF NOT EXISTS idx_eval_date ON evaluations(evaluation_date)",
    "CREATE INDEX IF NOT EXISTS idx_memb_member_date ON memberships(member_id, payment_date)",
    "CREATE INDEX IF NOT EXISTS idx_compentry_comp ON competition_entries(competition_id)",
    "CREATE INDEX IF NOT EXISTS idx_compentry_member ON competition_entries(member_id)",
    "CREATE INDEX IF NOT EXISTS idx_schedule_day ON schedule_sessions(day_of_week, start_time)",
    "CREATE INDEX IF NOT EXISTS idx_parent_code ON parent_access(code)",
]

# (table, column, definition) — added only if the column is missing
_COLUMN_ADDS = [
    ("memberships", "duration_months", "INTEGER DEFAULT 1"),
]


def _column_exists(cur, table, column):
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())


def ensure_schema(conn=None, db_path=DB_PATH):
    """تتأكد من وجود الجداول والأعمدة الجديدة. آمنة للتكرار."""
    own = conn is None
    if own:
        conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.cursor()
        for ddl in _TABLES:
            cur.execute(ddl)
        for table, column, definition in _COLUMN_ADDS:
            try:
                if not _column_exists(cur, table, column):
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            except sqlite3.OperationalError:
                # table may not exist yet on a brand-new DB; safe to skip
                pass
        for stmt in _INDEXES:
            try:
                cur.execute(stmt)
            except sqlite3.OperationalError:
                pass
        conn.commit()
    finally:
        if own:
            conn.close()


if __name__ == "__main__":
    ensure_schema()
    print("✅ Schema ensured (evaluations, competitions, schedule, parent_access)")
