import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, date, timedelta

# 日本の祝日リスト（例: 2024年）
JAPANESE_HOLIDAYS = ["2024-01-01", "2024-02-11", "2024-02-23", "2024-03-20", "2024-04-29", 
                      "2024-05-03", "2024-05-04", "2024-05-05", "2024-07-17", "2024-08-11",
                      "2024-09-18", "2024-09-23", "2024-10-09", "2024-11-03", "2024-11-23", "2024-12-23"]

# セッション変数の初期化
if "users" not in st.session_state:
    st.session_state.users = {}  # ユーザー管理
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "page" not in st.session_state:
    st.session_state.page = "login"  # "login" or "register" or "main"
if "events" not in st.session_state:
    st.session_state.events = []  # イベント管理リスト

# --- ログインページ ---
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

# --- アカウント作成ページ ---
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

# --- ログアウト処理 ---
def logout():
    st.session_state.current_user = None
    st.session_state.page = "login"

# --- メインページ ---
def main_page():
    st.title("海光園スケジュールシステム")
    st.sidebar.button("ログアウト", on_click=logout)

    # カレンダー
    st.markdown("### カレンダー")
    
    # FullCalendar の HTML
    html_calendar = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset='utf-8' />
      <link href='https://cdn.jsdelivr.net/npm/fullcalendar@5.10.1/main.min.css' rel='stylesheet' />
      <script src='https://cdn.jsdelivr.net/npm/fullcalendar@5.10.1/main.min.js'></script>
      <style>
        body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
        #calendar { max-width: 900px; margin: 20px auto; }
        .fc-day-sat { background-color: #ABE1FA !important; } /* 土曜日の背景色 */
        .fc-day-sun, .fc-day-holiday { background-color: #F9C1CF !important; } /* 日曜・祝日 */
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
            dayCellDidMount: function(info) {
              var d = info.date.toISOString().split('T')[0];
              var holidays = %s;
              if (info.date.getDay() === 6) { info.el.classList.add('fc-day-sat'); }
              if (info.date.getDay() === 0 || holidays.includes(d)) { info.el.classList.add('fc-day-sun', 'fc-day-holiday'); }
            },
            events: %s, 
            dateClick: function(info) {
              var title = prompt("イベントタイトルを入力してください", "新規イベント");
              if(title) {
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
              var newTitle = prompt("イベントを編集してください", info.event.title);
              if (newTitle !== null) {
                info.event.setProp("title", newTitle);
              }
              if (confirm("このイベントを削除しますか？")) {
                info.event.remove();
              }
            }
          });
          calendar.render();
        });
      </script>
    </body>
    </html>
    """ % (JAPANESE_HOLIDAYS, str([e for e in st.session_state.events]))
    
    components.html(html_calendar, height=700)

# --- ページ制御 ---
if st.session_state.current_user is None:
    if st.session_state.page == "register":
        register_page()
    else:
        login_page()
else:
    main_page()
