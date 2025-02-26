import streamlit as st
from sqlalchemy.orm import sessionmaker
from models import engine
from crud import get_user
from werkzeug.security import check_password_hash

SessionLocal = sessionmaker(bind=engine)

def show_login_page():
    st.title("ログイン")
    username = st.text_input("ユーザー名")
    password = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        with SessionLocal() as db:
            user = get_user(db, username)
            if user and check_password_hash(user.password, password):
                st.session_state.current_user = user
                st.session_state.page = "main"
                st.success("ログイン成功！")
            else:
                st.error("ユーザー名またはパスワードが正しくありません。")
    if st.button("アカウント作成"):
        st.session_state.page = "register"
