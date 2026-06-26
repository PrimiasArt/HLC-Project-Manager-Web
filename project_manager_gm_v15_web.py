import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.parse
import datetime
import calendar
import json
import pandas as pd
from io import BytesIO

# ====================================================================
# 💾 ĐẤT DIỄN CHO THEME & CẤU HÌNH TRANG SÂU
# ====================================================================
st.set_page_config(
    page_title="HLC Workstation Team Project Hub",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Khởi tạo các trạng thái Session State nếu chưa có
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "username" not in st.session_state: st.session_state.username = None
if "role" not in st.session_state: st.session_state.role = None
if "uid" not in st.session_state: st.session_state.uid = None
if "selected_date" not in st.session_state: st.session_state.selected_date = datetime.date.today()
if "current_page" not in st.session_state: st.session_state.current_page = "Dashboard"
if "editing_task_id" not in st.session_state: st.session_state.editing_task_id = None
if "search_kw" not in st.session_state: st.session_state.search_kw = ""

# ====================================================================
# 🔑 KẾT NỐI DATABASE SUPABASE Timestamptz-Safe
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
        st.error(f"💥 Lỗi Database: {e}")
        return None

# Helper ép kiểu JSON an toàn
def safe_json_load(raw_data):
    if not raw_data: return []
    if isinstance(raw_data, list): return raw_data
    if isinstance(raw_data, str):
        try: return json.loads(raw_data)
        except: return []
    return []

# Helper dọn dẹp múi giờ hiển thị hiển thị giống v15
def strip_tz(dt):
    if dt is None: return None
    if isinstance(dt, datetime.datetime):
        return dt.replace(tzinfo=None)
    return dt

# ====================================================================
# 🔒 MÀN HÌNH ĐĂNG NHẬP (Xác thực Cloud)
# ====================================================================
if not st.session_state.authenticated:
    st.markdown("<br><br><h2 style='text-align: center; color: #38bdf8;'>🔒 HLC SYSTEM CLOUD AUTHENTICATION</h2>", unsafe_allow_html=True)
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Tên đăng nhập (Username)").strip()
        password = st.text_input("Mật khẩu (Password)", type="password").strip()
        submit = st.form_submit_button("ĐĂNG NHẬP HỆ THỐNG", use_container_width=True)
        
        if submit:
            user = run_query(
                "SELECT username, role, uid FROM hlc_users WHERE username = %s AND password = %s;",
                (username, password), fetch="one"
            )
            if user:
                st.session_state.authenticated = True
                st.session_state.username = user['username']
                st.session_state.role = user['role']
                st.session_state.uid = str(user['uid'])
                st.rerun()
            else:
                st.error("❌ Sai tài khoản hoặc mật khẩu hệ thống!")
    st.stop()

# Load danh sách user phục vụ ứng dụng
users_db = run_query("SELECT username, uid, role FROM hlc_users ORDER BY username ASC;")
all_usernames = [u['username'] for u in users_db] if users_db else []
user_uid_map = {u['username']: str(u['uid']) for u in users_db} if users_db else {}
user_role_map = {u['username']: u['role'] for u in users_db} if users_db else {}

# Phân quyền danh sách phân bổ (Admin ẩn với Member/Manager trong form gán)
assignable_users = all_usernames if st.session_state.role == "Admin" else [un for un in all_usernames if user_role_map.get(un) != "Admin"]

# ====================================================================
# 📝 POP-UP CHỈNH SỬA CHI TIẾT ĐẦU VIỆC (TASK DETAIL / EDIT DIALOG)
# ====================================================================
if st.session_state.editing_task_id is not None:
    task = run_query("SELECT * FROM team_tasks WHERE id = %s;", (st.session_state.editing_task_id,), fetch="one")
    if task:
        st.markdown(f"### ✏️ Chi Tiết & Chỉnh Sửa Đầu Việc: `{task['task_name']}`")
        
        # Phân quyền chỉnh sửa chặt chẽ giống v15
        creator_role = user_role_map.get(task['created_by'], "Member")
        assignee_role = user_role_map.get(task['assignee'], "Member")
        
        if st.session_state.role == "Admin": is_owner = True
        elif st.session_state.role == "Manager": is_owner = (creator_role != "Admin" and assignee_role != "Admin")
        else: is_owner = (st.session_state.username.lower() in [task['created_by'].lower(), task['assignee'].lower()])
        
        sub_tasks = safe_json_load(task['sub_tasks'])
        tagged_users = safe_json_load(task['tagged_users'])
        
        if not is_owner or task['is_closed']:
            st.warning("👁️ Bạn đang ở chế độ xem hoặc Task đã đóng. Không thể sửa cấu hình chính.")
            
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
            
            edit_details = st.text_area("Mô tả chi tiết công việc", value=task['task_details'] or "", disabled=not is_owner or task['is_closed'])
            edit_docs = st.text_area("💬 Tài liệu Docs & Ghi chú (Comment Note)", value=task['task_docs'] or "")
            
            # Quản lý thẻ Tag người hỗ trợ
            edit_tags = st.multiselect("🏷️ Thành viên hỗ trợ (Tagged Users)", [u for u in assignable_users if u != edit_assignee], default=[t for t in tagged_users if t in assignable_users], disabled=not is_owner or task['is_closed'])
            
            st.write("📋 **Các bước thực hiện (Sub-tasks Checklist)**")
            updated_sub_tasks = []
            for idx, st_item in enumerate(sub_tasks):
                cb_val = st.checkbox(st_item.get('name', ''), value=st_item.get('done', False), key=f"sub_cb_{idx}")
                updated_sub_tasks.append({"name": st_item.get('name', ''), "done": cb_val})
                
            new_sub_name = st.text_input("➕ Thêm bước thực hiện mới (Nhập tên rồi bấm Lưu thay đổi)", key="new_sub_input", disabled=not is_owner or task['is_closed'])
            if new_sub_name.strip() and is_owner and not task['is_closed']:
                updated_sub_tasks.append({"name": new_sub_name.strip(), "done": False})
            
            col_save, col_close_t, col_cancel = st.columns([2, 2, 1])
            with col_save:
                save_btn = st.form_submit_button("💾 LƯU THAY ĐỔI LÊN CLOUD", use_container_width=True)
            with col_close_t:
                close_btn = st.form_submit_button("🔒 ĐÓNG VĨNH VIỄN TASK", use_container_width=True) if is_owner and not task['is_closed'] else False
            with col_cancel:
                cancel_btn = st.form_submit_button("Đóng", use_container_width=True)
                
            if save_btn:
                full_dl = datetime.datetime.combine(edit_dl_date, edit_dl_time)
                t_uids = [user_uid_map[u] for u in edit_tags if u in user_uid_map]
                if is_owner and not task['is_closed']:
                    run_query("""
                        UPDATE team_tasks 
                        SET task_name=%s, assignee=%s, assignee_uid=%s::uuid, start_date=%s, deadline_date=%s, task_details=%s, task_docs=%s, sub_tasks=%s::jsonb, tagged_users=%s::jsonb, tagged_uids=%s::jsonb
                        WHERE id=%s;
                    """, (edit_name, edit_assignee, user_uid_map.get(edit_assignee), edit_start, full_dl, edit_details, edit_docs, json.dumps(updated_sub_tasks), json.dumps(edit_tags), json.dumps(t_uids), task['id']), commit=True)
                else:
                    # Non-owner hoặc task đã đóng chỉ được update comment notes
                    run_query("UPDATE team_tasks SET task_docs=%s WHERE id=%s;", (edit_docs, task['id']), commit=True)
                st.success("Đã cập nhật dữ liệu thành công!")
                st.session_state.editing_task_id = None
                st.rerun()
                
            if close_btn:
                run_query("UPDATE team_tasks SET is_closed=TRUE, status='Done' WHERE id=%s;", (task['id'],), commit=True)
                st.success("Đã đóng hoàn toàn Task này!")
                st.session_state.editing_task_id = None
                st.rerun()
                
            if cancel_btn:
                st.session_state.editing_task_id = None
                st.rerun()
    st.stop()

# ====================================================================
# 📊 ĐIỀU HƯỚNG DASHBOARD CHÍNH
# ====================================================================
# --- TOP BANNER CONTROL ---
col_hub, col_p1, col_p2, col_p3 = st.columns([5, 2, 2, 2])
with col_hub:
    st.markdown(f"<h2 style='color: #0ea5e9; margin:0;'>📊 HLC PRODUCTION HUB ➔ {st.session_state.username.upper()} ({st.session_state.role.upper()})</h2>", unsafe_allow_html=True)
with col_p1:
    if st.session_state.role in ("Admin", "Manager"):
        if st.button("👥 QUẢN LÝ NHÂN SỰ", use_container_width=True):
            st.session_state.current_page = "HR"
            st.rerun()
with col_p2:
    if st.button("🔄 ĐỒNG BỘ CLOUD", use_container_width=True): st.rerun()
with col_p3:
    if st.button("🚪 ĐĂNG XUẤT", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# --- SEARCH & FILTER BAR ---
st.markdown("<br>", unsafe_allow_html=True)
col_search, col_sort, col_view = st.columns([5, 2, 2])
with col_search:
    st.session_state.search_kw = st.text_input("🔍 Nhập tên Task hoặc nhân sự để tìm kiếm...", value=st.session_state.search_kw)
with col_sort:
    sort_mode = st.selectbox("Sắp xếp", ["Mặc định", "Theo nhân sự", "Deadline gần nhất", "Deadline xa nhất", "Mới nhất", "Cũ nhất"])
with col_view:
    view_mode = st.selectbox("Chế độ xem", ["Kanban", "List", "Tuần", "Tháng"])

st.divider()

# Pull data thô từ Cloud phục vụ lọc
all_tasks = run_query("SELECT * FROM team_tasks ORDER BY is_closed ASC, id DESC;") or []

# Logic sắp xếp
if sort_mode == "Theo nhân sự": all_tasks = sorted(all_tasks, key=lambda x: (x['assignee'] or '').lower())
elif sort_mode == "Deadline gần nhất": all_tasks = sorted(all_tasks, key=lambda x: x['deadline_date'] or datetime.datetime.max)
elif sort_mode == "Deadline xa nhất": all_tasks = sorted(all_tasks, key=lambda x: x['deadline_date'] or datetime.datetime.min, reverse=True)
elif sort_mode == "Mới nhất": all_tasks = sorted(all_tasks, key=lambda x: x['id'], reverse=True)
elif sort_mode == "Cũ nhất": all_tasks = sorted(all_tasks, key=lambda x: x['id'])

# Từ khóa tìm kiếm
if st.session_state.search_kw.strip():
    kw = st.session_state.search_kw.lower()
    all_tasks = [t for t in all_tasks if kw in str(t['task_name']).lower() or kw in str(t['assignee']).lower()]

# ====================================================================
# LAYOUT CHIA ĐÔI MÀN HÌNH CHÍNH (TRÁI: CONTROL & CALENDAR | PHẢI: BOARD)
# ====================================================================
col_panel_left, col_panel_right = st.columns([1, 3])

# --- KHỐI BÊN TRÁI: MINI CALENDAR & KHỞI TẠO ĐẦU VIỆC MỚI ---
with col_panel_left:
    # 📅 Mini Calendar hiển thị tĩnh mô phỏng v15
    with st.container(border=True):
        st.markdown(f"<div style='text-align:center; font-weight:bold; color:#e5e7eb;'>📅 Tháng {st.session_state.selected_date.month} / {st.session_state.selected_date.year}</div>", unsafe_allow_html=True)
        cal_curr = st.date_input("Chọn ngày xem tiêu điểm", value=st.session_state.selected_date, label_visibility="collapsed")
        if cal_curr != st.session_state.selected_date:
            st.session_state.selected_date = cal_curr
            st.rerun()

    # Khởi tạo đầu việc mới 
    st.markdown("### ➕ KHỞI TẠO ĐẦU VIỆC MỚI")
    with st.form("add_task_form_main", clear_on_submit=True):
        c_name = st.text_input("Tên đầu việc (Task Name)")
        c_assignee = st.selectbox("Nhân sự phụ trách", assignable_users, index=assignable_users.index(st.session_state.username) if st.session_state.username in assignable_users else 0, disabled=(st.session_state.role == "Member"))
        
        c_start = st.date_input("📆 Ngày bắt đầu", datetime.date.today())
        c_dl_date = st.date_input("Ngày hạn chót (Deadline)", datetime.date.today() + datetime.timedelta(days=3))
        c_dl_time = st.time_input("Giờ hạn chót", datetime.time(23, 59))
        
        c_details = st.text_area("Mô tả chi tiết công việc")
        c_docs = st.text_area("Tài liệu Docs / Comment note")
        
        submit_new = st.form_submit_button("🚀 ĐẨY TASK LÊN ĐÁM MÂY", use_container_width=True)
        if submit_new:
            if not c_name.strip():
                st.error("Không được để trống tên việc!")
            else:
                full_dl_new = datetime.datetime.combine(c_dl_date, c_dl_time)
                run_query("""
                    INSERT INTO team_tasks (task_name, assignee, assignee_uid, start_date, deadline_date, status, task_details, task_docs, created_by, is_closed, sub_tasks, tagged_users)
                    VALUES (%s, %s, %s::uuid, %s, %s, 'To-do', %s, %s, %s, FALSE, '[]'::jsonb, '[]'::jsonb);
                """, (c_name, c_assignee, user_uid_map.get(c_assignee), c_start, full_dl_new, c_details, c_docs, st.session_state.username), commit=True)
                st.success("Tạo việc thành công!")
                st.rerun()

# --- KHỐI BÊN PHẢI: HIỂN THỊ DỮ LIỆU CÁC CHẾ ĐỘ XEM ---
with col_panel_right:
    st.markdown(f"##### 📅 Tiêu điểm ngày đang xem: `{st.session_state.selected_date.strftime('%d/%m/%Y')}`")
    
    # Lọc danh sách công việc chạm hoặc hiển thị trong ngày được chọn trên Calendar
    def is_touching_day(t, d):
        try:
            st_d = t['start_date'] if isinstance(t['start_date'], datetime.date) else t['created_at'].date()
            dl_d = t['deadline_date'].date() if isinstance(t['deadline_date'], datetime.datetime) else t['deadline_date']
            return st_d <= d <= dl_d
        except: return False
        
    day_tasks = [t for t in all_tasks if is_touching_day(t, st.session_state.selected_date)]

    # 1️⃣ CHẾ ĐỘ XEM KANBAN
    if view_mode == "Kanban":
        col_todo, col_doing, col_done = st.columns(3)
        
        with col_todo:
            st.markdown("<h4 style='color: #94a3b8;'>📌 CẦN LÀM (TO-DO)</h4>", unsafe_allow_html=True)
            for t in [x for x in day_tasks if x['status'] == 'To-do' and not x['is_closed']]:
                with st.container(border=True):
                    st.markdown(f"**{t['task_name']}**")
                    st.caption(f"👤 Phụ trách: {t['assignee']} | Hạn: {strip_tz(t['deadline_date'])}")
                    col_k1, col_k2 = st.columns(2)
                    with col_k1:
                        if st.button("✏️ CHI TIẾT", key=f"kb_ed_{t['id']}", use_container_width=True):
                            st.session_state.editing_task_id = t['id']
                            st.rerun()
                    with col_k2:
                        if st.button("TIẾN ĐỘ ➔", key=f"kb_mv_{t['id']}", use_container_width=True):
                            run_query("UPDATE team_tasks SET status='Doing' WHERE id=%s", (t['id'],), commit=True)
                            st.rerun()
                            
        with col_doing:
            st.markdown("<h4 style='color: #f59e0b;'>⚡ ĐANG TIẾN HÀNH</h4>", unsafe_allow_html=True)
            for t in [x for x in day_tasks if x['status'] == 'Doing' and not x['is_closed']]:
                with st.container(border=True):
                    st.markdown(f"**{t['task_name']}**")
                    st.caption(f"👤 Phụ trách: {t['assignee']} | Hạn: {strip_tz(t['deadline_date'])}")
                    st.button("✏️ CHI TIẾT & CHECKLIST", key=f"kb_ed_{t['id']}", on_click=lambda tid=t['id']: setattr(st.session_state, 'editing_task_id', tid))
                    col_kd1, col_kd2 = st.columns(2)
                    with col_kd1:
                        if st.button("⬅ HẠ CẤP", key=f"kb_dn_{t['id']}", use_container_width=True):
                            run_query("UPDATE team_tasks SET status='To-do' WHERE id=%s", (t['id'],), commit=True)
                            st.rerun()
                    with col_kd2:
                        if st.button("XONG ✅", key=f"kb_up_{t['id']}", use_container_width=True):
                            run_query("UPDATE team_tasks SET status='Done' WHERE id=%s", (t['id'],), commit=True)
                            st.rerun()

        with col_done:
            st.markdown("<h4 style='color: #10b981;'>✅ HOÀN THÀNH / CLOSED</h4>", unsafe_allow_html=True)
            for t in [x for x in day_tasks if x['status'] == 'Done' or x['is_closed']]:
                with st.container(border=True):
                    title_prefix = "🔒 [CLOSED] " if t['is_closed'] else "✅ "
                    st.markdown(f"**{title_prefix}{t['task_name']}**")
                    st.caption(f"👤 {t['assignee']} | Trạng thái: {t['status']}")
                    if st.button("✏️ XEM CHI TIẾT", key=f"kb_ed_{t['id']}", use_container_width=True):
                        st.session_state.editing_task_id = t['id']
                        st.rerun()

    # 2️⃣ CHẾ ĐỘ XEM LIST VIEW (Bản sao hoàn hảo theo thanh hàng ngang của hình anh chụp)
    elif view_mode == "List":
        for t in day_tasks:
            with st.container(border=True):
                col_l_status, col_l_name, col_l_user, col_l_dl, col_l_action = st.columns([1, 4, 2, 2, 2])
                with col_l_status:
                    if t['is_closed']: st.markdown("🔴 `CLOSED`")
                    elif t['status'] == 'Done': st.markdown("🟢 `DONE`")
                    elif t['status'] == 'Doing': st.markdown("🟡 `DOING`")
                    else: st.markdown("⚪ `TO-DO`")
                with col_l_name:
                    st.markdown(f"**{t['task_name']}**")
                with col_l_user:
                    st.caption(f"👤 {t['assignee']}")
                with col_l_dl:
                    st.caption(f"⏱️ {strip_tz(t['deadline_date']).strftime('%d/%m %H:%M') if t['deadline_date'] else '—'}")
                with col_l_action:
                    if st.button("MỞ XEM CHI TIẾT", key=f"lst_ed_{t['id']}", use_container_width=True):
                        st.session_state.editing_task_id = t['id']
                        st.rerun()

    # 3️⃣ CHẾ ĐỘ XEM TUẦN (WEEK VIEW)
    elif view_mode == "Tuần":
        dt_anchor = st.session_state.selected_date
        start_week = dt_anchor - datetime.timedelta(days=dt_anchor.weekday())
        
        st.write(f"📅 **Tuần từ {start_week.strftime('%d/%m')} đến {(start_week + datetime.timedelta(days=6)).strftime('%d/%m/%Y')}**")
        
        for i in range(7):
            loop_day = start_week + datetime.timedelta(days=i)
            day_tasks_loop = [t for t in all_tasks if is_touching_day(t, loop_day)]
            
            with st.expander(f"📆 {loop_day.strftime('%A - %d/%m/%Y')} ({len(day_tasks_loop)} việc)"):
                for t in day_tasks_loop:
                    st.write(f"• **{t['task_name']}** ({t['assignee']}) - *{t['status']}*")

    # 4️⃣ CHẾ ĐỘ XEM THÁNG (MONTH VIEW GRIDS)
    elif view_mode == "Tháng":
        st.info("💡 Tính năng xem ô lưới tổng quan lịch tháng. Chọn ngày trên lịch trái để hiển thị danh sách chi tiết các đầu việc tương quan.")
        st.dataframe(pd.DataFrame(all_tasks)[['id', 'task_name', 'assignee', 'status', 'deadline_date']], use_container_width=True)

# ====================================================================
# 👥 KHU VỰC QUẢN LÝ TÀI KHOẢN NHÂN SỰ
# ====================================================================
if st.session_state.current_page == "HR":
    st.divider()
    st.title("👥 QUẢN TRỊ & THÔNG TIN NHÂN SỰ")
    if st.button("◀ QUAY LẠI BẢNG ĐIỀU KHIỂN HUB"):
        st.session_state.current_page = "Dashboard"
        st.rerun()
        
    st.write("### Danh sách tài khoản hệ thống")
    all_users_raw = run_query("SELECT id, username, role, uid FROM hlc_users ORDER BY id ASC;")
    if all_users_raw:
        st.dataframe(pd.DataFrame(all_users_raw), use_container_width=True)
