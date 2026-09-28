# NINE – Your Personal AI Assistant

**NINE** is a free, cloud-based personal AI assistant inspired by Jarvis from Iron Man.

It runs completely for free using:
- **Streamlit** (beautiful chat UI)
- **Groq** free API (extremely fast Llama / Mixtral models)
- Optional browser voice input

Deploy it once on Streamlit Community Cloud and NINE stays online 24/7 at zero cost.

---

## Features

- Jarvis-style personality (calm, witty, loyal, calls you Sir/Boss)
- Real-time web search (DuckDuckGo)
- Calculator
- Conversation memory (session-based)
- Clean dark cyberpunk UI
- Completely free to run and host

---

## Quick Start (Local Testing)

1. Clone the repo
```bash
git clone https://github.com/NINE292/NINE.git
cd NINE
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Get a free Groq API key  
   → https://console.groq.com  (sign up → create API key)

4. Create a `.env` file
```env
GROQ_API_KEY=gsk_your_key_here
```

5. Run
```bash
streamlit run app.py
```

---

## Deploy Free on Streamlit Cloud (Recommended)

1. Go to [https://share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click **New app**
4. Select repository: `NINE292/NINE`
5. Main file path: `app.py`
6. Click **Advanced settings** → **Secrets** and paste:

```toml
GROQ_API_KEY = "gsk_your_actual_key_here"
```

7. Deploy!

You will get a permanent public URL like:  
`https://nine292-nine.streamlit.app`

NINE is now always online and free forever.

---

## Project Structure

```
NINE/
├── app.py              # Main Streamlit application
├── requirements.txt    # Dependencies
├── .env.example        # Example environment file
├── .gitignore
└── README.md
```

---

## Future Upgrades (still free)

- Long-term memory with SQLite / Hugging Face datasets
- Voice output (browser TTS)
- More tools (weather, calendar, email)
- Telegram / Discord bot version
- Multi-model routing

Feel free to open issues or PRs!

---

**License:** MIT
