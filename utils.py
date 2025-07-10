# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import logging, asyncio, os, re, random, pytz, aiohttp, requests, string, json, http.client
from info import * # Import all from info to ensure MAX_LIST_ELM, MSG_ALRT, LANGUAGES, YEARS are included
from imdb import Cinemagoer 
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import enums
from pyrogram.errors import *
from typing import Union
from Script import script
from datetime import datetime, date
from typing import List
from database.users_chats_db import db
from database.join_reqs import JoinReqs
from bs4 import BeautifulSoup
from shortzy import Shortzy

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
join_db = JoinReqs
BTN_URL_REGEX = re.compile(r"(\[([^\[]+?)\\]\((buttonurl|buttonalert):(?:/{0,2})(.+?)(:same)?\))")

imdb = Cinemagoer() 
TOKENS = {}
VERIFIED = {}
BANNED = {}
SECOND_SHORTENER = {}
SMART_OPEN = '“'
SMART_CLOSE = '”'
START_CHAR = ('\'', '"', SMART_OPEN)

# temp db for banned 
class temp(object):
    BANNED_USERS = []
    BANNED_CHATS = []
    ME = None
    BOT = None
    CURRENT=int(os.environ.get("SKIP", 2))
    CANCEL = False
    U_NAME = None
    B_NAME = None

# get file size
def get_size(size):
    """Get size in human readable format"""
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

# get duration
def get_duration(seconds):
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    hours = seconds // 3600
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

# get file name
def get_name(name):
    if name:
        name = re.sub(r"(\s|[^a-zA-Z0-9])+", " ", name).lower()
        return name
    return None

# get hash
def get_hash(hash):
    if hash:
        hash = re.sub(r"(\s|[^a-zA-Z0-9])+", " ", hash).lower()
        return hash
    return None

# is valid url
def is_valid_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

# get shortlink
async def get_shortlink(url):
    try:
        if SHORTLINK_MODE and SHORTLINK_API and SHORTLINK_URL:
            shortzy = Shortzy(SHORTLINK_URL, SHORTLINK_API)
            short_url = await shortzy.shorten_url(url)
            return short_url
        else:
            return url
    except Exception as e:
        logger.error(f"Error shortening URL: {e}")
        return url

# get second shortlink
async def get_second_shortlink(url):
    try:
        if VERIFY_SECOND_SHORTNER and VERIFY_SND_SHORTLINK_API and VERIFY_SND_SHORTLINK_URL:
            shortzy = Shortzy(VERIFY_SND_SHORTLINK_URL, VERIFY_SND_SHORTLINK_API)
            short_url = await shortzy.shorten_url(url)
            return short_url
        else:
            return url
    except Exception as e:
        logger.error(f"Error shortening second URL: {e}")
        return url

# get verify shortlink
async def get_verify_shortlink(url):
    try:
        if VERIFY and VERIFY_SHORTLINK_API and VERIFY_SHORTLINK_URL:
            shortzy = Shortzy(VERIFY_SHORTLINK_URL, VERIFY_SHORTLINK_API)
            short_url = await shortzy.shorten_url(url)
            return short_url
        else:
            return url
    except Exception as e:
        logger.error(f"Error shortening verify URL: {e}")
        return url

# get tutorial shortlink
async def get_tutorial_shortlink(url):
    try:
        if IS_TUTORIAL and TUTORIAL and SHORTLINK_API and SHORTLINK_URL:
            shortzy = Shortzy(SHORTLINK_URL, SHORTLINK_API)
            short_url = await shortzy.shorten_url(url)
            return short_url
        else:
            return url
    except Exception as e:
        logger.error(f"Error shortening tutorial URL: {e}")
        return url

# get verify tutorial shortlink
async def get_verify_tutorial_shortlink(url):
    try:
        if VERIFY and VERIFY_TUTORIAL and VERIFY_SHORTLINK_API and VERIFY_SHORTLINK_URL:
            shortzy = Shortzy(VERIFY_SHORTLINK_URL, VERIFY_SHORTLINK_API)
            short_url = await shortzy.shorten_url(url)
            return short_url
        else:
            return url
    except Exception as e:
        logger.error(f"Error shortening verify tutorial URL: {e}")
        return url


# get buttons
def get_buttons(markup, offset, files):
    buttons = []
    for file in files:
        file_name = file["file_name"]
        file_id = file["file_id"]
        buttons.append(
            [InlineKeyboardButton(text=file_name, url=f"https://telegram.me/{temp.U_NAME}?start=files_{file_id}")]
        )
    if len(markup.inline_keyboard) > offset:
        for btn in markup.inline_keyboard[offset:]:
            buttons.append(
                [InlineKeyboardButton(text=btn.text, url=btn.url)]
            )
    return buttons

# get file caption
async def get_file_caption(file):
    caption = CUSTOM_FILE_CAPTION
    if file.get("caption"):
        caption = file["caption"]
    
    replacements = {
        "{filename}": file.get("file_name", ""),
        "{filesize}": get_size(file.get("file_size", 0)),
        "{duration}": get_duration(file.get("duration", 0)) if file.get("duration") else "",
        "{mdate}": datetime.fromtimestamp(file.get('date', 0)).strftime('%Y/%m/%d %H:%M:%S')
    }

    for key, value in replacements.items():
        caption = caption.replace(key, str(value))
    
    return caption

# get batch file caption
async def get_batch_file_caption(file):
    caption = BATCH_FILE_CAPTION
    if file.get("caption"):
        caption = file["caption"]
    
    replacements = {
        "{filename}": file.get("file_name", ""),
        "{filesize}": get_size(file.get("file_size", 0)),
        "{duration}": get_duration(file.get("duration", 0)) if file.get("duration") else "",
        "{mdate}": datetime.fromtimestamp(file.get('date', 0)).strftime('%Y/%m/%d %H:%M:%S')
    }

    for key, value in replacements.items():
        caption = caption.replace(key, str(value))
    
    return caption

# get shortlink button
async def get_shortlink_button(url, text):
    return InlineKeyboardButton(text=text, url=await get_shortlink(url))

# get verify shortlink button
async def get_verify_shortlink_button(url, text):
    return InlineKeyboardButton(text=text, url=await get_verify_shortlink(url))

# get second shortlink button
async def get_second_shortlink_button(url, text):
    return InlineKeyboardButton(text=text, url=await get_second_shortlink(url))

# get tutorial shortlink button
async def get_tutorial_shortlink_button(url, text):
    return InlineKeyboardButton(text=text, url=await get_tutorial_shortlink(url))

# get verify tutorial shortlink button
async def get_verify_tutorial_shortlink_button(url, text):
    return InlineKeyboardButton(text=text, url=await get_verify_tutorial_shortlink(url))

# get file markup
async def get_file_markup(file, shortlink_text="Download"):
    buttons = []
    if STREAM_MODE:
        stream_url = f"{URL}watch/{file['file_id']}"
        buttons.append([InlineKeyboardButton(text="Watch Online", url=stream_url)])
    
    if SHORTLINK_MODE:
        buttons.append([await get_shortlink_button(f"{URL}files/{file['file_id']}", shortlink_text)])
    else:
        buttons.append([InlineKeyboardButton(text=shortlink_text, url=f"{URL}files/{file['file_id']}")])

    return InlineKeyboardMarkup(buttons)

# get verify file markup
async def get_verify_file_markup(file, shortlink_text="Verify And Download"):
    buttons = []
    if STREAM_MODE:
        stream_url = f"{URL}watch/{file['file_id']}"
        buttons.append([InlineKeyboardButton(text="Watch Online", url=stream_url)])
    
    if VERIFY:
        buttons.append([await get_verify_shortlink_button(f"{URL}verify/{file['file_id']}", shortlink_text)])
    else:
        buttons.append([InlineKeyboardButton(text=shortlink_text, url=f"{URL}files/{file['file_id']}")])

    return InlineKeyboardMarkup(buttons)


# get imdb info
async def get_imdb_info(query, message, remaining_seconds):
    try:
        results = imdb.search_movie(query)
        if not results:
            return None, None

        movie_id = results[0].movieID
        movie = imdb.get_movie(movie_id)

        title = movie.get('title')
        year = movie.get('year')
        genres = ', '.join(movie.get('genres', []))
        rating = movie.get('rating')
        votes = movie.get('votes')
        languages = ', '.join(movie.get('languages', []))
        runtime = movie.get('runtime')[0] if movie.get('runtime') else 'N/A'
        plot = movie.get('plot outline', movie.get('plot', 'No plot available.'))
        url = imdb.get_imdbURL(movie_id)
        
        # Get release date from release info
        release_date = "N/A"
        if 'release dates' in movie:
            for country_data in movie['release dates']:
                if 'country' in country_data and country_data['country'] == 'India': # Prioritize India release date
                    release_date = country_data.get('date', 'N/A')
                    break
            if release_date == "N/A": # If India not found, take the first available
                for country_data in movie['release dates']:
                    release_date = country_data.get('date', 'N/A')
                    if release_date != "N/A":
                        break

        countries = ', '.join(movie.get('countries', []))

        # Format plot for short/long description
        if not LONG_IMDB_DESCRIPTION:
            plot = plot[:200] + '...' if len(plot) > 200 else plot

        caption = IMDB_TEMPLATE.format(
            qurey=query,
            url=url,
            title=title,
            genres=genres,
            year=year,
            rating=rating,
            votes=votes,
            languages=languages,
            runtime=runtime,
            release_date=release_date,
            countries=countries,
            plot=plot,
            remaining_seconds=remaining_seconds,
            message=message
        )
        
        poster = movie.get('full-size poster') or movie.get('cover url')
        
        return caption, poster
    except Exception as e:
        logger.error(f"Error fetching IMDB info for '{query}': {e}")
        return None, None

# get search results caption
async def get_search_results_caption(search, files, query, remaining_seconds):
    cap = ""
    if VERIFY:
        cap = f"<b>Tʜᴇ Rᴇꜱᴜʟᴛꜱ Fᴏʀ ☞ {search}\n\nRᴇǫᴜᴇsᴛᴇᴅ Bʏ ☞ {query.from_user.mention}\n\nʀᴇsᴜʟᴛ sʜᴏᴡ ɪɴ ☞ {remaining_seconds} sᴇᴄᴏɴᴅs\n\nᴘᴏᴡᴇʀᴇᴅ ʙʏ ☞ : {query.message.chat.title} \n\n⚠️ ᴀꜰᴛᴇʀ 5 ᴍɪɴᴜᴛᴇꜱ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟY ᴅᴇʟᴇᴛᴇᴅ 🗑️\n\n</b>"
        cap+="<b><u>🍿 Your Movie Files 👇</u></b>\n\n"
        for file in files:
            cap += f"<b>📁 <a href='https://telegram.me/{temp.U_NAME}?start=verify_{file['file_id']}'>[{get_size(file['file_size'])}] {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file['file_name'].split()))}\n\n</a></b>"
    else:
        cap = f"<b>Tʜᴇ Rᴇꜱᴜʟᴛꜱ Fᴏʀ ☞ {search}\n\nRᴇǫᴜᴇsᴛᴇᴅ Bʏ ☞ {query.from_user.mention}\n\nʀᴇsᴜʟᴛ sʜᴏᴡ ɪɴ ☞ {remaining_seconds} sᴇᴄᴏɴᴅs\n\nᴘᴏᴡᴇʀᴇᴅ ʙʏ ☞ : {query.message.chat.title} \n\n⚠️ ᴀꜰᴛᴇʀ 5 ᴍɪɴᴜᴛᴇꜱ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟY ᴅᴇʟᴇᴛᴇᴅ 🗑️\n\n</b>"
        cap+="<b><u>🍿 Your Movie Files 👇</u></b>\n\n"
        for file in files:
            cap += f"<b>📁 <a href='https://telegram.me/{temp.U_NAME}?start=files_{file['file_id']}'>[{get_size(file['file_size'])}] {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file['file_name'].split()))}\n\n</a></b>"
    return cap


async def get_seconds(time_string):
    def extract_value_and_unit(ts):
        value = ""
        unit = ""
        index = 0
        while index < len(ts) and ts[index].isdigit():
            value += ts[index]
            index += 1
        while index < len(ts) and ts[index].isalpha():
            unit += ts[index]
            index += 1
        return int(value), unit.lower()

    value, unit = extract_value_and_unit(time_string)

    if unit == "week" or unit == "weeks":
        return value * 7 * 24 * 60 * 60
    elif unit == "day" or unit == "days":
        return value * 24 * 60 * 60
    elif unit == "hour" or unit == "hours":
        return value * 60 * 60
    elif unit == "minute" or unit == "minutes":
        return value * 60
    elif unit == "second" or unit == "seconds":
        return value
    elif unit == "month" or unit == "months":
        return value * 30 * 24 * 60 * 60  # Approximate month length
    else:
        raise ValueError("Invalid time unit")

# Placeholder for broadcast_messages
async def broadcast_messages(client, message, users):
    """
    Placeholder function for broadcasting messages to users.
    Replace with actual implementation.
    """
    logger.info(f"Attempting to broadcast message to {len(users)} users.")
    # Example: Iterate through users and send message
    success_count = 0
    failed_count = 0
    for user_id in users:
        try:
            await client.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.id)
            success_count += 1
            await asyncio.sleep(0.1) # Small delay to avoid flood waits
        except FloodWait as e:
            logger.warning(f"FloodWait encountered: {e.value} seconds. Waiting...")
            await asyncio.sleep(e.value)
            try: # Retry after flood wait
                await client.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.id)
                success_count += 1
            except Exception as ex:
                logger.error(f"Failed to send broadcast message to user {user_id} after retry: {ex}")
                failed_count += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast message to user {user_id}: {e}")
            failed_count += 1
    logger.info(f"Broadcast to users completed. Success: {success_count}, Failed: {failed_count}")
    return success_count, failed_count

# Placeholder for broadcast_messages_group
async def broadcast_messages_group(client, message, chats):
    """
    Placeholder function for broadcasting messages to groups.
    Replace with actual implementation.
    """
    logger.info(f"Attempting to broadcast message to {len(chats)} groups.")
    # Example: Iterate through chats and send message
    success_count = 0
    failed_count = 0
    for chat_id in chats:
        try:
            await client.copy_message(chat_id=chat_id, from_chat_id=message.chat.id, message_id=message.id)
            success_count += 1
            await asyncio.sleep(0.1) # Small delay to avoid flood waits
        except FloodWait as e:
            logger.warning(f"FloodWait encountered: {e.value} seconds. Waiting...")
            await asyncio.sleep(e.value)
            try: # Retry after flood wait
                await client.copy_message(chat_id=chat_id, from_chat_id=message.chat.id, message_id=message.id)
                success_count += 1
            except Exception as ex:
                logger.error(f"Failed to send broadcast message to group {chat_id} after retry: {ex}")
                failed_count += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast message to group {chat_id}: {e}")
            failed_count += 1
    logger.info(f"Broadcast to groups completed. Success: {success_count}, Failed: {failed_count}")
    return success_count, failed_count

def get_file_id(msg: Message):
    """
    Extracts the file_id from a Pyrogram Message object.
    This is a placeholder; you might need to adjust based on your exact needs.
    """
    if msg.document:
        return msg.document.file_id
    elif msg.video:
        return msg.video.file_id
    elif msg.audio:
        return msg.audio.file_id
    elif msg.photo:
        return msg.photo.file_id
    elif msg.animation:
        return msg.animation.file_id
    elif msg.sticker:
        return msg.sticker.file_id
    elif msg.voice:
        return msg.voice.file_id
    elif msg.video_note:
        return msg.video_note.file_id
    elif msg.new_chat_photo:
        return msg.new_chat_photo[0].file_id # New chat photo is a list of photos
    return None

def parser(text):
    """
    Parses text to extract commands or specific patterns.
    This is a generic placeholder; implement your specific parsing logic.
    """
    # Example: a very simple parser that returns the text itself
    return text.strip()

def split_quotes(text: str):
    """
    Splits a string by quotes, handling escaped quotes.
    This is a common utility for parsing commands with arguments.
    """
    if not text:
        return []
    
    parts = []
    current_part = []
    in_quote = False
    escape_next = False
    
    for char in text:
        if escape_next:
            current_part.append(char)
            escape_next = False
        elif char == '\\':
            escape_next = True
        elif char == '"':
            in_quote = not in_quote
            if not in_quote and current_part: # End of quote, add part
                parts.append("".join(current_part))
                current_part = []
        elif char.isspace() and not in_quote:
            if current_part:
                parts.append("".join(current_part))
                current_part = []
        else:
            current_part.append(char)
            
    if current_part:
        parts.append("".join(current_part))
        
    return parts

def gfilterparser(text):
    """
    Parses text specifically for global filters.
    This is a placeholder; implement your specific parsing logic for gfilters.
    """
    # Example: a very simple parser that returns the text itself for gfilters
    return text.strip()
