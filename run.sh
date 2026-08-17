#!/bin/bash
#
# سكريبت تشغيل نظام تحليل التزلج الفني
# Figure Skating Analysis System - Run Script
#

echo "═══════════════════════════════════════════════════════════"
echo "   ⛸️  نظام تحليل التزلج الفني - Figure Skating Analysis"
echo "═══════════════════════════════════════════════════════════"
echo ""

# التحقق من Python وتثبيته تلقائياً إن لم يكن موجوداً
if ! command -v python3 &> /dev/null; then
    echo "⚠️  Python 3 غير مثبت — جارٍ محاولة التثبيت التلقائي..."
    echo ""

    OS_TYPE="$(uname -s)"

    if [ "$OS_TYPE" = "Linux" ]; then
        if command -v apt-get &> /dev/null; then
            echo "📥 تثبيت Python عبر apt-get (Debian/Ubuntu)..."
            sudo apt-get update -y && sudo apt-get install -y python3 python3-pip python3-venv
        elif command -v dnf &> /dev/null; then
            echo "📥 تثبيت Python عبر dnf (Fedora)..."
            sudo dnf install -y python3 python3-pip
        elif command -v yum &> /dev/null; then
            echo "📥 تثبيت Python عبر yum (CentOS/RHEL)..."
            sudo yum install -y python3 python3-pip
        elif command -v pacman &> /dev/null; then
            echo "📥 تثبيت Python عبر pacman (Arch)..."
            sudo pacman -Sy --noconfirm python python-pip
        else
            echo "❌ لم يتم التعرف على مدير الحزم. الرجاء تثبيت Python 3.10+ يدوياً من https://python.org"
            exit 1
        fi
    elif [ "$OS_TYPE" = "Darwin" ]; then
        if command -v brew &> /dev/null; then
            echo "📥 تثبيت Python عبر Homebrew (macOS)..."
            brew install python3
        else
            echo "❌ Homebrew غير مثبت. ثبّته أولاً من https://brew.sh ثم أعد المحاولة"
            echo "   أو نزّل Python يدوياً من https://python.org"
            exit 1
        fi
    else
        echo "❌ نظام التشغيل غير مدعوم للتثبيت التلقائي ($OS_TYPE)"
        echo "   الرجاء تثبيت Python 3.10 أو أحدث يدوياً من https://python.org"
        exit 1
    fi

    if ! command -v python3 &> /dev/null; then
        echo "❌ فشل تثبيت Python تلقائياً. الرجاء تثبيته يدوياً من https://python.org"
        exit 1
    fi

    echo "✅ تم تثبيت Python بنجاح"
    echo ""
fi

echo "✅ Python: $(python3 --version)"
echo ""

# التحقق من pip وتثبيته إن لزم
if ! python3 -m pip --version &> /dev/null; then
    echo "📥 تثبيت pip..."
    python3 -m ensurepip --upgrade 2>/dev/null || {
        if command -v apt-get &> /dev/null; then
            sudo apt-get install -y python3-pip
        fi
    }
fi

# التحقق من المتطلبات
echo "📦 التحقق من المتطلبات..."
if [ ! -f "skating_database.db" ]; then
    echo "⚠️  قاعدة البيانات غير موجودة، سيتم إنشاؤها تلقائياً عند أول تشغيل..."
fi

# تثبيت المتطلبات إذا لزم الأمر
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "📥 تثبيت المتطلبات..."
    pip install -q -r requirements.txt
    echo "✅ تم تثبيت المتطلبات"
else
    echo "✅ جميع المتطلبات مثبتة"
fi

# protobuf 5.x removes MessageFactory.GetPrototype, which mediapipe's
# generated _pb2 files still call — crashes with "'MessageFactory' object
# has no attribute 'GetPrototype'". Pin it down regardless of what else
# may have pulled in a newer protobuf.
if ! python3 -c "import google.protobuf as p, sys; sys.exit(0 if int(p.__version__.split('.')[0]) < 5 else 1)" &> /dev/null; then
    echo "🔧 تصحيح إصدار protobuf للتوافق مع MediaPipe..."
    pip install -q "protobuf>=3.20,<5"
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
streamlit run final_app.py
