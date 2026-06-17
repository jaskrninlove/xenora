# 🍪 YouTube Cookie Setup (Required for JassMusic)

YouTube blocks yt-dlp from server IPs unless you provide cookies
from a logged-in account. This is a **one-time setup** that takes 2 minutes.

---

## Step 1 — Install the browser extension

Install **"Get cookies.txt LOCALLY"** in Chrome:
https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc

---

## Step 2 — Export YouTube cookies

1. Open **https://www.youtube.com** and make sure you are **logged in**
2. Click the extension icon
3. Select **"Export"** → **"Current Site"**
4. Save the file as `youtube.txt`

---

## Step 3 — Place the file in your bot folder

```
JassMusic/
├── cookies/
│   └── youtube.txt   ← place it here
├── jass/
├── ...
```

---

## Step 4 — Install the Invidious fallback plugin

```bash
pip install yt-dlp-invidious
```

Add to your `requirements.txt`:
```
yt-dlp-invidious
```

---

## Step 5 — Refresh cookies every 2–4 weeks

YouTube cookies expire. When the bot starts failing again, just
re-export and replace the file. You can add multiple cookie files
(e.g. `account1.txt`, `account2.txt`) — the bot rotates them randomly.

---

## Why this works

| Layer | Method | Works when |
|-------|--------|-----------|
| 1 | yt-dlp + your cookie | Cookie file present ✅ |
| 2 | Invidious mirror | YouTube blocks the request 🔄 |
| 3 | Search alternatives | Direct video is unavailable 🔄 |
