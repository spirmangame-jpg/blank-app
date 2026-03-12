import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import plotly.express as px

# ==========================================
# 1. SECURITY & CONFIG
# ==========================================
st.set_page_config(page_title="ConnectWise AI Assistant", page_icon="📈", layout="wide")

def check_password():
    """Returns True if the user had the correct password."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    st.title("🔐 Secure Login")
    pwd = st.text_input("Enter Company Access Key:", type="password")
    if st.button("Login"):
        # You can change 'admin123' to your preferred password
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
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("API Key not found. Please add GEMINI_API_KEY to your Streamlit Secrets.")
    st.stop()

model = genai.GenerativeModel(
    'gemini-2.5-pro',
    system_instruction="""
    You are Dentek Systems inc's personal AI assistant. You will help with queries. 
    When asked for a graph, chart, or visual:
    1. Provide a brief text summary of the insight.
    2. Provide a JSON block strictly in this format:
    ```json
    {
      "type": "pie", 
      "title": "Tickets by Status",
      "data": {"Open": 10, "Closed": 40, "Pending": 5}
    }
    ```
    Supported types: "bar", "line", "area", "pie".
    Always use the JSON format for any numerical comparison.
    """
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    st.session_state.gemini_chat = model.start_chat(history=[])

# ==========================================
# 3. CHAT INTERFACE
# ==========================================
st.title("📊 ConnectWise AI Assistant")
st.write("Ask me to analyze ticketing, financial trends, or technician performance.")

# Display history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["text"])
        if "chart_obj" in message:
            chart = message["chart_obj"]
            c_type = chart["type"]
            df = pd.DataFrame(list(chart["data"].items()), columns=['Category', 'Value'])
            
            if c_type == "pie":
                fig = px.pie(df, values='Value', names='Category', title=chart["title"], hole=0.3)
                st.plotly_chart(fig, use_container_width=True)
            elif c_type == "line":
                st.subheader(chart["title"])
                st.line_chart(chart["data"])
            elif c_type == "area":
                st.subheader(chart["title"])
                st.area_chart(chart["data"])
            else:
                st.subheader(chart["title"])
                st.bar_chart(chart["data"])

# Handle Input
if user_prompt := st.chat_input("Ask about your ConnectWise data..."):
    st.session_state.chat_history.append({"role": "user", "text": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            response = st.session_state.gemini_chat.send_message(user_prompt)
            reply_text = response.text
            chart_data_for_history = None

        if "```json" in reply_text:
            try:
                # 1. Extract JSON
                parts = reply_text.split("```json")
                text_part = parts[0].strip()
                json_part = parts[1].split("```")[0].strip()
                chart_json = json.loads(json_part)
                
                c_type = chart_json.get("type", "bar")
                c_title = chart_json.get("title", "Data Insight")
                c_data = chart_json.get("data")
                
                st.markdown(text_part)
                st.subheader(c_title)

                # 2. Logic to handle Multi-Series (Line/Bar) vs Simple (Pie)
                if isinstance(c_data, dict) and "series" in c_data:
                    # Format: {"categories": ["2000",...], "series": [{"name": "USA", "data": [...]}]}
                    df = pd.DataFrame(index=c_data["categories"])
                    for s in c_data["series"]:
                        df[s["name"]] = s["data"]
                    
                    if c_type == "line":
                        st.line_chart(df)
                    elif c_type == "area":
                        st.area_chart(df)
                    else:
                        st.bar_chart(df)
                        
                else:
                    # Format: {"Label1": 10, "Label2": 20} (Simple format)
                    df_simple = pd.DataFrame(list(c_data.items()), columns=['Category', 'Value'])
                    if c_type == "pie":
                        fig = px.pie(df_simple, values='Value', names='Category', hole=0.3)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.bar_chart(df_simple.set_index('Category'))

                reply_text = text_part
            except Exception as e:
                st.error(f"Charting Error: {e}")
                st.markdown(reply_text)
            else:
                st.markdown(reply_text)

    # Save to history
    st.session_state.chat_history.append({
        "role": "assistant", 
        "text": reply_text,
        "chart_obj": chart_data_for_history
    })