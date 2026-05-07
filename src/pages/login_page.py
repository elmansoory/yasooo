"""
Login Page for Figure Skating Analysis System
Supports Arabic (AR) and English (EN) display via the `lang` parameter.
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.auth.auth_manager import authenticate, seed_demo_data, init_auth_tables

# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------
_T = {
    "EN": {
        "app_title": "Figure Skating Analysis System",
        "app_subtitle": "Professional Performance Analytics",
        "sign_in": "Sign In",
        "username": "Username",
        "password": "Password",
        "login_btn": "Login",
        "invalid_creds": "Invalid username or password. Please try again.",
        "demo_hint_title": "Demo Credentials",
        "demo_hint_body": (
            "**Admin:** admin / admin123  \n"
            "**Coach:** coach1 / coach123  \n"
            "**Athlete:** athlete1 / athlete123"
        ),
        "welcome_admin":   "Welcome, Administrator {name}! You have full system access.",
        "welcome_club_manager": "Welcome, Club Manager {name}! You can manage your club.",
        "welcome_coach":   "Welcome, Coach {name}! Ready to analyse your athletes.",
        "welcome_athlete": "Welcome, {name}! Let's review your progress.",
        "welcome_default": "Welcome, {name}!",
        "logout": "Logout",
        "logged_in_as": "Logged in as",
        "role_label": "Role",
        "club_label": "Club",
    },
    "AR": {
        "app_title": "نظام تحليل التزلج الفني",
        "app_subtitle": "تحليلات الأداء الاحترافي",
        "sign_in": "تسجيل الدخول",
        "username": "اسم المستخدم",
        "password": "كلمة المرور",
        "login_btn": "دخول",
        "invalid_creds": "اسم المستخدم أو كلمة المرور غير صحيحة. حاول مرة أخرى.",
        "demo_hint_title": "بيانات تجريبية",
        "demo_hint_body": (
            "**المسؤول:** admin / admin123  \n"
            "**المدرب:** coach1 / coach123  \n"
            "**الرياضي:** athlete1 / athlete123"
        ),
        "welcome_admin":   "مرحباً، المسؤول {name}! لديك صلاحية الوصول الكاملة.",
        "welcome_club_manager": "مرحباً، مدير النادي {name}! يمكنك إدارة ناديك.",
        "welcome_coach":   "مرحباً، المدرب {name}! جاهز لتحليل رياضييك.",
        "welcome_athlete": "مرحباً، {name}! لنراجع تقدمك.",
        "welcome_default": "مرحباً، {name}!",
        "logout": "تسجيل الخروج",
        "logged_in_as": "مسجّل الدخول باسم",
        "role_label": "الدور",
        "club_label": "النادي",
    },
}

_ROLE_LABELS = {
    "EN": {"admin": "Admin", "club_manager": "Club Manager", "coach": "Coach", "athlete": "Athlete"},
    "AR": {"admin": "مسؤول", "club_manager": "مدير النادي", "coach": "مدرب", "athlete": "رياضي"},
}

# ---------------------------------------------------------------------------
# Page CSS
# ---------------------------------------------------------------------------
_LOGIN_CSS = """
<style>
    /* Hide default Streamlit header / footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    body {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    .login-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 80vh;
    }

    .login-card {
        background: rgba(255, 255, 255, 0.97);
        border-radius: 20px;
        padding: 48px 44px 40px 44px;
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.35);
        max-width: 420px;
        width: 100%;
        margin: auto;
    }

    .login-logo {
        text-align: center;
        font-size: 3rem;
        margin-bottom: 4px;
    }

    .login-title {
        text-align: center;
        font-size: 1.55rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 2px;
    }

    .login-subtitle {
        text-align: center;
        color: #888;
        font-size: 0.88rem;
        margin-bottom: 28px;
    }

    .stTextInput > label {
        font-weight: 600;
        color: #444;
    }

    div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.4rem;
        font-size: 1rem;
        font-weight: 600;
        width: 100%;
        transition: opacity 0.2s;
    }

    div[data-testid="stButton"] > button:hover {
        opacity: 0.88;
        color: white;
    }

    .demo-box {
        background: linear-gradient(135deg, #f0f3ff 0%, #f5f0ff 100%);
        border-left: 4px solid #667eea;
        border-radius: 8px;
        padding: 12px 14px;
        margin-top: 20px;
        font-size: 0.84rem;
    }

    .welcome-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 14px;
        padding: 22px 26px;
        color: white;
        text-align: center;
        margin-bottom: 18px;
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
    }

    .welcome-banner h2 {
        margin: 0 0 6px 0;
        font-size: 1.4rem;
    }

    .welcome-banner p {
        margin: 0;
        opacity: 0.88;
        font-size: 0.92rem;
    }

    .user-info-row {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        justify-content: center;
        margin-top: 10px;
    }

    .user-badge {
        background: rgba(255,255,255,0.22);
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 0.82rem;
        font-weight: 600;
    }
</style>
"""


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def logout() -> None:
    """Clear all authentication-related session state keys."""
    for key in ("user", "authenticated", "club_id"):
        st.session_state.pop(key, None)


def show_login_page(lang: str = "EN") -> None:
    """
    Render the login page.

    Parameters
    ----------
    lang : str
        Display language – "EN" (default) or "AR".
    """
    lang = lang.upper() if lang else "EN"
    if lang not in _T:
        lang = "EN"

    t = _T[lang]

    # Ensure DB tables and demo data exist
    try:
        init_auth_tables()
        seed_demo_data()
    except Exception:
        pass

    # Inject CSS
    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # Already authenticated – show a welcome banner + logout option
    # -----------------------------------------------------------------------
    if st.session_state.get("authenticated") and st.session_state.get("user"):
        user = st.session_state["user"]
        _show_welcome_banner(user, t, lang)
        if st.button(f"🚪 {t['logout']}", key="logout_btn"):
            logout()
            st.rerun()
        return

    # -----------------------------------------------------------------------
    # Login form
    # -----------------------------------------------------------------------
    # Centre the card using columns
    _, centre, _ = st.columns([1, 2, 1])
    with centre:
        st.markdown(
            f"""
            <div class="login-card">
                <div class="login-logo">⛸️</div>
                <div class="login-title">{t['app_title']}</div>
                <div class="login-subtitle">{t['app_subtitle']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(f"### {t['sign_in']}")

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input(t["username"], placeholder="e.g. admin", key="login_username")
            password = st.text_input(t["password"], type="password", key="login_password")
            submitted = st.form_submit_button(t["login_btn"], use_container_width=True)

        if submitted:
            if not username.strip() or not password:
                st.error(t["invalid_creds"])
            else:
                user = authenticate(username.strip(), password)
                if user:
                    st.session_state["user"] = user
                    st.session_state["authenticated"] = True
                    st.session_state["club_id"] = user.get("club_id")
                    st.rerun()
                else:
                    st.error(t["invalid_creds"])

        # Demo credentials hint
        with st.expander(f"ℹ️ {t['demo_hint_title']}", expanded=False):
            st.markdown(
                f'<div class="demo-box">{t["demo_hint_body"]}</div>',
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _show_welcome_banner(user: dict, t: dict, lang: str) -> None:
    """Render a role-specific welcome banner for an authenticated user."""
    role = user.get("role", "")
    name = user.get("full_name") or user.get("username", "")
    club_name = user.get("club_name") or ""

    role_key_map = {
        "admin":        "welcome_admin",
        "club_manager": "welcome_club_manager",
        "coach":        "welcome_coach",
        "athlete":      "welcome_athlete",
    }
    msg_key = role_key_map.get(role, "welcome_default")
    welcome_msg = t[msg_key].format(name=name)

    role_display = _ROLE_LABELS.get(lang, _ROLE_LABELS["EN"]).get(role, role.title())

    club_badge = f'<span class="user-badge">🏟️ {club_name}</span>' if club_name else ""
    st.markdown(
        f"""
        <div class="welcome-banner">
            <h2>⛸️ {welcome_msg}</h2>
            <div class="user-info-row">
                <span class="user-badge">👤 {user.get('username','')}</span>
                <span class="user-badge">🎭 {role_display}</span>
                {club_badge}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
