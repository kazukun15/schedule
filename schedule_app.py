import streamlit as st
from datetime import datetime, date, timedelta

# セッションステートの初期化
if "users" not in st.session_state:
    st.session_state.users = {}  # {username: {"password": ..., "department": ...}}
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "events" not in st.session_state:
    st.session_state.events = []  # 各イベントは dict: {id, date, start, end, title, description, user}
if "todos" not in st.session_state:
    st.session_state.todos = []   # 各 Todo は dict: {id, date, title, completed, user}
if "page" not in st.session_state:
    st.session_state.page = "login"  # login, register, main

# ユーザー認証関連
def login_page():
    st.title("ログイン")
    username = st.text_input("ユーザー名")
    password = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        if username in st.session_state.users and st.session_state.users[username]["password"] == password:
            st.session_state.current_user = username
            st.success("ログイン成功！")
            st.session_state.page = "main"
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

# メイン画面
def main_page():
    st.title("海光園スケジュールシステム")
    st.sidebar.button("ログアウト", on_click=logout)

    # 選択日 (カレンダーの代替として日付選択)
    selected_date = st.date_input("日付を選択", value=date.today())

    st.markdown("### 予定一覧")
    # ログインユーザーかつ選択日のイベント一覧
    events = [e for e in st.session_state.events if e["user"] == st.session_state.current_user and e["date"] == selected_date]
    if events:
        for event in events:
            st.write(f"【{event['start'].strftime('%H:%M')}～{event['end'].strftime('%H:%M')}】 {event['title']}")
            if st.button("削除", key=f"del_event_{event['id']}"):
                st.session_state.events = [e for e in st.session_state.events if e["id"] != event["id"]]
                st.success("イベント削除")
                st.experimental_rerun()
    else:
        st.info("この日の予定はありません。")

    st.markdown("---")
    st.markdown("### 新規イベント追加")
    with st.form("event_form"):
        event_title = st.text_input("タイトル")
        event_start_time = st.time_input("開始時刻", value=datetime.now().time().replace(second=0, microsecond=0))
        start_dt = datetime.combine(selected_date, event_start_time)
        default_end = (start_dt + timedelta(hours=1)).time()
        event_end_time = st.time_input("終了時刻", value=default_end)
        event_description = st.text_area("説明", height=100)
        submitted = st.form_submit_button("保存")
        if submitted:
            if not event_title:
                st.error("タイトルは必須です。")
            else:
                new_event = {
                    "id": int(datetime.now().timestamp() * 1000),
                    "date": selected_date,
                    "start": datetime.combine(selected_date, event_start_time),
                    "end": datetime.combine(selected_date, event_end_time),
                    "title": event_title,
                    "description": event_description,
                    "user": st.session_state.current_user
                }
                st.session_state.events.append(new_event)
                st.success("イベントが保存されました。")
                st.experimental_rerun()

    st.markdown("---")
    st.markdown("### 本日の Todo")
    # ここでは、Todo をカレンダーの横に配置するために、2カラムレイアウトを使用
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Todo 一覧")
        todos = [t for t in st.session_state.todos if t["user"] == st.session_state.current_user and t["date"] == selected_date and not t["completed"]]
        if todos:
            for todo in todos:
                st.write(f"- {todo['title']}")
        else:
            st.info("Todo はありません。")
    with col2:
        st.markdown("#### Todo 追加")
        with st.form("todo_form"):
            todo_title = st.text_input("Todo のタイトル")
            todo_submitted = st.form_submit_button("追加")
            if todo_submitted:
                if not todo_title:
                    st.error("Todo のタイトルは必須です。")
                else:
                    new_todo = {
                        "id": int(datetime.now().timestamp() * 1000),
                        "date": selected_date,
                        "title": todo_title,
                        "completed": False,
                        "user": st.session_state.current_user
                    }
                    st.session_state.todos.append(new_todo)
                    # 同時に、Todo と同じ内容のイベントを自動作成（例: 09:00～10:00）
                    start_dt = datetime.combine(selected_date, datetime.strptime("09:00", "%H:%M").time())
                    end_dt = start_dt + timedelta(hours=1)
                    new_event = {
                        "id": int(datetime.now().timestamp() * 1000) + 1,
                        "date": selected_date,
                        "start": start_dt,
                        "end": end_dt,
                        "title": todo_title,
                        "description": "",
                        "user": st.session_state.current_user
                    }
                    st.session_state.events.append(new_event)
                    st.success("Todo とイベントを追加しました。")
                    st.experimental_rerun()

    st.markdown("---")
    st.markdown("### Todo 完了")
    # Todo 完了ボタン：完了すると Todo を完了状態にし、同じタイトルのイベントを削除する
    complete_todos = [t for t in st.session_state.todos if t["user"] == st.session_state.current_user and t["date"] == selected_date and not t["completed"]]
    if complete_todos:
        for todo in complete_todos:
            if st.button(f"完了: {todo['title']}", key=f"complete_{todo['id']}"):
                # マーク完了
                for t in st.session_state.todos:
                    if t["id"] == todo["id"]:
                        t["completed"] = True
                # 同じタイトルのイベント（本日のもの）を削除
                st.session_state.events = [e for e in st.session_state.events if not (e["title"] == todo["title"] and e["date"] == selected_date and e["user"] == st.session_state.current_user)]
                st.success("Todo を完了しました。")
                st.experimental_rerun()
    else:
        st.info("完了する Todo はありません。")

# ページ遷移の処理
if st.session_state.current_user is None:
    if st.session_state.page == "register":
        register_page()
    else:
        login_page()
else:
    main_page()
