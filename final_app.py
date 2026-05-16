"""
🏆 Figure Skating Analysis System - Final Version
نظام تحليل التزلج الفني - النسخة النهائية المُصلحة

✅ ALL errors fixed
✅ Language switching (Arabic/English)
✅ Works with or without AI libraries
✅ Graceful error handling
✅ Performance: cached DB queries
✅ Full attendance recording
✅ Member search & filter
✅ Rich statistics charts
"""

import streamlit as st
import pandas as pd
import sqlite3
import io
import os
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# ============================================================================
# LANGUAGE SYSTEM
# ============================================================================

TRANSLATIONS = {
    'ar': {
        'title': '⛸️ نظام تحليل التزلج الفني',
        'subtitle': 'النظام الشامل المتكامل',
        'menu': '📋 القائمة',
        'home': '🏠 الرئيسية',
        'members': '👥 الأعضاء',
        'attendance': '📊 الحضور',
        'ml_training': '🤖 تدريب النموذج ⭐',
        'referee': '🏅 واجهة الحكام',
        'video_analysis': '🎥 تحليل الفيديو',
        'my_videos': '🎬 فيديوهاتي',
        'stats': '📈 الإحصائيات',
        'settings': '⚙️ الإعدادات',
        'language': '🌐 اللغة',
        'total_members': 'إجمالي الأعضاء',
        'attendance_records': 'سجلات الحضور',
        'active_subscriptions': 'الاشتراكات النشطة',
        'ai_status': 'حالة AI',
        'members_management': 'إدارة الأعضاء',
        'no_members': 'لا يوجد أعضاء',
        'add_member': '➕ إضافة عضو',
        'search_members': '🔍 بحث عن عضو',
        'filter_by_level': 'فلتر حسب المستوى',
        'all_levels': 'كل المستويات',
        'name': 'الاسم',
        'age': 'العمر',
        'gender': 'الجنس',
        'phone': 'الهاتف',
        'email': 'البريد الإلكتروني',
        'skill_level': 'المستوى',
        'notes': 'ملاحظات',
        'male': 'ذكر',
        'female': 'أنثى',
        'beginner': 'مبتدئ',
        'intermediate': 'متوسط',
        'advanced': 'متقدم',
        'professional': 'محترف',
        'save': '💾 حفظ',
        'success': 'تم بنجاح',
        'error': 'خطأ',
        'ai_not_available': 'ميزات AI غير متاحة',
        'install_ai': 'لتفعيل ميزات AI، ثبّت',
        'core_features_work': 'الميزات الأساسية تعمل بدون AI',
        'record_attendance': '✅ تسجيل حضور',
        'select_member': 'اختر العضو',
        'attendance_date': 'التاريخ',
        'attendance_note': 'ملاحظة',
        'recent_attendance': 'آخر سجلات الحضور',
        'attendance_trend': 'اتجاه الحضور (آخر 30 يوم)',
        'members_by_gender': 'الأعضاء حسب الجنس',
        'members_by_level': 'الأعضاء حسب المستوى',
        'attendance_by_member': 'أكثر الأعضاء حضوراً',
        'no_data': 'لا توجد بيانات',
        'theme': 'المظهر',
        'dark_mode': 'الوضع الداكن',
        'light_mode': 'الوضع الفاتح',
        'db_path': 'مسار قاعدة البيانات',
        'clear_cache': '🗑️ مسح الذاكرة المؤقتة',
        'cache_cleared': 'تم مسح الذاكرة المؤقتة',
        'system_info': 'معلومات النظام',
        'today_attendance': 'حضور اليوم',
        'week_attendance': 'حضور الأسبوع',
        'no_attendance': 'لا توجد سجلات حضور',
        'player_progress': '📈 تقدم اللاعبين',
        'analysis_history': '🗂️ سجل التحليل',
        'payments': '💰 المدفوعات',
        'schedule': '📅 جدول التدريبات',
        'bulk_attendance': '📋 تسجيل جماعي',
        'unpaid': '⚠️ لم يدفع',
        'export_excel': '📥 تصدير Excel',
        'print_report': '🖨️ طباعة تقرير',
        'photo_upload': '📷 رفع صورة',
        'add_session': '➕ إضافة حصة',
        'weekly_schedule': '📅 الجدول الأسبوعي',
    },
    'en': {
        'title': '⛸️ Figure Skating Analysis System',
        'subtitle': 'Complete Integrated System',
        'menu': '📋 Menu',
        'home': '🏠 Home',
        'members': '👥 Members',
        'attendance': '📊 Attendance',
        'ml_training': '🤖 ML Training ⭐',
        'referee': '🏅 Referee Interface',
        'video_analysis': '🎥 Video Analysis',
        'my_videos': '🎬 My Videos',
        'stats': '📈 Statistics',
        'settings': '⚙️ Settings',
        'language': '🌐 Language',
        'total_members': 'Total Members',
        'attendance_records': 'Attendance Records',
        'active_subscriptions': 'Active Subscriptions',
        'ai_status': 'AI Status',
        'members_management': 'Members Management',
        'no_members': 'No members found',
        'add_member': '➕ Add Member',
        'search_members': '🔍 Search members',
        'filter_by_level': 'Filter by level',
        'all_levels': 'All Levels',
        'name': 'Name',
        'age': 'Age',
        'gender': 'Gender',
        'phone': 'Phone',
        'email': 'Email',
        'skill_level': 'Skill Level',
        'notes': 'Notes',
        'male': 'Male',
        'female': 'Female',
        'beginner': 'Beginner',
        'intermediate': 'Intermediate',
        'advanced': 'Advanced',
        'professional': 'Professional',
        'save': '💾 Save',
        'success': 'Success',
        'error': 'Error',
        'ai_not_available': 'AI features not available',
        'install_ai': 'To enable AI features, install',
        'core_features_work': 'Core features work without AI',
        'record_attendance': '✅ Record Attendance',
        'select_member': 'Select Member',
        'attendance_date': 'Date',
        'attendance_note': 'Note',
        'recent_attendance': 'Recent Attendance',
        'attendance_trend': 'Attendance Trend (last 30 days)',
        'members_by_gender': 'Members by Gender',
        'members_by_level': 'Members by Level',
        'attendance_by_member': 'Top Attending Members',
        'no_data': 'No data available',
        'theme': 'Theme',
        'dark_mode': 'Dark Mode',
        'light_mode': 'Light Mode',
        'db_path': 'Database Path',
        'clear_cache': '🗑️ Clear Cache',
        'cache_cleared': 'Cache cleared',
        'system_info': 'System Info',
        'today_attendance': "Today's Attendance",
        'week_attendance': 'This Week',
        'no_attendance': 'No attendance records',
        'player_progress': '📈 Player Progress',
        'analysis_history': '🗂️ Analysis History',
        'realtime': '📷 Real-Time Analysis',
        'club_mgmt': '🏢 Club Management',
        'payments': '💰 Payments',
        'schedule': '📅 Schedule',
        'bulk_attendance': '📋 Bulk Attendance',
        'unpaid': '⚠️ Unpaid',
        'export_excel': '📥 Export Excel',
        'print_report': '🖨️ Print Report',
        'photo_upload': '📷 Upload Photo',
        'add_session': '➕ Add Session',
        'weekly_schedule': '📅 Weekly Schedule',
        'logout': 'Logout',
        'login': 'Login',
        'username': 'Username',
        'password': 'Password',
    },
    'fr': {
        'title': '⛸️ Système d\'Analyse de Patinage Artistique',
        'subtitle': 'Système Complet Intégré',
        'menu': '📋 Menu',
        'home': '🏠 Accueil',
        'members': '👥 Membres',
        'attendance': '📊 Présence',
        'ml_training': '🤖 Entraînement ML ⭐',
        'referee': '🏅 Interface Arbitre',
        'video_analysis': '🎥 Analyse Vidéo',
        'stats': '📈 Statistiques',
        'settings': '⚙️ Paramètres',
        'language': '🌐 Langue',
        'total_members': 'Total Membres',
        'attendance_records': 'Présences',
        'active_subscriptions': 'Abonnements Actifs',
        'ai_status': 'État AI',
        'members_management': 'Gestion des Membres',
        'no_members': 'Aucun membre trouvé',
        'add_member': '➕ Ajouter Membre',
        'search_members': '🔍 Rechercher',
        'filter_by_level': 'Filtrer par niveau',
        'all_levels': 'Tous les niveaux',
        'name': 'Nom', 'age': 'Âge', 'gender': 'Genre',
        'phone': 'Téléphone', 'email': 'Email', 'skill_level': 'Niveau',
        'notes': 'Notes', 'male': 'Homme', 'female': 'Femme',
        'beginner': 'Débutant', 'intermediate': 'Intermédiaire',
        'advanced': 'Avancé', 'professional': 'Professionnel',
        'save': '💾 Enregistrer', 'success': 'Succès', 'error': 'Erreur',
        'ai_not_available': 'Fonctions AI non disponibles',
        'install_ai': 'Pour activer l\'AI, installez',
        'core_features_work': 'Fonctions de base disponibles sans AI',
        'record_attendance': '✅ Enregistrer Présence',
        'select_member': 'Choisir Membre', 'attendance_date': 'Date',
        'attendance_note': 'Note', 'recent_attendance': 'Présences Récentes',
        'attendance_trend': 'Tendance (30 derniers jours)',
        'members_by_gender': 'Membres par Genre',
        'members_by_level': 'Membres par Niveau',
        'attendance_by_member': 'Membres les plus présents',
        'no_data': 'Aucune donnée', 'theme': 'Thème',
        'dark_mode': 'Mode Sombre', 'light_mode': 'Mode Clair',
        'db_path': 'Chemin Base de Données',
        'clear_cache': '🗑️ Vider Cache', 'cache_cleared': 'Cache vidé',
        'system_info': 'Infos Système',
        'today_attendance': "Présence Aujourd'hui", 'week_attendance': 'Cette Semaine',
        'no_attendance': 'Aucune présence enregistrée',
        'player_progress': '📈 Progrès Joueurs',
        'analysis_history': '🗂️ Historique Analyses',
        'payments': '💰 Paiements',
        'schedule': '📅 Planning',
        'bulk_attendance': '📋 Présence Groupée',
        'unpaid': '⚠️ Impayés',
        'export_excel': '📥 Exporter Excel',
        'print_report': '🖨️ Imprimer',
        'photo_upload': '📷 Photo',
        'add_session': '➕ Ajouter',
        'weekly_schedule': '📅 Planning Semaine',
        'realtime': '📷 Analyse Temps Réel',
        'club_mgmt': '🏢 Gestion Club',
        'logout': 'Déconnexion', 'login': 'Connexion',
        'username': "Nom d'utilisateur", 'password': 'Mot de passe',
    },
    'de': {
        'title': '⛸️ Eiskunstlauf-Analysesystem',
        'subtitle': 'Vollständiges integriertes System',
        'menu': '📋 Menü',
        'home': '🏠 Startseite',
        'members': '👥 Mitglieder',
        'attendance': '📊 Anwesenheit',
        'ml_training': '🤖 ML-Training ⭐',
        'referee': '🏅 Schiedsrichter',
        'video_analysis': '🎥 Videoanalyse',
        'stats': '📈 Statistiken',
        'settings': '⚙️ Einstellungen',
        'language': '🌐 Sprache',
        'total_members': 'Gesamtmitglieder',
        'attendance_records': 'Anwesenheiten',
        'active_subscriptions': 'Aktive Mitgliedschaften',
        'ai_status': 'KI-Status',
        'members_management': 'Mitgliederverwaltung',
        'no_members': 'Keine Mitglieder',
        'add_member': '➕ Mitglied hinzufügen',
        'search_members': '🔍 Suchen',
        'filter_by_level': 'Nach Level filtern',
        'all_levels': 'Alle Levels',
        'name': 'Name', 'age': 'Alter', 'gender': 'Geschlecht',
        'phone': 'Telefon', 'email': 'E-Mail', 'skill_level': 'Level',
        'notes': 'Notizen', 'male': 'Männlich', 'female': 'Weiblich',
        'beginner': 'Anfänger', 'intermediate': 'Mittel',
        'advanced': 'Fortgeschritten', 'professional': 'Profi',
        'save': '💾 Speichern', 'success': 'Erfolg', 'error': 'Fehler',
        'ai_not_available': 'KI-Funktionen nicht verfügbar',
        'install_ai': 'Zur KI-Aktivierung installieren',
        'core_features_work': 'Grundfunktionen ohne KI verfügbar',
        'record_attendance': '✅ Anwesenheit erfassen',
        'select_member': 'Mitglied wählen', 'attendance_date': 'Datum',
        'attendance_note': 'Notiz', 'recent_attendance': 'Letzte Anwesenheiten',
        'attendance_trend': 'Trend (letzte 30 Tage)',
        'members_by_gender': 'Mitglieder nach Geschlecht',
        'members_by_level': 'Mitglieder nach Level',
        'attendance_by_member': 'Top-Anwesende',
        'no_data': 'Keine Daten', 'theme': 'Design',
        'dark_mode': 'Dunkelmodus', 'light_mode': 'Hellmodus',
        'db_path': 'Datenbankpfad',
        'clear_cache': '🗑️ Cache leeren', 'cache_cleared': 'Cache geleert',
        'system_info': 'Systeminfo',
        'today_attendance': 'Heutige Anwesenheit', 'week_attendance': 'Diese Woche',
        'no_attendance': 'Keine Anwesenheiten',
        'player_progress': '📈 Spielerfortschritt',
        'analysis_history': '🗂️ Analysehistorie',
        'payments': '💰 Zahlungen',
        'schedule': '📅 Trainingsplan',
        'bulk_attendance': '📋 Gruppenanwesenheit',
        'unpaid': '⚠️ Unbezahlt',
        'export_excel': '📥 Excel Export',
        'print_report': '🖨️ Drucken',
        'photo_upload': '📷 Foto',
        'add_session': '➕ Session Hinzufügen',
        'weekly_schedule': '📅 Wochenplan',
        'realtime': '📷 Echtzeit-Analyse',
        'club_mgmt': '🏢 Club-Verwaltung',
        'logout': 'Abmelden', 'login': 'Anmelden',
        'username': 'Benutzername', 'password': 'Passwort',
    },
    'ru': {
        'title': '⛸️ Система Анализа Фигурного Катания',
        'subtitle': 'Комплексная интегрированная система',
        'menu': '📋 Меню',
        'home': '🏠 Главная',
        'members': '👥 Участники',
        'attendance': '📊 Посещаемость',
        'ml_training': '🤖 Обучение ML ⭐',
        'referee': '🏅 Интерфейс Судьи',
        'video_analysis': '🎥 Анализ Видео',
        'stats': '📈 Статистика',
        'settings': '⚙️ Настройки',
        'language': '🌐 Язык',
        'total_members': 'Всего участников',
        'attendance_records': 'Записи посещений',
        'active_subscriptions': 'Активные подписки',
        'ai_status': 'Статус ИИ',
        'members_management': 'Управление участниками',
        'no_members': 'Участники не найдены',
        'add_member': '➕ Добавить участника',
        'search_members': '🔍 Поиск',
        'filter_by_level': 'Фильтр по уровню',
        'all_levels': 'Все уровни',
        'name': 'Имя', 'age': 'Возраст', 'gender': 'Пол',
        'phone': 'Телефон', 'email': 'Email', 'skill_level': 'Уровень',
        'notes': 'Заметки', 'male': 'Мужской', 'female': 'Женский',
        'beginner': 'Начинающий', 'intermediate': 'Средний',
        'advanced': 'Продвинутый', 'professional': 'Профессионал',
        'save': '💾 Сохранить', 'success': 'Успешно', 'error': 'Ошибка',
        'ai_not_available': 'Функции ИИ недоступны',
        'install_ai': 'Для активации ИИ установите',
        'core_features_work': 'Базовые функции работают без ИИ',
        'record_attendance': '✅ Записать посещение',
        'select_member': 'Выбрать участника', 'attendance_date': 'Дата',
        'attendance_note': 'Заметка', 'recent_attendance': 'Последние посещения',
        'attendance_trend': 'Тренд (последние 30 дней)',
        'members_by_gender': 'Участники по полу',
        'members_by_level': 'Участники по уровню',
        'attendance_by_member': 'Топ посещений',
        'no_data': 'Нет данных', 'theme': 'Тема',
        'dark_mode': 'Тёмный режим', 'light_mode': 'Светлый режим',
        'db_path': 'Путь к базе данных',
        'clear_cache': '🗑️ Очистить кэш', 'cache_cleared': 'Кэш очищен',
        'system_info': 'Информация о системе',
        'today_attendance': 'Посещений сегодня', 'week_attendance': 'На этой неделе',
        'no_attendance': 'Нет записей посещений',
        'player_progress': '📈 Прогресс игроков',
        'analysis_history': '🗂️ История анализов',
        'payments': '💰 Платежи',
        'schedule': '📅 Расписание',
        'bulk_attendance': '📋 Групповая Посещаемость',
        'unpaid': '⚠️ Неоплачено',
        'export_excel': '📥 Экспорт Excel',
        'print_report': '🖨️ Печать',
        'photo_upload': '📷 Фото',
        'add_session': '➕ Добавить',
        'weekly_schedule': '📅 Расписание Недели',
        'realtime': '📷 Анализ в реальном времени',
        'club_mgmt': '🏢 Управление клубом',
        'logout': 'Выйти', 'login': 'Войти',
        'username': 'Имя пользователя', 'password': 'Пароль',
    },
    'es': {
        'title': '⛸️ Sistema de Análisis de Patinaje Artístico',
        'subtitle': 'Sistema Completo Integrado',
        'menu': '📋 Menú',
        'home': '🏠 Inicio',
        'members': '👥 Miembros',
        'attendance': '📊 Asistencia',
        'ml_training': '🤖 Entrenamiento ML ⭐',
        'referee': '🏅 Interfaz Árbitro',
        'video_analysis': '🎥 Análisis de Video',
        'stats': '📈 Estadísticas',
        'settings': '⚙️ Configuración',
        'language': '🌐 Idioma',
        'total_members': 'Total Miembros',
        'attendance_records': 'Registros Asistencia',
        'active_subscriptions': 'Suscripciones Activas',
        'ai_status': 'Estado IA',
        'members_management': 'Gestión de Miembros',
        'no_members': 'No hay miembros',
        'add_member': '➕ Agregar Miembro',
        'search_members': '🔍 Buscar',
        'filter_by_level': 'Filtrar por nivel',
        'all_levels': 'Todos los niveles',
        'name': 'Nombre', 'age': 'Edad', 'gender': 'Género',
        'phone': 'Teléfono', 'email': 'Correo', 'skill_level': 'Nivel',
        'notes': 'Notas', 'male': 'Masculino', 'female': 'Femenino',
        'beginner': 'Principiante', 'intermediate': 'Intermedio',
        'advanced': 'Avanzado', 'professional': 'Profesional',
        'save': '💾 Guardar', 'success': 'Éxito', 'error': 'Error',
        'ai_not_available': 'Funciones IA no disponibles',
        'install_ai': 'Para activar IA, instale',
        'core_features_work': 'Funciones básicas disponibles sin IA',
        'record_attendance': '✅ Registrar Asistencia',
        'select_member': 'Seleccionar Miembro', 'attendance_date': 'Fecha',
        'attendance_note': 'Nota', 'recent_attendance': 'Asistencias Recientes',
        'attendance_trend': 'Tendencia (últimos 30 días)',
        'members_by_gender': 'Miembros por Género',
        'members_by_level': 'Miembros por Nivel',
        'attendance_by_member': 'Más Asistentes',
        'no_data': 'Sin datos', 'theme': 'Tema',
        'dark_mode': 'Modo Oscuro', 'light_mode': 'Modo Claro',
        'db_path': 'Ruta Base de Datos',
        'clear_cache': '🗑️ Limpiar Caché', 'cache_cleared': 'Caché limpiado',
        'system_info': 'Info del Sistema',
        'today_attendance': 'Asistencia Hoy', 'week_attendance': 'Esta Semana',
        'no_attendance': 'Sin registros de asistencia',
        'player_progress': '📈 Progreso Jugadores',
        'analysis_history': '🗂️ Historial Análisis',
        'payments': '💰 Pagos',
        'schedule': '📅 Horario',
        'bulk_attendance': '📋 Asistencia Grupal',
        'unpaid': '⚠️ Sin Pagar',
        'export_excel': '📥 Exportar Excel',
        'print_report': '🖨️ Imprimir',
        'photo_upload': '📷 Foto',
        'add_session': '➕ Agregar',
        'weekly_schedule': '📅 Horario Semanal',
        'realtime': '📷 Análisis Tiempo Real',
        'club_mgmt': '🏢 Gestión Club',
        'logout': 'Cerrar Sesión', 'login': 'Iniciar Sesión',
        'username': 'Usuario', 'password': 'Contraseña',
    },
}


if 'language' not in st.session_state:
    st.session_state.language = 'ar'

LANG_NAMES = {
    'ar': '🇸🇦 العربية',
    'en': '🇬🇧 English',
    'fr': '🇫🇷 Français',
    'de': '🇩🇪 Deutsch',
    'ru': '🇷🇺 Русский',
    'es': '🇪🇸 Español',
}

def t(key):
    lang = st.session_state.get('language', 'ar')
    return TRANSLATIONS.get(lang, TRANSLATIONS['ar']).get(key, TRANSLATIONS['en'].get(key, key))

def switch_language():
    langs = list(LANG_NAMES.keys())
    current = st.session_state.get('language', 'ar')
    next_lang = langs[(langs.index(current) + 1) % len(langs)]
    st.session_state.language = next_lang
    st.rerun()

# ============================================================================
# AI LIBRARIES CHECK
# ============================================================================

CORE_AI_AVAILABLE = False
MEDIAPIPE_AVAILABLE = False
CV2_AVAILABLE = False
ANALYZER_AVAILABLE = False

try:
    import numpy as np
    CORE_AI_AVAILABLE = True
except ImportError:
    pass

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    pass

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    pass

if CORE_AI_AVAILABLE:
    try:
        from src.ai.advanced_analyzer import AdvancedSkatingAnalyzer
        ANALYZER_AVAILABLE = True
    except Exception:
        pass

# ============================================================================
# DATABASE
# ============================================================================

def init_db():
    conn = sqlite3.connect('skating_database.db')
    c = conn.cursor()
    # skaters, attendance, payments are created by merge_all_data.py
    # Only ensure legacy tables exist so old code paths don't crash
    c.execute("""CREATE TABLE IF NOT EXISTS skaters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        coach_name TEXT,
        level TEXT,
        bundle TEXT,
        membership_status TEXT DEFAULT 'active',
        gender TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skater_name TEXT,
        skater_id INTEGER,
        date TEXT,
        session_type TEXT,
        status TEXT,
        coach TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skater_id INTEGER,
        skater_name TEXT,
        amount REAL,
        payment_date TEXT,
        payment_method TEXT,
        bundle_type TEXT,
        discount REAL DEFAULT 0,
        received_by TEXT,
        status TEXT DEFAULT 'completed',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    conn.close()

@st.cache_resource
def setup_db():
    init_db()
    return True

def get_conn():
    return sqlite3.connect('skating_database.db')

@st.cache_data(ttl=30)
def load_members():
    try:
        conn = get_conn()
        df = pd.read_sql_query(
            "SELECT id AS member_id, name, gender, level AS skill_level, "
            "bundle, membership_status, coach_name, notes, created_at FROM skaters",
            conn
        )
        conn.close()
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=30)
def load_attendance():
    try:
        conn = get_conn()
        df = pd.read_sql_query(
            "SELECT id, skater_name, skater_id, date AS attendance_date, "
            "session_type, status, coach FROM attendance ORDER BY date DESC",
            conn
        )
        conn.close()
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=30)
def load_memberships():
    try:
        conn = get_conn()
        df = pd.read_sql_query(
            "SELECT id, skater_id, skater_name, amount, payment_date, "
            "bundle_type, status FROM payments ORDER BY payment_date DESC",
            conn
        )
        conn.close()
        return df
    except:
        return pd.DataFrame()

def invalidate_cache():
    load_members.clear()
    load_attendance.clear()
    load_memberships.clear()

def calc_age(birth_date):
    try:
        if pd.isna(birth_date) or birth_date == '':
            return 0
        birth = datetime.strptime(str(birth_date), '%Y-%m-%d')
        today = date.today()
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    except:
        return 0

# ============================================================================
# UTILITIES
# ============================================================================

def _df_to_excel(df: pd.DataFrame, sheet_name: str = 'Data') -> bytes:
    """Convert DataFrame to Excel bytes (falls back to CSV-UTF8 if openpyxl missing)."""
    buf = io.BytesIO()
    try:
        with pd.ExcelWriter(buf, engine='openpyxl') as w:
            df.to_excel(w, index=False, sheet_name=sheet_name)
        return buf.getvalue()
    except Exception:
        return df.to_csv(index=False).encode('utf-8-sig')

def _excel_ext() -> str:
    try:
        import openpyxl
        return '.xlsx'
    except ImportError:
        return '.csv'

def _excel_mime() -> str:
    try:
        import openpyxl
        return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    except ImportError:
        return 'text/csv'

PHOTOS_DIR = Path('data/photos')

def _save_photo(name: str, uploaded_file) -> str:
    """Save uploaded photo and return path."""
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    safe = name.replace(' ', '_').replace('/', '_')
    ext  = Path(uploaded_file.name).suffix or '.jpg'
    dest = PHOTOS_DIR / f"{safe}{ext}"
    dest.write_bytes(uploaded_file.read())
    conn = get_conn()
    conn.execute("UPDATE skaters SET notes=COALESCE(notes,'') WHERE name=?", (name,))
    conn.commit()
    conn.close()
    return str(dest)

def _init_schedule_table():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS training_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_of_week INTEGER NOT NULL,
            start_time  TEXT NOT NULL,
            end_time    TEXT NOT NULL,
            level       TEXT,
            coach       TEXT,
            session_type TEXT DEFAULT 'on-ice',
            max_capacity INTEGER DEFAULT 15,
            notes       TEXT,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Figure Skating Analysis",
    page_icon="⛸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.main{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);background-attachment:fixed;}
.block-container{background:rgba(255,255,255,0.98);border-radius:20px;padding:2rem;box-shadow:0 15px 40px rgba(0,0,0,0.3);}
h1{color:#667eea;text-align:center;font-weight:800;}
h2,h3{color:#764ba2;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#667eea 0%,#764ba2 100%);}
[data-testid="stSidebar"] *{color:white !important;}
.stButton>button{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:12px;padding:12px 28px;font-weight:700;transition:transform 0.1s;}
.stButton>button:hover{transform:scale(1.03);}
[data-testid="stMetricValue"]{font-size:2rem;color:#667eea;font-weight:700;}
.stDataFrame{border-radius:12px;overflow:hidden;}
div[data-testid="stExpander"]{border:1px solid #e2e8f0;border-radius:12px;}
.search-box input{border-radius:10px !important;}
</style>
""", unsafe_allow_html=True)

setup_db()

# ============================================================================
# SIDEBAR
# ============================================================================

st.sidebar.title(t('menu'))

# Language selector — 6 languages
current_lang = st.session_state.get('language', 'ar')
lang_choice = st.sidebar.selectbox(
    '🌐', list(LANG_NAMES.keys()),
    index=list(LANG_NAMES.keys()).index(current_lang),
    format_func=lambda k: LANG_NAMES[k],
    label_visibility='collapsed',
)
if lang_choice != current_lang:
    st.session_state.language = lang_choice
    st.rerun()

# Auth status in sidebar
try:
    from src.auth.auth_manager import seed_demo_data
    seed_demo_data()
    user = st.session_state.get('user')
    if user:
        role_icon = {'admin': '👑', 'club_manager': '🏢', 'coach': '🎿', 'athlete': '⛸️'}.get(user.get('role', ''), '👤')
        st.sidebar.markdown(f"""
        <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:8px 12px;margin:6px 0">
            <div style="font-weight:700">{role_icon} {user.get('full_name', user.get('username',''))}</div>
            <div style="font-size:.8em;opacity:.8">{user.get('club_name','')}</div>
        </div>""", unsafe_allow_html=True)
        if st.sidebar.button(t('logout'), use_container_width=True):
            for k in ['user', 'authenticated', 'club_id']:
                st.session_state.pop(k, None)
            st.rerun()
except Exception:
    pass

st.sidebar.markdown("---")

_nav_pages = [
    t('home'),
    t('members'),
    t('attendance'),
    t('payments'),
    t('schedule'),
    t('video_analysis'),
    t('my_videos'),
    t('realtime'),
    t('player_progress'),
    t('analysis_history'),
    t('ml_training'),
    t('referee'),
    t('stats'),
    t('club_mgmt'),
    t('settings'),
]
page = st.sidebar.radio("", _nav_pages)

# ============================================================================
# HOME PAGE
# ============================================================================

def show_home():
    st.markdown(f'<h1>{t("title")}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align:center;font-size:1.3em;color:#64748b;">{t("subtitle")}</p>', unsafe_allow_html=True)

    members = load_members()
    attendance = load_attendance()
    memberships = load_memberships()

    today_str = date.today().isoformat()
    week_ago_str = (date.today() - timedelta(days=7)).isoformat()

    today_att = 0
    week_att = 0
    if len(attendance) > 0 and 'attendance_date' in attendance.columns:
        today_att = len(attendance[attendance['attendance_date'] == today_str])
        week_att = len(attendance[attendance['attendance_date'] >= week_ago_str])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(t('total_members'), len(members))
    with col2:
        st.metric(t('today_attendance'), today_att)
    with col3:
        st.metric(t('week_attendance'), week_att)
    with col4:
        active_count = 0
        if 'membership_status' in members.columns:
            active_count = len(members[members['membership_status'] == 'active'])
        st.metric(t('active_subscriptions'), active_count)

    st.markdown("---")

    col1, col2 = st.columns(2)

    # Attendance trend chart
    with col1:
        if len(attendance) > 0 and 'attendance_date' in attendance.columns:
            st.subheader(t('attendance_trend'))
            cutoff = (date.today() - timedelta(days=30)).isoformat()
            recent = attendance[attendance['attendance_date'] >= cutoff].copy()
            if len(recent) > 0:
                trend = recent.groupby('attendance_date').size().reset_index(name='count')
                trend['attendance_date'] = pd.to_datetime(trend['attendance_date'])
                fig = px.bar(
                    trend, x='attendance_date', y='count',
                    color_discrete_sequence=['#667eea'],
                    labels={'attendance_date': '', 'count': ''},
                )
                fig.update_layout(
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=220,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                )
                st.plotly_chart(fig, use_container_width=True)

    # Level distribution
    with col2:
        if len(members) > 0 and 'skill_level' in members.columns and members['skill_level'].notna().any():
            st.subheader(t('members_by_level'))
            level_counts = members['skill_level'].value_counts().reset_index()
            level_counts.columns = ['level', 'count']
            fig = px.bar(
                level_counts, x='level', y='count',
                color='count',
                color_continuous_scale=['#667eea', '#764ba2'],
                labels={'level': '', 'count': ''},
            )
            fig.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                height=220,
                coloraxis_showscale=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig, use_container_width=True)

    if not CORE_AI_AVAILABLE:
        st.warning(f"⚠️ {t('ai_not_available')}")
        st.info(f"""
        {t('install_ai')}:
        ```
        pip install numpy opencv-python
        ```
        ✅ {t('core_features_work')}
        """)
    elif not MEDIAPIPE_AVAILABLE:
        st.info("ℹ️ MediaPipe غير متاح (لا يدعم Python 3.13 بعد). ميزات تحليل الحركة معطّلة، باقي الميزات تعمل.")

# ============================================================================
# MEMBERS PAGE
# ============================================================================

def show_members():
    st.header(t('members_management'))

    members = load_members()

    if len(members) > 0:
        if 'birth_date' in members.columns:
            members['age'] = members['birth_date'].apply(calc_age)

        # Search & filter row
        col_search, col_filter = st.columns([3, 1])
        with col_search:
            search = st.text_input(t('search_members'), placeholder=t('name'), label_visibility='collapsed')
        with col_filter:
            all_label = t('all_levels')
            actual_levels = sorted(members['skill_level'].dropna().unique().tolist()) if 'skill_level' in members.columns else []
            levels = [all_label] + actual_levels
            selected_level = st.selectbox(t('filter_by_level'), levels, label_visibility='collapsed')

        filtered = members.copy()
        if search:
            filtered = filtered[filtered['name'].str.contains(search, case=False, na=False)]
        if selected_level != all_label and 'skill_level' in filtered.columns:
            filtered = filtered[filtered['skill_level'] == selected_level]

        display_cols = [c for c in ['name', 'gender', 'skill_level', 'bundle', 'membership_status', 'coach_name'] if c in filtered.columns]
        if display_cols:
            st.dataframe(filtered[display_cols], use_container_width=True, height=350)
            # Export buttons
            col_ex1, col_ex2 = st.columns(2)
            with col_ex1:
                st.download_button(
                    t('export_excel'),
                    data=_df_to_excel(filtered[display_cols], 'Members'),
                    file_name=f"members{_excel_ext()}",
                    mime=_excel_mime(),
                    use_container_width=True,
                )
            with col_ex2:
                # Printable HTML summary
                html_rows = "".join(
                    f"<tr><td>{r['name']}</td><td>{r.get('skill_level','')}</td>"
                    f"<td>{r.get('bundle','')}</td><td>{r.get('coach_name','')}</td></tr>"
                    for _, r in filtered[display_cols].iterrows()
                )
                html_report = f"""<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8">
<style>body{{font-family:Arial;direction:rtl}} table{{border-collapse:collapse;width:100%}}
td,th{{border:1px solid #ccc;padding:6px 10px;text-align:right}}
th{{background:#667eea;color:white}} @media print{{button{{display:none}}}}</style></head>
<body><h2>قائمة الأعضاء - {date.today()}</h2>
<p>العدد: {len(filtered)}</p>
<table><thead><tr><th>الاسم</th><th>المستوى</th><th>الباقة</th><th>المدرب</th></tr></thead>
<tbody>{html_rows}</tbody></table>
<br><button onclick="window.print()">🖨️ طباعة</button></body></html>"""
                st.download_button(
                    t('print_report'),
                    data=html_report.encode('utf-8'),
                    file_name="members_report.html",
                    mime="text/html",
                    use_container_width=True,
                )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(t('total_members'), len(filtered))
        if 'gender' in members.columns:
            male_vals = ['Male', 'ذكر', 'Männlich', 'Masculino', 'Мужской']
            female_vals = ['Female', 'أنثى', 'Weiblich', 'Femenino', 'Женский']
            with col2:
                st.metric(t('male'), len(members[members['gender'].isin(male_vals)]))
            with col3:
                st.metric(t('female'), len(members[members['gender'].isin(female_vals)]))
    else:
        st.info(t('no_members'))

    # ── Member profile detail ────────────────────────────────────────────────
    if len(members) > 0 and 'name' in members.columns:
        st.markdown("---")
        st.subheader("👤 " + ("ملف اللاعب التفصيلي" if st.session_state.language == 'ar' else "Player Profile"))
        selected_profile = st.selectbox(
            "اختر لاعباً" if st.session_state.language == 'ar' else "Select player",
            ["—"] + sorted(members['name'].tolist()),
            key="profile_select"
        )
        if selected_profile != "—":
            row = members[members['name'] == selected_profile].iloc[0]

            # Photo + basic info
            col_photo, col_info = st.columns([1, 3])
            with col_photo:
                safe_name = selected_profile.replace(' ', '_').replace('/', '_')
                photo_found = False
                for ext in ['.jpg','.jpeg','.png','.webp']:
                    pp = PHOTOS_DIR / f"{safe_name}{ext}"
                    if pp.exists():
                        st.image(str(pp), width=140)
                        photo_found = True
                        break
                if not photo_found:
                    st.markdown(
                        "<div style='width:120px;height:120px;background:#667eea;border-radius:50%;"
                        "display:flex;align-items:center;justify-content:center;"
                        "color:white;font-size:2.5em'>👤</div>",
                        unsafe_allow_html=True
                    )
                uploaded_photo = st.file_uploader(
                    t('photo_upload'), type=['jpg','jpeg','png','webp'],
                    key=f"photo_{selected_profile}"
                )
                if uploaded_photo:
                    _save_photo(selected_profile, uploaded_photo)
                    st.success("✅ تم رفع الصورة")
                    st.rerun()

            with col_info:
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Level", row.get('skill_level') or '—')
                with c2:
                    st.metric("Bundle", row.get('bundle') or '—')
                with c3:
                    st.metric("Status", row.get('membership_status') or '—')
                if row.get('coach_name'):
                    st.write(f"**Coach:** {row['coach_name']}")

            # Attendance history for this player
            try:
                conn = get_conn()
                att_df = pd.read_sql_query(
                    "SELECT date AS attendance_date, session_type, status FROM attendance "
                    "WHERE skater_name=? ORDER BY date DESC LIMIT 30",
                    conn, params=(selected_profile,)
                )
                conn.close()
                if len(att_df) > 0:
                    total = len(att_df)
                    present = len(att_df[att_df['status'] == 'present'])
                    rate = round(present / total * 100) if total > 0 else 0
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Total Sessions", total)
                    c2.metric("Present", present)
                    c3.metric("Attendance Rate", f"{rate}%")
                    st.dataframe(att_df, use_container_width=True, height=200)
            except Exception:
                pass

            # Skills from player_skills
            try:
                conn = get_conn()
                skills_df = pd.read_sql_query(
                    "SELECT element_name, fse_level, achieved FROM player_skills "
                    "WHERE skater_name=? ORDER BY fse_level, element_name",
                    conn, params=(selected_profile,)
                )
                conn.close()
                if len(skills_df) > 0:
                    st.write(f"**Skills ({len(skills_df)} elements):**")
                    achieved = skills_df[skills_df['achieved'] == 1]
                    pending = skills_df[skills_df['achieved'] != 1]
                    c1, c2 = st.columns(2)
                    with c1:
                        st.success(f"✅ Achieved: {len(achieved)}")
                        if len(achieved) > 0:
                            st.dataframe(achieved[['element_name', 'fse_level']], use_container_width=True, height=180)
                    with c2:
                        st.warning(f"⏳ Pending: {len(pending)}")
                        if len(pending) > 0:
                            st.dataframe(pending[['element_name', 'fse_level']], use_container_width=True, height=180)
            except Exception:
                pass

    with st.expander(t('add_member')):
        with st.form("add_member"):
            name = st.text_input(t('name') + " *")
            col1, col2 = st.columns(2)
            with col1:
                gender = st.selectbox(t('gender'), [t('male'), t('female')])
            with col2:
                level = st.selectbox(t('skill_level'),
                                     ['Beta', 'Gamma', 'Delta', 'Pre-Freestyle', 'Freestyle'])
            col1, col2 = st.columns(2)
            with col1:
                coach_name = st.text_input('Coach')
            with col2:
                bundle = st.text_input('Bundle')
            notes = st.text_area(t('notes'))
            submitted = st.form_submit_button(t('save'))
            if submitted and name:
                try:
                    conn = get_conn()
                    c = conn.cursor()
                    c.execute("""INSERT OR IGNORE INTO skaters
                               (name, gender, level, coach_name, bundle, notes)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                              (name, gender, level, coach_name, bundle, notes))
                    conn.commit()
                    conn.close()
                    invalidate_cache()
                    st.success(f"✅ {t('success')}: {name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"{t('error')}: {str(e)}")

# ============================================================================
# ATTENDANCE PAGE
# ============================================================================

def show_attendance():
    st.header(t('attendance'))

    attendance = load_attendance()
    members = load_members()

    # Summary metrics
    today_str = date.today().isoformat()
    week_ago_str = (date.today() - timedelta(days=7)).isoformat()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(t('attendance_records'), len(attendance))
    with col2:
        today_count = 0
        if len(attendance) > 0 and 'attendance_date' in attendance.columns:
            today_count = len(attendance[attendance['attendance_date'] == today_str])
        st.metric(t('today_attendance'), today_count)
    with col3:
        week_count = 0
        if len(attendance) > 0 and 'attendance_date' in attendance.columns:
            week_count = len(attendance[attendance['attendance_date'] >= week_ago_str])
        st.metric(t('week_attendance'), week_count)

    st.markdown("---")

    # Attendance recording tabs
    tab_a1, tab_a2 = st.tabs([
        "✅ " + ("تسجيل فردي" if st.session_state.language == 'ar' else "Single Record"),
        "📋 " + t('bulk_attendance'),
    ])

    with tab_a1:
        if len(members) == 0:
            st.warning(t('no_members'))
        else:
            with st.form("record_attendance"):
                skater_names = sorted(members['name'].tolist()) if 'name' in members.columns else []
                selected_name = st.selectbox(t('select_member'), skater_names)
                att_date = st.date_input(t('attendance_date'), value=date.today())
                session_type = st.selectbox('Session', ['on-ice', 'off-ice', 'competition'])
                att_status = st.selectbox('Status', ['present', 'absent', 'late', 'excused'])
                submitted = st.form_submit_button(t('record_attendance'))
                if submitted and selected_name:
                    try:
                        conn = get_conn()
                        c = conn.cursor()
                        row = conn.execute("SELECT id FROM skaters WHERE name=?", (selected_name,)).fetchone()
                        skater_id = row[0] if row else None
                        c.execute("INSERT INTO attendance (skater_name, skater_id, date, session_type, status) VALUES (?,?,?,?,?)",
                                  (selected_name, skater_id, str(att_date), session_type, att_status))
                        conn.commit()
                        conn.close()
                        invalidate_cache()
                        st.success(f"✅ {t('success')}: {selected_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"{t('error')}: {str(e)}")

    with tab_a2:
        is_ar_att = st.session_state.language == 'ar'
        if len(members) == 0:
            st.warning(t('no_members'))
        else:
            with st.form("bulk_attendance"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    bulk_date = st.date_input("التاريخ" if is_ar_att else "Date", value=date.today())
                with c2:
                    bulk_session = st.selectbox("النوع" if is_ar_att else "Session Type", ['on-ice','off-ice','competition'])
                with c3:
                    bulk_coach = st.text_input("المدرب" if is_ar_att else "Coach")

                # Filter by level for easier bulk selection
                all_levels = ['All / الكل'] + sorted(members['skill_level'].dropna().unique().tolist()) if 'skill_level' in members.columns else ['All / الكل']
                bulk_level_filter = st.selectbox("فلتر حسب المستوى" if is_ar_att else "Filter by Level", all_levels)

                filtered_members_bulk = members.copy()
                if bulk_level_filter != 'All / الكل' and 'skill_level' in filtered_members_bulk.columns:
                    filtered_members_bulk = filtered_members_bulk[filtered_members_bulk['skill_level'] == bulk_level_filter]

                all_names = sorted(filtered_members_bulk['name'].tolist()) if 'name' in filtered_members_bulk.columns else []
                selected_bulk = st.multiselect(
                    "✅ " + ("اختر الحاضرين" if is_ar_att else "Select Present Members"),
                    all_names, default=all_names
                )
                absent_bulk = [n for n in all_names if n not in selected_bulk]

                st.info(f"حاضر: {len(selected_bulk)} | غائب: {len(absent_bulk)}" if is_ar_att else
                        f"Present: {len(selected_bulk)} | Absent: {len(absent_bulk)}")

                bulk_sub = st.form_submit_button(
                    f"💾 {'حفظ الجلسة' if is_ar_att else 'Save Session'} ({len(all_names)} {'لاعب' if is_ar_att else 'players'})",
                    type="primary"
                )
                if bulk_sub and all_names:
                    try:
                        conn = get_conn()
                        rows_to_insert = [(n, None, str(bulk_date), bulk_session, 'present', bulk_coach or None)
                                          for n in selected_bulk]
                        rows_to_insert += [(n, None, str(bulk_date), bulk_session, 'absent', bulk_coach or None)
                                           for n in absent_bulk]
                        conn.executemany(
                            "INSERT INTO attendance (skater_name, skater_id, date, session_type, status, coach) VALUES (?,?,?,?,?,?)",
                            rows_to_insert
                        )
                        conn.commit()
                        conn.close()
                        invalidate_cache()
                        st.success(f"✅ {'تم تسجيل' if is_ar_att else 'Saved'} {len(rows_to_insert)} {'سجل' if is_ar_att else 'records'}")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    # Attendance analytics
    if len(attendance) > 0:
        st.markdown("---")

        # Session type breakdown
        if 'session_type' in attendance.columns and attendance['session_type'].notna().any():
            col1, col2 = st.columns(2)
            with col1:
                type_counts = attendance['session_type'].value_counts().reset_index()
                type_counts.columns = ['type', 'count']
                fig = px.pie(type_counts, values='count', names='type',
                             title="On-Ice vs Off-Ice",
                             color_discrete_sequence=['#667eea', '#764ba2', '#f093fb'])
                fig.update_layout(height=260, margin=dict(l=0,r=0,t=40,b=0))
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                if 'attendance_date' in attendance.columns:
                    cutoff = (date.today() - timedelta(days=60)).isoformat()
                    trend = attendance[attendance['attendance_date'] >= cutoff].copy()
                    if len(trend) > 0:
                        t_grp = trend.groupby('attendance_date').size().reset_index(name='count')
                        t_grp['attendance_date'] = pd.to_datetime(t_grp['attendance_date'])
                        fig = px.bar(t_grp, x='attendance_date', y='count',
                                     title="الحضور خلال 60 يوم",
                                     color_discrete_sequence=['#667eea'],
                                     labels={'attendance_date': '', 'count': ''})
                        fig.update_layout(height=260, margin=dict(l=0,r=0,t=40,b=0),
                                          plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig, use_container_width=True)

        st.subheader(t('recent_attendance'))

        # Filters
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            search_att = st.text_input("🔍 " + t('search_members'), key="att_search")
        with col_f2:
            sess_types = ['All'] + sorted(attendance['session_type'].dropna().unique().tolist()) if 'session_type' in attendance.columns else ['All']
            sel_type = st.selectbox("Session Type", sess_types, key="att_type")
        with col_f3:
            statuses = ['All'] + sorted(attendance['status'].dropna().unique().tolist()) if 'status' in attendance.columns else ['All']
            sel_status = st.selectbox("Status", statuses, key="att_status")

        display_att = attendance.copy()
        if search_att:
            display_att = display_att[display_att['skater_name'].str.contains(search_att, case=False, na=False)]
        if sel_type != 'All' and 'session_type' in display_att.columns:
            display_att = display_att[display_att['session_type'] == sel_type]
        if sel_status != 'All' and 'status' in display_att.columns:
            display_att = display_att[display_att['status'] == sel_status]

        try:
            cols_to_show = [c for c in ['skater_name', 'attendance_date', 'session_type', 'status', 'coach'] if c in display_att.columns]
            if cols_to_show:
                st.dataframe(display_att[cols_to_show].head(100), use_container_width=True, height=350)
            st.caption(f"Showing {min(100, len(display_att))} of {len(display_att)} records")
            # Export
            col_xe1, col_xe2 = st.columns(2)
            with col_xe1:
                st.download_button(
                    t('export_excel'),
                    data=_df_to_excel(display_att[cols_to_show] if cols_to_show else display_att, 'Attendance'),
                    file_name=f"attendance{_excel_ext()}",
                    mime=_excel_mime(),
                    use_container_width=True,
                )
            with col_xe2:
                # Printable HTML attendance sheet
                is_ar_pr = st.session_state.language == 'ar'
                att_rows = "".join(
                    f"<tr><td>{r.get('skater_name','')}</td><td>{r.get('attendance_date','')}</td>"
                    f"<td>{r.get('session_type','')}</td><td>{r.get('status','')}</td>"
                    f"<td>{r.get('coach','')}</td></tr>"
                    for _, r in display_att[cols_to_show].head(200).iterrows()
                )
                html_att = f"""<!DOCTYPE html><html dir="{'rtl' if is_ar_pr else 'ltr'}">
<head><meta charset="utf-8"><style>
body{{font-family:Arial;direction:{'rtl' if is_ar_pr else 'ltr'}}}
table{{border-collapse:collapse;width:100%}} td,th{{border:1px solid #ccc;padding:5px 8px}}
th{{background:#667eea;color:white}} @media print{{button{{display:none}}}}</style></head>
<body><h2>{'كشف الحضور' if is_ar_pr else 'Attendance Report'} — {date.today()}</h2>
<p>{'العدد' if is_ar_pr else 'Count'}: {len(display_att)}</p>
<table><thead><tr><th>{'الاسم' if is_ar_pr else 'Name'}</th>
<th>{'التاريخ' if is_ar_pr else 'Date'}</th>
<th>{'النوع' if is_ar_pr else 'Type'}</th>
<th>{'الحالة' if is_ar_pr else 'Status'}</th>
<th>{'المدرب' if is_ar_pr else 'Coach'}</th></tr></thead>
<tbody>{att_rows}</tbody></table>
<br><button onclick="window.print()">🖨️ {'طباعة' if is_ar_pr else 'Print'}</button></body></html>"""
                st.download_button(
                    t('print_report'),
                    data=html_att.encode('utf-8'),
                    file_name="attendance_report.html",
                    mime="text/html",
                    use_container_width=True,
                )
        except Exception as e:
            st.error(f"Display error: {e}")
    else:
        st.info(t('no_attendance'))

# ============================================================================
# AI PAGES
# ============================================================================

def show_ml_training():
    try:
        from src.pages.model_training_page import show_model_training_page
        show_model_training_page(lang=st.session_state.language)
        return
    except Exception:
        pass
    st.header(t('ml_training'))
    if not CORE_AI_AVAILABLE:
        st.error(t('ai_not_available'))
        st.code("pip install mediapipe opencv-python numpy")
        return
    st.success("✅ AI features available!")
    st.info("Upload a video to analyze skating performance")

def show_referee():
    try:
        from src.pages.referee_testing_interface import show_referee_testing_interface
        show_referee_testing_interface()
    except Exception as e:
        st.header(t('referee'))
        st.error(f"تعذّر تحميل واجهة الحكام: {e}")
        if not CORE_AI_AVAILABLE:
            st.code("pip install mediapipe opencv-python numpy tensorflow")

def show_my_videos():
    try:
        from src.pages.my_videos_page import show_my_videos as _show
        _show(lang=st.session_state.language)
    except Exception as e:
        st.error(f"خطأ في تحميل الصفحة: {e}")


def show_video_analysis():
    try:
        from src.pages.video_analysis_page import show_video_analysis_page
        from src.analysis.history_manager import save_analysis, invalidate_history_cache
        from src.utils.report_builder import get_download_button_data

        show_video_analysis_page(lang=st.session_state.language)

        # Save & Export buttons when results exist
        results = st.session_state.get('analysis_results')
        if results:
            st.markdown('---')
            col_save, col_export = st.columns(2)
            with col_save:
                if st.button('💾 ' + ('حفظ الجلسة في السجل' if st.session_state.language == 'ar' else 'Save Session to History'),
                             use_container_width=True, type='primary'):
                    sid = save_analysis(results)
                    invalidate_history_cache()
                    st.success('✅ ' + (f'تم الحفظ — جلسة #{sid}' if st.session_state.language == 'ar' else f'Saved — Session #{sid}'))
            with col_export:
                data, fname, mime = get_download_button_data(results, lang=st.session_state.language)
                st.download_button(
                    label='📄 ' + ('تصدير تقرير PDF' if st.session_state.language == 'ar' else 'Export PDF Report'),
                    data=data,
                    file_name=fname,
                    mime=mime,
                    use_container_width=True,
                )
    except ImportError as e:
        st.error(f"تعذّر تحميل صفحة التحليل: {e}")
        st.code("pip install mediapipe opencv-python numpy")


def show_player_progress():
    try:
        from src.pages.player_progress_page import show_player_progress_page
        show_player_progress_page(lang=st.session_state.language)
    except ImportError as e:
        st.error(f"تعذّر تحميل صفحة التقدم: {e}")


def show_realtime():
    try:
        from src.pages.realtime_analysis_page import show_realtime_analysis_page
        show_realtime_analysis_page(lang=st.session_state.language)
    except ImportError as e:
        st.error(f"تعذّر تحميل الكاميرا المباشرة: {e}")
        st.code("pip install mediapipe opencv-python numpy")


def show_club_management():
    try:
        from src.auth.auth_manager import seed_demo_data
        seed_demo_data()
        from src.pages.club_management_page import show_club_management_page
        show_club_management_page(lang=st.session_state.language)
    except ImportError as e:
        st.error(f"تعذّر تحميل إدارة الأندية: {e}")


def show_login():
    try:
        from src.auth.auth_manager import seed_demo_data
        seed_demo_data()
        from src.pages.login_page import show_login_page
        show_login_page(lang=st.session_state.language)
    except ImportError as e:
        st.error(f"تعذّر تحميل صفحة الدخول: {e}")


# ============================================================================
# STATS PAGE
# ============================================================================

def show_stats():
    st.header(t('stats'))

    members = load_members()
    attendance = load_attendance()

    if len(members) == 0:
        st.info(t('no_data'))
        return

    col1, col2 = st.columns(2)

    # Gender pie
    with col1:
        if 'gender' in members.columns and members['gender'].notna().any():
            gender_counts = members['gender'].value_counts().reset_index()
            gender_counts.columns = ['gender', 'count']
            fig = px.pie(
                gender_counts, values='count', names='gender',
                title=t('members_by_gender'),
                color_discrete_sequence=['#667eea', '#764ba2', '#f093fb'],
            )
            fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=300)
            st.plotly_chart(fig, use_container_width=True)

    # Skill level bar
    with col2:
        if 'skill_level' in members.columns and members['skill_level'].notna().any():
            level_counts = members['skill_level'].value_counts().reset_index()
            level_counts.columns = ['level', 'count']
            fig = px.bar(
                level_counts, x='level', y='count',
                title=t('members_by_level'),
                color='count',
                color_continuous_scale=['#667eea', '#764ba2'],
            )
            fig.update_layout(
                margin=dict(l=0, r=0, t=40, b=0),
                height=300,
                coloraxis_showscale=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig, use_container_width=True)

    # Attendance trend (last 30 days)
    if len(attendance) > 0 and 'attendance_date' in attendance.columns:
        st.subheader(t('attendance_trend'))
        cutoff = (date.today() - timedelta(days=30)).isoformat()
        recent = attendance[attendance['attendance_date'] >= cutoff].copy()
        if len(recent) > 0:
            trend = recent.groupby('attendance_date').size().reset_index(name='count')
            trend['attendance_date'] = pd.to_datetime(trend['attendance_date'])
            fig = px.area(
                trend, x='attendance_date', y='count',
                color_discrete_sequence=['#667eea'],
                labels={'attendance_date': '', 'count': ''},
            )
            fig.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                height=250,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig, use_container_width=True)

    # Top attending members
    if len(attendance) > 0 and 'skater_name' in attendance.columns:
        st.subheader(t('attendance_by_member'))
        top = attendance.groupby('skater_name').size().reset_index(name='sessions')
        top = top.sort_values('sessions', ascending=False).head(10)
        fig = px.bar(
            top, x='skater_name', y='sessions',
            color='sessions',
            color_continuous_scale=['#667eea', '#764ba2'],
            labels={'skater_name': '', 'sessions': ''},
        )
        fig.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=300,
            coloraxis_showscale=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig, use_container_width=True)

    # Payments overview
    try:
        conn = get_conn()
        pay_df = pd.read_sql_query(
            "SELECT bundle_type, SUM(amount) as total, COUNT(*) as count "
            "FROM payments GROUP BY bundle_type ORDER BY total DESC",
            conn
        )
        conn.close()
        if len(pay_df) > 0:
            st.subheader("💰 " + ("توزيع الباقات" if st.session_state.language == 'ar' else "Bundle Distribution"))
            col1, col2 = st.columns(2)
            with col1:
                fig = px.pie(pay_df, values='count', names='bundle_type',
                             color_discrete_sequence=px.colors.sequential.Purples_r)
                fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=280)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                total_rev = pay_df['total'].sum()
                st.metric("Total Revenue", f"{total_rev:,.0f} EGP")
                st.dataframe(pay_df, use_container_width=True)
    except Exception:
        pass

# ============================================================================
# SETTINGS PAGE
# ============================================================================

def show_settings():
    st.header(t('settings'))

    st.subheader(t('system_info'))
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Python:** {sys.version.split()[0]}")
        st.info(f"**Database:** skating_database.db")
        st.info(f"**MediaPipe:** {'✅' if MEDIAPIPE_AVAILABLE else '❌'}")
    with col2:
        st.info(f"**OpenCV:** {'✅' if CV2_AVAILABLE else '❌'}")
        st.info(f"**Advanced Analyzer:** {'✅' if ANALYZER_AVAILABLE else '❌'}")
        members = load_members()
        st.info(f"**{t('total_members')}:** {len(members)}")

    st.markdown("---")

    st.subheader("🗄️ " + t('db_path'))
    st.code(str(Path('skating_database.db').resolve()))

    st.markdown("---")

    if st.button(t('clear_cache'), use_container_width=False):
        invalidate_cache()
        st.success(f"✅ {t('cache_cleared')}")

    if not CORE_AI_AVAILABLE:
        st.markdown("---")
        st.subheader("📦 " + t('install_ai'))
        st.code("pip install mediapipe opencv-python numpy")

# ============================================================================
# SCHEDULE PAGE
# ============================================================================

_DAYS_AR = ['الاثنين','الثلاثاء','الأربعاء','الخميس','الجمعة','السبت','الأحد']
_DAYS_EN = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

def show_schedule():
    _init_schedule_table()
    is_ar = st.session_state.language == 'ar'
    DAYS  = _DAYS_AR if is_ar else _DAYS_EN
    st.header(t('schedule'))

    conn = get_conn()
    sched_df = pd.read_sql_query(
        "SELECT id, day_of_week, start_time, end_time, level, coach, "
        "session_type, max_capacity, notes FROM training_schedule ORDER BY day_of_week, start_time",
        conn
    )
    conn.close()

    # Weekly grid view
    st.subheader(t('weekly_schedule'))

    if len(sched_df) == 0:
        st.info("لا توجد حصص مجدولة بعد — أضف حصة أولاً" if is_ar else "No sessions scheduled yet — add one below")
    else:
        cols = st.columns(7)
        for day_i, (col, day_name) in enumerate(zip(cols, DAYS)):
            day_sessions = sched_df[sched_df['day_of_week'] == day_i]
            with col:
                st.markdown(f"**{day_name}**")
                for _, row in day_sessions.iterrows():
                    color = '#667eea' if row['session_type'] == 'on-ice' else '#764ba2'
                    st.markdown(
                        f"<div style='background:{color};color:white;border-radius:6px;"
                        f"padding:6px 8px;margin-bottom:4px;font-size:0.8em'>"
                        f"<b>{row['start_time']}–{row['end_time']}</b><br>"
                        f"{row['level'] or ''} | {row['coach'] or ''}"
                        f"</div>",
                        unsafe_allow_html=True
                    )

    st.markdown("---")

    # Table view with delete
    if len(sched_df) > 0:
        with st.expander("📋 " + ("عرض الجدول كاملاً" if is_ar else "View Full Table")):
            disp = sched_df.copy()
            disp['day_of_week'] = disp['day_of_week'].apply(lambda d: DAYS[d] if 0 <= d < 7 else d)
            st.dataframe(disp.drop(columns=['id']), use_container_width=True)

            # Export
            ext = _excel_ext()
            st.download_button(
                t('export_excel'),
                data=_df_to_excel(disp.drop(columns=['id']), 'Schedule'),
                file_name=f"schedule{ext}",
                mime=_excel_mime(),
            )

            # Delete session
            del_id = st.selectbox(
                "🗑️ " + ("حذف حصة" if is_ar else "Delete Session"),
                ["—"] + [f"#{r['id']} {DAYS[r['day_of_week']]} {r['start_time']}" for _, r in sched_df.iterrows()],
                key="del_sched"
            )
            if del_id != "—" and st.button("🗑️ " + ("تأكيد الحذف" if is_ar else "Confirm Delete"), type="secondary"):
                sid = int(del_id.split('#')[1].split(' ')[0])
                conn = get_conn()
                conn.execute("DELETE FROM training_schedule WHERE id=?", (sid,))
                conn.commit()
                conn.close()
                st.success("✅ " + ("تم الحذف" if is_ar else "Deleted"))
                st.rerun()

    # Add session form
    with st.expander(t('add_session'), expanded=len(sched_df) == 0):
        members = load_members()
        coaches = sorted(members['coach_name'].dropna().unique().tolist()) if 'coach_name' in members.columns else []
        levels_list = sorted(members['skill_level'].dropna().unique().tolist()) if 'skill_level' in members.columns else ['Beta','Gamma','Delta']

        with st.form("add_session"):
            c1, c2, c3 = st.columns(3)
            with c1:
                day = st.selectbox("اليوم" if is_ar else "Day", list(enumerate(DAYS)), format_func=lambda x: x[1])
            with c2:
                start_t = st.time_input("بداية" if is_ar else "Start", value=datetime.strptime("09:00", "%H:%M").time())
            with c3:
                end_t = st.time_input("نهاية" if is_ar else "End", value=datetime.strptime("10:00", "%H:%M").time())

            c1, c2, c3 = st.columns(3)
            with c1:
                sess_level = st.selectbox("المستوى" if is_ar else "Level", levels_list)
            with c2:
                sess_coach = st.selectbox("المدرب" if is_ar else "Coach", [""] + coaches)
            with c3:
                sess_type = st.selectbox("النوع" if is_ar else "Type", ['on-ice','off-ice','competition'])
            capacity = st.number_input("السعة القصوى" if is_ar else "Max Capacity", min_value=1, max_value=50, value=15)
            notes_s = st.text_input("ملاحظات" if is_ar else "Notes")
            sub_s = st.form_submit_button("💾 " + ("حفظ الحصة" if is_ar else "Save Session"), type="primary")
            if sub_s:
                try:
                    conn = get_conn()
                    conn.execute(
                        "INSERT INTO training_schedule "
                        "(day_of_week,start_time,end_time,level,coach,session_type,max_capacity,notes) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (day[0], start_t.strftime("%H:%M"), end_t.strftime("%H:%M"),
                         sess_level, sess_coach or None, sess_type, capacity, notes_s or None)
                    )
                    conn.commit()
                    conn.close()
                    st.success("✅ " + ("تمت إضافة الحصة" if is_ar else "Session added"))
                    st.rerun()
                except Exception as e:
                    st.error(str(e))


# ============================================================================
# PAYMENTS PAGE
# ============================================================================

def show_payments():
    is_ar = st.session_state.language == 'ar'
    st.header(t('payments'))

    try:
        conn = get_conn()
        pay_df = pd.read_sql_query(
            "SELECT skater_name, amount, payment_date, payment_method, "
            "bundle_type, discount, received_by, status FROM payments ORDER BY payment_date DESC",
            conn
        )
        bundles_df = pd.read_sql_query(
            "SELECT name, hours, price, rink, group_level, coach FROM bundles",
            conn
        )
        conn.close()
    except Exception as e:
        st.error(f"DB error: {e}")
        return

    # Summary metrics
    total_rev = pay_df['amount'].sum() if len(pay_df) > 0 else 0
    avg_pay   = pay_df['amount'].mean() if len(pay_df) > 0 else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("إجمالي المدفوعات" if is_ar else "Total Revenue",  f"{total_rev:,.0f} EGP")
    c2.metric("عدد المدفوعات" if is_ar else "# Payments",         len(pay_df))
    c3.metric("متوسط الدفعة" if is_ar else "Avg Payment",         f"{avg_pay:,.0f} EGP")
    c4.metric("عدد الباقات" if is_ar else "# Bundles",            len(bundles_df))

    st.markdown("---")
    col1, col2 = st.columns(2)

    # Bundle chart
    with col1:
        if len(pay_df) > 0 and pay_df['bundle_type'].notna().any():
            bc = pay_df['bundle_type'].value_counts().reset_index()
            bc.columns = ['bundle', 'count']
            fig = px.bar(bc, x='bundle', y='count',
                         color='count', color_continuous_scale=['#667eea', '#764ba2'],
                         title="توزيع الباقات" if is_ar else "Bundle Distribution",
                         labels={'bundle': '', 'count': ''})
            fig.update_layout(height=280, margin=dict(l=0,r=0,t=40,b=0),
                               coloraxis_showscale=False,
                               plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

    # Payment method pie
    with col2:
        if len(pay_df) > 0 and pay_df['payment_method'].notna().any():
            mc = pay_df['payment_method'].value_counts().reset_index()
            mc.columns = ['method', 'count']
            fig = px.pie(mc, values='count', names='method',
                         title="طريقة الدفع" if is_ar else "Payment Method",
                         color_discrete_sequence=['#667eea', '#764ba2', '#f093fb'])
            fig.update_layout(height=280, margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig, use_container_width=True)

    # Bundles pricing table
    st.subheader("📦 " + ("قائمة الأسعار" if is_ar else "Pricing List"))
    bundles_display = bundles_df.copy()
    bundles_display.columns = ['Bundle', 'Hours/Month', 'Price (EGP)', 'Rink', 'Level', 'Coach']
    st.dataframe(bundles_display, use_container_width=True)

    # Tabs: Records | Unpaid | Export
    tab_pay1, tab_pay2, tab_pay3 = st.tabs([
        "🧾 " + ("السجلات" if is_ar else "Records"),
        "⚠️ " + ("لم يدفع" if is_ar else "Unpaid"),
        "📥 " + ("تصدير" if is_ar else "Export"),
    ])

    with tab_pay1:
        search_pay = st.text_input("🔍 " + ("بحث باسم اللاعب" if is_ar else "Search by player"), key="pay_search")
        filtered_pay = pay_df.copy()
        if search_pay:
            filtered_pay = filtered_pay[filtered_pay['skater_name'].str.contains(search_pay, case=False, na=False)]
        st.dataframe(filtered_pay, use_container_width=True, height=400)
        st.caption(f"{len(filtered_pay)} " + ("سجل" if is_ar else "records"))

    with tab_pay2:
        st.subheader("⚠️ " + ("الأعضاء بدون دفع خلال 60 يوم" if is_ar else "Members with no payment in 60 days"))
        try:
            members_all = load_members()
            cutoff_60 = (date.today() - timedelta(days=60)).isoformat()
            paid_recently = set(
                pay_df[pay_df['payment_date'] >= cutoff_60]['skater_name'].dropna().tolist()
                if 'payment_date' in pay_df.columns and pay_df['payment_date'].notna().any() else []
            )
            any_paid = set(pay_df['skater_name'].dropna().tolist())
            unpaid_df = members_all[
                (~members_all['name'].isin(paid_recently)) &
                (members_all['membership_status'] == 'active')
            ][['name','skill_level','bundle','coach_name']].copy()
            unpaid_df['has_any_payment'] = unpaid_df['name'].isin(any_paid).map(
                {True: '✅ سابقاً', False: '❌ لا يوجد'} if is_ar else {True: '✅ Historic', False: '❌ Never'}
            )
            st.metric("عدد غير المدفوعين" if is_ar else "Unpaid Count", len(unpaid_df))
            st.dataframe(unpaid_df, use_container_width=True, height=400)
            if len(unpaid_df) > 0:
                st.download_button(
                    t('export_excel'),
                    data=_df_to_excel(unpaid_df, 'Unpaid'),
                    file_name=f"unpaid{_excel_ext()}",
                    mime=_excel_mime(),
                )
        except Exception as e:
            st.error(str(e))

    with tab_pay3:
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "📥 " + ("تصدير المدفوعات" if is_ar else "Export Payments"),
                data=_df_to_excel(pay_df, 'Payments'),
                file_name=f"payments{_excel_ext()}",
                mime=_excel_mime(),
                use_container_width=True,
            )
        with c2:
            bd = bundles_df.copy()
            bd.columns = ['Bundle','Hours','Price_EGP','Rink','Level','Coach']
            st.download_button(
                "📥 " + ("تصدير الباقات" if is_ar else "Export Bundles"),
                data=_df_to_excel(bd, 'Bundles'),
                file_name=f"bundles{_excel_ext()}",
                mime=_excel_mime(),
                use_container_width=True,
            )

    # Add payment form
    st.markdown("---")
    with st.expander("➕ " + ("تسجيل دفعة جديدة" if is_ar else "Record New Payment")):
        members = load_members()
        with st.form("new_payment"):
            skater_names = sorted(members['name'].tolist()) if 'name' in members.columns else []
            selected_payer = st.selectbox("اللاعب" if is_ar else "Player", skater_names)
            c1, c2 = st.columns(2)
            with c1:
                bundle_choices = sorted(bundles_df['name'].tolist()) if len(bundles_df) > 0 else []
                chosen_bundle = st.selectbox("الباقة" if is_ar else "Bundle", bundle_choices)
            with c2:
                pay_amount = st.number_input("المبلغ (EGP)" if is_ar else "Amount (EGP)", min_value=0.0, step=100.0)
            c1, c2, c3 = st.columns(3)
            with c1:
                pay_date = st.date_input("تاريخ الدفع" if is_ar else "Payment Date", value=date.today())
            with c2:
                pay_method = st.selectbox("طريقة الدفع" if is_ar else "Method", ['Cash', 'Instapay', 'Bank Transfer', 'Card'])
            with c3:
                received_by = st.text_input("استُلم بواسطة" if is_ar else "Received By")
            discount = st.number_input("خصم (EGP)" if is_ar else "Discount (EGP)", min_value=0.0, step=50.0)
            sub = st.form_submit_button("💾 " + ("حفظ" if is_ar else "Save"), type="primary")
            if sub and selected_payer:
                try:
                    conn = get_conn()
                    conn.execute(
                        "INSERT INTO payments (skater_name, amount, payment_date, payment_method, "
                        "bundle_type, discount, received_by, status) VALUES (?,?,?,?,?,?,?,'completed')",
                        (selected_payer, pay_amount, str(pay_date), pay_method,
                         chosen_bundle, discount, received_by)
                    )
                    conn.commit()
                    conn.close()
                    invalidate_cache()
                    st.success(f"✅ تم تسجيل الدفعة: {selected_payer} — {pay_amount:,.0f} EGP")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))


# ============================================================================
# MAIN ROUTER
# ============================================================================

_ROUTER = {
    t('home'):            show_home,
    t('members'):         show_members,
    t('attendance'):      show_attendance,
    t('payments'):        show_payments,
    t('schedule'):        show_schedule,
    t('video_analysis'):  show_video_analysis,
    t('my_videos'):       show_my_videos,
    t('realtime'):        show_realtime,
    t('player_progress'): show_player_progress,
    t('analysis_history'):show_player_progress,
    t('ml_training'):     show_ml_training,
    t('referee'):         show_referee,
    t('stats'):           show_stats,
    t('club_mgmt'):       show_club_management,
}
_ROUTER.get(page, show_settings)()

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("v6.0 - Global Edition | 6 Languages | Auth | Real-Time AI")
