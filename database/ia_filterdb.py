# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re
import os
import asyncio
import time
import logging
from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram.enums import MessageEntityType, ChatMemberStatus
from pyrogram.errors import FloodWait, UserNotParticipant, PeerIdInvalid, ChannelInvalid

from database.users_chats_db import db
from database.ia_filterdb import get_search_results, save_file, get_file_details, col, sec_col
from utils import get_size, is_subscribed, get_poster, get_genres, get_cap, temp # Removed get_name
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
    VERIFY_SHORTLINK_API, VERIFY_SHORTLINK_URL, MSG_ALRT, LANGUAGES, YEARS
)
from Script import script

logger = logging.getLogger(__name__)

FLOOD_CAPS = {} # To store flood wait times for users

@Client.on_message(filters.command(["start", "help"]) & filters.private)
async def start_and_help(client: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.full_name)
        if MELCOW_NEW_USERS:
            try:
                await client.send_message(
                    LOG_CHANNEL,
                    f"#NEW_USER: {message.from_user.first_name} {message.from_user.last_name or ''}\nID: {message.from_user.id}\nUsername: @{message.from_user.username or 'None'}\nDate: {message.date}"
                )
            except Exception as e:
                logger.error(f"Error sending new user log to LOG_CHANNEL: {e}")
    
    # Check force subscribe
    if FORCE_SUB_MODE:
        try:
            user_status = await client.get_chat_member(AUTH_CHANNEL, message.from_user.id)
            if user_status.status in [ChatMemberStatus.BANNED, ChatMemberStatus.LEFT]:
                raise UserNotParticipant
        except UserNotParticipant:
            btn = [[InlineKeyboardButton(text="😇 Join Updates Channel 😇", url=f"https://t.me/{AUTH_CHANNEL}")]]
            if SUPPORT_CHAT:
                btn.append([InlineKeyboardButton(text="⭕ Support Group ⭕", url=f"https://t.me/{SUPPORT_CHAT}")])
            return await message.reply_text(
                text=script.JOIN_GROUP_ALERT.format(message.from_user.first_name),
                reply_markup=InlineKeyboardMarkup(btn),
                disable_web_page_preview=True
            )
        except (PeerIdInvalid, ChannelInvalid) as e:
            logger.error(f"Force subscribe channel invalid: {e}")
            # Continue without force sub if channel is invalid
        except Exception as e:
            logger.error(f"Error checking force subscribe: {e}")
            # Continue without force sub if other error

    btn = [[
        InlineKeyboardButton("🔎 Search Inline 🔍", switch_inline_query_current_chat=""),
        InlineKeyboardButton("⚙️ Settings ⚙️", callback_data="settings")
    ]]
    if ADMINS and message.from_user.id in ADMINS:
        btn.append([InlineKeyboardButton("👨‍💻 Admin Panel 👨‍�", callback_data="admin_panel")])
    
    try:
        await message.reply_photo(
            photo=PICS,
            caption=script.START_TXT.format(message.from_user.first_name, BOT_NAME),
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except Exception as e:
        logger.error(f"Error sending start photo/message: {e}")
        await message.reply_text(
            caption=script.START_TXT.format(message.from_user.first_name, BOT_NAME),
            reply_markup=InlineKeyboardMarkup(btn)
        )


@Client.on_message(filters.command("stats") & filters.private & filters.user(ADMINS))
async def show_stats(client: Client, message: Message):
    users = await db.total_users_count()
    chats = await db.total_chat_count()
    total_files = await col.estimated_document_count() + (await sec_col.estimated_document_count() if MULTIPLE_DATABASE else 0)
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
    m = await message.reply_text("Starting broadcast...")
    for user in users:
        try:
            await message.reply_to_message.copy(user["id"])
            b_count += 1
            await asyncio.sleep(0.5) # Small delay to prevent flood waits
        except FloodWait as e:
            await asyncio.sleep(e.value + 1) # Wait a bit longer than requested
            await message.reply_to_message.copy(user["id"])
            b_count += 1
        except Exception as e:
            logger.error(f"Error broadcasting to {user['id']}: {e}")
            e_count += 1
    await m.edit_text(f"Broadcast complete.\nSuccessful: {b_count}\nFailed: {e_count}")

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
                success, _ = await save_file(msg)
                if success:
                    total_saved += 1
        except Exception as e:
            logger.error(f"Error saving message {i} in batch: {e}")
            continue
    
    await m.edit_text(f"Batch save complete. Saved {total_saved} files.")

# Handler for incoming media messages (documents, videos, photos)
@Client.on_message(filters.private & filters.media & filters.user(ADMINS))
async def media_handler(client: Client, message: Message):
    if not message.media:
        return # Not a media message

    # Check if the message is forwarded from an authorized channel
    if message.forward_from_chat and message.forward_from_chat.id in CHANNELS:
        m = await message.reply_text("Saving file to database...")
        success, file_id = await save_file(message)
        if success:
            await m.edit_text(f"File saved successfully! File ID: `{file_id}`")
        else:
            await m.edit_text("Failed to save file or file already exists.")
    else:
        await message.reply_text("This media is not from an authorized channel. Only media forwarded from authorized channels can be saved.")


@Client.on_message(filters.text & filters.private & filters.incoming)
async def auto_filter(client: Client, message: Message):
    if re.findall(r"((^|\s)/batchfile)", message.text):
        return
    
    # Check force subscribe
    if FORCE_SUB_MODE:
        try:
            user_status = await client.get_chat_member(AUTH_CHANNEL, message.from_user.id)
            if user_status.status in [ChatMemberStatus.BANNED, ChatMemberStatus.LEFT]:
                raise UserNotParticipant
        except UserNotParticipant:
            btn = [[InlineKeyboardButton(text="😇 Join Updates Channel 😇", url=f"https://t.me/{AUTH_CHANNEL}")]]
            if SUPPORT_CHAT:
                btn.append([InlineKeyboardButton(text="⭕ Support Group ⭕", url=f"https://t.me/{SUPPORT_CHAT}")])
            return await message.reply_text(
                text=script.JOIN_GROUP_ALERT.format(message.from_user.first_name),
                reply_markup=InlineKeyboardMarkup(btn),
                disable_web_page_preview=True
            )
        except (PeerIdInvalid, ChannelInvalid) as e:
            logger.error(f"Force subscribe channel invalid: {e}")
            # Continue without force sub if channel is invalid
        except Exception as e:
            logger.error(f"Error checking force subscribe: {e}")
            # Continue without force sub if other error

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

    results = await get_search_results(query)

    if not results:
        if SPELL_CHECK_REPLY:
            return await message.reply_text(script.NO_RESULT_TXT.format(query))
        return

    keyboards = []
    if BUTTON_MODE:
        buttons_per_row = MAX_BTN if MAX_BTN > 0 else 5
        buttons = []
        for file_details in results:
            # Use file_details['_id'] which is the unique MongoDB ObjectId
            title = file_details.get("file_name", "Untitled File") # Fallback if file_name is missing
            file_db_id = str(file_details["_id"]) # Convert ObjectId to string for callback_data
            buttons.append(InlineKeyboardButton(title, callback_data=f"files#{file_db_id}"))
            if len(buttons) == buttons_per_row:
                keyboards.append(buttons)
                buttons = []
        if buttons: # Add any remaining buttons
            keyboards.append(buttons)
    else:
        # If not button mode, we will send individual messages or a formatted list
        pass

    if BUTTON_MODE and keyboards:
        if PM_SEARCH_MODE == "TEXT":
            # Send results as a list of buttons in a single message
            await message.reply_text(
                "I found some results. Choose from below:",
                reply_markup=InlineKeyboardMarkup(keyboards),
                disable_web_page_preview=True
            )
        else: # Default to sending as a list in Markdown
            search_results_text = "Here are some results:\n\n"
            for idx, file_details in enumerate(results):
                search_results_text += f"{idx + 1}. **{file_details.get('file_name', 'Untitled File')}**\n"
            search_results_text += "\nChoose a button below to get the file."
            await message.reply_text(
                search_results_text,
                reply_markup=InlineKeyboardMarkup(keyboards),
                disable_web_page_preview=True
            )
    else: # If not button mode, send files directly or list them
        for file_details in results:
            file_db_id = str(file_details["_id"])
            try:
                # Provide a button to get the file if not sending directly
                caption = await get_cap(file_details) # Use get_cap to format caption
                await message.reply_text(
                    caption,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Get File", callback_data=f"getfile#{file_db_id}")]])
                )
                await asyncio.sleep(1) # Delay to prevent flood
            except Exception as e:
                logger.error(f"Error sending search result for {file_details.get('file_name', 'Unknown')}: {e}")
                continue


@Client.on_callback_query(filters.regex("^files#|^getfile#"))
async def send_file_from_button(client: Client, callback_query: CallbackQuery):
    query_data = callback_query.data.split("#")
    action = query_data[0]
    file_db_id = query_data[1] # This is the MongoDB _id as a string

    file_details = await get_file_details(file_db_id) # Fetch by MongoDB _id
    if not file_details:
        return await callback_query.answer("File not found in database!", show_alert=True)
    
    # Extract original file_id (Telegram's file_id) and file_ref if available
    telegram_file_id = file_details.get('file_id')
    telegram_file_ref = file_details.get('file_ref') # This is crucial for send_cached_media
    file_type = file_details.get('file_type') # e.g., 'document', 'video', 'photo'

    if not telegram_file_id:
        return await callback_query.answer("Telegram file ID not found for this entry!", show_alert=True)

    try:
        caption = await get_cap(file_details) # Generate caption using utils.get_cap

        # Use send_cached_media for sending files by file_id and file_ref
        if file_type == 'document':
            await client.send_document(
                chat_id=callback_query.message.chat.id,
                document=telegram_file_id,
                file_ref=bytes.fromhex(telegram_file_ref) if telegram_file_ref else None,
                caption=caption,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Close", callback_data="close_msg")]])
            )
        elif file_type == 'video':
            await client.send_video(
                chat_id=callback_query.message.chat.id,
                video=telegram_file_id,
                file_ref=bytes.fromhex(telegram_file_ref) if telegram_file_ref else None,
                caption=caption,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Close", callback_data="close_msg")]])
            )
        elif file_type == 'photo':
            await client.send_photo(
                chat_id=callback_query.message.chat.id,
                photo=telegram_file_id,
                file_ref=bytes.fromhex(telegram_file_ref) if telegram_file_ref else None,
                caption=caption,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Close", callback_data="close_msg")]])
            )
        else:
            # Fallback for unknown types or if file_type is not stored
            await client.send_cached_media(
                chat_id=callback_query.message.chat.id,
                file_id=telegram_file_id,
                file_ref=bytes.fromhex(telegram_file_ref) if telegram_file_ref else None,
                caption=caption,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Close", callback_data="close_msg")]])
            )

        await callback_query.answer("File sent successfully!")
    except FloodWait as e:
        await callback_query.answer(f"Too many requests, please try again after {e.value} seconds.", show_alert=True)
        await asyncio.sleep(e.value + 1)
    except Exception as e:
        logger.error(f"Error sending file from callback: {e}")
        await callback_query.answer("Failed to send file. An error occurred.", show_alert=True)

@Client.on_callback_query(filters.regex("^settings"))
async def settings_callback(client: Client, query: CallbackQuery):
    # This is a placeholder. You'll need to implement your settings logic here.
    # For example, fetch user/chat settings from DB and display options.
    await query.answer("Settings menu will be implemented here!", show_alert=True)
    # Example:
    # user_settings = await db.get_user_settings(query.from_user.id)
    # await query.message.edit_text("Your settings:", reply_markup=InlineKeyboardMarkup(...))

@Client.on_callback_query(filters.regex("^admin_panel"))
async def admin_panel_callback(client: Client, query: CallbackQuery):
    if query.from_user.id not in ADMINS:
        return await query.answer("You are not authorized to access this panel.", show_alert=True)
    await query.answer("Admin panel will be implemented here!", show_alert=True)
    # Example:
    # await query.message.edit_text("Admin options:", reply_markup=InlineKeyboardMarkup(...))

@Client.on_callback_query(filters.regex("^close_msg"))
async def close_message_callback(client: Client, query: CallbackQuery):
    try:
        await query.message.delete()
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
    await query.answer("Message closed.")

