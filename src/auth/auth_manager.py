"""
Authentication Manager for Figure Skating Analysis System
Uses SQLite with hashlib-based password hashing (no external dependencies)
"""
import sqlite3
import hashlib
import os
import logging
from typing import Optional, Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Valid roles
ROLES = ["admin", "club_manager", "coach", "athlete"]

# Database path
_DB_PATH = str(Path(__file__).parent.parent.parent / "data" / "auth.db")


def _get_db_path() -> str:
    """Return the path to the auth database, creating directories if needed."""
    db_dir = os.path.dirname(_DB_PATH)
    os.makedirs(db_dir, exist_ok=True)
    return _DB_PATH


def _get_connection() -> sqlite3.Connection:
    """Create and return a SQLite connection with row factory."""
    conn = sqlite3.connect(_get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _hash_password(password: str) -> str:
    """Hash a password using SHA-256 with a salt."""
    salt = "yasooo_figure_skating_salt_2025"
    salted = f"{salt}{password}{salt}"
    return hashlib.sha256(salted.encode("utf-8")).hexdigest()


def init_auth_tables() -> None:
    """Create the users and clubs tables if they don't already exist."""
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS clubs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL UNIQUE,
                country     TEXT    NOT NULL DEFAULT '',
                logo_url    TEXT    NOT NULL DEFAULT '',
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT    NOT NULL UNIQUE,
                password    TEXT    NOT NULL,
                role        TEXT    NOT NULL CHECK(role IN ('admin','club_manager','coach','athlete')),
                full_name   TEXT    NOT NULL DEFAULT '',
                email       TEXT    NOT NULL DEFAULT '',
                club_id     INTEGER REFERENCES clubs(id) ON DELETE SET NULL,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                is_active   INTEGER NOT NULL DEFAULT 1
            );

            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_users_club    ON users(club_id);
            """
        )
        conn.commit()
        conn.close()
        logger.info("Auth tables initialized successfully.")
    except Exception as exc:
        logger.error("Failed to initialize auth tables: %s", exc)
        raise


def create_club(name: str, country: str, logo_url: str = "") -> int:
    """
    Insert a new club record and return its id.
    Returns -1 on failure.
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO clubs (name, country, logo_url) VALUES (?, ?, ?)",
            (name.strip(), country.strip(), logo_url.strip()),
        )
        conn.commit()
        club_id: int = cursor.lastrowid
        conn.close()
        logger.info("Club '%s' created with id=%d", name, club_id)
        return club_id
    except sqlite3.IntegrityError:
        logger.warning("Club '%s' already exists.", name)
        try:
            conn2 = _get_connection()
            row = conn2.execute("SELECT id FROM clubs WHERE name = ?", (name.strip(),)).fetchone()
            conn2.close()
            return row["id"] if row else -1
        except Exception:
            return -1
    except Exception as exc:
        logger.error("create_club error: %s", exc)
        return -1


def create_user(
    username: str,
    password: str,
    role: str,
    full_name: str,
    club_id: Optional[int],
    email: str = "",
) -> int:
    """
    Insert a new user and return its id.
    Returns -1 on failure.
    """
    try:
        if role not in ROLES:
            logger.error("Invalid role '%s'. Must be one of %s", role, ROLES)
            return -1
        hashed = _hash_password(password)
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO users (username, password, role, full_name, email, club_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (username.strip(), hashed, role, full_name.strip(), email.strip(), club_id),
        )
        conn.commit()
        user_id: int = cursor.lastrowid
        conn.close()
        logger.info("User '%s' created with id=%d role=%s", username, user_id, role)
        return user_id
    except sqlite3.IntegrityError:
        logger.warning("Username '%s' already exists.", username)
        return -1
    except Exception as exc:
        logger.error("create_user error: %s", exc)
        return -1


def authenticate(username: str, password: str) -> Optional[Dict]:
    """
    Validate credentials and return the user dict on success, or None on failure.
    Passwords are compared as SHA-256 hashes.
    """
    try:
        hashed = _hash_password(password)
        conn = _get_connection()
        row = conn.execute(
            """SELECT u.id, u.username, u.role, u.full_name, u.email,
                      u.club_id, u.is_active, u.created_at,
                      c.name AS club_name
               FROM users u
               LEFT JOIN clubs c ON c.id = u.club_id
               WHERE u.username = ? AND u.password = ? AND u.is_active = 1""",
            (username.strip(), hashed),
        ).fetchone()
        conn.close()
        if row is None:
            return None
        return dict(row)
    except Exception as exc:
        logger.error("authenticate error: %s", exc)
        return None


def get_user(username: str) -> Optional[Dict]:
    """Return the user dict for the given username, or None if not found."""
    try:
        conn = _get_connection()
        row = conn.execute(
            """SELECT u.id, u.username, u.role, u.full_name, u.email,
                      u.club_id, u.is_active, u.created_at,
                      c.name AS club_name
               FROM users u
               LEFT JOIN clubs c ON c.id = u.club_id
               WHERE u.username = ?""",
            (username.strip(),),
        ).fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as exc:
        logger.error("get_user error: %s", exc)
        return None


def get_club(club_id: int) -> Optional[Dict]:
    """Return the club dict for the given club_id, or None if not found."""
    try:
        conn = _get_connection()
        row = conn.execute("SELECT * FROM clubs WHERE id = ?", (club_id,)).fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as exc:
        logger.error("get_club error: %s", exc)
        return None


def list_clubs() -> List[Dict]:
    """Return all clubs as a list of dicts."""
    try:
        conn = _get_connection()
        rows = conn.execute(
            """SELECT c.*, COUNT(u.id) AS member_count
               FROM clubs c
               LEFT JOIN users u ON u.club_id = c.id AND u.is_active = 1
               GROUP BY c.id
               ORDER BY c.name"""
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        logger.error("list_clubs error: %s", exc)
        return []


def list_users(club_id: Optional[int] = None) -> List[Dict]:
    """
    Return all users as a list of dicts.
    Optionally filter by club_id.
    """
    try:
        conn = _get_connection()
        if club_id is not None:
            rows = conn.execute(
                """SELECT u.id, u.username, u.role, u.full_name, u.email,
                          u.club_id, u.is_active, u.created_at,
                          c.name AS club_name
                   FROM users u
                   LEFT JOIN clubs c ON c.id = u.club_id
                   WHERE u.club_id = ?
                   ORDER BY u.role, u.full_name""",
                (club_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT u.id, u.username, u.role, u.full_name, u.email,
                          u.club_id, u.is_active, u.created_at,
                          c.name AS club_name
                   FROM users u
                   LEFT JOIN clubs c ON c.id = u.club_id
                   ORDER BY u.role, u.full_name"""
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        logger.error("list_users error: %s", exc)
        return []


def seed_demo_data() -> None:
    """
    Populate the database with a demo club and demo users if they don't already exist.
    Demo accounts:
      admin    / admin123   (role: admin)
      coach1   / coach123   (role: coach)
      athlete1 / athlete123 (role: athlete)
    """
    try:
        init_auth_tables()

        # Demo club
        club_id = create_club("Crystal Ice Club", "International", "")
        if club_id == -1:
            existing = list_clubs()
            for c in existing:
                if c["name"] == "Crystal Ice Club":
                    club_id = c["id"]
                    break

        # Demo users
        demo_users = [
            ("admin",    "admin123",   "admin",   "System Administrator", None),
            ("coach1",   "coach123",   "coach",   "Alex Johnson",         club_id),
            ("athlete1", "athlete123", "athlete", "Sam Williams",         club_id),
        ]
        for uname, pwd, role, full_name, cid in demo_users:
            existing = get_user(uname)
            if existing is None:
                create_user(uname, pwd, role, full_name, cid, f"{uname}@crystaliceclub.example")

        logger.info("Demo data seeded successfully.")
    except Exception as exc:
        logger.error("seed_demo_data error: %s", exc)


def change_password(username: str, old_pw: str, new_pw: str) -> bool:
    """
    Change the password for a user after verifying the old password.
    Returns True on success, False otherwise.
    """
    try:
        if not new_pw or len(new_pw) < 6:
            logger.warning("New password too short for '%s'.", username)
            return False
        user = authenticate(username, old_pw)
        if user is None:
            logger.warning("change_password: authentication failed for '%s'.", username)
            return False
        new_hashed = _hash_password(new_pw)
        conn = _get_connection()
        conn.execute(
            "UPDATE users SET password = ? WHERE username = ?",
            (new_hashed, username.strip()),
        )
        conn.commit()
        conn.close()
        logger.info("Password changed for user '%s'.", username)
        return True
    except Exception as exc:
        logger.error("change_password error: %s", exc)
        return False
