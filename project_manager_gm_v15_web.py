import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.parse
import datetime
import json
import calendar

# ====================================================================
# 💾 CẤU HÌNH TRANG VÀ THEME HỆ THỐNG
# ====================================================================
st.set_page_config(
    page_title="HLC Workstation Team Project Hub",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ────────────────────────────────────────────────────────────────────
# THEME: LIGHT = vàng kem | DARK = xám xanh
# ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ===== LIGHT MODE – tone vàng kem ===== */
@media (prefers-color-scheme: light) {
    :root {
        --bg-main:       #fdf8ee;
        --bg-card:       #fffdf5;
        --bg-sidebar:    #f5eedb;
        --bg-panel:      #f0e8d0;
        --border-color:  #d4c49a;
        --text-primary:  #2d2416;
        --text-secondary:#6b5a38;
        --text-muted:    #9c8660;
        --accent-blue:   #2563eb;
        --accent-blue-bg:#dbeafe;
        --header-bg:     #e8dfc0;
        --tag-closed-bg: #e0d8c0;
        --tag-closed-txt:#7a6a48;
    }
}
/* ===== DARK MODE – tone xám xanh ===== */
@media (prefers-color-scheme: dark) {
    :root {
        --bg-main:       #1a2234;
        --bg-card:       #1e2940;
        --bg-sidebar:    #161f30;
        --bg-panel:      #202d44;
        --border-color:  #2d3f5c;
        --text-primary:  #e2e8f4;
        --text-secondary:#94a8c4;
        --text-muted:    #647a99;
        --accent-blue:   #38bdf8;
        --accent-blue-bg:#0c2540;
        --header-bg:     #1a2a42;
        --tag-closed-bg: #2d3f5c;
        --tag-closed-txt:#8da4c0;
    }
}
/* Fallback variables (Streamlit dark default) */
:root {
    --bg-main:       #1a2234;
    --bg-card:       #1e2940;
    --bg-sidebar:    #161f30;
    --bg-panel:      #202d44;
    --border-color:  #2d3f5c;
    --text-primary:  #e2e8f4;
    --text-secondary:#94a8c4;
    --text-muted:    #647a99;
    --accent-blue:   #38bdf8;
    --accent-blue-bg:#0c2540;
    --header-bg:     #1a2a42;
    --tag-closed-bg: #2d3f5c;
    --tag-closed-txt:#8da4c0;
}

/* ===== DATE HEADER ===== */
.hlc-date-header {
    background-color: var(--header-bg);
    border: 1px solid var(--border-color);
    padding: 8px 16px;
    border-radius: 4px;
    margin-top: 14px;
    margin-bottom: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: var(--accent-blue);
    font-size: 13px;
    font-weight: bold;
}

/* ===== TASK CARD ===== */
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

/* ===== TAG BADGES ===== */
.hlc-tag-badge {
    display: inline-block;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: bold;
    color: #ffffff !important;
    border-radius: 6px;
    text-align: center;
    margin-right: 6px;
    min-width: 85px;
}
.tag-todo    { background-color: #4b5563; }
.tag-doing   { background-color: #f59e0b; }
.tag-done    { background-color: #10b981; }
.tag-overdue { background-color: #ef4444; }

/* ===== PRIORITY TAG BADGES ===== */
.priority-gap {
    display: inline-block;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: bold;
    color: #ffffff !important;
    border-radius: 6px;
    background-color: #c2410c;
    margin-right: 6px;
}
.priority-very-gap {
    display: inline-block;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 900;
    color: #ffffff !important;
    border-radius: 6px;
    background-color: #dc2626;
    margin-right: 6px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* ===== TITLE STYLES ===== */
.t-title        { font-weight: bold; font-size: 14px; color: var(--text-primary); }
.t-title-closed { font-weight: bold; font-size: 14px; color: var(--text-muted); text-decoration: line-through; }
.t-sub-info     { font-size: 11px; color: var(--text-secondary); margin-top: 6px; padding-left: 2px; }

/* ===== CALENDAR TABLE ===== */
.cal-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    margin-bottom: 10px;
}
.cal-table th {
    background-color: var(--header-bg);
    color: var(--accent-blue);
    padding: 6px 2px;
    text-align: center;
    font-weight: bold;
    font-size: 11px;
}
.cal-table td {
    text-align: center;
    padding: 5px 2px;
    border: 1px solid var(--border-color);
    vertical-align: top;
    cursor: pointer;
    min-width: 36px;
    min-height: 40px;
}
.cal-day-num {
    font-size: 13px;
    font-weight: bold;
    color: var(--text-primary);
}
.cal-day-today .cal-day-num {
    background-color: var(--accent-blue);
    color: #fff;
    border-radius: 50%;
    width: 22px;
    height: 22px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}
.cal-day-selected {
    background-color: var(--accent-blue-bg) !important;
}
.cal-day-other-month .cal-day-num { color: var(--text-muted); }
.cal-dots {
    display: flex;
    justify-content: center;
    gap: 2px;
    margin-top: 2px;
    min-height: 8px;
}
.cal-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
}
.dot-gray { background-color: #64748b; }
.dot-blue { background-color: #3b82f6; }
.dot-orange { background-color: #f59e0b; }
.dot-red { background-color: #ef4444; }

/* ===== ADMIN PANEL – Windows-style ===== */
.win-panel {
    background-color: var(--bg-panel);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 0;
    margin-bottom: 10px;
}
.win-titlebar {
    background: linear-gradient(90deg, #1e3a5f 0%, #2563eb 100%);
    padding: 5px 12px;
    border-radius: 4px 4px 0 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 12px;
    font-weight: bold;
    color: #fff;
}
.win-titlebar-btn {
    display: inline-block;
    width: 12px; height: 12px;
    border-radius: 50%;
    margin-left: 4px;
    cursor: pointer;
}
.win-btn-red { background: #ff5f56; }
.win-btn-yellow { background: #ffbd2e; }
.win-btn-green { background: #27c93f; }
.win-body { padding: 10px 14px; }
.win-row {
    display: flex;
    align-items: center;
    padding: 6px 8px;
    border-bottom: 1px solid var(--border-color);
    font-size: 13px;
    gap: 8px;
}
.win-row:last-child { border-bottom: none; }
.win-row:hover { background-color: var(--accent-blue-bg); }
.win-avatar {
    width: 28px; height: 28px;
    border-radius: 50%;
    background: linear-gradient(135deg, #2563eb, #38bdf8);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: bold;
    color: #fff;
    flex-shrink: 0;
}
.win-name { font-weight: bold; color: var(--text-primary); flex: 2; }
.win-role-badge {
    display: inline-block;
    padding: 1px 8px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: bold;
}
.role-admin { background: #1e3a5f; color: #38bdf8; border: 1px solid #2563eb; }
.role-member { background: #064e3b; color: #34d399; border: 1px solid #10b981; }
.win-uid { font-size: 10px; color: var(--text-muted); flex: 3; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

# ====================================================================
# SESSION STATE TOÀN CỤC
# ====================================================================
defaults = {
    "authenticated": False, "username": None, "role": None, "uid": None,
    "selected_date": datetime.date.today(), "editing_task_id": None,
    "search_kw": "", "show_admin_panel": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ====================================================================
# 🔑 KẾT NỐI DATABASE SUPABASE
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
                conn.commit()
                return None
            if fetch == "all": return cur.fetchall()
            elif fetch == "one": return cur.fetchone()
    except Exception as e:
        conn.rollback()
        st.error(f"💥 Lỗi Kết Nối Cloud: {e}")
        return None

def safe_json_load(raw_data):
    if not raw_data: return []
    if isinstance(raw_data, list): return raw_data
    if isinstance(raw_data, str):
        try: return json.loads(raw_data)
        except: return []
    return []

def strip_tz(dt):
    if dt is None: return None
    if isinstance(dt, datetime.datetime): return dt.replace(tzinfo=None)
    return dt

# ====================================================================
# 🔒 SCREEN ĐĂNG NHẬP
# ====================================================================
if not st.session_state.authenticated:
    st.markdown("<br><br><h2 style='text-align: center; color: #38bdf8;'>🔒 HLC SYSTEM CLOUD AUTHENTICATION</h2>", unsafe_allow_html=True)
    with st.form("login_form"):
        username = st.text_input("Tên đăng nhập (Username)").strip()
        password = st.text_input("Mật khẩu (Password)", type="password").strip()
        submit = st.form_submit_button("ĐĂNG NHẬP HỆ THỐNG", use_container_width=True)
        if submit:
            user = run_query("SELECT username, role, uid FROM hlc_users WHERE username = %s AND password = %s;", (username, password), fetch="one")
            if user:
                st.session_state.authenticated = True
                st.session_state.username = user['username']
                st.session_state.role = user['role']
                st.session_state.uid = str(user['uid'])
                st.rerun()
            else: st.error("❌ Sai thông tin xác thực tài khoản!")
    st.stop()

# ====================================================================
# TẢI DỮ LIỆU CHÍNH
# ====================================================================
users_db = run_query("SELECT username, uid, role FROM hlc_users ORDER BY username ASC;") or []
all_usernames = [u['username'] for u in users_db]
user_uid_map = {u['username']: str(u['uid']) for u in users_db}
user_role_map = {u['username']: u['role'] for u in users_db}
assignable_users = all_usernames if st.session_state.role == "Admin" else [un for un in all_usernames if user_role_map.get(un) != "Admin"]

all_tasks = run_query("SELECT * FROM team_tasks ORDER BY is_closed ASC, deadline_date ASC;") or []
today_dt = datetime.datetime.now()

# Toast cảnh báo overdue
overdue_count = sum(1 for t in all_tasks if not t['is_closed'] and t['status'] != 'Done' and t['deadline_date'] and strip_tz(t['deadline_date']) < today_dt)
if overdue_count > 0:
    st.toast(f"🚨 Hệ thống phát hiện {overdue_count} task đang ở trạng thái QUÁ HẠN CHÓT!", icon="⚠️")

# ====================================================================
# PRIORITY TAG OPTIONS
# ====================================================================
PRIORITY_OPTIONS = ["(Không có)", "Gấp", "Rất Gấp"]

def priority_html(priority):
    if priority == "Gấp":
        return '<span class="priority-gap">🔶 Gấp</span>'
    elif priority == "Rất Gấp":
        return '<span class="priority-very-gap">🚨 RẤT GẤP</span>'
    return ""

# ====================================================================
# ✏️ POP-UP EDIT CHI TIẾT TASK
# ====================================================================
if st.session_state.editing_task_id is not None:
    task = run_query("SELECT * FROM team_tasks WHERE id = %s;", (st.session_state.editing_task_id,), fetch="one")
    if task:
        st.markdown(f"### ✏️ Chi Tiết & Chỉnh Sửa Đầu Việc: `{task['task_name']}`")
        is_owner = st.session_state.role == "Admin" or st.session_state.username.lower() in [task['created_by'].lower(), task['assignee'].lower()]
        sub_tasks = safe_json_load(task['sub_tasks'])
        tagged_users = safe_json_load(task['tagged_users'])

        # Đọc priority từ task_docs (JSON metadata) hoặc field riêng nếu có
        # Lưu priority trong task_docs dưới dạng prefix "__PRIORITY__:value\n"
        docs_raw = task['task_docs'] or ""
        current_priority = "(Không có)"
        docs_display = docs_raw
        if docs_raw.startswith("__PRIORITY__:"):
            lines = docs_raw.split("\n", 1)
            current_priority = lines[0].replace("__PRIORITY__:", "").strip()
            docs_display = lines[1] if len(lines) > 1 else ""

        with st.form("edit_task_form_cloud"):
            edit_name = st.text_input("Tên đầu việc", value=task['task_name'], disabled=not is_owner or task['is_closed'])
            
            # TAG ƯU TIÊN
            priority_idx = PRIORITY_OPTIONS.index(current_priority) if current_priority in PRIORITY_OPTIONS else 0
            edit_priority = st.selectbox(
                "🚨 Tag Ưu Tiên",
                PRIORITY_OPTIONS,
                index=priority_idx,
                disabled=not is_owner or task['is_closed']
            )

            edit_assignee = st.selectbox("Nhân sự phụ trách", assignable_users,
                index=assignable_users.index(task['assignee']) if task['assignee'] in assignable_users else 0,
                disabled=not is_owner or task['is_closed'])

            col_sd, col_dl = st.columns(2)
            with col_sd:
                s_date = task['start_date'] if isinstance(task['start_date'], datetime.date) else datetime.date.today()
                edit_start = st.date_input("Ngày bắt đầu", value=s_date, disabled=not is_owner or task['is_closed'])
            with col_dl:
                d_loc = strip_tz(task['deadline_date']) or datetime.datetime.now()
                edit_dl_date = st.date_input("Ngày hạn chót", value=d_loc.date(), disabled=not is_owner or task['is_closed'])
                edit_dl_time = st.time_input("Giờ hạn chót", value=d_loc.time(), disabled=not is_owner or task['is_closed'])

            edit_details = st.text_area("Mô tả chi tiết", value=task['task_details'] or "", disabled=not is_owner or task['is_closed'])
            edit_docs = st.text_area("💬 Ghi chú báo cáo (Comment Note)", value=docs_display)
            edit_tags = st.multiselect("🏷️ Thành viên hỗ trợ",
                [u for u in assignable_users if u != edit_assignee],
                default=[t for t in tagged_users if t in assignable_users],
                disabled=not is_owner or task['is_closed'])

            st.write("📋 **Các bước thực hiện:**")
            updated_sub_tasks = []
            for idx, st_item in enumerate(sub_tasks):
                cb_val = st.checkbox(st_item.get('name', ''), value=st_item.get('done', False), key=f"sub_cb_{idx}")
                updated_sub_tasks.append({"name": st_item.get('name', ''), "done": cb_val})

            bulk_sub_input = st.text_area("➕ Thêm hàng loạt bước thực hiện (Mỗi bước 1 dòng):", height=80)

            col_save, col_close_t, col_cancel = st.columns([2, 2, 1])
            with col_save: save_btn = st.form_submit_button("💾 LƯU THAY ĐỔI LÊN CLOUD", use_container_width=True)
            with col_close_t: close_btn = st.form_submit_button("🔒 ĐÓNG TASK VĨNH VIỄN", use_container_width=True) if is_owner and not task['is_closed'] else False
            with col_cancel: cancel_btn = st.form_submit_button("Đóng", use_container_width=True)

            if save_btn:
                if bulk_sub_input.strip() and is_owner and not task['is_closed']:
                    for line in [l.strip() for l in bulk_sub_input.split('\n') if l.strip()]:
                        updated_sub_tasks.append({"name": line, "done": False})
                full_dl = datetime.datetime.combine(edit_dl_date, edit_dl_time)
                t_uids = [user_uid_map[u] for u in edit_tags if u in user_uid_map]

                # Đóng gói priority vào task_docs
                priority_prefix = f"__PRIORITY__:{edit_priority}\n" if edit_priority != "(Không có)" else ""
                final_docs = priority_prefix + edit_docs

                if is_owner and not task['is_closed']:
                    run_query("""
                        UPDATE team_tasks SET task_name=%s, assignee=%s, assignee_uid=%s::uuid,
                        start_date=%s, deadline_date=%s, task_details=%s, task_docs=%s,
                        sub_tasks=%s::jsonb, tagged_users=%s::jsonb, tagged_uids=%s::jsonb
                        WHERE id=%s;
                    """, (edit_name, edit_assignee, user_uid_map.get(edit_assignee), edit_start, full_dl,
                          edit_details, final_docs, json.dumps(updated_sub_tasks),
                          json.dumps(edit_tags), json.dumps(t_uids), task['id']), commit=True)
                else:
                    # Member chỉ update docs
                    priority_prefix2 = f"__PRIORITY__:{current_priority}\n" if current_priority != "(Không có)" else ""
                    run_query("UPDATE team_tasks SET task_docs=%s WHERE id=%s;",
                              (priority_prefix2 + edit_docs, task['id']), commit=True)
                st.session_state.editing_task_id = None
                st.rerun()
            if close_btn:
                run_query("UPDATE team_tasks SET is_closed=TRUE, status='Done' WHERE id=%s;", (task['id'],), commit=True)
                st.session_state.editing_task_id = None
                st.rerun()
            if cancel_btn:
                st.session_state.editing_task_id = None
                st.rerun()
    st.stop()

# ====================================================================
# HELPER – lấy priority từ task_docs
# ====================================================================
def get_task_priority(task):
    docs_raw = task.get('task_docs') or ""
    if docs_raw.startswith("__PRIORITY__:"):
        line = docs_raw.split("\n", 1)[0]
        return line.replace("__PRIORITY__:", "").strip()
    return ""

# ====================================================================
# BANNER ĐẦU TRANG
# ====================================================================
col_hub, col_sync, col_admin_btn, col_logout = st.columns([6, 1.5, 2, 1.5])
with col_hub:
    st.markdown(f"<h2 style='color: #38bdf8; margin:0;'>📊 HLC PRODUCTION HUB ➔ {st.session_state.username.upper()}</h2>", unsafe_allow_html=True)
with col_sync:
    if st.button("🔄 ĐỒNG BỘ", use_container_width=True): st.rerun()
with col_admin_btn:
    if st.session_state.role == "Admin":
        admin_label = "👥 ẨN NHÂN SỰ" if st.session_state.show_admin_panel else "👥 QUẢN LÝ NHÂN SỰ"
        if st.button(admin_label, use_container_width=True):
            st.session_state.show_admin_panel = not st.session_state.show_admin_panel
            st.rerun()
with col_logout:
    if st.button("🚪 ĐĂNG XUẤT", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# ====================================================================
# 👥 BẢNG QUẢN LÝ NHÂN SỰ – WINDOWS STYLE (Admin only)
# ====================================================================
if st.session_state.role == "Admin" and st.session_state.show_admin_panel:
    st.markdown("---")
    st.markdown("#### 👥 BẢNG QUẢN LÝ NHÂN SỰ")

    # Windows-style panel
    rows_html = ""
    for u in users_db:
        initial = u['username'][0].upper() if u['username'] else "?"
        role_cls = "role-admin" if u['role'] == "Admin" else "role-member"
        role_label = u['role'] or "Member"
        uid_short = str(u['uid'])[:18] + "…" if len(str(u['uid'])) > 18 else str(u['uid'])
        rows_html += f"""
        <div class="win-row">
            <div class="win-avatar">{initial}</div>
            <div class="win-name">{u['username']}</div>
            <span class="win-role-badge {role_cls}">{role_label}</span>
            <div class="win-uid">{uid_short}</div>
        </div>"""

    st.markdown(f"""
    <div class="win-panel">
        <div class="win-titlebar">
            <span>🖥️ HLC User Manager — {len(users_db)} tài khoản</span>
            <span>
                <span class="win-titlebar-btn win-btn-red"></span>
                <span class="win-titlebar-btn win-btn-yellow"></span>
                <span class="win-titlebar-btn win-btn-green"></span>
            </span>
        </div>
        <div class="win-body" style="padding:0;">
            <div class="win-row" style="background:var(--header-bg); font-weight:bold; font-size:11px; color:var(--text-secondary);">
                <div style="width:28px;"></div>
                <div style="flex:2;">Tên đăng nhập</div>
                <div style="width:70px;">Vai trò</div>
                <div style="flex:3;">UID</div>
            </div>
            {rows_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Form thêm/đổi mật khẩu
    col_form1, col_form2 = st.columns(2)
    with col_form1:
        with st.expander("➕ Thêm tài khoản mới"):
            with st.form("add_user_form"):
                new_uname = st.text_input("Username mới")
                new_pass = st.text_input("Password", type="password")
                new_role = st.selectbox("Vai trò", ["Member", "Admin"])
                if st.form_submit_button("Tạo tài khoản", use_container_width=True):
                    if new_uname.strip():
                        run_query("INSERT INTO hlc_users (username, password, role) VALUES (%s, %s, %s);",
                                  (new_uname.strip(), new_pass, new_role), commit=True)
                        st.success(f"✅ Đã tạo tài khoản: {new_uname}")
                        st.rerun()
    with col_form2:
        with st.expander("🔑 Đổi mật khẩu"):
            with st.form("change_pass_form"):
                sel_user = st.selectbox("Chọn user", all_usernames)
                new_pw = st.text_input("Mật khẩu mới", type="password")
                if st.form_submit_button("Cập nhật", use_container_width=True):
                    if new_pw.strip():
                        run_query("UPDATE hlc_users SET password=%s WHERE username=%s;", (new_pw, sel_user), commit=True)
                        st.success(f"✅ Đã đổi mật khẩu cho: {sel_user}")
    st.markdown("---")

# ====================================================================
# BỘ LỌC & SẮP XẾP
# ====================================================================
col_search, col_sort, col_view = st.columns([5, 2, 2])
with col_search:
    st.session_state.search_kw = st.text_input("🔍 Nhập tên việc hoặc nhân sự để lọc...", value=st.session_state.search_kw)
with col_sort:
    sort_mode = st.selectbox("Sắp xếp", ["Mặc định", "Theo nhân sự"])
with col_view:
    view_mode = st.selectbox("Chế độ xem", ["Kanban", "List View", "Tuần", "Tháng"], index=0)

if st.session_state.search_kw.strip():
    kw = st.session_state.search_kw.lower()
    all_tasks = [t for t in all_tasks if kw in str(t['task_name']).lower() or kw in str(t['assignee']).lower()]

if sort_mode == "Theo nhân sự":
    all_tasks = sorted(all_tasks, key=lambda x: (x['assignee'] or '').lower())

st.divider()

# ====================================================================
# FUNCTION RENDER TASK CARD
# ====================================================================
def draw_task_item(t, scope_prefix, loop_unique_id=0):
    dl_naive = strip_tz(t['deadline_date'])
    is_overdue = not t['is_closed'] and t['status'] != 'Done' and dl_naive and dl_naive < today_dt
    priority = get_task_priority(t)

    if t['is_closed']:
        card_style = "task-block status-closed"
        tag_html = '<span class="hlc-tag-badge tag-todo">To do</span>'
        title_style = "t-title-closed"
    elif is_overdue:
        card_style = "task-block status-overdue"
        tag_html = '<span class="hlc-tag-badge tag-overdue">Urgent</span>'
        title_style = "t-title"
    elif t['status'] == 'Done':
        card_style = "task-block status-done"
        tag_html = '<span class="hlc-tag-badge tag-done">Done</span>'
        title_style = "t-title"
    else:
        if t['status'] == 'Doing':
            card_style = "task-block status-doing"
            tag_html = '<span class="hlc-tag-badge tag-doing">Processing</span>'
        else:
            card_style = "task-block"
            tag_html = '<span class="hlc-tag-badge tag-todo">To do</span>'
        title_style = "t-title"

    priority_badge = priority_html(priority)

    sub_list = safe_json_load(t['sub_tasks'])
    total_steps = len(sub_list)
    done_steps = sum(1 for item in sub_list if item.get('done', False))
    progress_val = (done_steps / total_steps) if total_steps > 0 else (1.0 if t['status'] == 'Done' else 0.0)

    st.markdown(f"""
    <div class="{card_style}">
        <div style="display: flex; align-items: center; gap: 4px; flex-wrap: wrap;">
            {tag_html}{priority_badge}
            <div class="{title_style}">{t['task_name']}</div>
        </div>
        <div class="t-sub-info">
            👤 Phụ trách: {t['assignee']} | 🎬 Tạo bởi: {t['created_by']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_c1, col_c2, col_c3 = st.columns([5, 4, 3])
    with col_c1:
        if total_steps > 0: st.caption(f"📋 Bước: {done_steps}/{total_steps}")
        else: st.caption(f"⏱️ Hạn: {dl_naive.strftime('%d/%m/%Y') if dl_naive else '—'}")
    with col_c2:
        st.progress(progress_val)
    with col_c3:
        if st.button("✏️ CHI TIẾT", key=f"btn_ed_{scope_prefix}_{t['id']}_{loop_unique_id}", use_container_width=True):
            st.session_state.editing_task_id = t['id']
            st.rerun()

# ====================================================================
# HÀM TÍNH TOÁN DOT CHO LỊCH
# ====================================================================
def get_day_dots(day, tasks_list):
    """Trả về list màu dots cho ngày đó (tối đa 4 dots)."""
    dots = []
    for t in tasks_list:
        try:
            t_start = t['start_date'] if isinstance(t['start_date'], datetime.date) else t['created_at'].date()
            t_dl = t['deadline_date']
            t_end = t_dl.date() if isinstance(t_dl, datetime.datetime) else t_dl
            if t_start <= day <= t_end:
                dl_naive = strip_tz(t['deadline_date'])
                is_overdue = not t['is_closed'] and t['status'] != 'Done' and dl_naive and dl_naive < today_dt
                if t['is_closed']:
                    color = "dot-gray"
                elif is_overdue:
                    color = "dot-red"
                elif t['status'] == 'Done':
                    color = "dot-blue"
                elif t['status'] == 'Doing':
                    color = "dot-orange"
                else:
                    color = "dot-gray"
                dots.append(color)
                if len(dots) >= 4:
                    break
        except:
            pass
    return dots

# ====================================================================
# LAYOUT HAI CỘT CHÍNH
# ====================================================================
col_panel_left, col_panel_right = st.columns([3, 7])

with col_panel_left:
    # ── LỊCH DẠNG BẢNG LUÔN HIỂN THỊ ──────────────────────────────
    anchor_date = st.session_state.selected_date
    year = anchor_date.year
    month = anchor_date.month
    today_date = datetime.date.today()

    # Nút điều hướng tháng
    col_prev, col_month_title, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.button("◀", key="cal_prev"):
            first = datetime.date(year, month, 1)
            prev_month = first - datetime.timedelta(days=1)
            st.session_state.selected_date = datetime.date(prev_month.year, prev_month.month, 1)
            st.rerun()
    with col_month_title:
        MONTHS_VN = ["Tháng 1","Tháng 2","Tháng 3","Tháng 4","Tháng 5","Tháng 6",
                     "Tháng 7","Tháng 8","Tháng 9","Tháng 10","Tháng 11","Tháng 12"]
        st.markdown(f"<div style='text-align:center; font-weight:bold; font-size:13px; color:var(--accent-blue); padding-top:6px;'>{MONTHS_VN[month-1]} {year}</div>", unsafe_allow_html=True)
    with col_next:
        if st.button("▶", key="cal_next"):
            _, last_day = calendar.monthrange(year, month)
            next_month_first = datetime.date(year, month, last_day) + datetime.timedelta(days=1)
            st.session_state.selected_date = next_month_first
            st.rerun()

    # Tạo ma trận lịch
    cal_matrix = calendar.monthcalendar(year, month)  # tuần x 7 ngày (0 = ngày trống)
    DAY_HEADERS = ["T2","T3","T4","T5","T6","T7","CN"]

    # Build HTML table
    thead = "".join(f"<th>{d}</th>" for d in DAY_HEADERS)
    tbody = ""
    for week in cal_matrix:
        tbody += "<tr>"
        for col_idx, day_num in enumerate(week):
            if day_num == 0:
                tbody += "<td></td>"
            else:
                day_obj = datetime.date(year, month, day_num)
                is_today = day_obj == today_date
                is_selected = day_obj == anchor_date
                is_sunday = col_idx == 6

                # CSS classes
                day_classes = "cal-day-num"
                td_class = ""
                if is_selected:
                    td_class += " cal-day-selected"
                if is_today:
                    td_class += " cal-day-today"

                num_color = "#ef4444" if is_sunday and not is_today else ""
                num_style = f"color:{num_color};" if num_color else ""

                day_html = f'<span class="{day_classes}" style="{num_style}">{day_num}</span>'

                # Dots
                dots = get_day_dots(day_obj, all_tasks)
                dots_html = "".join(f'<span class="cal-dot {c}"></span>' for c in dots[:4])
                dots_div = f'<div class="cal-dots">{dots_html}</div>' if dots else '<div class="cal-dots"></div>'

                tbody += f'<td class="{td_class.strip()}" onclick="">{day_html}{dots_div}</td>'
        tbody += "</tr>"

    st.markdown(f"""
    <table class="cal-table">
        <thead><tr>{thead}</tr></thead>
        <tbody>{tbody}</tbody>
    </table>
    """, unsafe_allow_html=True)

    # Nút chọn ngày thủ công (đồng bộ với lịch)
    pick_date = st.date_input("📅 Chọn ngày cụ thể", value=anchor_date, label_visibility="collapsed")
    if pick_date != st.session_state.selected_date:
        st.session_state.selected_date = pick_date
        st.rerun()

    # Chú thích dots
    st.markdown("""
    <div style="font-size:10px; color:var(--text-muted); margin-top:4px; display:flex; gap:10px; flex-wrap:wrap;">
        <span><span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#64748b;"></span> Closed</span>
        <span><span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#3b82f6;"></span> Done</span>
        <span><span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#f59e0b;"></span> Doing</span>
        <span><span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#ef4444;"></span> Quá hạn</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>📝 **Tạo đầu việc mới:**", unsafe_allow_html=True)

    # ── FORM TẠO TASK ──────────────────────────────────────────────
    with st.form("add_task_form_main", clear_on_submit=True):
        c_name = st.text_input("Tên đầu việc (Task Name)")
        
        # Priority tag khi tạo mới
        c_priority = st.selectbox("🚨 Tag Ưu Tiên", PRIORITY_OPTIONS)
        
        c_assignee = st.selectbox(
            "Nhân sự phụ trách", assignable_users,
            index=assignable_users.index(st.session_state.username) if st.session_state.username in assignable_users else 0,
            disabled=(st.session_state.role == "Member")
        )
        c_start = st.date_input("📆 Ngày bắt đầu", value=st.session_state.selected_date)
        c_dl_date = st.date_input("Ngày hạn chót", value=st.session_state.selected_date + datetime.timedelta(days=1))
        c_dl_time = st.time_input("Giờ hạn chót", datetime.time(18, 0))
        c_details = st.text_area("Mô tả chi tiết công việc")
        c_bulk_sub = st.text_area("Nhập hàng loạt bước con (Mỗi việc 1 dòng)...", height=80)

        submit_new = st.form_submit_button("🚀 ĐẨY TASK LÊN ĐÁM MÂY HLC", use_container_width=True)
        if submit_new and c_name.strip():
            initial_subs = [{"name": line.strip(), "done": False} for line in c_bulk_sub.split('\n') if line.strip()]
            full_dl_new = datetime.datetime.combine(c_dl_date, c_dl_time)
            priority_prefix = f"__PRIORITY__:{c_priority}\n" if c_priority != "(Không có)" else ""
            run_query("""
                INSERT INTO team_tasks (task_name, assignee, assignee_uid, start_date, deadline_date, status,
                task_details, task_docs, created_by, is_closed, sub_tasks, tagged_users)
                VALUES (%s, %s, %s::uuid, %s, %s, 'To-do', %s, %s, %s, FALSE, %s::jsonb, '[]'::jsonb);
            """, (c_name, c_assignee, user_uid_map.get(c_assignee), c_start, full_dl_new,
                  c_details, priority_prefix, st.session_state.username, json.dumps(initial_subs)), commit=True)
            st.toast("🚀 Đã đẩy tác vụ mới thành công!", icon="🎉")
            st.rerun()

# ====================================================================
# 2️⃣ CỘT PHẢI: CÁC CHẾ ĐỘ XEM
# ====================================================================
with col_panel_right:
    anchor_date = st.session_state.selected_date

    def is_task_active_on_day(t, d):
        try:
            st_d = t['start_date'] if isinstance(t['start_date'], datetime.date) else t['created_at'].date()
            dl_d = t['deadline_date'].date() if isinstance(t['deadline_date'], datetime.datetime) else t['deadline_date']
            return st_d <= d <= dl_d
        except: return False

    # ── KANBAN ──────────────────────────────────────────────────────
    if view_mode == "Kanban":
        st.markdown(f"#### ⚡ BOARD KANBAN NGÀY: `{anchor_date.strftime('%d/%m/%Y')}`")
        day_tasks = [t for t in all_tasks if is_task_active_on_day(t, anchor_date)]

        col_todo, col_doing, col_done = st.columns(3)
        with col_todo:
            st.markdown("<h5 style='color: #94a3b8; text-align:center;'>📌 CẦN LÀM</h5>", unsafe_allow_html=True)
            for idx, t in enumerate([x for x in day_tasks if x['status'] == 'To-do' and not x['is_closed']]):
                draw_task_item(t, "kb_todo", idx)
                if st.button("LÀM ➔", key=f"kb_do_mv_{t['id']}", use_container_width=True):
                    run_query("UPDATE team_tasks SET status='Doing' WHERE id=%s", (t['id'],), commit=True)
                    st.rerun()
        with col_doing:
            st.markdown("<h5 style='color: #f59e0b; text-align:center;'>🟡 ĐANG LÀM</h5>", unsafe_allow_html=True)
            for idx, t in enumerate([x for x in day_tasks if x['status'] == 'Doing' and not x['is_closed']]):
                draw_task_item(t, "kb_doing", idx)
                c_b1, c_b2 = st.columns(2)
                with c_b1:
                    if st.button("⬅ HẠ", key=f"kb_dw_mv_{t['id']}", use_container_width=True):
                        run_query("UPDATE team_tasks SET status='To-do' WHERE id=%s", (t['id'],), commit=True)
                        st.rerun()
                with c_b2:
                    if st.button("XONG ✅", key=f"kb_up_mv_{t['id']}", use_container_width=True):
                        run_query("UPDATE team_tasks SET status='Done' WHERE id=%s", (t['id'],), commit=True)
                        st.rerun()
        with col_done:
            st.markdown("<h5 style='color: #10b981; text-align:center;'>🟢 HOÀN THÀNH</h5>", unsafe_allow_html=True)
            for idx, t in enumerate([x for x in day_tasks if x['status'] == 'Done' or x['is_closed']]):
                draw_task_item(t, "kb_done", idx)

    # ── LIST VIEW ───────────────────────────────────────────────────
    elif view_mode == "List View":
        st.markdown(f"#### 📋 LIST VIEW NGÀY: `{anchor_date.strftime('%d/%m/%Y')}`")
        day_tasks = [t for t in all_tasks if is_task_active_on_day(t, anchor_date)]
        for idx, t in enumerate(day_tasks):
            draw_task_item(t, "list_view", idx)

    # ── TUẦN ────────────────────────────────────────────────────────
    elif view_mode == "Tuần":
        start_week = anchor_date - datetime.timedelta(days=anchor_date.weekday())
        days_in_week = [start_week + datetime.timedelta(days=i) for i in range(7)]
        day_names_vn = ["Thứ 2","Thứ 3","Thứ 4","Thứ 5","Thứ 6","Thứ 7","Chủ Nhật"]

        st.markdown(f"#### ⏱️ VIEW TUẦN: `{start_week.strftime('%d/%m')} ➔ {(start_week + datetime.timedelta(days=6)).strftime('%d/%m/%Y')}`")
        for i, target_day in enumerate(days_in_week):
            day_tasks = [t for t in all_tasks if is_task_active_on_day(t, target_day)]
            if not day_tasks: continue
            st.markdown(f'<div class="hlc-date-header"><span>⭐ {day_names_vn[i].upper()} - {target_day.strftime("%d/%m/%Y")}</span><span>{len(day_tasks)} TASK</span></div>', unsafe_allow_html=True)
            for idx, t in enumerate(day_tasks):
                draw_task_item(t, "week_view", idx + (i * 100))

    # ── THÁNG ───────────────────────────────────────────────────────
    elif view_mode == "Tháng":
        st.markdown(f"#### 🗓️ VIEW THÁNG: `{anchor_date.strftime('%m/%Y')}`")
        _, last_day_num = calendar.monthrange(anchor_date.year, anchor_date.month)
        first_of_month = datetime.date(anchor_date.year, anchor_date.month, 1)
        current_week_start = first_of_month - datetime.timedelta(days=first_of_month.weekday())
        week_count = 1

        while current_week_start <= datetime.date(anchor_date.year, anchor_date.month, last_day_num):
            current_week_end = current_week_start + datetime.timedelta(days=6)

            def is_task_in_week(t, ws, we):
                try:
                    t_start = t['start_date'] if isinstance(t['start_date'], datetime.date) else t['created_at'].date()
                    t_end = t['deadline_date'].date() if isinstance(t['deadline_date'], datetime.datetime) else t['deadline_date']
                    return not (t_end < ws or t_start > we)
                except: return False

            week_tasks = [t for t in all_tasks if is_task_in_week(t, current_week_start, current_week_end)]
            if week_tasks:
                st.markdown(f'<div class="hlc-date-header" style="background-color:#1e3a8a; border-color:#2563eb; color:#38bdf8;"><span>⚡ TUẦN {week_count} ({current_week_start.strftime("%d/%m")} ➔ {current_week_end.strftime("%d/%m")})</span><span>{len(week_tasks)} TASK</span></div>', unsafe_allow_html=True)
                for idx, t in enumerate(week_tasks):
                    draw_task_item(t, "month_view", idx + (week_count * 1000))

            current_week_start += datetime.timedelta(days=7)
            week_count += 1
