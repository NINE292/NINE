import streamlit as st
from groq import Groq
from duckduckgo_search import DDGS
from datetime import datetime
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────
# NINE – Personality (Jarvis-style)
# ─────────────────────────────────────────
SYSTEM_PROMPT = """You are NINE, a highly advanced personal AI assistant inspired by JARVIS.

Personality:
- Calm, precise, slightly dry British humour
- Extremely competent and loyal
- Address the user as "Sir", "Boss", or by name once they tell you
- Proactive: offer useful next steps when appropriate
- Never break character

You have access to real-time tools (web search, weather, calculator).
When you use tool results, incorporate them naturally into your reply.
Keep answers clear and concise unless the user asks for depth.

Current date & time: {current_time}
"""

# ─────────────────────────────────────────
# Tools
# ─────────────────────────────────────────
def get_current_time() -> str:
    return datetime.now().strftime("%A, %d %B %Y | %H:%M:%S")

def web_search(query: str, max_results: int = 5) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "No results found."
        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. **{r.get('title', '')}**\n   {r.get('body', '')}\n   {r.get('href', '')}")
        return "\n\n".join(lines)
    except Exception as e:
        return f"Search unavailable: {e}"

def get_weather(city: str = "London") -> str:
    """Free weather via Open-Meteo (no API key needed)."""
    try:
        # Geocode first
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=8
        ).json()
        if not geo.get("results"):
            return f"Could not find location: {city}"
        loc = geo["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]
        name = loc.get("name", city)

        weather = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                "timezone": "auto"
            },
            timeout=8
        ).json()
        cur = weather.get("current", {})
        return (
            f"Weather in {name}:\n"
            f"Temperature: {cur.get('temperature_2m')} °C\n"
            f"Humidity: {cur.get('relative_humidity_2m')}%\n"
            f"Wind: {cur.get('wind_speed_10m')} km/h"
        )
    except Exception as e:
        return f"Weather service error: {e}"

def calculator(expression: str) -> str:
    try:
        allowed = set("0123456789+-*/().% ")
        if not all(c in allowed for c in expression):
            return "Invalid characters."
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        return f"Calculation error: {e}"

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
    .stChatMessage { background-color: #141b2d; border-radius: 14px; padding: 0.6rem 1rem; }
    h1 { color: #00d4ff; letter-spacing: 3px; font-weight: 700; }
    .stSidebar { background-color: #0f1525; }
    div[data-testid="stChatInput"] textarea { background-color: #141b2d !important; }
</style>
""", unsafe_allow_html=True)

st.title("NINE")
st.caption("Personal AI Assistant • Always online • Completely free")

# Sidebar
with st.sidebar:
    st.header("Controls")

    # Prefer Streamlit secrets, then env, then empty
    default_key = ""
    try:
        default_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        pass
    if not default_key:
        default_key = os.getenv("GROQ_API_KEY", "")

    api_key = st.text_input("Groq API Key", type="password", value=default_key, help="Get one free at console.groq.com")

    model = st.selectbox(
        "Model",
        [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ],
        index=0
    )

    st.markdown("---")
    if st.button("Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("""
    **Free Groq API key**  
    1. [console.groq.com](https://console.groq.com)  
    2. Sign up → Create API Key  
    3. Paste above **or** put in Streamlit Secrets
    """)

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Talk to NINE..."):
    if not api_key:
        st.error("Please add your free Groq API key in the sidebar (or Streamlit Secrets).")
        st.stop()

    # User message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Build conversation
    current_time = get_current_time()
    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(current_time=current_time)}]
    for m in st.session_state.messages:
        messages.append({"role": m["role"], "content": m["content"]})

    # Simple but effective tool routing
    lower = prompt.lower()
    tool_context = ""

    if any(w in lower for w in ["weather", "temperature", "forecast", "how hot", "how cold"]):
        # crude city extraction
        city = "London"
        for word in ["in ", "at ", "for "]:
            if word in lower:
                parts = lower.split(word, 1)
                if len(parts) > 1:
                    city = parts[1].split()[0].strip(",.?!").title()
                    break
        with st.spinner(f"Checking weather for {city}..."):
            tool_context = get_weather(city)
            messages.append({"role": "system", "content": f"Tool result (weather):\n{tool_context}"})

    elif any(w in lower for w in ["search", "look up", "find online", "what is the latest", "news about", "who is", "google"]):
        with st.spinner("Searching the web..."):
            tool_context = web_search(prompt)
            messages.append({"role": "system", "content": f"Tool result (web search):\n{tool_context}"})

    elif any(op in prompt for op in ["+", "-", "*", "/"]) and any(c.isdigit() for c in prompt):
        expr = "".join(c for c in prompt if c in "0123456789+-*/(). ")
        if expr.strip():
            tool_context = calculator(expr)
            messages.append({"role": "system", "content": f"Tool result (calculator): {tool_context}"})

    # Call Groq with streaming
    client = Groq(api_key=api_key)
    with st.chat_message("assistant"):
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.65,
                max_tokens=1200,
                stream=True
            )
            reply = st.write_stream(stream)
        except Exception as e:
            reply = f"Apologies, Sir. I encountered an error: {str(e)}"
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
