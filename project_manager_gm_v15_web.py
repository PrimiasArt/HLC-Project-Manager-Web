import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.parse
import datetime
import json
import calendar

# ====================================================================
# 💾 CẤU HÌNH TRANG VÀ CSS THEME TỐI SÂU CHUẨN V15
# ====================================================================
st.set_page_config(
    page_title="HLC Workstation Team Project Hub",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Ép cấu hình CSS cho Group Header giống bản gốc v15
st.markdown("""
<style>
    .hlc-date-header {
        background-color: #1a2234;
        border: 1px solid #2d3748;
        padding: 8px 16px;
        border-radius: 4px;
        margin-top: 14px;
        margin-bottom: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #38bdf8;
        font-size: 13px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Khởi tạo các trạng thái Session State toàn cục
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "username" not in st.session_state: st.session_state.username = None
if "role" not in st.session_state: st.session_state.role = None
if "uid" not in st.session_state: st.session_state.uid = None
if "selected_date" not in st.session_state: st.session_state.selected_date = datetime.date.today()
if "editing_task_id" not in st.session_state: st.session_state.editing_task_id = None
if "search_kw" not in st.session_state: st.session_state.search_kw = ""

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
# 🔒 XÁC THỰC TÀI KHOẢN
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
            else: st.error("❌ Sai thông tin xác thực!")
    st.stop()

# Đọc danh sách nhân sự từ Cloud
users_db = run_query("SELECT username, uid, role FROM hlc_users ORDER BY username ASC;") or []
all_usernames = [u['username'] for u in users_db]
user_uid_map = {u['username']: str(u['uid']) for u in users_db}
user_role_map = {u['username']: u['role'] for u in users_db}
assignable_users = all_usernames if st.session_state.role == "Admin" else [un for un in all_usernames if user_role_map.get(un) != "Admin"]

all_tasks = run_query("SELECT * FROM team_tasks ORDER BY is_closed ASC, deadline_date ASC;") or []
today_dt = datetime.datetime.now()

# ====================================================================
# ✏️ POP-UP EDIT CHI TIẾT & TIẾN ĐỘ CHECKLIST CON HÀNG LOẠT
# ====================================================================
if st.session_state.editing_task_id is not None:
    task = run_query("SELECT * FROM team_tasks WHERE id = %s;", (st.session_state.editing_task_id,), fetch="one")
    if task:
        st.markdown(f"### ✏️ Chi Tiết & Chỉnh Sửa Đầu Việc: `{task['task_name']}`")
        is_owner = st.session_state.role == "Admin" or st.session_state.username.lower() in [task['created_by'].lower(), task['assignee'].lower()]
        sub_tasks = safe_json_load(task['sub_tasks'])
        tagged_users = safe_json_load(task['tagged_users'])
        
        with st.form("edit_task_form_cloud"):
            edit_name = st.text_input("Tên đầu việc", value=task['task_name'], disabled=not is_owner or task['is_closed'])
            edit_assignee = st.selectbox("Nhân sự phụ trách", assignable_users, index=assignable_users.index(task['assignee']) if task['assignee'] in assignable_users else 0, disabled=not is_owner or task['is_closed'])
            
            col_sd, col_dl = st.columns(2)
            with col_sd:
                s_date = task['start_date'] if isinstance(task['start_date'], datetime.date) else datetime.date.today()
                edit_start = st.date_input("Ngày bắt đầu", value=s_date, disabled=not is_owner or task['is_closed'])
            with col_dl:
                d_loc = strip_tz(task['deadline_date']) or datetime.datetime.now()
                edit_dl_date = st.date_input("Ngày hạn chót", value=d_loc.date(), disabled=not is_owner or task['is_closed'])
                edit_dl_time = st.time_input("Giờ hạn chót", value=d_loc.time(), disabled=not is_owner or task['is_closed'])
                
            edit_details = st.text_area("Mô tả chi tiết", value=task['task_details'] or "", disabled=not is_owner or task['is_closed'])
            edit_docs = st.text_area("💬 Ghi chú báo cáo (Comment Note)", value=task['task_docs'] or "")
            edit_tags = st.multiselect("🏷️ Thành viên hỗ trợ", [u for u in assignable_users if u != edit_assignee], default=[t for t in tagged_users if t in assignable_users], disabled=not is_owner or task['is_closed'])
            
            st.write("📋 **Các bước thực hiện:**")
            updated_sub_tasks = []
            for idx, st_item in enumerate(sub_tasks):
                cb_val = st.checkbox(st_item.get('name', ''), value=st_item.get('done', False), key=f"sub_cb_{idx}")
                updated_sub_tasks.append({"name": st_item.get('name', ''), "done": cb_val})
                
            bulk_sub_input = st.text_area("➕ Thêm hàng loạt bước thực hiện (Mỗi bước 1 dòng):", height=80)
            
            col_save, col_close_t, col_cancel = st.columns([2, 2, 1])
            with col_save: save_btn = st.form_submit_button("💾 LƯU THAY ĐỔI LÊN CLOUD", use_container_width=True)
            with col_close_t: close_btn = st.form_submit_button("🔒 ĐÓNG TASK VĨNH VIỄN", use_container_width=True) if is_owner and not task['is_closed'] else False
            with col_cancel: cancel_btn = st.form_submit_button("Đóng cửa sổ", use_container_width=True)
            
            if save_btn:
                if bulk_sub_input.strip() and is_owner and not task['is_closed']:
                    for line in [l.strip() for l in bulk_sub_input.split('\n') if l.strip()]:
                        updated_sub_tasks.append({"name": line, "done": False})
                full_dl = datetime.datetime.combine(edit_dl_date, edit_dl_time)
                t_uids = [user_uid_map[u] for u in edit_tags if u in user_uid_map]
                if is_owner and not task['is_closed']:
                    run_query("""
                        UPDATE team_tasks SET task_name=%s, assignee=%s, assignee_uid=%s::uuid, start_date=%s, deadline_date=%s, task_details=%s, task_docs=%s, sub_tasks=%s::jsonb, tagged_users=%s::jsonb, tagged_uids=%s::jsonb
                        WHERE id=%s;
                    """, (edit_name, edit_assignee, user_uid_map.get(edit_assignee), edit_start, full_dl, edit_details, edit_docs, json.dumps(updated_sub_tasks), json.dumps(edit_tags), json.dumps(t_uids), task['id']), commit=True)
                else:
                    run_query("UPDATE team_tasks SET task_docs=%s WHERE id=%s;", (edit_docs, task['id']), commit=True)
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
# BANNER ĐẦU TRANG & BỘ LỌC TÌM KIẾM
# ====================================================================
col_hub, col_p2, col_p3 = st.columns([7, 2, 2])
with col_hub:
    st.markdown(f"<h2 style='color: #0ea5e9; margin:0;'>📊 HLC PRODUCTION HUB ➔ {st.session_state.username.upper()}</h2>", unsafe_allow_html=True)
with col_p2:
    if st.button("🔄 ĐỒNG BỘ CLOUD", use_container_width=True): st.rerun()
with col_p3:
    if st.button("🚪 ĐĂNG XUẤT", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

col_search, col_sort, col_view = st.columns([5, 2, 2])
with col_search:
    st.session_state.search_kw = st.text_input("🔍 Nhập tên Task hoặc nhân sự để tìm kiếm...", value=st.session_state.search_kw)
with col_sort:
    sort_mode = st.selectbox("Sắp xếp", ["Mặc định", "Theo nhân sự"])
with col_view:
    view_mode = st.selectbox("Chế độ xem khoảng thời gian", ["Kanban", "List View", "Tuần", "Tháng"], index=0)

if st.session_state.search_kw.strip():
    kw = st.session_state.search_kw.lower()
    all_tasks = [t for t in all_tasks if kw in str(t['task_name']).lower() or kw in str(t['assignee']).lower()]

if sort_mode == "Theo nhân sự":
    all_tasks = sorted(all_tasks, key=lambda x: (x['assignee'] or '').lower())

st.divider()

# ====================================================================
# HELPER RENDER CARD CÔNG VIỆC CHUẨN ĐỊNH DẠNG MÀU SẮC THEO YÊU CẦU
# ====================================================================
def render_native_task_card(t):
    # Xác định màu sắc (Dấu chấm và tiêu đề trạng thái) theo 4 màu yêu cầu
    dl_naive = strip_tz(t['deadline_date'])
    is_overdue = not t['is_closed'] and t['status'] != 'Done' and dl_naive and dl_naive < today_dt
    
    if t['is_closed']:
        status_dot, status_label, text_prefix, text_suffix = "⚪", "Chờ (Closed)", "~~", "~~"
    elif is_overdue:
        status_dot, status_label, text_prefix, text_suffix = "🔴", "Quá hạn", "", ""
    elif t['status'] == 'Done':
        status_dot, status_label, text_prefix, text_suffix = "🟢", "Hoàn thành", "", ""
    else: # Doing hoặc To-do chưa trễ
        status_dot = "🟡" if t['status'] == 'Doing' else "⚪"
        status_label = "Đang làm" if t['status'] == 'Doing' else "Cần làm"
        text_prefix, text_suffix = "", ""

    # Tính toán tiến độ Sub-tasks
    sub_list = safe_json_load(t['sub_tasks'])
    total_steps = len(sub_list)
    done_steps = sum(1 for item in sub_list if item.get('done', False))
    progress_val = (done_steps / total_steps) if total_steps > 0 else (1.0 if t['status'] == 'Done' else 0.0)

    with st.container(border=True):
        col_c1, col_c2, col_c3 = st.columns([6, 3, 2])
        with col_c1:
            st.markdown(f"{status_dot} {text_prefix}**{t['task_name']}**{text_suffix}")
            st.caption(f"👤 Phụ trách: {t['assignee']} | 🎬 Tạo bởi: {t['created_by']}")
            if total_steps > 0:
                st.caption(f"📋 Tiến độ bước: {done_steps}/{total_steps}")
        with col_c2:
            st.caption(f"⏱️ Hạn: {dl_naive.strftime('%d/%m %H:%M') if dl_naive else '—'}")
            st.progress(progress_val)
        with col_c3:
            if st.button("✏️ CHI TIẾT", key=f"btn_edit_{view_mode}_{t['id']}_{dl_naive.day if dl_naive else 0}", use_container_width=True):
                st.session_state.editing_task_id = t['id']
                st.rerun()

# ====================================================================
# LAYOUT HAI PHÂN KHÚC CHÍNH (TRÁI: CONTROL | PHẢI: BẢNG KHUNG HIỂN THỊ)
# ====================================================================
col_panel_left, col_panel_right = st.columns([3, 7])

with col_panel_left:
    st.markdown("#### 📅 LỊCH TRỰC QUAN")
    cal_curr = st.date_input("Chọn ngày mốc tiêu điểm", value=st.session_state.selected_date, label_visibility="collapsed")
    if cal_curr != st.session_state.selected_date:
        st.session_state.selected_date = cal_curr
        st.rerun()

    st.markdown("<br>📅 **Khởi tạo đầu việc mới:**", unsafe_allow_html=True)
    with st.form("add_task_form_main", clear_on_submit=True):
        c_name = st.text_input("Tên đầu việc (Task Name)")
        c_assignee = st.selectbox("Nhân sự phụ trách", assignable_users, index=assignable_users.index(st.session_state.username) if st.session_state.username in assignable_users else 0, disabled=(st.session_state.role == "Member"))
        c_start = st.date_input("📆 Ngày bắt đầu", value=st.session_state.selected_date)
        c_dl_date = st.date_input("Ngày hạn chót (Deadline)", value=st.session_state.selected_date + datetime.timedelta(days=1))
        c_dl_time = st.time_input("Giờ hạn chót", datetime.time(18, 00))
        c_details = st.text_area("Mô tả chi tiết công việc")
        c_bulk_sub = st.text_area("Nhập hàng loạt bước con (Mỗi việc 1 dòng)...", height=80)
        
        submit_new = st.form_submit_button("🚀 ĐẨY TASK LÊN ĐÁM MÂY HLC", use_container_width=True)
        if submit_new and c_name.strip():
            initial_subs = [{"name": line.strip(), "done": False} for line in c_bulk_sub.split('\n') if line.strip()]
            full_dl_new = datetime.datetime.combine(c_dl_date, c_dl_time)
            run_query("""
                INSERT INTO team_tasks (task_name, assignee, assignee_uid, start_date, deadline_date, status, task_details, task_docs, created_by, is_closed, sub_tasks, tagged_users)
                VALUES (%s, %s, %s::uuid, %s, %s, 'To-do', %s, '', %s, FALSE, %s::jsonb, '[]'::jsonb);
            """, (c_name, c_assignee, user_uid_map.get(c_assignee), c_start, full_dl_new, c_details, st.session_state.username, json.dumps(initial_subs)), commit=True)
            st.toast("🚀 Đã đẩy tác vụ mới thành công!", icon="🎉")
            st.rerun()

# --- 2️⃣ BÊN PHẢI: PHÂN TÁCH BIÊN ĐỘ HIỂN THỊ CỦA 4 CHẾ ĐỘ XEM ĐỘC LẬP ---
with col_panel_right:
    anchor_date = st.session_state.selected_date

    def is_task_active_on_day(t, d):
        try:
            st_d = t['start_date'] if isinstance(t['start_date'], datetime.date) else t['created_at'].date()
            dl_d = t['deadline_date'].date() if isinstance(t['deadline_date'], datetime.datetime) else t['deadline_date']
            return st_d <= d <= dl_d
        except: return False

    # 1️⃣ CHẾ ĐỘ XEM MẶC ĐỊNH: KANBAN 3 CỘT ĐỨNG THEO NGÀY CHỌN TRÊN LỊCH
    if view_mode == "Kanban":
        st.markdown(f"#### ⚡ BOARD KANBAN NGÀY: `{anchor_date.strftime('%d/%m/%Y')}`")
        day_tasks = [t for t in all_tasks if is_task_active_on_day(t, anchor_date)]
        
        col_todo, col_doing, col_done = st.columns(3)
        
        with col_todo:
            st.markdown("<h5 style='color: #94a3b8; text-align:center;'>📌 CẦN LÀM (TO-DO)</h5>", unsafe_allow_html=True)
            for t in [x for x in day_tasks if x['status'] == 'To-do' and not x['is_closed']]:
                render_native_task_card(t)
                if st.button("LÀM ➔", key=f"kb_mv_do_{t['id']}", use_container_width=True):
                    run_query("UPDATE team_tasks SET status='Doing' WHERE id=%s", (t['id'],), commit=True)
                    st.rerun()

        with col_doing:
            st.markdown("<h5 style='color: #f59e0b; text-align:center;'>🟡 ĐANG TIẾN HÀNH</h5>", unsafe_allow_html=True)
            for t in [x for x in day_tasks if x['status'] == 'Doing' and not x['is_closed']]:
                render_native_task_card(t)
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    if st.button("⬅ HẠ CẤP", key=f"kb_mv_bk_{t['id']}", use_container_width=True):
                        run_query("UPDATE team_tasks SET status='To-do' WHERE id=%s", (t['id'],), commit=True)
                        st.rerun()
                with col_m2:
                    if st.button("XONG ✅", key=f"kb_mv_dn_{t['id']}", use_container_width=True):
                        run_query("UPDATE team_tasks SET status='Done' WHERE id=%s", (t['id'],), commit=True)
                        st.rerun()

        with col_done:
            st.markdown("<h5 style='color: #10b981; text-align:center;'>🟢 HOÀN THÀNH / CLOSED</h5>", unsafe_allow_html=True)
            for t in [x for x in day_tasks if x['status'] == 'Done' or x['is_closed']]:
                render_native_task_card(t)

    # 2️⃣ CHẾ ĐỘ XEM: LIST VIEW HÀNG NGANG GỌN GÀNG CỦA NGÀY ĐANG CHỌN
    elif view_mode == "List View":
        st.markdown(f"#### 📋 LIST VIEW THEO NGÀY: `{anchor_date.strftime('%d/%m/%Y')}`")
        day_tasks = [t for t in all_tasks if is_task_active_on_day(t, anchor_date)]
        if not day_tasks:
            st.info("☘️ Không có công việc nào phát sinh trong ngày này.")
        else:
            for t in day_tasks:
                render_native_task_card(t)

    # 3️⃣ CHẾ ĐỘ XEM: TUẦN (GOM VIỆC CẢ TUẦN, CHIA THEO TỪNG GROUP NGÀY)
    elif view_mode == "Tuần":
        start_week = anchor_date - datetime.timedelta(days=anchor_date.weekday())
        days_in_week = [start_week + datetime.timedelta(days=i) for i in range(7)]
        day_names_vn = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]

        st.markdown(f"#### ⏱️ VIEW TUẦN: `{start_week.strftime('%d/%m')} ➔ {(start_week + datetime.timedelta(days=6)).strftime('%d/%m/%Y')}`")
        
        for i, target_day in enumerate(days_in_week):
            day_tasks = [t for t in all_tasks if is_task_active_on_day(t, target_day)]
            if not day_tasks: continue
            
            # Khung tiêu đề Ngày màu xám xanh xịn sò như app gốc
            st.markdown(f'<div class="hlc-date-header"><span>⭐ {day_names_vn[i].upper()} - {target_day.strftime("%d/%m/%Y")}</span><span>{len(day_tasks)} TASK</span></div>', unsafe_allow_html=True)
            for t in day_tasks:
                render_native_task_card(t)

    # 4️⃣ CHẾ ĐỘ XEM: THÁNG (GOM VIỆC CẢ THÁNG, CHIA THEO TỪNG GROUP TUẦN)
    elif view_mode == "Tháng":
        st.markdown(f"#### 🗓️ VIEW THÁNG TỔNG QUAN: `{anchor_date.strftime('%m/%Y')}`")
        
        _, last_day_num = calendar.monthrange(anchor_date.year, anchor_date.month)
        first_of_month = datetime.date(anchor_date.year, anchor_date.month, 1)
        
        # Tạo mốc phân hoạch tuần tự 4-5 tuần trong tháng
        current_week_start = first_of_month - datetime.timedelta(days=first_of_month.weekday())
        week_count = 1
        
        while current_week_start <= datetime.date(anchor_date.year, anchor_date.month, last_day_num):
            current_week_end = current_week_start + datetime.timedelta(days=6)
            
            # Lọc toàn bộ task giao thoa trúng tầm biên độ của Tuần này
            def is_task_in_week_range(t, ws, we):
                try:
                    t_start = t['start_date'] if isinstance(t['start_date'], datetime.date) else t['created_at'].date()
                    t_end = t['deadline_date'].date() if isinstance(t['deadline_date'], datetime.datetime) else t['deadline_date']
                    return not (t_end < ws or t_start > we)
                except: return False

            week_tasks = [t for t in all_tasks if is_task_in_week_range(t, current_week_start, current_week_end)]
            
            if week_tasks:
                # Group Header phân mốc theo TUẦN như yêu cầu mới
                st.markdown(f'<div class="hlc-date-header" style="background-color: #1e3a8a; border-color: #2563eb; color: #38bdf8;"><span>⚡ TUẦN {week_count} ({current_week_start.strftime("%d/%m")} ➔ {current_week_end.strftime("%d/%m")})</span><span>{len(week_tasks)} TASK ĐANG CHẠY</span></div>', unsafe_allow_html=True)
                for t in week_tasks:
                    render_native_task_card(t)
            
            current_week_start += datetime.timedelta(days=7)
            week_count += 1
