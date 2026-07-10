"""
محلل ملفات إكسل (حضور / عضويات / قوائم أعضاء) بدون أي اتصال بقاعدة البيانات.
يحول أي ملف إكسل شهري (بنفس شكل الملفات المستخدمة حالياً) إلى بنية بيانات موحدة:
- roster_rows: صفوف من قائمة الأعضاء (اسم، مستوى، كوتش، باقة)
- payment_rows: صفوف دفعات/عضويات (اسم، باقة، مبلغ، خصم، تاريخ الدفع)
- attendance_rows: صفوف حضور (اسم، تاريخ، نوع الحصة on-ice/off-ice، كوتش)
- sheet_notes: ملاحظة عن كل ورقة (تم التعرف عليها/تجاهلها/غير معروفة) حتى لا يتم إسقاط أي بيانات بصمت
"""
import re
from datetime import datetime, date
from io import BytesIO

import pandas as pd

SKIP_NAME_TOKENS = {'coach', 'nan', '!!', '-', '--', 'كوتش'}
MIN_ATTENDANCE_DATE_COLS = 5
STRIDE3_MIN_MATCH_RATIO = 0.9


def normalize_name(raw) -> str:
    """يحذف المسافات الزائدة مع الحفاظ على شكل الاسم الأصلي للعرض."""
    return re.sub(r'\s+', ' ', str(raw).strip())


def name_key(raw) -> str:
    """مفتاح مطابقة الاسم (بدون حساسية لحالة الأحرف أو المسافات)."""
    return normalize_name(raw).casefold()


def _cellstr(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ''
    if isinstance(v, (pd.Timestamp, datetime, date)):
        return ''
    return str(v).strip().casefold()


def _is_dateish(v) -> bool:
    if isinstance(v, (pd.Timestamp, datetime, date)) and pd.notna(v):
        return True
    return False


def _is_blank(v) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and pd.isna(v):
        return True
    if isinstance(v, (pd.Timestamp,)) and pd.isna(v):
        return True
    s = str(v).strip()
    return s == '' or s.casefold() == 'nan' or s.casefold() == 'nat'


def _is_plausible_name(v) -> bool:
    if _is_blank(v) or _is_dateish(v):
        return False
    s = str(v).strip()
    if s.casefold() in SKIP_NAME_TOKENS:
        return False
    if len(s) < 2:
        return False
    return True


def _find_col(cells, predicate):
    for idx, c in enumerate(cells):
        if predicate(c):
            return idx
    return None


def _try_payments_header(cells):
    has_member = any(c == 'member' for c in cells)
    has_bundle = any(c.startswith('bundle') for c in cells)
    has_amount = any('amount' in c for c in cells)
    has_dop = any(c == 'dop' or 'date of payment' in c for c in cells)
    return has_member and has_bundle and has_amount and has_dop


def _try_monthly_report_header(cells):
    has_coach = any(c == 'coach' for c in cells)
    has_name = any(c == 'name' for c in cells)
    has_attendance = any(c == 'attendance' for c in cells)
    has_absence = any(c == 'absence' for c in cells)
    return has_coach and has_name and has_attendance and has_absence


def _try_roster_header(cells):
    has_name = any(c == 'name' for c in cells)
    has_membership = any('membership' in c for c in cells)
    has_coach = any(c == 'coach' for c in cells)
    has_level = any(c == 'level' for c in cells)
    return has_name and (has_membership or (has_coach and has_level))


def _classify_sheet(sheet_name, df):
    """يحدد نوع الورقة وموقع رأس الجدول وبداية البيانات."""
    nrows, ncols = df.shape

    max_scan = min(6, nrows)
    for r in range(max_scan):
        cells = [_cellstr(v) for v in df.iloc[r].tolist()]
        if _try_payments_header(cells):
            return {'type': 'payments', 'header_rows': [r], 'data_start': r + 1}

    for r in range(max_scan):
        cells = [_cellstr(v) for v in df.iloc[r].tolist()]
        if _try_monthly_report_header(cells):
            return {'type': 'monthly_report', 'header_rows': [r], 'data_start': r + 1}

    max_scan_roster = min(4, max(nrows - 1, 0))
    for r in range(max_scan_roster):
        row_a = df.iloc[r].tolist()
        row_b = df.iloc[r + 1].tolist() if r + 1 < nrows else [None] * ncols
        merged = [a if not _is_blank(a) else b for a, b in zip(row_a, row_b)]
        cells = [_cellstr(v) for v in merged]
        if _try_roster_header(cells):
            return {'type': 'roster', 'header_rows': [r, r + 1], 'data_start': r + 2, 'merged_header': merged}

    if nrows >= 1:
        row0 = df.iloc[0].tolist()
        date_cols = [i for i, v in enumerate(row0) if _is_dateish(v)]
        if len(date_cols) >= MIN_ATTENDANCE_DATE_COLS:
            diffs = [b - a for a, b in zip(date_cols, date_cols[1:])]
            stride3_matches = sum(1 for d in diffs if d == 3)
            stride1_matches = sum(1 for d in diffs if d == 1)
            if diffs and stride3_matches / len(diffs) >= STRIDE3_MIN_MATCH_RATIO:
                label_row = None
                if nrows > 1:
                    row1 = [_cellstr(v) for v in df.iloc[1].tolist()]
                    hits = 0
                    checked = 0
                    for c in date_cols:
                        off_lbl, on_lbl, coach_lbl = (
                            row1[c] if c < ncols else '',
                            row1[c + 1] if c + 1 < ncols else '',
                            row1[c + 2] if c + 2 < ncols else '',
                        )
                        checked += 1
                        if off_lbl == 'off-ice' and on_lbl == 'on-ice' and coach_lbl == 'coach':
                            hits += 1
                    if checked and hits / checked >= 0.5:
                        label_row = 1
                data_start = 2 if label_row is not None else 1
                return {
                    'type': 'attendance_grid_3col',
                    'date_row': 0,
                    'date_cols': date_cols,
                    'data_start': data_start,
                }
            if diffs and stride1_matches / len(diffs) >= STRIDE3_MIN_MATCH_RATIO:
                has_data_below = False
                for c in date_cols:
                    col_vals = df.iloc[1:, c] if nrows > 1 else []
                    if any(_is_plausible_name(v) for v in col_vals):
                        has_data_below = True
                        break
                if not has_data_below:
                    return {'type': 'empty', 'reason': 'يحتوي على تواريخ فقط بدون أي بيانات حضور أسفلها'}
                return {
                    'type': 'attendance_grid_1col',
                    'date_row': 0,
                    'date_cols': date_cols,
                    'data_start': 1,
                }

    non_empty_cells = 0
    for r in range(nrows):
        for v in df.iloc[r].tolist():
            if not _is_blank(v):
                non_empty_cells += 1
        if non_empty_cells > 3:
            break
    if non_empty_cells <= 3:
        return {'type': 'empty', 'reason': 'ورقة فارغة تقريباً، لا توجد بيانات لاستيرادها'}

    return {'type': 'unknown', 'reason': 'لم يتم التعرف على شكل هذه الورقة تلقائياً'}


def _parse_roster_sheet(df, meta):
    cells = [_cellstr(v) for v in meta['merged_header']]
    col_name = _find_col(cells, lambda c: c == 'name')
    col_coach = _find_col(cells, lambda c: c == 'coach')
    col_level = _find_col(cells, lambda c: c == 'level')
    col_bundle = _find_col(cells, lambda c: c.startswith('bundle'))

    rows = []
    for r in range(meta['data_start'], len(df)):
        row = df.iloc[r]
        raw_name = row.iloc[col_name] if col_name is not None else None
        if not _is_plausible_name(raw_name):
            continue
        rows.append({
            'name': normalize_name(raw_name),
            'coach': normalize_name(row.iloc[col_coach]) if col_coach is not None and not _is_blank(row.iloc[col_coach]) else None,
            'level': normalize_name(row.iloc[col_level]) if col_level is not None and not _is_blank(row.iloc[col_level]) else None,
            'bundle': normalize_name(row.iloc[col_bundle]) if col_bundle is not None and not _is_blank(row.iloc[col_bundle]) else None,
        })
    return rows


def _parse_payments_sheet(df, meta):
    header_row = meta['header_rows'][0]
    cells = [_cellstr(v) for v in df.iloc[header_row].tolist()]
    col_member = _find_col(cells, lambda c: c == 'member')
    if col_member is None:
        col_member = _find_col(cells, lambda c: c == 'name')
    col_level = _find_col(cells, lambda c: c == 'level')
    col_coach = _find_col(cells, lambda c: c == 'coach')
    col_bundle = _find_col(cells, lambda c: c == 'bundle')
    if col_bundle is None:
        col_bundle = _find_col(cells, lambda c: c.startswith('bundle'))
    col_amount = _find_col(cells, lambda c: 'amount' in c)
    col_discount = _find_col(cells, lambda c: 'discount' in c)
    col_dop = _find_col(cells, lambda c: c == 'dop' or 'date of payment' in c)

    rows = []
    for r in range(meta['data_start'], len(df)):
        row = df.iloc[r]
        raw_name = row.iloc[col_member] if col_member is not None else None
        if not _is_plausible_name(raw_name):
            continue

        amount = None
        if col_amount is not None and not _is_blank(row.iloc[col_amount]):
            try:
                amount = float(row.iloc[col_amount])
            except (TypeError, ValueError):
                amount = None

        discount = 0.0
        if col_discount is not None and not _is_blank(row.iloc[col_discount]):
            try:
                discount = float(row.iloc[col_discount])
            except (TypeError, ValueError):
                discount = 0.0

        payment_date = None
        if col_dop is not None and not _is_blank(row.iloc[col_dop]):
            try:
                payment_date = pd.to_datetime(row.iloc[col_dop]).strftime('%Y-%m-%d')
            except (TypeError, ValueError):
                payment_date = None

        rows.append({
            'name': normalize_name(raw_name),
            'level': normalize_name(row.iloc[col_level]) if col_level is not None and not _is_blank(row.iloc[col_level]) else None,
            'coach': normalize_name(row.iloc[col_coach]) if col_coach is not None and not _is_blank(row.iloc[col_coach]) else None,
            'bundle': normalize_name(row.iloc[col_bundle]) if col_bundle is not None and not _is_blank(row.iloc[col_bundle]) else None,
            'amount': amount,
            'discount': discount,
            'payment_date': payment_date,
        })
    return rows


def _parse_attendance_grid_3col(df, meta):
    rows = []
    for date_col in meta['date_cols']:
        date_val = df.iat[meta['date_row'], date_col]
        if not _is_dateish(date_val):
            continue
        date_str = pd.Timestamp(date_val).strftime('%Y-%m-%d')
        off_col, on_col, coach_col = date_col, date_col + 1, date_col + 2
        for r in range(meta['data_start'], len(df)):
            coach_val = df.iat[r, coach_col] if coach_col < df.shape[1] else None
            coach_name = None
            if not _is_blank(coach_val) and _cellstr(coach_val) not in SKIP_NAME_TOKENS and not _is_dateish(coach_val):
                coach_name = normalize_name(coach_val)

            off_val = df.iat[r, off_col] if off_col < df.shape[1] else None
            if _is_plausible_name(off_val):
                rows.append({'name': normalize_name(off_val), 'date': date_str, 'session_type': 'off-ice', 'coach': coach_name})

            on_val = df.iat[r, on_col] if on_col < df.shape[1] else None
            if _is_plausible_name(on_val):
                rows.append({'name': normalize_name(on_val), 'date': date_str, 'session_type': 'on-ice', 'coach': coach_name})
    return rows


def _parse_attendance_grid_1col(df, meta):
    rows = []
    for date_col in meta['date_cols']:
        date_val = df.iat[meta['date_row'], date_col]
        if not _is_dateish(date_val):
            continue
        date_str = pd.Timestamp(date_val).strftime('%Y-%m-%d')
        for r in range(meta['data_start'], len(df)):
            val = df.iat[r, date_col]
            if _is_plausible_name(val):
                rows.append({'name': normalize_name(val), 'date': date_str, 'session_type': 'off-ice', 'coach': None})
    return rows


def parse_workbook(file_bytes: bytes):
    """
    يحلل ملف إكسل كامل (كل الأوراق) ويعيد بنية موحدة:
    {
      'roster_rows': [...],
      'payment_rows': [...],
      'attendance_rows': [...],
      'sheet_notes': [{'sheet': str, 'type': str, 'message': str}],
    }
    """
    xl = pd.ExcelFile(BytesIO(file_bytes))
    roster_rows, payment_rows, attendance_rows, sheet_notes = [], [], [], []

    for sheet_name in xl.sheet_names:
        df = xl.parse(sheet_name, header=None)
        meta = _classify_sheet(sheet_name, df)
        stype = meta['type']

        if stype == 'roster':
            parsed = _parse_roster_sheet(df, meta)
            roster_rows.extend(parsed)
            sheet_notes.append({'sheet': sheet_name, 'type': stype,
                                 'message': f'تم التعرف عليها كقائمة أعضاء: {len(parsed)} صف'})
        elif stype == 'payments':
            parsed = _parse_payments_sheet(df, meta)
            payment_rows.extend(parsed)
            sheet_notes.append({'sheet': sheet_name, 'type': stype,
                                 'message': f'تم التعرف عليها كدفعات/عضويات: {len(parsed)} صف'})
        elif stype == 'attendance_grid_3col':
            parsed = _parse_attendance_grid_3col(df, meta)
            attendance_rows.extend(parsed)
            sheet_notes.append({'sheet': sheet_name, 'type': stype,
                                 'message': f'تم التعرف عليها كجدول حضور ({len(meta["date_cols"])} يوم): {len(parsed)} سجل حضور'})
        elif stype == 'attendance_grid_1col':
            parsed = _parse_attendance_grid_1col(df, meta)
            attendance_rows.extend(parsed)
            sheet_notes.append({'sheet': sheet_name, 'type': stype,
                                 'message': f'تم التعرف عليها كجدول حضور بسيط ({len(meta["date_cols"])} يوم): {len(parsed)} سجل حضور'})
        elif stype == 'monthly_report':
            sheet_notes.append({'sheet': sheet_name, 'type': stype,
                                 'message': 'ورقة تقرير إجمالي شهري (ملخص وليس بيانات خام) — لن يتم استيراد بيانات منها لأنها إجماليات محسوبة مسبقاً وسيحسبها النظام تلقائياً من الحضور والدفعات المستوردة'})
        elif stype == 'empty':
            sheet_notes.append({'sheet': sheet_name, 'type': stype, 'message': meta.get('reason', 'ورقة فارغة')})
        else:
            sheet_notes.append({'sheet': sheet_name, 'type': stype,
                                 'message': meta.get('reason', 'لم يتم التعرف على شكل هذه الورقة، لم يتم استيراد أي بيانات منها')})

    return {
        'roster_rows': roster_rows,
        'payment_rows': payment_rows,
        'attendance_rows': attendance_rows,
        'sheet_notes': sheet_notes,
    }
