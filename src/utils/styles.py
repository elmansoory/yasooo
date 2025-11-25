"""
أنماط CSS مخصصة للواجهة الاحترافية
"""

def get_custom_css():
    """الحصول على CSS مخصص للتطبيق"""
    return """
    <style>
    /* استيراد خطوط عربية احترافية */
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap');

    /* تطبيق الخط على كل العناصر */
    * {
        font-family: 'Cairo', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }

    /* تحسين الشريط الجانبي */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%);
        padding-top: 2rem;
    }

    [data-testid="stSidebar"] .css-1d391kg {
        padding: 2rem 1rem;
    }

    /* تحسين عنوان الشريط الجانبي */
    [data-testid="stSidebar"] h1 {
        color: #ffffff !important;
        text-align: center;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        margin-bottom: 2rem;
    }

    /* تحسين أزرار الراديو */
    [data-testid="stSidebar"] .stRadio > label {
        color: #e0e7ff !important;
        font-size: 1.1rem !important;
        font-weight: 500 !important;
    }

    [data-testid="stSidebar"] .stRadio > div {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 0.5rem;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label {
        background-color: rgba(255, 255, 255, 0.08) !important;
        border-radius: 8px !important;
        padding: 0.6rem 1rem !important;
        margin: 0.3rem 0 !important;
        transition: all 0.3s ease !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background-color: rgba(255, 255, 255, 0.15) !important;
        transform: translateX(-5px);
        border-color: rgba(255, 255, 255, 0.3) !important;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%) !important;
        border-color: #60a5fa !important;
        box-shadow: 0 4px 6px rgba(59, 130, 246, 0.3);
    }

    /* تحسين البطاقات الإحصائية */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
    }

    [data-testid="stMetric"] label {
        color: #ffffff !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
    }

    /* تنويع ألوان البطاقات */
    [data-testid="column"]:nth-child(1) [data-testid="stMetric"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    [data-testid="column"]:nth-child(2) [data-testid="stMetric"] {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }

    [data-testid="column"]:nth-child(3) [data-testid="stMetric"] {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }

    [data-testid="column"]:nth-child(4) [data-testid="stMetric"] {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
    }

    [data-testid="column"]:nth-child(5) [data-testid="stMetric"] {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    }

    /* تحسين العناوين */
    h1 {
        color: #1e40af !important;
        font-weight: 700 !important;
        font-size: 2.5rem !important;
        margin-bottom: 1.5rem !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }

    h2 {
        color: #2563eb !important;
        font-weight: 600 !important;
        font-size: 1.8rem !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
    }

    h3 {
        color: #3b82f6 !important;
        font-weight: 600 !important;
        font-size: 1.4rem !important;
        margin-top: 1.5rem !important;
    }

    /* تحسين الأزرار */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 10px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* تحسين الـ Expanders */
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, #f0f9ff 0%, #e0f2fe 100%);
        border-radius: 10px;
        border: 1px solid #bfdbfe;
        font-weight: 600;
        color: #1e40af !important;
        padding: 1rem;
        transition: all 0.3s ease;
    }

    .streamlit-expanderHeader:hover {
        background: linear-gradient(90deg, #dbeafe 0%, #bfdbfe 100%);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* تحسين التنبيهات */
    .stAlert {
        border-radius: 12px;
        border-left: 5px solid;
        padding: 1rem 1.5rem;
        font-weight: 500;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* تحسين الجداول */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* تحسين حقول الإدخال */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stDateInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e5e7eb;
        padding: 0.75rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }

    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stDateInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }

    /* تحسين الـ Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #f3f4f6;
        border-radius: 8px 8px 0 0;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        color: #6b7280;
        border: none;
        transition: all 0.3s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e5e7eb;
        color: #374151;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%) !important;
        color: white !important;
        box-shadow: 0 4px 6px rgba(59, 130, 246, 0.3);
    }

    /* تحسين الـ File Uploader */
    [data-testid="stFileUploader"] {
        border: 2px dashed #3b82f6;
        border-radius: 12px;
        padding: 2rem;
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        transition: all 0.3s ease;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: #2563eb;
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
    }

    /* تحسين الـ Download Button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(16, 185, 129, 0.3);
    }

    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 12px rgba(16, 185, 129, 0.4);
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
    }

    /* إضافة Animation للعناصر */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    [data-testid="stMetric"],
    .stAlert,
    .stDataFrame {
        animation: fadeIn 0.6s ease-out;
    }

    /* تحسين الـ Progress Bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }

    /* تحسين الـ Checkbox */
    .stCheckbox {
        padding: 0.5rem;
        transition: all 0.3s ease;
    }

    .stCheckbox:hover {
        background-color: rgba(59, 130, 246, 0.05);
        border-radius: 8px;
    }

    /* إخفاء العناصر غير الضرورية */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* تحسين المسافات */
    .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
        padding-left: 4rem;
        padding-right: 4rem;
    }

    /* تأثيرات إضافية للبطاقات */
    .card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        border: 1px solid #e5e7eb;
        transition: all 0.3s ease;
    }

    .card:hover {
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
        transform: translateY(-3px);
    }

    /* Gradient Text */
    .gradient-text {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
    }

    /* Badge Styles */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .badge-success {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
    }

    .badge-warning {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
    }

    .badge-danger {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
    }

    .badge-info {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
    }
    </style>
    """


def get_metric_card_html(title, value, icon, color="blue"):
    """إنشاء بطاقة إحصائية مخصصة بتصميم احترافي"""

    colors = {
        "blue": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "pink": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        "cyan": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
        "green": "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
        "orange": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
        "purple": "linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)",
    }

    gradient = colors.get(color, colors["blue"])

    return f"""
    <div style="
        background: {gradient};
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        text-align: center;
    ">
        <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{icon}</div>
        <div style="color: white; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.5rem;">
            {title}
        </div>
        <div style="color: white; font-size: 2rem; font-weight: 700; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);">
            {value}
        </div>
    </div>
    """


def get_alert_html(message, alert_type="info"):
    """إنشاء تنبيه مخصص بتصميم احترافي"""

    styles = {
        "success": {
            "bg": "linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)",
            "border": "#10b981",
            "icon": "✅",
            "color": "#065f46"
        },
        "warning": {
            "bg": "linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)",
            "border": "#f59e0b",
            "icon": "⚠️",
            "color": "#78350f"
        },
        "error": {
            "bg": "linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)",
            "border": "#ef4444",
            "icon": "❌",
            "color": "#7f1d1d"
        },
        "info": {
            "bg": "linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)",
            "border": "#3b82f6",
            "icon": "ℹ️",
            "color": "#1e3a8a"
        }
    }

    style = styles.get(alert_type, styles["info"])

    return f"""
    <div style="
        background: {style['bg']};
        border-left: 5px solid {style['border']};
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        gap: 1rem;
    ">
        <div style="font-size: 1.5rem;">{style['icon']}</div>
        <div style="color: {style['color']}; font-weight: 500; font-size: 1rem;">
            {message}
        </div>
    </div>
    """
