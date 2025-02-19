import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, date, timedelta

# セッション初期化（簡易ユーザー認証・Todo・イベント管理）
if "users" not in st.session_state:
    st.session_state.users = {}  # {username: {"password": ..., "department": ...}}
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "page" not in st.session_state:
    st.session_state.page = "login"  # login, register, main
if "events" not in st.session_state:
    st.session_state.events = []  # 各イベントは dict: {id, date, start, end, title, description, user}
if "todos" not in st.session_state:
    st.session_state.todos = []   # 各 Todo は dict: {id, date, title, completed, user}

# --- ユーザー認証関連 ---
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
            st.success("アカウント作成に成功しました。ログインしてください。")
            st.session_state.page = "login"
    if st.button("ログインページへ"):
        st.session_state.page = "login"

def logout():
    st.session_state.current_user = None
    st.session_state.page = "login"

# --- メインページ（カレンダー中心） ---
def main_page():
    st.title("海光園スケジュールシステム")
    st.sidebar.button("ログアウト", on_click=logout)

    # サイドバー：本日の Todo 管理
    st.sidebar.header("本日の Todo")
    with st.sidebar.form("todo_form"):
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
            st.experimental_rerun()
    st.sidebar.markdown("#### Todo 一覧")
    if st.session_state.todos:
        for i, todo in enumerate([t for t in st.session_state.todos if t["user"]==st.session_state.current_user and t["date"]==date.today() and not t["completed"]]):
            st.sidebar.write(f"- {todo['title']}")
            if st.sidebar.button(f"完了 {i}", key=f"complete_{i}"):
                st.session_state.todos = [t for t in st.session_state.todos if t["id"] != todo["id"]]
                # ここで、Todo 完了時に同じタイトルのイベントを削除する処理
                st.session_state.events = [e for e in st.session_state.events if not (e["title"]==todo["title"] and e["user"]==st.session_state.current_user and e["date"]==date.today())]
                st.success("Todo 完了")
                st.experimental_rerun()
    else:
        st.sidebar.info("Todo はありません。")

    # カレンダーエリア：ここでは st.components.v1.html を利用して FullCalendar を埋め込む
    st.markdown("### カレンダー")
    # 選択日（カレンダーで扱う日付、ここではシンプルに入力する）
    selected_date = st.date_input("日付を選択", value=date.today())
    # HTML/JS で FullCalendar を埋め込む（※実際はサーバー連携が必要な部分ですが、ここではシンプルなデモ）
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
            events: %s, 
            dateClick: function(info) {
              var title = prompt("イベントタイトルを入力してください", "新規イベント");
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
                // Streamlit 側へは連携していません（このデモはローカル状態のみ）
              }
            },
            eventDrop: function(info) {
              alert("イベント移動: " + info.event.title);
            },
            eventResize: function(info) {
              alert("イベントリサイズ: " + info.event.title);
            },
            eventClick: function(info) {
              if(confirm("このイベントを削除しますか？")){
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
    """ % (str([e for e in st.session_state.events if e["user"]==st.session_state.current_user and e["date"]==selected_date]))
    # 注意：上記は簡易的にセッションのイベントリストを JSON 風に出力しているだけなので、実際は適切な変換が必要です
    components.html(html_calendar, height=700)

# ページ制御
if st.session_state.current_user is None:
    if st.session_state.page == "register":
        register_page()
    else:
        login_page()
else:
    main_page()
