"""
نظام الثيم الحديث والمحسن
Modern Theme System for Better UX
"""

class ModernTheme:
    """ثيم عصري للتطبيق"""

    # الألوان الأساسية
    PRIMARY = "#667eea"
    SECONDARY = "#764ba2"
    SUCCESS = "#10b981"
    DANGER = "#ef4444"
    WARNING = "#f59e0b"
    INFO = "#3b82f6"

    # ألوان الخلفية
    BG_LIGHT = "#f8fafc"
    BG_DARK = "#1e293b"
    BG_GRADIENT = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"

    # ألوان النص
    TEXT_PRIMARY = "#1e293b"
    TEXT_SECONDARY = "#64748b"
    TEXT_LIGHT = "#ffffff"

    @staticmethod
    def get_css() -> str:
        """الحصول على CSS كامل للتطبيق"""
        return """
        <style>
        /* ========== إعدادات عامة ========== */
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap');

        * {
            font-family: 'Cairo', sans-serif !important;
        }

        .main {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
        }

        .stApp {
            max-width: 1600px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }

        /* ========== العناوين ========== */
        h1 {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            font-size: 3.5em;
            font-weight: 700;
            margin-bottom: 40px;
            animation: fadeInDown 1s ease;
        }

        h2 {
            color: #667eea;
            font-size: 2em;
            font-weight: 600;
            margin: 30px 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }

        h3 {
            color: #764ba2;
            font-size: 1.5em;
            font-weight: 600;
            margin: 20px 0 15px 0;
        }

        /* ========== البطاقات ========== */
        .metric-card {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            border: 2px solid transparent;
            position: relative;
            overflow: hidden;
        }

        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }

        .metric-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.3);
            border-color: #667eea;
        }

        /* ========== Metrics ========== */
        .stMetric {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
            border-left: 5px solid #667eea;
            transition: all 0.3s ease;
        }

        .stMetric:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.15);
        }

        .stMetric label {
            color: #64748b;
            font-size: 0.9em;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .stMetric [data-testid="stMetricValue"] {
            color: #667eea;
            font-size: 2.5em;
            font-weight: 700;
        }

        .stMetric [data-testid="stMetricDelta"] {
            font-size: 0.9em;
            font-weight: 600;
        }

        /* ========== الأزرار ========== */
        .stButton>button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 30px;
            font-weight: 600;
            font-size: 1.1em;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            cursor: pointer;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .stButton>button:hover {
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
        }

        .stButton>button:active {
            transform: translateY(-1px);
        }

        /* ========== المدخلات ========== */
        .stTextInput>div>div>input,
        .stSelectbox>div>div>select {
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            padding: 15px;
            font-size: 1em;
            transition: all 0.3s ease;
            background: white;
        }

        .stTextInput>div>div>input:focus,
        .stSelectbox>div>div>select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            outline: none;
        }

        /* ========== الجداول ========== */
        .dataframe {
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
            background: white;
        }

        .dataframe thead tr {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .dataframe thead th {
            padding: 15px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .dataframe tbody tr {
            transition: all 0.3s ease;
        }

        .dataframe tbody tr:hover {
            background: #f8fafc;
            transform: scale(1.01);
        }

        .dataframe tbody td {
            padding: 12px 15px;
        }

        /* ========== القائمة الجانبية ========== */
        .css-1d391kg {
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            padding: 30px 20px;
        }

        .sidebar .sidebar-content {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] label {
            color: white !important;
        }

        [data-testid="stSidebar"] .stRadio label {
            color: white;
            font-size: 1.1em;
            padding: 10px;
            border-radius: 8px;
            transition: all 0.3s ease;
        }

        [data-testid="stSidebar"] .stRadio label:hover {
            background: rgba(255, 255, 255, 0.2);
        }

        /* ========== Tabs ========== */
        .stTabs {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background: #f8fafc;
            padding: 10px;
            border-radius: 10px;
        }

        .stTabs [data-baseweb="tab"] {
            background: white;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: 600;
            transition: all 0.3s ease;
            border: 2px solid transparent;
        }

        .stTabs [data-baseweb="tab"]:hover {
            background: #f8fafc;
            border-color: #667eea;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
        }

        /* ========== Expander ========== */
        .streamlit-expanderHeader {
            background: white;
            border-radius: 10px;
            padding: 15px;
            font-weight: 600;
            font-size: 1.1em;
            border: 2px solid #e2e8f0;
            transition: all 0.3s ease;
        }

        .streamlit-expanderHeader:hover {
            border-color: #667eea;
            background: #f8fafc;
        }

        /* ========== Progress Bar ========== */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
        }

        /* ========== Alerts ========== */
        .stAlert {
            border-radius: 15px;
            padding: 20px;
            border-left: 5px solid;
        }

        [data-baseweb="notification"] {
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }

        /* ========== Animations ========== */
        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(30px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        /* ========== Spinner ========== */
        .stSpinner > div {
            border-top-color: #667eea !important;
        }

        /* ========== File Uploader ========== */
        [data-testid="stFileUploader"] {
            background: white;
            border: 2px dashed #667eea;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            transition: all 0.3s ease;
        }

        [data-testid="stFileUploader"]:hover {
            background: #f8fafc;
            border-color: #764ba2;
        }

        /* ========== Plotly Charts ========== */
        .js-plotly-plot {
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        }

        /* ========== Success Box ========== */
        .success-box {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
            margin: 20px 0;
        }

        /* ========== Info Box ========== */
        .info-box {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
            margin: 20px 0;
        }

        /* ========== Warning Box ========== */
        .warning-box {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3);
            margin: 20px 0;
        }

        /* ========== Responsive Design ========== */
        @media (max-width: 768px) {
            h1 {
                font-size: 2em;
            }

            .stApp {
                padding: 10px;
            }

            .metric-card {
                padding: 15px;
            }
        }

        /* ========== Dark Mode Support ========== */
        @media (prefers-color-scheme: dark) {
            .stApp {
                background: rgba(30, 41, 59, 0.95);
                color: #f8fafc;
            }

            .metric-card, .stMetric {
                background: #1e293b;
                color: #f8fafc;
            }

            .dataframe tbody tr:hover {
                background: #334155;
            }
        }

        /* ========== Custom Scrollbar ========== */
        ::-webkit-scrollbar {
            width: 12px;
        }

        ::-webkit-scrollbar-track {
            background: #f1f5f9;
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(180deg, #764ba2 0%, #667eea 100%);
        }

        /* ========== Loading Animation ========== */
        .loading {
            display: inline-block;
            width: 50px;
            height: 50px;
            border: 5px solid #f3f4f6;
            border-top-color: #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        </style>
        """

    @staticmethod
    def create_metric_card(title: str, value: str, delta: str = "", icon: str = "📊") -> str:
        """إنشاء بطاقة إحصائية مخصصة"""
        return f"""
        <div class="metric-card">
            <div style="font-size: 2em; margin-bottom: 10px;">{icon}</div>
            <div style="color: #64748b; font-size: 0.9em; font-weight: 500; text-transform: uppercase; margin-bottom: 10px;">
                {title}
            </div>
            <div style="color: #667eea; font-size: 2.5em; font-weight: 700; margin-bottom: 5px;">
                {value}
            </div>
            {f'<div style="color: #10b981; font-size: 0.9em; font-weight: 600;">{delta}</div>' if delta else ''}
        </div>
        """

    @staticmethod
    def create_alert_box(message: str, alert_type: str = "info") -> str:
        """إنشاء صندوق تنبيه"""
        class_name = f"{alert_type}-box"
        icons = {
            'success': '✅',
            'info': 'ℹ️',
            'warning': '⚠️',
            'danger': '❌'
        }
        icon = icons.get(alert_type, 'ℹ️')

        return f"""
        <div class="{class_name}">
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="font-size: 2em;">{icon}</div>
                <div style="font-size: 1.1em; font-weight: 500;">{message}</div>
            </div>
        </div>
        """
