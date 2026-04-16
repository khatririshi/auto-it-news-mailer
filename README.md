# 🖥️ Auto IT News Mailer

A fully automated Python script that fetches the latest IT/technology news and
delivers a beautifully formatted HTML email to your inbox every day — no admin
panel, no UI, just pure automation.

---

## 📁 Project Structure

```
auto_it_news_mailer/
├── main.py           ← Entry point + daily scheduler
├── fetch_news.py     ← Calls NewsAPI to get raw articles
├── filter_news.py    ← Filters & normalises IT-related articles
├── send_mail.py      ← Builds HTML email & sends via Gmail SMTP
├── template.html     ← Professional dark-mode email template
├── config.py         ← Loads .env variables + validation
├── requirements.txt  ← Python dependencies
├── .env.example      ← Template for your secrets (copy → .env)
├── .gitignore        ← Keeps .env out of git
└── mailer.log        ← Auto-created log file
```

---

## ⚙️ Step-by-Step Setup

### Step 1 — Prerequisites

- Python **3.10+** installed (`python --version`)
- A **Gmail account** with 2-Step Verification enabled
- A free **NewsAPI** account

### Step 2 — Clone / download the project

```bash
# If you have git:
git clone https://github.com/yourname/auto-it-news-mailer.git
cd auto_it_news_mailer

# Or just unzip the folder and open a terminal inside it
```

### Step 3 — Create a virtual environment (recommended)

```bash
# Create
python -m venv venv

# Activate (macOS / Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 5 — Get your NewsAPI key

1. Go to <https://newsapi.org/register>
2. Sign up for a **free account** (500 requests/day is enough)
3. Copy your **API key** from the dashboard

### Step 6 — Create a Gmail App Password

> Regular Gmail passwords don't work with SMTP. You need an App Password.

1. Go to your Google Account → **Security**
2. Make sure **2-Step Verification** is ON
3. Search for **"App Passwords"** in the search bar
4. Choose app: **Mail** / device: **Other** → give it a name (e.g. "NewsMailer")
5. Click **Generate** — copy the **16-character password**

### Step 7 — Configure your .env file

```bash
# Copy the template
cp .env.example .env

# Edit it with your real values
nano .env        # Linux/macOS
notepad .env     # Windows
```

Fill in:

```env
NEWS_API_KEY=abc123yourapikey
SENDER_EMAIL=you@gmail.com
SENDER_PASSWORD=abcd efgh ijkl mnop   # the 16-char App Password (spaces are fine)
RECIPIENT_EMAIL=inbox@example.com
```

To send to **multiple recipients**, separate with commas:

```env
RECIPIENT_EMAIL=alice@example.com,bob@example.com
```

---

## 🚀 How to Run

### Send immediately (test / one-shot)

```bash
python main.py --now
```

This runs the full pipeline right away: fetch → filter → send.
Check your inbox and `mailer.log` for the result.

### Start the daily scheduler

```bash
python main.py
```

- Sends one email immediately on first launch (to confirm everything works)
- Then sends every day at **08:00** in your configured timezone
- To change the time, edit `send_time` in `app_config.json`
- Keep the terminal / process running (see "Keep Running" below)

---

## ⏰ How to Schedule Daily Execution

### Option A — Keep the Python scheduler running (simplest)

Just leave `python main.py` running in a terminal or tmux/screen session.
The `schedule` library handles the daily trigger internally.

```bash
# In a persistent terminal session:
python main.py
```

### Option B — Linux/macOS cron job (no process to keep alive)

Use cron to launch the script once a day and let it exit.

```bash
# Open the crontab editor
crontab -e

# Add this line (sends at 08:00 every day)
# Format: minute hour day month weekday command
0 8 * * * /path/to/venv/bin/python /path/to/auto_it_news_mailer/main.py --now >> /path/to/auto_it_news_mailer/mailer.log 2>&1
```

Replace `/path/to/` with your actual paths. Find them with:

```bash
which python          # inside your activated venv
pwd                   # current directory
```

### Option C — Windows Task Scheduler

1. Open **Task Scheduler** → Create Basic Task
2. Trigger: **Daily** at 08:00
3. Action: **Start a program**
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `C:\path\to\auto_it_news_mailer\main.py --now`

---

## 📧 What the Email Looks Like

Each email contains:

- **Header** with today's date and category tags
- **Up to 8 article cards**, each showing:
  - Colour-coded source badge (blue=AI, red=Security, green=Dev, etc.)
  - Publication timestamp
  - Article title
  - Full description / content preview
  - **"Read Full Article →"** button linking to the original
- Optional **thumbnail image** if the article has one
- Professional **dark-mode** design with inline CSS (renders in all email clients)

---

## 🔐 Security Notes

- API keys and passwords live **only in `.env`** — never in code
- `.gitignore` prevents `.env` from being committed
- Gmail SMTP uses **TLS encryption** (port 587)
- Use an **App Password**, not your real Gmail password

---

## 🛠️ Customisation

| What to change | Where |
|----------------|-------|
| Send time | `send_time` in `app_config.json` |
| Number of articles | `MAX_ARTICLES = 8` in `config.py` |
| IT keywords / topics | `IT_KEYWORDS` list in `filter_news.py` |
| Email subject line | `EMAIL_SUBJECT` in `config.py` |
| Email design | `template.html` |
| News search query | `IT_SEARCH_QUERY` in `fetch_news.py` |

---

## 🐛 Troubleshooting

| Problem | Fix |
|---------|-----|
| `Missing required environment variables` | Check your `.env` file — all 4 values must be set |
| `Gmail authentication failed` | Use an **App Password**, not your account password; enable 2FA first |
| `No articles fetched` | Verify `NEWS_API_KEY` is correct; free tier allows 500 req/day |
| Email goes to spam | Add your sender address to contacts; check Gmail "Sent" to confirm it was sent |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside your venv |

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | 2.32.3 | HTTP calls to NewsAPI |
| `python-dotenv` | 1.0.1 | Load `.env` file |
| `schedule` | 1.2.2 | Pure-Python daily scheduler |

`smtplib` and `email` are part of the Python standard library — no install needed.

---

## 📄 License

MIT — free to use, modify, and distribute.
