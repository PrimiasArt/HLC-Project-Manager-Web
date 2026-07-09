import streamlit as st
import streamlit.components.v1 as components
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.parse
import datetime
import json
import calendar

# ====================================================================
# CẤU HÌNH TRANG
# ====================================================================
st.set_page_config(
    page_title="HLC Workstation Team Project Hub",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ====================================================================
# CSS TOÀN CỤC
# ====================================================================
st.markdown("""
<style>
/* ─── LIGHT MODE: vàng kem ─────────────────────────────────────── */
[data-testid="stAppViewContainer"][class*="light"],
.stApp[data-theme="light"] {
    background-color: #fdf8ee;
}

/* Streamlit light override via attribute */
@media (prefers-color-scheme: light) {
    :root {
        --bg-card:        #fffdf5;
        --bg-panel:       #f0e8d0;
        --border-color:   #c8b87a;
        --text-primary:   #1a1000;
        --text-secondary: #4a3a18;
        --text-muted:     #6b5a38;
        --accent-blue:    #1d4ed8;
        --accent-blue-bg: #dbeafe;
        --header-bg:      #e4d9b0;
        --tag-closed-bg:  #ddd5b8;
    }
}

/* ─── DARK MODE: xám xanh ──────────────────────────────────────── */
@media (prefers-color-scheme: dark) {
    :root {
        --bg-card:        #1e2940;
        --bg-panel:       #202d44;
        --border-color:   #2d3f5c;
        --text-primary:   #e2e8f4;
        --text-secondary: #94a8c4;
        --text-muted:     #647a99;
        --accent-blue:    #38bdf8;
        --accent-blue-bg: #0c2540;
        --header-bg:      #1a2a42;
        --tag-closed-bg:  #2d3f5c;
    }
}

/* Fallback (dark) */
:root {
    --bg-card:        #1e2940;
    --bg-panel:       #202d44;
    --border-color:   #2d3f5c;
    --text-primary:   #e2e8f4;
    --text-secondary: #94a8c4;
    --text-muted:     #647a99;
    --accent-blue:    #38bdf8;
    --accent-blue-bg: #0c2540;
    --header-bg:      #1a2a42;
    --tag-closed-bg:  #2d3f5c;
}

/* ─── DATE HEADER ───────────────────────────────────────────────── */
.hlc-date-header {
    background-color: var(--header-bg);
    border: 1px solid var(--border-color);
    padding: 8px 16px;
    border-radius: 4px;
    margin-top: 14px; margin-bottom: 6px;
    display: flex; justify-content: space-between; align-items: center;
    color: var(--accent-blue);
    font-size: 13px; font-weight: bold;
}

/* ─── TASK CARD ─────────────────────────────────────────────────── */
.task-block {
    padding: 12px 14px;
    border-radius: 8px;
    margin-bottom: 8px;
    border-left: 5px solid #ccc;
    background-color: var(--bg-card);
}
.status-closed  { border-left-color: #64748b !important; background-color: var(--tag-closed-bg) !important; }
.status-doing   { border-left-color: #f59e0b !important; }
.status-done    { border-left-color: #10b981 !important; }
.status-overdue { border-left-color: #ef4444 !important; }

/* ─── STATUS BADGES ─────────────────────────────────────────────── */
.hlc-tag-badge {
    display: inline-block;
    padding: 2px 10px; font-size: 11px; font-weight: bold;
    color: #ffffff !important;
    border-radius: 6px; text-align: center;
    margin-right: 6px; min-width: 85px;
}
.tag-todo    { background-color: #4b5563; }
.tag-doing   { background-color: #f59e0b; }
.tag-done    { background-color: #10b981; }
.tag-overdue { background-color: #ef4444; }

/* ─── PRIORITY BADGES ───────────────────────────────────────────── */
.priority-gap {
    display: inline-block;
    padding: 2px 10px; font-size: 11px; font-weight: bold;
    color: #ffffff !important;
    border-radius: 6px; background-color: #c2410c; margin-right: 6px;
}
.priority-very-gap {
    display: inline-block;
    padding: 2px 10px; font-size: 11px; font-weight: 900;
    color: #ffffff !important;
    border-radius: 6px; background-color: #dc2626; margin-right: 6px;
    letter-spacing: .06em; text-transform: uppercase;
}

/* ─── TEXT ──────────────────────────────────────────────────────── */
.t-title        { font-weight: bold; font-size: 14px; color: var(--text-primary); }
.t-title-closed { font-weight: bold; font-size: 14px; color: var(--text-muted); text-decoration: line-through; }
.t-sub-info     { font-size: 11px; color: var(--text-secondary); margin-top: 6px; }

/* ─── CALENDAR TABLE ────────────────────────────────────────────── */
.cal-table { width:100%; border-collapse:collapse; font-size:12px; margin-bottom:8px; }
.cal-table th {
    background-color: var(--header-bg); color: var(--accent-blue);
    padding: 5px 2px; text-align: center; font-weight: bold; font-size: 11px;
}
.cal-table td {
    text-align: center; padding: 4px 2px;
    border: 1px solid var(--border-color);
    vertical-align: top; min-width: 34px;
}
.cal-day-num { font-size: 13px; font-weight: bold; color: var(--text-primary); }
.cal-day-today .cal-day-num {
    background-color: var(--accent-blue); color: #fff;
    border-radius: 50%; width:22px; height:22px;
    display:inline-flex; align-items:center; justify-content:center;
}
.cal-day-selected { background-color: var(--accent-blue-bg) !important; }
.cal-dots { display:flex; justify-content:center; gap:2px; margin-top:2px; min-height:8px; }
.cal-dot  { width:6px; height:6px; border-radius:50%; flex-shrink:0; }
.dot-gray   { background-color: #64748b; }
.dot-blue   { background-color: #3b82f6; }
.dot-orange { background-color: #f59e0b; }
.dot-red    { background-color: #ef4444; }
</style>
""", unsafe_allow_html=True)

# ====================================================================
# SESSION STATE
# ====================================================================
defaults = {
    "authenticated": False, "username": None, "role": None, "uid": None,
    "selected_date": datetime.date.today(), "editing_task_id": None,
    "search_kw": "", "active_tab": "tasks",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ====================================================================
# DATABASE
# ====================================================================
DB_PASS = "Sha220393..!#"
DB_USER = "postgres.ynfgjerpqjhvnuakcduv"
DB_HOST = "aws-1-ap-southeast-2.pooler.supabase.com"
DB_PORT = "6543"
DB_NAME = "postgres"
SAFE_PASS = urllib.parse.quote_plus(DB_PASS.strip())
DB_URL = f"postgres://{DB_USER}:{SAFE_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"

@st.cache_resource
def get_db_connection():
    return psycopg2.connect(DB_URL)

def run_query(sql, params=None, commit=False, fetch="all"):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            if commit:
                conn.commit(); return None
            return cur.fetchall() if fetch == "all" else cur.fetchone()
    except Exception as e:
        conn.rollback()
        st.error(f"💥 Lỗi Cloud: {e}")
        return None

def safe_json_load(raw):
    if not raw: return []
    if isinstance(raw, list): return raw
    try: return json.loads(raw)
    except: return []

def strip_tz(dt):
    if dt is None: return None
    if isinstance(dt, datetime.datetime): return dt.replace(tzinfo=None)
    return dt

# ====================================================================
# LOGIN
# ====================================================================
if not st.session_state.authenticated:
    st.markdown("<br><br><h2 style='text-align:center;color:#38bdf8;'>🔒 HLC SYSTEM CLOUD AUTHENTICATION</h2>", unsafe_allow_html=True)
    with st.form("login_form"):
        uname = st.text_input("Tên đăng nhập").strip()
        pwd   = st.text_input("Mật khẩu", type="password").strip()
        if st.form_submit_button("ĐĂNG NHẬP HỆ THỐNG", use_container_width=True):
            u = run_query("SELECT username,role,uid FROM hlc_users WHERE username=%s AND password=%s;", (uname, pwd), fetch="one")
            if u:
                st.session_state.update(authenticated=True, username=u['username'], role=u['role'], uid=str(u['uid']))
                st.rerun()
            else:
                st.error("❌ Sai thông tin xác thực!")
    st.stop()

# ====================================================================
# TẢI DỮ LIỆU
# ====================================================================
users_db       = run_query("SELECT username,uid,role FROM hlc_users ORDER BY username ASC;") or []
all_usernames  = [u['username'] for u in users_db]
user_uid_map   = {u['username']: str(u['uid']) for u in users_db}
user_role_map  = {u['username']: u['role']     for u in users_db}
assignable_users = all_usernames if st.session_state.role == "Admin" \
                   else [u for u in all_usernames if user_role_map.get(u) != "Admin"]

all_tasks = run_query("SELECT * FROM team_tasks ORDER BY is_closed ASC, deadline_date ASC;") or []
today_dt  = datetime.datetime.now()

# ── TOAST THÔNG BÁO QUÁ HẠN ─────────────────────────────────────
overdue_tasks = [t for t in all_tasks
                 if not t['is_closed']
                 and t['status'] != 'Done'
                 and t['deadline_date']
                 and strip_tz(t['deadline_date']) < today_dt]
overdue_count = len(overdue_tasks)
if overdue_count > 0:
    st.toast(f"🚨 {overdue_count} task QUÁ HẠN CHÓT! Kiểm tra ngay.", icon="⚠️")

# ── TOAST TASK SẮP ĐẾN HẠN (trong 24h) ──────────────────────────
soon_tasks = [t for t in all_tasks
              if not t['is_closed']
              and t['status'] != 'Done'
              and t['deadline_date']
              and today_dt <= strip_tz(t['deadline_date']) <= today_dt + datetime.timedelta(hours=24)]
if soon_tasks:
    st.toast(f"⏰ {len(soon_tasks)} task đến hạn trong 24 giờ tới!", icon="🔔")

# ====================================================================
# PRIORITY HELPERS
# ====================================================================
PRIORITY_OPTIONS = ["(Không có)", "Gấp", "Rất Gấp"]

def get_priority(task):
    raw = task.get('task_docs') or ""
    if raw.startswith("__PRIORITY__:"):
        return raw.split("\n", 1)[0].replace("__PRIORITY__:", "").strip()
    return ""

def get_docs_clean(task):
    raw = task.get('task_docs') or ""
    if raw.startswith("__PRIORITY__:"):
        parts = raw.split("\n", 1)
        return parts[1] if len(parts) > 1 else ""
    return raw

def pack_docs(priority, docs_text):
    if priority and priority != "(Không có)":
        return f"__PRIORITY__:{priority}\n{docs_text}"
    return docs_text

def priority_html(p):
    if p == "Gấp":      return '<span class="priority-gap">🔶 Gấp</span>'
    if p == "Rất Gấp":  return '<span class="priority-very-gap">🚨 RẤT GẤP</span>'
    return ""

# ====================================================================
# EDIT TASK POPUP
# ====================================================================
if st.session_state.editing_task_id is not None:
    task = run_query("SELECT * FROM team_tasks WHERE id=%s;", (st.session_state.editing_task_id,), fetch="one")
    if task:
        st.markdown(f"### ✏️ Chi Tiết & Chỉnh Sửa: `{task['task_name']}`")
        is_owner = (st.session_state.role == "Admin"
                    or st.session_state.username.lower() in
                       [str(task['created_by']).lower(), str(task['assignee']).lower()])
        sub_tasks    = safe_json_load(task['sub_tasks'])
        tagged_users = safe_json_load(task['tagged_users'])
        cur_priority = get_priority(task)
        docs_display = get_docs_clean(task)

        with st.form("edit_task_form"):
            edit_name     = st.text_input("Tên đầu việc", value=task['task_name'],
                                          disabled=not is_owner or task['is_closed'])
            priority_idx  = PRIORITY_OPTIONS.index(cur_priority) if cur_priority in PRIORITY_OPTIONS else 0
            edit_priority = st.selectbox("🚨 Tag Ưu Tiên", PRIORITY_OPTIONS, index=priority_idx,
                                         disabled=not is_owner or task['is_closed'])
            edit_assignee = st.selectbox("Nhân sự phụ trách", assignable_users,
                                         index=assignable_users.index(task['assignee'])
                                               if task['assignee'] in assignable_users else 0,
                                         disabled=not is_owner or task['is_closed'])
            col_sd, col_dl = st.columns(2)
            with col_sd:
                s_date     = task['start_date'] if isinstance(task['start_date'], datetime.date) else datetime.date.today()
                edit_start = st.date_input("Ngày bắt đầu", value=s_date, disabled=not is_owner or task['is_closed'])
            with col_dl:
                d_loc       = strip_tz(task['deadline_date']) or datetime.datetime.now()
                edit_dl_d   = st.date_input("Ngày hạn chót", value=d_loc.date(), disabled=not is_owner or task['is_closed'])
                edit_dl_t   = st.time_input("Giờ hạn chót",  value=d_loc.time(), disabled=not is_owner or task['is_closed'])
            edit_details = st.text_area("Mô tả chi tiết", value=task['task_details'] or "",
                                        disabled=not is_owner or task['is_closed'])
            edit_docs    = st.text_area("💬 Ghi chú / Comment", value=docs_display)
            edit_tags    = st.multiselect("🏷️ Thành viên hỗ trợ",
                                          [u for u in assignable_users if u != edit_assignee],
                                          default=[t for t in tagged_users if t in assignable_users],
                                          disabled=not is_owner or task['is_closed'])
            st.write("📋 **Các bước thực hiện:**")
            updated_subs = []
            for idx, si in enumerate(sub_tasks):
                cb = st.checkbox(si.get('name',''), value=si.get('done', False), key=f"sub_{idx}")
                updated_subs.append({"name": si.get('name',''), "done": cb})
            bulk = st.text_area("➕ Thêm bước hàng loạt (mỗi dòng 1 bước):", height=70)

            cs, cc, cx = st.columns([2,2,1])
            with cs: save_btn   = st.form_submit_button("💾 LƯU THAY ĐỔI", use_container_width=True)
            with cc: close_btn  = st.form_submit_button("🔒 ĐÓNG TASK",     use_container_width=True) \
                                  if is_owner and not task['is_closed'] else False
            with cx: cancel_btn = st.form_submit_button("Đóng", use_container_width=True)

            if save_btn:
                if bulk.strip() and is_owner and not task['is_closed']:
                    for line in [l.strip() for l in bulk.split('\n') if l.strip()]:
                        updated_subs.append({"name": line, "done": False})
                full_dl  = datetime.datetime.combine(edit_dl_d, edit_dl_t)
                t_uids   = [user_uid_map[u] for u in edit_tags if u in user_uid_map]
                new_docs = pack_docs(edit_priority, edit_docs)
                if is_owner and not task['is_closed']:
                    run_query("""
                        UPDATE team_tasks
                        SET task_name=%s, assignee=%s, assignee_uid=%s::uuid,
                            start_date=%s, deadline_date=%s, task_details=%s, task_docs=%s,
                            sub_tasks=%s::jsonb, tagged_users=%s::jsonb, tagged_uids=%s::jsonb
                        WHERE id=%s;
                    """, (edit_name, edit_assignee, user_uid_map.get(edit_assignee),
                          edit_start, full_dl, edit_details, new_docs,
                          json.dumps(updated_subs), json.dumps(edit_tags), json.dumps(t_uids),
                          task['id']), commit=True)
                else:
                    run_query("UPDATE team_tasks SET task_docs=%s WHERE id=%s;",
                              (pack_docs(cur_priority, edit_docs), task['id']), commit=True)
                st.session_state.editing_task_id = None; st.rerun()
            if close_btn:
                run_query("UPDATE team_tasks SET is_closed=TRUE, status='Done' WHERE id=%s;",
                          (task['id'],), commit=True)
                st.session_state.editing_task_id = None; st.rerun()
            if cancel_btn:
                st.session_state.editing_task_id = None; st.rerun()
    st.stop()

# ====================================================================
# HEADER + TAB NAVIGATION
# ====================================================================
col_hub, col_sync, col_logout = st.columns([8, 1.5, 1.5])
with col_hub:
    st.markdown(f"<h2 style='color:#38bdf8;margin:0;'>📊 HLC PRODUCTION HUB ➔ {st.session_state.username.upper()}</h2>",
                unsafe_allow_html=True)
with col_sync:
    if st.button("🔄 ĐỒNG BỘ", use_container_width=True): st.rerun()
with col_logout:
    if st.button("🚪 ĐĂNG XUẤT", use_container_width=True):
        st.session_state.authenticated = False; st.rerun()

# ── TAB NAVIGATION ───────────────────────────────────────────────
tab_labels = ["📋 Quản Lý Công Việc"]
if st.session_state.role == "Admin":
    tab_labels.append("👥 Quản Lý Nhân Sự")

tabs = st.tabs(tab_labels)

# ====================================================================
# TAB 1: QUẢN LÝ CÔNG VIỆC
# ====================================================================
with tabs[0]:

    # ── BỘ LỌC ────────────────────────────────────────────────────
    col_search, col_sort, col_view = st.columns([5, 2, 2])
    with col_search:
        st.session_state.search_kw = st.text_input(
            "🔍 Lọc theo tên việc hoặc nhân sự...",
            value=st.session_state.search_kw, key="search_input")
    with col_sort:
        sort_mode = st.selectbox("Sắp xếp", ["Mặc định", "Theo nhân sự"])
    with col_view:
        view_mode = st.selectbox("Chế độ xem", ["Kanban", "List View", "Tuần", "Tháng"])

    filtered_tasks = all_tasks[:]
    if st.session_state.search_kw.strip():
        kw = st.session_state.search_kw.lower()
        filtered_tasks = [t for t in filtered_tasks
                          if kw in str(t['task_name']).lower()
                          or kw in str(t['assignee']).lower()]
    if sort_mode == "Theo nhân sự":
        filtered_tasks = sorted(filtered_tasks, key=lambda x: (x['assignee'] or '').lower())

    st.divider()

    # ── TASK CARD RENDER ──────────────────────────────────────────
    def draw_task_item(t, prefix, uid=0):
        dl      = strip_tz(t['deadline_date'])
        overdue = not t['is_closed'] and t['status'] != 'Done' and dl and dl < today_dt
        pri     = get_priority(t)

        if t['is_closed']:
            card_cls = "task-block status-closed"
            tag_html = '<span class="hlc-tag-badge tag-todo">To do</span>'
            ttl_cls  = "t-title-closed"
        elif overdue:
            card_cls = "task-block status-overdue"
            tag_html = '<span class="hlc-tag-badge tag-overdue">Urgent</span>'
            ttl_cls  = "t-title"
        elif t['status'] == 'Done':
            card_cls = "task-block status-done"
            tag_html = '<span class="hlc-tag-badge tag-done">Done</span>'
            ttl_cls  = "t-title"
        elif t['status'] == 'Doing':
            card_cls = "task-block status-doing"
            tag_html = '<span class="hlc-tag-badge tag-doing">Processing</span>'
            ttl_cls  = "t-title"
        else:
            card_cls = "task-block"
            tag_html = '<span class="hlc-tag-badge tag-todo">To do</span>'
            ttl_cls  = "t-title"

        pri_html  = priority_html(pri)
        subs      = safe_json_load(t['sub_tasks'])
        total     = len(subs)
        done_s    = sum(1 for s in subs if s.get('done'))
        prog      = (done_s / total) if total else (1.0 if t['status'] == 'Done' else 0.0)

        st.markdown(f"""
        <div class="{card_cls}">
            <div style="display:flex;align-items:center;gap:4px;flex-wrap:wrap;">
                {tag_html}{pri_html}
                <span class="{ttl_cls}">{t['task_name']}</span>
            </div>
            <div class="t-sub-info">👤 {t['assignee']} | 🎬 {t['created_by']}</div>
        </div>""", unsafe_allow_html=True)

        c1, c2, c3 = st.columns([5, 4, 3])
        with c1:
            st.caption(f"📋 {done_s}/{total}" if total else f"⏱️ {dl.strftime('%d/%m/%Y') if dl else '—'}")
        with c2:
            st.progress(prog)
        with c3:
            if st.button("✏️ CHI TIẾT", key=f"ed_{prefix}_{t['id']}_{uid}", use_container_width=True):
                st.session_state.editing_task_id = t['id']; st.rerun()

    # ── DOT HELPER ────────────────────────────────────────────────
    def get_day_dots(day, tasks_list):
        dots = []
        for t in tasks_list:
            try:
                t_s = t['start_date'] if isinstance(t['start_date'], datetime.date) else t['created_at'].date()
                t_e = t['deadline_date'].date() if isinstance(t['deadline_date'], datetime.datetime) else t['deadline_date']
                if t_s <= day <= t_e:
                    dl  = strip_tz(t['deadline_date'])
                    ov  = not t['is_closed'] and t['status'] != 'Done' and dl and dl < today_dt
                    if t['is_closed']:       dots.append("dot-gray")
                    elif ov:                 dots.append("dot-red")
                    elif t['status']=='Done': dots.append("dot-blue")
                    elif t['status']=='Doing': dots.append("dot-orange")
                    else:                    dots.append("dot-gray")
                    if len(dots) >= 4: break
            except: pass
        return dots

    # ── LAYOUT: CỘT TRÁI (LỊCH + FORM) / CỘT PHẢI (VIEW) ────────
    col_left, col_right = st.columns([3, 7])

    with col_left:
        # LỊCH BẢNG LUÔN HIỂN THỊ
        anchor = st.session_state.selected_date
        y, m   = anchor.year, anchor.month
        today0 = datetime.date.today()
        MONTHS_VN = ["Tháng 1","Tháng 2","Tháng 3","Tháng 4","Tháng 5","Tháng 6",
                     "Tháng 7","Tháng 8","Tháng 9","Tháng 10","Tháng 11","Tháng 12"]

        cp, ct, cn = st.columns([1, 4, 1])
        with cp:
            if st.button("◀", key="cal_prev"):
                first = datetime.date(y, m, 1)
                prev  = first - datetime.timedelta(days=1)
                st.session_state.selected_date = datetime.date(prev.year, prev.month, 1)
                st.rerun()
        with ct:
            st.markdown(f"<div style='text-align:center;font-weight:bold;font-size:13px;"
                        f"color:var(--accent-blue);padding-top:6px;'>{MONTHS_VN[m-1]} {y}</div>",
                        unsafe_allow_html=True)
        with cn:
            if st.button("▶", key="cal_next"):
                _, ld = calendar.monthrange(y, m)
                st.session_state.selected_date = datetime.date(y, m, ld) + datetime.timedelta(days=1)
                st.rerun()

        cal_matrix = calendar.monthcalendar(y, m)
        DAY_HDR    = ["T2","T3","T4","T5","T6","T7","CN"]
        thead = "".join(f"<th>{d}</th>" for d in DAY_HDR)
        tbody = ""
        for week in cal_matrix:
            tbody += "<tr>"
            for ci, dn in enumerate(week):
                if dn == 0:
                    tbody += "<td></td>"
                else:
                    d_obj  = datetime.date(y, m, dn)
                    td_cls = ""
                    if d_obj == anchor: td_cls += " cal-day-selected"
                    if d_obj == today0: td_cls += " cal-day-today"
                    num_color = "#ef4444" if ci == 6 and d_obj != today0 else ""
                    num_sty   = f"color:{num_color};" if num_color else ""
                    day_span  = f'<span class="cal-day-num" style="{num_sty}">{dn}</span>'
                    dots      = get_day_dots(d_obj, filtered_tasks)
                    dots_html = "".join(f'<span class="cal-dot {c}"></span>' for c in dots[:4])
                    dots_div  = f'<div class="cal-dots">{dots_html}</div>'
                    tbody    += f'<td class="{td_cls.strip()}">{day_span}{dots_div}</td>'
            tbody += "</tr>"

        st.markdown(f"""
        <table class="cal-table">
            <thead><tr>{thead}</tr></thead>
            <tbody>{tbody}</tbody>
        </table>""", unsafe_allow_html=True)

        pick = st.date_input("Chọn ngày", value=anchor, label_visibility="collapsed")
        if pick != st.session_state.selected_date:
            st.session_state.selected_date = pick; st.rerun()

        st.markdown("""
        <div style="font-size:10px;color:var(--text-muted);display:flex;gap:8px;flex-wrap:wrap;margin-top:3px;">
            <span>⬤ <span style='color:#64748b'>Closed</span></span>
            <span>⬤ <span style='color:#3b82f6'>Done</span></span>
            <span>⬤ <span style='color:#f59e0b'>Doing</span></span>
            <span>⬤ <span style='color:#ef4444'>Quá hạn</span></span>
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>📝 **Tạo task mới:**", unsafe_allow_html=True)

        with st.form("add_task_form", clear_on_submit=True):
            c_name     = st.text_input("Tên đầu việc")
            c_priority = st.selectbox("🚨 Tag Ưu Tiên", PRIORITY_OPTIONS)
            c_assignee = st.selectbox("Nhân sự phụ trách", assignable_users,
                index=assignable_users.index(st.session_state.username)
                      if st.session_state.username in assignable_users else 0,
                disabled=(st.session_state.role == "Member"))
            c_start    = st.date_input("Ngày bắt đầu", value=st.session_state.selected_date)
            c_dl_d     = st.date_input("Hạn chót", value=st.session_state.selected_date + datetime.timedelta(days=1))
            c_dl_t     = st.time_input("Giờ hạn chót", datetime.time(18, 0))
            c_details  = st.text_area("Mô tả chi tiết")
            c_bulk     = st.text_area("Bước thực hiện (mỗi dòng 1 bước)", height=70)

            if st.form_submit_button("🚀 ĐẨY TASK LÊN CLOUD", use_container_width=True) and c_name.strip():
                subs    = [{"name": l.strip(), "done": False} for l in c_bulk.split('\n') if l.strip()]
                full_dl = datetime.datetime.combine(c_dl_d, c_dl_t)
                docs    = pack_docs(c_priority, "")
                run_query("""
                    INSERT INTO team_tasks
                        (task_name, assignee, assignee_uid, start_date, deadline_date,
                         status, task_details, task_docs, created_by, is_closed, sub_tasks, tagged_users)
                    VALUES (%s,%s,%s::uuid,%s,%s,'To-do',%s,%s,%s,FALSE,%s::jsonb,'[]'::jsonb);
                """, (c_name, c_assignee, user_uid_map.get(c_assignee), c_start, full_dl,
                      c_details, docs, st.session_state.username, json.dumps(subs)), commit=True)
                st.toast("🚀 Đã tạo task thành công!", icon="🎉"); st.rerun()

    # ── CỘT PHẢI: CÁC VIEW ────────────────────────────────────────
    with col_right:
        anchor = st.session_state.selected_date

        def on_day(t, d):
            try:
                ts = t['start_date'] if isinstance(t['start_date'], datetime.date) else t['created_at'].date()
                te = t['deadline_date'].date() if isinstance(t['deadline_date'], datetime.datetime) else t['deadline_date']
                return ts <= d <= te
            except: return False

        # KANBAN
        if view_mode == "Kanban":
            st.markdown(f"#### ⚡ KANBAN — `{anchor.strftime('%d/%m/%Y')}`")
            day_t = [t for t in filtered_tasks if on_day(t, anchor)]
            ct, cd, cn2 = st.columns(3)
            with ct:
                st.markdown("<h5 style='color:#94a3b8;text-align:center;'>📌 CẦN LÀM</h5>", unsafe_allow_html=True)
                for i, t in enumerate([x for x in day_t if x['status']=='To-do' and not x['is_closed']]):
                    draw_task_item(t, "kbt", i)
                    if st.button("LÀM ➔", key=f"mv_do_{t['id']}", use_container_width=True):
                        run_query("UPDATE team_tasks SET status='Doing' WHERE id=%s", (t['id'],), commit=True); st.rerun()
            with cd:
                st.markdown("<h5 style='color:#f59e0b;text-align:center;'>🟡 ĐANG LÀM</h5>", unsafe_allow_html=True)
                for i, t in enumerate([x for x in day_t if x['status']=='Doing' and not x['is_closed']]):
                    draw_task_item(t, "kbd", i)
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("⬅ HẠ", key=f"mv_dw_{t['id']}", use_container_width=True):
                            run_query("UPDATE team_tasks SET status='To-do' WHERE id=%s", (t['id'],), commit=True); st.rerun()
                    with b2:
                        if st.button("XONG ✅", key=f"mv_up_{t['id']}", use_container_width=True):
                            run_query("UPDATE team_tasks SET status='Done' WHERE id=%s", (t['id'],), commit=True); st.rerun()
            with cn2:
                st.markdown("<h5 style='color:#10b981;text-align:center;'>🟢 HOÀN THÀNH</h5>", unsafe_allow_html=True)
                for i, t in enumerate([x for x in day_t if x['status']=='Done' or x['is_closed']]):
                    draw_task_item(t, "kbn", i)

        # LIST VIEW
        elif view_mode == "List View":
            st.markdown(f"#### 📋 LIST VIEW — `{anchor.strftime('%d/%m/%Y')}`")
            for i, t in enumerate([x for x in filtered_tasks if on_day(x, anchor)]):
                draw_task_item(t, "lv", i)

        # TUẦN
        elif view_mode == "Tuần":
            sw = anchor - datetime.timedelta(days=anchor.weekday())
            days_w = [sw + datetime.timedelta(days=i) for i in range(7)]
            VN = ["Thứ 2","Thứ 3","Thứ 4","Thứ 5","Thứ 6","Thứ 7","Chủ Nhật"]
            st.markdown(f"#### ⏱️ TUẦN: `{sw.strftime('%d/%m')} ➔ {(sw+datetime.timedelta(days=6)).strftime('%d/%m/%Y')}`")
            for i, td in enumerate(days_w):
                dt = [t for t in filtered_tasks if on_day(t, td)]
                if not dt: continue
                st.markdown(f'<div class="hlc-date-header"><span>⭐ {VN[i].upper()} — {td.strftime("%d/%m/%Y")}</span>'
                            f'<span>{len(dt)} TASK</span></div>', unsafe_allow_html=True)
                for j, t in enumerate(dt): draw_task_item(t, "wv", j + i*100)

        # THÁNG
        elif view_mode == "Tháng":
            st.markdown(f"#### 🗓️ THÁNG: `{anchor.strftime('%m/%Y')}`")
            _, ld = calendar.monthrange(anchor.year, anchor.month)
            cur_ws = datetime.date(anchor.year, anchor.month, 1)
            cur_ws -= datetime.timedelta(days=cur_ws.weekday())
            wn = 1
            while cur_ws <= datetime.date(anchor.year, anchor.month, ld):
                cur_we = cur_ws + datetime.timedelta(days=6)
                def in_week(t, ws=cur_ws, we=cur_we):
                    try:
                        ts = t['start_date'] if isinstance(t['start_date'], datetime.date) else t['created_at'].date()
                        te = t['deadline_date'].date() if isinstance(t['deadline_date'], datetime.datetime) else t['deadline_date']
                        return not (te < ws or ts > we)
                    except: return False
                wt = [t for t in filtered_tasks if in_week(t)]
                if wt:
                    st.markdown(f'<div class="hlc-date-header" style="background:#1e3a8a;border-color:#2563eb;color:#38bdf8;">'
                                f'<span>⚡ TUẦN {wn} ({cur_ws.strftime("%d/%m")} ➔ {cur_we.strftime("%d/%m")})</span>'
                                f'<span>{len(wt)} TASK</span></div>', unsafe_allow_html=True)
                    for j, t in enumerate(wt): draw_task_item(t, "mv", j + wn*1000)
                cur_ws += datetime.timedelta(days=7); wn += 1

# ====================================================================
# TAB 2: QUẢN LÝ NHÂN SỰ (Admin only) – dùng components.html()
# ====================================================================
if st.session_state.role == "Admin" and len(tabs) > 1:
    with tabs[1]:
        st.markdown("#### 👥 BẢNG QUẢN LÝ NHÂN SỰ")

        # Build rows HTML
        rows_html = ""
        for u in users_db:
            init      = (u['username'][0] if u['username'] else "?").upper()
            role_lbl  = u['role'] or "Member"
            role_cls  = "role-admin" if role_lbl == "Admin" else "role-member"
            uid_str   = str(u['uid'])
            uid_short = uid_str[:22] + "…" if len(uid_str) > 22 else uid_str
            rows_html += f"""
            <div class="win-row">
              <div class="win-avatar">{init}</div>
              <div class="win-name">{u['username']}</div>
              <span class="win-role-badge {role_cls}">{role_lbl}</span>
              <div class="win-uid">{uid_short}</div>
            </div>"""

        panel_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ margin:0; padding:0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          background: transparent; }}
  .win-panel {{
    border: 1px solid #2d3f5c; border-radius: 6px;
    overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,.35);
  }}
  .win-titlebar {{
    background: linear-gradient(90deg, #1e3a5f 0%, #2563eb 100%);
    padding: 7px 14px;
    display: flex; align-items: center; justify-content: space-between;
    font-size: 13px; font-weight: 700; color: #fff; user-select: none;
  }}
  .win-dots {{ display:flex; gap:5px; }}
  .win-dot  {{ width:13px; height:13px; border-radius:50%; }}
  .d-red    {{ background:#ff5f56; }}
  .d-yel    {{ background:#ffbd2e; }}
  .d-grn    {{ background:#27c93f; }}
  .win-header-row {{
    display: flex; align-items: center; gap: 10px;
    padding: 6px 12px; background: #131e30;
    font-size: 11px; font-weight: 700; color: #647a99;
    border-bottom: 1px solid #2d3f5c;
  }}
  .win-row {{
    display: flex; align-items: center; gap: 10px;
    padding: 7px 12px; border-bottom: 1px solid #2d3f5c;
    font-size: 13px; color: #e2e8f4;
    transition: background .15s;
  }}
  .win-row:last-child {{ border-bottom: none; }}
  .win-row:hover {{ background: rgba(56,189,248,.08); }}
  .win-avatar {{
    width:30px; height:30px; border-radius:50%; flex-shrink:0;
    background: linear-gradient(135deg,#2563eb,#38bdf8);
    display:flex; align-items:center; justify-content:center;
    font-size:13px; font-weight:700; color:#fff;
  }}
  .win-name  {{ flex:2; font-weight:600; color:#e2e8f4; }}
  .win-role-badge {{
    display:inline-block; padding:2px 10px;
    border-radius:3px; font-size:11px; font-weight:700;
    flex-shrink:0; width:72px; text-align:center;
  }}
  .role-admin  {{ background:#0f2a4a; color:#38bdf8; border:1px solid #2563eb; }}
  .role-member {{ background:#052e20; color:#34d399; border:1px solid #10b981; }}
  .win-uid     {{ flex:3; font-size:11px; color:#647a99; font-family:monospace; }}
  .col-av  {{ width:30px; flex-shrink:0; color:#647a99; font-size:10px; text-align:center; }}
</style>
</head>
<body>
<div class="win-panel">
  <div class="win-titlebar">
    <span>🖥️ HLC User Manager &mdash; {len(users_db)} tài khoản</span>
    <div class="win-dots">
      <div class="win-dot d-red"></div>
      <div class="win-dot d-yel"></div>
      <div class="win-dot d-grn"></div>
    </div>
  </div>
  <div class="win-header-row">
    <div class="col-av">AV</div>
    <div style="flex:2;">Tên đăng nhập</div>
    <div style="width:72px;">Vai trò</div>
    <div style="flex:3;">UID</div>
  </div>
  {rows_html}
</div>
</body>
</html>"""

        # Tính chiều cao động
        row_h  = 46
        panel_h = 44 + 34 + len(users_db) * row_h + 20
        components.html(panel_html, height=panel_h, scrolling=False)

        st.markdown("---")
        col_add, col_pw = st.columns(2)
        with col_add:
            with st.expander("➕ Thêm tài khoản mới"):
                with st.form("add_user"):
                    nu = st.text_input("Username mới")
                    np = st.text_input("Password", type="password")
                    nr = st.selectbox("Vai trò", ["Member", "Admin", "Manager"])
                    if st.form_submit_button("Tạo tài khoản", use_container_width=True) and nu.strip():
                        run_query("INSERT INTO hlc_users (username,password,role) VALUES (%s,%s,%s);",
                                  (nu.strip(), np, nr), commit=True)
                        st.success(f"✅ Đã tạo: {nu}"); st.rerun()
        with col_pw:
            with st.expander("🔑 Đổi mật khẩu"):
                with st.form("chg_pw"):
                    su = st.selectbox("Chọn user", all_usernames)
                    pw = st.text_input("Mật khẩu mới", type="password")
                    if st.form_submit_button("Cập nhật", use_container_width=True) and pw.strip():
                        run_query("UPDATE hlc_users SET password=%s WHERE username=%s;", (pw, su), commit=True)
                        st.success(f"✅ Đã đổi mật khẩu cho: {su}")
