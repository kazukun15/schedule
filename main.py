import streamlit as st
from pages import login, register, main_page

st.set_page_config(layout="wide")
st.session_state.setdefault("current_user", None)
st.session_state.setdefault("page", "login")

if st.session_state.current_user is None:
    if st.session_state.page == "register":
        register.show_register_page()
    else:
        login.show_login_page()
else:
    main_page.show_main_page()
