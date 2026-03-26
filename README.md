# 📰 PulseNews

A Django-powered Indian news aggregator that automatically scrapes full articles, summarizes them with AI, and presents them in a clean, category-organized feed — no paywalls, no source redirects.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/YOUR_USERNAME/pulsenews&env=SECRET_KEY,NEWS_API_KEY,GROQ_API_KEY&envDescription=API%20keys%20required%20to%20run%20PulseNews&envLink=https://github.com/YOUR_USERNAME/pulsenews#environment-variables)

> ⚠️ Replace `YOUR_USERNAME` in the deploy button URL with your actual GitHub username after pushing the repo.

---

## ✨ Features

- 🇮🇳 **India-only news** — fetches and filters articles from Indian sources across all categories
- 🕷️ **Full article scraping** — automatically scrapes complete article text so readers never leave the site
- 🤖 **AI summarization** — every article is auto-summarized and rewritten in journalist style using Groq AI (free)
- 🗂️ **Category organization** — Technology, Business, Sports, Health, Science, Entertainment, Politics, General
- 👤 **User accounts** — registration, login, commenting
- ✍️ **Reporter dashboard** — fetch news by category, manage articles
- 🛡️ **Admin panel** — manage users, articles, categories, comments
- 🏷️ **Auto tagging** — AI generates relevant tags for every article
- 🔍 **Search** — full-text search across titles, summaries, and content

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.2, Django REST Framework |
| AI | Groq API (Llama 3 — free tier) |
| News Source | NewsAPI.org (free tier) |
| Scraping | newspaper3k, lxml |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Frontend | Vanilla HTML/CSS/JS |

---

## 🚀 Local Setup

### Prerequisites
- Python 3.10+
- A free [NewsAPI key](https://newsapi.org)
- A free [Groq API key](https://console.groq.com)

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/pulsenews.git
cd pulsenews

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env and fill in your keys (see below)

# 4. Run migrations
python manage.py migrate

# 5. Create categories, admin user, and demo reporter
python setup.py

# 6. Start the server
python manage.py runserver
```

Visit **http://127.0.0.1:8000**

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
NEWS_API_KEY=your_newsapi_key_here
GROQ_API_KEY=your_groq_api_key_here
```

| Variable | Where to get it |
|---|---|
| `SECRET_KEY` | Any random string (50+ chars) |
| `NEWS_API_KEY` | [newsapi.org](https://newsapi.org) — free plan works |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) — free plan works |

---

## 👤 Default Credentials

After running `python setup.py`:

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Reporter | `reporter1` | `reporter123` |

> ⚠️ Change these passwords before deploying to production.

---

## 📋 How to Fetch News

1. Log in as `admin` or `reporter1`
2. Go to the **Reporter Dashboard** → http://127.0.0.1:8000/reporter/
3. Select a category from the dropdown
4. Click **Fetch**
5. Articles are automatically scraped for full content and processed by AI

---

## ☁️ Deploying to Vercel

> Django on Vercel requires a few extra steps since Vercel is primarily a Node/serverless platform. The recommended approach is to use a `vercel.json` config with a WSGI handler.

### 1. Add `vercel.json` to your project root

```json
{
  "builds": [
    {
      "src": "newsagg/wsgi.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "15mb",
        "runtime": "python3.12"
      }
    }
  ],
  "routes": [
    {
      "src": "/static/(.*)",
      "dest": "/static/$1"
    },
    {
      "src": "/(.*)",
      "dest": "newsagg/wsgi.py"
    }
  ]
}
```

### 2. Update `settings.py` for production

```python
import os
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['*']

# Use PostgreSQL on Vercel (add DATABASE_URL to env vars)
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(default=os.getenv('DATABASE_URL'))
}

STATIC_ROOT = 'staticfiles'
```

### 3. Add production dependencies

```
pip install dj-database-url psycopg2-binary whitenoise
```

Add `whitenoise.middleware.WhiteNoiseMiddleware` to `MIDDLEWARE` (after `SecurityMiddleware`).

### 4. Set environment variables on Vercel

In your Vercel project dashboard → Settings → Environment Variables, add:

```
SECRET_KEY
NEWS_API_KEY
GROQ_API_KEY
DATABASE_URL   ← from Vercel Postgres or Supabase
DEBUG=False
```

### 5. Deploy

```bash
vercel --prod
```

Or use the **Deploy with Vercel** button at the top of this README.

---

## 📁 Project Structure

```
pulsenews/
├── apps/
│   ├── accounts/        # User auth, profiles
│   ├── news/            # Articles, categories, scraping, AI
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── services.py  # NewsAPI + scraper + Groq AI
│   │   └── templatetags/
│   │       └── news_filters.py
│   ├── reporter/        # Reporter dashboard
│   └── core/            # Homepage routing
├── templates/
│   ├── base.html
│   ├── news/
│   ├── accounts/
│   ├── reporter/
│   └── admin_panel/
├── static/
│   ├── css/
│   └── js/
├── newsagg/
│   ├── settings.py
│   └── urls.py
├── manage.py
├── setup.py
├── requirements.txt
└── .env.example
```

---

## 🤖 AI Pipeline

Every fetched article goes through this automatic pipeline:

```
NewsAPI fetch → Full article scrape → Groq AI summarize → Groq AI rephrase → Auto tag → Save
```

- **Summarize** — 4-5 sentence journalist-style summary
- **Rephrase** — full article rewritten in inverted-pyramid style
- **Tag** — 5-8 relevant topic tags extracted automatically

---

## 📝 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Credits

- [NewsAPI](https://newsapi.org) for news data
- [Groq](https://groq.com) for free AI inference
- [newspaper3k](https://github.com/codelucas/newspaper) for article scraping
- [Django](https://djangoproject.com) for the web framework
