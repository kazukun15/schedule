import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, date, timedelta

# セッションステート初期化（ユーザー認証・Todo・ページ切替用）
if "users" not in st.session_state:
    st.session_state.users = {}  # {username: {"password": ...}}
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "page" not in st.session_state:
    st.session_state.page = "login"  # "login" or "register" or "main"
if "todos" not in st.session_state:
    st.session_state.todos = []  # Todo リスト（例：リストの各要素は文字列）

# --- ユーザー認証用ページ ---
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

# --- メインページ（カレンダー中心の画面） ---
def main_page():
    # ヘッダー：タイトルとログアウトボタン
    st.title("海光園スケジュールシステム")
    st.sidebar.button("ログアウト", on_click=logout)

    # サイドバー：本日の Todo 管理
    st.sidebar.header("本日の Todo")
    # Todo 追加フォーム（シンプルな入力）
    with st.sidebar.form("todo_form"):
        todo_title = st.text_input("Todo のタイトル")
        submitted = st.form_submit_button("Todo 追加")
        if submitted and todo_title:
            st.session_state.todos.append(todo_title)
            st.success("Todo を追加しました。")
    st.sidebar.markdown("#### Todo 一覧")
    if st.session_state.todos:
        for i, todo in enumerate(st.session_state.todos):
            st.sidebar.write(f"- {todo}")
            # Todo 完了ボタン（クリックすると Todo と同じタイトルのイベントを削除）
            if st.sidebar.button(f"完了 {i}", key=f"complete_{i}"):
                # 削除：Todo を削除
                st.session_state.todos.pop(i)
                # ※本サンプルでは「同じタイトルのイベント削除」は実装していません
                st.experimental_rerun()
    else:
        st.sidebar.info("Todo はありません。")

    # メインエリア：カレンダー
    st.markdown("### カレンダー")
    # ここでは FullCalendar を埋め込む
    html_calendar = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset='utf-8' />
      <title>FullCalendar Demo</title>
      <link href='https://cdn.jsdelivr.net/npm/fullcalendar@5.10.1/main.min.css' rel='stylesheet' />
      <script src='https://cdn.jsdelivr.net/npm/fullcalendar@5.10.1/main.min.js'></script>
      <style>
        body {{
          margin: 0; padding: 0; font-family: Arial, sans-serif;
        }}
        #calendar {{
          max-width: 900px;
          margin: 20px auto;
        }}
      </style>
    </head>
    <body>
      <div id='calendar'></div>
      <script>
        document.addEventListener('DOMContentLoaded', function() {{
          var calendarEl = document.getElementById('calendar');
          var calendar = new FullCalendar.Calendar(calendarEl, {{
            initialView: 'dayGridMonth',
            selectable: true,
            editable: true,
            // サンプルイベント（実際はサーバー連携などで動的に生成）
            events: [
              // 例: {{ id: 1, title: "会議", start: "{(date.today()).isoformat()}T09:00:00", end: "{(date.today()).isoformat()}T10:00:00" }}
            ],
            dateClick: function(info) {{
              // 日付クリックで簡単なイベント追加プロンプト
              var title = prompt("イベントタイトルを入力してください", "新規イベント");
              if(title){{
                var start = info.date;
                var end = new Date(start.getTime() + 60*60*1000); // 1時間後
                var newEvent = {{
                  id: Date.now(),
                  title: title,
                  start: start.toISOString(),
                  end: end.toISOString()
                }};
                calendar.addEvent(newEvent);
                // ※このサンプルは localStorage 等で保存していません
              }}
            }},
            eventDrop: function(info) {{
              // ドラッグ後の更新処理（ここではアラート表示のみ）
              alert("イベント移動: " + info.event.title);
            }},
            eventResize: function(info) {{
              alert("イベントリサイズ: " + info.event.title);
            }},
            eventClick: function(info) {{
              if(confirm("このイベントを削除しますか？")){
                info.event.remove();
              }}
            }}
          }});
          calendar.render();
        }});
      </script>
    </body>
    </html>
    """
    components.html(html_calendar, height=700)

def logout():
    st.session_state.current_user = None
    st.session_state.page = "login"

# --- ページ表示の制御 ---
if st.session_state.current_user is None:
    if st.session_state.page == "register":
        register_page()
    else:
        login_page()
else:
    main_page()
