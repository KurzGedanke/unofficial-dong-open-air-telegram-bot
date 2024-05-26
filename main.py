import logging
import os
import datetime
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
    ['Next', 'Bands', 'About', 'Stop']
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Hi! Welcome to the Unoffical Dong Open Air Telegram bot! You got the following commands\n/next\n/bands\n/about\n/stop\n If the bot stops responing try to enter /start again.",
        reply_markup=markup,
    )

    return CHOOSING


async def upnext(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    r = requests.get('https://festivals.kurzgedanke.de/api/festivals/doa24/stages/mainstage/upnext')
    upnext = r.json()
    await update.message.reply_text(f"Up-Next:\n{upnext[0]['band']}\n{upnext[0]['startTime']}")

    return CHOOSING


async def bands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Loading...')
    r = requests.get('https://festivals.kurzgedanke.de/api/festivals/doa24/stages/mainstage/timeslots')
    timeslotsMainStage = r.json()
    weekendStr = f"Running Order Dong Open Air 2024\n"

    for timeslot in timeslotsMainStage:
        timestamp = timeslot['startTime']['timestamp']
        value = datetime.datetime.fromtimestamp(timestamp)
        weekendStr += f" {value:%A %H:%M}\t-\t{timeslot['band']}\n"

    await update.message.reply_text(weekendStr)


    return CHOOSING


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Stopping!\nYou stopped the bot. To restart it type \n/start")
    return CHOOSING


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Stopping!")
    await update.message.reply_text("You stopped the bot. To restart it type \n/start")
    return ConversationHandler.END


def main() -> None:
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(filters.Regex("^Next$"), upnext),
                MessageHandler(filters.Regex("^Bands$"), bands),
                MessageHandler(filters.Regex("^Stop$"), stop),
                MessageHandler(filters.Regex("^About"), about),
                MessageHandler(filters.Regex("^Help"), about),
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^Done$"), stop)],
    )

    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
