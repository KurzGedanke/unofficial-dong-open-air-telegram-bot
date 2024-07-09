import logging
import os
import datetime
import sqlite3
import hashlib

import requests
import telemetrydeckpy
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, Update
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
APP_ID = os.getenv('APP_ID')
SALT = os.getenv('SALT')
HASH = os.getenv('HASH')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.basicConfig(filename='main.log', encoding='utf-8', level=logging.DEBUG)
logger = logging.getLogger(__name__)

con = sqlite3.connect('db.sqlite')

CHOOSING, AUTH_REPLY, AUTH_BROADCAST = range(3)

reply_keyboard = [
    ['/next', '/bands', '/about']
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

telemetry = telemetrydeckpy.TelemetryDeck()


def make_sha(chat_id):
    return hashlib.sha256(str(chat_id).encode('utf-8')).hexdigest()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_message.chat_id

    try:
        cur = con.cursor()
        cur.execute('INSERT INTO User (chat_id, consent) VALUES (?, ?)', (str(chat_id), 1))
        con.commit()
    except Exception as e:
        logger.error(e)

    # print(chat_id)
    signal = telemetrydeckpy.Signal(APP_ID, make_sha(chat_id), 'Dong.Telegram.Start')
    # signal.is_test_mode = True

    telemetry.send_signal(signal)

    await update.message.reply_text(
        'Hi! Welcome to the unoffical Dong Open Air Telegram bot! You got the following commands\n/next\n/bands\n/about\n/stop\n If the bot stops responing try to enter /start again.',
        reply_markup=markup,
    )

    return CHOOSING


async def upnext(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_message.chat_id
    signal = telemetrydeckpy.Signal(APP_ID, make_sha(chat_id), 'Dong.Telegram.UpNext')
    signal.is_test_mode = True

    telemetry.send_signal(signal)

    r = requests.get('https://festivals.kurzgedanke.de/api/festivals/doa24/stages/mainstage/upnext')
    upnext = r.json()
    await update.message.reply_text(f"Up-Next:\n{upnext[0]['band']}\n{upnext[0]['startTime']}")

    return CHOOSING


async def bands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_message.chat_id
    signal = telemetrydeckpy.Signal(APP_ID, make_sha(chat_id), 'Dong.Telegram.Bands')
    signal.is_test_mode = True

    telemetry.send_signal(signal)

    await update.message.reply_text('Loading...')
    r = requests.get('https://festivals.kurzgedanke.de/api/festivals/doa24/stages/mainstage/timeslots')
    timeslots_main_stage = r.json()
    weekend_str = f"Running Order Dong Open Air 2024\n"

    for timeslot in timeslots_main_stage:
        timestamp = timeslot['startTime']['timestamp']
        value = datetime.datetime.fromtimestamp(timestamp)
        weekend_str += f" {value:%A %H:%M}\t-\t{timeslot['band']}\n"

    await update.message.reply_text(weekend_str)

    return CHOOSING


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_message.chat_id
    signal = telemetrydeckpy.Signal(APP_ID, make_sha(chat_id), 'Dong.Telegram.About')
    signal.is_test_mode = True

    telemetry.send_signal(signal)

    await update.message.reply_text('Hey! Thanks for using the unoffical Dong Open Air Telegram bot!')
    await update.message.reply_text('This bot, as well as the data source, is open source and can be found on github.')
    await update.message.reply_text('https://github.com/KurzGedanke/unofficial-dong-open-air-telegram-bot')
    await update.message.reply_text(
        'If you notice anything off or have any question, please contact me!\nYou will find me on most social network with the handel @ KurzGedanke.')
    await update.message.reply_text('Have fun and stay save at Dong Open Air 2024!')
    return CHOOSING


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_message.chat_id
    signal = telemetrydeckpy.Signal(APP_ID, make_sha(chat_id), 'Dong.Telegram.Stop')
    signal.is_test_mode = True

    telemetry.send_signal(signal)

    await update.message.reply_text('Stopping!')
    await update.message.reply_text('You stopped the bot. To restart it type \n/start')
    return ConversationHandler.END


async def auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Please input: ')
    return AUTH_REPLY


async def processed_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password = update.message.text

    hash_pw = make_sha(SALT + HASH)
    hash_input_pw = make_sha(SALT + password)

    if hash_pw == hash_input_pw:
        await update.message.reply_text('AUTHED!')
        await update.message.reply_text('Please input broadcast text: ')

        return AUTH_BROADCAST
    else:
        return CHOOSING


async def notice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_message.chat_id
    signal = telemetrydeckpy.Signal(APP_ID, make_sha(chat_id), 'Dong.Telegram.Notice')
    signal.is_test_mode = True
    telemetry.send_signal(signal)
    broadcast_text = update.message.text

    try:
        cur = con.cursor()
        res = cur.execute('SELECT chat_id FROM User')
        chat_ids = res.fetchall()
    except Exception as e:
        logger.error(e)

    for chatid in chat_ids:
        context.job_queue.run_once(broadcast, 1, chat_id=chatid[0], name=str(chat_id), data=str(broadcast_text))

    return CHOOSING


async def broadcast(context: ContextTypes.DEFAULT_TYPE):
    job = context.job

    await context.bot.send_message(job.chat_id, text=job.data)


def main() -> None:
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(filters.Regex('^/next$'), upnext),
                MessageHandler(filters.Regex('^/bands$'), bands),
                MessageHandler(filters.Regex('^/stop$'), stop),
                MessageHandler(filters.Regex('^/about$'), about),
                MessageHandler(filters.Regex('^/help$'), about),
                MessageHandler(filters.Regex('^auth'), auth),
            ],
            AUTH_REPLY: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex('^Done$')),
                    processed_auth,
                )
            ],
            AUTH_BROADCAST: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex('^Done$')),
                    notice,
                )
            ],
        },
        fallbacks=[MessageHandler(filters.Regex('^Done$'), stop)],
    )

    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
