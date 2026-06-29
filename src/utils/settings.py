"""
إعدادات النادي (الاسم + الشعار) المستخدمة في التقارير
Club settings persisted as a small JSON file.
"""
import hashlib
import hmac
import json
import os
import secrets

SETTINGS_PATH = os.path.join("data", "club_settings.json")
LOGO_PATH = os.path.join("assets", "club_logo.png")

DEFAULTS = {
    "club_name": "نادي التزلج",
    "club_subtitle": "نظام صناعة البطل - مبني على معايير ISU",
    "logo_path": "",
}


def load_settings():
    data = dict(DEFAULTS)
    try:
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data.update(json.load(f))
    except Exception:
        pass
    return data


def save_settings(settings: dict):
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    current = load_settings()
    current.update({k: v for k, v in settings.items() if v is not None})
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)
    return current


def save_logo(uploaded_bytes: bytes):
    os.makedirs(os.path.dirname(LOGO_PATH), exist_ok=True)
    with open(LOGO_PATH, "wb") as f:
        f.write(uploaded_bytes)
    save_settings({"logo_path": LOGO_PATH})
    return LOGO_PATH


# ── Owner PIN (protects the parent-code admin page) ──────────────
def has_owner_pin() -> bool:
    s = load_settings()
    return bool(s.get("owner_pin_hash") and s.get("owner_pin_salt"))


def set_owner_pin(pin: str):
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + str(pin)).encode("utf-8")).hexdigest()
    save_settings({"owner_pin_salt": salt, "owner_pin_hash": h})


def verify_owner_pin(pin: str) -> bool:
    s = load_settings()
    salt, h = s.get("owner_pin_salt"), s.get("owner_pin_hash")
    if not salt or not h:
        return False
    cand = hashlib.sha256((salt + str(pin)).encode("utf-8")).hexdigest()
    return hmac.compare_digest(h, cand)
