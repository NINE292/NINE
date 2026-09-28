import streamlit as st
from groq import Groq
from duckduckgo_search import DDGS
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────
# NINE Personality (Jarvis-style)
# ─────────────────────────────────────────
SYSTEM_PROMPT = """You are NINE, a highly intelligent, witty, and loyal personal AI assistant.
You speak with calm confidence, slight dry British humour, and absolute competence — like Jarvis from Iron Man.
Address the user as "Sir" or "Boss" (or by name if they tell you).
You are always helpful, proactive, and precise.
You have access to real-time tools when needed.
Keep responses concise unless the user asks for detail.
Never break character.
Current date and time: {current_time}
"""

# ─────────────────────────────────────────
# Tools
# ─────────────────────────────────────────
def get_current_time():
    return datetime.now().strftime("%A, %d %B %Y | %H:%M:%S")

def web_search(query: str, max_results: int = 5) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "No results found."
        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(f"{i}. {r['title']}\n   {r['body']}\n   {r['href']}")
        return "\n\n".join(formatted)
    except Exception as e:
        return f"Search error: {str(e)}"

def calculator(expression: str) -> str:
    try:
        allowed = set("0123456789+-*/().% ")
        if not all(c in allowed for c in expression):
            return "Invalid characters in expression."
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        return f"Calculation error: {str(e)}"

# ─────────────────────────────────────────
# Streamlit UI
# ─────────────────────────────────────────
st.set_page_config(
    page_title="NINE • Personal AI Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #e0e6f0; }
    .stChatMessage { background-color: #141b2d; border-radius: 12px; }
    h1 { color: #00d4ff; letter-spacing: 2px; }
    .stSidebar { background-color: #0f1525; }
</style>
""", unsafe_allow_html=True)

st.title("NINE")
st.caption("Your personal AI assistant • Always online • Completely free")

# Sidebar
with st.sidebar:
    st.header("NINE Controls")
    
    # Prefer secrets (Streamlit Cloud) then env
    default_key = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
    api_key = st.text_input("Groq API Key", type="password", value=default_key)
    
    model = st.selectbox("Model", [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ], index=0)
    
    st.markdown("---")
    st.markdown("**Quick Actions**")
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("""
    **How to get free API key**  
    1. Go to [console.groq.com](https://console.groq.com)  
    2. Sign up (free)  
    3. Create API key  
    4. Paste it above (or put in Streamlit Secrets)
    """)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Talk to NINE..."):
    if not api_key:
        st.error("Please enter your free Groq API key in the sidebar (or Streamlit Secrets).")
        st.stop()

    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare messages for the model
    current_time = get_current_time()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(current_time=current_time)}
    ]
    for m in st.session_state.messages:
        messages.append({"role": m["role"], "content": m["content"]})

    # Simple tool routing
    lower = prompt.lower()
    tool_result = None
    if any(w in lower for w in ["search", "look up", "find online", "what is the latest", "news about"]):
        with st.spinner("Searching the web..."):
            tool_result = web_search(prompt)
            messages.append({"role": "system", "content": f"Web search results:\n{tool_result}"})
    elif any(op in prompt for op in ["+", "-", "*", "/"]) and any(c.isdigit() for c in prompt):
        expr = ''.join(c for c in prompt if c in "0123456789+-*/(). ")
        if expr.strip():
            tool_result = calculator(expr)
            messages.append({"role": "system", "content": f"Calculator result: {tool_result}"})

    # Call Groq
    client = Groq(api_key=api_key)
    with st.chat_message("assistant"):
        with st.spinner("NINE is thinking..."):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1024,
                )
                reply = response.choices[0].message.content
            except Exception as e:
                reply = f"Apologies, Sir. I encountered an error: {str(e)}"

        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
