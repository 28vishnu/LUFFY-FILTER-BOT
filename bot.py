# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

# Clone Code Credit : YT - @Tech_VJ / TG - @VJ_Bots / GitHub - @VJBots

import sys, glob, importlib, logging, logging.config, pytz, asyncio
from pathlib import Path

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("cinemagoer").setLevel(logging.ERROR)

from pyrogram import Client, idle
from database.users_chats_db import db
# Explicitly import necessary variables from info
from info import (
    LOG_CHANNEL, CHANNELS, AUTH_CHANNEL, CLONE_MODE, ON_HEROKU, PORT,
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
from typing import Union, Optional, AsyncGenerator
from Script import script 
from datetime import date, datetime 
from aiohttp import web
from plugins import web_server
from plugins.clone import restart_bots

# Assuming TechVJ is a package/directory at the same level as bot.py and plugins
# If TechVJ.bot or TechVJ.util.keepalive do not exist, these imports will fail.
# Based on the user's traceback, it seems TechVJ is a valid path.
from TechVJ.bot import TechVJBot
from TechVJ.util.keepalive import ping_server
from TechVJ.bot.clients import initialize_clients

ppath = "plugins/*.py"
files = glob.glob(ppath)
TechVJBot.start()
loop = asyncio.get_event_loop()


async def start():
    print('\n')
    print('Initalizing Your Bot')
    bot_info = await TechVJBot.get_me()
    await initialize_clients()
    for name in files:
        with open(name) as a:
            patt = Path(a.name)
            plugin_name = patt.stem.replace(".py", "")
            plugins_dir = Path(f"plugins/{plugin_name}.py")
            import_path = "plugins.{}".format(plugin_name)
            spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
            load = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(load)
            sys.modules["plugins." + plugin_name] = load
            print("Tech VJ Imported => " + plugin_name)
    if ON_HEROKU:
        asyncio.create_task(ping_server())
    b_users, b_chats = await db.get_banned()
    temp.BANNED_USERS = b_users
    temp.BANNED_CHATS = b_chats
    me = await TechVJBot.get_me()
    temp.BOT = TechVJBot
    temp.ME = me.id
    temp.U_NAME = me.username
    temp.B_NAME = me.first_name
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
    if CLONE_MODE == True:
        print("Restarting All Clone Bots.......\n")
        await restart_bots()
        print("Restarted All Clone Bots.\n")
    app = web.AppRunner(await web_server())
    await app.setup()
    bind_address = "0.0.0.0"
    await web.TCPSite(app, bind_address, PORT).start()
    await idle()


if __name__ == '__main__':
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye 👋')
