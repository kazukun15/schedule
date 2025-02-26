import streamlit as st
from datetime import datetime, date, timedelta
from sqlalchemy.orm import sessionmaker
from models import engine
from crud import (get_events_from_db, add_event_to_db, delete_event_from_db, 
                  add_todo_to_db, get_todos_from_db, complete_todo_in_db)
from utils import get_holidays_for_month, serialize_events_for_period
import json
import streamlit.components.v1 as components

SessionLocal = sessionmaker(bind=engine)

def show_main_page():
    st.title("海光園スケジュールシステム")
    # ログアウトボタン等の共通UIはここに実装
    # 新規予定追加フォーム、Todo 管理、カレンダー表示など各処理を記述
    # 元のコードの内容を必要に応じて関数化して呼び出す
    st.markdown("### カレンダー表示")
    display_date = st.date_input("カレンダー表示日", value=date.today(), key="calendar_date")
    
    first_day_of_month = display_date.replace(day=1)
    if display_date.month == 12:
        first_day_next_month = display_date.replace(year=display_date.year+1, month=1, day=1)
    else:
        first_day_next_month = display_date.replace(month=display_date.month+1, day=1)
    with SessionLocal() as db:
        events = get_events_from_db(db, st.session_state.current_user.id, date.today())
        events_json = serialize_events_for_period(events)
        holidays = get_holidays_for_month(first_day_of_month)
    
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
      </style>
    </head>
    <body>
      <div id='calendar'></div>
      <script>
        document.addEventListener('DOMContentLoaded', function() {{
          var calendarEl = document.getElementById('calendar');
          var calendar = new FullCalendar.Calendar(calendarEl, {{
            initialView: 'dayGridMonth',
            events: {events_json},
            dayCellDidMount: function(info) {{
              // 祝日や土日の背景色変更
              if(info.date.getDay() === 6)
                info.el.style.backgroundColor = "#ABE1FA";
              if(info.date.getDay() === 0 || {json.dumps(holidays)}.indexOf(info.date.toISOString().slice(0,10)) !== -1)
                info.el.style.backgroundColor = "#F9C1CF";
            }}
          }});
          calendar.render();
        }});
      </script>
    </body>
    </html>
    """
    components.html(html_calendar, height=700)
