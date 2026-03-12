import streamlit as st
import google.generativeai as genai
import pandas as pd
import json

# ==========================================
# 1. SECURITY & CONFIG
# ==========================================
st.set_page_config(page_title="ConnectWise AI Assistant", page_icon="📈")

# Simple Password Protection
def check_password():
    """Returns True if the user had the correct password."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    st.title("🔐 Secure Login")
    pwd = st.text_input("Enter Company Access Key:", type="password")
    if st.button("Login"):
        # CHANGE 'admin123' to whatever password you want!
        if pwd == "admin123":
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("Invalid Password")
    return False

if not check_password():
    st.stop()

# ==========================================
# 2. AI BRAIN SETUP
# ==========================================
# This pulls from your .streamlit/secrets.toml file
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("API Key not found. Please check your .streamlit/secrets.toml file.")
    st.stop()

model = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction="""
    You are a ConnectWise data specialist. 
    When asked for a graph or chart:
    1. Provide a brief text summary first.
    2. Provide the data in a JSON code block like this:
    ```json
    {"Title": {"Label1": 10, "Label2": 20}}
    ```
    """
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    st.session_state.gemini_chat = model.start_chat(history=[])

# ==========================================
# 3. CHAT INTERFACE
# ==========================================
st.title("📊 ConnectWise AI Assistant")
st.write("Ask me to analyze ticketing or generate financial graphs.")

# Display history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["text"])
        if "chart_data" in message:
            df = pd.DataFrame.from_dict(message["chart_data"], orient='index', columns=['Value'])
            st.bar_chart(df)

# Handle Input
if user_prompt := st.chat_input("Type your message here..."):
    st.session_state.chat_history.append({"role": "user", "text": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.gemini_chat.send_message(user_prompt)
            reply_text = response.text
            chart_dict = None

            # Check if AI outputted a JSON graph
            if "```json" in reply_text:
                try:
                    parts = reply_text.split("```json")
                    text_part = parts[0].strip()
                    json_part = parts[1].split("```")[0].strip()
                    parsed_json = json.loads(json_part)
                    
                    title = list(parsed_json.keys())[0]
                    chart_dict = parsed_json[title]
                    
                    st.markdown(text_part)
                    st.subheader(title)
                    df = pd.DataFrame.from_dict(chart_dict, orient='index', columns=['Value'])
                    st.bar_chart(df)
                    reply_text = text_part
                except:
                    st.markdown(reply_text)
            else:
                st.markdown(reply_text)

    st.session_state.chat_history.append({
        "role": "assistant", 
        "text": reply_text,
        **({"chart_data": chart_dict} if chart_dict else {})
    })