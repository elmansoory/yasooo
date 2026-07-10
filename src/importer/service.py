"""
خدمة استيراد إكسل - تقارن البيانات المُحلَّلة بقاعدة البيانات (preview) ثم تكتبها (commit).
كل دوال هذا الملف تأخذ اتصال sqlite3 حي.
"""
from .parser import name_key, normalize_name

MEMBER_FIELDS = ('level', 'coach', 'bundle')


def _load_existing_members(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, name, level, coach, bundle FROM members")
    by_key = {}
    for mid, name, level, coach, bundle in cur.fetchall():
        by_key[name_key(name)] = {
            'id': mid, 'name': name, 'level': level, 'coach': coach, 'bundle': bundle,
        }
    return by_key


def build_preview(conn, parsed):
    """
    يقارن البيانات المُحلَّلة من الملف بقاعدة البيانات الحالية.
    يعيد بنية تلخّص: أعضاء جدد، أعضاء تم التعرف عليهم، تحديثات حقول فارغة،
    دفعات جديدة/مكررة، سجلات حضور جديدة/مكررة، وأسماء حضور غير معروفة.
    لا يكتب أي شيء في قاعدة البيانات.
    """
    existing_members = _load_existing_members(conn)

    new_members = {}
    matched_updates = {}

    def register_member_info(raw_name, level, coach, bundle):
        key = name_key(raw_name)
        if key in existing_members:
            m = existing_members[key]
            upd = matched_updates.setdefault(key, {'id': m['id'], 'name': m['name'], 'changes': {}})
            for field, val in (('level', level), ('coach', coach), ('bundle', bundle)):
                if val and not (m.get(field) or '').strip() and field not in upd['changes']:
                    upd['changes'][field] = val
        else:
            entry = new_members.setdefault(key, {'name': normalize_name(raw_name), 'level': None, 'coach': None, 'bundle': None})
            for field, val in (('level', level), ('coach', coach), ('bundle', bundle)):
                if val and not entry[field]:
                    entry[field] = val
        return key

    for row in parsed['roster_rows']:
        register_member_info(row['name'], row.get('level'), row.get('coach'), row.get('bundle'))
    for row in parsed['payment_rows']:
        register_member_info(row['name'], row.get('level'), row.get('coach'), row.get('bundle'))

    cur = conn.cursor()
    payments_new, payments_dup = [], []
    for row in parsed['payment_rows']:
        key = name_key(row['name'])
        member_id = existing_members[key]['id'] if key in existing_members else None
        is_dup = False
        if member_id is not None:
            cur.execute(
                "SELECT id FROM memberships WHERE member_id=? AND bundle_type IS ? AND amount IS ? AND payment_date IS ?",
                (member_id, row.get('bundle'), row.get('amount'), row.get('payment_date')),
            )
            is_dup = cur.fetchone() is not None
        item = {**row, 'member_key': key, 'existing_member_id': member_id}
        (payments_dup if is_dup else payments_new).append(item)

    attendance_new, attendance_dup, attendance_unmatched = [], [], {}
    for row in parsed['attendance_rows']:
        key = name_key(row['name'])
        if key in existing_members:
            member_id = existing_members[key]['id']
            cur.execute(
                "SELECT id FROM attendance WHERE member_id=? AND date=? AND session_type=?",
                (member_id, row['date'], row['session_type']),
            )
            item = {**row, 'member_key': key, 'existing_member_id': member_id}
            if cur.fetchone() is not None:
                attendance_dup.append(item)
            else:
                attendance_new.append(item)
        elif key in new_members:
            # سيتم إنشاء هذا العضو ضمن نفس عملية الاستيراد، لذلك حضوره جديد بالتأكيد
            item = {**row, 'member_key': key, 'existing_member_id': None}
            attendance_new.append(item)
        else:
            attendance_unmatched[row['name']] = attendance_unmatched.get(row['name'], 0) + 1

    return {
        'sheet_notes': parsed['sheet_notes'],
        'new_members': list(new_members.values()),
        'matched_updates': [u for u in matched_updates.values() if u['changes']],
        'payments_new': payments_new,
        'payments_dup': payments_dup,
        'attendance_new': attendance_new,
        'attendance_dup': attendance_dup,
        'attendance_unmatched': sorted(attendance_unmatched.items(), key=lambda x: -x[1]),
    }


def commit_import(conn, preview):
    """
    يكتب نتائج المعاينة في قاعدة البيانات داخل معاملة واحدة.
    يعيد إعادة فحص التكرار وقت الكتابة (وليس فقط وقت المعاينة) لضمان الأمان.
    """
    cur = conn.cursor()
    key_to_id = {}

    added_members = 0
    for nm in preview['new_members']:
        key = name_key(nm['name'])
        cur.execute("SELECT id FROM members WHERE name = ?", (nm['name'],))
        row = cur.fetchone()
        if row:
            key_to_id[key] = row[0]
            continue
        cur.execute(
            "INSERT INTO members (name, level, coach, bundle) VALUES (?, ?, ?, ?)",
            (nm['name'], nm.get('level'), nm.get('coach'), nm.get('bundle')),
        )
        key_to_id[key] = cur.lastrowid
        added_members += 1

    updated_members = 0
    for upd in preview['matched_updates']:
        for field, val in upd['changes'].items():
            cur.execute(
                f"UPDATE members SET {field} = ? WHERE id = ? AND ({field} IS NULL OR {field} = '')",
                (val, upd['id']),
            )
        updated_members += 1

    def resolve_member_id(item):
        if item.get('existing_member_id') is not None:
            return item['existing_member_id']
        return key_to_id.get(item['member_key'])

    added_payments = 0
    for item in preview['payments_new']:
        member_id = resolve_member_id(item)
        if member_id is None:
            continue
        cur.execute(
            "SELECT id FROM memberships WHERE member_id=? AND bundle_type IS ? AND amount IS ? AND payment_date IS ?",
            (member_id, item.get('bundle'), item.get('amount'), item.get('payment_date')),
        )
        if cur.fetchone() is not None:
            continue
        cur.execute(
            "INSERT INTO memberships (member_id, bundle_type, amount, payment_date, discount, duration_months) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (member_id, item.get('bundle'), item.get('amount'), item.get('payment_date'), item.get('discount') or 0, 1),
        )
        added_payments += 1

    added_attendance = 0
    for item in preview['attendance_new']:
        member_id = resolve_member_id(item)
        if member_id is None:
            continue
        cur.execute(
            "SELECT id FROM attendance WHERE member_id=? AND date=? AND session_type=?",
            (member_id, item['date'], item['session_type']),
        )
        if cur.fetchone() is not None:
            continue
        cur.execute(
            "INSERT INTO attendance (member_id, date, status, session_type, coach) VALUES (?, ?, ?, ?, ?)",
            (member_id, item['date'], 'present', item['session_type'], item.get('coach')),
        )
        added_attendance += 1

    conn.commit()
    return {
        'added_members': added_members,
        'updated_members': updated_members,
        'added_payments': added_payments,
        'added_attendance': added_attendance,
    }
