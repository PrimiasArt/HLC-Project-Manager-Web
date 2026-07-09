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
# CSS
# ====================================================================
st.markdown("""
<style>
@media (prefers-color-scheme: light) {
    :root {
        --bg-card:#fffdf5; --bg-panel:#f0e8d0; --border-color:#c8b87a;
        --text-primary:#1a1000; --text-secondary:#4a3a18; --text-muted:#6b5a38;
        --accent-blue:#1d4ed8; --accent-blue-bg:#dbeafe;
        --header-bg:#e4d9b0; --tag-closed-bg:#ddd5b8;
    }
}
@media (prefers-color-scheme: dark) {
    :root {
        --bg-card:#1e2940; --bg-panel:#202d44; --border-color:#2d3f5c;
        --text-primary:#e2e8f4; --text-secondary:#94a8c4; --text-muted:#647a99;
        --accent-blue:#38bdf8; --accent-blue-bg:#0c2540;
        --header-bg:#1a2a42; --tag-closed-bg:#2d3f5c;
    }
}
:root {
    --bg-card:#1e2940; --bg-panel:#202d44; --border-color:#2d3f5c;
    --text-primary:#e2e8f4; --text-secondary:#94a8c4; --text-muted:#647a99;
    --accent-blue:#38bdf8; --accent-blue-bg:#0c2540;
    --header-bg:#1a2a42; --tag-closed-bg:#2d3f5c;
}
.hlc-date-header {
    background-color:var(--header-bg); border:1px solid var(--border-color);
    padding:8px 16px; border-radius:4px; margin-top:14px; margin-bottom:6px;
    display:flex; justify-content:space-between; align-items:center;
    color:var(--accent-blue); font-size:13px; font-weight:bold;
}
.task-block {
    padding:12px 14px; border-radius:8px; margin-bottom:8px;
    border-left:5px solid #ccc; background-color:var(--bg-card);
}
.task-hidden { opacity:0.45; filter:blur(0.5px); }
.status-closed  { border-left-color:#64748b !important; background-color:var(--tag-closed-bg) !important; }
.status-doing   { border-left-color:#f59e0b !important; }
.status-done    { border-left-color:#10b981 !important; }
.status-overdue { border-left-color:#ef4444 !important; }
.hlc-tag-badge {
    display:inline-block; padding:2px 10px; font-size:11px; font-weight:bold;
    color:#fff !important; border-radius:6px; text-align:center;
    margin-right:6px; min-width:85px;
}
.tag-todo    { background-color:#4b5563; }
.tag-doing   { background-color:#f59e0b; }
.tag-done    { background-color:#10b981; }
.tag-overdue { background-color:#ef4444; }
.priority-gap {
    display:inline-block; padding:2px 10px; font-size:11px; font-weight:bold;
    color:#fff !important; border-radius:6px; background-color:#c2410c; margin-right:6px;
}
.priority-very-gap {
    display:inline-block; padding:2px 10px; font-size:11px; font-weight:900;
    color:#fff !important; border-radius:6px; background-color:#dc2626; margin-right:6px;
    letter-spacing:.06em; text-transform:uppercase;
}
.hidden-badge {
    display:inline-block; padding:2px 8px; font-size:10px; font-weight:bold;
    color:#fff !important; border-radius:4px; background-color:#6b21a8; margin-right:6px;
}
.t-title        { font-weight:bold; font-size:14px; color:var(--text-primary); }
.t-title-closed { font-weight:bold; font-size:14px; color:var(--text-muted); text-decoration:line-through; }
.t-sub-info     { font-size:11px; color:var(--text-secondary); margin-top:6px; }
.cal-table { width:100%; border-collapse:collapse; font-size:12px; margin-bottom:8px; }
.cal-table th {
    background-color:var(--header-bg); color:var(--accent-blue);
    padding:5px 2px; text-align:center; font-weight:bold; font-size:11px;
}
.cal-table td {
    text-align:center; padding:4px 2px; border:1px solid var(--border-color);
    vertical-align:top; min-width:34px;
}
.cal-day-num { font-size:13px; font-weight:bold; color:var(--text-primary); }
.cal-day-today .cal-day-num {
    background-color:var(--accent-blue); color:#fff;
    border-radius:50%; width:22px; height:22px;
    display:inline-flex; align-items:center; justify-content:center;
}
.cal-day-selected { background-color:var(--accent-blue-bg) !important; }
.cal-dots { display:flex; justify-content:center; gap:2px; margin-top:2px; min-height:8px; }
.cal-dot  { width:6px; height:6px; border-radius:50%; flex-shrink:0; }
.dot-gray   { background-color:#64748b; }
.dot-blue   { background-color:#3b82f6; }
.dot-orange { background-color:#f59e0b; }
.dot-red    { background-color:#ef4444; }
/* NOTIFICATION BELL */
.notif-bell-wrap {
    position:relative; display:inline-block; cursor:pointer;
}
.notif-dot {
    position:absolute; top:-3px; right:-4px;
    width:10px; height:10px; border-radius:50%;
    background:#ef4444; border:2px solid var(--bg-card);
}
/* RECAP CARD */
.recap-card {
    padding:12px 16px; border-radius:8px; margin-bottom:10px;
    border-left:5px solid #8b5cf6; background-color:var(--bg-card);
}
.recap-title { font-weight:bold; font-size:15px; color:var(--text-primary); }
.recap-meta  { font-size:11px; color:var(--text-secondary); margin-top:4px; }
</style>
""", unsafe_allow_html=True)

# ====================================================================
# SESSION STATE
# ====================================================================
defaults = {
    "authenticated":False,"username":None,"role":None,"uid":None,
    "selected_date":datetime.date.today(),"editing_task_id":None,
    "search_kw":"","show_notif":False,"notif_read_count":0,
    "viewing_user":None,"editing_user":None,
    "editing_recap_id":None,
}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k]=v

# ====================================================================
# DATABASE
# ====================================================================
DB_PASS="Sha220393..!#"
DB_USER="postgres.ynfgjerpqjhvnuakcduv"
DB_HOST="aws-1-ap-southeast-2.pooler.supabase.com"
DB_PORT="6543"; DB_NAME="postgres"
SAFE_PASS=urllib.parse.quote_plus(DB_PASS.strip())
DB_URL=f"postgres://{DB_USER}:{SAFE_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"

@st.cache_resource
def get_db():
    return psycopg2.connect(DB_URL)

def run_query(sql, params=None, commit=False, fetch="all"):
    conn=get_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql,params)
            if commit: conn.commit(); return None
            return cur.fetchall() if fetch=="all" else cur.fetchone()
    except Exception as e:
        conn.rollback(); st.error(f"💥 DB Error: {e}"); return None

def safe_json(raw):
    if not raw: return []
    if isinstance(raw,list): return raw
    try: return json.loads(raw)
    except: return []

def strip_tz(dt):
    if dt is None: return None
    if isinstance(dt,datetime.datetime): return dt.replace(tzinfo=None)
    return dt

# ====================================================================
# PUSH NOTIFICATION HELPER
# ====================================================================
def push_notif(actor, action, subject, detail=""):
    """Ghi thông báo vào bảng hlc_notifications."""
    run_query("""
        INSERT INTO hlc_notifications (actor, action, subject, detail, created_at)
        VALUES (%s,%s,%s,%s, NOW());
    """, (actor, action, subject, detail), commit=True)

def get_notifs(limit=40):
    return run_query("""
        SELECT * FROM hlc_notifications ORDER BY created_at DESC LIMIT %s;
    """, (limit,)) or []

def mark_notifs_read(count):
    st.session_state.notif_read_count = count

# ====================================================================
# LOGIN
# ====================================================================
if not st.session_state.authenticated:
    st.markdown("<br><br><h2 style='text-align:center;color:#38bdf8;'>🔒 HLC SYSTEM CLOUD AUTHENTICATION</h2>",unsafe_allow_html=True)
    with st.form("login_form"):
        uname=st.text_input("Tên đăng nhập").strip()
        pwd=st.text_input("Mật khẩu",type="password").strip()
        if st.form_submit_button("ĐĂNG NHẬP HỆ THỐNG",use_container_width=True):
            u=run_query("SELECT username,role,uid FROM hlc_users WHERE username=%s AND password=%s;",(uname,pwd),fetch="one")
            if u:
                st.session_state.update(authenticated=True,username=u['username'],role=u['role'],uid=str(u['uid']))
                st.rerun()
            else: st.error("❌ Sai thông tin xác thực!")
    st.stop()

# ====================================================================
# TẢI DỮ LIỆU
# ====================================================================
users_db      = run_query("SELECT username,uid,role FROM hlc_users ORDER BY username ASC;") or []
all_usernames = [u['username'] for u in users_db]
user_uid_map  = {u['username']:str(u['uid']) for u in users_db}
user_role_map = {u['username']:u['role']     for u in users_db}
assignable_users = all_usernames if st.session_state.role=="Admin" \
                   else [u for u in all_usernames if user_role_map.get(u)!="Admin"]

raw_tasks = run_query("SELECT * FROM team_tasks ORDER BY is_closed ASC, deadline_date ASC;") or []
today_dt  = datetime.datetime.now()

# Lọc ẩn với member
def visible_tasks(tasks):
    if st.session_state.role=="Admin": return tasks
    return [t for t in tasks if not t.get('is_hidden',False)]

all_tasks     = raw_tasks
filtered_show = visible_tasks(all_tasks)

# ── TOASTS ──
overdue_count = sum(1 for t in filtered_show if not t['is_closed'] and t['status']!='Done'
                    and t['deadline_date'] and strip_tz(t['deadline_date'])<today_dt)
if overdue_count>0:
    st.toast(f"🚨 {overdue_count} task QUÁ HẠN! Kiểm tra ngay.",icon="⚠️")
soon = [t for t in filtered_show if not t['is_closed'] and t['status']!='Done'
        and t['deadline_date']
        and today_dt<=strip_tz(t['deadline_date'])<=today_dt+datetime.timedelta(hours=24)]
if soon: st.toast(f"⏰ {len(soon)} task đến hạn trong 24h!",icon="🔔")

# ── NOTIFICATION COUNT ──
all_notifs  = get_notifs(40)
total_notif = len(all_notifs)
unread_count= max(0, total_notif - st.session_state.notif_read_count)

# ====================================================================
# PRIORITY / HIDDEN HELPERS
# ====================================================================
PRIORITY_OPTIONS=["(Không có)","Gấp","Rất Gấp"]

def get_priority(task):
    raw=task.get('task_docs') or ""
    if raw.startswith("__PRIORITY__:"): return raw.split("\n",1)[0].replace("__PRIORITY__:","").strip()
    return ""

def get_docs_clean(task):
    raw=task.get('task_docs') or ""
    if raw.startswith("__PRIORITY__:"):
        parts=raw.split("\n",1); return parts[1] if len(parts)>1 else ""
    return raw

def pack_docs(priority,docs_text):
    if priority and priority!="(Không có)": return f"__PRIORITY__:{priority}\n{docs_text}"
    return docs_text

def priority_html(p):
    if p=="Gấp":     return '<span class="priority-gap">🔶 Gấp</span>'
    if p=="Rất Gấp": return '<span class="priority-very-gap">🚨 RẤT GẤP</span>'
    return ""

# ====================================================================
# EDIT TASK POPUP
# ====================================================================
if st.session_state.editing_task_id is not None:
    task=run_query("SELECT * FROM team_tasks WHERE id=%s;",(st.session_state.editing_task_id,),fetch="one")
    if task:
        st.markdown(f"### ✏️ Chi Tiết: `{task['task_name']}`")
        is_owner=(st.session_state.role=="Admin"
                  or st.session_state.username.lower() in
                     [str(task['created_by']).lower(),str(task['assignee']).lower()])
        sub_tasks   =safe_json(task['sub_tasks'])
        tagged_users=safe_json(task['tagged_users'])
        cur_pri=get_priority(task)
        docs_display=get_docs_clean(task)
        is_hidden=task.get('is_hidden',False)

        with st.form("edit_task_form"):
            en=st.text_input("Tên đầu việc",value=task['task_name'],disabled=not is_owner or task['is_closed'])
            pidx=PRIORITY_OPTIONS.index(cur_pri) if cur_pri in PRIORITY_OPTIONS else 0
            ep=st.selectbox("🚨 Tag Ưu Tiên",PRIORITY_OPTIONS,index=pidx,disabled=not is_owner or task['is_closed'])
            ea=st.selectbox("Nhân sự phụ trách",assignable_users,
                            index=assignable_users.index(task['assignee']) if task['assignee'] in assignable_users else 0,
                            disabled=not is_owner or task['is_closed'])
            c1,c2=st.columns(2)
            with c1:
                sd=task['start_date'] if isinstance(task['start_date'],datetime.date) else datetime.date.today()
                es=st.date_input("Ngày bắt đầu",value=sd,disabled=not is_owner or task['is_closed'])
            with c2:
                dl=strip_tz(task['deadline_date']) or datetime.datetime.now()
                edd=st.date_input("Ngày hạn chót",value=dl.date(),disabled=not is_owner or task['is_closed'])
                edt=st.time_input("Giờ hạn chót",value=dl.time(),disabled=not is_owner or task['is_closed'])
            ede=st.text_area("Mô tả chi tiết",value=task['task_details'] or "",disabled=not is_owner or task['is_closed'])
            edc=st.text_area("💬 Ghi chú / Comment",value=docs_display)
            etg=st.multiselect("🏷️ Thành viên hỗ trợ",
                               [u for u in assignable_users if u!=ea],
                               default=[t for t in tagged_users if t in assignable_users],
                               disabled=not is_owner or task['is_closed'])
            # Admin: toggle ẩn task
            hide_toggle=False
            if st.session_state.role=="Admin":
                hide_toggle=st.checkbox("🔒 Ẩn task này với Member",value=is_hidden)

            st.write("📋 **Các bước thực hiện:**")
            updated_subs=[]
            for idx,si in enumerate(sub_tasks):
                cb=st.checkbox(si.get('name',''),value=si.get('done',False),key=f"sub_{idx}")
                updated_subs.append({"name":si.get('name',''),"done":cb})
            bulk=st.text_area("➕ Thêm bước (mỗi dòng 1 bước):",height=70)

            cs,cc,cx=st.columns([2,2,1])
            with cs: save_btn  =st.form_submit_button("💾 LƯU",use_container_width=True)
            with cc: close_btn =st.form_submit_button("🔒 ĐÓNG TASK",use_container_width=True) if is_owner and not task['is_closed'] else False
            with cx: cancel_btn=st.form_submit_button("Đóng",use_container_width=True)

            if save_btn:
                if bulk.strip() and is_owner and not task['is_closed']:
                    for line in [l.strip() for l in bulk.split('\n') if l.strip()]:
                        updated_subs.append({"name":line,"done":False})
                fdl=datetime.datetime.combine(edd,edt)
                tuids=[user_uid_map[u] for u in etg if u in user_uid_map]
                nd=pack_docs(ep,edc)
                if is_owner and not task['is_closed']:
                    run_query("""
                        UPDATE team_tasks SET task_name=%s,assignee=%s,assignee_uid=%s::uuid,
                        start_date=%s,deadline_date=%s,task_details=%s,task_docs=%s,
                        sub_tasks=%s::jsonb,tagged_users=%s::jsonb,tagged_uids=%s::jsonb,
                        is_hidden=%s WHERE id=%s;
                    """,(en,ea,user_uid_map.get(ea),es,fdl,ede,nd,
                         json.dumps(updated_subs),json.dumps(etg),json.dumps(tuids),
                         hide_toggle,task['id']),commit=True)
                    push_notif(st.session_state.username,"CẬP NHẬT TASK",en,
                               f"Trạng thái: {task['status']} | Hạn: {fdl.strftime('%d/%m/%Y %H:%M')}")
                else:
                    run_query("UPDATE team_tasks SET task_docs=%s WHERE id=%s;",
                              (pack_docs(cur_pri,edc),task['id']),commit=True)
                    push_notif(st.session_state.username,"COMMENT TASK",task['task_name'],edc[:80])
                st.session_state.editing_task_id=None; st.rerun()
            if close_btn:
                run_query("UPDATE team_tasks SET is_closed=TRUE,status='Done' WHERE id=%s;",(task['id'],),commit=True)
                push_notif(st.session_state.username,"ĐÓNG TASK",task['task_name'],"Task đã được đóng vĩnh viễn")
                st.session_state.editing_task_id=None; st.rerun()
            if cancel_btn:
                st.session_state.editing_task_id=None; st.rerun()
    st.stop()

# ====================================================================
# EDIT RECAP POPUP
# ====================================================================
if st.session_state.editing_recap_id is not None:
    rec=run_query("SELECT * FROM hlc_recaps WHERE id=%s;",(st.session_state.editing_recap_id,),fetch="one")
    if rec:
        st.markdown(f"### 📝 Chi Tiết Recap: `{rec['title']}`")
        with st.form("edit_recap_form"):
            er_title=st.text_input("Tiêu đề",value=rec['title'])
            er_time =st.text_input("Thời gian",value=rec['meeting_time'] or "")
            er_place=st.text_input("Địa điểm",value=rec['location'] or "")
            er_parts=st.text_input("Người tham gia (cách nhau bởi dấu phẩy)",
                                   value=", ".join(safe_json(rec.get('participants',[]))))
            er_body =st.text_area("Nội dung Recap",value=rec['content'] or "",height=200)
            rs,rx=st.columns([3,1])
            with rs: rsave=st.form_submit_button("💾 LƯU",use_container_width=True)
            with rx: rcancel=st.form_submit_button("Đóng",use_container_width=True)
            if rsave:
                parts_list=[p.strip() for p in er_parts.split(",") if p.strip()]
                run_query("""UPDATE hlc_recaps SET title=%s,meeting_time=%s,location=%s,
                             participants=%s::jsonb,content=%s WHERE id=%s;""",
                          (er_title,er_time,er_place,json.dumps(parts_list),er_body,rec['id']),commit=True)
                push_notif(st.session_state.username,"CẬP NHẬT RECAP",er_title)
                st.session_state.editing_recap_id=None; st.rerun()
            if rcancel:
                st.session_state.editing_recap_id=None; st.rerun()
    st.stop()

# ====================================================================
# HEADER
# ====================================================================
hc1,hc2,hc3,hc4=st.columns([7.5,1.2,1.2,1.2])
with hc1:
    st.markdown(f"<h2 style='color:#38bdf8;margin:0;'>📊 HLC PRODUCTION HUB ➔ {st.session_state.username.upper()}</h2>",
                unsafe_allow_html=True)
with hc2:
    if st.button("🔄 ĐỒNG BỘ",use_container_width=True): st.rerun()
with hc3:
    # CHUÔNG THÔNG BÁO
    bell_label = f"🔔 ({unread_count})" if unread_count>0 else "🔔"
    if st.button(bell_label,use_container_width=True,type="primary" if unread_count>0 else "secondary"):
        st.session_state.show_notif=not st.session_state.show_notif
        if st.session_state.show_notif:
            mark_notifs_read(total_notif)
        st.rerun()
with hc4:
    if st.button("🚪 ĐĂNG XUẤT",use_container_width=True):
        st.session_state.authenticated=False; st.rerun()

# ── NOTIFICATION PANEL ────────────────────────────────────────────
if st.session_state.show_notif:
    with st.container():
        st.markdown("---")
        st.markdown("##### 🔔 TRUNG TÂM THÔNG BÁO")
        if not all_notifs:
            st.info("Chưa có thông báo nào.")
        else:
            for n in all_notifs[:20]:
                ts=n['created_at']
                if isinstance(ts,datetime.datetime): ts=ts.strftime('%d/%m %H:%M')
                color_map={"CẬP NHẬT TASK":"#f59e0b","TẠO TASK":"#10b981","ĐÓNG TASK":"#64748b",
                           "COMMENT TASK":"#3b82f6","TẠO RECAP":"#8b5cf6","CẬP NHẬT RECAP":"#8b5cf6",
                           "TẠO USER":"#06b6d4","ĐỔI MẬT KHẨU":"#f43f5e","CẬP NHẬT USER":"#f97316"}
                c=color_map.get(str(n['action']),"#94a3b8")
                det=f" — {n['detail']}" if n.get('detail') else ""
                st.markdown(
                    f"<div style='padding:6px 10px;margin-bottom:4px;border-left:3px solid {c};"
                    f"background:var(--bg-card);border-radius:4px;font-size:12px;'>"
                    f"<span style='color:{c};font-weight:bold;'>[{n['action']}]</span> "
                    f"<b style='color:var(--text-primary);'>{n['subject']}</b>"
                    f"<span style='color:var(--text-muted);'>{det}</span>"
                    f"<span style='float:right;color:var(--text-muted);font-size:10px;'>by {n['actor']} · {ts}</span>"
                    f"</div>",unsafe_allow_html=True)
        if st.button("✕ Đóng thông báo",use_container_width=True):
            st.session_state.show_notif=False; st.rerun()
        st.markdown("---")

# ====================================================================
# TABS
# ====================================================================
tab_labels=["📋 Công Việc","📝 Recap / Thông Báo"]
if st.session_state.role=="Admin": tab_labels.append("👥 Nhân Sự")
tabs=st.tabs(tab_labels)

# ====================================================================
# TAB 0: CÔNG VIỆC
# ====================================================================
with tabs[0]:
    csr,cso,csv_=st.columns([5,2,2])
    with csr: st.session_state.search_kw=st.text_input("🔍 Lọc...",value=st.session_state.search_kw,key="srch")
    with cso: sort_mode=st.selectbox("Sắp xếp",["Mặc định","Theo nhân sự"])
    with csv_: view_mode=st.selectbox("Chế độ xem",["Kanban","List View","Tuần","Tháng"])

    ftasks=filtered_show[:]
    if st.session_state.search_kw.strip():
        kw=st.session_state.search_kw.lower()
        ftasks=[t for t in ftasks if kw in str(t['task_name']).lower() or kw in str(t['assignee']).lower()]
    if sort_mode=="Theo nhân sự":
        ftasks=sorted(ftasks,key=lambda x:(x['assignee'] or '').lower())
    # Admin thấy thêm task ẩn (có badge)
    if st.session_state.role=="Admin":
        ftasks=raw_tasks[:]
        if st.session_state.search_kw.strip():
            kw=st.session_state.search_kw.lower()
            ftasks=[t for t in ftasks if kw in str(t['task_name']).lower() or kw in str(t['assignee']).lower()]
        if sort_mode=="Theo nhân sự":
            ftasks=sorted(ftasks,key=lambda x:(x['assignee'] or '').lower())

    st.divider()

    # ── TASK CARD ──────────────────────────────────────────────────
    def draw_task_item(t,prefix,uid=0):
        dl=strip_tz(t['deadline_date'])
        ov=not t['is_closed'] and t['status']!='Done' and dl and dl<today_dt
        pri=get_priority(t)
        hidden=t.get('is_hidden',False)

        if t['is_closed']:
            ccs="task-block status-closed"; tag='<span class="hlc-tag-badge tag-todo">To do</span>'; tcs="t-title-closed"
        elif ov:
            ccs="task-block status-overdue"; tag='<span class="hlc-tag-badge tag-overdue">Urgent</span>'; tcs="t-title"
        elif t['status']=='Done':
            ccs="task-block status-done"; tag='<span class="hlc-tag-badge tag-done">Done</span>'; tcs="t-title"
        elif t['status']=='Doing':
            ccs="task-block status-doing"; tag='<span class="hlc-tag-badge tag-doing">Processing</span>'; tcs="t-title"
        else:
            ccs="task-block"; tag='<span class="hlc-tag-badge tag-todo">To do</span>'; tcs="t-title"

        if hidden and st.session_state.role=="Admin": ccs+=" task-hidden"
        ph=priority_html(pri)
        hb='<span class="hidden-badge">🔒 Ẩn</span>' if hidden and st.session_state.role=="Admin" else ""
        subs=safe_json(t['sub_tasks']); total=len(subs)
        done_s=sum(1 for s in subs if s.get('done'))
        prog=(done_s/total) if total else (1.0 if t['status']=='Done' else 0.0)

        st.markdown(f"""
        <div class="{ccs}">
            <div style="display:flex;align-items:center;gap:4px;flex-wrap:wrap;">
                {tag}{ph}{hb}<span class="{tcs}">{t['task_name']}</span>
            </div>
            <div class="t-sub-info">👤 {t['assignee']} | 🎬 {t['created_by']}</div>
        </div>""",unsafe_allow_html=True)
        a,b,c3=st.columns([5,4,3])
        with a: st.caption(f"📋 {done_s}/{total}" if total else f"⏱️ {dl.strftime('%d/%m/%Y') if dl else '—'}")
        with b: st.progress(prog)
        with c3:
            if st.button("✏️ CHI TIẾT",key=f"ed_{prefix}_{t['id']}_{uid}",use_container_width=True):
                st.session_state.editing_task_id=t['id']; st.rerun()

    # ── DOT ────────────────────────────────────────────────────────
    def get_day_dots(day,tlist):
        dots=[]
        for t in tlist:
            try:
                ts=t['start_date'] if isinstance(t['start_date'],datetime.date) else t['created_at'].date()
                te=t['deadline_date'].date() if isinstance(t['deadline_date'],datetime.datetime) else t['deadline_date']
                if ts<=day<=te:
                    dl=strip_tz(t['deadline_date'])
                    ov=not t['is_closed'] and t['status']!='Done' and dl and dl<today_dt
                    if t['is_closed']: dots.append("dot-gray")
                    elif ov: dots.append("dot-red")
                    elif t['status']=='Done': dots.append("dot-blue")
                    elif t['status']=='Doing': dots.append("dot-orange")
                    else: dots.append("dot-gray")
                    if len(dots)>=4: break
            except: pass
        return dots

    # ── LAYOUT ─────────────────────────────────────────────────────
    cl,cr=st.columns([3,7])
    with cl:
        anchor=st.session_state.selected_date
        y,m=anchor.year,anchor.month
        today0=datetime.date.today()
        MVN=["Tháng 1","Tháng 2","Tháng 3","Tháng 4","Tháng 5","Tháng 6",
             "Tháng 7","Tháng 8","Tháng 9","Tháng 10","Tháng 11","Tháng 12"]
        cp2,ct2,cn2=st.columns([1,4,1])
        with cp2:
            if st.button("◀",key="cp"):
                f=datetime.date(y,m,1); p=f-datetime.timedelta(days=1)
                st.session_state.selected_date=datetime.date(p.year,p.month,1); st.rerun()
        with ct2:
            st.markdown(f"<div style='text-align:center;font-weight:bold;font-size:13px;color:var(--accent-blue);padding-top:6px;'>{MVN[m-1]} {y}</div>",unsafe_allow_html=True)
        with cn2:
            if st.button("▶",key="cn"):
                _,ld=calendar.monthrange(y,m)
                st.session_state.selected_date=datetime.date(y,m,ld)+datetime.timedelta(days=1); st.rerun()

        cal_m=calendar.monthcalendar(y,m)
        DH=["T2","T3","T4","T5","T6","T7","CN"]
        thead="".join(f"<th>{d}</th>" for d in DH)
        tbody=""
        for wk in cal_m:
            tbody+="<tr>"
            for ci,dn in enumerate(wk):
                if dn==0: tbody+="<td></td>"
                else:
                    do=datetime.date(y,m,dn); tc=""
                    if do==anchor: tc+=" cal-day-selected"
                    if do==today0: tc+=" cal-day-today"
                    nc="#ef4444" if ci==6 and do!=today0 else ""
                    ns=f"color:{nc};" if nc else ""
                    ds=f'<span class="cal-day-num" style="{ns}">{dn}</span>'
                    dots=get_day_dots(do,ftasks)
                    dh="".join(f'<span class="cal-dot {c}"></span>' for c in dots[:4])
                    tbody+=f'<td class="{tc.strip()}">{ds}<div class="cal-dots">{dh}</div></td>'
            tbody+="</tr>"

        st.markdown(f'<table class="cal-table"><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table>',
                    unsafe_allow_html=True)
        pk=st.date_input("Chọn ngày",value=anchor,label_visibility="collapsed")
        if pk!=st.session_state.selected_date:
            st.session_state.selected_date=pk; st.rerun()
        st.markdown("""<div style="font-size:10px;color:var(--text-muted);display:flex;gap:8px;flex-wrap:wrap;margin-top:3px;">
            <span>⬤<span style='color:#64748b'> Closed</span></span>
            <span>⬤<span style='color:#3b82f6'> Done</span></span>
            <span>⬤<span style='color:#f59e0b'> Doing</span></span>
            <span>⬤<span style='color:#ef4444'> Quá hạn</span></span></div>""",unsafe_allow_html=True)

        st.markdown("<br>📝 **Tạo task mới:**",unsafe_allow_html=True)
        with st.form("add_task_form",clear_on_submit=True):
            cn_=st.text_input("Tên đầu việc")
            cp_=st.selectbox("🚨 Tag Ưu Tiên",PRIORITY_OPTIONS)
            ca_=st.selectbox("Nhân sự phụ trách",assignable_users,
                index=assignable_users.index(st.session_state.username) if st.session_state.username in assignable_users else 0,
                disabled=(st.session_state.role=="Member"))
            csd=st.date_input("Ngày bắt đầu",value=st.session_state.selected_date)
            cdld=st.date_input("Hạn chót",value=st.session_state.selected_date+datetime.timedelta(days=1))
            cdlt=st.time_input("Giờ hạn chót",datetime.time(18,0))
            cde=st.text_area("Mô tả chi tiết")
            cbk=st.text_area("Bước thực hiện (mỗi dòng 1 bước)",height=70)
            if st.form_submit_button("🚀 ĐẨY TASK LÊN CLOUD",use_container_width=True) and cn_.strip():
                subs=[{"name":l.strip(),"done":False} for l in cbk.split('\n') if l.strip()]
                fdl=datetime.datetime.combine(cdld,cdlt)
                docs=pack_docs(cp_,"")
                run_query("""
                    INSERT INTO team_tasks
                    (task_name,assignee,assignee_uid,start_date,deadline_date,
                     status,task_details,task_docs,created_by,is_closed,is_hidden,sub_tasks,tagged_users)
                    VALUES (%s,%s,%s::uuid,%s,%s,'To-do',%s,%s,%s,FALSE,FALSE,%s::jsonb,'[]'::jsonb);
                """,(cn_,ca_,user_uid_map.get(ca_),csd,fdl,cde,docs,st.session_state.username,json.dumps(subs)),commit=True)
                push_notif(st.session_state.username,"TẠO TASK",cn_,f"Giao cho: {ca_} | Hạn: {fdl.strftime('%d/%m/%Y')}")
                st.toast("🚀 Đã tạo task!",icon="🎉"); st.rerun()

    with cr:
        anchor=st.session_state.selected_date
        def on_day(t,d):
            try:
                ts=t['start_date'] if isinstance(t['start_date'],datetime.date) else t['created_at'].date()
                te=t['deadline_date'].date() if isinstance(t['deadline_date'],datetime.datetime) else t['deadline_date']
                return ts<=d<=te
            except: return False

        if view_mode=="Kanban":
            st.markdown(f"#### ⚡ KANBAN — `{anchor.strftime('%d/%m/%Y')}`")
            dt=[t for t in ftasks if on_day(t,anchor)]
            ct_,cd_,cn_=st.columns(3)
            with ct_:
                st.markdown("<h5 style='color:#94a3b8;text-align:center;'>📌 CẦN LÀM</h5>",unsafe_allow_html=True)
                for i,t in enumerate([x for x in dt if x['status']=='To-do' and not x['is_closed']]):
                    draw_task_item(t,"kbt",i)
                    if st.button("LÀM ➔",key=f"mv_do_{t['id']}",use_container_width=True):
                        run_query("UPDATE team_tasks SET status='Doing' WHERE id=%s",(t['id'],),commit=True)
                        push_notif(st.session_state.username,"CẬP NHẬT TASK",t['task_name'],"To-do → Doing")
                        st.rerun()
            with cd_:
                st.markdown("<h5 style='color:#f59e0b;text-align:center;'>🟡 ĐANG LÀM</h5>",unsafe_allow_html=True)
                for i,t in enumerate([x for x in dt if x['status']=='Doing' and not x['is_closed']]):
                    draw_task_item(t,"kbd",i)
                    b1,b2=st.columns(2)
                    with b1:
                        if st.button("⬅ HẠ",key=f"mv_dw_{t['id']}",use_container_width=True):
                            run_query("UPDATE team_tasks SET status='To-do' WHERE id=%s",(t['id'],),commit=True)
                            push_notif(st.session_state.username,"CẬP NHẬT TASK",t['task_name'],"Doing → To-do")
                            st.rerun()
                    with b2:
                        if st.button("XONG ✅",key=f"mv_up_{t['id']}",use_container_width=True):
                            run_query("UPDATE team_tasks SET status='Done' WHERE id=%s",(t['id'],),commit=True)
                            push_notif(st.session_state.username,"CẬP NHẬT TASK",t['task_name'],"Doing → Done ✅")
                            st.rerun()
            with cn_:
                st.markdown("<h5 style='color:#10b981;text-align:center;'>🟢 HOÀN THÀNH</h5>",unsafe_allow_html=True)
                for i,t in enumerate([x for x in dt if x['status']=='Done' or x['is_closed']]):
                    draw_task_item(t,"kbn",i)

        elif view_mode=="List View":
            st.markdown(f"#### 📋 LIST VIEW — `{anchor.strftime('%d/%m/%Y')}`")
            for i,t in enumerate([x for x in ftasks if on_day(x,anchor)]): draw_task_item(t,"lv",i)

        elif view_mode=="Tuần":
            sw=anchor-datetime.timedelta(days=anchor.weekday())
            dw=[sw+datetime.timedelta(days=i) for i in range(7)]
            VN=["Thứ 2","Thứ 3","Thứ 4","Thứ 5","Thứ 6","Thứ 7","Chủ Nhật"]
            st.markdown(f"#### ⏱️ TUẦN: `{sw.strftime('%d/%m')} ➔ {(sw+datetime.timedelta(days=6)).strftime('%d/%m/%Y')}`")
            for i,td in enumerate(dw):
                dt=[t for t in ftasks if on_day(t,td)]
                if not dt: continue
                st.markdown(f'<div class="hlc-date-header"><span>⭐ {VN[i].upper()} — {td.strftime("%d/%m/%Y")}</span><span>{len(dt)} TASK</span></div>',unsafe_allow_html=True)
                for j,t in enumerate(dt): draw_task_item(t,"wv",j+i*100)

        elif view_mode=="Tháng":
            st.markdown(f"#### 🗓️ THÁNG: `{anchor.strftime('%m/%Y')}`")
            _,ld=calendar.monthrange(anchor.year,anchor.month)
            cws=datetime.date(anchor.year,anchor.month,1); cws-=datetime.timedelta(days=cws.weekday()); wn=1
            while cws<=datetime.date(anchor.year,anchor.month,ld):
                cwe=cws+datetime.timedelta(days=6)
                def iw(t,ws=cws,we=cwe):
                    try:
                        ts=t['start_date'] if isinstance(t['start_date'],datetime.date) else t['created_at'].date()
                        te=t['deadline_date'].date() if isinstance(t['deadline_date'],datetime.datetime) else t['deadline_date']
                        return not(te<ws or ts>we)
                    except: return False
                wt=[t for t in ftasks if iw(t)]
                if wt:
                    st.markdown(f'<div class="hlc-date-header" style="background:#1e3a8a;border-color:#2563eb;color:#38bdf8;"><span>⚡ TUẦN {wn} ({cws.strftime("%d/%m")} ➔ {cwe.strftime("%d/%m")})</span><span>{len(wt)} TASK</span></div>',unsafe_allow_html=True)
                    for j,t in enumerate(wt): draw_task_item(t,"mv",j+wn*1000)
                cws+=datetime.timedelta(days=7); wn+=1

# ====================================================================
# TAB 1: RECAP / THÔNG BÁO
# ====================================================================
with tabs[1]:
    rt1,rt2=st.tabs(["📋 Danh Sách Recap","✍️ Tạo Recap Mới"])

    with rt2:
        st.markdown("#### ✍️ Tạo Recap / Thông Báo Cuộc Họp")
        with st.form("add_recap_form",clear_on_submit=True):
            r_title=st.text_input("📌 Tiêu đề cuộc họp / thông báo")
            rc1,rc2=st.columns(2)
            with rc1: r_time=st.text_input("⏰ Thời gian","")
            with rc2: r_place=st.text_input("📍 Địa điểm","")

            # Tag người tham gia (user + khách)
            st.write("👥 **Người tham gia:**")
            r_users=st.multiselect("Chọn từ danh sách user",all_usernames)
            r_guests=st.text_input("Khách mời không phải user (cách nhau bởi dấu phẩy)","")
            r_body=st.text_area("📝 Nội dung Recap / Thông báo",height=200)

            if st.form_submit_button("📤 ĐĂNG RECAP",use_container_width=True) and r_title.strip():
                guest_list=[g.strip() for g in r_guests.split(",") if g.strip()]
                all_parts=r_users+guest_list
                # Lưu khách vào hlc_users với role='Khách' nếu chưa có
                for g in guest_list:
                    ex=run_query("SELECT uid FROM hlc_users WHERE username=%s;",(g,),fetch="one")
                    if not ex:
                        run_query("INSERT INTO hlc_users (username,password,role) VALUES (%s,'',\'Khách\');",(g,),commit=True)
                run_query("""
                    INSERT INTO hlc_recaps (title,meeting_time,location,participants,content,created_by,created_at)
                    VALUES (%s,%s,%s,%s::jsonb,%s,%s,NOW());
                """,(r_title,r_time,r_place,json.dumps(all_parts),r_body,st.session_state.username),commit=True)
                push_notif(st.session_state.username,"TẠO RECAP",r_title,
                           f"Địa điểm: {r_place} | Tham gia: {', '.join(all_parts[:3])}{'...' if len(all_parts)>3 else ''}")
                st.toast("📤 Đã đăng Recap!",icon="✅"); st.rerun()

    with rt1:
        recaps=run_query("SELECT * FROM hlc_recaps ORDER BY created_at DESC LIMIT 50;") or []
        if not recaps:
            st.info("Chưa có recap nào. Tạo recap đầu tiên ở tab bên phải.")
        for rec in recaps:
            parts=safe_json(rec.get('participants',[]))
            ts=rec['created_at']
            if isinstance(ts,datetime.datetime): ts=ts.strftime('%d/%m/%Y %H:%M')
            parts_str=", ".join(parts[:5])+("..." if len(parts)>5 else "")
            st.markdown(f"""
            <div class="recap-card">
                <div class="recap-title">📋 {rec['title']}</div>
                <div class="recap-meta">
                    ⏰ {rec.get('meeting_time') or '—'} &nbsp;|&nbsp;
                    📍 {rec.get('location') or '—'} &nbsp;|&nbsp;
                    👥 {parts_str or '—'} &nbsp;|&nbsp;
                    🖊️ {rec.get('created_by','?')} · {ts}
                </div>
            </div>""",unsafe_allow_html=True)
            with st.expander("Xem nội dung & Chỉnh sửa"):
                st.text_area("Nội dung",value=rec.get('content',''),height=150,disabled=True,key=f"rc_body_{rec['id']}")
                ra,rb=st.columns(2)
                with ra:
                    if st.button("✏️ Chỉnh sửa",key=f"rc_ed_{rec['id']}",use_container_width=True):
                        st.session_state.editing_recap_id=rec['id']; st.rerun()
                with rb:
                    if st.session_state.role=="Admin":
                        if st.button("🗑️ Xoá",key=f"rc_del_{rec['id']}",use_container_width=True):
                            run_query("DELETE FROM hlc_recaps WHERE id=%s;",(rec['id'],),commit=True)
                            push_notif(st.session_state.username,"XOÁ RECAP",rec['title'])
                            st.rerun()

# ====================================================================
# TAB 2: QUẢN LÝ NHÂN SỰ (Admin)
# ====================================================================
if st.session_state.role=="Admin" and len(tabs)>2:
    with tabs[2]:
        st.markdown("#### 👥 QUẢN LÝ NHÂN SỰ")

        # Nếu đang xem chi tiết user
        if st.session_state.viewing_user:
            u_info=run_query("SELECT * FROM hlc_users WHERE username=%s;",
                             (st.session_state.viewing_user,),fetch="one")
            if u_info:
                u_tasks=run_query("SELECT * FROM team_tasks WHERE assignee=%s ORDER BY deadline_date DESC LIMIT 20;",
                                  (st.session_state.viewing_user,)) or []
                st.markdown(f"### 👤 Hồ Sơ: **{u_info['username']}**")
                i1,i2,i3=st.columns(3)
                with i1: st.metric("Vai trò",u_info.get('role','?'))
                with i2: st.metric("Task đang làm",sum(1 for t in u_tasks if t['status']=='Doing' and not t['is_closed']))
                with i3: st.metric("Task quá hạn",sum(1 for t in u_tasks if not t['is_closed'] and t['status']!='Done'
                                                        and t['deadline_date'] and strip_tz(t['deadline_date'])<today_dt))
                st.code(f"UID: {u_info.get('uid','?')}")

                st.markdown("##### ✏️ Chỉnh sửa tài khoản")
                with st.form(f"edit_user_{u_info['username']}"):
                    new_role=st.selectbox("Vai trò",["Member","Admin","Manager","Khách"],
                                          index=["Member","Admin","Manager","Khách"].index(u_info.get('role','Member'))
                                          if u_info.get('role') in ["Member","Admin","Manager","Khách"] else 0)
                    new_pw=st.text_input("Đặt mật khẩu mới (để trống = giữ nguyên)",type="password")
                    eu1,eu2=st.columns(2)
                    with eu1:
                        if st.form_submit_button("💾 Cập nhật",use_container_width=True):
                            run_query("UPDATE hlc_users SET role=%s WHERE username=%s;",
                                      (new_role,u_info['username']),commit=True)
                            if new_pw.strip():
                                run_query("UPDATE hlc_users SET password=%s WHERE username=%s;",
                                          (new_pw,u_info['username']),commit=True)
                            push_notif(st.session_state.username,"CẬP NHẬT USER",u_info['username'],f"Role → {new_role}")
                            st.success("✅ Đã cập nhật!"); st.rerun()
                    with eu2:
                        if st.form_submit_button("🗑️ Xoá tài khoản",use_container_width=True):
                            run_query("DELETE FROM hlc_users WHERE username=%s;",(u_info['username'],),commit=True)
                            push_notif(st.session_state.username,"XOÁ USER",u_info['username'])
                            st.session_state.viewing_user=None; st.rerun()

                st.markdown("##### 📋 Task của nhân sự này")
                for t in u_tasks:
                    dl=strip_tz(t['deadline_date'])
                    ov=not t['is_closed'] and t['status']!='Done' and dl and dl<today_dt
                    s=t['status'] or "To-do"
                    color={"Done":"#10b981","Doing":"#f59e0b"}.get(s,"#64748b")
                    if ov: color="#ef4444"
                    st.markdown(f"<div style='padding:5px 10px;margin-bottom:4px;border-left:3px solid {color};"
                                f"background:var(--bg-card);border-radius:4px;font-size:12px;'>"
                                f"<b style='color:var(--text-primary);'>{t['task_name']}</b> "
                                f"<span style='color:var(--text-muted);'>· {dl.strftime('%d/%m/%Y') if dl else '—'}</span>"
                                f"</div>",unsafe_allow_html=True)
                if st.button("← Quay lại danh sách",key="back_usr"):
                    st.session_state.viewing_user=None; st.rerun()
        else:
            # DANH SÁCH USER – Windows style qua components.html
            rows_html=""
            for u in users_db:
                init=(u['username'][0] if u['username'] else "?").upper()
                rl=u['role'] or "Member"
                rcls="role-admin" if rl=="Admin" else ("role-manager" if rl=="Manager" else "role-member")
                uid_s=str(u['uid'])[:22]+"…" if len(str(u['uid']))>22 else str(u['uid'])
                rows_html+=f"""
                <div class="win-row">
                  <div class="win-avatar">{init}</div>
                  <div class="win-name">{u['username']}</div>
                  <span class="win-role-badge {rcls}">{rl}</span>
                  <div class="win-uid">{uid_s}</div>
                </div>"""

            panel_html=f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
              body{{margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:transparent;}}
              .win-panel{{border:1px solid #2d3f5c;border-radius:6px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,.35);}}
              .win-titlebar{{background:linear-gradient(90deg,#1e3a5f,#2563eb);padding:7px 14px;
                display:flex;align-items:center;justify-content:space-between;
                font-size:13px;font-weight:700;color:#fff;user-select:none;}}
              .win-dots{{display:flex;gap:5px;}}
              .win-dot{{width:13px;height:13px;border-radius:50%;}}
              .d-r{{background:#ff5f56;}} .d-y{{background:#ffbd2e;}} .d-g{{background:#27c93f;}}
              .win-header{{display:flex;align-items:center;gap:10px;padding:6px 12px;
                background:#131e30;font-size:11px;font-weight:700;color:#647a99;border-bottom:1px solid #2d3f5c;}}
              .win-row{{display:flex;align-items:center;gap:10px;padding:7px 12px;
                border-bottom:1px solid #2d3f5c;font-size:13px;color:#e2e8f4;transition:background .15s;}}
              .win-row:last-child{{border-bottom:none;}}
              .win-row:hover{{background:rgba(56,189,248,.08);}}
              .win-avatar{{width:30px;height:30px;border-radius:50%;flex-shrink:0;
                background:linear-gradient(135deg,#2563eb,#38bdf8);
                display:flex;align-items:center;justify-content:center;
                font-size:13px;font-weight:700;color:#fff;}}
              .win-name{{flex:2;font-weight:600;color:#e2e8f4;}}
              .win-role-badge{{display:inline-block;padding:2px 10px;border-radius:3px;font-size:11px;font-weight:700;flex-shrink:0;width:72px;text-align:center;}}
              .role-admin{{background:#0f2a4a;color:#38bdf8;border:1px solid #2563eb;}}
              .role-member{{background:#052e20;color:#34d399;border:1px solid #10b981;}}
              .role-manager{{background:#2d1b69;color:#c4b5fd;border:1px solid #8b5cf6;}}
              .win-uid{{flex:3;font-size:11px;color:#647a99;font-family:monospace;}}
            </style></head><body>
            <div class="win-panel">
              <div class="win-titlebar">
                <span>🖥️ HLC User Manager &mdash; {len(users_db)} tài khoản</span>
                <div class="win-dots"><div class="win-dot d-r"></div><div class="win-dot d-y"></div><div class="win-dot d-g"></div></div>
              </div>
              <div class="win-header">
                <div style="width:30px;"></div><div style="flex:2;">Tên đăng nhập</div>
                <div style="width:72px;">Vai trò</div><div style="flex:3;">UID</div>
              </div>
              {rows_html}
            </div></body></html>"""

            ph=44+34+len(users_db)*46+20
            components.html(panel_html,height=ph,scrolling=False)

            st.markdown("---")
            st.markdown("##### 🔍 Xem chi tiết / Chỉnh sửa nhân sự")
            sel_view=st.selectbox("Chọn nhân sự để xem",["— Chọn —"]+all_usernames,key="sel_usr_view")
            if st.button("👤 Xem chi tiết",key="view_usr_btn",use_container_width=False):
                if sel_view!="— Chọn —":
                    st.session_state.viewing_user=sel_view; st.rerun()

            st.markdown("---")
            c_add,c_pw=st.columns(2)
            with c_add:
                with st.expander("➕ Thêm tài khoản mới"):
                    with st.form("add_user"):
                        nu=st.text_input("Username mới")
                        np=st.text_input("Password",type="password")
                        nr=st.selectbox("Vai trò",["Member","Admin","Manager","Khách"])
                        if st.form_submit_button("Tạo tài khoản",use_container_width=True) and nu.strip():
                            run_query("INSERT INTO hlc_users (username,password,role) VALUES (%s,%s,%s);",(nu.strip(),np,nr),commit=True)
                            push_notif(st.session_state.username,"TẠO USER",nu.strip(),f"Role: {nr}")
                            st.success(f"✅ Đã tạo: {nu}"); st.rerun()
            with c_pw:
                with st.expander("🔑 Đổi mật khẩu nhanh"):
                    with st.form("chg_pw"):
                        su=st.selectbox("Chọn user",all_usernames)
                        pw=st.text_input("Mật khẩu mới",type="password")
                        if st.form_submit_button("Cập nhật",use_container_width=True) and pw.strip():
                            run_query("UPDATE hlc_users SET password=%s WHERE username=%s;",(pw,su),commit=True)
                            push_notif(st.session_state.username,"ĐỔI MẬT KHẨU",su)
                            st.success(f"✅ Đã đổi mật khẩu cho: {su}")
