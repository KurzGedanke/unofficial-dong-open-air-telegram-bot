import logging
import os
import json
from typing import Dict

import requests
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)

# loads env
load_dotenv()

TOKEN = os.getenv('TOKEN')

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

CHOOSING, WEEKEND, DAY, ABOUT = range(4)

reply_keyboard = [
    ['Next', 'Day', 'Weekend', 'About', 'Stop']
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Hi! Welcome to the Unoffocial Dong Open Air Telegram bot!",
        reply_markup=markup,
    )

    return CHOOSING


async def upnext(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    r = requests.get('https://festivals.kurzgedanke.de/api/festivals/doa24/stages/mainstage/upnext')
    upnext = r.json()
    await update.message.reply_text(f"Up-Next:\n{upnext[0]['band']}\n{upnext[0]['startTime']}")

    return CHOOSING


async def day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("DAY!")

    return CHOOSING


async def weekend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("WEEKEND!")

    return CHOOSING


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Stopping!\nYou stopped the bot. To restart it type \n/start")
    return ConversationHandler.END


def main() -> None:
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(filters.Regex("^Next$"), upnext),
                MessageHandler(filters.Regex("^Day$"), day),
                MessageHandler(filters.Regex("^Weekend$"), weekend),
                MessageHandler(filters.Regex("^Stop$"), stop),
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^Done$"), stop)],
    )

    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
