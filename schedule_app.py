import streamlit as st
import streamlit.components.v1 as components
import json
import jpholiday
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from streamlit_autorefresh import st_autorefresh

# ---------------------------
# 自動更新（10秒ごと）
# ---------------------------
st_autorefresh(interval=10000, limit=100, key="event_refresh")

# ---------------------------
# データベース設定 (SQLite)
# ---------------------------
engine = create_engine("sqlite:///data.db", connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# テーブル定義
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # ※実際はハッシュ化すべき
    department = Column(String)

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    description = Column(String)
    owner_id = Column(Integer, nullable=False)
    deleted = Column(Boolean, default=False)  # 疑似削除用フラグ

class Todo(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    date = Column(Date, nullable=False, default=date.today)
    completed = Column(Boolean, default=False)
    owner_id = Column(Integer, nullable=False)

Base.metadata.create_all(bind=engine)

# DBセッションを取得するヘルパー関数（コンテキストマネージャ版）
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------
# Streamlit セッション初期化
# ---------------------------
st.session_state.setdefault("current_user", None)
st.session_state.setdefault("page", "login")  # "login", "register", "main"

# ---------------------------
# ヘルパー関数（DB操作）
# ---------------------------
def get_user(username):
    with SessionLocal() as db:
        return db.query(User).filter(User.username == username).first()

def create_user(username, password, department):
    """ユーザー作成（パスワードは実運用ではハッシュ化推奨）"""
    with SessionLocal() as db:
        user = User(username=username, password=password, department=department)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

def add_event_to_db(title, start_time, end_time, description, owner_id):
    with SessionLocal() as db:
        ev = Event(
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            owner_id=owner_id,
            deleted=False
        )
        db.add(ev)
        db.commit()
        db.refresh(ev)
        return ev

def get_events_from_db(owner_id, target_date):
    """対象日をまたぐイベントも含めて取得 (deleted=Falseのみ)"""
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())
    with SessionLocal() as db:
        events = db.query(Event).filter(
            Event.owner_id == owner_id,
            Event.deleted == False,
            Event.start_time <= end_of_day,
            Event.end_time >= start_of_day
        ).all()
        return events

def complete_event_in_db(event_id, owner_id):
    """
    イベントを「完了」として処理する。
    今回はソフトデリート（deleted=True）のみ実施。
    """
    with SessionLocal() as db:
        ev = db.query(Event).filter(
            Event.id == event_id,
            Event.owner_id == owner_id
        ).first()
        if ev:
            ev.deleted = True
            db.commit()
            return True
        return False

def add_todo_to_db(title, owner_id):
    with SessionLocal() as db:
        t = Todo(title=title, date=date.today(), completed=False, owner_id=owner_id)
        db.add(t)
        db.commit()
        db.refresh(t)
        return t

def get_todos_from_db(owner_id, target_date):
    """完了していないTodoを取得"""
    with SessionLocal() as db:
        todos = db.query(Todo).filter(
            Todo.owner_id == owner_id,
            Todo.date == target_date,
            Todo.completed == False
        ).all()
        return todos

def complete_todo_in_db(todo_id, owner_id):
    """
    Todoを完了とし、completed=True に更新。
    もし必要であれば関連するEventも削除する。
    """
    with SessionLocal() as db:
        todo = db.query(Todo).filter(
            Todo.id == todo_id,
            Todo.owner_id == owner_id
        ).first()
        if todo:
            todo.completed = True
            db.commit()
            return True
        return False

def get_holidays_for_month(target_date):
    """指定月の祝日をリストで返す"""
    first_day = target_date.replace(day=1)
    if target_date.month == 12:
        next_month = target_date.replace(year=target_date.year+1, month=1, day=1)
    else:
        next_month = target_date.replace(month=target_date.month+1, day=1)
    last_day = next_month - timedelta(days=1)
    holidays = []
    d = first_day
    while d <= last_day:
        if jpholiday.is_holiday(d):
            holidays.append(d.isoformat())
        d += timedelta(days=1)
    return holidays

def serialize_events(owner_id, target_date):
    """イベントを JSON 形式に変換"""
    events = get_events_from_db(owner_id, target_date)
    evs = []
    for ev in events:
        evs.append({
            "id": ev.id,
            "title": ev.title,
            "start": ev.start_time.isoformat(),
            "end": ev.end_time.isoformat(),
            "description": ev.description
        })
    return json.dumps(evs)

# ---------------------------
# Streamlit UI: ユーザー認証
# ---------------------------
def login_page():
    st.title("ログイン")
    username = st.text_input("ユーザー名")
    password = st.text_input("パスワード", type="password")
    
    if st.button("ログイン"):
        user = get_user(username)
        if user and user.password == password:
            st.session_state.current_user = user
            st.session_state.page = "main"
            st.success("ログイン成功！")
            st.experimental_rerun()
        else:
            st.error("ユーザー名またはパスワードが正しくありません。")
    
    if st.button("アカウント作成"):
        st.session_state.page = "register"
        st.experimental_rerun()

def register_page():
    st.title("アカウント作成")
    username = st.text_input("ユーザー名", key="reg_username")
    password = st.text_input("パスワード", type="password", key="reg_password")
    department = st.text_input("部署", key="reg_department")
    
    if st.button("登録"):
        if get_user(username):
            st.error("このユーザー名は既に存在します。")
        else:
            create_user(username, password, department)
            st.success("アカウント作成に成功しました。ログインしてください。")
            st.session_state.page = "login"
            st.experimental_rerun()
    
    if st.button("ログインページへ"):
        st.session_state.page = "login"
        st.experimental_rerun()

def logout_ui():
    st.session_state.current_user = None
    st.session_state.page = "login"
    st.experimental_rerun()

# ---------------------------
# Streamlit UI: メインページ
# ---------------------------
def main_page():
    st.title("海光園スケジュールシステム")

    # 手動更新ボタン
    if st.button("更新"):
        st.experimental_rerun()

    st.sidebar.button("ログアウト", on_click=logout_ui)
    
    # サイドバー: イベント入力フォーム
    st.sidebar.markdown("### 新規予定追加")
    with st.sidebar.form("event_form"):
        event_title = st.text_input("予定（イベント）タイトル")
        event_start_date = st.date_input("開始日", value=date.today(), key="start_date")
        event_end_date = st.date_input("終了日", value=date.today(), key="end_date")
        all_day = st.checkbox("終日", value=False)
        
        if not all_day:
            event_start_time = st.time_input(
                "開始時刻",
                value=datetime.now().time().replace(second=0, microsecond=0)
            )
            start_dt = datetime.combine(event_start_date, event_start_time)
            default_end = (start_dt + timedelta(hours=1)).time()
            event_end_time = st.time_input("終了時刻", value=default_end)
        else:
            event_start_time = datetime.strptime("00:00", "%H:%M").time()
            event_end_time = datetime.strptime("23:59", "%H:%M").time()
        
        event_description = st.text_area("備考", height=100)
        
        if st.form_submit_button("保存予定"):
            if not event_title:
                st.error("予定のタイトルは必須です。")
            else:
                add_event_to_db(
                    title=event_title,
                    start_time=datetime.combine(event_start_date, event_start_time),
                    end_time=datetime.combine(event_end_date, event_end_time),
                    description=event_description,
                    owner_id=st.session_state.current_user.id
                )
                st.success("予定が保存されました。")
                st.experimental_rerun()
    
    # サイドバー: 今日の予定一覧（完了ボタン付き）
    st.sidebar.markdown("### 本日の予定一覧")
    events_today = get_events_from_db(st.session_state.current_user.id, date.today())
    if events_today:
        for ev in events_today:
            st.sidebar.write(f"{ev.title} ({ev.start_time.strftime('%H:%M')}～{ev.end_time.strftime('%H:%M')})")
            if st.sidebar.button(f"完了 (ID:{ev.id})", key=f"complete_event_{ev.id}"):
                complete_event_in_db(ev.id, st.session_state.current_user.id)
                st.success("予定を完了しました。")
                st.experimental_rerun()
    else:
        st.sidebar.info("本日の予定はありません。")
    
    # サイドバー: Todo 管理
    st.sidebar.markdown("### 本日の Todo")
    with st.sidebar.form("todo_form"):
        todo_title = st.text_input("Todo のタイトル")
        if st.form_submit_button("Todo 追加") and todo_title:
            add_todo_to_db(todo_title, st.session_state.current_user.id)
            st.success("Todo を追加しました。")
            st.experimental_rerun()
    
    st.sidebar.markdown("#### Todo 一覧")
    todos = get_todos_from_db(st.session_state.current_user.id, date.today())
    if todos:
        for i, todo in enumerate(todos):
            st.sidebar.write(f"- {todo.title}")
            if st.sidebar.button(f"完了 {i}", key=f"complete_{i}"):
                # Todoを完了にする
                complete_todo_in_db(todo.id, st.session_state.current_user.id)
                
                # Todoと同じタイトル/日付のEventも論理削除している
                # ※もしイベントとTodoを紐づけるなら別カラムなどで管理するのが望ましい
                with SessionLocal() as db:
                    db.query(Event).filter(
                        Event.owner_id == st.session_state.current_user.id,
                        func.date(Event.start_time) == date.today(),
                        Event.title == todo.title
                    ).update({Event.deleted: True})
                    db.commit()
                
                st.success("Todo を完了し、対応するイベントも削除(論理)しました。")
                st.experimental_rerun()
    else:
        st.sidebar.info("Todo はありません。")
    
    # メインエリア: カレンダー表示
    st.markdown("### カレンダー")
    target_date = date.today()
    holidays = get_holidays_for_month(target_date)
    events_json = serialize_events(st.session_state.current_user.id, target_date)
    
    # ※ dateClick で直接予定をDBに保存する処理は行っていません。
    #   以下をコメントアウトすることでクリック追加を無効化しています。
    #   もし有効にする場合は、JS → Python への連携が必要です。
    html_calendar = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset='utf-8' />
      <title>FullCalendar Demo</title>
      <link href='https://cdn.jsdelivr.net/npm/fullcalendar@5.10.1/main.min.css' rel='stylesheet' />
      <script src='https://cdn.jsdelivr.net/npm/fullcalendar@5.10.1/main.min.js'></script>
      <style>
        body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; }}
        #calendar {{ max-width: 900px; margin: 20px auto; }}
        .fc-day-sat {{ background-color: #ABE1FA !important; }}
        .fc-day-sun, .fc-day-holiday {{ background-color: #F9C1CF !important; }}
        .fc-event-title {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 0.8rem; color: #555555; }}
        .fc-event-time {{ font-size: 0.7rem; color: #555555; }}
        .fc-event-multiday {{ background-color: #D0EFFF !important; }}
      </style>
    </head>
    <body>
      <div id='calendar'></div>
      <script>
        function formatLocalDate(d) {{
          var year = d.getFullYear();
          var month = ("0" + (d.getMonth()+1)).slice(-2);
          var day = ("0" + d.getDate()).slice(-2);
          return year + "-" + month + "-" + day;
        }}
        document.addEventListener('DOMContentLoaded', function() {{
          var holidays = {json.dumps(holidays)};
          var calendarEl = document.getElementById('calendar');
          var calendar = new FullCalendar.Calendar(calendarEl, {{
            initialView: 'dayGridMonth',
            selectable: true,
            editable: true,
            dayMaxEvents: true,
            height: 'auto',
            events: {events_json},
            dayCellDidMount: function(info) {{
              var dStr = formatLocalDate(info.date);
              // 土曜日
              if(info.date.getDay() === 6){{
                info.el.style.backgroundColor = "#ABE1FA";
              }}
              // 日曜 or 祝日
              if(info.date.getDay() === 0 || holidays.indexOf(dStr) !== -1){{
                info.el.style.backgroundColor = "#F9C1CF";
              }}
            }},
            // dateClick: function(info) {{
            //   var title = prompt("予定のタイトルを入力してください", "新規予定");
            //   if(title){{
            //     var start = info.date;
            //     var end = new Date(start.getTime() + 60*60*1000);
            //     var newEvent = {{
            //       id: Date.now(),
            //       title: title,
            //       start: start.toISOString(),
            //       end: end.toISOString()
            //     }};
            //     calendar.addEvent(newEvent);
            //     alert("現在、この操作で追加された予定はDBに保存されません。サイドバーから追加してください。");
            //   }}
            // }},
            eventClick: function(info) {{
              alert("削除(完了)はサイドバーの『本日の予定一覧』から実施してください。");
            }},
            eventContent: function(arg) {{
              var startTime = FullCalendar.formatDate(arg.event.start, {{hour: '2-digit', minute: '2-digit'}});
              var endTime = FullCalendar.formatDate(arg.event.end, {{hour: '2-digit', minute: '2-digit'}});
              var timeEl = document.createElement('div');
              timeEl.style.fontSize = '0.7rem';
              timeEl.style.color = '#555555';
              timeEl.innerText = startTime + '～' + endTime;
              
              var titleEl = document.createElement('div');
              titleEl.style.fontSize = '0.8rem';
              titleEl.style.color = '#555555';
              titleEl.innerText = arg.event.title;
              
              var container = document.createElement('div');
              // マルチデイの場合の背景色を変更
              if(new Date(arg.event.start).toDateString() !== new Date(arg.event.end).toDateString()){{
                container.classList.add("fc-event-multiday");
              }}
              
              container.appendChild(timeEl);
              container.appendChild(titleEl);
              return {{ domNodes: [ container ] }};
            }}
          }});
          calendar.render();
        }});
      </script>
    </body>
    </html>
    """
    
    components.html(html_calendar, height=700)

# ---------------------------
# ページ切り替えロジック
# ---------------------------
if st.session_state.current_user is None:
    if st.session_state.page == "register":
        register_page()
    else:
        login_page()
else:
    main_page()
