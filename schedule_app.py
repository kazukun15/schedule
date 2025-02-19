import streamlit as st
from datetime import date, datetime, timedelta

# セッションステートにイベントリストがなければ初期化
if "events" not in st.session_state:
    st.session_state.events = []

# ヘッダー
st.title("スケジュール管理アプリ (Streamlit)")

# サイドバーにナビゲーション（例：ログアウトボタンも配置できる）
with st.sidebar:
    st.header("メニュー")
    # ここにログアウト処理などのボタンを配置する場合は別途認証実装が必要
    st.button("ログアウト")

st.markdown("---")

# イベント入力フォーム
st.subheader("新規イベントの作成")

# 日付入力
event_date = st.date_input("日付", value=date.today())

# 開始時刻入力
start_time = st.time_input("開始時刻", value=datetime.now().time().replace(second=0, microsecond=0))

# 自動的に終了時刻を設定（開始時刻＋1時間）
start_dt = datetime.combine(event_date, start_time)
end_dt = start_dt + timedelta(hours=1)
end_time_str = end_dt.strftime("%H:%M")
st.write(f"自動設定の終了時刻: **{end_time_str}** (開始時刻の1時間後)")

# タイトルと説明の入力
title = st.text_input("タイトル")
description = st.text_area("説明", height=100)

# 保存ボタン
if st.button("イベントを保存"):
    # 入力チェック
    if not title:
        st.error("タイトルは必須です。")
    else:
        # 新規イベントを辞書として追加
        new_event = {
            "id": len(st.session_state.events) + 1,
            "date": event_date,
            "start": start_dt,
            "end": end_dt,
            "title": title,
            "description": description,
        }
        st.session_state.events.append(new_event)
        st.success("イベントが保存されました。")

st.markdown("---")

# 保存済みイベントの表示
st.subheader("保存済みイベント")
if st.session_state.events:
    for event in st.session_state.events:
        st.write(f"**{event['date'].strftime('%Y-%m-%d')} {event['start'].strftime('%H:%M')}～{event['end'].strftime('%H:%M')}** - {event['title']}")
        if event["description"]:
            st.write(f"説明: {event['description']}")
        # イベント削除ボタン
        delete_key = f"delete_{event['id']}"
        if st.button("削除", key=delete_key):
            st.session_state.events = [ev for ev in st.session_state.events if ev["id"] != event["id"]]
            st.experimental_rerun()
else:
    st.info("まだイベントが登録されていません。")
