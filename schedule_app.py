import streamlit as st
import streamlit.components.v1 as components
import json
import jpholiday
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ---------------------------
# データベース設定 (SQLite)
# ---------------------------
engine = create_engine("sqlite:///data.db", connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

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

class Todo(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    date = Column(Date, nullable=False, default=date.today)
    completed = Column(Boolean, default=False)
    owner_id = Column(Integer, nullable=False)

Base.metadata.create_all(bind=engine)

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
st.session_state.setdefault("page", "login")  # login, register, main

# ---------------------------
# ヘルパー関数（DB操作）
# ---------------------------
def get_user(username):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    return user

def create_user(username, password, department):
    db = SessionLocal()
    user = User(username=username, password=password, department=department)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

def add_event_to_db(title, start_time, end_time, description, owner_id):
    db = SessionLocal()
    ev = Event(title=title, start_time=start_time, end_time=end_time, description=description, owner_id=owner_id)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    db.close()
    return ev

def get_events_from_db(owner_id, target_date):
    db = SessionLocal()
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())
    events = db.query(Event).filter(Event.owner_id == owner_id, Event.start_time >= start_of_day, Event.start_time <= end_of_day).all()
    db.close()
    return events

def delete_event_from_db(event_id, owner_id):
    db = SessionLocal()
    ev = db.query(Event).filter(Event.id == event_id, Event.owner_id == owner_id).first()
    if ev:
        db.delete(ev)
        db.commit()
        db.close()
        return True
    db.close()
    return False

def add_todo_to_db(title, owner_id):
    db = SessionLocal()
    t = Todo(title=title, date=date.today(), completed=False, owner_id=owner_id)
    db.add(t)
    db.commit()
    db.refresh(t)
    db.close()
    return t

def get_todos_from_db(owner_id, target_date):
    db = SessionLocal()
    todos = db.query(Todo).filter(Todo.owner_id == owner_id, Todo.date == target_date, Todo.completed == False).all()
    db.close()
    return todos

def complete_todo_in_db(todo_id, owner_id):
    db = SessionLocal()
    todo = db.query(Todo).filter(Todo.id == todo_id, Todo.owner_id == owner_id).first()
    if todo:
        todo.completed = True
        db.commit()
        db.close()
        return True
    db.close()
    return False

def get_holidays_for_month(target_date):
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
        if get_user(username):
            st.error("このユーザー名は既に存在します。")
        else:
            create_user(username, password, department)
            st.success("アカウント作成に成功しました。ログインしてください。")
            st.session_state.page = "login"
    if st.button("ログインページへ"):
        st.session_state.page = "login"

def logout_ui():
    st.session_state.current_user = None
    st.session_state.page = "login"

# ---------------------------
# Streamlit UI: メインページ
# ---------------------------
def main_page():
    st.title("海光園スケジュールシステム")
    st.sidebar.button("ログアウト", on_click=logout_ui)
    
    # サイドバー: イベント入力フォーム（予定入力をサイドバーに配置）
    st.sidebar.markdown("### 新規予定追加")
    with st.sidebar.form("event_form"):
        event_title = st.text_input("予定（イベント）タイトル")
        event_start_date = st.date_input("開始日", value=date.today(), key="start_date")
        event_end_date = st.date_input("終了日", value=date.today(), key="end_date")
        all_day = st.checkbox("終日", value=False)
        if not all_day:
            event_start_time = st.time_input("開始時刻", value=datetime.now().time().replace(second=0, microsecond=0))
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
                    event_title,
                    datetime.combine(event_start_date, event_start_time),
                    datetime.combine(event_end_date, event_end_time),
                    event_description,
                    st.session_state.current_user.id
                )
                st.success("予定が保存されました。")
                # 再描画は自動更新に任せる

    # サイドバー: Todo 管理
    st.sidebar.markdown("### 本日の Todo")
    with st.sidebar.form("todo_form"):
        todo_title = st.text_input("Todo のタイトル")
        if st.form_submit_button("Todo 追加") and todo_title:
            add_todo_to_db(todo_title, st.session_state.current_user.id)
            st.success("Todo を追加しました。")
    st.sidebar.markdown("#### Todo 一覧")
    todos = get_todos_from_db(st.session_state.current_user.id, date.today())
    if todos:
        for i, todo in enumerate(todos):
            st.sidebar.write(f"- {todo.title}")
            if st.sidebar.button(f"完了 {i}", key=f"complete_{i}"):
                complete_todo_in_db(todo.id, st.session_state.current_user.id)
                # 同じタイトルの予定（本日のもの）を削除
                db = SessionLocal()
                db.query(Event).filter(
                    Event.owner_id == st.session_state.current_user.id,
                    func.date(Event.start_time) == date.today(),
                    Event.title == todo.title
                ).delete()
                db.commit()
                db.close()
                st.success("Todo 完了")
    else:
        st.sidebar.info("Todo はありません。")
    
    # メインエリア: カレンダー表示
    st.markdown("### カレンダー")
    target_date = date.today()
    holidays = get_holidays_for_month(target_date)
    events_json = serialize_events(st.session_state.current_user.id, target_date)
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
        .fc-event-title { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 0.8rem; }
        .fc-event-time { font-size: 0.7rem; }
      </style>
    </head>
    <body>
      <div id='calendar'></div>
      <script>
        function formatLocalDate(d) {
          var year = d.getFullYear();
          var month = ("0" + (d.getMonth()+1)).slice(-2);
          var day = ("0" + d.getDate()).slice(-2);
          return year + "-" + month + "-" + day;
        }
        document.addEventListener('DOMContentLoaded', function() {
          var holidays = %s;
          var calendarEl = document.getElementById('calendar');
          var calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            selectable: true,
            editable: true,
            height: 'auto',
            events: %s,
            dayCellDidMount: function(info) {
              var dStr = formatLocalDate(info.date);
              if(info.date.getDay() === 6){
                info.el.style.backgroundColor = "#ABE1FA";
              }
              if(info.date.getDay() === 0 || holidays.indexOf(dStr) !== -1){
                info.el.style.backgroundColor = "#F9C1CF";
              }
            },
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
              if(confirm("この予定を削除しますか？")){
                info.event.remove();
              }
            },
            eventContent: function(arg) {
              var startTime = FullCalendar.formatDate(arg.event.start, {hour: '2-digit', minute: '2-digit'});
              var endTime = FullCalendar.formatDate(arg.event.end, {hour: '2-digit', minute: '2-digit'});
              var timeEl = document.createElement('div');
              timeEl.style.fontSize = '0.7rem';
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
    """ % (json.dumps(holidays), events_json)
    components.html(html_calendar, height=700)

if st.session_state.current_user is None:
    if st.session_state.page == "register":
        register_page()
    else:
        login_page()
else:
    main_page()
