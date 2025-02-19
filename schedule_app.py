import streamlit as st
import streamlit.components.v1 as components

st.title("Streamlit FullCalendar Demo")
st.markdown("このサンプルは、FullCalendar を st.components.v1.html で埋め込み、イベントの追加、更新、削除（ドラッグ＆ドロップ、クリックで削除）をローカルストレージで管理する例です。")

html_code = """
<!DOCTYPE html>
<html>
<head>
  <meta charset='utf-8' />
  <title>FullCalendar Demo</title>
  <link href='https://cdn.jsdelivr.net/npm/fullcalendar@5.10.1/main.min.css' rel='stylesheet' />
  <script src='https://cdn.jsdelivr.net/npm/fullcalendar@5.10.1/main.min.js'></script>
  <link href='https://cdn.jsdelivr.net/npm/bootstrap@4.6.1/dist/css/bootstrap.min.css' rel='stylesheet' />
  <script src='https://cdn.jsdelivr.net/npm/bootstrap@4.6.1/dist/js/bootstrap.bundle.min.js'></script>
  <style>
    body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
    #calendar { max-width: 900px; margin: 20px auto; }
    /* 予定削除エリア（ゴミ箱）のスタイル：上部に小さく配置 */
    #trash-bin {
      width: 150px;
      height: 50px;
      background-color: #ffcccc;
      border: 2px dashed #ff0000;
      border-radius: 10px;
      text-align: center;
      line-height: 50px;
      font-weight: bold;
      color: #ff0000;
      margin: 10px auto;
    }
  </style>
</head>
<body>
  <!-- 予定削除エリア -->
  <div id='trash-bin'>予定削除</div>
  <div id='calendar'></div>
  <script>
    // localStorage でイベント管理（初期は空配列）
    var events = [];
    if(localStorage.getItem('fcEvents')){
      events = JSON.parse(localStorage.getItem('fcEvents'));
    }
    function saveEvents(){
      localStorage.setItem('fcEvents', JSON.stringify(events));
    }

    document.addEventListener('DOMContentLoaded', function() {
      var calendarEl = document.getElementById('calendar');
      var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        selectable: true,
        editable: true,
        dayMaxEvents: true,
        events: events,
        // 日付をクリックすると、新規イベント追加のプロンプトを表示
        dateClick: function(info) {
          var title = prompt("イベントタイトルを入力してください", "新規イベント");
          if(title){
            var start = info.date;
            var end = new Date(start.getTime() + 60*60*1000); // 1時間後
            var newEvent = {
              id: Date.now(),
              title: title,
              start: start.toISOString(),
              end: end.toISOString()
            };
            events.push(newEvent);
            saveEvents();
            calendar.addEvent(newEvent);
          }
        },
        // ドラッグ＆ドロップやリサイズで変更があった場合、localStorage 更新
        eventDrop: function(info) {
          updateEvent(info.event);
        },
        eventResize: function(info) {
          updateEvent(info.event);
        },
        // イベントをクリックすると削除確認（クリックで削除）
        eventClick: function(info) {
          if(confirm("このイベントを削除しますか？")){
            info.event.remove();
            events = events.filter(e => e.id != info.event.id);
            saveEvents();
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

      function updateEvent(eventObj) {
        events = events.map(e => {
          if(e.id == eventObj.id){
            e.start = eventObj.start.toISOString();
            e.end = eventObj.end.toISOString();
          }
          return e;
        });
        saveEvents();
      }
    });
  </script>
</body>
</html>
"""

# st.components.v1.html で上記 HTML/JS を埋め込み表示（高さ 700px）
components.html(html_code, height=700)
