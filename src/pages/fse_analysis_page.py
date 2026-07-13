"""
FSE Financial & Operational Analysis Page
لوحة تحليل الأداء المالي والتشغيلي لأكاديمية FSE
"""
import streamlit as st
import streamlit.components.v1 as components

FSE_ANALYSIS_HTML = """<!DOCTYPE html>
<html lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FSE — تحليل الأداء المالي والتشغيلي</title>
<style>
:root {
  --bg:#F2F6FA;--surface:#FFFFFF;--surface2:#E8EFF7;--border:#D0DCE9;
  --text:#0F2033;--text2:#4A607A;--text3:#8299B0;
  --accent:#1A9FC0;--accent2:#0D7A96;
  --gain:#1DB88A;--gain-bg:#E6FAF4;--loss:#D94F3A;--loss-bg:#FDF0EE;
  --warn:#E09530;--warn-bg:#FDF4E3;
  --navy:#0F1C2E;--ice:#C8E8F4;
  --shadow:0 2px 12px rgba(15,32,51,.08);--shadow-lg:0 6px 28px rgba(15,32,51,.14);
  --r:12px;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg:#08121E;--surface:#0F1E2E;--surface2:#162638;--border:#1E3249;
    --text:#E8F0FA;--text2:#7AAAC8;--text3:#3D6480;
    --accent:#3FB8D4;--accent2:#2A9AB8;
    --gain:#2DCE9A;--gain-bg:#0B2A20;--loss:#E86C58;--loss-bg:#2A100C;
    --warn:#F0B84A;--warn-bg:#2A1E08;
    --shadow:0 2px 12px rgba(0,0,0,.3);--shadow-lg:0 6px 28px rgba(0,0,0,.5);
  }
}
:root[data-theme="light"] {
  --bg:#F2F6FA;--surface:#FFFFFF;--surface2:#E8EFF7;--border:#D0DCE9;
  --text:#0F2033;--text2:#4A607A;--text3:#8299B0;
  --accent:#1A9FC0;--accent2:#0D7A96;
  --gain:#1DB88A;--gain-bg:#E6FAF4;--loss:#D94F3A;--loss-bg:#FDF0EE;
  --warn:#E09530;--warn-bg:#FDF4E3;
  --shadow:0 2px 12px rgba(15,32,51,.08);--shadow-lg:0 6px 28px rgba(15,32,51,.14);
}
:root[data-theme="dark"] {
  --bg:#08121E;--surface:#0F1E2E;--surface2:#162638;--border:#1E3249;
  --text:#E8F0FA;--text2:#7AAAC8;--text3:#3D6480;
  --accent:#3FB8D4;--accent2:#2A9AB8;
  --gain:#2DCE9A;--gain-bg:#0B2A20;--loss:#E86C58;--loss-bg:#2A100C;
  --warn:#F0B84A;--warn-bg:#2A1E08;
  --shadow:0 2px 12px rgba(0,0,0,.3);--shadow-lg:0 6px 28px rgba(0,0,0,.5);
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html{direction:rtl;font-size:16px;}
body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--text);min-height:100vh;line-height:1.6;}
@media (prefers-reduced-motion:reduce){*{transition:none !important;animation:none !important;}}
.header{background:var(--navy);color:#fff;padding:0;position:relative;overflow:hidden;}
.header::before{content:'';position:absolute;inset:0;background:linear-gradient(135deg,rgba(63,184,212,.15) 0%,transparent 50%),linear-gradient(225deg,rgba(29,184,138,.08) 30%,transparent 70%);pointer-events:none;}
.header::after{content:'';position:absolute;bottom:-1px;left:0;right:0;height:40px;background:var(--bg);clip-path:polygon(0 100%,100% 100%,100% 60%,85% 30%,70% 60%,55% 10%,40% 55%,25% 20%,10% 55%,0 30%);}
.header-inner{position:relative;z-index:1;max-width:1100px;margin:0 auto;padding:36px 28px 52px;display:flex;justify-content:space-between;align-items:flex-start;gap:20px;flex-wrap:wrap;}
.header-brand{display:flex;flex-direction:column;gap:6px;}
.brand-tag{font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);opacity:.9;}
.brand-title{font-size:clamp(1.5rem,4vw,2.4rem);font-weight:800;color:#fff;line-height:1.15;text-wrap:balance;}
.brand-sub{font-size:.95rem;color:rgba(255,255,255,.55);margin-top:2px;}
.header-meta{display:flex;flex-direction:column;align-items:flex-start;gap:8px;padding-top:4px;}
.period-chip{display:flex;align-items:center;gap:8px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.18);border-radius:50px;padding:6px 16px;font-size:.8rem;font-weight:600;color:rgba(255,255,255,.85);}
.period-dot{width:7px;height:7px;border-radius:50%;background:var(--accent);flex-shrink:0;}
.theme-btn{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2);border-radius:8px;padding:6px 12px;color:rgba(255,255,255,.75);font-size:.78rem;cursor:pointer;transition:background .2s;}
.theme-btn:hover{background:rgba(255,255,255,.2);}
.theme-btn:focus-visible{outline:2px solid var(--accent);}
.main{max-width:1100px;margin:0 auto;padding:32px 20px 60px;display:flex;flex-direction:column;gap:32px;}
.section-label{display:flex;align-items:center;gap:12px;margin-bottom:16px;}
.section-label h2{font-size:1.05rem;font-weight:700;color:var(--text);}
.section-label .rule{flex:1;height:1px;background:var(--border);}
.section-label .badge{font-size:.72rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--accent);background:color-mix(in srgb,var(--accent) 12%,transparent);border:1px solid color-mix(in srgb,var(--accent) 25%,transparent);padding:3px 10px;border-radius:20px;}
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;}
.kpi-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:20px 18px 16px;box-shadow:var(--shadow);transition:box-shadow .2s,transform .2s;display:flex;flex-direction:column;gap:4px;}
.kpi-card:hover{box-shadow:var(--shadow-lg);transform:translateY(-2px);}
.kpi-label{font-size:.75rem;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:var(--text3);}
.kpi-value{font-size:1.9rem;font-weight:800;font-variant-numeric:tabular-nums;color:var(--text);line-height:1.1;}
.kpi-value .currency{font-size:.85rem;font-weight:600;color:var(--text2);margin-right:3px;}
.kpi-delta{display:inline-flex;align-items:center;gap:4px;font-size:.75rem;font-weight:700;padding:2px 8px;border-radius:20px;margin-top:4px;width:fit-content;}
.kpi-delta.up{color:var(--gain);background:var(--gain-bg);}
.kpi-delta.down{color:var(--loss);background:var(--loss-bg);}
.kpi-delta.warn{color:var(--warn);background:var(--warn-bg);}
.kpi-delta.flat{color:var(--text3);background:var(--surface2);}
.kpi-sub{font-size:.72rem;color:var(--text3);margin-top:2px;}
.coach-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;}
.coach-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:20px;box-shadow:var(--shadow);display:flex;flex-direction:column;gap:14px;}
.coach-header{display:flex;justify-content:space-between;align-items:center;}
.coach-avatar{width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.95rem;color:#fff;flex-shrink:0;}
.coach-name-block{display:flex;flex-direction:column;}
.coach-name{font-weight:700;font-size:1rem;color:var(--text);}
.coach-count{font-size:.75rem;color:var(--text3);}
.coach-compare{display:grid;grid-template-columns:1fr 1fr;gap:8px;}
.cmp-cell{background:var(--surface2);border-radius:8px;padding:8px 10px;display:flex;flex-direction:column;gap:2px;}
.cmp-label{font-size:.68rem;font-weight:600;color:var(--text3);}
.cmp-val{font-size:.95rem;font-weight:700;font-variant-numeric:tabular-nums;color:var(--text);}
.cmp-delta{font-size:.7rem;font-weight:700;}
.cmp-delta.up{color:var(--gain);}
.cmp-delta.down{color:var(--loss);}
.cmp-delta.flat{color:var(--text3);}
.bar-track{height:6px;background:var(--surface2);border-radius:3px;overflow:hidden;}
.bar-fill{height:100%;border-radius:3px;transition:width .8s cubic-bezier(.22,1,.36,1);}
.table-wrap{overflow-x:auto;border-radius:var(--r);border:1px solid var(--border);}
table{width:100%;border-collapse:collapse;font-size:.875rem;}
thead th{background:var(--surface2);color:var(--text2);font-size:.72rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:10px 16px;text-align:right;border-bottom:1px solid var(--border);white-space:nowrap;}
tbody tr{border-bottom:1px solid var(--border);transition:background .15s;}
tbody tr:last-child{border-bottom:none;}
tbody tr:hover{background:var(--surface2);}
tbody td{padding:11px 16px;color:var(--text);font-variant-numeric:tabular-nums;}
tbody td.label-cell{font-weight:600;}
.pill{display:inline-flex;align-items:center;gap:4px;font-size:.72rem;font-weight:700;padding:3px 9px;border-radius:20px;}
.pill.up{color:var(--gain);background:var(--gain-bg);}
.pill.flat{color:var(--text3);background:var(--surface2);}
.pill.down{color:var(--loss);background:var(--loss-bg);}
.chart-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:24px 24px 20px;box-shadow:var(--shadow);}
.chart-title{font-size:.95rem;font-weight:700;margin-bottom:18px;color:var(--text);}
canvas{display:block;width:100%;}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
@media (max-width:680px){.two-col{grid-template-columns:1fr;}}
.insight-list{display:flex;flex-direction:column;gap:10px;}
.insight{display:flex;gap:14px;align-items:flex-start;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 16px;}
.insight-icon{width:36px;height:36px;flex-shrink:0;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1.1rem;}
.insight-icon.green{background:var(--gain-bg);}
.insight-icon.amber{background:var(--warn-bg);}
.insight-icon.red{background:var(--loss-bg);}
.insight-icon.blue{background:color-mix(in srgb,var(--accent) 12%,transparent);}
.insight-body{flex:1;}
.insight-title{font-weight:700;font-size:.9rem;margin-bottom:3px;}
.insight-desc{font-size:.8rem;color:var(--text2);line-height:1.5;}
.footer{text-align:center;font-size:.75rem;color:var(--text3);padding:20px;border-top:1px solid var(--border);}
</style>
</head>
<body>

<header class="header">
  <div class="header-inner">
    <div class="header-brand">
      <span class="brand-tag">⛸ FSE — Figure Skating Egypt</span>
      <h1 class="brand-title">تحليل الأداء المالي<br>والتشغيلي</h1>
      <p class="brand-sub">ثلاثة أشهر · خمسة مدربين · مقارنة شاملة</p>
    </div>
    <div class="header-meta">
      <div class="period-chip"><span class="period-dot"></span>مايو 2025 — يونيو 2026</div>
      <div class="period-chip"><span class="period-dot" style="background:var(--gain)"></span>5 مدربين · 95 لاعب فعلي</div>
      <button class="theme-btn" onclick="toggleTheme()">🌙 / ☀️ التبديل</button>
    </div>
  </div>
</header>

<main class="main">

  <section>
    <div class="section-label">
      <h2>المؤشرات الرئيسية</h2><div class="rule"></div><span class="badge">KPIs</span>
    </div>
    <div class="kpi-grid">
      <div class="kpi-card">
        <span class="kpi-label">إجمالي الإيرادات — أبريل 2026</span>
        <div class="kpi-value"><span class="currency">ج.م</span>60,300</div>
        <span class="kpi-delta up">↑ +19% عن مايو 2025</span>
        <span class="kpi-sub">5 مدربين · 68 طالب</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">إجمالي الإيرادات — يونيو 2026</span>
        <div class="kpi-value"><span class="currency">ج.م</span>65,350</div>
        <span class="kpi-delta up">↑ +8.4% عن أبريل</span>
        <span class="kpi-sub">5 مدربين · 95 طالب</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">نمو قاعدة الطلاب</span>
        <div class="kpi-value">+48%</div>
        <span class="kpi-delta up">64 → 95 طالب</span>
        <span class="kpi-sub">من مايو 2025 إلى يونيو 2026</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">زيادة أسعار الباقات</span>
        <div class="kpi-value">+20%</div>
        <span class="kpi-delta warn">↑ على الجليد فقط</span>
        <span class="kpi-sub">الباقات خارج الجليد: بدون تغيير</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">متوسط الحضور — أبريل 2026</span>
        <div class="kpi-value">3.4<span style="font-size:.9rem;font-weight:500;color:var(--text2)"> جلسة</span></div>
        <span class="kpi-delta flat">→ 3.1 في يونيو</span>
        <span class="kpi-sub">من إجمالي 4 أو 8 جلسات</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">طالب بدون حضور — أبريل</span>
        <div class="kpi-value">1</div>
        <span class="kpi-delta down">Hala Ahmed — Esraa</span>
        <span class="kpi-sub">دفعت 1,600 ج.م · 0 جلسة · 8 غياب</span>
      </div>
    </div>
  </section>

  <section>
    <div class="section-label">
      <h2>مسار الإيرادات الزمني</h2><div class="rule"></div><span class="badge">Timeline</span>
    </div>
    <div class="chart-card">
      <div class="chart-title">الإيرادات الشهرية (ج.م) — مايو 2025 إلى يونيو 2026</div>
      <canvas id="revenueChart" height="200"></canvas>
    </div>
  </section>

  <section>
    <div class="section-label">
      <h2>أداء المدربين — مقارنة أبريل vs يونيو 2026</h2><div class="rule"></div><span class="badge">Coaches</span>
    </div>
    <div class="coach-grid">
      <div class="coach-card">
        <div class="coach-header">
          <div style="display:flex;align-items:center;gap:10px">
            <div class="coach-avatar" style="background:linear-gradient(135deg,#1A9FC0,#0D7A96)">إ</div>
            <div class="coach-name-block"><span class="coach-name">Esraa</span><span class="coach-count">أبريل: 24 طالب · يونيو: 36 طالب</span></div>
          </div>
        </div>
        <div class="coach-compare">
          <div class="cmp-cell"><span class="cmp-label">أبريل 2026</span><span class="cmp-val">24,450</span><span class="cmp-delta flat">ج.م</span></div>
          <div class="cmp-cell"><span class="cmp-label">يونيو 2026</span><span class="cmp-val">21,250</span><span class="cmp-delta down">−13.1%</span></div>
        </div>
        <div class="bar-track"><div class="bar-fill" style="width:100%;background:linear-gradient(90deg,#1A9FC0,#3FB8D4)"></div></div>
        <div style="font-size:.78rem;color:var(--text3)">الأعلى إيراداً في أبريل · تراجع مع زيادة الطلاب (جلسات فردية)</div>
      </div>
      <div class="coach-card">
        <div class="coach-header">
          <div style="display:flex;align-items:center;gap:10px">
            <div class="coach-avatar" style="background:linear-gradient(135deg,#9B59B6,#7D3C98)">إ</div>
            <div class="coach-name-block"><span class="coach-name">Eman</span><span class="coach-count">أبريل: 19 طالب · يونيو: 27 طالب</span></div>
          </div>
        </div>
        <div class="coach-compare">
          <div class="cmp-cell"><span class="cmp-label">أبريل 2026</span><span class="cmp-val">16,150</span><span class="cmp-delta flat">ج.م</span></div>
          <div class="cmp-cell"><span class="cmp-label">يونيو 2026</span><span class="cmp-val">20,300</span><span class="cmp-delta up">+25.7%</span></div>
        </div>
        <div class="bar-track"><div class="bar-fill" style="width:85%;background:linear-gradient(90deg,#9B59B6,#BB8FCC)"></div></div>
        <div style="font-size:.78rem;color:var(--text3)">نمو قوي — أكبر ارتفاع مطلق: +4,150 ج.م</div>
      </div>
      <div class="coach-card">
        <div class="coach-header">
          <div style="display:flex;align-items:center;gap:10px">
            <div class="coach-avatar" style="background:linear-gradient(135deg,#1DB88A,#148C68)">م</div>
            <div class="coach-name-block"><span class="coach-name">Maryam</span><span class="coach-count">أبريل: 5 طلاب · يونيو: 20 طالب</span></div>
          </div>
        </div>
        <div class="coach-compare">
          <div class="cmp-cell"><span class="cmp-label">أبريل 2026</span><span class="cmp-val">6,100</span><span class="cmp-delta flat">ج.م</span></div>
          <div class="cmp-cell"><span class="cmp-label">يونيو 2026</span><span class="cmp-val">14,200</span><span class="cmp-delta up">+133%</span></div>
        </div>
        <div class="bar-track"><div class="bar-fill" style="width:60%;background:linear-gradient(90deg,#1DB88A,#58D68D)"></div></div>
        <div style="font-size:.78rem;color:var(--text3)">⭐ أكبر نمو نسبي — تضاعف الطلاب 4× في شهرين</div>
      </div>
      <div class="coach-card">
        <div class="coach-header">
          <div style="display:flex;align-items:center;gap:10px">
            <div class="coach-avatar" style="background:linear-gradient(135deg,#E09530,#B7770D)">ه</div>
            <div class="coach-name-block"><span class="coach-name">Hajar</span><span class="coach-count">أبريل: 12 طالب · يونيو: 12 طالب</span></div>
          </div>
        </div>
        <div class="coach-compare">
          <div class="cmp-cell"><span class="cmp-label">أبريل 2026</span><span class="cmp-val">8,050</span><span class="cmp-delta flat">ج.م</span></div>
          <div class="cmp-cell"><span class="cmp-label">يونيو 2026</span><span class="cmp-val">8,150</span><span class="cmp-delta up">+1.2%</span></div>
        </div>
        <div class="bar-track"><div class="bar-fill" style="width:34%;background:linear-gradient(90deg,#E09530,#F0C060)"></div></div>
        <div style="font-size:.78rem;color:var(--text3)">ثابت — نفس الطلاب وإيرادات مستقرة</div>
      </div>
      <div class="coach-card">
        <div class="coach-header">
          <div style="display:flex;align-items:center;gap:10px">
            <div class="coach-avatar" style="background:linear-gradient(135deg,#D94F3A,#A93226)">ك</div>
            <div class="coach-name-block"><span class="coach-name">Clara</span><span class="coach-count">أبريل: 8 طلاب · يونيو: 9 طلاب</span></div>
          </div>
        </div>
        <div class="coach-compare">
          <div class="cmp-cell"><span class="cmp-label">أبريل 2026</span><span class="cmp-val">5,550</span><span class="cmp-delta flat">ج.م</span></div>
          <div class="cmp-cell"><span class="cmp-label">يونيو 2026</span><span class="cmp-val">1,450</span><span class="cmp-delta down">−73.9%</span></div>
        </div>
        <div class="bar-track"><div class="bar-fill" style="width:23%;background:linear-gradient(90deg,#D94F3A,#E87B6B)"></div></div>
        <div style="font-size:.78rem;color:var(--warn)">⚠️ انخفاض حاد — مبالغ سالبة (خصومات) بقيمة −1,800 ج.م في يونيو</div>
      </div>
    </div>
  </section>

  <div class="two-col">
    <div class="chart-card">
      <div class="chart-title">توزيع الإيرادات — أبريل 2026</div>
      <canvas id="donutApr" height="220"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">توزيع الإيرادات — يونيو 2026</div>
      <canvas id="donutJun" height="220"></canvas>
    </div>
  </div>

  <section>
    <div class="section-label">
      <h2>مقارنة أسعار الباقات</h2><div class="rule"></div><span class="badge">Bundle Pricing</span>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>الباقة</th><th>الساعات</th><th>أبريل 2026</th><th>يونيو 2026</th><th>التغيير</th></tr>
        </thead>
        <tbody>
          <tr><td class="label-cell">On-Ice Bronze</td><td>4 ساعات</td><td>1,500 ج.م</td><td>1,800 ج.م</td><td><span class="pill up">↑ +20%</span></td></tr>
          <tr><td class="label-cell">On-Ice Silver</td><td>8 ساعات</td><td>2,800 ج.م</td><td>3,400 ج.م</td><td><span class="pill up">↑ +21%</span></td></tr>
          <tr><td class="label-cell">On-Ice Gold</td><td>12 ساعة</td><td>4,000 ج.م</td><td>4,800 ج.م</td><td><span class="pill up">↑ +20%</span></td></tr>
          <tr><td class="label-cell">Off-Ice Bronze</td><td>4 ساعات</td><td>800 ج.م</td><td>800 ج.م</td><td><span class="pill flat">= ثابت</span></td></tr>
          <tr><td class="label-cell">Off-Ice Silver</td><td>8 ساعات</td><td>1,400 ج.م</td><td>1,400 ج.م</td><td><span class="pill flat">= ثابت</span></td></tr>
          <tr><td class="label-cell">Off-Ice Gold</td><td>12 ساعة</td><td>2,000 ج.م</td><td>2,000 ج.م</td><td><span class="pill flat">= ثابت</span></td></tr>
          <tr><td class="label-cell">خاص Private</td><td>1 ساعة</td><td>600 ج.م</td><td>700 ج.م</td><td><span class="pill up">↑ +17%</span></td></tr>
          <tr><td class="label-cell">Per Session</td><td>جلسة واحدة</td><td>400 ج.م</td><td>500 ج.م</td><td><span class="pill up">↑ +25%</span></td></tr>
          <tr><td class="label-cell" style="color:var(--text3)">Off-On Ice Bronze</td><td>4+4</td><td>2,300 ج.م</td><td>3,600 ج.م</td><td><span class="pill up">↑ +57%</span></td></tr>
          <tr><td class="label-cell" style="color:var(--text3)">Off-On Ice Silver</td><td>8+4</td><td>3,600 ج.م</td><td>4,200 ج.م</td><td><span class="pill up">↑ +17%</span></td></tr>
        </tbody>
      </table>
    </div>
  </section>

  <section>
    <div class="section-label">
      <h2>تفاصيل مايو 2025 — إيرادات المدربين</h2><div class="rule"></div><span class="badge">May 2025</span>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>المدرب</th><th>عدد الطلاب</th><th>إجمالي الجلسات</th><th>الإيرادات (ج.م)</th><th>ملاحظة</th></tr>
        </thead>
        <tbody>
          <tr><td class="label-cell">Esraa</td><td>9</td><td>50</td><td>15,200</td><td>—</td></tr>
          <tr><td class="label-cell">Clara</td><td>6</td><td>21</td><td>7,500</td><td>—</td></tr>
          <tr><td class="label-cell">Maryam</td><td>17</td><td>89</td><td>19,100</td><td>أكبر مجموعة ومجموع جلسات</td></tr>
          <tr><td class="label-cell">Hajar</td><td>10</td><td>33</td><td>8,850</td><td>—</td></tr>
          <tr><td class="label-cell" style="color:var(--text2)">Eman</td><td>22</td><td style="color:var(--warn)">−36*</td><td style="color:var(--text3)">—</td><td style="color:var(--warn);font-size:.78rem">طلاب بجلسات مفردة — الأرصدة تشير لجلسات زائدة عن الباقات</td></tr>
          <tr style="background:var(--surface2)">
            <td class="label-cell">الإجمالي</td>
            <td style="font-weight:700">64</td>
            <td style="font-weight:700">193</td>
            <td style="font-weight:700;color:var(--accent)">50,650+</td>
            <td style="font-size:.78rem;color:var(--text3)">* قسم Eman بتنسيق مختلف</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <section>
    <div class="section-label">
      <h2>أبرز الاستنتاجات والتوصيات</h2><div class="rule"></div><span class="badge">Insights</span>
    </div>
    <div class="insight-list">
      <div class="insight">
        <div class="insight-icon green">📈</div>
        <div class="insight-body">
          <div class="insight-title">نمو استثنائي في قاعدة الطلاب</div>
          <div class="insight-desc">ارتفع عدد الطلاب من 64 (مايو 2025) إلى 95 (يونيو 2026) بنسبة <strong>+48%</strong>. هذا النمو جاء مع رفع أسعار الجلسات على الجليد بنسبة 20%، مما يدل على قوة الطلب وصحة الأكاديمية.</div>
        </div>
      </div>
      <div class="insight">
        <div class="insight-icon green">⭐</div>
        <div class="insight-body">
          <div class="insight-title">Maryam — النجمة الصاعدة</div>
          <div class="insight-desc">قفز إجمالي إيرادات Maryam من <strong>6,100 ج.م</strong> في أبريل إلى <strong>14,200 ج.م</strong> في يونيو (+133%). تضاعف عدد طلابها من 5 إلى 20 — تستحق دعماً إضافياً وربما توسيع مجموعاتها.</div>
        </div>
      </div>
      <div class="insight">
        <div class="insight-icon blue">💡</div>
        <div class="insight-body">
          <div class="insight-title">Eman — نمو صحي ومستدام</div>
          <div class="insight-desc">نمت إيرادات Eman بنسبة <strong>+25.7%</strong> مع زيادة الطلاب من 19 إلى 27. أعلى زيادة مطلقة في القيمة (+4,150 ج.م). تعتمد على مزيج متوازن بين الباقات والجلسات الفردية.</div>
        </div>
      </div>
      <div class="insight">
        <div class="insight-icon amber">⚠️</div>
        <div class="insight-body">
          <div class="insight-title">Clara — تراجع حاد يستدعي المراجعة</div>
          <div class="insight-desc">انخفضت إيرادات Clara من 5,550 ج.م إلى 1,450 ج.م (−73.9%) رغم ثبات عدد الطلاب. يونيو 2026 يحتوي على خصومات سالبة بقيمة −1,800 ج.م. يُنصح بمراجعة سياسة الخصومات مع هذا المدرب.</div>
        </div>
      </div>
      <div class="insight">
        <div class="insight-icon amber">🔔</div>
        <div class="insight-body">
          <div class="insight-title">Hala Ahmed — أداء صفري مع دفع كامل</div>
          <div class="insight-desc">الطالبة <strong>Hala Ahmed</strong> (Esraa) سجلت 0 حضور و8 غياب في أبريل 2026 مع رسوم مدفوعة 1,600 ج.م. يجب التواصل معها لمعرفة سبب الانقطاع وإما ترحيل الجلسات أو الإلغاء.</div>
        </div>
      </div>
      <div class="insight">
        <div class="insight-icon blue">💰</div>
        <div class="insight-body">
          <div class="insight-title">رفع الأسعار مدروس وانتقائي</div>
          <div class="insight-desc">تم رفع أسعار الجلسات على الجليد (On-Ice) وجلسات Per Session بنسب 17–25%، بينما بقيت أسعار Off-Ice ثابتة. هذا التمييز الذكي يحافظ على إمكانية وصول الطلاب مع تعظيم الإيرادات من الخدمات الأعلى تكلفة.</div>
        </div>
      </div>
      <div class="insight">
        <div class="insight-icon red">📋</div>
        <div class="insight-body">
          <div class="insight-title">توحيد نماذج التتبع ضرورة عاجلة</div>
          <div class="insight-desc">ملف مايو 2025 يختلف جذرياً في التنسيق عن ملفي 2026 — مما يجعل المقارنة التاريخية صعبة. يُنصح باعتماد نموذج موحد للتقارير الشهرية، ويفضل تحميل البيانات مباشرة في نظام YASOOO.</div>
        </div>
      </div>
    </div>
  </section>

</main>

<footer class="footer">
  FSE Figure Skating Egypt · تحليل مُنشأ بواسطة YASOOO · البيانات: 5 ملفات Excel · 3 أشهر · 5 مدربين
</footer>

<script>
function toggleTheme() {
  const root = document.documentElement;
  const cur = root.getAttribute('data-theme');
  if (cur === 'dark') root.setAttribute('data-theme','light');
  else if (cur === 'light') root.setAttribute('data-theme','dark');
  else {
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    root.setAttribute('data-theme', isDark ? 'light' : 'dark');
  }
  drawCharts();
}
function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}
function drawRevenueChart() {
  const canvas = document.getElementById('revenueChart');
  if (!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const W = canvas.parentElement.clientWidth - 48;
  const H = 200;
  canvas.width = W * dpr; canvas.height = H * dpr;
  canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  const data = [
    { label: 'مايو 2025',  value: 50650 },
    { label: 'أبريل 2026', value: 60300 },
    { label: 'يونيو 2026', value: 65350 },
  ];
  const pad = { t:20, r:20, b:40, l:70 };
  const cw = W - pad.l - pad.r;
  const ch = H - pad.t - pad.b;
  const maxVal = 75000;
  const accent = cssVar('--accent');
  const text2  = cssVar('--text2');
  const text3  = cssVar('--text3');
  const border = cssVar('--border');
  ctx.strokeStyle = border; ctx.lineWidth = 1;
  [0,25000,50000,75000].forEach(v => {
    const y = pad.t + ch - (v / maxVal) * ch;
    ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(pad.l + cw, y); ctx.stroke();
    ctx.fillStyle = text3; ctx.font = '11px system-ui'; ctx.textAlign = 'right';
    ctx.fillText((v/1000) + 'k', pad.l - 8, y + 4);
  });
  const pts = data.map((d, i) => ({
    x: pad.l + (i / (data.length - 1)) * cw,
    y: pad.t + ch - (d.value / maxVal) * ch
  }));
  const grad = ctx.createLinearGradient(0, pad.t, 0, pad.t + ch);
  grad.addColorStop(0, 'rgba(26,159,192,0.25)');
  grad.addColorStop(1, 'rgba(26,159,192,0.02)');
  ctx.beginPath();
  ctx.moveTo(pts[0].x, pad.t + ch);
  pts.forEach(p => ctx.lineTo(p.x, p.y));
  ctx.lineTo(pts[pts.length-1].x, pad.t + ch);
  ctx.closePath(); ctx.fillStyle = grad; ctx.fill();
  ctx.beginPath(); ctx.strokeStyle = accent; ctx.lineWidth = 2.5; ctx.lineJoin = 'round';
  pts.forEach((p, i) => i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y));
  ctx.stroke();
  pts.forEach((p, i) => {
    ctx.beginPath(); ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
    ctx.fillStyle = accent; ctx.fill();
    ctx.strokeStyle = cssVar('--surface'); ctx.lineWidth = 2; ctx.stroke();
    ctx.fillStyle = cssVar('--text'); ctx.font = 'bold 12px system-ui'; ctx.textAlign = 'center';
    ctx.fillText(data[i].value.toLocaleString() + ' ج.م', p.x, p.y - 12);
    ctx.fillStyle = text2; ctx.font = '11px system-ui';
    ctx.fillText(data[i].label, p.x, H - 8);
  });
}
function drawDonut(canvasId, values, labels, colors) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const W = canvas.parentElement.clientWidth - 48;
  const H = 220;
  canvas.width = W * dpr; canvas.height = H * dpr;
  canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  const total = values.reduce((a, b) => a + b, 0);
  const cx = W * 0.4; const cy = H / 2;
  const R = Math.min(cx, cy) * 0.75; const r = R * 0.55;
  let angle = -Math.PI / 2;
  values.forEach((v, i) => {
    const slice = (v / total) * 2 * Math.PI;
    ctx.beginPath(); ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, R, angle, angle + slice);
    ctx.closePath(); ctx.fillStyle = colors[i]; ctx.fill();
    angle += slice;
  });
  ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fillStyle = cssVar('--surface'); ctx.fill();
  ctx.textAlign = 'center';
  ctx.fillStyle = cssVar('--text'); ctx.font = 'bold 14px system-ui';
  ctx.fillText(total.toLocaleString(), cx, cy - 4);
  ctx.fillStyle = cssVar('--text3'); ctx.font = '11px system-ui';
  ctx.fillText('ج.م', cx, cy + 14);
  const lx = W * 0.78; const lineH = 26;
  const startY = cy - ((values.length * lineH) / 2);
  values.forEach((v, i) => {
    const y = startY + i * lineH;
    ctx.fillStyle = colors[i];
    ctx.beginPath(); ctx.roundRect(lx - 12, y - 6, 10, 10, 3); ctx.fill();
    ctx.fillStyle = cssVar('--text'); ctx.font = '600 11px system-ui'; ctx.textAlign = 'right';
    ctx.fillText(labels[i], lx + 50, y + 3);
    ctx.fillStyle = cssVar('--text2'); ctx.font = '11px system-ui'; ctx.textAlign = 'right';
    ctx.fillText(Math.round(v / total * 100) + '%', lx + 90, y + 3);
  });
}
function drawCharts() {
  drawRevenueChart();
  drawDonut('donutApr',[24450,16150,8050,5550,6100],['Esraa','Eman','Hajar','Clara','Maryam'],['#1A9FC0','#9B59B6','#E09530','#D94F3A','#1DB88A']);
  drawDonut('donutJun',[21250,20300,14200,8150,1450],['Esraa','Eman','Maryam','Hajar','Clara'],['#1A9FC0','#9B59B6','#1DB88A','#E09530','#D94F3A']);
}
window.addEventListener('load', drawCharts);
window.addEventListener('resize', () => { clearTimeout(window._rt); window._rt = setTimeout(drawCharts, 120); });
</script>
</body>
</html>"""


def show_fse_analysis():
    ar = st.session_state.get('language', 'ar') == 'ar'

    st.markdown(
        f"<h2 style='margin-bottom:4px'>{'📊 تحليل الأداء المالي — FSE' if ar else '📊 FSE Financial Performance Analysis'}</h2>"
        f"<p style='color:#64748b;margin-bottom:16px'>{'بيانات 5 ملفات Excel · 3 أشهر · 5 مدربين' if ar else '5 Excel files · 3 months · 5 coaches'}</p>",
        unsafe_allow_html=True
    )

    components.html(FSE_ANALYSIS_HTML, height=2800, scrolling=True)
