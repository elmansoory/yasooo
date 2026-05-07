"""
Club Management Page for Figure Skating Analysis System
Admin-only page to manage clubs and users.
Supports Arabic (AR) and English (EN) display via the `lang` parameter.
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.auth.auth_manager import (
    create_club,
    create_user,
    list_clubs,
    list_users,
    ROLES,
)

# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------
_T = {
    "EN": {
        "page_title": "Club Management",
        "page_subtitle": "Manage clubs and users",
        "access_denied": "Access Denied: This page is for administrators only.",
        "clubs_section": "Clubs",
        "no_clubs": "No clubs found.",
        "club_name_col": "Club Name",
        "country_col": "Country",
        "members_col": "Members",
        "add_club": "Add New Club",
        "club_name_label": "Club Name",
        "country_label": "Country",
        "logo_url_label": "Logo URL (optional)",
        "club_name_placeholder": "e.g. Crystal Ice Club",
        "country_placeholder": "e.g. USA",
        "submit_club": "Create Club",
        "club_created": "Club '{name}' created successfully (ID: {id}).",
        "club_create_error": "Failed to create club. It may already exist.",
        "club_name_required": "Club name is required.",
        "country_required": "Country is required.",
        "users_section": "Users",
        "filter_by_club": "Filter by Club",
        "all_clubs": "All Clubs",
        "no_users": "No users found.",
        "username_col": "Username",
        "full_name_col": "Full Name",
        "role_col": "Role",
        "email_col": "Email",
        "club_col": "Club",
        "status_col": "Status",
        "active": "Active",
        "inactive": "Inactive",
        "add_user": "Add New User",
        "username_label": "Username",
        "password_label": "Password",
        "role_label": "Role",
        "full_name_label": "Full Name",
        "email_label": "Email (optional)",
        "club_assign_label": "Assign to Club",
        "no_club": "No Club",
        "submit_user": "Create User",
        "user_created": "User '{username}' created successfully.",
        "user_create_error": "Failed to create user. Username may already exist.",
        "username_required": "Username is required.",
        "password_required": "Password is required (min 6 characters).",
        "full_name_required": "Full name is required.",
        "role_required": "Please select a role.",
        "stats_header": "Statistics",
        "total_clubs": "Total Clubs",
        "total_users": "Total Users",
        "total_admins": "Admins",
        "total_coaches": "Coaches",
        "total_athletes": "Athletes",
    },
    "AR": {
        "page_title": "إدارة الأندية",
        "page_subtitle": "إدارة الأندية والمستخدمين",
        "access_denied": "رفض الوصول: هذه الصفحة للمسؤولين فقط.",
        "clubs_section": "الأندية",
        "no_clubs": "لا توجد أندية.",
        "club_name_col": "اسم النادي",
        "country_col": "الدولة",
        "members_col": "الأعضاء",
        "add_club": "إضافة نادي جديد",
        "club_name_label": "اسم النادي",
        "country_label": "الدولة",
        "logo_url_label": "رابط الشعار (اختياري)",
        "club_name_placeholder": "مثال: نادي الجليد الكريستالي",
        "country_placeholder": "مثال: السعودية",
        "submit_club": "إنشاء نادي",
        "club_created": "تم إنشاء النادي '{name}' بنجاح (المعرف: {id}).",
        "club_create_error": "فشل إنشاء النادي. قد يكون موجوداً بالفعل.",
        "club_name_required": "اسم النادي مطلوب.",
        "country_required": "الدولة مطلوبة.",
        "users_section": "المستخدمون",
        "filter_by_club": "تصفية حسب النادي",
        "all_clubs": "جميع الأندية",
        "no_users": "لا يوجد مستخدمون.",
        "username_col": "اسم المستخدم",
        "full_name_col": "الاسم الكامل",
        "role_col": "الدور",
        "email_col": "البريد الإلكتروني",
        "club_col": "النادي",
        "status_col": "الحالة",
        "active": "نشط",
        "inactive": "غير نشط",
        "add_user": "إضافة مستخدم جديد",
        "username_label": "اسم المستخدم",
        "password_label": "كلمة المرور",
        "role_label": "الدور",
        "full_name_label": "الاسم الكامل",
        "email_label": "البريد الإلكتروني (اختياري)",
        "club_assign_label": "تعيين إلى نادي",
        "no_club": "بلا نادي",
        "submit_user": "إنشاء مستخدم",
        "user_created": "تم إنشاء المستخدم '{username}' بنجاح.",
        "user_create_error": "فشل إنشاء المستخدم. قد يكون اسم المستخدم موجوداً بالفعل.",
        "username_required": "اسم المستخدم مطلوب.",
        "password_required": "كلمة المرور مطلوبة (6 أحرف على الأقل).",
        "full_name_required": "الاسم الكامل مطلوب.",
        "role_required": "الرجاء اختيار دور.",
        "stats_header": "الإحصائيات",
        "total_clubs": "إجمالي الأندية",
        "total_users": "إجمالي المستخدمين",
        "total_admins": "المسؤولون",
        "total_coaches": "المدربون",
        "total_athletes": "الرياضيون",
    },
}

_ROLE_LABELS = {
    "EN": {
        "admin": "Admin",
        "club_manager": "Club Manager",
        "coach": "Coach",
        "athlete": "Athlete",
    },
    "AR": {
        "admin": "مسؤول",
        "club_manager": "مدير النادي",
        "coach": "مدرب",
        "athlete": "رياضي",
    },
}

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
_MGMT_CSS = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .mgmt-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 14px;
        padding: 22px 28px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 6px 20px rgba(102,126,234,0.3);
    }

    .mgmt-header h1 {
        margin: 0 0 4px 0;
        font-size: 1.7rem;
    }

    .mgmt-header p {
        margin: 0;
        opacity: 0.85;
        font-size: 0.92rem;
    }

    .stat-card {
        background: white;
        border-radius: 12px;
        padding: 18px 16px;
        text-align: center;
        box-shadow: 0 4px 14px rgba(102,126,234,0.12);
        border-top: 4px solid #667eea;
    }

    .stat-card .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
        line-height: 1;
    }

    .stat-card .stat-label {
        font-size: 0.82rem;
        color: #888;
        margin-top: 6px;
    }

    .section-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #444;
        border-bottom: 3px solid #667eea;
        padding-bottom: 6px;
        margin: 28px 0 16px 0;
    }

    .club-row {
        background: #f8f9ff;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
        border-left: 5px solid #667eea;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .club-name {
        font-weight: 700;
        color: #333;
        font-size: 1rem;
    }

    .club-meta {
        color: #777;
        font-size: 0.85rem;
    }

    .member-badge {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.82rem;
        font-weight: 600;
    }

    .user-row {
        background: white;
        border-radius: 10px;
        padding: 10px 16px;
        margin-bottom: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
    }

    .role-badge {
        border-radius: 14px;
        padding: 3px 10px;
        font-size: 0.78rem;
        font-weight: 600;
    }

    .role-admin    { background: #ffeaea; color: #c0392b; }
    .role-club_manager { background: #fff3e0; color: #e67e22; }
    .role-coach    { background: #e8f5e9; color: #27ae60; }
    .role-athlete  { background: #e3f2fd; color: #2980b9; }

    .form-card {
        background: #f8f9ff;
        border-radius: 14px;
        padding: 24px;
        box-shadow: 0 2px 10px rgba(102,126,234,0.1);
        margin-top: 12px;
    }

    div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1.2rem;
        font-weight: 600;
        transition: opacity 0.2s;
    }

    div[data-testid="stButton"] > button:hover {
        opacity: 0.87;
        color: white;
    }

    .access-denied {
        background: #ffeaea;
        border: 2px solid #e74c3c;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        color: #c0392b;
        font-weight: 600;
        font-size: 1rem;
    }
</style>
"""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _t(lang: str) -> dict:
    lang = (lang or "EN").upper()
    return _T.get(lang, _T["EN"])


def _role_label(role: str, lang: str) -> str:
    labels = _ROLE_LABELS.get(lang.upper(), _ROLE_LABELS["EN"])
    return labels.get(role, role.title())


def _render_stats(clubs: list, users: list, t: dict) -> None:
    """Render a row of statistics cards."""
    st.markdown(f'<div class="section-title">{t["stats_header"]}</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    roles_count = {}
    for u in users:
        roles_count[u["role"]] = roles_count.get(u["role"], 0) + 1

    for col, label, value in [
        (c1, t["total_clubs"],   len(clubs)),
        (c2, t["total_users"],   len(users)),
        (c3, t["total_admins"],  roles_count.get("admin", 0)),
        (c4, t["total_coaches"], roles_count.get("coach", 0)),
        (c5, t["total_athletes"], roles_count.get("athlete", 0)),
    ]:
        col.markdown(
            f'<div class="stat-card"><div class="stat-value">{value}</div>'
            f'<div class="stat-label">{label}</div></div>',
            unsafe_allow_html=True,
        )


def _render_clubs_list(clubs: list, t: dict, lang: str) -> None:
    """Render the list of clubs."""
    st.markdown(f'<div class="section-title">🏟️ {t["clubs_section"]}</div>', unsafe_allow_html=True)
    if not clubs:
        st.info(t["no_clubs"])
        return

    for club in clubs:
        count = club.get("member_count", 0)
        st.markdown(
            f"""
            <div class="club-row">
                <div>
                    <div class="club-name">🏟️ {club['name']}</div>
                    <div class="club-meta">🌍 {club.get('country', '')}</div>
                </div>
                <div>
                    <span class="member-badge">👥 {count} {t['members_col']}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_add_club_form(t: dict, lang: str) -> None:
    """Render the add-club form."""
    with st.expander(f"➕ {t['add_club']}", expanded=False):
        st.markdown('<div class="form-card">', unsafe_allow_html=True)
        with st.form("add_club_form", clear_on_submit=True):
            club_name = st.text_input(
                t["club_name_label"],
                placeholder=t["club_name_placeholder"],
                key="new_club_name",
            )
            country = st.text_input(
                t["country_label"],
                placeholder=t["country_placeholder"],
                key="new_club_country",
            )
            logo_url = st.text_input(
                t["logo_url_label"],
                placeholder="https://...",
                key="new_club_logo",
            )
            submitted = st.form_submit_button(t["submit_club"], use_container_width=True)

        if submitted:
            errors = []
            if not club_name.strip():
                errors.append(t["club_name_required"])
            if not country.strip():
                errors.append(t["country_required"])
            if errors:
                for err in errors:
                    st.error(err)
            else:
                club_id = create_club(club_name.strip(), country.strip(), logo_url.strip())
                if club_id != -1:
                    st.success(t["club_created"].format(name=club_name.strip(), id=club_id))
                    st.rerun()
                else:
                    st.error(t["club_create_error"])
        st.markdown("</div>", unsafe_allow_html=True)


def _render_users_list(clubs: list, t: dict, lang: str) -> None:
    """Render the users list with optional club filter."""
    st.markdown(f'<div class="section-title">👤 {t["users_section"]}</div>', unsafe_allow_html=True)

    # Build club filter options
    club_options = {t["all_clubs"]: None}
    for c in clubs:
        club_options[c["name"]] = c["id"]

    selected_club_label = st.selectbox(
        t["filter_by_club"],
        options=list(club_options.keys()),
        key="user_filter_club",
    )
    selected_club_id = club_options[selected_club_label]

    users = list_users(club_id=selected_club_id)

    if not users:
        st.info(t["no_users"])
        return

    for user in users:
        role = user.get("role", "")
        role_display = _role_label(role, lang)
        club_name = user.get("club_name") or "-"
        status = t["active"] if user.get("is_active") else t["inactive"]
        status_icon = "🟢" if user.get("is_active") else "🔴"

        st.markdown(
            f"""
            <div class="user-row">
                <span><strong>{user.get('username', '')}</strong></span>
                <span style="color:#555;">{user.get('full_name', '')}</span>
                <span class="role-badge role-{role}">{role_display}</span>
                <span style="color:#888; font-size:0.85rem;">🏟️ {club_name}</span>
                <span style="color:#888; font-size:0.85rem;">✉️ {user.get('email', '') or '-'}</span>
                <span style="font-size:0.82rem;">{status_icon} {status}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_add_user_form(clubs: list, t: dict, lang: str) -> None:
    """Render the add-user form."""
    with st.expander(f"➕ {t['add_user']}", expanded=False):
        st.markdown('<div class="form-card">', unsafe_allow_html=True)

        # Build club choices for the form
        club_choices = {t["no_club"]: None}
        for c in clubs:
            club_choices[c["name"]] = c["id"]

        # Build role choices with translated labels
        role_choices = {_role_label(r, lang): r for r in ROLES}

        with st.form("add_user_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input(
                    t["username_label"],
                    placeholder="e.g. athlete2",
                    key="new_user_username",
                )
                password = st.text_input(
                    t["password_label"],
                    type="password",
                    key="new_user_password",
                )
                full_name = st.text_input(
                    t["full_name_label"],
                    placeholder="e.g. Jane Doe",
                    key="new_user_fullname",
                )
            with col2:
                role_display = st.selectbox(
                    t["role_label"],
                    options=list(role_choices.keys()),
                    key="new_user_role",
                )
                club_display = st.selectbox(
                    t["club_assign_label"],
                    options=list(club_choices.keys()),
                    key="new_user_club",
                )
                email = st.text_input(
                    t["email_label"],
                    placeholder="user@example.com",
                    key="new_user_email",
                )

            submitted = st.form_submit_button(t["submit_user"], use_container_width=True)

        if submitted:
            errors = []
            if not username.strip():
                errors.append(t["username_required"])
            if not password or len(password) < 6:
                errors.append(t["password_required"])
            if not full_name.strip():
                errors.append(t["full_name_required"])
            if errors:
                for err in errors:
                    st.error(err)
            else:
                role = role_choices[role_display]
                club_id = club_choices[club_display]
                user_id = create_user(
                    username=username.strip(),
                    password=password,
                    role=role,
                    full_name=full_name.strip(),
                    club_id=club_id,
                    email=email.strip(),
                )
                if user_id != -1:
                    st.success(t["user_created"].format(username=username.strip()))
                    st.rerun()
                else:
                    st.error(t["user_create_error"])

        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def show_club_management_page(lang: str = "EN") -> None:
    """
    Render the admin-only Club Management page.

    Parameters
    ----------
    lang : str
        Display language – "EN" (default) or "AR".
    """
    lang = (lang or "EN").upper()
    if lang not in _T:
        lang = "EN"

    t = _t(lang)

    # Inject CSS
    st.markdown(_MGMT_CSS, unsafe_allow_html=True)

    # Access control
    user = st.session_state.get("user")
    if not st.session_state.get("authenticated") or not user or user.get("role") != "admin":
        st.markdown(
            f'<div class="access-denied">🔒 {t["access_denied"]}</div>',
            unsafe_allow_html=True,
        )
        return

    # Page header
    st.markdown(
        f"""
        <div class="mgmt-header">
            <h1>🏟️ {t['page_title']}</h1>
            <p>{t['page_subtitle']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Fetch data
    clubs = list_clubs()
    all_users = list_users()

    # Stats
    _render_stats(clubs, all_users, t)

    # Divider
    st.markdown("---")

    # Clubs section
    _render_clubs_list(clubs, t, lang)
    _render_add_club_form(t, lang)

    st.markdown("---")

    # Users section
    _render_users_list(clubs, t, lang)
    _render_add_user_form(clubs, t, lang)
