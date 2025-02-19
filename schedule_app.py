import streamlit as st
import streamlit.components.v1 as components
import json
from datetime import datetime, date, timedelta

# --- セッション初期化 ---
if "users" not in st.session_state:
    st.session_state.users = {}  # {username: {"password": ..., "department": ...}}
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "page" not in st.session_state:
    st.session_state.page = "login"  # login, register, main
if "events" not in st.session_state:
    st.session_state.events = []  # 各イベント: {id, date, start, end, title, description, user}
if "todos" not in st.session_state:
    st.session_state.todos = []   # 各 Todo: {id, date, title, completed, user}

# --- ヘルパー関数 ---
def serialize_events(user, target_date):
    evs = []
    for ev in st.session_state.events:
        if ev["user"] == user and ev["date"] == target_date:
            evs.append({
                "id": ev["id"],
                "title": ev["title"],
                "start": ev["start"].isoformat(),
                "end": ev["end"].isoformat(),
                "description": ev["description"]
            })
    return json.dumps(evs)

# --- ユーザー認証 ---
def login_page():
    st.title("ログイン")
    username = st.text_input("ユーザー名")
    password = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        if username in st.session_state.users and st.session_state.users[username]["password"] == password:
            st.session_state.current_user = username
            st.session_state.page = "main"
            st.success("ログイン成功！")
        else:
            st.error("ユーザー名またはパスワードが正しくありません。")
    if st.button("アカウント作成"):
        st.session_state.page = "register"

def register_page():
    st.title("アカウント作成")
    username = st.text_input("ユーザー名", key="reg_username")
    password = st.text_input("パスワード", type="password", key="reg_password")
    department = st.text_input("部署", key="reg_department")
    if st.button("登録"):
        if username in st.session_state.users:
            st.error("このユーザー名は既に存在します。")
        else:
            st.session_state.users[username] = {"password": password, "department": department}
            st.success("アカウント作成成功！")
            st.session_state.page = "login"
    if st.button("ログインページへ"):
        st.session_state.page = "login"

def logout():
    st.session_state.current_user = None
    st.session_state.page = "login"

# --- メインページ ---
def main_page():
    st.title("海光園スケジュールシステム")
    
    # サイドバーにログアウトボタンとイベント入力フォーム、Todo 管理
    with st.sidebar:
        st.header("メニュー")
        st.button("ログアウト", on_click=logout)
        
        st.markdown("### 新規予定追加")
        with st.form("event_form"):
            event_title = st.text_input("予定タイトル")
            event_date = st.date_input("日付", value=date.today())
            event_start_time = st.time_input("開始時刻", value=datetime.now().time().replace(second=0, microsecond=0))
            start_dt = datetime.combine(event_date, event_start_time)
            default_end = (start_dt + timedelta(hours=1)).time()
            event_end_time = st.time_input("終了時刻", value=default_end)
            event_description = st.text_area("備考", height=100)
            if st.form_submit_button("保存予定"):
                if not event_title:
                    st.error("予定のタイトルは必須です。")
                else:
                    new_event = {
                        "id": int(datetime.now().timestamp() * 1000),
                        "date": event_date,
                        "start": datetime.combine(event_date, event_start_time),
                        "end": datetime.combine(event_date, event_end_time),
                        "title": event_title,
                        "description": event_description,
                        "user": st.session_state.current_user
                    }
                    st.session_state.events.append(new_event)
                    st.success("予定が保存されました。")
        
        st.markdown("### 本日の Todo")
        with st.form("todo_form"):
            todo_title = st.text_input("Todo のタイトル")
            if st.form_submit_button("Todo 追加") and todo_title:
                new_todo = {
                    "id": int(datetime.now().timestamp() * 1000),
                    "date": date.today(),
                    "title": todo_title,
                    "completed": False,
                    "user": st.session_state.current_user
                }
                st.session_state.todos.append(new_todo)
                st.success("Todo を追加しました。")
        st.markdown("#### Todo 一覧")
        current_todos = [t for t in st.session_state.todos if t["user"] == st.session_state.current_user and t["date"] == date.today() and not t["completed"]]
        if current_todos:
            for i, todo in enumerate(current_todos):
                st.write(f"- {todo['title']}")
                if st.button(f"完了 {i}", key=f"complete_{i}"):
                    st.session_state.todos = [t for t in st.session_state.todos if t["id"] != todo["id"]]
                    # 同じタイトルの予定（本日のもの）を削除
                    st.session_state.events = [e for e in st.session_state.events if not (e["title"] == todo["title"] and e["user"] == st.session_state.current_user and e["date"] == date.today())]
                    st.success("Todo 完了")
                    st.experimental_rerun()
        else:
            st.info("Todo はありません。")
    
    # メインエリア：カレンダー表示
    st.markdown("### カレンダー")
    # FullCalendar 用に、ログインユーザーの本日の予定のみを JSON 化
    events_json = serialize_events(st.session_state.current_user, date.today())
    html_calendar = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset='utf-8' />
      <title>FullCalendar Demo</title>
      <link href='https://cdn.jsdelivr.net/npm/fullcalendar@5.10.1/main.min.css' rel='stylesheet' />
      <script src='https://cdn.jsdelivr.net/npm/fullcalendar@5.10.1/main.min.js'></script>
      <style>
        body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
        #calendar { max-width: 900px; margin: 20px auto; }
        .fc-day-sat { background-color: #ABE1FA !important; }
        .fc-day-sun, .fc-day-holiday { background-color: #F9C1CF !important; }
      </style>
    </head>
    <body>
      <div id='calendar'></div>
      <script>
        document.addEventListener('DOMContentLoaded', function() {
          var calendarEl = document.getElementById('calendar');
          var calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            selectable: true,
            editable: true,
            height: 'auto',
            events: %s,
            dateClick: function(info) {
              var title = prompt("予定のタイトルを入力してください", "新規予定");
              if(title){
                var start = info.date;
                var end = new Date(start.getTime() + 60*60*1000);
                var newEvent = {
                  id: Date.now(),
                  title: title,
                  start: start.toISOString(),
                  end: end.toISOString()
                };
                calendar.addEvent(newEvent);
              }
            },
            eventClick: function(info) {
              // ダブルクリックによる編集・削除は実装は省略し、クリックで削除確認
              if(confirm("この予定を削除しますか？")){
                info.event.remove();
              }
            },
            eventContent: function(arg) {
              var startTime = FullCalendar.formatDate(arg.event.start, {hour: '2-digit', minute: '2-digit'});
              var endTime = FullCalendar.formatDate(arg.event.end, {hour: '2-digit', minute: '2-digit'});
              var timeEl = document.createElement('div');
              timeEl.style.fontSize = '0.9rem';
              timeEl.innerText = startTime + '～' + endTime;
              var titleEl = document.createElement('div');
              titleEl.style.fontSize = '0.8rem';
              titleEl.innerText = arg.event.title;
              var container = document.createElement('div');
              container.appendChild(timeEl);
              container.appendChild(titleEl);
              return { domNodes: [ container ] };
            }
          });
          calendar.render();
        });
      </script>
    </body>
    </html>
    """ % (events_json)
    components.html(html_calendar, height=700)

# --- ページ制御 ---
if st.session_state.current_user is None:
    if st.session_state.page == "register":
        register_page()
    else:
        login_page()
else:
    main_page()
