# NINE – Your Personal AI Assistant

**NINE** is a free, always-online personal AI assistant inspired by JARVIS.

It runs completely free using:
- **Streamlit** (beautiful chat interface)
- **Groq** free API (very fast Llama / Mixtral models)
- Free tools: web search + weather + calculator

Deploy once on Streamlit Community Cloud → NINE stays online 24/7 at zero cost.

**Live repo:** https://github.com/NINE292/NINE

---

## Features

- JARVIS-style personality (calm, witty, loyal, calls you Sir/Boss)
- Real-time web search (DuckDuckGo)
- Live weather (Open-Meteo – no key needed)
- Calculator
- Streaming responses
- Clean dark UI
- Completely free to host and run

---

## 1. Get a free Groq API key (30 seconds)

1. Go to [https://console.groq.com](https://console.groq.com)
2. Sign up / log in
3. Create an API key
4. Copy it (starts with `gsk_`)

---

## 2. Deploy free on Streamlit Cloud (Recommended)

1. Go to [https://share.streamlit.io](https://share.streamlit.io)
2. Sign in with the **same GitHub account** (`NINE292`)
3. Click **New app**
4. Choose repository: `NINE292/NINE`
5. Main file path: `app.py`
6. Click **Advanced settings** → **Secrets** and paste:

```toml
GROQ_API_KEY = "gsk_your_actual_key_here"
```

7. Click **Deploy**

You will receive a permanent public URL, for example:  
`https://nine292-nine.streamlit.app`

NINE is now online and free forever.

---

## 3. Run locally (optional)

```bash
git clone https://github.com/NINE292/NINE.git
cd NINE
pip install -r requirements.txt
```

Create a `.env` file:

```env
GROQ_API_KEY=gsk_your_key_here
```

Then:

```bash
streamlit run app.py
```

---

## Project Structure

```
NINE/
├── app.py              # Main application
├── requirements.txt    # Dependencies
├── .env.example        # Example env file
├── .gitignore
└── README.md
```

---

## Future ideas (still free)

- Long-term memory
- Voice input / output (browser Speech API)
- More tools (calendar, notes, email)
- Telegram / Discord version

Feel free to open issues or pull requests.

**License:** MIT
