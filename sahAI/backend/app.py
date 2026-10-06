import streamlit as st

st.set_page_config(
    page_title="sahAI",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 sahAI")
st.subheader("MLRITM R25 Academic & Campus Assistant")

user_input = st.chat_input("Ask me anything...")

if user_input:
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        st.write("sahAI is under construction 🚧")