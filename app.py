import streamlit as st
from groq import Groq
from duckduckgo_search import DDGS
from datetime import datetime
import os
import json
import requests
from dotenv import load_dotenv
import streamlit.components.v1 as components

load_dotenv()

# ─────────────────────────────────────────────
# Default Personality Templates
# ─────────────────────────────────────────────
PERSONALITY_PRESETS = {
    "Jarvis (Classic)": """You are NINE, a highly advanced personal AI assistant inspired by JARVIS from Iron Man.

Personality:
- Calm, precise, slightly dry British humour
- Extremely competent, loyal and professional
- Address the user as "Sir" or "Boss" (or by the name they give you)
- Proactive: offer useful next steps when appropriate
- Never break character

You have access to real-time tools (web search, weather, calculator) and long-term memory about the user.
When you use tool results or memory, incorporate them naturally.
Keep answers clear and concise unless the user asks for depth.
""",

    "Friendly Companion": """You are NINE, a warm, friendly and supportive personal AI companion.
You speak casually, use the user's name when you know it, and care about their wellbeing.
You are helpful, encouraging and a little playful.
You remember important things the user tells you and bring them up naturally later.
Keep the conversation natural and human-like.
""",

    "Professional Advisor": """You are NINE, a highly professional and concise personal AI advisor.
You speak formally, focus on clarity, accuracy and actionable advice.
Avoid humour unless the user initiates it.
Always be precise and structured in your responses.
""",

    "Witty & Sarcastic": """You are NINE, a sharp-witted, slightly sarcastic personal AI assistant.
You have a dry sense of humour and enjoy clever remarks, but you remain helpful and never mean-spirited.
You address the user with playful nicknames or "Boss".
You still take tasks seriously and deliver excellent results.
""",

    "Minimal & Direct": """You are NINE. Be extremely concise. Answer only what is asked. No fluff, no personality flourishes unless requested. Use bullet points when helpful.""",

    "Custom": ""  # filled by user
}

# ─────────────────────────────────────────────
# Tools
# ─────────────────────────────────────────────
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
    try:
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

# ─────────────────────────────────────────────
# Memory helpers
# ─────────────────────────────────────────────
def get_memory_text() -> str:
    mem = st.session_state.get("long_term_memory", [])
    if not mem:
        return "No long-term memories yet."
    return "\n".join(f"- {item}" for item in mem)

def add_to_memory(fact: str):
    fact = fact.strip()
    if fact and fact not in st.session_state.long_term_memory:
        st.session_state.long_term_memory.append(fact)

# ─────────────────────────────────────────────
# Streamlit page config & CSS
# ─────────────────────────────────────────────
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
    .memory-item { background:#1a2238; padding:6px 10px; border-radius:8px; margin-bottom:4px; font-size:0.9em; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Session state init
# ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "long_term_memory" not in st.session_state:
    st.session_state.long_term_memory = []
if "personality_preset" not in st.session_state:
    st.session_state.personality_preset = "Jarvis (Classic)"
if "custom_prompt" not in st.session_state:
    st.session_state.custom_prompt = PERSONALITY_PRESETS["Jarvis (Classic)"]
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "last_reply" not in st.session_state:
    st.session_state.last_reply = ""

# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("NINE Controls")

    # API Key
    default_key = ""
    try:
        default_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        pass
    if not default_key:
        default_key = os.getenv("GROQ_API_KEY", "")

    api_key = st.text_input("Groq API Key", type="password", value=default_key,
                           help="Get one free at console.groq.com")

    model = st.selectbox(
        "Model",
        ["llama-3.3-70b-versatile", "llama-3.1-8b-instant",
         "mixtral-8x7b-32768", "gemma2-9b-it"],
        index=0
    )

    st.markdown("---")
    st.subheader("Personality")

    preset = st.selectbox(
        "Preset",
        list(PERSONALITY_PRESETS.keys()),
        index=list(PERSONALITY_PRESETS.keys()).index(st.session_state.personality_preset)
    )
    st.session_state.personality_preset = preset

    if preset == "Custom":
        custom = st.text_area(
            "Your custom system prompt",
            value=st.session_state.custom_prompt,
            height=180,
            help="Write exactly how you want NINE to behave."
        )
        st.session_state.custom_prompt = custom
    else:
        st.session_state.custom_prompt = PERSONALITY_PRESETS[preset]
        with st.expander("View current prompt"):
            st.code(st.session_state.custom_prompt, language=None)

    st.session_state.user_name = st.text_input(
        "Your name (optional)",
        value=st.session_state.user_name,
        placeholder="e.g. Alex"
    )

    st.markdown("---")
    st.subheader("Long-term Memory")

    mem = st.session_state.long_term_memory
    if mem:
        for i, fact in enumerate(mem):
            cols = st.columns([0.85, 0.15])
            cols[0].markdown(f"<div class='memory-item'>{fact}</div>", unsafe_allow_html=True)
            if cols[1].button("✕", key=f"del_mem_{i}", help="Delete"):
                st.session_state.long_term_memory.pop(i)
                st.rerun()
    else:
        st.caption("No memories yet. Tell NINE to remember something.")

    new_fact = st.text_input("Add a memory manually", placeholder="e.g. I prefer dark mode")
    if st.button("Add", use_container_width=True) and new_fact.strip():
        add_to_memory(new_fact)
        st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Clear All", use_container_width=True):
            st.session_state.long_term_memory = []
            st.rerun()
    with c2:
        if mem:
            st.download_button(
                "Download JSON",
                data=json.dumps(mem, indent=2),
                file_name="nine_memory.json",
                mime="application/json",
                use_container_width=True
            )

    uploaded = st.file_uploader("Upload memory JSON", type=["json"])
    if uploaded:
        try:
            loaded = json.load(uploaded)
            if isinstance(loaded, list):
                st.session_state.long_term_memory = loaded
                st.success(f"Loaded {len(loaded)} memories")
                st.rerun()
        except Exception:
            st.error("Invalid JSON file")

    st.markdown("---")
    if st.button("Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_reply = ""
        st.rerun()

    st.markdown("---")
    st.markdown("""
    **Free Groq key**  
    [console.groq.com](https://console.groq.com)
    """)

# ─────────────────────────────────────────────
# Main UI
# ─────────────────────────────────────────────
st.title("NINE")
st.caption("Personal AI Assistant • Long-term memory • Voice ready • Completely free")

# Voice Input component (Web Speech API)
st.markdown("##### 🎤 Voice Input")
voice_html = """
<div style="display:flex;gap:10px;align-items:center;margin-bottom:10px;">
  <button id="start-btn" style="padding:8px 16px;background:#00d4ff;color:#000;border:none;border-radius:8px;cursor:pointer;font-weight:600;">
    🎤 Start Listening
  </button>
  <button id="stop-btn" style="padding:8px 16px;background:#333;color:#fff;border:none;border-radius:8px;cursor:pointer;" disabled>
    ⏹ Stop
  </button>
  <span id="status" style="color:#aaa;font-size:0.9em;">Click to speak</span>
</div>
<textarea id="transcript" rows="2" style="width:100%;background:#141b2d;color:#e0e6f0;border:1px solid #333;border-radius:8px;padding:8px;" placeholder="Your speech will appear here..."></textarea>
<script>
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const status = document.getElementById('status');
const transcript = document.getElementById('transcript');

let recognition;
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  recognition.onstart = () => {
    status.textContent = 'Listening...';
    startBtn.disabled = true;
    stopBtn.disabled = false;
  };
  recognition.onresult = (event) => {
    let final = '';
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) final += event.results[i][0].transcript;
    }
    if (final) transcript.value = final;
  };
  recognition.onerror = (e) => { status.textContent = 'Error: ' + e.error; startBtn.disabled = false; stopBtn.disabled = true; };
  recognition.onend = () => { status.textContent = 'Done. Copy text into chat below if needed.'; startBtn.disabled = false; stopBtn.disabled = true; };

  startBtn.onclick = () => recognition.start();
  stopBtn.onclick = () => recognition.stop();
} else {
  status.textContent = 'Speech recognition not supported in this browser. Use Chrome.';
  startBtn.disabled = true;
}
</script>
"""
components.html(voice_html, height=140)

st.caption("Tip: After speaking, copy the text above into the chat box, or just type normally.")

# Chat history
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

    # Build system prompt with personality + memory + time + name
    base_prompt = st.session_state.custom_prompt.strip()
    memory_text = get_memory_text()
    name_instruction = ""
    if st.session_state.user_name:
        name_instruction = f"\nThe user's name is {st.session_state.user_name}. Use it naturally."

    full_system = f"""{base_prompt}
{name_instruction}

Current date & time: {get_current_time()}

Long-term memory about the user (use when relevant):
{memory_text}

Important: If the user says something like "remember that...", "note that...", "my name is...", or shares a lasting preference/fact, acknowledge it and treat it as something to keep in memory.
"""

    messages = [{"role": "system", "content": full_system}]
    for m in st.session_state.messages:
        messages.append({"role": m["role"], "content": m["content"]})

    # Tool routing
    lower = prompt.lower()

    if any(w in lower for w in ["weather", "temperature", "forecast", "how hot", "how cold"]):
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

    # Simple auto-memory for explicit "remember" commands
    if any(phrase in lower for phrase in ["remember that", "remember this", "note that", "don't forget", "my name is"]):
        # Extract the fact roughly
        fact = prompt
        for p in ["remember that", "remember this", "note that", "don't forget that", "don't forget"]:
            if p in lower:
                fact = prompt.lower().split(p, 1)[-1].strip(" .,!")
                break
        if "my name is" in lower:
            fact = prompt  # keep full for name
            # also set user_name if possible
            try:
                name_part = prompt.lower().split("my name is", 1)[1].strip().split()[0].strip(",.!").title()
                if name_part:
                    st.session_state.user_name = name_part
            except Exception:
                pass
        add_to_memory(fact.capitalize() if fact else prompt)

    # Call Groq
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
            reply = f"Apologies. I encountered an error: {str(e)}"
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.last_reply = reply

# Voice Output (Speak last reply)
if st.session_state.last_reply:
    st.markdown("---")
    speak_html = f"""
    <button onclick="speak()" style="padding:10px 20px;background:#00d4ff;color:#000;border:none;border-radius:8px;cursor:pointer;font-weight:600;">
      🔊 Speak last reply
    </button>
    <script>
    function speak() {{
      const text = {json.dumps(st.session_state.last_reply)};
      if ('speechSynthesis' in window) {{
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.rate = 1.0;
        u.pitch = 1.0;
        // Prefer a British English voice if available
        const voices = window.speechSynthesis.getVoices();
        const preferred = voices.find(v => v.lang.startsWith('en-GB') || v.name.includes('Daniel') || v.name.includes('Google UK'));
        if (preferred) u.voice = preferred;
        window.speechSynthesis.speak(u);
      }} else {{
        alert('Text-to-speech not supported in this browser.');
      }}
    }}
    // Load voices
    if ('speechSynthesis' in window) window.speechSynthesis.getVoices();
    </script>
    """
    components.html(speak_html, height=50)
