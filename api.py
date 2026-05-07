"""
🌐 REST API - Figure Skating Analysis System
FastAPI backend for mobile app integration
"""

import os
import sqlite3
import uuid
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Optional import of ISU scorer — graceful degradation if deps are missing
# ---------------------------------------------------------------------------
try:
    from src.analysis.isu_scorer import (
        GOE_MULTIPLIERS,
        JUMP_BASE_VALUES,
        PCS_COMPONENTS,
        SPIN_BASE_VALUES,
        ISUScorer,
    )

    _isu_scorer = ISUScorer()
    _isu_available = True
except Exception:  # pragma: no cover
    _isu_available = False
    _isu_scorer = None
    JUMP_BASE_VALUES: Dict[str, float] = {}
    SPIN_BASE_VALUES: Dict[str, list] = {}
    PCS_COMPONENTS: List[str] = []
    GOE_MULTIPLIERS: List[float] = []

# ---------------------------------------------------------------------------
# Application constants
# ---------------------------------------------------------------------------

VERSION = "1.0.0"
DB_PATH = os.environ.get("DB_PATH", "skating_database.db")
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Figure Skating Analysis API",
    description="REST API for the Figure Skating Analysis & Attendance System",
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all origins for mobile app integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Database helpers (sqlite3, matching existing codebase)
# ---------------------------------------------------------------------------


def get_db() -> sqlite3.Connection:
    """Open and return a sqlite3 connection with row_factory set."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Ensure required tables exist (idempotent)."""
    conn = get_db()
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                gender TEXT,
                birth_date TEXT,
                level TEXT,
                coach TEXT,
                bundle TEXT,
                club_id INTEGER,
                email TEXT,
                phone TEXT,
                membership_status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER,
                date TEXT NOT NULL,
                status TEXT DEFAULT 'present',
                session_type TEXT,
                coach TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (member_id) REFERENCES members (id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memberships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER,
                bundle_type TEXT,
                amount REAL,
                payment_date TEXT,
                discount REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (member_id) REFERENCES members (id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                player_name TEXT,
                member_id INTEGER,
                video_filename TEXT,
                video_path TEXT,
                status TEXT DEFAULT 'pending',
                total_score REAL,
                technical_score REAL,
                components_score REAL,
                program_type TEXT,
                analysis_result TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                FOREIGN KEY (member_id) REFERENCES members (id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS session_elements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                element_code TEXT,
                element_type TEXT,
                base_value REAL,
                goe INTEGER,
                goe_value REAL,
                final_score REAL,
                deductions REAL DEFAULT 0,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES analysis_sessions (session_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS session_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                error_type TEXT,
                description TEXT,
                timestamp_seconds REAL,
                severity TEXT DEFAULT 'warning',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES analysis_sessions (session_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                full_name TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT
            )
            """
        )

        # Seed a default admin account if table is empty
        existing = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if existing == 0:
            import hashlib

            pw_hash = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute(
                "INSERT INTO users (username, password_hash, role, full_name) VALUES (?,?,?,?)",
                ("admin", pw_hash, "admin", "System Administrator"),
            )

        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Startup event
# ---------------------------------------------------------------------------


@app.on_event("startup")
def on_startup() -> None:
    """Initialize database and upload directory on app start."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    init_db()


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    isu_engine: bool
    db_path: str


# -- Members --


class MemberCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    level: Optional[str] = None
    coach: Optional[str] = None
    bundle: Optional[str] = None
    club_id: Optional[int] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    membership_status: str = "active"


class MemberResponse(BaseModel):
    id: int
    name: str
    gender: Optional[str]
    birth_date: Optional[str]
    level: Optional[str]
    coach: Optional[str]
    bundle: Optional[str]
    club_id: Optional[int]
    email: Optional[str]
    phone: Optional[str]
    membership_status: Optional[str]
    created_at: Optional[str]


class MemberListResponse(BaseModel):
    total: int
    members: List[MemberResponse]


# -- Sessions --


class SessionSummary(BaseModel):
    id: int
    session_id: str
    player_name: Optional[str]
    member_id: Optional[int]
    video_filename: Optional[str]
    status: str
    total_score: Optional[float]
    technical_score: Optional[float]
    components_score: Optional[float]
    program_type: Optional[str]
    created_at: Optional[str]
    completed_at: Optional[str]


class ElementDetail(BaseModel):
    id: int
    element_code: Optional[str]
    element_type: Optional[str]
    base_value: Optional[float]
    goe: Optional[int]
    goe_value: Optional[float]
    final_score: Optional[float]
    deductions: Optional[float]
    notes: Optional[str]


class ErrorDetail(BaseModel):
    id: int
    error_type: Optional[str]
    description: Optional[str]
    timestamp_seconds: Optional[float]
    severity: Optional[str]


class SessionDetail(BaseModel):
    session: SessionSummary
    elements: List[ElementDetail]
    errors: List[ErrorDetail]


class SessionListResponse(BaseModel):
    total: int
    sessions: List[SessionSummary]


# -- Upload --


class UploadResponse(BaseModel):
    session_id: str
    filename: str
    size_bytes: int
    status: str
    message: str
    analysis: Dict[str, Any]


# -- Progress --


class ProgressEntry(BaseModel):
    session_id: str
    date: Optional[str]
    total_score: Optional[float]
    technical_score: Optional[float]
    components_score: Optional[float]
    program_type: Optional[str]


class ProgressResponse(BaseModel):
    player_name: str
    total_sessions: int
    average_score: Optional[float]
    best_score: Optional[float]
    progress: List[ProgressEntry]


# -- Auth --


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user: Dict[str, Any]


# -- ISU --


class ISUElement(BaseModel):
    code: str
    type: str
    base_value: float
    description: Optional[str] = None


class ISUElementsResponse(BaseModel):
    jumps: Dict[str, float]
    spins: Dict[str, Any]
    pcs_components: List[str]
    goe_multipliers: List[float]


class ISUScoreResponse(BaseModel):
    element: str
    rotations: Optional[int]
    goe: int
    base_value: float
    goe_value: float
    final_score: float
    deductions: float
    notes: List[str]


# -- Stats --


class StatsResponse(BaseModel):
    total_members: int
    active_members: int
    total_sessions: int
    completed_sessions: int
    total_elements_analyzed: int
    isu_engine_available: bool
    version: str
    timestamp: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/", response_model=HealthResponse, tags=["Health"])
def health_check() -> HealthResponse:
    """Health check endpoint with version and capability info."""
    return HealthResponse(
        status="ok",
        version=VERSION,
        timestamp=datetime.utcnow().isoformat(),
        isu_engine=_isu_available,
        db_path=DB_PATH,
    )


# ---- Members ---------------------------------------------------------------


@app.get("/api/v1/members", response_model=MemberListResponse, tags=["Members"])
def list_members(
    club_id: Optional[int] = Query(None, description="Filter by club ID"),
    search: Optional[str] = Query(None, description="Search by name"),
    limit: int = Query(100, ge=1, le=1000),
) -> MemberListResponse:
    """List members with optional filtering."""
    conn = get_db()
    try:
        conditions: List[str] = []
        params: List[Any] = []

        if club_id is not None:
            conditions.append("club_id = ?")
            params.append(club_id)

        if search:
            conditions.append("name LIKE ?")
            params.append(f"%{search}%")

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.append(limit)

        rows = conn.execute(
            f"SELECT * FROM members {where} ORDER BY name LIMIT ?", params
        ).fetchall()

        count_params = params[:-1]
        total = conn.execute(
            f"SELECT COUNT(*) FROM members {where}", count_params
        ).fetchone()[0]

        members = [
            MemberResponse(
                id=r["id"],
                name=r["name"],
                gender=r["gender"],
                birth_date=r["birth_date"],
                level=r["level"],
                coach=r["coach"],
                bundle=r["bundle"],
                club_id=r["club_id"] if "club_id" in r.keys() else None,
                email=r["email"] if "email" in r.keys() else None,
                phone=r["phone"] if "phone" in r.keys() else None,
                membership_status=r["membership_status"] if "membership_status" in r.keys() else "active",
                created_at=r["created_at"],
            )
            for r in rows
        ]
        return MemberListResponse(total=total, members=members)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        conn.close()


@app.post(
    "/api/v1/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Members"],
)
def create_member(body: MemberCreate) -> MemberResponse:
    """Create a new member."""
    conn = get_db()
    try:
        now = datetime.utcnow().isoformat()
        cursor = conn.execute(
            """
            INSERT INTO members
                (name, gender, birth_date, level, coach, bundle, club_id,
                 email, phone, membership_status, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                body.name,
                body.gender,
                body.birth_date,
                body.level,
                body.coach,
                body.bundle,
                body.club_id,
                body.email,
                body.phone,
                body.membership_status,
                now,
            ),
        )
        conn.commit()
        member_id = cursor.lastrowid

        row = conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
        return MemberResponse(
            id=row["id"],
            name=row["name"],
            gender=row["gender"],
            birth_date=row["birth_date"],
            level=row["level"],
            coach=row["coach"],
            bundle=row["bundle"],
            club_id=row["club_id"] if "club_id" in row.keys() else None,
            email=row["email"] if "email" in row.keys() else None,
            phone=row["phone"] if "phone" in row.keys() else None,
            membership_status=row["membership_status"] if "membership_status" in row.keys() else "active",
            created_at=row["created_at"],
        )
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        conn.close()


@app.get("/api/v1/members/{member_id}", response_model=MemberResponse, tags=["Members"])
def get_member(member_id: int) -> MemberResponse:
    """Get a member by ID."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM members WHERE id = ?", (member_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(
                status_code=404, detail=f"Member {member_id} not found"
            )
        return MemberResponse(
            id=row["id"],
            name=row["name"],
            gender=row["gender"],
            birth_date=row["birth_date"],
            level=row["level"],
            coach=row["coach"],
            bundle=row["bundle"],
            club_id=row["club_id"] if "club_id" in row.keys() else None,
            email=row["email"] if "email" in row.keys() else None,
            phone=row["phone"] if "phone" in row.keys() else None,
            membership_status=row["membership_status"] if "membership_status" in row.keys() else "active",
            created_at=row["created_at"],
        )
    finally:
        conn.close()


# ---- Sessions --------------------------------------------------------------


def _row_to_session_summary(r: sqlite3.Row) -> SessionSummary:
    keys = r.keys()
    return SessionSummary(
        id=r["id"],
        session_id=r["session_id"],
        player_name=r["player_name"] if "player_name" in keys else None,
        member_id=r["member_id"] if "member_id" in keys else None,
        video_filename=r["video_filename"] if "video_filename" in keys else None,
        status=r["status"],
        total_score=r["total_score"] if "total_score" in keys else None,
        technical_score=r["technical_score"] if "technical_score" in keys else None,
        components_score=r["components_score"] if "components_score" in keys else None,
        program_type=r["program_type"] if "program_type" in keys else None,
        created_at=r["created_at"] if "created_at" in keys else None,
        completed_at=r["completed_at"] if "completed_at" in keys else None,
    )


@app.get("/api/v1/sessions", response_model=SessionListResponse, tags=["Sessions"])
def list_sessions(
    player_name: Optional[str] = Query(None, description="Filter by player name"),
    limit: int = Query(50, ge=1, le=500),
) -> SessionListResponse:
    """List analysis sessions."""
    conn = get_db()
    try:
        conditions: List[str] = []
        params: List[Any] = []

        if player_name:
            conditions.append("player_name LIKE ?")
            params.append(f"%{player_name}%")

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        count_params = list(params)
        params.append(limit)

        rows = conn.execute(
            f"SELECT * FROM analysis_sessions {where} ORDER BY created_at DESC LIMIT ?",
            params,
        ).fetchall()

        total = conn.execute(
            f"SELECT COUNT(*) FROM analysis_sessions {where}", count_params
        ).fetchone()[0]

        return SessionListResponse(
            total=total,
            sessions=[_row_to_session_summary(r) for r in rows],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        conn.close()


@app.get(
    "/api/v1/sessions/{session_id}", response_model=SessionDetail, tags=["Sessions"]
)
def get_session(session_id: str) -> SessionDetail:
    """Get full session detail including elements and errors."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM analysis_sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(
                status_code=404, detail=f"Session '{session_id}' not found"
            )

        elements_rows = conn.execute(
            "SELECT * FROM session_elements WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()

        errors_rows = conn.execute(
            "SELECT * FROM session_errors WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()

        elements = [
            ElementDetail(
                id=e["id"],
                element_code=e["element_code"],
                element_type=e["element_type"],
                base_value=e["base_value"],
                goe=e["goe"],
                goe_value=e["goe_value"],
                final_score=e["final_score"],
                deductions=e["deductions"],
                notes=e["notes"],
            )
            for e in elements_rows
        ]

        errors = [
            ErrorDetail(
                id=err["id"],
                error_type=err["error_type"],
                description=err["description"],
                timestamp_seconds=err["timestamp_seconds"],
                severity=err["severity"],
            )
            for err in errors_rows
        ]

        return SessionDetail(
            session=_row_to_session_summary(row),
            elements=elements,
            errors=errors,
        )
    finally:
        conn.close()


# ---- Video Upload ----------------------------------------------------------


@app.post(
    "/api/v1/analyze/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Analysis"],
)
async def upload_video(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload a video file for analysis.
    Returns a session ID and a placeholder analysis result.
    """
    allowed_extensions = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(allowed_extensions)}",
        )

    session_id = str(uuid.uuid4())
    dest_dir = os.path.join(UPLOAD_DIR, session_id)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, file.filename)

    try:
        with open(dest_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        size_bytes = os.path.getsize(dest_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {exc}") from exc

    # Persist session record
    conn = get_db()
    try:
        now = datetime.utcnow().isoformat()
        conn.execute(
            """
            INSERT INTO analysis_sessions
                (session_id, video_filename, video_path, status, created_at)
            VALUES (?,?,?,?,?)
            """,
            (session_id, file.filename, dest_path, "uploaded", now),
        )
        conn.commit()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        conn.close()

    # Build a placeholder analysis payload (real processing would be async)
    analysis: Dict[str, Any] = {
        "session_id": session_id,
        "filename": file.filename,
        "size_bytes": size_bytes,
        "status": "uploaded",
        "message": "Video uploaded successfully. Analysis queued.",
        "estimated_processing_seconds": max(10, size_bytes // 1_000_000 * 5),
        "isu_engine_available": _isu_available,
    }

    return UploadResponse(
        session_id=session_id,
        filename=file.filename,
        size_bytes=size_bytes,
        status="uploaded",
        message="Video uploaded successfully. Analysis queued.",
        analysis=analysis,
    )


# ---- Player Progress -------------------------------------------------------


@app.get(
    "/api/v1/players/{name}/progress",
    response_model=ProgressResponse,
    tags=["Players"],
)
def player_progress(name: str) -> ProgressResponse:
    """Get historical progress data for a player."""
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT session_id, created_at, total_score, technical_score,
                   components_score, program_type
            FROM analysis_sessions
            WHERE player_name LIKE ?
            ORDER BY created_at ASC
            """,
            (f"%{name}%",),
        ).fetchall()

        entries = [
            ProgressEntry(
                session_id=r["session_id"],
                date=r["created_at"],
                total_score=r["total_score"],
                technical_score=r["technical_score"],
                components_score=r["components_score"],
                program_type=r["program_type"],
            )
            for r in rows
        ]

        scores = [e.total_score for e in entries if e.total_score is not None]
        avg_score = round(sum(scores) / len(scores), 2) if scores else None
        best_score = max(scores) if scores else None

        return ProgressResponse(
            player_name=name,
            total_sessions=len(entries),
            average_score=avg_score,
            best_score=best_score,
            progress=entries,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        conn.close()


# ---- Auth ------------------------------------------------------------------


@app.post("/api/v1/auth/login", response_model=LoginResponse, tags=["Auth"])
def login(body: LoginRequest) -> LoginResponse:
    """Authenticate user and return a session token."""
    import hashlib

    pw_hash = hashlib.sha256(body.password.encode()).hexdigest()
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password_hash = ?",
            (body.username, pw_hash),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Update last login
    conn = get_db()
    try:
        conn.execute(
            "UPDATE users SET last_login = ? WHERE username = ?",
            (datetime.utcnow().isoformat(), body.username),
        )
        conn.commit()
    finally:
        conn.close()

    # Generate a simple token (for production use JWT or similar)
    token = str(uuid.uuid4())

    user_info: Dict[str, Any] = {
        "id": row["id"],
        "username": row["username"],
        "role": row["role"],
        "full_name": row["full_name"],
    }

    return LoginResponse(token=token, user=user_info)


# ---- ISU Scoring -----------------------------------------------------------


@app.get(
    "/api/v1/isu/elements",
    response_model=ISUElementsResponse,
    tags=["ISU Scoring"],
)
def isu_elements() -> ISUElementsResponse:
    """List all ISU elements with base values."""
    spins_with_levels: Dict[str, Any] = {}
    for spin_type, levels in SPIN_BASE_VALUES.items():
        spins_with_levels[spin_type] = {
            str(i): v for i, v in enumerate(levels)
        }

    return ISUElementsResponse(
        jumps=dict(JUMP_BASE_VALUES),
        spins=spins_with_levels,
        pcs_components=list(PCS_COMPONENTS),
        goe_multipliers=list(GOE_MULTIPLIERS),
    )


@app.get(
    "/api/v1/isu/score",
    response_model=ISUScoreResponse,
    tags=["ISU Scoring"],
)
def isu_score(
    element: str = Query(..., description="Element code e.g. 3A, 4T, CoSp"),
    rotations: Optional[int] = Query(None, ge=1, le=4, description="Rotations (jumps only)"),
    goe: int = Query(0, ge=-5, le=5, description="Grade of Execution (-5 to +5)"),
    downgrade: bool = Query(False, description="Apply downgrade"),
    fall: bool = Query(False, description="Fall occurred"),
    level: int = Query(0, ge=0, le=4, description="Level (spins only)"),
) -> ISUScoreResponse:
    """Calculate score for a single ISU element."""
    if not _isu_available:
        raise HTTPException(
            status_code=503,
            detail="ISU scoring engine not available",
        )

    # Decide whether it is a jump or spin
    jump_types = {"A", "Lz", "F", "Lo", "S", "T"}
    spin_types = set(SPIN_BASE_VALUES.keys())

    # Try jump first
    if rotations is not None:
        jump_type = element
        # Strip leading digit if caller supplied e.g. "3A"
        if element and element[0].isdigit():
            rotations = int(element[0])
            jump_type = element[1:]
        if jump_type in jump_types:
            result = _isu_scorer.calc_jump_score(
                jump_type, rotations, goe, downgrade=downgrade, fall=fall
            )
            return ISUScoreResponse(
                element=element,
                rotations=rotations,
                goe=goe,
                base_value=result["base_value"],
                goe_value=result["goe_value"],
                final_score=result["final_score"],
                deductions=result["deductions"],
                notes=result.get("notes", []),
            )

    # If element starts with digit, parse as jump
    if element and element[0].isdigit():
        rot = int(element[0])
        jtype = element[1:]
        if jtype in jump_types:
            result = _isu_scorer.calc_jump_score(
                jtype, rot, goe, downgrade=downgrade, fall=fall
            )
            return ISUScoreResponse(
                element=element,
                rotations=rot,
                goe=goe,
                base_value=result["base_value"],
                goe_value=result["goe_value"],
                final_score=result["final_score"],
                deductions=result["deductions"],
                notes=result.get("notes", []),
            )

    # Try as spin
    for stype in spin_types:
        if element.startswith(stype):
            result = _isu_scorer.calc_spin_score(stype, level, goe)
            return ISUScoreResponse(
                element=element,
                rotations=None,
                goe=goe,
                base_value=result["base_value"],
                goe_value=result["goe_value"],
                final_score=result["final_score"],
                deductions=0.0,
                notes=[],
            )

    # Generic base value lookup
    bv = _isu_scorer.get_base_value(element)
    if bv == 0.0:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown element '{element}'. Check /api/v1/isu/elements for valid codes.",
        )

    info = _isu_scorer.element_lookup(element)
    return ISUScoreResponse(
        element=element,
        rotations=info.get("rotations"),
        goe=goe,
        base_value=bv,
        goe_value=0.0,
        final_score=bv,
        deductions=0.0,
        notes=[],
    )


# ---- Stats -----------------------------------------------------------------


@app.get("/api/v1/stats", response_model=StatsResponse, tags=["Stats"])
def stats() -> StatsResponse:
    """Return system-wide statistics."""
    conn = get_db()
    try:
        total_members = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]

        try:
            active_members = conn.execute(
                "SELECT COUNT(*) FROM members WHERE membership_status = 'active'"
            ).fetchone()[0]
        except Exception:
            active_members = total_members

        try:
            total_sessions = conn.execute(
                "SELECT COUNT(*) FROM analysis_sessions"
            ).fetchone()[0]
        except Exception:
            total_sessions = 0

        try:
            completed_sessions = conn.execute(
                "SELECT COUNT(*) FROM analysis_sessions WHERE status = 'completed'"
            ).fetchone()[0]
        except Exception:
            completed_sessions = 0

        try:
            total_elements = conn.execute(
                "SELECT COUNT(*) FROM session_elements"
            ).fetchone()[0]
        except Exception:
            total_elements = 0

        return StatsResponse(
            total_members=total_members,
            active_members=active_members,
            total_sessions=total_sessions,
            completed_sessions=completed_sessions,
            total_elements_analyzed=total_elements,
            isu_engine_available=_isu_available,
            version=VERSION,
            timestamp=datetime.utcnow().isoformat(),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
