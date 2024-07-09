# Unoffical Dong Open Air Telegram Bot

Based on [Band-API](https://github.com/KurzGedanke/band-api).

## Deploy

Create a `.env` with

```env
TOKEN="$BOT_TOKEN"
APP_ID="$TELEMETRY_APP_ID"
SALT="$SALT"
HASH="$HASH"
```

```bash
# create virtual env
$ virtualenv venv
$ source venv/bin/activate

# install packages
$ pip install -r requirements.txt

# run
$ python main.py
```
