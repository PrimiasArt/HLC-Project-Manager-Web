import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.parse
import datetime
import json
import pandas as pd

# ====================================================================
# 💾 CẤU HÌNH TRANG VÀ CSS CHIA MÀU TASK (GIỐNG BẢN GỐC V15)
# ====================================================================
st.set_page_config(
    page_title="HLC Workstation Team Project Hub",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Nhúng CSS tùy biến để ép màu và bo góc thẻ Task giống hệt CustomTkinter
st.markdown("""
<style>
    .task-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #ccc; background-color: #1e293b; }
    .task-overdue { border-left-color: #ef4444 !important; background-color: #2d1a1a !important; } /* Đỏ: Trễ hạn / Khẩn */
    .task-doing { border-left-color: #f59e0b !important; background-color: #2d2414 !important; }   /* Vàng: Đang làm */
    .task-done { border-left-color: #10b981 !important; background-color: #142d20 !important; }    /* Xanh: Hoàn thành */
    .task-title { font-weight: bold; font-size: 16px; color: #f8fafc; }
</style>
""", unsafe_allow_html=True)

# Khởi tạo các trạng thái Session State toàn cục
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "username" not in st.session_state: st.session_state.username = None
if "role" not in st.session_state: st.session_state.role = None
if "uid" not in st.session_state: st.session_state.uid = None
if "selected_date" not in st.session_state: st.session_state.selected_date = datetime.date.today()
if "current_page" not in st.session_state: st.session_state.current_page = "Dashboard"
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
# 🔒 MÀN HÌNH ĐĂNG NHẬP
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
                st.toast(f"🎉 Chào mừng {user['username']} quay trở lại hệ thống!", icon="🚀")
                st.rerun()
            else:
                st.error("❌ Sai tài khoản hoặc mật khẩu hệ thống!")
    st.stop()

# Đọc danh sách nhân sự từ Cloud
users_db = run_query("SELECT username, uid, role FROM hlc_users ORDER BY username ASC;") or []
all_usernames = [u['username'] for u in users_db]
user_uid_map = {u['username']: str(u['uid']) for u in users_db}
user_role_map = {u['username']: u['role'] for u in users_db}
assignable_users = all_usernames if st.session_state.role == "Admin" else [un for un in all_usernames if user_role_map.get(un) != "Admin"]

# Pull toàn bộ danh sách task phục vụ hiển thị lịch và kiểm tra cảnh báo trễ hạn
all_tasks = run_query("SELECT * FROM team_tasks ORDER BY is_closed ASC, deadline_date ASC;") or []

# 🔔 TÍNH NĂNG THÔNG BÁO WEB CHẠY TỰ ĐỘNG (Xử lý việc cảnh báo trễ hạn trực quan)
today_dt = datetime.datetime.now()
overdue_count = 0
for t in all_tasks:
    if not t['is_closed'] and t['status'] != 'Done' and t['deadline_date']:
        dl_naive = strip_tz(t['deadline_date'])
        if dl_naive < today_dt:
            overdue_count += 1

if overdue_count > 0:
    st.toast(f"⚠️ CẢNH BÁO: Hiện có {overdue_count} đầu việc trên hệ thống đã QUÁ HẠN CHÓT!", icon="🚨")

# ====================================================================
# ✏️ POP-UP DIALOG CHỈNH SỬA VÀ THÊM CHECKLIST HÀNG LOẠT
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
            
            edit_details = st.text_area("Mô tả chi tiết công việc", value=task['task_details'] or "", disabled=not is_owner or task['is_closed'])
            edit_docs = st.text_area("💬 Tài liệu Docs & Ghi chú (Comment Note)", value=task['task_docs'] or "")
            edit_tags = st.multiselect("🏷️ Thành viên hỗ trợ (Tagged Users)", [u for u in assignable_users if u != edit_assignee], default=[t for t in tagged_users if t in assignable_users], disabled=not is_owner or task['is_closed'])
            
            # --- KHU VỰC SUB-TASKS: HIỂN THỊ VÀ THÊM HÀNG LOẠT ---
            st.write("📋 **Các bước thực hiện hiện tại:**")
            updated_sub_tasks = []
            for idx, st_item in enumerate(sub_tasks):
                cb_val = st.checkbox(st_item.get('name', ''), value=st_item.get('done', False), key=f"sub_cb_{idx}")
                updated_sub_tasks.append({"name": st_item.get('name', ''), "done": cb_val})
            
            st.write("➕ **Thêm hàng loạt bước thực hiện con mới (Mỗi bước viết trên 1 dòng):**")
            bulk_sub_input = st.text_area("Ví dụ:\nBước 1: Khảo sát hiện trạng\nBước 2: Lập hồ sơ thiết kế cơ sở", height=100, placeholder="Nhập danh sách bước tại đây...")
            
            col_save, col_close_t, col_cancel = st.columns([2, 2, 1])
            with col_save: save_btn = st.form_submit_button("💾 LƯU THAY ĐỔI LÊN CLOUD", use_container_width=True)
            with col_close_t: close_btn = st.form_submit_button("🔒 ĐÓNG VĨNH VIỄN TASK", use_container_width=True) if is_owner and not task['is_closed'] else False
            with col_cancel: cancel_btn = st.form_submit_button("Đóng", use_container_width=True)
                
            if save_btn:
                # Xử lý bóc tách text gõ hàng loạt thành mảng JSON dữ liệu
                if bulk_sub_input.strip() and is_owner and not task['is_closed']:
                    lines = [line.strip() for line in bulk_sub_input.split('\n') if line.strip()]
                    for line in lines:
                        updated_sub_tasks.append({"name": line, "done": False})
                
                full_dl = datetime.datetime.combine(edit_dl_date, edit_dl_time)
                t_uids = [user_uid_map[u] for u in edit_tags if u in user_uid_map]
                
                if is_owner and not task['is_closed']:
                    run_query("""
                        UPDATE team_tasks 
                        SET task_name=%s, assignee=%s, assignee_uid=%s::uuid, start_date=%s, deadline_date=%s, task_details=%s, task_docs=%s, sub_tasks=%s::jsonb, tagged_users=%s::jsonb, tagged_uids=%s::jsonb
                        WHERE id=%s;
                    """, (edit_name, edit_assignee, user_uid_map.get(edit_assignee), edit_start, full_dl, edit_details, edit_docs, json.dumps(updated_sub_tasks), json.dumps(edit_tags), json.dumps(t_uids), task['id']), commit=True)
                else:
                    run_query("UPDATE team_tasks SET task_docs=%s WHERE id=%s;", (edit_docs, task['id']), commit=True)
                
                st.toast("✅ Đã cập nhật toàn bộ thông tin công việc lên Cloud thành công!", icon="⚡")
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
# INTERFACE BANNER CHÍNH & SEARCH BỘ LỌC
# ====================================================================
col_hub, col_p1, col_p2, col_p3 = st.columns([5, 2, 2, 2])
with col_hub:
    st.markdown(f"<h2 style='color: #0ea5e9; margin:0;'>📊 HLC PRODUCTION HUB ➔ {st.session_state.username.upper()}</h2>", unsafe_allow_html=True)
with col_p1:
    if st.session_state.role in ("Admin", "Manager") and st.button("👥 QUẢN LÝ NHÂN SỰ", use_container_width=True):
        st.session_state.current_page = "HR" if st.session_state.current_page == "Dashboard" else "Dashboard"
        st.rerun()
with col_p2:
    if st.button("🔄 ĐỒNG BỘ CLOUD", use_container_width=True): st.rerun()
with col_p3:
    if st.button("🚪 ĐĂNG XUẤT", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# Bộ lọc tìm kiếm nhanh đầu trang
col_search, col_sort = st.columns([6, 4])
with col_search:
    st.session_state.search_kw = st.text_input("🔍 Nhập tên việc hoặc tên nhân sự để lọc danh sách...", value=st.session_state.search_kw)
with col_sort:
    sort_mode = st.selectbox("Sắp xếp thứ tự danh sách", ["Mặc định", "Deadline gần nhất", "Theo nhân sự phụ trách"])

if st.session_state.search_kw.strip():
    kw = st.session_state.search_kw.lower()
    all_tasks = [t for t in all_tasks if kw in str(t['task_name']).lower() or kw in str(t['assignee']).lower()]

if sort_mode == "Deadline gần nhất":
    all_tasks = sorted(all_tasks, key=lambda x: x['deadline_date'] or datetime.datetime.max)
elif sort_mode == "Theo nhân sự phụ trách":
    all_tasks = sorted(all_tasks, key=lambda x: (x['assignee'] or '').lower())

st.divider()

# ====================================================================
# LAYOUT CHIA ĐÔI MÀN HÌNH CHÍNH (TRÁI: LỊCH THÁNG & TẠO VIỆC | PHẢI: CHI TIẾT)
# ====================================================================
col_panel_left, col_panel_right = st.columns([4, 6])

# --- 1️⃣ BÊN TRÁI: BẢNG LỊCH HIỂN THỊ FULL TRỰC QUAN & FORM KHỞI TẠO ---
with col_panel_left:
    st.markdown("#### 📅 BẢNG LỊCH TIÊU ĐIỂM THÁNG")
    
    # Sử dụng widget date_input ở chế độ tĩnh hiển thị toàn bộ ngày trực quan trên màn hình luôn
    cal_curr = st.date_input("Chọn ngày tiêu điểm để xem và gán việc bên dưới", value=st.session_state.selected_date, label_visibility="visible")
    if cal_curr != st.session_state.selected_date:
        st.session_state.selected_date = cal_curr
        st.rerun()

    st.markdown("<br>📅 **Khởi tạo đầu việc mới trực tiếp cho ngày đang xem:**", unsafe_allow_html=True)
    with st.form("add_task_form_main", clear_on_submit=True):
        c_name = st.text_input("Tên đầu việc (Task Name)")
        c_assignee = st.selectbox("Nhân sự phụ trách", assignable_users, index=assignable_users.index(st.session_state.username) if st.session_state.username in assignable_users else 0, disabled=(st.session_state.role == "Member"))
        
        c_start = st.date_input("📆 Ngày bắt đầu", value=st.session_state.selected_date)
        c_dl_date = st.date_input("Ngày hạn chót (Deadline)", value=st.session_state.selected_date + datetime.timedelta(days=1))
        c_dl_time = st.time_input("Giờ hạn chót", datetime.time(18, 00))
        
        c_details = st.text_area("Mô tả chi tiết công việc")
        
        st.write("📋 **Nhập hàng loạt bước thực hiện con ban đầu (Mỗi bước 1 dòng):**")
        c_bulk_sub = st.text_area("Danh sách bước con...", key="create_bulk_sub", height=80)
        
        submit_new = st.form_submit_button("🚀 ĐẨY TASK LÊN ĐÁM MÂY HLC", use_container_width=True)
        if submit_new:
            if not c_name.strip():
                st.error("Không được bỏ trống tên đầu việc!")
            else:
                initial_subs = []
                if c_bulk_sub.strip():
                    initial_subs = [{"name": line.strip(), "done": False} for line in c_bulk_sub.split('\n') if line.strip()]
                    
                full_dl_new = datetime.datetime.combine(c_dl_date, c_dl_time)
                run_query("""
                    INSERT INTO team_tasks (task_name, assignee, assignee_uid, start_date, deadline_date, status, task_details, task_docs, created_by, is_closed, sub_tasks, tagged_users)
                    VALUES (%s, %s, %s::uuid, %s, %s, 'To-do', %s, '', %s, FALSE, %s::jsonb, '[]'::jsonb);
                """, (c_name, c_assignee, user_uid_map.get(c_assignee), c_start, full_dl_new, c_details, st.session_state.username, json.dumps(initial_subs)), commit=True)
                
                st.toast("🚀 Đã đẩy tác vụ mới lên Cloud thành công!", icon="🎉")
                st.rerun()

# --- 2️⃣ BÊN PHẢI: KANBAN BOARD CHIA THEO TIÊU CHUẨN 3 LOẠI MÀU SẮC ---
with col_panel_right:
    st.markdown(f"#### ⚡ DANH SÁCH VIỆC CHẠM NGÀY: `{st.session_state.selected_date.strftime('%d/%m/%Y')}`")
    
    # Hàm lọc task giao thoa trúng ngày đang chọn trên lịch giống v15
    def is_touching_day(t, d):
        try:
            st_d = t['start_date'] if isinstance(t['start_date'], datetime.date) else t['created_at'].date()
            dl_d = t['deadline_date'].date() if isinstance(t['deadline_date'], datetime.datetime) else t['deadline_date']
            return st_d <= d <= dl_d
        except: return False
        
    day_tasks = [t for t in all_tasks if is_touching_day(t, st.session_state.selected_date)]

    if not day_tasks:
        st.info("☘️ Tuyệt vời! Ngày này hiện chưa có đầu việc nào được phân bổ hoặc cần xử lý.")
    else:
        col_todo, col_doing, col_done = st.columns(3)
        
        with col_todo:
            st.markdown("<h5 style='color: #94a3b8; text-align:center;'>📌 CẦN LÀM</h5>", unsafe_allow_html=True)
            for t in [x for x in day_tasks if x['status'] == 'To-do' and not x['is_closed']]:
                # --- PHÂN CHIA LOẠI MÀU SẮC DỰA VÀO DEADLINE ---
                dl_naive = strip_tz(t['deadline_date'])
                card_class = "task-card task-overdue" if (dl_naive and dl_naive < today_dt) else "task-card"
                
                st.markdown(f"""
                <div class="{card_class}">
                    <div class="task-title">{t['task_name']}</div>
                    <span style='font-size:12px; color:#94a3b8;'>👤 {t['assignee']}</span><br>
                    <span style='font-size:12px; color:#f87171;'>⏱️ Hạn: {dl_naive.strftime('%d/%m %H:%M') if dl_naive else '—'}</span>
                </div>
                """, unsafe_allow_html=True)
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("✏️ CHI TIẾT", key=f"td_ed_{t['id']}", use_container_width=True):
                        st.session_state.editing_task_id = t['id']
                        st.rerun()
                with col_btn2:
                    if st.button("LÀM ➔", key=f"td_mv_{t['id']}", use_container_width=True):
                        run_query("UPDATE team_tasks SET status='Doing' WHERE id=%s", (t['id'],), commit=True)
                        st.rerun()

        with col_doing:
            st.markdown("<h5 style='color: #f59e0b; text-align:center;'>⚡ ĐANG LÀM</h5>", unsafe_allow_html=True)
            for t in [x for x in day_tasks if x['status'] == 'Doing' and not x['is_closed']]:
                dl_naive = strip_tz(t['deadline_date'])
                card_class = "task-card task-overdue" if (dl_naive and dl_naive < today_dt) else "task-card task-doing"
                
                st.markdown(f"""
                <div class="{card_class}">
                    <div class="task-title">{t['task_name']}</div>
                    <span style='font-size:12px; color:#94a3b8;'>👤 {t['assignee']}</span><br>
                    <span style='font-size:12px; color:#fbbf24;'>⏱️ Hạn: {dl_naive.strftime('%d/%m %H:%M') if dl_naive else '—'}</span>
                </div>
                """, unsafe_allow_html=True)
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("✏️ CHECKLIST", key=f"dg_ed_{t['id']}", use_container_width=True):
                        st.session_state.editing_task_id = t['id']
                        st.rerun()
                with col_btn2:
                    if st.button("XONG ✅", key=f"dg_mv_{t['id']}", use_container_width=True):
                        run_query("UPDATE team_tasks SET status='Done' WHERE id=%s", (t['id'],), commit=True)
                        st.rerun()

        with col_done:
            st.markdown("<h5 style='color: #10b981; text-align:center;'>✅ HOÀN THÀNH</h5>", unsafe_allow_html=True)
            for t in [x for x in day_tasks if x['status'] == 'Done' or x['is_closed']]:
                st.markdown(f"""
                <div class="task-card task-done">
                    <div class="task-title" style="text-decoration: line-through; color: #a1a1aa;">{t['task_name']}</div>
                    <span style='font-size:12px; color:#a1a1aa;'>👤 Phụ trách: {t['assignee']}</span>
                </div>
                """, unsafe_allow_html=True)
                if st.button("XEM LẠI", key=f"dn_ed_{t['id']}", use_container_width=True):
                    st.session_state.editing_task_id = t['id']
                    st.rerun()

# ====================================================================
# QUẢN LÝ NHÂN SỰ FRAME (NẾU ĐƯỢC CHỌN)
# ====================================================================
if st.session_state.current_page == "HR":
    st.divider()
    st.title("👥 DANH SÁCH TÀI KHOẢN NHÂN SỰ HỆ THỐNG")
    all_users_raw = run_query("SELECT id, username, role, uid FROM hlc_users ORDER BY id ASC;")
    if all_users_raw: st.dataframe(pd.DataFrame(all_users_raw), use_container_width=True)
