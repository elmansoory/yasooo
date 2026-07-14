"""
أدوات معالجة النص العربي للتقارير والرسوم (PDF + matplotlib)
Arabic text shaping helpers for PDF and chart rendering.
"""
import os

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    _RESHAPE_OK = True
except Exception:
    _RESHAPE_OK = False

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT_DIR = os.path.join(_ROOT, "assets", "fonts")
FONT_REGULAR = os.path.join(FONT_DIR, "Amiri-Regular.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "Amiri-Bold.ttf")


def ar(text):
    """يعيد تشكيل النص العربي ليظهر بشكل صحيح في PDF/الرسوم."""
    if text is None:
        return ""
    text = str(text)
    if not _RESHAPE_OK or not text.strip():
        return text
    try:
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


def fonts_available():
    return os.path.exists(FONT_REGULAR)


def reshaping_available():
    return _RESHAPE_OK
