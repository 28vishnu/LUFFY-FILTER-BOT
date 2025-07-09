# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re
import os
import asyncio
import time
import logging
import math # Import math for ceil function
from datetime import datetime, timedelta
from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, ChatPermissions, WebAppInfo, Message
from pyrogram.enums import MessageEntityType, ChatMemberStatus
from pyrogram.errors import FloodWait, UserNotParticipant, PeerIdInvalid, ChannelInvalid, MessageNotModified, MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from urllib.parse import quote_plus # Import quote_plus for URL encoding

from database.users_chats_db import db
from database.ia_filterdb import get_search_results, save_file, get_file_details, col, sec_col, get_bad_files # Import get_bad_files
from database.filters_mdb import get_filters, find_filter, del_all
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, make_inactive
from database.gfilters_mdb import find_gfilter, get_gfilters, del_allg

from utils import get_settings, is_subscribed, pub_is_subscribed, get_shortlink, get_token, check_verification, get_tutorial, get_seconds, send_all, get_cap, save_group_settings, get_poster, temp 
# Removed get_name and get_hash from utils import as they are not in utils.py.
# Placeholder implementations are added below.
from info import (
    BOT_USERNAME, FORCE_SUB_MODE, AUTH_CHANNEL, SUPPORT_CHAT,
    CHANNELS, ADMINS, CUSTOM_FILE_CAPTION, PICS, IMDB, IMDB_TEMPLATE,
    LONG_IMDB_DESCRIPTION, SPELL_CHECK_REPLY, PM_SEARCH_MODE, BUTTON_MODE, MAX_BTN,
    AUTO_FFILTER, PREMIUM_AND_REFERAL_MODE, REFERAL_COUNT, REFERAL_PREMEIUM_TIME,
    PAYMENT_QR, PAYMENT_TEXT, MELCOW_NEW_USERS, REQUEST_TO_JOIN_MODE,
    TRY_AGAIN_BTN, STREAM_MODE, SHORTLINK_MODE, SHORTLINK_URL, SHORTLINK_API,
    IS_TUTORIAL, TUTORIAL, VERIFY_TUTORIAL, MULTI_CLIENT, BOT_ID, BOT_NAME,
    PING_INTERVAL, URL, RENAME_MODE, AUTO_APPROVE_MODE, REACTIONS,
    VERIFY_SECOND_SHORTNER, VERIFY_SND_SHORTLINK_API, VERIFY_SND_SHORTLINK_URL,
    VERIFY_SHORTLINK_API, VERIFY_SHORTLINK_URL, MSG_ALRT, LANGUAGES, YEARS,
    SUPPORT_CHAT_ID # Ensure this is imported for group filter
)
from Script import script
from TechVJ.util.human_readable import get_readable_file_size # Assuming this path is correct

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

lock = asyncio.Lock()

# --- Placeholder for get_name and get_hash ---
# IMPORTANT: If these functions exist elsewhere in your project (e.g., in TechVJ.util.media_info),
# you should import them from there and remove these placeholder implementations.
# These are minimal versions to prevent ImportErrors.
def get_name(message: Message):
    """Extracts a display name from a message's media."""
    if message.document:
        return message.document.file_name
    if message.video:
        return message.video.file_name
    if message.audio:
        return message.audio.file_name
    return "Unknown File" # Fallback

def get_hash(message: Message):
    """Generates a simple hash for a message (placeholder)."""
    # This is a very basic placeholder. For real security, use a proper hashing algorithm.
    if message.document:
        return hash(message.document.file_id)
    if message.video:
        return hash(message.video.file_id)
    if message.audio:
        return hash(message.audio.file_id)
    return hash(message.id) # Fallback to message ID hash

# --- Global Variables (if not already in info.py or utils.py) ---
# These are moved here from the user's provided pm_filter.py if they were not in info.py
# If they are already in info.py, this is redundant but harmless.
# If they are meant to be dynamic, they should be handled differently.
# For now, assuming they are fixed lists.
# Note: YEARS, LANGUAGES are already imported from info.py, so these local definitions might be redundant.
# Keeping them here for now to match the user's provided file structure.
YEARS = ["2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015"]
EPISODES = ["e01", "e02", "e03", "e04", "e05", "e06", "e07", "e08", "e09", "e10"]
LANGUAGES = ["english", "hindi", "tamil", "telugu", "malayalam", "kannada", "bengali", "marathi", "gujarati", "punjabi"]
QUALITIES = ["480p", "720p", "1080p", "2160p", "hd", "fhd", "uhd"]
SEASONS = ["s01", "s02", "s03", "s04", "s05", "s06", "s07", "s08", "s09", "s10"]

FRESH = {}
BUTTON = {}
BUTTONS = {}
SPELL_CHECK = {}

# To store flood wait times for users for search
FLOOD_CAPS = {} 

# --- Message Handlers ---

@Client.on_message(filters.command(["start", "help"]) & filters.private)
async def start_and_help(client: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.full_name)
        if MELCOW_NEW_USERS:
            await client.send_message(
                LOG_CHANNEL,
                f"#NEW_USER: {message.from_user.first_name} {message.from_user.last_name or ''}\nID: {message.from_user.id}\nUsername: @{message.from_user.username or 'None'}\nDate: {message.date}"
            )
    
    # Check force subscribe
    if FORCE_SUB_MODE and not await is_subscribed(client, message):
        btn = [[InlineKeyboardButton(text="😇 Join Updates Channel 😇", url=f"https://t.me/{AUTH_CHANNEL}")]]
        if SUPPORT_CHAT:
            btn.append([InlineKeyboardButton(text="⭕ Support Group ⭕", url=f"https://t.me/{SUPPORT_CHAT}")])
        return await message.reply_text(
            text=script.JOIN_GROUP_ALERT.format(message.from_user.first_name),
            reply_markup=InlineKeyboardMarkup(btn),
            disable_web_page_preview=True
        )

    btn = [[
        InlineKeyboardButton("🔎 Search Inline 🔍", switch_inline_query_current_chat=""),
        InlineKeyboardButton("⚙️ Settings ⚙️", callback_data="settings")
    ]]
    if ADMINS and message.from_user.id in ADMINS:
        btn.append([InlineKeyboardButton("👨‍💻 Admin Panel 👨‍💻", callback_data="admin_panel")])
    
    await message.reply_photo(
        photo=PICS,
        caption=script.START_TXT.format(message.from_user.first_name, BOT_NAME),
        reply_markup=InlineKeyboardMarkup(btn)
    )

@Client.on_message(filters.command("stats") & filters.private & filters.user(ADMINS))
async def show_stats(client: Client, message: Message):
    users = await db.total_users_count()
    chats = await db.total_chat_count()
    # Assuming db.total_files_count() exists in database.users_chats_db
    # If not, you might need to implement it or use col.estimated_document_count()
    total_files = await db.total_files_count() 
    await message.reply_text(
        script.STATUS_TXT.format(users, chats, total_files)
    )

@Client.on_message(filters.command("broadcast") & filters.private & filters.user(ADMINS))
async def broadcast_message(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a message to broadcast.")
    
    users = await db.get_all_users()
    b_count = 0
    e_count = 0
    for user in users:
        try:
            await message.reply_to_message.copy(user["id"])
            b_count += 1
            await asyncio.sleep(0.5) # Small delay to prevent flood waits
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.reply_to_message.copy(user["id"])
            b_count += 1
        except Exception:
            e_count += 1
    await message.reply_text(f"Broadcast complete.\nSuccessful: {b_count}\nFailed: {e_count}")

@Client.on_message(filters.command("batch") & filters.private & filters.user(ADMINS))
async def batch_start(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to the last message of a channel/group batch to save.")
    
    if not message.reply_to_message.forward_from_chat or not message.reply_to_message.forward_from_chat.id in CHANNELS:
        return await message.reply_text("This message is not from an authorized channel.")
    
    first_id = message.reply_to_message.forward_from_message_id
    last_id = message.reply_to_message.id
    
    m = await message.reply_text("Starting batch save...")
    
    total_saved = 0
    for i in range(first_id, last_id + 1):
        try:
            msg = await client.get_messages(message.reply_to_message.forward_from_chat.id, i)
            if msg.media:
                saved, _ = await save_file(msg) # save_file returns (success_bool, inserted_id_or_error_message)
                if saved:
                    total_saved += 1
        except Exception as e:
            logger.error(f"Error saving message {i} in batch: {e}")
            continue
    
    await m.edit_text(f"Batch save complete. Saved {total_saved} files.")

# New: Handler for incoming media messages in private chat
@Client.on_message(filters.private & (filters.document | filters.video | filters.photo) & filters.incoming)
async def save_media_handler(client: Client, message: Message):
    if not message.from_user:
        return

    # Check force subscription
    if AUTH_CHANNEL and not await is_subscribed(client, message):
        try:
            invite_link = await client.create_chat_invite_link(int(AUTH_CHANNEL))
        except Exception as e:
            logger.error(f"Error creating invite link for force sub: {e}")
            await message.reply_text("Something went wrong with force subscribe channel. Please contact admin.")
            return

        btn = [[InlineKeyboardButton("ʙᴀᴄᴋᴜᴘ ᴄʜᴀɴɴᴇʟ", url=invite_link.invite_link)]]
        await message.reply_text(
            "**🕵️ ʏᴏᴜ ᴅᴏ ɴᴏᴛ ᴊᴏɪɴ ᴍʏ ʙᴀᴄᴋᴜᴘ ᴄʜᴀɴɴᴇʟ ғɪʀsᴛ ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ ᴛʜᴇɴ ᴛʀʏ ᴀɢᴀɪɴ**",
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return

    if message.media:
        m = await message.reply_text("Saving your file to database...")
        saved, result_info = await save_file(message) # result_info will be the MongoDB _id or error string
        if saved:
            await m.edit_text(f"File saved successfully! MongoDB ID: `{result_info}`")
        else:
            await m.edit_text(f"Failed to save file: {result_info}")
    else:
        await message.reply_text("I can only save documents, videos, or photos.")


@Client.on_message(filters.text & filters.private & filters.incoming)
async def auto_filter(client: Client, message: Message):
    if re.findall(r"((^|\s)/batchfile)", message.text):
        return
    
    # Check force subscribe
    if FORCE_SUB_MODE and not await is_subscribed(client, message):
        btn = [[InlineKeyboardButton(text="😇 Join Updates Channel 😇", url=f"https://t.me/{AUTH_CHANNEL}")]]
        if SUPPORT_CHAT:
            btn.append([InlineKeyboardButton(text="⭕ Support Group ⭕", url=f"https://t.me/{SUPPORT_CHAT}")])
        return await message.reply_text(
            text=script.JOIN_GROUP_ALERT.format(message.from_user.first_name),
            reply_markup=InlineKeyboardMarkup(btn),
            disable_web_page_preview=True
        )

    # Flood control for searching
    user_id = message.from_user.id
    current_time = time.time()
    if user_id in FLOOD_CAPS:
        last_search_time = FLOOD_CAPS[user_id]
        if current_time - last_search_time < 2: # 2-second cooldown
            return # Ignore rapid searches
    FLOOD_CAPS[user_id] = current_time

    query = message.text.strip()
    if not query:
        return

    # Set U_NAME and B_NAME dynamically if not already set
    if temp.U_NAME is None or temp.B_NAME is None:
        me = await client.get_me()
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name

    # Check verification if VERIFY is True and user is not premium
    if not await db.has_premium_access(user_id) and VERIFY:
        if not await check_verification(client, user_id):
            btn = [[
                InlineKeyboardButton("ᴠᴇʀɪғʏ", url=await get_token(client, user_id, f"https://telegram.me/{temp.U_NAME}?start="))
            ],[
                InlineKeyboardButton("ʜᴏᴡ ᴛᴏ ᴠᴇʀɪғʏ", url=VERIFY_TUTORIAL)
            ]]
            text = "<b>ʜᴇʏ {} 👋,\n\nʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴠᴇʀɪғɪᴇᴅ ᴛᴏᴅᴀʏ, ᴘʟᴇᴀꜱᴇ ᴄʟɪᴄᴋ ᴏɴ ᴠᴇʀɪғʏ & ɢᴇᴛ ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇꜱꜱ ғᴏʀ ᴛᴏᴅᴀʏ</b>"
            if PREMIUM_AND_REFERAL_MODE:
                text += "<b>\n\nɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴅɪʀᴇᴄᴛ ғɪʟᴇꜱ ᴡɪᴛʜᴏᴜᴛ ᴀɴy ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴꜱ ᴛʜᴇɴ ʙᴜʏ ʙᴏᴛ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ☺️\n\n💶 ꜱᴇɴᴅ /plan ᴛᴏ ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ</b>"
            await message.reply_text(
                text=text.format(message.from_user.mention),
                protect_content=True,
                reply_markup=InlineKeyboardMarkup(btn)
            )
            return

    # Normalize the query for better search results
    search_query = re.sub(r'[^\w\s]', '', query) # Remove non-alphanumeric, non-space characters
    search_query = re.sub(r'\s+', ' ', search_query).strip() # Replace multiple spaces with single space

    if not search_query:
        await message.reply_text("Please provide a valid movie name to search.")
        return

    # Call auto_filter which handles the actual search and response
    vj_search = True # Indicate that this is an AI search (for spell check logic)
    reply_msg = await message.reply_text(f"<b><i>Searching For {search_query} 🔍</i></b>")
    await auto_filter_logic(client, search_query, message, reply_msg, vj_search) # Renamed to avoid recursion

# Renamed auto_filter to auto_filter_logic to avoid direct recursion with the message handler
async def auto_filter_logic(client, query_text, message_obj, reply_msg_obj, vj_search, spoll=None):
    """
    Handles the automatic filtering logic for search queries.
    This function is crucial for search.
    """
    chat_id = message_obj.chat.id
    user_id = message_obj.from_user.id
    settings = await get_settings(chat_id)

    # Generate a unique key for this search session
    search_key = str(user_id) + "_" + str(datetime.now().timestamp()).replace(".", "")
    FRESH[search_key] = query_text # Store the original query for later pagination

    files, next_offset, total_results = await get_search_results(chat_id, query_text, offset=0, filter=True)

    if not files:
        # No results found
        if settings["spell_check"] and vj_search:
            # Call spell check if enabled and it's an AI search
            return await advantage_spell_chok(client, query_text, message_obj, reply_msg_obj, vj_search)
        else:
            if NO_RESULTS_MSG:
                reqstr = await client.get_users(user_id)
                await client.send_message(chat_id=LOG_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, query_text)))
            
            # Edit the "Searching For..." message to "No File Found" and add a close button
            await reply_msg_obj.edit_text(f"**⚠️ No File Found For Your Query - {query_text}**\n**Make Sure Spelling Is Correct.**")
            close_btn = InlineKeyboardMarkup([[InlineKeyboardButton("Close", callback_data="close_data")]])
            await reply_msg_obj.edit_reply_markup(reply_markup=close_btn)
            await asyncio.sleep(10) # Keep the message for 10 seconds
            await reply_msg_obj.delete()
            return

    # If files are found, proceed to display them
    temp.GETALL[search_key] = files
    temp.SHORT[user_id] = chat_id # Store chat_id for shortlink callback
    
    pre = 'filep' if settings['file_secure'] else 'file'
    btn = []

    if settings["button"]:
        for file in files:
            file_name = file.get("file_name", "Unknown File")
            file_size = get_readable_file_size(file.get("file_size", 0))
            btn.append([InlineKeyboardButton(f"[{file_size}] {file_name}", callback_data=f'{pre}#{file["_id"]}')]) # Use _id for database ID
    
        btn.insert(0, [
            InlineKeyboardButton('ǫᴜᴀʟɪᴛʏ', callback_data=f"qualities#{search_key}"),
            InlineKeyboardButton("ᴇᴘɪsᴏᴅᴇs", callback_data=f"episodes#{search_key}"),
            InlineKeyboardButton("sᴇᴀsᴏɴs",  callback_data=f"seasons#{search_key}")
        ])
        btn.insert(0, [
            InlineKeyboardButton("𝐒𝐞𝐧𝐝 𝐀�𝐥", callback_data=f"sendfiles#{search_key}"),
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback_data=f"languages#{search_key}"),
            InlineKeyboardButton("ʏᴇᴀʀs", callback_data=f"years#{search_key}")
        ])
    else: # Text mode, still include filter options
        btn.insert(0, [
            InlineKeyboardButton('ǫᴜᴀʟɪᴛʏ', callback_data=f"qualities#{search_key}"),
            InlineKeyboardButton("ᴇᴘɪsᴏᴅᴇs", callback_data=f"episodes#{search_key}"),
            InlineKeyboardButton("sᴇᴀsᴏɴs",  callback_data=f"seasons#{search_key}")
        ])
        btn.insert(0, [
            InlineKeyboardButton("𝐒𝐞𝐧𝐝 𝐀𝐥𝐥", callback_data=f"sendfiles#{search_key}"),
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback=f"languages#{search_key}"),
            InlineKeyboardButton("ʏᴇᴀʀs", callback_data=f"years#{search_key}")
        ])

    items_per_page = 10 if settings.get('max_btn', True) else MAX_BTN
    total_pages = math.ceil(total_results / items_per_page)
    current_page = math.ceil((offset + items_per_page) / items_per_page)

    pagination_buttons = []
    if offset > 0:
        prev_offset = offset - items_per_page
        if prev_offset < 0: prev_offset = 0
        pagination_buttons.append(InlineKeyboardButton("⌫ 𝐁𝐀𝐂𝐊", callback_data=f"next_{user_id}_{search_key}_{prev_offset}"))

    pagination_buttons.append(InlineKeyboardButton(f"{current_page} / {total_pages}", callback_data="pages"))

    if next_offset != 0: # Use n_offset for next page
        pagination_buttons.append(InlineKeyboardButton("𝐍𝐄𝐗𝐓 ➪", callback_data=f"next_{user_id}_{search_key}_{next_offset}"))

    if pagination_buttons:
        btn.append(pagination_buttons)
    else:
        btn.append([InlineKeyboardButton(text="𝐎 𝐌𝐎𝐑𝐄 𝐏𝐀𝐆𝐄𝐒 𝐀𝐕𝐀𝐈𝐋𝐀𝐁𝐋𝐄", callback_data="pages")])

    imdb_data = await get_poster(query_text, file=(files[0])['file_name']) if settings.get("imdb") else None
    
    remaining_seconds = "300" # Default for auto-delete timer

    # Use get_cap for generating the caption
    cap = await get_cap(settings, remaining_seconds, files, message_obj, total_results, query_text)

    if imdb_data and imdb_data.get('poster'):
        try:
            hehe = await reply_msg_obj.reply_photo(photo=imdb_data.get('poster'), caption=cap, reply_markup=InlineKeyboardMarkup(btn))
            await reply_msg_obj.delete()
            if settings.get('auto_delete'):
                await asyncio.sleep(300)
                await hehe.delete()
                await message_obj.delete()
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty) as e:
            logger.warning(f"Failed to send IMDB photo, falling back to text: {e}")
            poster = imdb_data.get('poster', '').replace('.jpg', "._V1_UX360.jpg")
            if poster:
                try:
                    hmm = await reply_msg_obj.reply_photo(photo=poster, caption=cap, reply_markup=InlineKeyboardMarkup(btn))
                    await reply_msg_obj.delete()
                    if settings.get('auto_delete'):
                        await asyncio.sleep(300)
                        await hmm.delete()
                        await message_obj.delete()
                except Exception as e_fallback:
                    logger.error(f"Failed to send fallback IMDB photo, sending text: {e_fallback}")
                    fek = await reply_msg_obj.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn))
                    if settings.get('auto_delete'):
                        await asyncio.sleep(300)
                        await fek.delete()
                        await message_obj.delete()
            else: # No valid poster URL, send text only
                fek = await reply_msg_obj.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn))
                if settings.get('auto_delete'):
                    await asyncio.sleep(300)
                    await fek.delete()
                    await message_obj.delete()
        except Exception as e:
            logger.exception(e)
            fek = await reply_msg_obj.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn))
            if settings.get('auto_delete'):
                await asyncio.sleep(300)
                await fek.delete()
                await message_obj.delete()
    else:
        fuk = await reply_msg_obj.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
        if settings.get('auto_delete'):
            await asyncio.sleep(300)
            await fuk.delete()
            await message_obj.delete()

async def advantage_spell_chok(client, name, msg, reply_msg, vj_search):
    mv_id = msg.id
    mv_rqst = name
    reqstr1 = msg.from_user.id if msg.from_user else 0
    reqstr = await client.get_users(reqstr1)
    settings = await get_settings(msg.chat.id)
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", msg.text, flags=re.IGNORECASE)
    query = query.strip() + " movie"
    try:
        movies = await get_poster(mv_rqst, bulk=True)
    except Exception as e:
        logger.exception(e)
        reqst_gle = mv_rqst.replace(" ", "+")
        button = [[
            InlineKeyboardButton("Gᴏᴏɢʟᴇ", url=f"https://www.google.com/search?q={reqst_gle}")
        ]]
        if NO_RESULTS_MSG:
            await client.send_message(chat_id=LOG_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, mv_rqst)))
        k = await reply_msg.edit_text(text=script.I_CUDNT.format(mv_rqst), reply_markup=InlineKeyboardMarkup(button))
        await asyncio.sleep(30)
        await k.delete()
        return
    movielist = []
    if not movies:
        reqst_gle = mv_rqst.replace(" ", "+")
        button = [[
            InlineKeyboardButton("Gᴏᴏɢʟᴇ", url=f"https://www.google.com/search?q={reqst_gle}")
        ]]
        if NO_RESULTS_MSG:
            await client.send_message(chat_id=LOG_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, mv_rqst)))
        k = await reply_msg.edit_text(text=script.I_CUDNT.format(mv_rqst), reply_markup=InlineKeyboardMarkup(button))
        await asyncio.sleep(30)
        await k.delete()
        return
    movielist += [movie.get('title') for movie in movies]
    movielist += [f"{movie.get('title')} {movie.get('year')}" for movie in movies]
    SPELL_CHECK[mv_id] = movielist
    if AI_SPELL_CHECK and vj_search:
        vj_search_new = False
        vj_ai_msg = await reply_msg.edit_text("<b><i>I Am Trying To Find Your Movie With Your Wrong Spelling.</i></b>")
        movienamelist = []
        movienamelist += [movie.get('title') for movie in movies]
        for techvj in movienamelist:
            try:
                mv_rqst = mv_rqst.capitalize()
            except Exception:
                pass
            if mv_rqst.startswith(techvj[0]):
                await auto_filter_logic(client, techvj, msg, reply_msg, vj_search_new) # Call auto_filter_logic
                break
        reqst_gle = mv_rqst.replace(" ", "+")
        button = [[
            InlineKeyboardButton("Gᴏᴏɢʟᴇ", url=f"https://www.google.com/search?q={reqst_gle}")
        ]]
        if NO_RESULTS_MSG:
            await client.send_message(chat_id=LOG_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, mv_rqst)))
        k = await reply_msg.edit_text(text=script.I_CUDNT.format(mv_rqst), reply_markup=InlineKeyboardMarkup(button))
        await asyncio.sleep(30)
        await k.delete()
        return
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=movie_name.strip(),
                    callback_data=f"spol#{reqstr1}#{k}",
                )
            ]
            for k, movie_name in enumerate(movielist)
        ]
        btn.append([InlineKeyboardButton(text="Close", callback_data=f'spol#{reqstr1}#close_spellcheck')])
        spell_check_del = await reply_msg.edit_text(
            text=script.CUDNT_FND.format(mv_rqst),
            reply_markup=InlineKeyboardMarkup(btn)
        )
        if settings.get('auto_delete'): # Use .get() for safe access
            await asyncio.sleep(600)
            await spell_check_del.delete()

async def manual_filters(client, message, text=False):
    settings = await get_settings(message.chat.id)
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            joelkb = await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                protect_content=True if settings.get("file_secure") else False,
                                reply_to_message_id=reply_id
                            )
                            if settings.get('auto_ffilter'):
                                ai_search = True
                                reply_msg = await message.reply_text(f"<b><i>Searching For {message.text} 🔍</i></b>")
                                await auto_filter_logic(client, message.text, message, reply_msg, ai_search) # Call auto_filter_logic
                                if settings.get('auto_delete'):
                                    await joelkb.delete()
                        else:
                            button = eval(btn)
                            joelkb = await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                protect_content=True if settings.get("file_secure") else False,
                                reply_to_message_id=reply_id
                            )
                            if settings.get('auto_ffilter'):
                                ai_search = True
                                reply_msg = await message.reply_text(f"<b><i>Searching For {message.text} 🔍</i></b>")
                                await auto_filter_logic(client, message.text, message, reply_msg, ai_search) # Call auto_filter_logic
                                if settings.get('auto_delete'):
                                    await joelkb.delete()
                    elif btn == "[]":
                        joelkb = await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            protect_content=True if settings.get("file_secure") else False,
                            reply_to_message_id=reply_id
                        )
                        if settings.get('auto_ffilter'):
                            ai_search = True
                            reply_msg = await message.reply_text(f"<b><i>Searching For {message.text} 🔍</i></b>")
                            await auto_filter_logic(client, message.text, message, reply_msg, ai_search) # Call auto_filter_logic
                            if settings.get('auto_delete'):
                                await joelkb.delete()
                    else:
                        button = eval(btn)
                        joelkb = await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                        if settings.get('auto_ffilter'):
                            ai_search = True
                            reply_msg = await message.reply_text(f"<b><i>Searching For {message.text} 🔍</i></b>")
                            await auto_filter_logic(client, message.text, message, reply_msg, ai_search) # Call auto_filter_logic
                            if settings.get('auto_delete'):
                                await joelkb.delete()

                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False

async def global_filters(client, message, text=False):
    settings = await get_settings(message.chat.id)
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_gfilters('gfilters')
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_gfilter('gfilters', keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            joelkb = await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_to_message_id=reply_id
                            )
                            manual = await manual_filters(client, message)
                            if manual == False:
                                settings = await get_settings(message.chat.id)
                                if settings.get('auto_ffilter'):
                                    ai_search = True
                                    reply_msg = await message.reply_text(f"<b><i>Searching For {message.text} 🔍</i></b>")
                                    await auto_filter_logic(client, message.text, message, reply_msg, ai_search) # Call auto_filter_logic
                                    if settings.get('auto_delete'):
                                        await joelkb.delete()
                        else:
                            button = eval(btn)
                            joelkb = await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                            manual = await manual_filters(client, message)
                            if manual == False:
                                settings = await get_settings(message.chat.id)
                                if settings.get('auto_ffilter'):
                                    ai_search = True
                                    reply_msg = await message.reply_text(f"<b><i>Searching For {message.text} 🔍</i></b>")
                                    await auto_filter_logic(client, message.text, message, reply_msg, ai_search) # Call auto_filter_logic
                                    if settings.get('auto_delete'):
                                        await joelkb.delete()

                    elif btn == "[]":
                        joelkb = await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )
                        manual = await manual_filters(client, message)
                        if manual == False:
                            settings = await get_settings(message.chat.id)
                            if settings.get('auto_ffilter'):
                                ai_search = True
                                reply_msg = await message.reply_text(f"<b><i>Searching For {message.text} 🔍</i></b>")
                                await auto_filter_logic(client, message.text, message, reply_msg, ai_search) # Call auto_filter_logic
                                if settings.get('auto_delete'):
                                    await joelkb.delete()

                    else:
                        button = eval(btn)
                        joelkb = await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                        manual = await manual_filters(client, message)
                        if manual == False:
                            settings = await get_settings(message.chat.id)
                            if settings.get('auto_ffilter'):
                                ai_search = True
                                reply_msg = await message.reply_text(f"<b><i>Searching For {message.text} 🔍</i></b>")
                                await auto_filter_logic(client, message.text, message, reply_msg, ai_search) # Call auto_filter_logic
                                if settings.get('auto_delete'):
                                    await joelkb.delete()

                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False


# --- Group Message Filter ---
@Client.on_message(filters.group & filters.text & filters.incoming)
async def give_filter(client, message):
    if message.chat.id != SUPPORT_CHAT_ID:
        settings = await get_settings(message.chat.id)
        chatid = message.chat.id
        user_id = message.from_user.id if message.from_user else 0
        if settings['fsub'] != None:
            try:
                btn = await pub_is_subscribed(client, message, settings['fsub'])
                if btn:
                    btn.append([InlineKeyboardButton("Unmute Me 🔕", callback_data=f"unmuteme#{int(user_id)}")])
                    await client.restrict_chat_member(chatid, message.from_user.id, ChatPermissions(can_send_messages=False))
                    await message.reply_photo(photo=random.choice(PICS), caption=f"👋 Hello {message.from_user.mention},\n\nPlease join the channel then click on unmute me button. 😇", reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
                    return
            except Exception as e:
                logger.error(f"Error in force subscribe check for group: {e}")

        # Check for global filters first
        gl = await global_filters(client, message)
        if gl == False: # If no global filter handled it
            manual = await manual_filters(client, message)
            if manual == False: # If no manual filter handled it
                settings = await get_settings(message.chat.id)
                if settings.get('auto_ffilter'): # Use .get() for safe access
                    ai_search = True
                    reply_msg = await message.reply_text(f"<b><i>Searching For {message.text} 🔍</i></b>")
                    await auto_filter_logic(client, message.text, message, reply_msg, ai_search) # Call auto_filter_logic
    else: # This block is for the SUPPORT_CHAT_ID group
        search = message.text
        temp_files, temp_offset, total_results = await get_search_results(chat_id=message.chat.id, query=search.lower(), offset=0, filter=True)
        if total_results == 0:
            return
        else:
            return await message.reply_text(f"<b>Hᴇʏ {message.from_user.mention}, {str(total_results)} ʀᴇsᴜʟᴛs ᴀʀᴇ ғᴏᴜɴᴅ ɪɴ ᴍʏ ᴅᴀᴛᴀʙᴀsᴇ ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {search}. \n\nTʜɪs ɪs ᴀ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ sᴏ ᴛʜᴀᴛ ʏᴏᴜ ᴄᴀn't ɢᴇᴛ ғɪʟᴇs ғʀᴏᴍ ʜᴇʀᴇ...\n\nJᴏɪn ᴀɴᴅ Sᴇᴀʀᴄʜ Hᴇʀᴇ - {GRP_LNK}</b>")

# --- Callback Query Handlers ---
@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    try:
        offset = int(offset)
    except ValueError:
        offset = 0
    search = FRESH.get(key)
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        return

    files, n_offset, total = await get_search_results(query.message.chat.id, search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except ValueError:
        n_offset = 0

    if not files:
        return await query.answer("🚫 No more files found for this query.", show_alert=True)

    temp.GETALL[key] = files
    temp.SHORT[query.from_user.id] = query.message.chat.id
    settings = await get_settings(query.message.chat.id)
    pre = 'filep' if settings['file_secure'] else 'file'

    btn = []
    if settings["button"]:
        for file in files:
            file_name = file.get("file_name", "Unknown File")
            file_size = get_readable_file_size(file.get("file_size", 0))
            btn.append([InlineKeyboardButton(f"[{file_size}] {file_name}", callback_data=f'{pre}#{file["_id"]}')]) # Use _id for database ID

        btn.insert(0, [
            InlineKeyboardButton('ǫᴜᴀʟɪᴛʏ', callback_data=f"qualities#{key}"),
            InlineKeyboardButton("ᴇᴘɪsᴏᴅᴇs", callback_data=f"episodes#{key}"),
            InlineKeyboardButton("sᴇᴀsᴏɴs",  callback_data=f"seasons#{key}")
        ])
        btn.insert(0, [
            InlineKeyboardButton("𝐒𝐞𝐧𝐝 𝐀𝐥𝐥", callback_data=f"sendfiles#{key}"),
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback=f"languages#{key}"),
            InlineKeyboardButton("ʏᴇᴀʀs", callback_data=f"years#{key}")
        ])
    else:
        btn.insert(0, [
            InlineKeyboardButton('ǫᴜᴀʟɪᴛʏ', callback_data=f"qualities#{key}"),
            InlineKeyboardButton("ᴇᴘɪsᴏᴅᴇs", callback_data=f"episodes#{key}"),
            InlineKeyboardButton("sᴇᴀsᴏɴs",  callback_data=f"seasons#{key}")
        ])
        btn.insert(0, [
            InlineKeyboardButton("𝐒𝐞𝐧𝐝 𝐀𝐥𝐥", callback_data=f"sendfiles#{key}"),
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback_data=f"languages#{key}"),
            InlineKeyboardButton("ʏᴇᴀʀs", callback_data=f"years#{key}")
        ])

    items_per_page = 10 if settings.get('max_btn', True) else MAX_BTN
    total_pages = math.ceil(total / items_per_page)
    current_page = math.ceil((offset + items_per_page) / items_per_page)

    pagination_buttons = []
    if offset > 0:
        prev_offset = offset - items_per_page
        if prev_offset < 0: prev_offset = 0
        pagination_buttons.append(InlineKeyboardButton("⌫ 𝐁𝐀𝐂𝐊", callback_data=f"next_{req}_{key}_{prev_offset}"))

    pagination_buttons.append(InlineKeyboardButton(f"{current_page} / {total_pages}", callback_data="pages"))

    if n_offset != 0: # Use n_offset for next page
        pagination_buttons.append(InlineKeyboardButton("𝐍𝐄𝐗𝐓 ➪", callback_data=f"next_{req}_{key}_{n_offset}"))

    if pagination_buttons:
        btn.append(pagination_buttons)
    else:
        btn.append([InlineKeyboardButton(text="𝐎 𝐌𝐎𝐑𝐄 𝐏𝐀𝐆𝐄𝐒 𝐀𝐕𝐀𝐈𝐋𝐀𝐁𝐋𝐄", callback_data="pages")])

    if not settings["button"]:
        remaining_seconds = "N/A"
        cap = await get_cap(settings, remaining_seconds, files, query, total, search)
        try:
            await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
        except MessageNotModified:
            pass
    else:
        try:
            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(btn)
            )
        except MessageNotModified:
            pass
    await query.answer()

@Client.on_callback_query(filters.regex(r"^spol"))
async def advantage_spoll_choker(bot, query):
    _, user, movie_ = query.data.split('#')
    movies = SPELL_CHECK.get(query.message.reply_to_message.id)
    if not movies:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    if movie_ == "close_spellcheck":
        return await query.message.delete()
    movie = movies[(int(movie_))]
    movie = re.sub(r"[:\-]", " ", movie)
    movie = re.sub(r"\s+", " ", movie).strip()
    await query.answer(script.TOP_ALRT_MSG)
    
    # Re-call auto_filter_logic with the corrected movie name
    vj_search = True # Indicate it's an AI search (from spell check)
    reply_msg = await query.message.edit_text(f"<b><i>Searching For {movie} 🔍</i></b>")
    await auto_filter_logic(bot, movie, query.message, reply_msg, vj_search)


# Year
@Client.on_callback_query(filters.regex(r"^years#"))
async def years_cb_handler(client: Client, query: CallbackQuery):
    try:
        if int(query.from_user.id) not in [query.message.reply_to_message.from_user.id, 0]:
            return await query.answer(
                f"⚠️ ʜᴇʟʟᴏ{query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇQᴜᴇꜱᴛ,\nʀᴇQᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
                show_alert=True,
            )
    except Exception:
        pass

    _, key = query.data.split("#")
    search = FRESH.get(key)
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    search = re.sub(r'\b\d{4}\b', '', search).strip()

    btn = []
    for i in range(0, len(YEARS), 4):
        row = []
        for j in range(4):
            if i + j < len(YEARS):
                year = YEARS[i + j]
                row.append(
                    InlineKeyboardButton(
                        text=year,
                        callback_data=f"fy#{year}#{key}"
                    )
                )
        if row:
            btn.append(row)

    btn.insert(0, [InlineKeyboardButton(text="sᴇʟᴇᴄᴛ ʏᴏᴜʀ ʏᴇᴀʀ", callback_data="ident")])
    btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ↭", callback_data=f"fy#homepage#{key}")])

    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()


@Client.on_callback_query(filters.regex(r"^fy#"))
async def filter_yearss_cb_handler(client: Client, query: CallbackQuery):
    _, year_filter, key = query.data.split("#")
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    search = FRESH.get(key)
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    original_search_cleaned = re.sub(r'\b\d{4}\b', '', search).strip()
    
    if year_filter != "homepage":
        search_with_filter = f"{original_search_cleaned} {year_filter}".strip()
    else:
        search_with_filter = original_search_cleaned


    files, offset, total_results = await get_search_results(query.message.chat.id, search_with_filter, offset=0, filter=True)
    if not files:
        await query.answer("🚫 𝗡𝗼 𝗙𝗶𝗹𝗲 𝗪𝗲𝗿𝗲 𝗙𝗼𝘂𝗻𝗱 🚫", show_alert=True)
        return

    temp.GETALL[key] = files
    settings = await get_settings(query.message.chat.id)
    pre = 'filep' if settings['file_secure'] else 'file'

    btn = []
    if settings["button"]:
        for file in files:
            file_name = file.get("file_name", "Unknown File")
            file_size = get_readable_file_size(file.get("file_size", 0))
            btn.append([InlineKeyboardButton(f"[{file_size}] {file_name}", callback_data=f'{pre}#{file["_id"]}')])

        btn.insert(0, [
            InlineKeyboardButton('ǫᴜᴀʟɪᴛʏ', callback_data=f"qualities#{key}"),
            InlineKeyboardButton("ᴇᴘɪsᴏᴅᴇs", callback_data=f"episodes#{key}"),
            InlineKeyboardButton("sᴇᴀsᴏɴs",  callback_data=f"seasons#{key}")
        ])
        btn.insert(0, [
            InlineKeyboardButton("𝐒𝐞𝐧𝐝 𝐀𝐥𝐥", callback_data=f"sendfiles#{key}"),
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback_data=f"languages#{key}"),
            InlineKeyboardButton("ʏᴇᴀʀs", callback_data=f"years#{key}")
        ])
    else:
        btn.insert(0, [
            InlineKeyboardButton('ǫᴜᴀʟɪᴛʏ', callback_data=f"qualities#{key}"),
            InlineKeyboardButton("ᴇᴘɪsᴏᴅᴇs", callback_data=f"episodes#{key}"),
            InlineKeyboardButton("sᴇᴀsᴏɴs",  callback_data=f"seasons#{key}")
        ])
        btn.insert(0, [
            InlineKeyboardButton("𝐒𝐞𝐧𝐝 𝐀𝐥𝐥", callback_data=f"sendfiles#{key}"),
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback_data=f"languages#{key}"),
            InlineKeyboardButton("ʏᴇᴀʀs", callback_data=f"years#{key}")
        ])

    items_per_page = 10 if settings.get('max_btn', True) else MAX_BTN
    total_pages = math.ceil(total_results / items_per_page)
    current_page = math.ceil((offset + items_per_page) / items_per_page)

    pagination_buttons = []
    if offset > 0:
        prev_offset = offset - items_per_page
        if prev_offset < 0: prev_offset = 0
        pagination_buttons.append(InlineKeyboardButton("⌫ 𝐁𝐀𝐂𝐊", callback_data=f"next_{query.from_user.id}_{key}_{prev_offset}"))

    pagination_buttons.append(InlineKeyboardButton(f"{current_page} / {total_pages}", callback_data="pages"))

    if offset != "" and offset != 0:
        pagination_buttons.append(InlineKeyboardButton("𝐍𝐄𝐗𝐓 ➪", callback_data=f"next_{query.from_user.id}_{key}_{offset}"))

    if pagination_buttons:
        btn.append(pagination_buttons)
    else:
        btn.append([InlineKeyboardButton(text="𝐍𝐎 𝐌𝐎𝐑𝐄 𝐏𝐀𝐆𝐄𝐒 𝐀𝐕𝐀𝐈𝐋𝐀𝐁𝐋𝐄", callback_data="pages")])

    if year_filter != "homepage":
        btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ↭", callback_data=f"fy#homepage#{key}")])

    if not settings["button"]:
        remaining_seconds = "N/A"
        cap = await get_cap(settings, remaining_seconds, files, query, total_results, search_with_filter)
        try:
            await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
        except MessageNotModified:
            pass
    else:
        try:
            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(btn)
            )
        except MessageNotModified:
            pass
    await query.answer()

# Episode
@Client.on_callback_query(filters.regex(r"^episodes#"))
async def episodes_cb_handler(client: Client, query: CallbackQuery):
    try:
        if int(query.from_user.id) not in [query.message.reply_to_message.from_user.id, 0]:
            return await query.answer(
                f"⚠️ ʜᴇʟʟᴏ{query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇQᴜᴇꜱᴛ,\nʀᴇQᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
                show_alert=True,
            )
    except Exception:
        pass

    _, key = query.data.split("#")
    search = FRESH.get(key)
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    search = re.sub(r'\b(e\d{1,2}|episode\s\d{1,2})\b', '', search, flags=re.IGNORECASE).strip()

    btn = []
    for i in range(0, len(EPISODES), 4):
        row = []
        for j in range(4):
            if i + j < len(EPISODES):
                episode = EPISODES[i + j]
                row.append(
                    InlineKeyboardButton(
                        text=episode.title(),
                        callback_data=f"fe#{episode.lower()}#{key}"
                    )
                )
        if row:
            btn.append(row)

    btn.insert(0, [InlineKeyboardButton(text="sᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴇᴘɪsᴏᴅᴇ", callback_data="ident")])
    btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ↭", callback_data=f"fe#homepage#{key}")])

    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()


@Client.on_callback_query(filters.regex(r"^fe#"))
async def filter_episodes_cb_handler(client: Client, query: CallbackQuery):
    _, episode_filter, key = query.data.split("#")
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    search = FRESH.get(key)
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    search_cleaned = re.sub(r'\b(e\d{1,2}|episode\s\d{1,2})\b', '', search, flags=re.IGNORECASE).strip()

    if episode_filter != "homepage":
        search_with_filter = f"{search_cleaned} {episode_filter}".strip()
    else:
        search_with_filter = search_cleaned


    files, offset, total_results = await get_search_results(query.message.chat.id, search_with_filter, offset=0, filter=True)
    if not files:
        await query.answer("🚫 𝗡𝗼 𝗙𝗶𝗹𝗲 𝗪𝗲𝗿𝗲 𝗙𝗼𝘂𝗻𝗱 🚫", show_alert=True)
        return

    temp.GETALL[key] = files
    settings = await get_settings(query.message.chat.id)
    pre = 'filep' if settings['file_secure'] else 'file'

    btn = []
    if settings["button"]:
        for file in files:
            file_name = file.get("file_name", "Unknown File")
            file_size = get_readable_file_size(file.get("file_size", 0))
            btn.append([InlineKeyboardButton(f"[{file_size}] {file_name}", callback_data=f'{pre}#{file["_id"]}')])

        btn.insert(0, [
            InlineKeyboardButton('ǫᴜᴀʟɪᴛʏ', callback_data=f"qualities#{key}"),
            InlineKeyboardButton("ᴇᴘɪsᴏᴅᴇs", callback_data=f"episodes#{key}"),
            InlineKeyboardButton("sᴇᴀsᴏɴs",  callback_data=f"seasons#{key}")
        ])
        btn.insert(0, [
            InlineKeyboardButton("𝐒𝐞𝐧𝐝 𝐀𝐥𝐥", callback_data=f"sendfiles#{key}"),
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback_data=f"languages#{key}"),
            InlineKeyboardButton("ʏᴇᴀʀs", callback_data=f"years#{key}")
        ])
    else:
        btn.insert(0, [
            InlineKeyboardButton('ǫᴜᴀʟɪᴛʏ', callback_data=f"qualities#{key}"),
            InlineKeyboardButton("ᴇᴘɪsᴏᴅᴇs", callback_data=f"episodes#{key}"),
            InlineKeyboardButton("sᴇᴀsᴏɴs",  callback_data=f"seasons#{key}")
        ])
        btn.insert(0, [
            InlineKeyboardButton("𝐒𝐞𝐧𝐝 𝐀𝐥𝐥", callback_data=f"sendfiles#{key}"),
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback_data=f"languages#{key}"),
            InlineKeyboardButton("ʏᴇᴀʀs", callback_data=f"years#{key}")
        ])

    items_per_page = 10 if settings.get('max_btn', True) else MAX_BTN
    total_pages = math.ceil(total_results / items_per_page)
    current_page = math.ceil((offset + items_per_page) / items_per_page)

    pagination_buttons = []
    if offset > 0:
        prev_offset = offset - items_per_page
        if prev_offset < 0: prev_offset = 0
        pagination_buttons.append(InlineKeyboardButton("⌫ 𝐁𝐀𝐂𝐊", callback_data=f"next_{query.from_user.id}_{key}_{prev_offset}"))

    pagination_buttons.append(InlineKeyboardButton(f"{current_page} / {total_pages}", callback_data="pages"))

    if offset != "" and offset != 0:
        pagination_buttons.append(InlineKeyboardButton("𝐍𝐄𝐗𝐓 ➪", callback_data=f"next_{query.from_user.id}_{key}_{offset}"))

    if pagination_buttons:
        btn.append(pagination_buttons)
    else:
        btn.append([InlineKeyboardButton(text="𝐍𝐎 𝐌𝐎𝐑𝐄 𝐏𝐀𝐆𝐄𝐒 𝐀𝐕𝐀𝐈𝐋𝐀𝐁𝐋𝐄", callback_data="pages")])

    if episode_filter != "homepage":
        btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ↭", callback_data=f"fe#homepage#{key}")])

    if not settings["button"]:
        remaining_seconds = "N/A"
        cap = await get_cap(settings, remaining_seconds, files, query, total_results, search_with_filter)
        try:
            await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
        except MessageNotModified:
            pass
    else:
        try:
            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(btn)
            )
        except MessageNotModified:
            pass
    await query.answer()


#languages
@Client.on_callback_query(filters.regex(r"^languages#"))
async def languages_cb_handler(client: Client, query: CallbackQuery):
    try:
        if int(query.from_user.id) not in [query.message.reply_to_message.from_user.id, 0]:
            return await query.answer(
                f"⚠️ ʜᴇʟʟᴏ{query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇQᴜᴇꜱᴛ,\nʀᴇQᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
                show_alert=True,
            )
    except Exception:
        pass

    _, key = query.data.split("#")
    search = FRESH.get(key)
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    for lang in LANGUAGES:
        search = re.sub(r'\b' + re.escape(lang) + r'\b', '', search, flags=re.IGNORECASE).strip()

    btn = []
    for i in range(0, len(LANGUAGES), 2):
        row = []
        if i < len(LANGUAGES):
            row.append(InlineKeyboardButton(text=LANGUAGES[i].title(), callback_data=f"fl#{LANGUAGES[i].lower()}#{key}"))
        if i + 1 < len(LANGUAGES):
            row.append(InlineKeyboardButton(text=LANGUAGES[i+1].title(), callback_data=f"fl#{LANGUAGES[i+1].lower()}#{key}"))
        if row:
            btn.append(row)

    btn.insert(0, [InlineKeyboardButton(text="👇 𝖲𝖾𝗅𝖾𝖼𝗍 𝖸𝗈𝗎𝗋 𝖫𝖺𝗇𝗀𝗎𝖺𝗀𝖾𝗌 👇", callback_data="ident")])
    btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ​↭", callback_data=f"fl#homepage#{key}")])

    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()


@Client.on_callback_query(filters.regex(r"^fl#"))
async def filter_languages_cb_handler(client: Client, query: CallbackQuery):
    _, lang_filter, key = query.data.split("#")
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    search = FRESH.get(key)
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    for lang in LANGUAGES:
        search = re.sub(r'\b' + re.escape(lang) + r'\b', '', search, flags=re.IGNORECASE).strip()

    if lang_filter != "homepage":
        search_with_filter = f"{search} {lang_filter}".strip()
    else:
        search_with_filter = search


    files, offset, total_results = await get_search_results(query.message.chat.id, search_with_filter, offset=0, filter=True)
    if not files:
        await query.answer("🚫 𝗡𝗼 𝗙𝗶𝗹𝗲 𝗪𝗲𝗿𝗲 𝗙𝗼𝘂𝗻𝗱 🚫", show_alert=True)
        return

    temp.GETALL[key] = files
    settings = await get_settings(query.message.chat.id)
    pre = 'filep' if settings['file_secure'] else 'file'

    btn = []
    if settings["button"]:
        for file in files:
            file_name = file.get("file_name", "Unknown File")
            file_size = get_readable_file_size(file.get("file_size", 0))
            btn.append([InlineKeyboardButton(f"[{file_size}] {file_name}", callback_data=f'{pre}#{file["_id"]}')])

        btn.insert(0, [
            InlineKeyboardButton('ǫᴜᴀʟɪᴛʏ', callback_data=f"qualities#{key}"),
            InlineKeyboardButton("ᴇᴘɪsᴏᴅᴇs", callback_data=f"episodes#{key}"),
            InlineKeyboardButton("sᴇᴀsᴏɴs",  callback_data=f"seasons#{key}")
        ])
        btn.insert(0, [
            InlineKeyboardButton("𝐒𝐞𝐧𝐝 𝐀𝐥𝐥", callback_data=f"sendfiles#{key}"),
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback_data=f"languages#{key}"),
            InlineKeyboardButton("ʏᴇᴀʀs", callback_data=f"years#{key}")
        ])
    else:
        btn.insert(0, [
            InlineKeyboardButton('ǫᴜᴀʟɪᴛʏ', callback_data=f"qualities#{key}"),
            InlineKeyboardButton("ᴇᴘɪsᴏᴅᴇs", callback_data=f"episodes#{key}"),
            InlineKeyboardButton("sᴇᴀsᴏɴs",  callback_data=f"seasons#{key}")
        ])
        btn.insert(0, [
            InlineKeyboardButton("𝐒𝐞𝐧𝐝 𝐀𝐥𝐥", callback_data=f"sendfiles#{key}"),
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback_data=f"languages#{key}"),
            InlineKeyboardButton("ʏᴇᴀʀs", callback_data=f"years#{key}")
        ])

    items_per_page = 10 if settings.get('max_btn', True) else MAX_BTN
    total_pages = math.ceil(total_results / items_per_page)
    current_page = math.ceil((offset + items_per_page) / items_per_page)

    pagination_buttons = []
    if offset > 0:
        prev_offset = offset - items_per_page
        if prev_offset < 0: prev_offset = 0
        pagination_buttons.append(InlineKeyboardButton("⌫ 𝐁𝐀𝐂𝐊", callback_data=f"next_{query.from_user.id}_{key}_{prev_offset}"))

    pagination_buttons.append(InlineKeyboardButton(f"{current_page} / {total_pages}", callback_data="pages"))

    if offset != "" and offset != 0:
        pagination_buttons.append(InlineKeyboardButton("𝐍𝐄𝐗𝐓 ➪", callback_data=f"next_{query.from_user.id}_{key}_{offset}"))

    if pagination_buttons:
        btn.append(pagination_buttons)
    else:
        btn.append([InlineKeyboardButton(text="𝐍𝐎 𝐌𝐎𝐑𝐄 𝐏𝐀𝐆𝐄𝐒 𝐀𝐕𝐀𝐈𝐋𝐀𝐁𝐋𝐄", callback_data="pages")])

    if lang_filter != "homepage":
        btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ↭", callback_data=f"fl#homepage#{key}")])

    if not settings["button"]:
        remaining_seconds = "N/A"
        cap = await get_cap(settings, remaining_seconds, files, query, total_results, search_with_filter)
        try:
            await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
        except MessageNotModified:
            pass
    else:
        try:
            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(btn)
            )
        except MessageNotModified:
            pass
    await query.answer()

@Client.on_callback_query(filters.regex(r"^seasons#"))
async def seasons_cb_handler(client: Client, query: CallbackQuery):
    try:
        if int(query.from_user.id) not in [query.message.reply_to_message.from_user.id, 0]:
            return await query.answer(
                f"⚠️ ʜᴇʟʟᴏ{query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇQᴜᴇꜱᴛ,\nʀᴇQᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
                show_alert=True,
            )
    except Exception:
        pass

    _, key = query.data.split("#")
    search = FRESH.get(key)
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    season_search_patterns = ["s\d{1,2}", "season\s\d{1,2}"]
    for pattern in season_search_patterns:
        search = re.sub(r'\b' + pattern + r'\b', '', search, flags=re.IGNORECASE).strip()

    btn = []
    for i in range(0, len(SEASONS), 2):
        row = []
        if i < len(SEASONS):
            row.append(InlineKeyboardButton(text=SEASONS[i].title(), callback_data=f"fs#{SEASONS[i].lower()}#{key}"))
        if i + 1 < len(SEASONS):
            row.append(InlineKeyboardButton(text=SEASONS[i+1].title(), callback_data=f"fs#{SEASONS[i+1].lower()}#{key}"))
        if row:
            btn.append(row)

    btn.insert(0, [InlineKeyboardButton(text="👇 𝖲𝖾𝗅𝖾𝖼𝗍 Season 👇", callback_data="ident")])
    btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ​↭", callback_data=f"fs#homepage#{key}")])

    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()

@Client.on_callback_query(filters.regex(r"^fs#"))
async def filter_seasons_cb_handler(client: Client, query: CallbackQuery):
    _, season_filter, key = query.data.split("#")
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    search = FRESH.get(key)
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    season_search_patterns = ["s\d{1,2}", "season\s\d{1,2}"]
    for pattern in season_search_patterns:
        search = re.sub(r'\b' + pattern + r'\b', '', search, flags=re.IGNORECASE).strip()

    if season_filter != "homepage":
        search_with_filter = f"{search} {season_filter}".strip()
    else:
        search_with_filter = search


    files, offset, total_results = await get_search_results(query.message.chat.id, search_with_filter, offset=0, filter=True)

    if not files:
        await query.answer("🚫 𝗡𝗼 𝗙𝗶𝗹𝗲 𝗪𝗲𝗿𝗲 𝗙𝗼𝘂𝗻𝗱 🚫", show_alert=True)
        return

    temp.GETALL[key] = files
    settings = await get_settings(query.message.chat.id)
    pre = 'filep' if settings['file_secure'] else 'file'

    btn = []
    if settings["button"]:
        for file in files:
            file_name = file.get("file_name", "Unknown File")
            file_size = get_readable_file_size(file.get("file_size", 0))
            btn.append([InlineKeyboardButton(f"[{file_size}] {file_name}", callback_data=f'{pre}#{file["_id"]}')])

        btn.insert(0, [
            InlineKeyboardButton('ǫᴜᴀʟɪᴛʏ', callback_data=f"qualities#{key}"),
            InlineKeyboardButton("ᴇᴘɪsᴏᴅᴇs", callback_data=f"episodes#{key}"),
            InlineKeyboardButton("sᴇᴀsᴏɴs",  callback_data=f"seasons#{key}")
        ])
        btn.insert(0, [
            InlineKeyboardButton("𝐒𝐞𝐧𝐝 𝐀𝐥𝐥", callback_data=f"sendfiles#{key}"),
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback_data=f"languages#{key}"),
            InlineKeyboardButton("ʏᴇᴀʀs", callback_data=f"years#{key}")
        ])
    else:
        btn.insert(0, [
            InlineKeyboardButton('ǫᴜᴀʟɪᴛʏ', callback_data=f"qualities#{key}"),
            InlineKeyboardButton("ᴇᴘɪsᴏᴅᴇs", callback_data=f"episodes#{key}"),
            InlineKeyboardButton("sᴇᴀsᴏɴs",  callback_data=f"seasons#{key}")
        ])
        btn.insert(0, [
            InlineKeyboardButton("𝐒𝐞𝐧𝐝 𝐀𝐥𝐥", callback_data=f"sendfiles#{key}"),
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback_data=f"languages#{key}"),
            InlineKeyboardButton("ʏᴇᴀʀs", callback_data=f"years#{key}")
        ])

    items_per_page = 10 if settings.get('max_btn', True) else MAX_BTN
    total_pages = math.ceil(total_results / items_per_page)
    current_page = math.ceil((offset + items_per_page) / items_per_page)

    pagination_buttons = []
    if offset > 0:
        prev_offset = offset - items_per_page
        if prev_offset < 0: prev_offset = 0
        pagination_buttons.append(InlineKeyboardButton("⌫ 𝐁𝐀𝐂𝐊", callback_data=f"next_{query.from_user.id}_{key}_{prev_offset}"))

    pagination_buttons.append(InlineKeyboardButton(f"{current_page} / {total_pages}", callback_data="pages"))

    if offset != "" and offset != 0:
        pagination_buttons.append(InlineKeyboardButton("𝐍𝐄𝐗𝐓 ➪", callback_data=f"next_{query.from_user.id}_{key}_{offset}"))

    if pagination_buttons:
        btn.append(pagination_buttons)
    else:
        btn.append([InlineKeyboardButton(text="𝐍𝐎 𝐌𝐎𝐑𝐄 𝐏𝐀𝐆𝐄𝐒 𝐀𝐕𝐀𝐈𝐋𝐀𝐁𝐋𝐄", callback_data="pages")])

    if season_filter != "homepage":
        btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ↭", callback_data=f"fs#homepage#{key}")])

    if not settings["button"]:
        remaining_seconds = "N/A"
        cap = await get_cap(settings, remaining_seconds, files, query, total_results, search_with_filter)
        try:
            await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
        except MessageNotModified:
            pass
    else:
        try:
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
        except MessageNotModified:
            pass
    await query.answer()

@Client.on_callback_query(filters.regex(r"^qualities#"))
async def qualities_cb_handler(client: Client, query: CallbackQuery):
    try:
        if int(query.from_user.id) not in [query.message.reply_to_message.from_user.id, 0]:
            return await query.answer(
                f"⚠️ ʜᴇʟʟᴏ{query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇQᴜᴇꜱᴛ,\nʀᴇQᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
                show_alert=True,
            )
    except Exception:
        pass

    _, key = query.data.split("#")
    search = FRESH.get(key)
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    for quality in QUALITIES:
        search = re.sub(r'\b' + re.escape(quality) + r'\b', '', search, flags=re.IGNORECASE).strip()

    btn = []
    for i in range(0, len(QUALITIES), 2):
        row = []
        if i < len(QUALITIES):
            row.append(InlineKeyboardButton(text=QUALITIES[i].title(), callback_data=f"fq#{QUALITIES[i].lower()}#{key}"))
        if i + 1 < len(QUALITIES):
            row.append(InlineKeyboardButton(text=QUALITIES[i+1].title(), callback_data=f"fq#{QUALITIES[i+1].lower()}#{key}"))
        if row:
            btn.append(row)

    btn.insert(0, [InlineKeyboardButton(text="⇊ ꜱᴇʟᴇᴄᴛ ʏᴏᴜʀ ǫᴜᴀʟɪᴛʏ ⇊", callback_data="ident")])
    btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ↭", callback_data=f"fq#homepage#{key}")])

    try:
        await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))
    except MessageNotModified:
        pass
    await query.answer()

@Client.on_callback_query(filters.regex(r"^fq#"))
async def filter_qualities_cb_handler(client: Client, query: CallbackQuery):
    _, qual_filter, key = query.data.split("#")
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    search = FRESH.get(key)
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    for quality in QUALITIES:
        search = re.sub(r'\b' + re.escape(quality) + r'\b', '', search, flags=re.IGNORECASE).strip()

    if qual_filter != "homepage":
        search_with_filter = f"{search} {qual_filter}".strip()
    else:
        search_with_filter = search


    files, offset, total_results = await get_search_results(query.message.chat.id, search_with_filter, offset=0, filter=True)
    if not files:
        await query.answer("🚫 𝗡𝗼 𝗙𝗶𝗹𝗲 𝗪𝗲𝗿𝗲 𝗙𝗼𝘂𝗻𝗱 🚫", show_alert=True)
        return

    temp.GETALL[key] = files
    settings = await get_settings(query.message.chat.id)
    pre = 'filep' if settings['file_secure'] else 'file'

    btn = []
    if settings["button"]:
        for file in files:
            file_name = file.get("file_name", "Unknown File")
            file_size = get_readable_file_size(file.get("file_size", 0))
            btn.append([InlineKeyboardButton(f"[{file_size}] {file_name}", callback_data=f'{pre}#{file["_id"]}')])

        btn.insert(0, [
            InlineKeyboardButton('ǫᴜᴀʟɪᴛʏ', callback_data=f"qualities#{key}"),
            InlineKeyboardButton("ᴇᴘɪsᴏᴅᴇs", callback_data=f"episodes#{key}"),
            InlineKeyboardButton("sᴇᴀsᴏɴs",  callback_data=f"seasons#{key}")
        ])
        btn.insert(0, [
            InlineKeyboardButton("𝐒𝐞𝐧𝐝 𝐀𝐥𝐥", callback_data=f"sendfiles#{key}"),
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback_data=f"languages#{key}"),
            InlineKeyboardButton("ʏᴇᴀʀs", callback_data=f"years#{key}")
        ])
    else:
        btn.insert(0, [
            InlineKeyboardButton('ǫᴜᴀʟɪᴛʏ', callback_data=f"qualities#{key}"),
            InlineKeyboardButton("ᴇᴘɪsᴏᴅᴇs", callback_data=f"episodes#{key}"),
            InlineKeyboardButton("sᴇᴀsᴏɴs",  callback_data=f"seasons#{key}")
        ])
        btn.insert(0, [
            InlineKeyboardButton("𝐒𝐞𝐧𝐝 𝐀𝐥𝐥", callback_data=f"sendfiles#{key}"),
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback_data=f"languages#{key}"),
            InlineKeyboardButton("ʏᴇᴀʀs", callback_data=f"years#{key}")
        ])

    items_per_page = 10 if settings.get('max_btn', True) else MAX_BTN
    total_pages = math.ceil(total_results / items_per_page)
    current_page = math.ceil((offset + items_per_page) / items_per_page)

    pagination_buttons = []
    if offset > 0:
        prev_offset = offset - items_per_page
        if prev_offset < 0: prev_offset = 0
        pagination_buttons.append(InlineKeyboardButton("⌫ 𝐁𝐀𝐂𝐊", callback_data=f"next_{query.from_user.id}_{key}_{prev_offset}"))

    pagination_buttons.append(InlineKeyboardButton(f"{current_page} / {total_pages}", callback_data="pages"))

    if offset != "" and offset != 0:
        pagination_buttons.append(InlineKeyboardButton("𝐍𝐄𝐗𝐓 ➪", callback_data=f"next_{query.from_user.id}_{key}_{offset}"))

    if pagination_buttons:
        btn.append(pagination_buttons)
    else:
        btn.append([InlineKeyboardButton(text="𝐍𝐎 𝐌𝐎𝐑𝐄 𝐏𝐀𝐆𝐄𝐒 𝐀𝐕𝐀𝐈𝐋𝐀𝐁𝐋𝐄", callback_data="pages")])

    if qual_filter != "homepage":
        btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ↭", callback_data=f"fq#homepage#{key}")])

    if not settings["button"]:
        remaining_seconds = "N/A"
        cap = await get_cap(settings, remaining_seconds, files, query, total_results, search_with_filter)
        try:
            await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
        except MessageNotModified:
            pass
    else:
        try:
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
        except MessageNotModified:
            pass
    await query.answer()

# --- Main Callback Handler (Consolidated) ---
@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    cb_data = query.data

    if cb_data == "close_data":
        await query.message.delete()
        await query.answer() # Acknowledge the callback
    elif cb_data == "get_trail":
        user_id = query.from_user.id
        free_trial_status = await db.get_free_trial_status(user_id)
        if not free_trial_status:
            await db.give_free_trail(user_id)
            new_text = "**ʏᴏᴜ ᴄᴀɴ ᴜsᴇ ꜰʀᴇᴇ ᴛʀᴀɪʟ ꜰᴏʀ 5 ᴍɪɴᴜᴛᴇs ꜰʀᴏᴍ ɴᴏᴡ 😀\n\nआप अब से 5 मिनट के लिए निःशुल्क ट्रायल का उपयोग कर सकते हैं 😀**"
            await query.message.edit_text(text=new_text)
        else:
            new_text = "**🤣 you already used free now no more free trail. please buy subscription here are our 👉 /plans**"
            await query.message.edit_text(text=new_text)
        await query.answer() # Acknowledge the callback
        return

    elif cb_data == "buy_premium":
        btn = [[
            InlineKeyboardButton("✅sᴇɴᴅ ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ ʀᴇᴄᴇɪᴘᴛ ʜᴇʀᴇ ✅", url=OWNER_LNK)
        ]]
        btn.append([InlineKeyboardButton("⚠️ᴄʟᴏsᴇ / ᴅᴇʟᴇᴛᴇ⚠️", callback_data="close_data")])
        reply_markup = InlineKeyboardMarkup(btn)
        await query.message.reply_photo(
            photo=PAYMENT_QR,
            caption=PAYMENT_TEXT,
            reply_markup=reply_markup
        )
        await query.answer() # Acknowledge the callback
        return

    elif cb_data == "gfiltersdeleteallconfirm":
        await del_allg(query.message, 'gfilters')
        await query.answer("Done !")
        return
    elif cb_data == "gfiltersdeleteallcancel":
        await query.message.reply_to_message.delete()
        await query.message.delete()
        await query.answer("Process Cancelled !")
        return
    elif cb_data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except Exception:
                    await query.message.edit_text("Mᴀᴋᴇ sᴜʀᴇ I'm ᴘʀᴇsᴇɴᴛ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ!!", quote=True)
                    return await query.answer("Error fetching chat info.", show_alert=True)
            else:
                await query.message.edit_text(
                    "I'ᴍ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴀɴʏ ɢʀᴏᴜᴘs!\nCʜᴇᴄᴋ /connections ᴏʀ ᴄᴏɴɴᴇᴄᴛ ᴛᴏ ᴀɴʏ ɢʀᴏᴜᴘs",
                    quote=True
                )
                return await query.answer("No active connections.", show_alert=True)

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            await query.answer("This command is not supported here.", show_alert=True)
            return

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("Yᴏᴜ ɴᴇᴇᴅ ᴛᴏ ʙᴇ Gʀᴏᴜᴘ Oᴡɴᴇʀ ᴏʀ ᴀɴ Aᴜᴛʜ Usᴇʀ ᴛᴏ ᴅᴏ ᴛʜᴀᴛ!", show_alert=True)
        await query.answer() # Acknowledge the callback
    elif cb_data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except Exception:
                    pass
            else:
                await query.answer("Tʜᴀᴛ's ɴᴏᴛ ғᴏʀ ʏᴏᴜ!!", show_alert=True)
        await query.answer() # Acknowledge the callback
    elif "groupcb" in cb_data:
        await query.answer()

        group_id = cb_data.split(":")[1]
        act = cb_data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Gʀᴏᴜᴘ Nᴀᴍᴇ : **{title}**\nGʀᴏᴜᴘ ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        await query.answer("Group details.", show_alert=True)
    elif "connectcb" in cb_data:
        await query.answer()

        group_id = cb_data.split(":")[1]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Cᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text('Sᴏᴍᴇ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!!', parse_mode=enums.ParseMode.MARKDOWN)
        await query.answer("Connection status updated.", show_alert=True)
    elif "disconnect" in cb_data:
        await query.answer()

        group_id = cb_data.split(":")[1]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Dɪsᴄᴏɴɴᴇᴄᴛᴇᴅ ғʀᴏᴍ **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text(
                f"Sᴏᴍᴇ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        await query.answer("Connection status updated.", show_alert=True)
    elif "deletecb" in cb_data:
        await query.answer()

        user_id = query.from_user.id
        group_id = cb_data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ᴄᴏɴɴᴇᴄᴛɪᴏɴ !"
            )
        else:
            await query.message.edit_text(
                f"Sᴏᴍᴇ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        await query.answer("Connection deleted.", show_alert=True)
    elif cb_data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "Tʜᴇʀᴇ ᴀʀᴇ ɴᴏ ᴀᴄᴛɪᴠᴇ ᴄᴏɴɴᴇᴄᴛɪᴏns!! Cᴏɴɴᴇᴄᴛ ᴛᴏ sᴏᴍᴇ ɢʀᴏᴜᴘs ғɪʀsᴛ.",
            )
            await query.answer("No active connections.", show_alert=True)
            return
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except Exception:
                pass
        if buttons:
            await query.message.edit_text(
                "Yᴏᴜʀ ᴄᴏɴɴᴇᴄᴛᴇᴅ ɢʀᴏᴜᴘ ᴅᴇᴛᴀɪʟs ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        await query.answer() # Acknowledge the callback
    elif "gfilteralert" in cb_data:
        grp_id = query.message.chat.id
        i = cb_data.split(":")[1]
        keyword = cb_data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_gfilter('gfilters', keyword)
        if alerts is not None:
            alerts = eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
        await query.answer() # Acknowledge the callback

    elif "alertmessage" in cb_data:
        grp_id = query.message.chat.id
        i = cb_data.split(":")[1]
        keyword = cb_data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
        await query.answer() # Acknowledge the callback

    elif cb_data.startswith("file"):
        clicked = query.from_user.id
        try:
            typed = query.message.reply_to_message.from_user.id
        except Exception:
            typed = query.from_user.id

        ident, file_id = cb_data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            await query.answer('Nᴏ sᴜᴄʜ ғɪʟᴇ ᴇxɪsᴛ.')
            return
        files = files_[0]
        title = files.get("file_name", "Unknown File")
        size = get_size(files.get("file_size", 0))
        f_caption = files.get("caption", "")
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name=title, file_size=size, file_caption=f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if not f_caption:
            f_caption = f"{title}"

        try:
            if settings.get('is_shortlink') and not await db.has_premium_access(query.from_user.id):
                if clicked == typed:
                    await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=short_{file_id}")
                    return
                else:
                    await query.answer(f"Hᴇʏ {query.from_user.first_name}, Tʜɪs Is NᴏT YᴏUʀ Mᴏᴠie Rᴇǫᴜᴇsᴛ. Rᴇǫᴜᴇsᴛ YᴏUʀ's !", show_alert=True)
            elif settings.get('is_shortlink') and await db.has_premium_access(query.from_user.id):
                if clicked == typed:
                    await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start={ident}_{file_id}")
                    return
                else:
                    await query.answer(f"Hᴇʏ {query.from_user.first_name}, Tʜɪs Is NᴏT YᴏUʀ Mᴏᴠie Rᴇǫᴜᴇsᴛ. Rᴇǫᴜᴇsᴛ YᴏUʀ's !", show_alert=True)

            else:
                if clicked == typed:
                    await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start={ident}_{file_id}")
                    return
                else:
                    await query.answer(f"Hᴇʏ {query.from_user.first_name}, Tʜɪs Is NᴏT YᴏUʀ Mᴏᴠie Rᴇǫᴜᴇsᴛ. Rᴇǫᴜᴇsᴛ YᴏUʀ's !", show_alert=True)
        except UserIsBlocked:
            await query.answer('Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴍᴀʜɴ !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            logger.exception(e)
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start={ident}_{file_id}")
        await query.answer() # Acknowledge the callback

    elif cb_data.startswith("sendfiles"):
        clicked = query.from_user.id
        ident, key = cb_data.split("#")
        settings = await get_settings(query.message.chat.id)
        pre = 'allfilesp' if settings.get('file_secure') else 'allfiles'
        try:
            if settings.get('is_shortlink') and not await db.has_premium_access(query.from_user.id):
                await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles1_{key}")
            elif settings.get('is_shortlink') and await db.has_premium_access(query.from_user.id):
                await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start={pre}_{key}")
                return
            else:
                await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start={pre}_{key}")

        except UserIsBlocked:
            await query.answer('Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴍᴀʜɴ !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles3_{key}")
        except Exception as e:
            logger.exception(e)
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles4_{key}")
        await query.answer() # Acknowledge the callback

    elif cb_data.startswith("unmuteme"):
        ident, userid = cb_data.split("#")
        user_id = query.from_user.id
        settings = await get_settings(int(query.message.chat.id))
        if userid == 0:
            await query.answer("You are anonymous admin !", show_alert=True)
            return
        try:
            btn = await pub_is_subscribed(client, query, settings['fsub'])
            if btn:
                await query.answer("Kindly Join Given Channel Then Click On Unmute Button", show_alert=True)
            else:
                await client.unban_chat_member(query.message.chat.id, user_id)
                await query.answer("Unmuted Successfully !", show_alert=True)
                try:
                    await query.message.delete()
                except Exception:
                    return
        except Exception:
            await query.answer("Not For Your My Dear", show_alert=True)
        await query.answer() # Acknowledge the callback

    elif cb_data.startswith("del#"):
        ident, file_id = cb_data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            await query.answer('Nᴏ sᴜᴄʜ ғɪʟᴇ ᴇxɪsᴛ.')
            return
        files = files_[0]
        title = files.get('file_name', "Unknown File")
        size = get_size(files.get('file_size', 0))
        f_caption = files.get('caption', "")
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name=title, file_size=size, file_caption=f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if not f_caption:
            f_caption = f"{title}"

        if STREAM_MODE:
            try:
                log_msg = await client.send_cached_media(chat_id=LOG_CHANNEL, file_id=file_id)
                fileName = quote_plus(get_name(log_msg)) # Using placeholder get_name
                stream = f"{URL}watch/{str(log_msg.id)}/{fileName}?hash={get_hash(log_msg)}" # Using placeholder get_hash
                download = f"{URL}{str(log_msg.id)}/{fileName}?hash={get_hash(log_msg)}" # Using placeholder get_hash
                button = [[
                    InlineKeyboardButton("• ᴅᴏᴡɴʟᴏᴀᴅ •", url=download),
                    InlineKeyboardButton('• ᴡᴀᴛᴄʜ •', url=stream)
                ],[
                    InlineKeyboardButton("• ᴡᴀᴛᴄʜ ɪɴ ᴡᴇʙ ᴀᴘᴘ •", web_app=WebAppInfo(url=stream))
                ]]
                reply_markup = InlineKeyboardMarkup(button)
            except Exception as e:
                logger.error(f"Error generating stream link for 'del#' callback: {e}")
                reply_markup = None
        else:
            reply_markup = None

        msg = await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=True if settings.get('file_secure') else False,
            reply_markup=reply_markup
        )
        btn = [[InlineKeyboardButton("✅ ɢᴇᴛ ғɪʟᴇ ᴀɢᴀɪɴ ✅", callback_data=f'del#{file_id}')]]
        k = await msg.reply(text=f"<blockquote><b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ <b><u>10 mins</u> 🫥 <i></b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs)</i>.\n\n<b><i>ᴘʟᴇᴀsᴇ ғᴏʀᴡᴀʀᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ᴏʀ ᴀɴy ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ.</i></b></div>")
        await asyncio.sleep(600)
        await msg.delete()
        await k.edit_text("<b>✅ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ɪs sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴀɢᴀɪɴ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ</b>", reply_markup=InlineKeyboardMarkup(btn))
        await query.message.delete()
        await query.answer() # Acknowledge the callback

    elif cb_data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("Jᴏɪɴ ᴏᴜʀ Bᴀᴄᴋ-ᴜᴘ ᴄʜᴀɴɴᴇʟ ᴍᴀʜɴ! 😒", show_alert=True)
            return
        ident, kk, file_id = cb_data.split("#")
        await query.answer(url=f"https://t.me/{temp.U_NAME}?start={kk}_{file_id}")
        await query.answer() # Acknowledge the callback

    elif cb_data == "pages":
        await query.answer() # Acknowledge the callback

    elif cb_data.startswith("send_fsall"):
        temp_var, key, offset = cb_data.split("#")
        search = FRESH.get(key)
        if not search:
            await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
            return
        files, n_offset, total = await get_search_results(query.message.chat.id, search, offset=int(offset), filter=True)
        await send_all(client, query.from_user.id, files, "allfiles", query.message.chat.id, query.from_user.first_name, query) # Changed ident to "allfiles"
        await query.answer(f"Hey {query.from_user.first_name}, All files on this page has been sent successfully to your PM !", show_alert=True)
        await query.answer() # Acknowledge the callback

    elif cb_data.startswith("send_fall"):
        temp_var, key, offset = cb_data.split("#")
        search = FRESH.get(key)
        if not search:
            await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
            return
        files, n_offset, total = await get_search_results(query.message.chat.id, search, offset=int(offset), filter=True)
        await send_all(client, query.from_user.id, files, "allfiles", query.message.chat.id, query.from_user.first_name, query) # Changed ident to "allfiles"
        await query.answer(f"Hey {query.from_user.first_name}, All files on this page has been sent successfully to your PM !", show_alert=True)
        await query.answer() # Acknowledge the callback

    elif cb_data.startswith("killfilesdq"):
        ident, keyword = cb_data.split("#")
        files, total = await get_bad_files(keyword)
        await query.message.edit_text("<b>File deletion process will start in 5 seconds !</b>")
        await asyncio.sleep(5)
        deleted = 0
        async with lock:
            try:
                for file in files:
                    file_ids = file["file_id"]
                    file_name = file["file_name"]
                    result = col.delete_one({'file_id': file_ids})
                    if not result.deleted_count:
                        result = sec_col.delete_one({'file_id': file_ids})
                    if result.deleted_count:
                        logger.info(f'File Found for your query {keyword}! Successfully deleted {file_name} from database.')
                    deleted += 1
                    if deleted % 50 == 0:
                        await query.message.edit_text(f"<b>Process started for deleting files from DB. Successfully deleted {str(deleted)} files from DB for your query {keyword} !\n\nPlease wait...</b>")
            except Exception as e:
                logger.exception(e)
                await query.message.edit_text(f'Error: {e}')
            else:
                await query.message.edit_text(f"<b>Process Completed for file deletion !\n\nSuccessfully deleted {str(deleted)} files from database for your query {keyword}.</b>")
        await query.answer() # Acknowledge the callback

    elif cb_data.startswith("opnsetgrp"):
        ident, grp_id = cb_data.split("#")
        userid = query.from_user.id if query.from_user else None
        st = await client.get_chat_member(grp_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and str(userid) not in ADMINS
        ):
            await query.answer("Yᴏᴜ Dᴏɴ't Hᴀᴠᴇ Tʜᴇ Rɪɢʜᴛs Tᴏ Dᴏ Tʜɪs !", show_alert=True)
            return
        title = query.message.chat.title
        settings = await get_settings(grp_id)
        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('Rᴇsᴜʟᴛ Pᴀɢᴇ',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('Bᴜᴛᴛᴏɴ' if settings["button"] else 'Tᴇxᴛ',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Pʀᴏᴛᴇᴄᴛ Cᴏɴᴛᴇɴᴛ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ Oɴ' if settings["file_secure"] else '✘ Oғғ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Iᴍᴅʙ', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ Oɴ' if settings["imdb"] else '✘ Oғғ',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Sᴘᴇʟʟ Cʜᴇᴄᴋ',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ Oɴ' if settings["spell_check"] else '✘ Oғғ',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Wᴇʟᴄᴏᴍᴇ Msɢ', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ Oɴ' if settings["welcome"] else '✘ Oғғ',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Aᴜᴛᴏ-Dᴇʟᴇᴛᴇ',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}'),
                    InlineKeyboardButton('5 Mɪɴs' if settings["auto_delete"] else '✘ Oғғ',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Aᴜᴛᴏ-Fɪʟᴛᴇʀ',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ Oɴ' if settings["auto_ffilter"] else '✘ Oғғ',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Mᴀx Bᴜᴛᴛoɴs',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}'),
                    InlineKeyboardButton('10' if settings["max_btn"] else f'{MAX_BTN}',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('SʜᴏʀᴛLɪɴᴋ',
                                         callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ Oɴ' if settings["is_shortlink"] else '✘ Oғғ',
                                         callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{str(grp_id)}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_text(
                text=f"<b>Cʜᴀɴɢᴇ Yᴏᴜʀ Sᴇᴛᴛɪɴgs Fᴏʀ {title} As Yᴏᴜʀ Wɪsʜ ⚙</b>",
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML
            )
            await query.message.edit_reply_markup(reply_markup)
        await query.answer() # Acknowledge the callback

    elif cb_data.startswith("opnsetpm"):
        ident, grp_id = cb_data.split("#")
        userid = query.from_user.id if query.from_user else None
        st = await client.get_chat_member(grp_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and str(userid) not in ADMINS
        ):
            await query.answer("Yᴏᴜ Dᴏɴ't Hᴀᴠᴇ Tʜᴇ Rɪɢʜᴛs Tᴏ Dᴏ Tʜɪs !", show_alert=True)
            return
        title = query.message.chat.title
        settings = await get_settings(grp_id)
        btn2 = [[
                 InlineKeyboardButton("Cʜᴇᴄᴋ PM", url=f"telegram.me/{temp.U_NAME}")
               ]]
        reply_markup = InlineKeyboardMarkup(btn2)
        await query.message.edit_text(f"<b>Yᴏᴜʀ sᴇᴛᴛɪɴgs ᴍᴇɴᴜ ғᴏʀ {title} ʜᴀs ʙᴇᴇɴ sᴇɴᴛ ᴛᴏ ʏᴏᴜʀ PM</b>")
        await query.message.edit_reply_markup(reply_markup)
        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('Rᴇsᴜʟᴛ Pᴀɢᴇ',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('Bᴜᴛᴛᴏɴ' if settings["button"] else 'Tᴇxᴛ',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Pʀᴏᴛᴇᴄᴛ Cᴏɴᴛᴇɴᴛ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ Oɴ' if settings["file_secure"] else '✘ Oғғ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Iᴍᴅʙ', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ Oɴ' if settings["imdb"] else '✘ Oғғ',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Sᴘᴇʟʟ Cʜᴇᴄᴋ',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ Oɴ' if settings["spell_check"] else '✘ Oғғ',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Wᴇʟᴄᴏᴍᴇ Msɢ', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ Oɴ' if settings["welcome"] else '✘ Oғғ',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Aᴜᴛᴏ-Dᴇʟᴇᴛᴇ',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}'),
                    InlineKeyboardButton('5 Mɪɴs' if settings["auto_delete"] else '✘ Oғғ',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Aᴜᴛᴏ-Fɪʟᴛᴇʀ',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ Oɴ' if settings["auto_ffilter"] else '✘ Oғғ',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Mᴀx Bᴜᴛᴛoɴs',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}'),
                    InlineKeyboardButton('10' if settings["max_btn"] else f'{MAX_BTN}',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('SʜᴏʀᴛLɪɴᴋ',
                                         callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ Oɴ' if settings["is_shortlink"] else '✘ Oғғ',
                                         callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{str(grp_id)}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await client.send_message(
                chat_id=userid,
                text=f"<b>Cʜᴀɴɢᴇ Yᴏᴜʀ Sᴇᴛᴛɪɴgs Fᴏʀ {title} As Yᴏᴜʀ Wɪsʜ ⚙</b>",
                reply_markup=reply_markup,
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
                reply_to_message_id=query.message.id
            )
        await query.answer() # Acknowledge the callback

    elif cb_data.startswith("show_option"):
        ident, from_user = cb_data.split("#")
        btn = [[
                InlineKeyboardButton("Uɴᴀᴠᴀɪʟᴀʙʟᴇ", callback_data=f"unavailable#{from_user}"),
                InlineKeyboardButton("Uᴘʟᴏᴀᴅᴇᴅ", callback_data=f"uploaded#{from_user}")
             ],[
                InlineKeyboardButton("Aʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ", callback_data=f"already_available#{from_user}")
              ]]
        link_placeholder = "https://t.me/your_channel_link"
        btn2 = [[
                 InlineKeyboardButton('Jᴏɪɴ Cʜᴀɴɴᴇʟ', url=link_placeholder),
                 InlineKeyboardButton("Vɪᴇᴡ Sᴛᴀᴛᴜs", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Hᴇʀᴇ ᴀʀᴇ ᴛʜᴇ ᴏᴘᴛɪᴏɴs !")
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ't ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)
        await query.answer() # Acknowledge the callback

    elif cb_data.startswith("unavailable"):
        ident, from_user = cb_data.split("#")
        btn = [[
                InlineKeyboardButton("⚠️ Uɴᴀᴠᴀɪʟᴀʙʟᴇ ⚠️", callback_data=f"unalert#{from_user}")
              ]]
        link_placeholder = "https://t.me/your_channel_link"
        btn2 = [[
                 InlineKeyboardButton('Jᴏɪɴ Cʜᴀɴɴᴇʟ', url=link_placeholder),
                 InlineKeyboardButton("Vɪᴇᴡ Sᴛᴀᴛᴜs", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Uɴᴀᴠᴀɪʟᴀʙʟᴇ !")
            try:
                await client.send_message(chat_id=int(from_user), text=f"<b>Hᴇʏ {user.mention}, Sᴏʀʀʏ Yᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ ɪs ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ. Sᴏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs ᴄᴀɴ't ᴜᴘʟᴏᴀᴅ ɪᴛ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=f"<b>Hᴇʏ {user.mention}, Sᴏʀʀʏ Yᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ ɪs ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ. Sᴏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs ᴄᴀɴ't ᴜᴘʟᴏᴀᴅ ɪᴛ.\n\nNᴏᴛᴇ: Tʜɪs ᴍᴇssᴀɢᴇ ɪs sᴇɴᴛ ᴛᴏ ᴛʜɪs ɢʀᴏᴜᴘ ʙᴇᴄᴀᴜsᴇ ʏᴏᴜ'ᴠᴇ ʙʟᴏᴄᴋᴇᴅ ᴛʜᴇ ʙᴏᴛ. Tᴏ sᴇɴᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ PM, Mᴜsᴛ ᴜɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ't ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)
        await query.answer() # Acknowledge the callback

    elif cb_data.startswith("uploaded"):
        ident, from_user = cb_data.split("#")
        btn = [[
                InlineKeyboardButton("✅ Uᴘʟᴏᴀᴅᴇᴅ ✅", callback_data=f"upalert#{from_user}")
              ]]
        link_placeholder = "https://t.me/your_channel_link"
        btn2 = [[
                 InlineKeyboardButton('Jᴏɪɴ Cʜᴀɴɴᴇʟ', url=link_placeholder),
                 InlineKeyboardButton("Vɪᴇᴡ Sᴛᴀᴛᴜs", url=f"{query.message.link}")
               ],[
                 InlineKeyboardButton("Rᴇᴏ̨ᴜᴇsᴛ Gʀᴏᴜᴘ Lɪɴᴋ", url="https://t.me/+KzbVzahVdqQ3MmM1")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Uᴘʟᴏᴀᴅᴇᴅ !")
            try:
                await client.send_message(chat_id=int(from_user), text=f"<b>Hᴇʏ {user.mention}, Yᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ ʜᴀs ʙᴇᴇɴ ᴜᴘʟᴏᴀᴅᴇᴅ ʙʏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs. Kɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=f"<b>Hᴇʏ {user.mention}, Yᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ ʜᴀs ʙᴇᴇɴ ᴜᴘʟᴏᴀᴅᴇᴅ ʙʏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs. Kɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.\n\nNᴏᴛᴇ: Tʜɪs ᴍᴇssᴀɢᴇ ɪs sᴇɴᴛ ᴛᴏ ᴛʜɪs ɢʀᴏᴜᴘ ʙᴇᴄᴀᴜsᴇ ʏᴏᴜ'ᴠᴇ ʙʟᴏᴄᴋᴇᴅ ᴛʜᴇ ʙᴏᴛ. Tᴏ sᴇɴᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ PM, Mᴜsᴛ ᴜɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ't ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)
        await query.answer() # Acknowledge the callback

    elif cb_data.startswith("already_available"):
        ident, from_user = cb_data.split("#")
        btn = [[
            InlineKeyboardButton("🟢 Aʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ 🟢", callback_data=f"alalert#{from_user}")
        ]]
        link_placeholder = "https://t.me/your_channel_link"
        btn2 = [[
            InlineKeyboardButton('Jᴏɪɴ Cʜᴀɴɴᴇʟ', url=link_placeholder),
            InlineKeyboardButton("Vɪᴇᴡ Sᴛᴀᴛᴜs", url=f"{query.message.link}")
        ],[
            InlineKeyboardButton("Rᴇᴏ̨ᴜᴇsᴛ Gʀᴏᴜᴘ Lɪɴᴋ", url="https://t.me/vj_bots")
        ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Aʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ !")
            try:
                await client.send_message(chat_id=int(from_user), text=f"<b>Hᴇʏ {user.mention}, Yᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ ɪs ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ ᴏɴ ᴏᴜʀ ʙᴏᴛ's ᴅᴀᴛᴀʙᴀsᴇ. Kɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=f"<b>Hᴇʏ {user.mention}, Yᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ ɪs ᴀʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ ᴏɴ ᴏᴜʀ ʙᴏᴛ's ᴅᴀᴛᴀʙᴀsᴇ. Kɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.\n\nNᴏᴛᴇ: Tʜɪs ᴍᴇssᴀɢᴇ ɪs sᴇɴᴛ ᴛᴏ ᴛʜɪs ɢʀᴏᴜᴘ ʙᴇᴄᴀᴜsᴇ ʏᴏᴜ'ᴠᴇ ʙʟᴏᴄᴋᴇᴅ ᴛʜᴇ ʙᴏᴛ. Tᴏ sᴇɴᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ PM, Mᴜsᴛ ᴜɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ't ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)
        await query.answer() # Acknowledge the callback

    elif cb_data.startswith("alalert"):
        ident, from_user = cb_data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Hᴇʏ {user.first_name}, Yᴏᴜʀ Rᴇᴏ̨ᴜᴇsᴛ ɪs Aʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ !", show_alert=True)
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ't ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)
        await query.answer() # Acknowledge the callback

    elif cb_data.startswith("upalert"):
        ident, from_user = cb_data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Hᴇʏ {user.first_name}, Yᴏᴜʀ Rᴇᴏ̨ᴜᴇsᴛ ɪs Uᴘʟᴏᴀᴅᴇᴅ !", show_alert=True)
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ't ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)
        await query.answer() # Acknowledge the callback

    elif cb_data.startswith("unalert"):
        ident, from_user = cb_data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Hᴇʏ {user.first_name}, Yᴏᴜʀ Rᴇᴏ̨ᴜᴇsᴛ ɪs Uɴᴀᴠᴀɪʟᴀʙʟᴇ !", show_alert=True)
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ't ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)
        await query.answer() # Acknowledge the callback

    elif cb_data.startswith("generate_stream_link"):
        _, file_id = cb_data.split(":")
        try:
            log_msg = await client.send_cached_media(chat_id=LOG_CHANNEL, file_id=file_id)
            fileName = quote_plus(get_name(log_msg)) # Using placeholder get_name
            stream = f"{URL}watch/{str(log_msg.id)}/{fileName}?hash={get_hash(log_msg)}" # Using placeholder get_hash
            download = f"{URL}{str(log_msg.id)}/{fileName}?hash={get_hash(log_msg)}" # Using placeholder get_hash
            button = [[
                InlineKeyboardButton("• ᴅᴏᴡɴʟᴏᴀᴅ •", url=download),
                InlineKeyboardButton('• ᴡᴀᴛᴄʜ •', url=stream)
            ],[
                InlineKeyboardButton("• ᴡᴀᴛᴄʜ ɪɴ ᴡᴇʙ ᴀᴘᴘ •", web_app=WebAppInfo(url=stream))
            ]]
            await query.message.edit_reply_markup(InlineKeyboardMarkup(button))
        except Exception as e:
            logger.error(f"Error generating stream link: {e}")
            await query.answer(f"Something went wrong while generating stream link.\nError: {e}", show_alert=True)
            return
        await query.answer() # Acknowledge the callback

    elif cb_data == "reqinfo":
        await query.answer(text=script.REQINFO, show_alert=True)

    elif cb_data == "select":
        await query.answer(text=script.SELECT, show_alert=True)

    elif cb_data == "sinfo":
        await query.answer(text=script.SINFO, show_alert=True)

    elif cb_data == "start":
        buttons = []
        if PREMIUM_AND_REFERAL_MODE:
            buttons.extend([[
                InlineKeyboardButton('⤬ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ⤬', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
            ],[
                InlineKeyboardButton('ᴇᴀʀɴ ᴍᴏɴᴇʏ', callback_data="shortlink_info"),
                InlineKeyboardButton('ᴍᴏᴠɪᴇ ɢʀᴏᴜᴘ', url=GRP_LNK)
            ],[
                InlineKeyboardButton('ʜᴇʟᴘ', callback_data='help'),
                InlineKeyboardButton('ᴀʙᴏᴜᴛ', callback_data='about')
            ],[
                InlineKeyboardButton('ᴘʀᴇᴍɪᴜᴍ ᴀɴᴅ ʀᴇғᴇʀʀᴀʟ', callback_data='subscription')
            ],[
                InlineKeyboardButton('ᴊᴏɪɴ ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url=CHNL_LNK)
            ]])
        else:
            buttons.extend([[
                InlineKeyboardButton('⤬ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ⤬', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
            ],[
                InlineKeyboardButton('ᴇᴀʀɴ ᴍᴏɴᴇʏ', callback_data="shortlink_info"),
                InlineKeyboardButton('ᴍᴏᴠɪᴇ ɢʀᴏᴜᴘ', url=GRP_LNK)
            ],[
                InlineKeyboardButton('ʜᴇʟᴘ', callback_data='help'),
                InlineKeyboardButton('ᴀʙᴏᴜᴛ', callback_data='about')
            ],[
                InlineKeyboardButton('ᴊᴏɪɴ ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url=CHNL_LNK)
            ]])
        if CLONE_MODE:
            buttons.append([InlineKeyboardButton('ᴄʀᴇᴀᴛᴇ ᴏᴡɴ ᴄʟᴏɴᴇ ʙᴏᴛ', callback_data='clone')])
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Start menu loaded.", show_alert=True)

    elif cb_data == "clone":
        buttons = [[
            InlineKeyboardButton('⟸ Bᴀᴄᴋ', callback_data='start')
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CLONE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Clone info loaded.", show_alert=True)

    elif cb_data == "filters":
        buttons = [[
            InlineKeyboardButton('Mᴀɴᴜᴀʟ FIʟᴛᴇʀ', callback_data='manuelfilter'),
            InlineKeyboardButton('Aᴜᴛᴏ FIʟᴛᴇʀ', callback_data='autofilter')
        ],[
            InlineKeyboardButton('⟸ Bᴀᴄᴋ', callback_data='help'),
            InlineKeyboardButton('Gʟᴏʙᴀʟ Fɪʟᴛᴇʀs', callback_data='global_filters')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.ALL_FILTERS.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Filters menu loaded.", show_alert=True)

    elif cb_data == "global_filters":
        buttons = [[
            InlineKeyboardButton('⟸ Bᴀᴄᴋ', callback_data='filters')
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.GFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Global filters info loaded.", show_alert=True)

    elif cb_data == "help":
        buttons = [[
             InlineKeyboardButton('⚙️ ᴀᴅᴍɪɴ ᴏɴʟʏ 🔧', callback_data='admin'),
         ], [
             InlineKeyboardButton('ʀᴇɴᴀᴍᴇ', callback_data='r_txt'),
             InlineKeyboardButton('sᴛʀᴇᴀᴍ/ᴅᴏᴡɴʟᴏᴀᴅ', callback_data='s_txt')
         ], [
             InlineKeyboardButton('ꜰɪʟᴇ ꜱᴛᴏʀᴇ', callback_data='store_file'),
             InlineKeyboardButton('ᴛᴇʟᴇɢʀᴀᴘʜ', callback_data='tele')
         ], [
             InlineKeyboardButton('ᴄᴏɴɴᴇᴄᴛɪᴏɴꜱ', callback_data='coct'),
             InlineKeyboardButton('ꜰɪʟᴛᴇʀꜱ', callback_data='filters')
         ], [
             InlineKeyboardButton('ʏᴛ-ᴅʟ', callback_data='ytdl'),
             InlineKeyboardButton('ꜱʜᴀʀᴇ ᴛᴇxᴛ', callback_data='share')
         ], [
             InlineKeyboardButton('ꜱᴏɴɢ', callback_data='song'),
             InlineKeyboardButton('ᴇᴀʀɴ ᴍᴏɴᴇʏ', callback_data='shortlink_info')
         ], [
             InlineKeyboardButton('ꜱᴛɪᴄᴋᴇʀ-ɪᴅ', callback_data='sticker'),
             InlineKeyboardButton('ᴊ-ꜱᴏɴ', callback_data='json')
         ], [
             InlineKeyboardButton('🏠 𝙷𝙾ᴍ𝙴 🏠', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.HELP_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Help menu loaded.", show_alert=True)

    elif cb_data == "about":
        buttons = [[
            InlineKeyboardButton('Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ', url=GRP_LNK),
            InlineKeyboardButton('Sᴏᴜʀᴄᴇ Cᴏᴅᴇ', url=SOURCE_CODE_LNK)
        ],[
            InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start'),
            InlineKeyboardButton('Cʟᴏsᴇ', callback_data='close_data')
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(BOT_NAME, BOT_USERNAME, OWNER_LNK),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("About info loaded.", show_alert=True)

    elif cb_data == "subscription":
        buttons = [[
            InlineKeyboardButton('⇚Back', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.SUBSCRIPTION_TXT.format(REFERAL_PREMEIUM_TIME, temp.U_NAME, query.from_user.id, REFERAL_COUNT),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Subscription info loaded.", show_alert=True)

    elif cb_data == "manuelfilter":
        buttons = [[
            InlineKeyboardButton('⟸ Bᴀᴄᴋ', callback_data='filters'),
            InlineKeyboardButton('Bᴜᴛᴛᴏɴs', callback_data='button')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.MANUELFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Manual filter info loaded.", show_alert=True)

    elif cb_data == "button":
        buttons = [[
            InlineKeyboardButton('⟸ Bᴀᴄᴋ', callback_data='manuelfilter')
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.BUTTON_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Button info loaded.", show_alert=True)

    elif cb_data == "autofilter":
        buttons = [[
            InlineKeyboardButton('⟸ Bᴀᴄᴋ', callback_data='filters')
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.AUTOFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Auto filter info loaded.", show_alert=True)

    elif cb_data == "coct":
        buttons = [[
            InlineKeyboardButton('⟸ Bᴀᴄᴋ', callback_data='help')
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CONNECTION_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Connections info loaded.", show_alert=True)

    elif cb_data == "admin":
        buttons = [[
            InlineKeyboardButton('⟸ Bᴀᴄᴋ', callback_data='help'),
            InlineKeyboardButton('ᴇxᴛʀᴀ', callback_data='extra')
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ADMIN_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Admin menu loaded.", show_alert=True)

    elif cb_data == "store_file":
        buttons = [[
            InlineKeyboardButton('⟸ Bᴀᴄᴋ', callback_data='help')
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.FILE_STORE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("File store info loaded.", show_alert=True)

    elif cb_data == "r_txt":
        buttons = [[
            InlineKeyboardButton('⟸ Bᴀᴄᴋ', callback_data='help')
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.RENAME_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Rename info loaded.", show_alert=True)

    elif cb_data == "s_txt":
        buttons = [[
            InlineKeyboardButton('⟸ Bᴀᴄᴋ', callback_data='help')
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.STREAM_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Stream info loaded.", show_alert=True)

    elif cb_data == "extra":
        buttons = [[
            InlineKeyboardButton('⟸ Bᴀᴄᴋ', callback_data='admin')
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.EXTRAMOD_TXT.format(OWNER_LNK, CHNL_LNK),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Extra modes info loaded.", show_alert=True)

    elif cb_data == "stats":
        buttons = [[
            InlineKeyboardButton('⟸ Bᴀᴄᴋ', callback_data='help'),
            InlineKeyboardButton('⟲ Rᴇғʀᴇsʜ', callback_data='rfrsh')
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        total_users = await db.total_users_count()
        totl_chats = await db.total_chat_count()
        filesp = await col.count_documents({}) # Use await for motor
        totalsec = await sec_col.count_documents({}) if sec_col else 0 # Use await and check if sec_col exists
        try:
            stats = await col.database.command('dbStats') # Use await
            used_dbSize = (stats['dataSize']/(1024*1024))+(stats['indexSize']/(1024*1024))
            free_dbSize = 512-used_dbSize
        except Exception:
            used_dbSize = 0
            free_dbSize = 0
        try:
            stats2 = await sec_col.database.command('dbStats') if sec_col else {} # Use await and check
            used_dbSize2 = (stats2.get('dataSize', 0)/(1024*1024))+(stats2.get('indexSize', 0)/(1024*1024))
            free_dbSize2 = 512-used_dbSize2
        except Exception:
            used_dbSize2 = 0
            free_dbSize2 = 0
        try:
            stats3 = await db.client.admin.command('dbStats', db.name) # Use await
            used_dbSize3 = (stats3['dataSize']/(1024*1024))+(stats3['indexSize']/(1024*1024))
            free_dbSize3 = 512-used_dbSize3
        except Exception:
            used_dbSize3 = 0
            free_dbSize3 = 0

        await query.message.edit_text(
            text=script.STATUS_TXT.format((int(filesp)+int(totalsec)), total_users, totl_chats, filesp, round(used_dbSize, 2), round(free_dbSize, 2), totalsec, round(used_dbSize2, 2), round(free_dbSize2, 2), round(used_dbSize3, 2), round(free_dbSize3, 2)),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Stats loaded.", show_alert=True)

    elif cb_data == "rfrsh":
        await query.answer("Fetching MongoDb DataBase")
        buttons = [[
            InlineKeyboardButton('⟸ Bᴀᴄᴋ', callback_data='help'),
            InlineKeyboardButton('⟲ Rᴇғʀᴇsʜ', callback_data='rfrsh')
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        total_users = await db.total_users_count()
        totl_chats = await db.total_chat_count()
        filesp = await col.count_documents({}) # Use await for motor
        totalsec = await sec_col.count_documents({}) if sec_col else 0 # Use await and check if sec_col exists
        try:
            stats = await col.database.command('dbStats') # Use await
            used_dbSize = (stats['dataSize']/(1024*1024))+(stats['indexSize']/(1024*1024))
            free_dbSize = 512-used_dbSize
        except Exception:
            used_dbSize = 0
            free_dbSize = 0
        try:
            stats2 = await sec_col.database.command('dbStats') if sec_col else {} # Use await and check
            used_dbSize2 = (stats2.get('dataSize', 0)/(1024*1024))+(stats2.get('indexSize', 0)/(1024*1024))
            free_dbSize2 = 512-used_dbSize2
        except Exception:
            used_dbSize2 = 0
            free_dbSize2 = 0
        try:
            stats3 = await db.client.admin.command('dbStats', db.name) # Use await
            used_dbSize3 = (stats3['dataSize']/(1024*1024))+(stats3['indexSize']/(1024*1024))
            free_dbSize3 = 512-used_dbSize3
        except Exception:
            used_dbSize3 = 0
            free_dbSize3 = 0

        await query.message.edit_text(
            text=script.STATUS_TXT.format((int(filesp)+int(totalsec)), total_users, totl_chats, filesp, round(used_dbSize, 2), round(free_dbSize, 2), totalsec, round(used_dbSize2, 2), round(free_dbSize2, 2), round(used_dbSize3, 2), round(free_dbSize3, 2)),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Stats refreshed.", show_alert=True)

    elif cb_data == "shortlink_info":
        btn = [[
            InlineKeyboardButton("👇Select Your Language 👇", callback_data="laninfo")
        ],[
            InlineKeyboardButton("Tamil", callback_data="tamil_info"),
            InlineKeyboardButton("English", callback_data="english_info"),
            InlineKeyboardButton("Hindi", callback_data="hindi_info")
        ],[
            InlineKeyboardButton("Malayalam", callback_data="malayalam_info"),
            InlineKeyboardButton("Urdu", callback_data="urdu_info"),
            InlineKeyboardButton("Bangla", callback_data="bangladesh_info")
        ],[
            InlineKeyboardButton("Telugu", callback_data="telugu_info"),
            InlineKeyboardButton("Kannada", callback_data="kannada_info"),
            InlineKeyboardButton("Gujarati", callback_data="gujarati_info")
        ],[
            InlineKeyboardButton("⟸ Bᴀᴄᴋ", callback_data="start")
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(btn)
        await query.message.edit_text(
            text=(script.SHORTLINK_INFO),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Shortlink info loaded.", show_alert=True)

    elif cb_data == "tele":
        btn = [[
            InlineKeyboardButton("⟸ Bᴀᴄᴋ", callback_data="help"),
            InlineKeyboardButton("Cᴏɴᴛᴀᴄᴛ", url=OWNER_LNK)
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(btn)
        await query.message.edit_text(
            text=(script.TELE_TXT),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Telegraph info loaded.", show_alert=True)

    elif cb_data == "ytdl":
        buttons = [[
            InlineKeyboardButton('⇍ ʙᴀᴄᴋ ⇏', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.YTDL_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("YouTube-DL info loaded.", show_alert=True)

    elif cb_data == "share":
        btn = [[
            InlineKeyboardButton("⟸ Bᴀᴄᴋ", callback_data="help"),
            InlineKeyboardButton("Cᴏɴᴛᴀᴄᴛ", url=OWNER_LNK)
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(btn)
        await query.message.edit_text(
            text=(script.SHARE_TXT),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Share text info loaded.", show_alert=True)

    elif cb_data == "song":
        btn = [[
            InlineKeyboardButton("⟸ Bᴀᴄᴋ", callback_data="help"),
            InlineKeyboardButton("Cᴏɴᴛᴀᴄᴛ", url=OWNER_LNK)
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(btn)
        await query.message.edit_text(
            text=(script.SONG_TXT),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Song info loaded.", show_alert=True)

    elif cb_data == "json":
        buttons = [[
            InlineKeyboardButton('⇍ ʙᴀᴄᴋ ⇏', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.JSON_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("JSON info loaded.", show_alert=True)

    elif cb_data == "sticker":
        btn = [[
            InlineKeyboardButton("⟸ Bᴀᴄᴋ", callback_data="help"),
            InlineKeyboardButton("Cᴏɴᴛᴀᴄᴛ", url=OWNER_LNK)
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(btn)
        await query.message.edit_text(
            text=(script.STICKER_TXT),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Sticker info loaded.", show_alert=True)

    elif cb_data == "tamil_info":
        btn = [[
            InlineKeyboardButton("⟸ Bᴀᴄᴋ", callback_data="start"),
            InlineKeyboardButton("Cᴏɴᴛᴀᴄᴛ", url=OWNER_LNK)
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(btn)
        await query.message.edit_text(
            text=(script.TAMIL_INFO),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Tamil info loaded.", show_alert=True)

    elif cb_data == "english_info":
        btn = [[
            InlineKeyboardButton("⟸ Bᴀᴄᴋ", callback_data="start"),
            InlineKeyboardButton("Cᴏɴᴛᴀᴄᴛ", url=OWNER_LNK)
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(btn)
        await query.message.edit_text(
            text=(script.ENGLISH_INFO),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("English info loaded.", show_alert=True)

    elif cb_data == "hindi_info":
        btn = [[
            InlineKeyboardButton("⟸ Bᴀᴄᴋ", callback_data="start"),
            InlineKeyboardButton("Cᴏɴᴛᴀᴄᴛ", url=OWNER_LNK)
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(btn)
        await query.message.edit_text(
            text=(script.HINDI_INFO),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Hindi info loaded.", show_alert=True)

    elif cb_data == "telugu_info":
        btn = [[
            InlineKeyboardButton("⟸ Bᴀᴄᴋ", callback_data="start"),
            InlineKeyboardButton("Cᴏɴᴛᴀᴄᴛ", url=OWNER_LNK)
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(btn)
        await query.message.edit_text(
            text=(script.TELUGU_INFO),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Telugu info loaded.", show_alert=True)

    elif cb_data == "malayalam_info":
        btn = [[
            InlineKeyboardButton("⟸ Bᴀᴄᴋ", callback_data="start"),
            InlineKeyboardButton("Cᴏɴᴛᴀᴄᴛ", url=OWNER_LNK)
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(btn)
        await query.message.edit_text(
            text=(script.MALAYALAM_INFO),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Malayalam info loaded.", show_alert=True)

    elif cb_data == "urdu_info":
        btn = [[
            InlineKeyboardButton("⟸ Bᴀᴄᴋ", callback_data="start"),
            InlineKeyboardButton("Cᴏɴᴛᴀᴄᴛ", url=OWNER_LNK)
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(btn)
        await query.message.edit_text(
            text=(script.URTU_INFO),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Urdu info loaded.", show_alert=True)

    elif cb_data == "bangladesh_info":
        btn = [[
            InlineKeyboardButton("⟸ Bᴀᴄᴋ", callback_data="start"),
            InlineKeyboardButton("Cᴏɴᴛᴀᴄᴛ", url=OWNER_LNK)
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(btn)
        await query.message.edit_text(
            text=(script.BANGLADESH_INFO),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Bangladesh info loaded.", show_alert=True)

    elif cb_data == "kannada_info":
        btn = [[
            InlineKeyboardButton("⟸ Bᴀᴄᴋ", callback_data="start"),
            InlineKeyboardButton("Cᴏɴᴛᴀᴄᴛ", url=OWNER_LNK)
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(btn)
        await query.message.edit_text(
            text=(script.KANNADA_INFO),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Kannada info loaded.", show_alert=True)

    elif cb_data == "gujarati_info":
        btn = [[
            InlineKeyboardButton("⟸ Bᴀᴄᴋ", callback_data="start"),
            InlineKeyboardButton("Cᴏɴᴛᴀᴄᴛ", url=OWNER_LNK)
        ]]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(btn)
        await query.message.edit_text(
            text=(script.GUJARATI_INFO),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("Gujarati info loaded.", show_alert=True)

    elif cb_data.startswith("setgs"):
        ident, set_type, status, grp_id = cb_data.split("#")
        grpid = await active_connection(str(query.from_user.id))

        if str(grp_id) != str(grpid):
            await query.message.edit("Yᴏᴜʀ Aᴄᴛɪᴠᴇ Cᴏɴɴᴇᴄᴛɪᴏn Hᴀs Bᴇᴇɴ Cʜᴀɴɢᴇᴅ. Gᴏ Tᴏ /connections ᴀɴᴅ ᴄʜᴀɴɢᴇ ʏᴏᴜʀ ᴀᴄᴛɪᴠᴇ ᴄᴏɴɴᴇᴄᴛɪᴏn.")
            return await query.answer("Active connection changed.", show_alert=True)

        if status == "True":
            await save_group_settings(grpid, set_type, False)
        else:
            settings = await get_settings(grpid)
            if set_type == "is_shortlink" and not settings.get('shortlink'):
                return await query.answer(text = "First Add Your Shortlink Url And Api By /shortlink Command, Then Turn Me On.", show_alert = True)
            await save_group_settings(grpid, set_type, True)

        settings = await get_settings(grpid)

        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('Rᴇsᴜʟᴛ Pᴀɢᴇ',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('Bᴜᴛᴛᴏɴ' if settings["button"] else 'Tᴇxᴛ',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Pʀᴏᴛᴇᴄᴛ Cᴏɴᴛᴇɴᴛ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ Oɴ' if settings["file_secure"] else '✘ Oғғ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Iᴍᴅʙ', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ Oɴ' if settings["imdb"] else '✘ Oғғ',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Sᴘᴇʟʟ Cʜᴇᴄᴋ',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ Oɴ' if settings["spell_check"] else '✘ Oғғ',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Wᴇʟᴄᴏᴍᴇ Msɢ', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ Oɴ' if settings["welcome"] else '✘ Oғғ',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Aᴜᴛᴏ-Dᴇʟᴇᴛᴇ',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}'),
                    InlineKeyboardButton('5 Mɪɴs' if settings["auto_delete"] else '✘ Oғғ',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Aᴜᴛᴏ-Fɪʟᴛᴇʀ',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ Oɴ' if settings["auto_ffilter"] else '✘ Oғғ',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Mᴀx Bᴜᴛᴛoɴs',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}'),
                    InlineKeyboardButton('10' if settings["max_btn"] else f'{MAX_BTN}',
                                         callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('SʜᴏʀᴛLɪɴᴋ',
                                         callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✔ Oɴ' if settings["is_shortlink"] else '✘ Oғғ',
                                         callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{str(grp_id)}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)
        await query.answer("Settings updated.", show_alert=True)

