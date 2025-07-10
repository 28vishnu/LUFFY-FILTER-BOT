import os, string, logging, random, asyncio, time, datetime, re, sys, json, base64
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import *
from database.ia_filterdb import get_file_details, unpack_new_file_id, get_bad_files
from database.users_chats_db import db, delete_all_referal_users, get_referal_users_count, get_referal_all_users, referal_add_user
from database.join_reqs import JoinReqs
from info import *
# Corrected imports: get_settings, is_subscribed, verify_user, check_token, check_verification, get_token are now handled via 'db' or defined here.
from utils import get_size, temp, get_shortlink, get_tutorial_shortlink, get_seconds # get_tutorial is now get_tutorial_shortlink
from database.connections_mdb import active_connection # Keep if active_connection is used elsewhere

from urllib.parse import quote_plus
from TechVJ.util.file_properties import get_name, get_hash, get_media_file_size
logger = logging.getLogger(__name__)

BATCH_FILES = {}
join_db = JoinReqs

# --- Helper functions for verification (adapted to use db object) ---
async def check_verification(client, user_id):
    """
    Checks if a user is verified for the current day.
    Verification status is stored in user settings.
    """
    user_settings = await db.get_settings(user_id)
    is_verified = user_settings.get("is_verified", False)
    last_verified_time = user_settings.get("last_verified_time")

    if is_verified and last_verified_time:
        # Check if verification is still valid for today (e.g., within the same UTC day)
        # You might want to adjust this logic based on your definition of "today"
        if datetime.datetime.utcnow().date() == last_verified_time.date():
            return True
        else:
            # Reset verification if it's a new day
            user_settings["is_verified"] = False
            user_settings["token"] = None
            user_settings["last_verified_time"] = None
            await db.update_settings(user_id, user_settings)
            return False
    return False

async def verify_user(client, user_id, token):
    """
    Sets a user as verified and updates their settings.
    """
    user_settings = await db.get_settings(user_id)
    user_settings["is_verified"] = True
    user_settings["token"] = token # Store the token if needed for re-validation
    user_settings["last_verified_time"] = datetime.datetime.utcnow()
    await db.update_settings(user_id, user_settings)
    return True

async def get_token(client, user_id, start_link_base):
    """
    Generates a unique token for verification and a verification URL.
    """
    # Generate a simple random token
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    
    # Store the token in user settings
    user_settings = await db.get_settings(user_id)
    user_settings["token"] = token
    # Set is_verified to False initially, it will be set to True upon successful verification
    user_settings["is_verified"] = False
    user_settings["last_verified_time"] = None
    await db.update_settings(user_id, user_settings)

    # Construct the verification URL
    # The start_link_base should typically be something like "https://t.me/YourBotUsername?start="
    verification_url = f"{start_link_base}verify-{user_id}-{token}"
    
    # Shorten the verification URL if VERIFY is True
    if VERIFY:
        verification_url = await get_verify_shortlink(verification_url)
        
    return verification_url

async def is_subscribed(client, user_id, channel_id):
    """
    Checks if a user is subscribed to a given channel.
    This is a placeholder; actual implementation depends on Pyrogram's methods.
    """
    if not channel_id:
        return True # If no channel is set for force subscribe, always return True

    try:
        member = await client.get_chat_member(channel_id, user_id)
        # Check if the user is a member, creator, or administrator
        if member.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"Error checking subscription for user {user_id} in channel {channel_id}: {e}")
        return False # Assume not subscribed on error
# --- End of Helper functions ---


@Client.on_chat_join_request((filters.group | filters.channel))
async def auto_approve(client, message: ChatJoinRequest):
    if AUTO_APPROVE_MODE == True:
        if not await db.is_user_exist(message.from_user.id):
            await db.add_user(message.from_user.id, message.from_user.first_name)
        if message.chat.id == AUTH_CHANNEL:
            return 
        chat = message.chat 
        user = message.from_user  
        await client.approve_chat_join_request(chat_id=chat.id, user_id=user.id)
        text = f"<b>ʜᴇʟʟᴏ {message.from_user.mention} 👋,\n\nʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ {message.chat.title} ɪs ᴀᴘᴘʀᴏᴠᴇᴅ.\n\nᴘᴏᴡᴇʀᴇᴅ ʙʏ - {CHNL_LNK}</b>"
        await client.send_message(chat_id=user.id, text=text)
         
    if REQUEST_TO_JOIN_MODE == False:
        return 
    if message.chat.id != AUTH_CHANNEL:
        return 
    if not join_db().isActive():
        return
    ap_user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username
    date = message.date
    await join_db().add_user(user_id=ap_user_id, first_name=first_name, username=username, date=date)
    if TRY_AGAIN_BTN == True:
        return 
    data = await db.get_msg_command(ap_user_id)
        
    if data and data.split("-", 1)[0] == "VJ": # Added check for data existence
        user_id = int(data.split("-", 1)[1])
        vj = await referal_add_user(user_id, message.from_user.id)
        if vj and PREMIUM_AND_REFERAL_MODE == True:
            await message.reply(f"<b>You have joined using the referral link of user with ID {user_id}\n\nSend /start again to use the bot</b>")
            num_referrals = await get_referal_users_count(user_id)
            await client.send_message(chat_id = user_id, text = "<b>{} start the bot with your referral link\n\nTotal Referals - {}</b>".format(message.from_user.mention, num_referrals))
            if num_referrals == REFERAL_COUNT:
                time_str = REFERAL_PREMEIUM_TIME       
                seconds = await get_seconds(time_str)
                if seconds > 0:
                    expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
                    await db.add_premium_user(user_id, expiry_time) # Use add_premium_user
                    await delete_all_referal_users(user_id)
                    await client.send_message(chat_id = user_id, text = "<b>You Have Successfully Completed Total Referal.\n\nYou Added In Premium For {}</b>".format(REFERAL_PREMEIUM_TIME))
                    return 
        else:
            if PREMIUM_AND_REFERAL_MODE == True:
                buttons = [[
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
                ]]
            else:
                buttons = [[
                    InlineKeyboardButton('⤬ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ⤬', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
                ],[
                    InlineKeyboardButton('ᴇᴀʀɴ ᴍᴏɴᴇʏ', callback_data="shortlink_info"),
                    InlineKeyboardButton('ᴍᴏᴠɪᴇ ɢʀᴏᴜᴘ', url=GRP_LNK)
                ],[
                    InlineKeyboardButton('ʜᴇʟᴘ', callback_data='help'),
                    InlineKeyboardButton('ᴀʙᴏᴜᴛ', callback_data='about')
                ],[
                    InlineKeyboardButton('ᴊᴏɪɴ ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url=CHNL_LNK)
                ]]
            if CLONE_MODE == True:
                buttons.append([InlineKeyboardButton('ᴄʀᴇᴀᴛᴇ ᴏᴡɴ ᴄʟᴏɴᴇ ʙᴏᴛ', callback_data='clone')])
            reply_markup = InlineKeyboardMarkup(buttons)
            m=await message.reply_sticker("CAACAgUAAxkBAAEKVaxlCWGs1Ri6ti45xliLiUeweCnu4AACBAADwSQxMYnlHW4Ls8gQMAQ") 
            await asyncio.sleep(1)
            await m.delete()
            await message.reply_photo(
                photo=random.choice(PICS),
                caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )
            return 
            
    try:
        pre, file_id = data.split('_', 1)
    except:
        file_id = data
        pre = ""
        
    if data and data.split("-", 1)[0] == "BATCH": # Added check for data existence
        sts = await message.reply("<b>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
        file_id = data.split("-", 1)[1]
        msgs = BATCH_FILES.get(file_id)
        if not msgs:
            file_path = await client.download_media(file_id) # Renamed 'file' to 'file_path' to avoid conflict
            try: 
                with open(file_path) as file_data:
                    msgs=json.loads(file_data.read())
            except Exception as e: # Catch specific exception
                logger.error(f"Error reading batch file: {e}")
                await sts.edit("FAILED")
                return await client.send_message(LOG_CHANNEL, "UNABLE TO OPEN FILE.")
            os.remove(file_path)
            BATCH_FILES[file_id] = msgs

        filesarr = []
        for msg_data in msgs: # Renamed 'msg' to 'msg_data' to avoid conflict
            title = msg_data.get("title")
            size=get_size(int(msg_data.get("size", 0)))
            f_caption=msg_data.get("caption", "")
            if BATCH_FILE_CAPTION:
                try:
                    f_caption=BATCH_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                except:
                    f_caption=f_caption
            if f_caption is None:
                f_caption = f"{title}"
            try:
                if STREAM_MODE == True:
                    log_msg = await client.send_cached_media(chat_id=LOG_CHANNEL, file_id=msg_data.get("file_id"))
                    # Ensure get_name and get_hash handle None or empty values gracefully
                    file_name_quoted = quote_plus(get_name(log_msg.file_name) if log_msg.file_name else "")
                    file_hash = get_hash(log_msg.file_id) # Assuming file_id can be used for hash
                    stream = f"{URL}watch/{str(log_msg.id)}/{file_name_quoted}?hash={file_hash}"
                    download = f"{URL}{str(log_msg.id)}/{file_name_quoted}?hash={file_hash}"

                if STREAM_MODE == True:
                    button = [[
                        InlineKeyboardButton("• ᴅᴏᴡɴʟᴏᴀᴅ •", url=download),
                        InlineKeyboardButton('• ᴡᴀᴛᴄʜ •', url=stream)
                    ],[
                        InlineKeyboardButton("• ᴡᴀᴛᴄʜ ɪɴ ᴡᴇʙ ᴀᴘᴘ •", web_app=WebAppInfo(url=stream))
                    ]]
                    reply_markup = InlineKeyboardMarkup(button)
                else:
                    reply_markup = None
                    
                msg = await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg_data.get("file_id"),
                    caption=f_caption,
                    protect_content=msg_data.get('protect', False),
                    reply_markup=reply_markup
                )
                filesarr.append(msg)
                
            except FloodWait as e:
                await asyncio.sleep(e.value)
                msg = await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg_data.get("file_id"),
                    caption=f_caption,
                    protect_content=msg_data.get('protect', False),
                    reply_markup=InlineKeyboardMarkup(button)
                )
                filesarr.append(msg)
            except Exception as e: # Catch all other exceptions
                logger.error(f"Error sending cached media in batch: {e}")
                continue
            await asyncio.sleep(1) 
        await sts.delete()
        k = await client.send_message(chat_id = message.from_user.id, text=f"<blockquote><b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ <b><u>10 mins</u> 🫥 <i></b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs)</i>.\n\n<b><i>ᴘʟᴇᴀsᴇ ғᴏʀᴡᴀʀᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ᴏʀ ᴀɴy ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ.</i></b></blockquote>")
        await asyncio.sleep(600)
        for x in filesarr:
            try:
                await x.delete()
            except Exception as e:
                logger.warning(f"Failed to delete message in batch cleanup: {e}")
        await k.edit_text("<b>✅ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ɪs sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ</b>")  
        return
        
    elif data and data.split("-", 1)[0] == "DSTORE": # Added check for data existence
        sts = await message.reply("<b>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
        b_string = data.split("-", 1)[1]
        decoded = (base64.urlsafe_b64decode(b_string + "=" * (-len(b_string) % 4))).decode("ascii")
        try:
            f_msg_id, l_msg_id, f_chat_id, protect = decoded.split("_", 3)
        except ValueError: # Handle cases where protect might be missing
            f_msg_id, l_msg_id, f_chat_id = decoded.split("_", 2)
            protect = "/pbatch" if PROTECT_CONTENT else "batch" # Default protect value
        
        filesarr = []
        # Using async for with iter_messages is correct
        async for msg in client.iter_messages(int(f_chat_id), int(l_msg_id), int(f_msg_id)):
            if msg.media:
                media = getattr(msg, msg.media.value)
                file_type = msg.media
                file = getattr(msg, file_type.value)
                size = get_size(int(file.file_size))
                file_name = getattr(media, 'file_name', '')
                f_caption = getattr(msg, 'caption', file_name)
                if BATCH_FILE_CAPTION:
                    try:
                        f_caption=BATCH_FILE_CAPTION.format(file_name=file_name, file_size='' if size is None else size, file_caption=f_caption)
                    except:
                        f_caption = getattr(msg, 'caption', '')
                file_id = file.file_id
                if STREAM_MODE == True:
                    log_msg = await client.send_cached_media(chat_id=LOG_CHANNEL, file_id=file_id)
                    file_name_quoted = quote_plus(get_name(log_msg.file_name) if log_msg.file_name else "")
                    file_hash = get_hash(log_msg.file_id) # Assuming file_id can be used for hash
                    stream = f"{URL}watch/{str(log_msg.id)}/{file_name_quoted}?hash={file_hash}"
                    download = f"{URL}{str(log_msg.id)}/{file_name_quoted}?hash={file_hash}"
 
                if STREAM_MODE == True:
                    button = [[
                        InlineKeyboardButton("• ᴅᴏᴡɴʟᴏᴀᴅ •", url=download),
                        InlineKeyboardButton('• ᴡᴀᴛᴄʜ •', url=stream)
                    ],[
                        InlineKeyboardButton("• ᴡᴀᴛᴄʜ ɪɴ ᴡᴇʙ ᴀᴘᴘ •", web_app=WebAppInfo(url=stream))
                    ]]
                    reply_markup = InlineKeyboardMarkup(button)
                else:
                    reply_markup = None
                try:
                    p = await msg.copy(message.chat.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False, reply_markup=reply_markup)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    p = await msg.copy(message.chat.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False, reply_markup=reply_markup)
                except Exception as e:
                    logger.error(f"Error copying media in DSTORE: {e}")
                    continue
            elif msg.empty:
                continue
            else:
                try:
                    p = await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    p = await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                except Exception as e:
                    logger.error(f"Error copying message in DSTORE: {e}")
                    continue
            filesarr.append(p)
            await asyncio.sleep(1)
        await sts.delete()
        k = await client.send_message(chat_id = message.from_user.id, text=f"<blockquote><b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ <b><u>10 mins</u> 🫥 <i></b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs)</i>.\n\n<b><i>ᴘʟᴇᴀsᴇ ғᴏʀᴡᴀʀᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ᴏʀ ᴀɴy ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ.</i></b></blockquote>")
        await asyncio.sleep(600)
        for x in filesarr:
            try:
                await x.delete()
            except Exception as e:
                logger.warning(f"Failed to delete message in DSTORE cleanup: {e}")
        await k.edit_text("<b>✅ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ɪs sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ</b>")
        return

    elif data and data.split("-", 1)[0] == "verify": # Added check for data existence
        userid = int(data.split("-", 2)[1]) # Ensure userid is int
        token = data.split("-", 3)[2]
        if message.from_user.id != userid: # Direct comparison of int
            return await message.reply_text(text="<b>ɪɴᴠᴀʟɪᴅ ʟɪɴᴋ ᴏʀ ᴇxᴘɪʀᴇᴅ ʟɪɴᴋ</b>", protect_content=True)
        is_valid = await check_token(client, userid, token) # check_token is a helper function
        if is_valid == True:
            text = "<b>ʜᴇʏ {} 👋,\n\nʏᴏᴜ ʜᴀᴠᴇ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ᴛʜᴇ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ...\n\nɴᴏᴡ ʏᴏᴜ ʜᴀᴠᴇ ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇss ᴛɪʟʟ ᴛᴏᴅᴀʏ ɴᴏᴡ ᴇɴᴊᴏʏ\n\n</b>"
            if PREMIUM_AND_REFERAL_MODE == True:
                text += "<b>ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴅɪʀᴇᴄᴛ ғɪʟᴇꜱ ᴡɪᴛʜᴏᴜᴛ ᴀɴʏ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴꜱ ᴛʜᴇɴ ʙᴜʏ ʙᴏᴛ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ☺️\n\n💶 ꜱᴇɴᴅ /plan ᴛᴏ ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ</b>"           
            await message.reply_text(text=text.format(message.from_user.mention), protect_content=True)
            await verify_user(client, userid, token) # verify_user is a helper function
        else:
            return await message.reply_text(text="<b>ɪɴᴠᴀʟɪᴅ ʟɪɴᴋ ᴏʀ ᴇxᴘɪʀᴇᴅ ʟɪɴᴋ</b>", protect_content=True)
            
    if data and data.startswith("sendfiles"): # Added check for data existence
        chat_id = int("-" + file_id.split("-")[1])
        # userid = message.from_user.id if message.from_user else None # Already defined from message.from_user.id
        settings = await db.get_settings(chat_id) # Use db.get_settings
        pre = 'allfilesp' if settings['file_secure'] else 'allfiles'
        g = await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start={pre}_{file_id}") # get_shortlink from utils
        btn = [[
            InlineKeyboardButton('ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ', url=g)
        ]]
        if settings.get('tutorial') and IS_TUTORIAL: # Check if tutorial setting is True and IS_TUTORIAL is True
            btn.append([InlineKeyboardButton('ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ', url=await get_tutorial_shortlink(TUTORIAL))]) # Use get_tutorial_shortlink and TUTORIAL from info
        text = "<b>✅ ʏᴏᴜʀ ғɪʟᴇ ʀᴇᴀᴅʏ ᴄʟɪᴄᴋ ᴏɴ ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ ʙᴜᴛᴛᴏɴ ᴛʜᴇɴ ᴏᴘᴇɴ ʟɪɴᴋ ᴛᴏ ɢᴇᴛ ғɪʟᴇ\n\n</b>"
        if PREMIUM_AND_REFERAL_MODE == True:
            text += "<b>ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴅɪʀᴇᴄᴛ ғɪʟᴇꜱ ᴡɪᴛʜᴏᴜᴛ ᴀɴʏ ᴏᴘᴇɴɪɴɢ ʟɪɴᴋ ᴀɴᴅ ᴡᴀᴛᴄʜɪɴɢ ᴀᴅs ᴛʜᴇɴ ʙᴜʏ ʙᴏᴛ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ☺️\n\n💶 ꜱᴇɴᴅ /plan ᴛᴏ ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ</b>"
        k = await client.send_message(chat_id=message.from_user.id, text=text, reply_markup=InlineKeyboardMarkup(btn))
        await asyncio.sleep(300)
        await k.edit("<b>✅ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ɪs sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ</b>")
        return

    elif data and data.startswith("short"): # Added check for data existence
        user = message.from_user.id
        chat_id = temp.SHORT.get(user)
        if chat_id is None: # Handle case where chat_id might not be set in temp.SHORT
            await message.reply_text(text="<b>Please Search Again in Group</b>")
            return
        settings = await db.get_settings(chat_id) # Use db.get_settings
        pre = 'filep' if settings['file_secure'] else 'file'
        g = await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start={pre}_{file_id}") # get_shortlink from utils
        btn = [[
            InlineKeyboardButton('ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ', url=g)
        ]]
        if settings.get('tutorial') and IS_TUTORIAL: # Check if tutorial setting is True and IS_TUTORIAL is True
            btn.append([InlineKeyboardButton('ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ', url=await get_tutorial_shortlink(TUTORIAL))]) # Use get_tutorial_shortlink and TUTORIAL from info
        text = "<b>✅ ʏᴏᴜʀ ғɪʟᴇ ʀᴇᴀᴅʏ ᴄʟɪᴄᴋ ᴏɴ ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ ʙᴜᴛᴛᴏɴ ᴛʜᴇɴ ᴏᴘᴇɴ ʟɪɴᴋ ᴛᴏ ɢᴇᴛ ғɪʟᴇ\n\n</b>"
        if PREMIUM_AND_REFERAL_MODE == True:
            text += "<b>ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴅɪʀᴇᴄᴛ ғɪʟᴇꜱ ᴡɪᴛʜᴏᴜᴛ ᴀɴʏ ᴏᴘᴇɴɪɴɢ ʟɪɴᴋ ᴀɴᴅ ᴡᴀᴛᴄʜɪɴɢ ᴀᴅs ᴛʜᴇɴ ʙᴜʏ ʙᴏᴛ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ☺️\n\n💶 ꜱᴇɴᴅ /plan ᴛᴏ ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ</b>"
        k = await client.send_message(chat_id=user, text=text, reply_markup=InlineKeyboardMarkup(btn))
        await asyncio.sleep(1200)
        await k.edit("<b>✅ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ɪs sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ</b>")
        return
        
    elif data and data.startswith("all"): # Added check for data existence
        files = temp.GETALL.get(file_id)
        if not files:
            return await message.reply('<b><i>No such file exist.</b></i>')
        filesarr = []
        for file_data in files: # Renamed 'file' to 'file_data'
            file_id_inner = file_data["file_id"] # Renamed 'file_id' to 'file_id_inner' to avoid conflict
            files1 = await get_file_details(file_id_inner)
            if not files1: # Handle case where file details might not be found
                continue
            title = files1["file_name"]
            size=get_size(files1["file_size"])
            f_caption=files1["caption"]
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                except:
                    f_caption=f_caption
            if f_caption is None:
                f_caption = f"{' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), files1['file_name'].split()))}"
            
            # Verification logic
            if not await db.has_premium_access(message.from_user.id):
                if not await check_verification(client, message.from_user.id) and VERIFY == True:
                    btn = [[
                        InlineKeyboardButton("ᴠᴇʀɪғʏ", url=await get_token(client, message.from_user.id, f"https://telegram.me/{temp.U_NAME}?start="))
                    ],[
                        InlineKeyboardButton("ʜᴏᴡ ᴛᴏ ᴠᴇʀɪғʏ", url=VERIFY_TUTORIAL)
                    ]]
                    text = "<b>ʜᴇʏ {} 👋,\n\nʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴠᴇʀɪғɪᴇᴅ ᴛᴏᴅᴀʏ, ᴘʟᴇᴀꜱᴇ ᴄʟɪᴄᴋ ᴏɴ ᴠᴇʀɪғʏ & ɢᴇᴛ ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇꜱꜱ ғᴏʀ ᴛᴏᴅᴀʏ</b>"
                    if PREMIUM_AND_REFERAL_MODE == True:
                        text += "<b>ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴅɪʀᴇᴄᴛ ғɪʟᴇꜱ ᴡɪᴛʜᴏᴜᴛ ᴀɴʏ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴꜱ ᴛʜᴇɴ ʙᴜʏ ʙᴏᴛ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ☺️\n\n💶 ꜱᴇɴᴅ /plan ᴛᴏ ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ</b>"
                    await message.reply_text(
                        text=text.format(message.from_user.mention),
                        protect_content=True,
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                    return
            
            if STREAM_MODE == True:
                button = [[InlineKeyboardButton('sᴛʀᴇᴀᴍ ᴀɴᴅ ᴅᴏᴡɴʟᴏᴀᴅ', callback_data=f'generate_stream_link:{file_id_inner}')]]
                reply_markup=InlineKeyboardMarkup(button)
            else:
                reply_markup = None
            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id_inner,
                caption=f_caption,
                protect_content=True if pre == 'allfilesp' else False,
                reply_markup=reply_markup
            )
            filesarr.append(msg)
        k = await client.send_message(chat_id = message.from_user.id, text=f"<blockquote><b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ <b><u>10 mins</u> 🫥 <i></b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs)</i>.\n\n<b><i>ᴘʟᴇᴀsᴇ ғᴏʀᴡᴀʀᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ᴏʀ ᴀɴy ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ.</i></b></blockquote>")
        await asyncio.sleep(600)
        for x in filesarr:
            try:
                await x.delete()
            except Exception as e:
                logger.warning(f"Failed to delete message in allfiles cleanup: {e}")
        await k.edit_text("<b>✅ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ɪs sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ</b>")
        return    

    elif data and data.startswith("files"): # Added check for data existence
        user = message.from_user.id
        if temp.SHORT.get(user) is None:
            await message.reply_text(text="<b>Please Search Again in Group</b>")
            return
        else:
            chat_id = temp.SHORT.get(user)
        settings = await db.get_settings(chat_id) # Use db.get_settings
        pre = 'filep' if settings['file_secure'] else 'file'
        if settings['is_shortlink'] and not await db.has_premium_access(user):
            g = await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start={pre}_{file_id}") # get_shortlink from utils
            btn = [[
                InlineKeyboardButton('ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ', url=g)
            ]]
            if settings.get('tutorial') and IS_TUTORIAL: # Check if tutorial setting is True and IS_TUTORIAL is True
                btn.append([InlineKeyboardButton('ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ', url=await get_tutorial_shortlink(TUTORIAL))]) # Use get_tutorial_shortlink and TUTORIAL from info
            text = "<b>✅ ʏᴏᴜʀ ғɪʟᴇ ʀᴇᴀᴅʏ ᴄʟɪᴄᴋ ᴏɴ ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ ʙᴜᴛᴛᴏɴ ᴛʜᴇɴ ᴏᴘᴇɴ ʟɪɴᴋ ᴛᴏ ɢᴇᴛ ғɪʟᴇ\n\n</b>"
            if PREMIUM_AND_REFERAL_MODE == True:
                text += "<b>ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴅɪʀᴇᴄᴛ ғɪʟᴇꜱ ᴡɪᴛʜᴏᴜᴛ ᴀɴʏ ᴏᴘᴇɴɪɴɢ ʟɪɴᴋ ᴀɴᴅ ᴡᴀᴛᴄʜɪɴɢ ᴀᴅs ᴛʜᴇɴ ʙᴜʏ ʙᴏᴛ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ☺️\n\n💶 ꜱᴇɴᴅ /plan ᴛᴏ ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ</b>"
            k = await client.send_message(chat_id=message.from_user.id, text=text, reply_markup=InlineKeyboardMarkup(btn))
            await asyncio.sleep(1200)
            await k.edit("<b>✅ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ɪs sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ</b>")
            return

    user = message.from_user.id
    files_ = await get_file_details(file_id)           
    if not files_:
        try:
            pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
        except Exception as e:
            logger.error(f"Error decoding file_id from data: {e}")
            return await message.reply('No such file exist or invalid data.')
        
        try:
            if not await db.has_premium_access(message.from_user.id):
                if not await check_verification(client, message.from_user.id) and VERIFY == True:
                    btn = [[
                        InlineKeyboardButton("ᴠᴇʀɪғʏ", url=await get_token(client, message.from_user.id, f"https://telegram.me/{temp.U_NAME}?start="))
                    ],[
                        InlineKeyboardButton("ʜᴏᴡ ᴛᴏ ᴠᴇʀɪғʏ", url=VERIFY_TUTORIAL)
                    ]]
                    text = "<b>ʜᴇʏ {} 👋,\n\nʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴠᴇʀɪғɪᴇᴅ ᴛᴏᴅᴀʏ, ᴘʟᴇᴀꜱᴇ ᴄʟɪᴄᴋ ᴏɴ ᴠᴇʀɪғʏ & ɢᴇᴛ ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇꜱꜱ ғᴏʀ ᴛᴏᴅᴀʏ</b>"
                    if PREMIUM_AND_REFERAL_MODE == True:
                        text += "<b>ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴅɪʀᴇᴄᴛ ғɪʟᴇꜱ ᴡɪᴛʜᴏᴜᴛ ᴀɴʏ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴꜱ ᴛʜᴇɴ ʙᴜʏ ʙᴏᴛ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ☺️\n\n💶 ꜱᴇɴᴅ /plan ᴛᴏ ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ</b>"
                    await message.reply_text(
                        text=text.format(message.from_user.mention),
                        protect_content=True,
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                    return
            if STREAM_MODE == True:
                button = [[InlineKeyboardButton('sᴛʀᴇᴀᴍ ᴀɴᴅ ᴅᴏᴡɴʟᴏᴀᴅ', callback_data=f'generate_stream_link:{file_id}')]]
                reply_markup=InlineKeyboardMarkup(button)
            else:
                reply_markup = None
            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                protect_content=True if pre == 'filep' else False,
                reply_markup=reply_markup
            )
            filetype = msg.media
            file = getattr(msg, filetype.value)
            title = file.file_name
            size=get_size(file.file_size)
            f_caption = f"<code>{title}</code>"
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='')
                except:
                    return
            await msg.edit_caption(caption=f_caption)
            btn = [[InlineKeyboardButton("✅ ɢᴇᴛ ғɪʟᴇ ᴀɢᴀɪɴ ✅", callback_data=f'del#{file_id}')]]
            k = await msg.reply(text=f"<blockquote><b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ <b><u>10 mins</u> 🫥 <i></b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs)</i>.\n\n<b><i>ᴘʟᴇᴀsᴇ ғᴏʀᴡᴀʀᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ᴏʀ ᴀɴy ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ.</i></b></blockquote>")
            await asyncio.sleep(600)
            try:
                await msg.delete()
            except Exception as e:
                logger.warning(f"Failed to delete message in file cleanup: {e}")
            await k.edit_text("<b>✅ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ɪs sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴀɢᴀɪɴ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ</b>",reply_markup=InlineKeyboardMarkup(btn))
            return
        except Exception as e:
            logger.error(f"Error processing file details from base64 data: {e}")
            pass # Continue to the "No such file exist" message
        return await message.reply('No such file exist.')
        
    files = files_
    title = files["file_name"]
    size=get_size(files["file_size"])
    f_caption=files["caption"]
    if CUSTOM_FILE_CAPTION:
        try:
            f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
        except:
            f_caption=f_caption
    if f_caption is None:
        f_caption = f"{' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), files['file_name'].split()))}"
    
    # Verification logic
    if not await db.has_premium_access(message.from_user.id):
        if not await check_verification(client, message.from_user.id) and VERIFY == True:
            btn = [[
                InlineKeyboardButton("ᴠᴇʀɪғʏ", url=await get_token(client, message.from_user.id, f"https://telegram.me/{temp.U_NAME}?start="))
            ],[
                InlineKeyboardButton("ʜᴏᴡ ᴛᴏ ᴠᴇʀɪғʏ", url=VERIFY_TUTORIAL)
            ]]
            text = "<b>ʜᴇʏ {} 👋,\n\nʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴠᴇʀɪғɪᴇᴅ ᴛᴏᴅᴀʏ, ᴘʟᴇᴀꜱᴇ ᴄʟɪᴄᴋ ᴏɴ ᴠᴇʀɪғʏ & ɢᴇᴛ ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇꜱꜱ ғᴏʀ ᴛᴏᴅᴀʏ</b>"
            if PREMIUM_AND_REFERAL_MODE == True:
                text += "<b>ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴅɪʀᴇᴄᴛ ғɪʟᴇꜱ ᴡɪᴛʜᴏᴜᴛ ᴀɴʏ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴꜱ ᴛʜᴇɴ ʙᴜʏ ʙᴏᴛ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ☺️\n\n💶 ꜱᴇɴᴅ /plan ᴛᴏ ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ</b>"
            await message.reply_text(
                text=text.format(message.from_user.mention),
                protect_content=True,
                reply_markup=InlineKeyboardMarkup(btn)
            )
            return
    
    if STREAM_MODE == True:
        button = [[InlineKeyboardButton('sᴛʀᴇᴀᴍ ᴀɴᴅ ᴅᴏᴡɴʟᴏᴀᴅ', callback_data=f'generate_stream_link:{file_id}')]]
        reply_markup=InlineKeyboardMarkup(button)
    else:
        reply_markup = None
    msg = await client.send_cached_media(
        chat_id=message.from_user.id,
        file_id=file_id,
        caption=f_caption,
        protect_content=True if pre == 'filep' else False,
        reply_markup=reply_markup
    )
    btn = [[InlineKeyboardButton("✅ ɢᴇᴛ ғɪʟᴇ ᴀɢᴀɪɴ ✅", callback_data=f'del#{file_id}')]]
    k = await msg.reply(text=f"<blockquote><b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ <b><u>10 mins</u> 🫥 <i></b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs)</i>.\n\n<b><i>ᴘʟᴇᴀsᴇ ғᴏʀᴡᴀʀᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ᴏʀ ᴀɴy ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ.</i></b></blockquote>")
    await asyncio.sleep(600)
    try:
        await msg.delete()
    except Exception as e:
        logger.warning(f"Failed to delete message in file cleanup: {e}")
    await k.edit_text("<b>✅ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ɪs sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴀɢᴀɪɴ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ</b>",reply_markup=InlineKeyboardMarkup(btn))
    return   

