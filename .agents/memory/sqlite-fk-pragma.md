---
name: SQLite foreign-key enforcement
description: Why ON DELETE CASCADE / FK constraints silently do nothing in SQLite unless a per-connection pragma is set.
---

In SQLite, declaring `FOREIGN KEY ... REFERENCES ... ON DELETE CASCADE` in a table schema does **nothing** by default. FK enforcement is OFF unless you run `PRAGMA foreign_keys = ON`, and the pragma is **per-connection** — it must be set on every connection, not just at table-creation time.

**Why:** Without the pragma, orphan child rows can be inserted against non-existent parents, and deleting a parent leaves dangling children (cascade never fires). This silently corrupts referential integrity.

**How to apply:** Set `PRAGMA foreign_keys = ON` on every connection (here: inside the cached `get_connection()` and inside `ensure_schema()`). For a shared, long-lived cached connection used across Streamlit sessions, also set `PRAGMA journal_mode = WAL` and `PRAGMA busy_timeout` (+ `timeout=`) to tolerate concurrent reads/writes. Verify enforcement with a test: an insert with a bad foreign key should raise `sqlite3.IntegrityError`, and deleting a parent should remove its children.
