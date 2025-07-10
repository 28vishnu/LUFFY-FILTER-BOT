# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

# Clone Code Credit : YT - @Tech_VJ / TG - @VJ_Bots / GitHub - @VJBots

import sys, glob, importlib, logging, logging.config, pytz, asyncio
from pathlib import Path
from datetime import date, datetime
from aiohttp import web

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("cinemagoer").setLevel(logging.ERROR)

# Define the logger instance
logger = logging.getLogger(__name__)

from pyrogram import Client, idle
from pyrogram.errors import FloodWait # Import FloodWait specifically
from database.users_chats_db import db
# Explicitly import necessary variables from info
from info import (
    LOG_CHANNEL, CHANNELS, AUTH_CHANNEL, CLONE_MODE, ON_HEROKU, PORT, # Ensure PORT is imported
    API_ID, API_HASH, BOT_TOKEN, PICS, ADMINS, AUTH_USERS, REQST_CHANNEL,
    INDEX_REQ_CHANNEL, FILE_STORE_CHANNEL, DELETE_CHANNELS, SUPPORT_CHAT,
    OWNER_LNK, CHNL_LNK, GRP_LNK, VERIFY, BOT_USERNAME, BOT_NAME, BOT_ID,
    DATABASE_URI, DATABASE_NAME, COLLECTION_NAME, MULTIPLE_DATABASE,
    FILE_DB_URI, SEC_FILE_DB_URI, OTHER_DB_URI, CLONE_DATABASE_URI,
    CLONE_DATABASE_NAME, CLONE_COLLECTION_NAME, CLONE_API_ID, CLONE_API_HASH,
    CLONE_BOT_TOKEN, CLONE_PICS, CLONE_ADMINS, CLONE_AUTH_USERS, CLONE_REQST_CHANNEL,
    CLONE_INDEX_REQ_CHANNEL, CLONE_FILE_STORE_CHANNEL, CLONE_DELETE_CHANNELS,
    CLONE_SUPPORT_CHAT, CLONE_OWNER_LNK, CLONE_CHNL_LNK, CLONE_GRP_LNK,
    CLONE_VERIFY, CLONE_BOT_USERNAME, CLONE_BOT_NAME, CLONE_BOT_ID,
    CLONE_IMDB, CLONE_SPELL_CHECK_REPLY, CLONE_NO_RESULTS_MSG, CLONE_CUSTOM_FILE_CAPTION,
    CLONE_MAX_BTN, CLONE_VERIFY_SECOND_SHORTNER, CLONE_VERIFY_SND_SHORTLINK_API,
    CLONE_VERIFY_SND_SHORTLINK_URL, CLONE_VERIFY_TUTORIAL, CLONE_VERIFY_SHORTLINK_API,
    CLONE_VERIFY_SHORTLINK_URL, CLONE_SHORTLINK_API, CLONE_SHORTLINK_URL,
    CLONE_SHORTLINK_MODE, CLONE_TUTORIAL, CLONE_IS_TUTORIAL, CLONE_STREAM_MODE,
    CLONE_LONG_IMDB_DESCRIPTION, CLONE_IMDB_TEMPLATE, CLONE_BATCH_FILE_CAPTION,
    CLONE_REQUEST_TO_JOIN_MODE, CLONE_TRY_AGAIN_BTN, CLONE_PAYMENT_QR, CLONE_PAYMENT_TEXT,
    CLONE_REFERAL_COUNT, CLONE_REFERAL_PREMEIUM_TIME, CLONE_PREMIUM_AND_REFERAL_MODE,
    CLONE_REACTIONS, CLONE_RENAME_MODE, CLONE_AUTO_APPROVE_MODE, CLONE_USE_CAPTION_FILTER
)
from utils import temp
from typing import Union, Optional, AsyncGenerator
from Script import script 
from plugins import web_server
from plugins.clone import restart_bots # Assuming this is correct for clone mode

# Initialize the main bot client
TechVJBot = Client(
    name=SESSION,
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins"),
    sleep_threshold=SLEEP_THRESHOLD
)

loop = asyncio.get_event_loop()

async def start():
    print('\n')
    print('Initalizing Your Bot')
    
    # Try to start the bot with FloodWait handling
    try:
        await TechVJBot.start()
    except FloodWait as e:
        logger.error(f"FloodWait encountered during bot start. Waiting for {e.value} seconds.")
        await asyncio.sleep(e.value)
        await TechVJBot.start() # Retry after waiting
    except Exception as e:
        logger.exception(f"Error starting bot: {e}")
        sys.exit(1) # Exit if bot cannot start

    bot_info = await TechVJBot.get_me()
    temp.BANNED_USERS = await db.get_banned_users()
    temp.BANNED_CHATS = await db.get_banned_chats()
    temp.ME = bot_info.id
    temp.U_NAME = bot_info.username
    temp.B_NAME = bot_info.first_name

    logging.info(script.LOGO)
    tz = pytz.timezone('Asia/Kolkata')
    today = date.today()
    now = datetime.now(tz)
    time = now.strftime("%H:%M:%S %p")

    try:
        await TechVJBot.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(today, time))
    except Exception as e:
        print(f"Error sending restart message to LOG_CHANNEL: {e}")
        print("Make Your Bot Admin In Log Channel With Full Rights")

    for ch in CHANNELS:
        try:
            k = await TechVJBot.send_message(chat_id=ch, text="**Bot Restarted**")
            await k.delete()
        except Exception as e:
            print(f"Error sending restart message to CHANNELS: {e}")
            print("Make Your Bot Admin In File Channels With Full Rights")

    try:
        k = await TechVJBot.send_message(chat_id=AUTH_CHANNEL, text="**Bot Restarted**")
        await k.delete()
    except Exception as e:
        print(f"Error sending restart message to AUTH_CHANNEL: {e}")
        print("Make Your Bot Admin In Force Subscribe Channel With Full Rights")

    # Restart clone bots if enabled
    if CLONE_MODE == True:
        print("Restarting All Clone Bots.......\\n")
        await restart_bots()
        print("Restarted All Clone Bots.\\n")

    # Start web server
    app = web.AppRunner(await web_server())
    await app.setup()
    bind_address = "0.0.0.0"
    # Use the PORT environment variable provided by Render
    await web.TCPSite(app, bind_address, PORT).start() # <--- IMPORTANT: Ensure PORT is used here

    # Keep the bot running indefinitely
    await idle()


if __name__ == '__main__':
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye �')
    except Exception as e:
        # Log the unhandled exception before exiting
        logging.exception('An unhandled exception occurred during bot startup!')
        sys.exit(1) # Exit with an error code
