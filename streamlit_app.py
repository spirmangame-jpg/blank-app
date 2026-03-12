import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import plotly.express as px

# ==========================================
# 1. SECURITY & CONFIG
# ==========================================
st.set_page_config(page_title="Dentek AI Assistant", page_icon="📈", layout="wide")

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True

    st.title("🔐 Dentek Secure Access")
    pwd = st.text_input("Enter Company Access Key:", type="password")
    if st.button("Login"):
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
    st.error("API Key not found in Streamlit Secrets.")
    st.stop()

# Using Pro for higher reasoning/logic
model = genai.GenerativeModel(
    'gemini-2.5-pro',
    system_instruction="""
    You are Dentek Systems Inc's Senior AI Strategy Assistant. 
    When asked for a visual:
    1. Provide a professional executive summary.
    2. Provide a JSON block for charting.
    
    JSON FORMAT RULES:
    - Use "type": "bar", "line", "area", or "pie".
    - Use "title": "Chart Title".
    - For data, you can provide a simple dict {"Label": Value} 
      OR a list of objects [{"Category": "A", "Value": 10}, {"Category": "B", "Value": 20}].
    
    Example for multi-series:
    {"type": "line", "title": "Trend", "data": [{"Year": 2020, "Sales": 10, "Profit": 5}, {"Year": 2021, "Sales": 15, "Profit": 7}]}
    """
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    st.session_state.gemini_chat = model.start_chat(history=[])

# ==========================================
# 3. ROBUST CHARTING ENGINE
# ==========================================
def render_custom_chart(chart_json):
    try:
        c_type = chart_json.get("type", "bar").lower()
        c_title = chart_json.get("title", "Data Visualization")
        raw_data = chart_json.get("data")

        # TRANSFORM DATA INTO DATAFRAME RUGGEDLY
        if isinstance(raw_data, list):
            # Case: List of dicts [{"Year": 2000, "USA": 10}, ...]
            df = pd.DataFrame(raw_data)
            # Find the best column for the X-axis (usually 'Year', 'Category', or the first column)
            x_axis = df.columns[0]
            df.set_index(x_axis, inplace=True)
        elif isinstance(raw_data, dict):
            if "series" in raw_data and "categories" in raw_data:
                # Case: Nested series format
                df = pd.DataFrame(index=raw_data["categories"])
                for s in raw_data["series"]:
                    df[s["name"]] = s["data"]
            else:
                # Case: Simple dict {"USA": 10, "China": 8}
                df = pd.DataFrame.from_dict(raw_data, orient='index', columns=['Value'])
        
        st.subheader(c_title)

        if c_type == "pie":
            # For Pie, we need a flat structure
            reset_df = df.reset_index()
            fig = px.pie(reset_df, values=reset_df.columns[1], names=reset_df.columns[0], hole=0.3)
            st.plotly_chart(fig, use_container_width=True)
        elif c_type == "line":
            st.line_chart(df)
        elif c_type == "area":
            st.area_chart(df)
        else:
            st.bar_chart(df)
            
    except Exception as e:
        st.error(f"Visualization Error: {e}")

# ==========================================
# 4. MAIN CHAT UI
# ==========================================
st.title("📊 Dentek Executive Assistant")

# Display History
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["text"])
        if "chart_obj" in message and message["chart_obj"]:
            render_custom_chart(message["chart_obj"])

# New Input
if user_prompt := st.chat_input("How can I assist you with Dentek data today?"):
    st.session_state.chat_history.append({"role": "user", "text": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processing Executive Data..."):
            response = st.session_state.gemini_chat.send_message(user_prompt)
            full_response = response.text
            
            # Parsing Logic
            display_text = full_response
            chart_obj = None
            
            if "```json" in full_response:
                parts = full_response.split("```json")
                display_text = parts[0].strip()
                json_str = parts[1].split("```")[0].strip()
                try:
                    chart_obj = json.loads(json_str)
                    st.markdown(display_text)
                    render_custom_chart(chart_obj)
                except:
                    st.markdown(full_response)
            else:
                st.markdown(full_response)

    # Save Assistant response to history
    st.session_state.chat_history.append({
        "role": "assistant", 
        "text": display_text,
        "chart_obj": chart_obj
    })