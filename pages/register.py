import streamlit as st
from sqlalchemy.orm import sessionmaker
from models import engine
from crud import create_user, get_user

SessionLocal = sessionmaker(bind=engine)

def show_register_page():
    st.title("アカウント作成")
    username = st.text_input("ユーザー名", key="reg_username")
    password = st.text_input("パスワード", type="password", key="reg_password")
    department = st.text_input("部署", key="reg_department")
    if st.button("登録"):
        with SessionLocal() as db:
            if get_user(db, username):
                st.error("このユーザー名は既に存在します。")
            else:
                create_user(db, username, password, department)
                st.success("アカウント作成に成功しました。ログインしてください。")
                st.session_state.page = "login"
    if st.button("ログインページへ"):
        st.session_state.page = "login"
