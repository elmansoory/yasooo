#!/bin/bash
#
# سكريبت تشغيل نظام تحليل التزلج الفني — YASOOO
# Figure Skating Analysis System - Run Script (Linux/macOS)
#
# Usage: ./run.sh
#

set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

LOG="$APP_DIR/launch.log"
: > "$LOG"

echo "════════════════════════════════════════════════════════════"
echo "   ⛸️  YASOOO - نظام تحليل التزلج الفني"
echo "   Figure Skating Analysis System"
echo "════════════════════════════════════════════════════════════"
echo ""

# ── [1/5] Python check ───────────────────────────────────────────
echo "[1/5] التحقق من Python..."
PYTHON_BIN=""
for candidate in python3.11 python3 python; do
    if command -v "$candidate" &> /dev/null; then
        PYTHON_BIN="$candidate"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "❌ خطأ: Python غير مثبت."
    echo "   ثبّت Python 3.11 من https://www.python.org/downloads/"
    exit 1
fi
echo "[OK] $($PYTHON_BIN --version)"
echo ""

# ── [2/5] Required libraries ─────────────────────────────────────
echo "[2/5] التحقق من المكتبات المطلوبة..."
if ! "$PYTHON_BIN" -c "import streamlit, plotly, pandas, numpy, cv2, sklearn, joblib" &> /dev/null; then
    echo "📥 تثبيت المكتبات المفقودة... (قد يستغرق دقائق)"
    "$PYTHON_BIN" -m pip install --quiet --upgrade pip >> "$LOG" 2>&1 || true
    "$PYTHON_BIN" -m pip install --quiet \
        streamlit plotly pandas numpy opencv-python openpyxl sqlalchemy \
        scikit-learn joblib >> "$LOG" 2>&1
    echo "[OK] تم تثبيت المكتبات."
else
    echo "[OK] جميع المكتبات مثبتة."
fi
echo ""

# ── [3/5] Database ───────────────────────────────────────────────
echo "[3/5] التحقق من قاعدة البيانات..."
if [ ! -f "$APP_DIR/skating_database.db" ]; then
    echo "إنشاء قاعدة البيانات..."
    "$PYTHON_BIN" import_all_data.py >> "$LOG" 2>&1 || \
        echo "⚠️  تحذير: فشل استيراد البيانات. سيبدأ النظام بقاعدة بيانات فاضية."
fi
echo "[OK] قاعدة البيانات جاهزة."
echo ""

echo "[3b/5] دمج بيانات Excel في قاعدة البيانات..."
"$PYTHON_BIN" merge_all_data.py >> "$LOG" 2>&1 && \
    echo "[OK] تم دمج كل بيانات Excel." || \
    echo "⚠️  تحذير: حدثت مشكلة في الدمج. راجع launch.log."
echo ""

# ── [4/5] Video scan ──────────────────────────────────────────────
echo "[4/5] مسح الجهاز عن ملفات الفيديو..."
"$PYTHON_BIN" setup_auto.py --scan-videos >> "$LOG" 2>&1 || true
echo "[OK] انتهى المسح. تحقق من النتائج داخل التطبيق."
echo ""

# ── [5/5] Launch ──────────────────────────────────────────────────
echo "════════════════════════════════════════════════════════════"
echo "🚀 بدء التطبيق..."
echo "   سيُفتح المتصفح على: http://localhost:8501"
echo "   للإيقاف: اضغط Ctrl+C"
echo "════════════════════════════════════════════════════════════"
echo ""

"$PYTHON_BIN" -m streamlit run final_app.py --browser.gatherUsageStats false
