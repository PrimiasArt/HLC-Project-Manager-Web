import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.parse
import datetime
import calendar
import pandas as pd
from io import BytesIO

# ====================================================================
# 🛡️ CẤU HÌNH TRANG & GIAO DIỆN SÂU (DARK MODE)
# ====================================================================
st.set_page_config(
    page_title="HLC Workstation Team Project Hub",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Khởi tạo Session State (Quản lý trạng thái phiên làm việc) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None
if "uid" not in st.session_state:
    st.session_state.uid = None
if "selected_date" not in st.session_state:
    st.session_state.selected_date = datetime.date.today()
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

# ====================================================================
# 🔑 CẤU HÌNH DATABASE SUPABASE
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
    """Tối ưu kết nối bằng cache resource của Streamlit (thay thế Pooler thủ công)"""
    return psycopg2.connect(DB_URL)

def run_query(sql, params=None, commit=False, fetch="all"):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            if commit:
                conn.commit()
                return None
            if fetch == "all":
                return cur.fetchall()
            elif fetch == "one":
                return cur.fetchone()
    except Exception as e:
        conn.rollback()
        st.error(f"Database Error: {e}")
        return None

# ====================================================================
# 🔒 MÀN HÌNH ĐĂNG NHẬP
# ====================================================================
def render_login():
    st.markdown("<h2 style='text-align: center; color: #38bdf8;'>🔒 HLC SYSTEM CLOUD AUTHENTICATION</h2>", unsafe_allow_html=True)
    
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Tên đăng nhập (Username)").strip()
        password = st.text_input("Mật khẩu (Password)", type="password").strip()
        submit = st.form_submit_button("ĐĂNG NHẬP HỆ THỐNG", use_container_width=True)
        
        if submit:
            if not username or not password:
                st.error("❌ Vui lòng điền đầy đủ thông tin tài khoản!")
            else:
                user = run_query(
                    "SELECT username, role, uid FROM hlc_users WHERE username = %s AND password = %s;",
                    (username, password), fetch="one"
                )
                if user:
                    st.session_state.authenticated = True
                    st.session_state.username = user['username']
                    st.session_state.role = user['role']
                    st.session_state.uid = str(user['uid'])
                    st.success("Đăng nhập thành công!")
                    st.rerun()
                else:
                    st.error("❌ Sai tài khoản hoặc mật khẩu hệ thống!")

# ====================================================================
# 📊 MÀN HÌNH CHÍNH (DASHBOARD KANBAN + LIST VÀ EXCEL XUẤT KHẨU)
# ====================================================================
def render_dashboard():
    # --- TOP BAR ---
    col_title, col_btn1, col_btn2, col_btn3 = st.columns([5, 2, 2, 2])
    with col_title:
        st.title(f"📊 HLC PRODUCTION HUB ➔ {st.session_state.username.upper()} ({st.session_state.role.upper()})")
    
    with col_btn1:
        if st.session_state.role in ("Admin", "Manager"):
            if st.button("👥 QUẢN LÝ NHÂN SỰ", use_container_width=True):
                st.session_state.current_page = "HR"
                st.rerun()
    with col_btn2:
        if st.button("🔄 LÀM MỚI CLOUD", use_container_width=True):
            st.rerun()
    with col_btn3:
        if st.button("🚪 ĐĂNG XUẤT", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

    st.divider()

    # --- CHIA LAYOUT: TRÁI (TẠO TASK & CALENDAR) | PHẢI (KANBAN BOARD) ---
    col_left, col_right = st.columns([1, 3])

    with col_left:
        st.subheader("➕ KHỞI TẠO ĐẦU VIỆC MỚI")
        
        # Load danh sách user phục vụ Assignee dropdown
        users_data = run_query("SELECT username FROM hlc_users ORDER BY username ASC;")
        user_list = [u['username'] for u in users_data] if users_data else ["postgres"]

        with st.form("create_task_form"):
            task_name = st.text_input("Tên đầu việc (Task Name)")
            
            # Phân quyền Assignee giống code cũ của anh
            if st.session_state.role == "Member":
                assignee = st.selectbox("Nhân sự phụ trách", [st.session_state.username], disabled=True)
            else:
                assignee = st.selectbox("Nhân sự phụ trách", user_list)

            start_date = st.date_input("📆 Ngày bắt đầu", datetime.date.today())
            deadline_date = st.date_input("Hạn chót (Deadline)", datetime.date.today() + datetime.timedelta(days=3))
            deadline_time = st.time_input("Giờ hạn chót", datetime.time(23, 59))
            
            task_details = st.text_area("Mô tả chi tiết công việc")
            task_docs = st.text_area("Tài liệu Docs / Comment note")
            
            submit_task = st.form_submit_button("🚀 ĐẨY TASK LÊN ĐÁM MÂY", use_container_width=True)
            
            if submit_task:
                if not task_name:
                    st.error("Vui lòng nhập tên công việc!")
                else:
                    full_deadline = datetime.datetime.combine(deadline_date, deadline_time)
                    run_query("""
                        INSERT INTO team_tasks (task_name, assignee, start_date, deadline_date, status, task_details, task_docs, created_by, is_closed, sub_tasks, tagged_users)
                        VALUES (%s, %s, %s, %s, 'To-do', %s, %s, %s, FALSE, '[]'::jsonb, '[]'::jsonb);
                    """, (task_name, assignee, start_date, full_deadline, task_details, task_docs, st.session_state.username), commit=True)
                    st.success("Khởi tạo công việc lên Cloud thành công!")
                    st.rerun()

    with col_right:
        # Bộ lọc & Tìm kiếm nhanh
        search_kw = st.text_input("🔍 Tìm nhanh theo tên Task hoặc Nhân sự...").strip().lower()
        
        # Pull data từ Supabase về hiển thị
        tasks = run_query("SELECT * FROM team_tasks ORDER BY is_closed ASC, deadline_date ASC;")
        
        if tasks:
            # Filter dữ liệu theo từ khoá tìm kiếm
            filtered_tasks = [
                t for t in tasks 
                if not search_kw or search_kw in str(t['task_name']).lower() or search_kw in str(t['assignee']).lower()
            ]

            # Chia 3 cột Kanban Board trực quan bằng thẻ `st.container`
            tab_todo, tab_doing, tab_done = st.columns(3)
            
            with tab_todo:
                st.markdown("### 📌 CẦN LÀM")
                for t in [x for x in filtered_tasks if x['status'] == 'To-do' and not x['is_closed']]:
                    with st.container(border=True):
                        st.markdown(f"**{t['task_name']}**")
                        st.caption(f"👤 {t['assignee']} | Hạn: {t['deadline_date']}")
                        if st.button("TIẾN ĐỘ ➔", key=f"btn_go_{t['id']}"):
                            run_query("UPDATE team_tasks SET status='Doing' WHERE id=%s", (t['id'],), commit=True)
                            st.rerun()

            with tab_doing:
                st.markdown("### ⚡ ĐANG LÀM")
                for t in [x for x in filtered_tasks if x['status'] == 'Doing' and not x['is_closed']]:
                    with st.container(border=True):
                        st.markdown(f"**{t['task_name']}**")
                        st.caption(f"👤 {t['assignee']} | Hạn: {t['deadline_date']}")
                        col_b1, col_b2 = st.columns(2)
                        with col_b1:
                            if st.button("⬅ HẠ CẤP", key=f"btn_back_{t['id']}"):
                                run_query("UPDATE team_tasks SET status='To-do' WHERE id=%s", (t['id'],), commit=True)
                                st.rerun()
                        with col_b2:
                            if st.button("XONG ✅", key=f"btn_done_{t['id']}"):
                                run_query("UPDATE team_tasks SET status='Done' WHERE id=%s", (t['id'],), commit=True)
                                st.rerun()

            with tab_done:
                st.markdown("### ✅ HOÀN THÀNH / ĐÓNG")
                for t in [x for x in filtered_tasks if x['status'] == 'Done' or x['is_closed']]:
                    with st.container(border=True):
                        st.markdown(f"~~{t['task_name']}~~" if t['is_closed'] else f"**{t['task_name']}**")
                        st.caption(f"👤 {t['assignee']} | Trạng thái: {t['status']}")
                        
        else:
            st.info("Hiện không có công việc nào trên Cloud.")

# ====================================================================
# 👥 MÀN HÌNH QUẢN LÝ NHÂN SỰ (HR)
# ====================================================================
def render_hr():
    st.title("👥 QUẢN TRỊ NHÂN SỰ HỆ THỐNG")
    if st.button("◀ QUAY LẠI DASHBOARD"):
        st.session_state.current_page = "Dashboard"
        st.rerun()
        
    users = run_query("SELECT id, username, role, uid FROM hlc_users ORDER BY role ASC;")
    if users:
        df_users = pd.DataFrame(users)
        st.dataframe(df_users, use_container_width=True)

# ====================================================================
# ĐIỀU HƯỚNG ROUTING CHÍNH CỦA APP
# ====================================================================
if not st.session_state.authenticated:
    render_login()
else:
    if st.session_state.current_page == "Dashboard":
        render_dashboard()
    elif st.session_state.current_page == "HR":
        render_hr()