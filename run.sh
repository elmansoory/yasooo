#!/bin/bash
#
# سكريبت تشغيل نظام تحليل التزلج الفني
# Figure Skating Analysis System - Run Script
#

echo "═══════════════════════════════════════════════════════════"
echo "   ⛸️  نظام تحليل التزلج الفني - Figure Skating Analysis"
echo "═══════════════════════════════════════════════════════════"
echo ""

# التحقق من Python
if ! command -v python3 &> /dev/null; then
    echo "❌ خطأ: Python 3 غير مثبت"
    echo "   الرجاء تثبيت Python 3.10 أو أحدث"
    exit 1
fi

echo "✅ Python: $(python3 --version)"
echo ""

# التحقق من المتطلبات
echo "📦 التحقق من المتطلبات..."
if [ ! -f "skating_analysis.db" ]; then
    echo "⚠️  قاعدة البيانات غير موجودة، سيتم إنشاؤها..."
fi

# تثبيت المتطلبات إذا لزم الأمر
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "📥 تثبيت المتطلبات..."
    pip install -q -r requirements.txt
    echo "✅ تم تثبيت المتطلبات"
else
    echo "✅ جميع المتطلبات مثبتة"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "🚀 بدء التطبيق..."
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "💡 سيتم فتح التطبيق في المتصفح على:"
echo "   http://localhost:8501"
echo ""
echo "⌨️  للإيقاف: اضغط Ctrl+C"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

# تشغيل التطبيق
streamlit run app.py
