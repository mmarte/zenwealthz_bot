# ZenWealthz Bot

A lightweight social automation bot inspired by the rock_bot workflow for the ZenWealthz brand.

It generates short, high-value posts for wealth, money mindset, and personal growth, queues them locally, and can publish them to Facebook, X, and Instagram when the required credentials are configured.

Accounts to connect:
- Facebook: https://www.facebook.com/profile.php?id=61554551697574
- Instagram: https://www.instagram.com/zenwealthwisdom/
- X: https://x.com/ZenWealthz

## What it does
- Generates one pending post per run in [generate.py](generate.py)
- Publishes the next pending post to available platforms in [publish.py](publish.py)
- Prints a simple weekly summary in [report.py](report.py)
- Stores queue and history in [posts.json](posts.json), [log.json](log.json), and [bot_state.json](bot_state.json)

## Quick start
```bash
cd c:\zenwealthz_bot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Then edit [.env.example](.env.example) values and run:
```bash
python generate.py
python publish.py
python report.py
```

## Supported publishing platforms
- Facebook: requires FB_PAGE_ID and FB_PAGE_TOKEN
- X: requires X_BEARER_TOKEN
- Instagram: requires IG_USER_ID and IG_ACCESS_TOKEN, plus optionally IG_MEDIA_URL or PEXELS_API_KEY

## Environment variables
See [.env.example](.env.example) for the full list.
