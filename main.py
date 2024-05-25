import logging
import os
from typing import Dict

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
    ['day', 'weekend', 'about']
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Hi! Welcome to the Unoffocial Dong Open Air Telegram bot!",
        reply_markup=markup,
    )

    return CHOOSING


async def day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("DAY!")

    return CHOOSING


async def weekend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("WEEKEND!")

    return CHOOSING


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Stopping!")
    return ConversationHandler.END


def main() -> None:
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(filters.Regex("^day$"), day),
                MessageHandler(filters.Regex("^weekend$"), weekend),
                MessageHandler(filters.Regex("^done$"), done),
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^Done$"), done)],
    )

    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
