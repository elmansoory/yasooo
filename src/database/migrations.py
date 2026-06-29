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

_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_eval_member_date ON evaluations(member_id, evaluation_date)",
    "CREATE INDEX IF NOT EXISTS idx_eval_date ON evaluations(evaluation_date)",
]


def ensure_schema(conn=None, db_path=DB_PATH):
    """تتأكد من وجود الجداول الجديدة. آمنة للتكرار."""
    own = conn is None
    if own:
        conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.cursor()
        cur.execute(_EVALUATIONS)
        for stmt in _INDEXES:
            cur.execute(stmt)
        conn.commit()
    finally:
        if own:
            conn.close()


if __name__ == "__main__":
    ensure_schema()
    print("✅ Schema ensured (evaluations table ready)")
