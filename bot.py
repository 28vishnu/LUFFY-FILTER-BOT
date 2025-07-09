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
    FORCE_SUB_MODE, PROTECT_CONTENT, AUTO_DELETE, AUTO_DELETE_TIME,
    CUSTOM_FILE_CAPTION, BATCH_FILE_CAPTION, USE_CAPTION_FILTER,
    PUBLIC_FILE_STORE, CACHE_TIME,
    IMDB, IMDB_TEMPLATE, LONG_IMDB_DESCRIPTION, SPELL_CHECK_REPLY,
    PM_SEARCH_MODE, BUTTON_MODE, MAX_BTN, AUTO_FFILTER, PREMIUM_AND_REFERAL_MODE,
    REFERAL_COUNT, REFERAL_PREMEIUM_TIME, PAYMENT_QR, PAYMENT_TEXT,
    MELCOW_NEW_USERS, REQUEST_TO_JOIN_MODE, TRY_AGAIN_BTN, STREAM_MODE,
    SHORTLINK_MODE, SHORTLINK_URL, SHORTLINK_API, IS_TUTORIAL, TUTORIAL,
    VERIFY_TUTORIAL, MULTI_CLIENT, SLEEP_THRESHOLD, PING_INTERVAL, URL,
    RENAME_MODE, AUTO_APPROVE_MODE, REACTIONS,
    VERIFY_SECOND_SHORTNER, VERIFY_SND_SHORTLINK_API, VERIFY_SND_SHORTLINK_URL,
    VERIFY_SHORTLINK_API, VERIFY_SHORTLINK_URL,
    MSG_ALRT,
    LANGUAGES,
    YEARS # Ensure YEARS is imported
)
from utils import temp
from Script import script
from plugins import web_server
from plugins.clone import restart_bots

# Import cleanup and index functions from ia_filterdb
from database.ia_filterdb import remove_duplicate_files, ensure_indexes

# Assuming TechVJ is a package/directory at the same level as bot.py and plugins
# If TechVJ.bot or TechVJ.util.keepalive do not exist, these imports will fail.
# Based on the user's traceback, it seems TechVJ is a valid path.
# CRITICAL: This import assumes TechVJ/bot.py defines and exports 'TechVJBot'
from TechVJ.bot import TechVJBot 
from TechVJ.util.keepalive import ping_server
from TechVJ.bot.clients import initialize_clients # Assuming this function exists

ppath = "plugins/*.py"
files = glob.glob(ppath)
# DeprecationWarning: There is no current event loop - This is often harmless if asyncio.run() is used later
# loop = asyncio.get_event_loop() # Removed as asyncio.run() handles loop creation


async def start():
    print('\n')
    print('Initalizing Your Bot')

    # CRITICAL: Clean duplicates and ensure indexes before bot starts
    try:
        await remove_duplicate_files()
        await ensure_indexes()
        logger.info("Database cleanup and index setup complete.")
    except Exception as e:
        logger.error(f"Error during database cleanup or index setup: {e}. Exiting.")
        sys.exit(1) # Exit if database setup fails critically

    # Start the bot client with FloodWait handling and retry logic
    max_retries = 5
    for attempt in range(max_retries):
        try:
            await TechVJBot.start()
            logger.info("Bot started successfully!")
            break # Exit loop if startup is successful
        except FloodWait as e:
            wait_time = e.value + 5 # Add a small buffer to the wait time
            logger.warning(f"FloodWait during bot startup (Attempt {attempt+1}/{max_retries}): Telegram says to wait for {e.value} seconds. Retrying after {wait_time}s.")
            await asyncio.sleep(wait_time)
        except Exception as e:
            logger.exception(f"An error occurred during bot startup (Attempt {attempt+1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                logger.error("Max retries reached. Exiting due to persistent startup error.")
                sys.exit(1) # Exit if max retries are exhausted
            await asyncio.sleep(10) # Wait a bit before next retry for other errors

    # If bot didn't start after retries, exit
    if not TechVJBot.is_connected:
        logger.error("Bot failed to connect after multiple retries. Exiting.")
        sys.exit(1)

    # Initialize other clients (if any, from TechVJ.bot.clients)
    try:
        await initialize_clients()
    except Exception as e:
        logger.error(f"Error initializing other clients: {e}")

    # Load plugins dynamically
    for name in files:
        try:
            patt = Path(name)
            plugin_name = patt.stem.replace(".py", "")
            plugins_dir = Path(f"plugins/{plugin_name}.py")
            import_path = "plugins.{}".format(plugin_name)
            spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
            load = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(load)
            sys.modules["plugins." + plugin_name] = load
            print("Tech VJ Imported => " + plugin_name)
        except Exception as e:
            logger.error(f"Error importing plugin {name}: {e}")

    # Start ping server if on Heroku (or similar environment where keepalive is needed)
    if ON_HEROKU:
        asyncio.create_task(ping_server())

    # Load banned users and chats
    try:
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats
    except Exception as e:
        logger.error(f"Error loading banned users/chats: {e}")
        temp.BANNED_USERS = []
        temp.BANNED_CHATS = []

    # Fetch bot's info and store in temp
    try:
        me = await TechVJBot.get_me()
        temp.BOT = TechVJBot
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        logging.info(script.LOGO)
    except Exception as e:
        logger.error(f"Error fetching bot info: {e}")

    # Send restart messages with small delays
    tz = pytz.timezone('Asia/Kolkata')
    today = date.today()
    now = datetime.now(tz)
    time_str = now.strftime("%H:%M:%S %p")
    
    # Send to LOG_CHANNEL
    try:
        await TechVJBot.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(today, time_str))
        await asyncio.sleep(1) # Small delay
    except Exception as e:
        print(f"Error sending restart message to LOG_CHANNEL: {e}")
        print("Make Your Bot Admin In Log Channel With Full Rights")

    # Send to CHANNELS
    for ch in CHANNELS:
        try:
            k = await TechVJBot.send_message(chat_id=ch, text="**Bot Restarted**")
            await k.delete()
            await asyncio.sleep(1) # Small delay
        except Exception as e:
            print(f"Error sending restart message to CHANNELS: {e}")
            print("Make Your Bot Admin In File Channels With Full Rights")

    # Send to AUTH_CHANNEL
    try:
        k = await TechVJBot.send_message(chat_id=AUTH_CHANNEL, text="**Bot Restarted**")
        await k.delete()
        await asyncio.sleep(1) # Small delay
    except Exception as e:
        print(f"Error sending restart message to AUTH_CHANNEL: {e}")
        print("Make Your Bot Admin In Force Subscribe Channel With Full Rights")

    # Restart clone bots if enabled
    if CLONE_MODE == True:
        print("Restarting All Clone Bots.......\n")
        try:
            await restart_bots()
            print("Restarted All Clone Bots.\n")
        except Exception as e:
            logger.error(f"Error restarting clone bots: {e}")

    # Start web server
    try:
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        site = web.TCPSite(app, bind_address, PORT)
        await site.start()
        logger.info(f"Web server started on {bind_address}:{PORT}")
    except Exception as e:
        logger.error(f"Error starting web server: {e}. Ensure PORT is correctly configured and available.")
        # This is a critical component for some bots, might want to exit or log prominently.

    # Keep the bot running indefinitely
    await idle()


if __name__ == '__main__':
    try:
        # Use asyncio.run() for proper event loop management
        asyncio.run(start())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye �')
    except Exception as e:
        # Log the unhandled exception before exiting
        logger.exception(f"An unhandled error occurred in main execution: {e}")

