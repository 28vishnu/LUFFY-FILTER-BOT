# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01


import re
from os import environ
from Script import script

id_pattern = re.compile(r'^.\d+$')

# Bot information
SESSION = environ.get('SESSION', 'TechVJBot')
API_ID = int(environ.get('API_ID', '23394197')) # Updated
API_HASH = environ.get('API_HASH', 'c479cdf25a47b32295ff0d6b15709aac') # Updated with the provided API Hash
BOT_TOKEN = environ.get('BOT_TOKEN', "") # Reverted to empty string. This MUST be set as an environment variable on Render.


# This Pictures Is For Start Message Picture, You Can Add Multiple By Giving One Space Between Each.
PICS = (environ.get('PICS', '')).split()


# Admins & Users
ADMINS = [int(admin) if id_pattern.search(admin) else admin for admin in environ.get('ADMINS', '7204704497').split()] # Updated
auth_users = [int(user) if id_pattern.search(user) else user for user in environ.get('AUTH_USERS', '7204704497').split()]  # Updated
AUTH_USERS = (auth_users + ADMINS) if auth_users else []

# This Channel Is For When User Start Your Bot Then Bot Send That User Name And Id In This Log Channel, Same For Group Also.
LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '-1002737880991')) # Updated
# Updated LOG_CHANNEL to -1002737880981 as per user request

# This Channel Is For When You Add Your File In This Channel Then Bot Automatically Save All Files In Your Database.
CHANNELS = [int(ch) for ch in environ.get('CHANNELS', '-1002829192804').split()] # Updated (empty)

# This Channel Is For Force Subscribtion, When User Start Your Bot Then Bot Send A Message For Force Subscribtion.
AUTH_CHANNEL = int(environ.get('AUTH_CHANNEL', '-1002804738225')) # Corrected AUTH_CHANNEL to the provided channel ID
# Updated AUTH_CHANNEL to -1002804738225 as per user request

# This Channel Is For When User Request A Movie In Your Bot Then Bot Send That Movie Name In This Channel.
REQST_CHANNEL = int(environ.get('REQST_CHANNEL', '-1002412902656')) # Updated (empty, assuming 0 if not set)
# Updated REQST_CHANNEL to -1002412902656 as per user request

# This Channel Is For When User Request A Movie In Your Bot And Bot Not Found That Movie Then Bot Send That Movie Name In This Channel.
INDEX_REQ_CHANNEL = int(environ.get('INDEX_REQ_CHANNEL', '-1002802211490')) # Updated
# Updated INDEX_REQ_CHANNEL to -1002802211490 as per user request

# This Channel Is For When You Want To Store Files In Your Bot Database Then Add Your File In This Channel.
FILE_STORE_CHANNEL = int(environ.get('FILE_STORE_CHANNEL', '-1002829192804')) # Updated
# Updated FILE_STORE_CHANNEL to -1002829192804 as per user request

# This Channel Is For When You Delete Any File From Your Bot Then Bot Automatically Delete That File From This Channel.
DELETE_CHANNELS = [int(dch) for dch in environ.get('DELETE_CHANNELS', '0').split()] # Updated (assuming 0 means empty, or a specific channel ID)


# About Bot
BOT_USERNAME = environ.get('BOT_USERNAME', 'autofilterrmoviesbot')
BOT_NAME = environ.get('BOT_NAME', 'ᴄɪɴᴇʙᴏᴛ')
BOT_ID = int(environ.get('BOT_ID', '0')) # Changed default to '0' to avoid ValueError


# Database
DATABASE_URI = environ.get('DATABASE_URI', "mongodb+srv://vishnusaketh07:moviesai25@cluster0.bdifagm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0") # Keep as is, you need to provide your MongoDB URI
DATABASE_NAME = environ.get('DATABASE_NAME', "Filter-Bot")
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'Telegram_Files')

# For Multiple Database
MULTIPLE_DATABASE = bool(environ.get('MULTIPLE_DATABASE', False)) # Set True or False
FILE_DB_URI = environ.get('FILE_DB_URI', DATABASE_URI)
SEC_FILE_DB_URI = environ.get('SEC_FILE_DB_URI', "mongodb+srv://vishnusaketh07:moviesai25@cluster0.bdifagm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0") # If MULTIPLE_DATABASE is True, set this to your second DB URI

# Other Database
OTHER_DB_URI = environ.get('OTHER_DB_URI', DATABASE_URI)

# Clone Bot Database
CLONE_DATABASE_URI = environ.get('CLONE_DATABASE_URI', DATABASE_URI)


# Force Subscribtion
FORCE_SUB_MODE = bool(environ.get('FORCE_SUB_MODE', True)) # Set True or False


# Protect Content
PROTECT_CONTENT = bool(environ.get('PROTECT_CONTENT', False)) # Set True or False


# Auto Delete
AUTO_DELETE = bool(environ.get('AUTO_DELETE', False)) # Set True or False
AUTO_DELETE_TIME = int(environ.get('AUTO_DELETE_TIME', '300')) # In Seconds

# Custom Caption
CUSTOM_FILE_CAPTION = environ.get('CUSTOM_FILE_CAPTION', script.CAPTION) # Corrected from script.CUSTOM_CAPTION
BATCH_FILE_CAPTION = environ.get('BATCH_FILE_CAPTION', script.BATCH_CAPTION) # Corrected from script.BATCH_CAPTION


# IMDB Info
IMDB = bool(environ.get('IMDB', False)) # Set to False
IMDB_TEMPLATE = environ.get('IMDB_TEMPLATE', script.IMDB_TEMPLATE_TXT) # Corrected to IMDB_TEMPLATE_TXT

# Long IMDB Description (Added this line)
LONG_IMDB_DESCRIPTION = bool(environ.get('LONG_IMDB_DESCRIPTION', False)) # Set to False


# Spell Check
SPELL_CHECK_REPLY = bool(environ.get('SPELL_CHECK_REPLY', True)) # Set True or False
AI_SPELL_CHECK = bool(environ.get('AI_SPELL_CHECK', True)) # Added AI_SPELL_CHECK


# Bot PM Search
PM_SEARCH_MODE = bool(environ.get('PM_SEARCH_MODE', True)) # Set True or False


# Button Mode
BUTTON_MODE = bool(environ.get('BUTTON_MODE', True)) # Set True or False
MAX_BTN = int(environ.get('MAX_BTN', '10')) # Max 10. Corrected from MAX_B_TN
MAX_LIST_ELM = int(environ.get('MAX_LIST_ELM', '5')) # Added MAX_LIST_ELM


# Auto Filter
AUTO_FFILTER = bool(environ.get('AUTO_FFILTER', True)) # Set True or False


# Premium and Referal
PREMIUM_AND_REFERAL_MODE = bool(environ.get('PREMIUM_AND_REFERAL_MODE', False)) # Set True or False
REFERAL_COUNT = int(environ.get('REFERAL_COUNT', '5')) # How Many Refer For Premium
REFERAL_PREMEIUM_TIME = int(environ.get('REFERAL_PREMEIUM_TIME', '3600')) # In Seconds
PAYMENT_QR = environ.get('PAYMENT_QR', 'https://graph.org/file/ce1723991756e48c35aa1.jpg')
PAYMENT_TEXT = environ.get('PAYMENT_TEXT', script.PAYMENT_TXT) # Corrected to PAYMENT_TXT


# Request To Join
REQUEST_TO_JOIN_MODE = bool(environ.get('REQUEST_TO_JOIN_MODE', False)) # Set True or False
TRY_AGAIN_BTN = bool(environ.get('TRY_AGAIN_BTN', True)) # Set True or False


# Stream
STREAM_MODE = bool(environ.get('STREAM_MODE', True)) # Set True or False


# Url Shortner
SHORTLINK_MODE = bool(environ.get('SHORTLINK_MODE', False)) # Set True or False
SHORTLINK_URL = environ.get('SHORTLINK_URL', '')
SHORTLINK_API = environ.get('SHORTLINK_API', '')
VERIFY_SHORTLINK_URL = environ.get('VERIFY_SHORTLINK_URL', '') # Added
VERIFY_SHORTLINK_API = environ.get('VERIFY_SHORTLINK_API', '') # Added
VERIFY_SECOND_SHORTNER = bool(environ.get('VERIFY_SECOND_SHORTNER', False)) # Added
VERIFY_SND_SHORTLINK_URL = environ.get('VERIFY_SND_SHORTLINK_URL', '') # Added
VERIFY_SND_SHORTLINK_API = environ.get('VERIFY_SND_SHORTLINK_API', '') # Added


# Tutorial
IS_TUTORIAL = bool(environ.get('IS_TUTORIAL', False)) # Set True or False
TUTORIAL = environ.get('TUTORIAL', '')
VERIFY_TUTORIAL = environ.get('VERIFY_TUTORIAL', '')


# Clone
CLONE_MODE = bool(environ.get('CLONE_MODE', False)) # Set True or False


# Multi Client : If True Then Don't Fill.
MULTI_CLIENT = False
SLEEP_THRESHOLD = int(environ.get('SLEEP_THRESHOLD', '60'))
PING_INTERVAL = int(environ.get("PING_INTERVAL", "1200"))  # 20 minutes
if 'DYNO' in environ:
    ON_HEROKU = True
else:
    ON_HEROKU = False
URL = environ.get("URL", "https://testofvjfilter-1fa60b1b8498.herokuapp.com/")


# Port for web server
PORT = int(environ.get('PORT', '8080')) # Added PORT


# Rename Info : If True Then Bot Rename File Else Not
RENAME_MODE = bool(environ.get('RENAME_MODE', False)) # Set True or False


# Auto Approve Info : If True Then Bot Approve New Upcoming Join Request Else Not
AUTO_APPROVE_MODE = bool(environ.get('AUTO_APPROVE_MODE', False)) # Set True or False


# Banned Users & Chats
BANNED_USERS = [int(b_users) for b_users in environ.get('BANNED_USERS', '').split()]
BANNED_CHATS = [int(b_chats) for b_chats in environ.get('BANNED_CHATS', '').split()]


# IMDB Watch
IMDB_WATCH = bool(environ.get('IMDB_WATCH', False)) # Set to False

# IMDB Poster
IMDB_POSTER = bool(environ.get('IMDB_POSTER', False)) # Set to False

# IMDB Plot
IMDB_PLOT = bool(environ.get('IMDB_PLOT', False)) # Set to False

# IMDB Cast
IMDB_CAST = bool(environ.get('IMDB_CAST', False)) # Set to False

# IMDB Director
IMDB_DIRECTOR = bool(environ.get('IMDB_DIRECTOR', False)) # Set to False

# IMDB Writer
IMDB_WRITER = bool(environ.get('IMDB_WRITER', False)) # Set to False

# IMDB Producer
IMDB_PRODUCER = bool(environ.get('IMDB_PRODUCER', False)) # Set to False

# IMDB Composer
IMDB_COMPOSER = bool(environ.get('IMDB_COMPOSER', False)) # Set to False

# IMDB Cinematographer
IMDB_CINEMATOGRAPHER = bool(environ.get('IMDB_CINEMATOGRAPHER', False)) # Set to False

# IMDB Music Team
IMDB_MUSIC_TEAM = bool(environ.get('IMDB_MUSIC_TEAM', False)) # Set to False

# IMDB Distributors
IMDB_DISTRIBUTORS = bool(environ.get('IMDB_DISTRIBUTORS', False)) # Set to False

# IMDB Release Date
IMDB_RELEASE_DATE = bool(environ.get('IMDB_RELEASE_DATE', False)) # Set to False

# IMDB Year
IMDB_YEAR = bool(environ.get('IMDB_YEAR', False)) # Set to False

# IMDB Genres
IMDB_GENRES = bool(environ.get('IMDB_GENRES', False)) # Set to False

# IMDB Rating
IMDB_RATING = bool(environ.get('IMDB_RATING', False)) # Set to False

# IMDB Votes
IMDB_VOTES = bool(environ.get('IMDB_VOTES', False)) # Set to False

# IMDB Runtime
IMDB_RUNTIME = bool(environ.get('IMDB_RUNTIME', False)) # Set to False

# IMDB Countries
IMDB_COUNTRIES = bool(environ.get('IMDB_COUNTRIES', False)) # Set to False

# IMDB Languages
IMDB_LANGUAGES = bool(environ.get('IMDB_LANGUAGES', False)) # Set to False

# IMDB Certificates
IMDB_CERTIFICATES = bool(environ.get('IMDB_CERTIFICATES', False)) # Set to False

# IMDB Box Office
IMDB_BOX_OFFICE = bool(environ.get('IMDB_BOX_OFFICE', False)) # Set to False

# IMDB Localized Title
IMDB_LOCALIZED_TITLE = bool(environ.get('IMDB_LOCALIZED_TITLE', False)) # Set to False

# IMDB Kind
IMDB_KIND = bool(environ.get('IMDB_KIND', False)) # Set to False

# IMDB AKA
IMDB_AKA = bool(environ.get('IMDB_AKA', False)) # Set to False

# Welcome message for new users
MELCOW_NEW_USERS = bool(environ.get('MELCOW_NEW_USERS', True)) # Added MELCOW_NEW_USERS

# Cache Time
CACHE_TIME = int(environ.get('CACHE_TIME', 300)) # Added CACHE_TIME

# Public File Store
PUBLIC_FILE_STORE = bool(environ.get('PUBLIC_FILE_STORE', True)) # Added PUBLIC_FILE_STORE

# Support Chat
SUPPORT_CHAT = environ.get('SUPPORT_CHAT', 'luffydev2k') # Added SUPPORT_CHAT

# Owner Link
OWNER_LNK = environ.get('OWNER_LNK', 'https://t.me/luffydev2k') # Added OWNER_LNK

# Channel Link
CHNL_LNK = environ.get('CHNL_LNK', 'https://t.me/cineofcl') # Added CHNL_LNK

# Group Link
GRP_LNK = environ.get('GRP_LNK', 'https://t.me/cinebotofclgrup') # Added GRP_LNK

# Verify
VERIFY = bool(environ.get('VERIFY', False)) # Added VERIFY

# No Results Message
NO_RESULTS_MSG = bool(environ.get('NO_RESULTS_MSG', True)) # Added NO_RESULTS_MSG

# Start Command Reactions
REACTIONS = ["🤝", "😇", "🤗", "😍", "👍", "🎅", "😐", "🥰", "🤩", "😱", "🤣", "😘", "👏", "😛", "😈", "🎉", "⚡️", "🫡", "🤓", "😎", "�", "🔥", "🤭", "🌚", "🆒", "👻", "😁"] #don't add any emoji because tg not support all emoji reactions

# Use Caption Filter
USE_CAPTION_FILTER = bool(environ.get('USE_CAPTION_FILTER', True)) # Added USE_CAPTION_FILTER

# Message Alert (Added this line)
MSG_ALRT = environ.get('MSG_ALRT', "This is an alert message.") # Added MSG_ALRT

# Languages (Added this line)
LANGUAGES = [] # Added LANGUAGES

# Years (Added this line)
YEARS = [] # Added YEARS

if MULTIPLE_DATABASE == False:
    USER_DB_URI = DATABASE_URI
    OTHER_DB_URI = DATABASE_URI
    FILE_DB_URI = DATABASE_URI
    SEC_FILE_DB_URI = DATABASE_URI
    CLONE_DATABASE_URI = DATABASE_URI
