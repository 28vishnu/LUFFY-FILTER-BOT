# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os, string, logging, random, asyncio, time, datetime, re, sys, json, base64
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import *
from database.ia_filterdb import col, sec_col, get_file_details, unpack_new_file_id, get_bad_files
from database.users_chats_db import db, delete_all_referal_users, get_referal_users_count, get_referal_all_users, referal_add_user
from database.join_reqs import JoinReqs
from info import CLONE_MODE, OWNER_LNK, REACTIONS, CHANNELS, REQUEST_TO_JOIN_MODE, TRY_AGAIN_BTN, ADMINS, SHORTLINK_MODE, PREMIUM_AND_REFERAL_MODE, STREAM_MODE, AUTH_CHANNEL, REFERAL_PREMEIUM_TIME, REFERAL_COUNT, PAYMENT_TEXT, PAYMENT_QR, LOG_CHANNEL, PICS, BATCH_FILE_CAPTION, CUSTOM_FILE_CAPTION, PROTECT_CONTENT, CHNL_LNK, GRP_LNK, REQST_CHANNEL, SUPPORT_CHAT, MAX_B_TN, VERIFY, SHORTLINK_API, SHORTLINK_URL, TUTORIAL, VERIFY_TUTORIAL, IS_TUTORIAL, URL
from utils import get_settings, pub_is_subscribed, get_size, is_subscribed, save_group_settings, temp, verify_user, check_token, check_verification, get_token, get_shortlink, get_tutorial, get_seconds
from database.connections_mdb import active_connection
from urllib.parse import quote_plus
from TechVJ.util.file_properties import get_name, get_hash, get_media_file_size
logger = logging.getLogger(__name__)

BATCH_FILES = {}
join_db = JoinReqs

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except:
        pass
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        buttons = [[
            InlineKeyboardButton('⤬ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ⤬', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
        ],[
            InlineKeyboardButton('sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ', url=f'https://t.me/{SUPPORT_CHAT}'),
            InlineKeyboardButton('ᴍᴏᴠɪᴇ ɢʀᴏᴜᴘ', url=GRP_LNK)
        ],[
            InlineKeyboardButton('ᴊᴏɪɴ ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url=CHNL_LNK)
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply(script.START_TXT.format(message.from_user.mention if message.from_user else message.chat.title, temp.U_NAME, temp.B_NAME), reply_markup=reply_markup, disable_web_page_preview=True)
        await asyncio.sleep(2) # 😢 https://github.com/EvamariaTG/EvaMaria/blob/master/plugins/p_ttishow.py#L17 😬 wait a bit, before checking.
        if not await db.get_chat(message.chat.id):
            total=await client.get_chat_members_count(message.chat.id)
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, "Unknown"))       
            await db.add_chat(message.chat.id, message.chat.title)
        return 
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention))
    if len(message.command) != 2:
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
    
    if AUTH_CHANNEL and not await is_subscribed(client, message):
        try:
            if REQUEST_TO_JOIN_MODE == True:
                invite_link = await client.create_chat_invite_link(chat_id=(int(AUTH_CHANNEL)), creates_join_request=True)
            else:
                invite_link = await client.create_chat_invite_link(int(AUTH_CHANNEL))
        except Exception as e:
            print(e)
            await message.reply_text("Make sure Bot is admin in Forcesub channel")
            return
        try:
            btn = [[InlineKeyboardButton("ʙᴀᴄᴋᴜᴘ ᴄʜᴀɴɴᴇʟ", url=invite_link.invite_link)]]
            if message.command[1] != "subscribe":
                if REQUEST_TO_JOIN_MODE == True:
                    if TRY_AGAIN_BTN == True:
                        try:
                            kk, file_id = message.command[1].split("_", 1)
                            btn.append([InlineKeyboardButton("↻ ᴛʀʏ ᴀɢᴀɪɴ", callback_data=f"checksub#{kk}#{file_id}")])
                        except (IndexError, ValueError):
                            btn.append([InlineKeyboardButton("↻ ᴛʀʏ ᴀɢᴀɪɴ", url=f"https://t.me/{temp.U_NAME}?start={message.command[1]}")])
                else:
                    try:
                        kk, file_id = message.command[1].split("_", 1)
                        btn.append([InlineKeyboardButton("↻ ᴛʀʏ ᴀɢᴀɪɴ", callback_data=f"checksub#{kk}#{file_id}")])
                    except (IndexError, ValueError):
                        btn.append([InlineKeyboardButton("↻ ᴛʀʏ ᴀɢᴀɪɴ", url=f"https://t.me/{temp.U_NAME}?start={message.command[1]}")])
            if REQUEST_TO_JOIN_MODE == True:
                if TRY_AGAIN_BTN == True:
                    text = "**🕵️ ʏᴏᴜ ᴅᴏ ɴᴏᴛ ᴊᴏɪɴ ᴍʏ ʙᴀᴄᴋᴜᴘ ᴄʜᴀɴɴᴇʟ ғɪʀsᴛ ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ ᴛʜᴇɴ ᴛʀʏ ᴀɢᴀɪɴ**"
                else:
                    await db.set_msg_command(message.from_user.id, com=message.command[1])
                    text = "**🕵️ ʏᴏᴜ ᴅᴏ ɴᴏᴛ ᴊᴏɪɴ ᴍʏ ʙᴀᴄᴋᴜᴘ ᴄʜᴀɴɴᴇʟ ғɪʀsᴛ ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ**"
            else:
                text = "**🕵️ ʏᴏᴜ ᴅᴏ ɴᴏᴛ ᴊᴏɪɴ ᴍʏ ʙᴀᴄᴋᴜᴘ ᴄʜᴀɴɴᴇʟ ғɪʀsᴛ ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ ᴛʜᴇɴ ᴛʀʏ ᴀɢᴀɪɴ**"
            await client.send_message(
                chat_id=message.from_user.id,
                text=text,
                reply_markup=InlineKeyboardMarkup(btn),
                parse_mode=enums.ParseMode.MARKDOWN
            )
            return
        except Exception as e:
            print(e)
            return await message.reply_text("something wrong with force subscribe.")
            
    if len(message.command) == 2 and message.command[1] in ["subscribe", "error", "okay", "help"]:
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
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return
    data = message.command[1]
    if data.split("-", 1)[0] == "VJ":
        user_id = int(data.split("-", 1)[1])
        vj = await referal_add_user(user_id, message.from_user.id)
        if vj and PREMIUM_AND_REFERAL_MODE == True:
            await message.reply(f"<b>You have joined using the referral link of user with ID {user_id}\n\nSend /start again to use the bot</b>")
            num_referrals = await get_referal_users_count(user_id)
            await client.send_message(chat_id = user_id, text = "<b>{} start the bot with your referral link\n\nTotal Referals - {}</b>".format(message.from_user.mention, num_referrals))
            if num_referrals == REFERAL_COUNT:
                time = REFERAL_PREMEIUM_TIME       
                seconds = await get_seconds(time)
                if seconds > 0:
                    expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
                    user_data = {"id": user_id, "expiry_time": expiry_time} 
                    await db.update_user(user_data)  # Use the update_user method to update or insert user data
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
    if data.split("-", 1)[0] == "BATCH":
        sts = await message.reply("<b>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
        file_id = data.split("-", 1)[1]
        msgs = BATCH_FILES.get(file_id)
        if not msgs:
            file = await client.download_media(file_id)
            try: 
                with open(file) as file_data:
                    msgs=json.loads(file_data.read())
            except:
                await sts.edit("FAILED")
                return await client.send_message(LOG_CHANNEL, "UNABLE TO OPEN FILE.")
            os.remove(file)
            BATCH_FILES[file_id] = msgs

        filesarr = []
        for msg in msgs:
            title = msg.get("title")
            size=get_size(int(msg.get("size", 0)))
            f_caption=msg.get("caption", "")
            if BATCH_FILE_CAPTION:
                try:
                    f_caption=BATCH_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                except:
                    f_caption=f_caption
            if f_caption is None:
                f_caption = f"{title}"
            try:
                if STREAM_MODE == True:
                    log_msg = await client.send_cached_media(chat_id=LOG_CHANNEL, file_id=msg.get("file_id"))
                    fileName = {quote_plus(get_name(log_msg))}
                    stream = f"{URL}watch/{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
                    download = f"{URL}{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"

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
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False),
                    reply_markup=reply_markup
                )
                filesarr.append(msg)
                
            except FloodWait as e:
                await asyncio.sleep(e.value)
                msg = await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False),
                    reply_markup=InlineKeyboardMarkup(button)
                )
                filesarr.append(msg)
            except:
                continue
            await asyncio.sleep(1) 
        await sts.delete()
        k = await client.send_message(chat_id = message.from_user.id, text=f"<blockquote><b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ <b><u>10 mins</u> 🫥 <i></b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs)</i>.\n\n<b><i>ᴘʟᴇᴀsᴇ ғᴏʀᴡᴀʀᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ᴏʀ ᴀɴʏ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ.</i></b></blockquote>")
        await asyncio.sleep(600)
        for x in filesarr:
            await x.delete()
        await k.edit_text("<b>✅ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ɪs sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ</b>")  
        return
    
    elif data.split("-", 1)[0] == "DSTORE":
        sts = await message.reply("<b>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
        b_string = data.split("-", 1)[1]
        decoded = (base64.urlsafe_b64decode(b_string + "=" * (-len(b_string) % 4))).decode("ascii")
        try:
            f_msg_id, l_msg_id, f_chat_id, protect = decoded.split("_", 3)
        except:
            f_msg_id, l_msg_id, f_chat_id = decoded.split("_", 2)
            protect = "/pbatch" if PROTECT_CONTENT else "batch"
        diff = int(l_msg_id) - int(f_msg_id)
        filesarr = []
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
                    fileName = {quote_plus(get_name(log_msg))}
                    stream = f"{URL}watch/{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
                    download = f"{URL}{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
 
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
                except:
                    continue
            elif msg.empty:
                continue
            else:
                try:
                    p = await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    p = await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                except:
                    continue
            filesarr.append(p)
            await asyncio.sleep(1)
        await sts.delete()
        k = await client.send_message(chat_id = message.from_user.id, text=f"<blockquote><b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ <b><u>10 mins</u> 🫥 <i></b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs)</i>.\n\n<b><i>ᴘʟᴇᴀsᴇ ғᴏʀᴡᴀʀᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ᴏʀ ᴀɴʏ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ.</i></b></blockquote>")
        await asyncio.sleep(600)
        for x in filesarr:
            await x.delete()
        await k.edit_text("<b>✅ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ɪs sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ</b>")
        return

    elif data.split("-", 1)[0] == "verify":
        userid = data.split("-", 2)[1]
        token = data.split("-", 3)[2]
        if str(message.from_user.id) != str(userid):
            return await message.reply_text(text="<b>ɪɴᴠᴀʟɪᴅ ʟɪɴᴋ ᴏʀ ᴇxᴘɪʀᴇᴅ ʟɪɴᴋ</b>", protect_content=True)
        is_valid = await check_token(client, userid, token)
        if is_valid == True:
            text = "<b>ʜᴇʏ {} 👋,\n\nʏᴏᴜ ʜᴀᴠᴇ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ᴛʜᴇ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ...\n\nɴᴏᴡ ʏᴏᴜ ʜᴀᴠᴇ ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇss ᴛɪʟʟ ᴛᴏᴅᴀʏ ɴᴏᴡ ᴇɴᴊᴏʏ\n\n</b>"
            if PREMIUM_AND_REFERAL_MODE == True:
                text += "<b>ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴅɪʀᴇᴄᴛ ғɪʟᴇꜱ ᴡɪᴛʜᴏᴜᴛ ᴀɴʏ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴꜱ ᴛʜᴇɴ ʙᴜʏ ʙᴏᴛ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ☺️\n\n💶 ꜱᴇɴᴅ /plan ᴛᴏ ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ</b>"           
            await message.reply_text(text=text.format(message.from_user.mention), protect_content=True)
            await verify_user(client, userid, token)
        else:
            return await message.reply_text(text="<b>ɪɴᴠᴀʟɪᴅ ʟɪɴᴋ ᴏʀ ᴇxᴘɪʀᴇᴅ ʟɪɴᴋ</b>", protect_content=True)
            
    if data.startswith("sendfiles"):
        chat_id = int("-" + file_id.split("-")[1])
        userid = message.from_user.id if message.from_user else None
        settings = await get_settings(chat_id)
        pre = 'allfilesp' if settings['file_secure'] else 'allfiles'
        g = await get_shortlink(chat_id, f"https://telegram.me/{temp.U_NAME}?start={pre}_{file_id}")
        btn = [[
            InlineKeyboardButton('ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ', url=g)
        ]]
        if settings['tutorial']:
            btn.append([InlineKeyboardButton('ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ', url=await get_tutorial(chat_id))])
        text = "<b>✅ ʏᴏᴜʀ ғɪʟᴇ ʀᴇᴀᴅʏ ᴄʟɪᴄᴋ ᴏɴ ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ ʙᴜᴛᴛᴏɴ ᴛʜᴇɴ ᴏᴘᴇɴ ʟɪɴᴋ ᴛᴏ ɢᴇᴛ ғɪʟᴇ\n\n</b>"
        if PREMIUM_AND_REFERAL_MODE == True:
            text += "<b>ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴅɪʀᴇᴄᴛ ғɪʟᴇꜱ ᴡɪᴛʜᴏᴜᴛ ᴀɴʏ ᴏᴘᴇɴɪɴɢ ʟɪɴᴋ ᴀɴᴅ ᴡᴀᴛᴄʜɪɴɢ ᴀᴅs ᴛʜᴇɴ ʙᴜʏ ʙᴏᴛ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ☺️\n\n💶 ꜱᴇɴᴅ /plan ᴛᴏ ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ</b>"
        k = await client.send_message(chat_id=message.from_user.id, text=text, reply_markup=InlineKeyboardMarkup(btn))
        await asyncio.sleep(300)
        await k.edit("<b>✅ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ɪs sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ</b>")
        return
        
    
    elif data.startswith("short"):
        user = message.from_user.id
        chat_id = temp.SHORT.get(user)
        settings = await get_settings(chat_id)
        pre = 'filep' if settings['file_secure'] else 'file'
        g = await get_shortlink(chat_id, f"https://telegram.me/{temp.U_NAME}?start={pre}_{file_id}")
        btn = [[
            InlineKeyboardButton('ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ', url=g)
        ]]
        if settings['tutorial']:
            btn.append([InlineKeyboardButton('ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ', url=await get_tutorial(chat_id))])
        text = "<b>✅ ʏᴏᴜʀ ғɪʟᴇ ʀᴇᴀᴅʏ ᴄʟɪᴄᴋ ᴏɴ ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ ʙᴜᴛᴛᴏɴ ᴛʜᴇɴ ᴏᴘᴇɴ ʟɪɴᴋ ᴛᴏ ɢᴇᴛ ғɪʟᴇ\n\n</b>"
        if PREMIUM_AND_REFERAL_MODE == True:
            text += "<b>ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴅɪʀᴇᴄᴛ ғɪʟᴇꜱ ᴡɪᴛʜᴏᴜᴛ ᴀɴʏ ᴏᴘᴇɴɪɴɢ ʟɪɴᴋ ᴀɴᴅ ᴡᴀᴛᴄʜɪɴɢ ᴀᴅs ᴛʜᴇɴ ʙᴜʏ ʙᴏᴛ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ☺️\n\n💶 ꜱᴇɴᴅ /plan ᴛᴏ ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ</b>"
        k = await client.send_message(chat_id=user, text=text, reply_markup=InlineKeyboardMarkup(btn))
        await asyncio.sleep(1200)
        await k.edit("<b>✅ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ɪs sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ</b>")
        return
        
    elif data.startswith("all"):
        files = temp.GETALL.get(file_id)
        if not files:
            return await message.reply('<b><i>No such file exist.</b></i>')
        filesarr = []
        for file in files:
            file_id = file["file_id"]
            files1 = await get_file_details(file_id)
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
                protect_content=True if pre == 'allfilesp' else False,
                reply_markup=reply_markup
            )
            filesarr.append(msg)
        k = await client.send_message(chat_id = message.from_user.id, text=f"<blockquote><b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ <b><u>10 mins</u> 🫥 <i></b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs)</i>.\n\n<b><i>ᴘʟᴇᴀsᴇ ғᴏʀᴡᴀʀᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ᴏʀ ᴀɴʏ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ.</i></b></div>")
        await asyncio.sleep(600)
        for x in filesarr:
            await x.delete()
        await k.edit_text("<b>✅ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ɪs sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ</b>")
        return    
        
    elif data.startswith("files"):
        user = message.from_user.id
        if temp.SHORT.get(user)==None:
            await message.reply_text(text="<b>Please Search Again in Group</b>")
        else:
            chat_id = temp.SHORT.get(user)
        settings = await get_settings(chat_id)
        pre = 'filep' if settings['file_secure'] else 'file'
        if settings['is_shortlink'] and not await db.has_premium_access(user):
            g = await get_shortlink(chat_id, f"https://telegram.me/{temp.U_NAME}?start={pre}_{file_id}")
            btn = [[
                InlineKeyboardButton('ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ', url=g)
            ]]
            if settings['tutorial']:
                btn.append([InlineKeyboardButton('ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ', url=await get_tutorial(chat_id))])
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
        pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
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
                    return await msg.edit_caption(caption=f_caption)
            btn = [[InlineKeyboardButton("✅ ɢᴇᴛ ғɪʟᴇ ᴀɢᴀɪɴ ✅", callback_data=f'del#{file_id}')]]
            k = await msg.reply(text=f"<blockquote><b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ <b><u>10 mins</u> 🫥 <i></b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs)</i>.\n\n<b><i>ᴘʟᴇᴀsᴇ ғᴏʀᴡᴀʀᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ᴏʀ ᴀɴʏ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ.</i></b></blockquote>")
            await asyncio.sleep(600)
            await msg.delete()
            await k.edit_text("<b>✅ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ɪs sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴀɢᴀɪɴ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ</b>",reply_markup=InlineKeyboardMarkup(btn))
            return
        except:
            pass
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
    k = await msg.reply(text=f"<blockquote><b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ <b><u>10 mins</u> 🫥 <i></b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs)</i>.\n\n<b><i>ᴘʟᴇᴀsᴇ ғᴏʀᴡᴀʀᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ᴏʀ ᴀɴʏ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ.</i></b></blockquote>")
    await asyncio.sleep(600)
    await msg.delete()
    await k.edit_text("<b>✅ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ɪs sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴀɢᴀɪɴ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ</b>",reply_markup=InlineKeyboardMarkup(btn))
    
    
@Client.on_message(filters.command('settings'))
async def settings(client, message):
    userid = message.from_user.id if message.from_user else None
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        buttons = [[
            InlineKeyboardButton('Oᴘᴇɴ Sᴇᴛᴛɪɴɢs Iɴ Gʀᴏᴜᴘ', callback_data=f'opnsetgrp#{message.chat.id}'),
            InlineKeyboardButton('Oᴘᴇɴ Sᴇᴛᴛɪɴɢs Iɴ PM', callback_data=f'opnsetpm#{message.chat.id}')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_text(
            text="<b>Hᴇʀᴇ Iꜱ Yᴏᴜʀ Sᴇᴛᴛɪɴɢs Bᴜᴛᴛᴏɴs Fᴏʀ Yᴏᴜr Gʀᴏᴜᴘ ⚙</b>",
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await message.reply_text(
            text="<b>Yᴏᴜ Cᴀɴ Usᴇ Tʜɪs Cᴏᴍᴍᴀɴᴅ Iɴ Gʀᴏᴜᴘs Oɴʟy !</b>",
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML
        )

@Client.on_message(filters.command('status') & filters.user(ADMINS))
async def status(client, message):
    
    total_users = await db.total_users_count()
    total_chats = await db.total_chat_count()
    total_files = await col.estimated_document_count()
    total_files_sec = await sec_col.estimated_document_count()
    total_gfilters = await get_gfilters('gfilters')
    total_gfilters_count = len(total_gfilters) if total_gfilters else 0
    
    # Get database sizes
    db_stats = await db.db.command("dbstats")
    file_db_stats = await col.database.command("dbstats")
    sec_file_db_stats = await sec_col.database.command("dbstats")
    other_db_stats = await mydb.command("dbstats")

    # Calculate used and free storage in MB
    total_storage_bytes = db_stats['dataSize'] + file_db_stats['dataSize'] + sec_file_db_stats['dataSize'] + other_db_stats['dataSize']
    total_free_storage_bytes = db_stats['fsTotalSize'] - db_stats['fsUsedSize'] + \
                               file_db_stats['fsTotalSize'] - file_db_stats['fsUsedSize'] + \
                               sec_file_db_stats['fsTotalSize'] - sec_file_db_stats['fsUsedSize'] + \
                               other_db_stats['fsTotalSize'] - other_db_stats['fsUsedSize']

    total_storage_mb = round(total_storage_bytes / (1024 * 1024), 2)
    total_free_storage_mb = round(total_free_storage_bytes / (1024 * 1024), 2)

    if MULTIPLE_DATABASE == True:
        text = script.STATUS_TXT.format(total_files + total_files_sec, total_users, total_chats, total_files, round(file_db_stats['dataSize'] / (1024 * 1024), 2), round((file_db_stats['fsTotalSize'] - file_db_stats['fsUsedSize']) / (1024 * 1024), 2), total_files_sec, round(sec_file_db_stats['dataSize'] / (1024 * 1024), 2), round((sec_file_db_stats['fsTotalSize'] - sec_file_db_stats['fsUsedSize']) / (1024 * 1024), 2), round(other_db_stats['dataSize'] / (1024 * 1024), 2), round((other_db_stats['fsTotalSize'] - other_db_stats['fsUsedSize']) / (1024 * 1024), 2))
    else:
        text = script.SEC_STATUS_TXT.format(total_users, total_chats, total_files, round(file_db_stats['dataSize'] / (1024 * 1024), 2), round((file_db_stats['fsTotalSize'] - file_db_stats['fsUsedSize']) / (1024 * 1024), 2))
    
    await message.reply_text(
        text=text,
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True
    )

@Client.on_message(filters.command('ban') & filters.user(ADMINS))
async def ban(client, message):
    if len(message.command) == 1:
        await message.reply_text(
            'Use this command to ban a user.\n\nUsage:\n\n`/ban user_id ban_reason`\n\nEg: `/ban 1234567 This is a test reason`'
        )
        return

    try:
        user_id = int(message.command[1])
        ban_reason = ' '.join(message.command[2:])
        if not ban_reason:
            ban_reason = 'No reason provided.'
    except:
        await message.reply_text(
            'Use this command to ban a user.\n\nUsage:\n\n`/ban user_id ban_reason`\n\nEg: `/ban 1234567 This is a test reason`'
        )
        return

    ban_status = await db.get_ban_status(user_id)
    if ban_status['is_banned']:
        await message.reply_text(
            f'This user is already banned.\nReason: {ban_status["ban_reason"]}'
        )
        return

    await db.ban_user(user_id, ban_reason)
    await message.reply_text(f'Successfully banned {user_id}.')

@Client.on_message(filters.command('unban') & filters.user(ADMINS))
async def unban(client, message):
    if len(message.command) == 1:
        await message.reply_text(
            'Use this command to unban a user.\n\nUsage:\n\n`/unban user_id`\n\nEg: `/unban 1234567`'
        )
        return

    try:
        user_id = int(message.command[1])
    except:
        await message.reply_text(
            'Use this command to unban a user.\n\nUsage:\n\n`/unban user_id`\n\nEg: `/unban 1234567`'
        )
        return

    ban_status = await db.get_ban_status(user_id)
    if not ban_status['is_banned']:
        await message.reply_text('This user is not banned.')
        return

    await db.remove_ban(user_id)
    await message.reply_text(f'Successfully unbanned {user_id}.')

@Client.on_message(filters.command('users') & filters.user(ADMINS))
async def users(client, message):
    users_list = await db.get_all_users()
    users_text = 'Total users:\n\n'
    for user in users_list:
        users_text += f'{user["id"]} - {user["name"]}\n'
    await message.reply_text(users_text)

@Client.on_message(filters.command('chats') & filters.user(ADMINS))
async def chats(client, message):
    chats_list = await db.get_all_chats()
    chats_text = 'Total chats:\n\n'
    for chat in chats_list:
        chats_text += f'{chat["id"]} - {chat["title"]}\n'
    await message.reply_text(chats_text)

@Client.on_message(filters.command('broadcast') & filters.user(ADMINS))
async def broadcast(client, message):
    if len(message.command) < 2:
        await message.reply_text('Please provide a message to broadcast.')
        return

    message_to_send = message.reply_to_message or message.text.split(' ', 1)[1]
    users_list = await db.get_all_users()
    
    success_count = 0
    failed_count = 0

    for user in users_list:
        try:
            if isinstance(message_to_send, Message):
                await message_to_send.copy(user['id'])
            else:
                await client.send_message(user['id'], message_to_send)
            success_count += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            if isinstance(message_to_send, Message):
                await message_to_send.copy(user['id'])
            else:
                await client.send_message(user['id'], message_to_send)
            success_count += 1
        except Exception as e:
            logger.error(f"Error broadcasting to user {user['id']}: {e}")
            failed_count += 1
            
    await message.reply_text(f'Broadcast complete.\nSuccess: {success_count}\nFailed: {failed_count}')


@Client.on_message(filters.command('grp_broadcast') & filters.user(ADMINS))
async def grp_broadcast(client, message):
    if len(message.command) < 2:
        await message.reply_text('Please provide a message to broadcast to groups.')
        return

    message_to_send = message.reply_to_message or message.text.split(' ', 1)[1]
    chats_list = await db.get_all_chats()
    
    success_count = 0
    failed_count = 0

    for chat in chats_list:
        try:
            if isinstance(message_to_send, Message):
                await message_to_send.copy(chat['id'])
            else:
                await client.send_message(chat['id'], message_to_send)
            success_count += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            if isinstance(message_to_send, Message):
                await message_to_send.copy(chat['id'])
            else:
                await client.send_message(chat['id'], message_to_send)
            success_count += 1
        except Exception as e:
            logger.error(f"Error broadcasting to chat {chat['id']}: {e}")
            failed_count += 1
            
    await message.reply_text(f'Group broadcast complete.\nSuccess: {success_count}\nFailed: {failed_count}')

@Client.on_message(filters.command('leave') & filters.user(ADMINS))
async def leave_chat(client, message):
    if len(message.command) < 2:
        await message.reply_text('Please provide the chat ID to leave.')
        return

    try:
        chat_id = int(message.command[1])
    except ValueError:
        await message.reply_text('Invalid chat ID. Please provide a numeric ID.')
        return

    try:
        await client.leave_chat(chat_id)
        await db.delete_chat(chat_id)
        await message.reply_text(f'Successfully left chat {chat_id}.')
    except Exception as e:
        await message.reply_text(f'Error leaving chat {chat_id}: {e}')

@Client.on_message(filters.command('disable') & filters.user(ADMINS))
async def disable_chat(client, message):
    if len(message.command) < 2:
        await message.reply_text('Please provide the chat ID to disable.\nUsage: `/disable chat_id reason`')
        return

    try:
        chat_id = int(message.command[1])
        reason = ' '.join(message.command[2:]) if len(message.command) > 2 else 'No reason provided.'
    except ValueError:
        await message.reply_text('Invalid chat ID. Please provide a numeric ID.')
        return

    chat_status = await db.get_chat_status(chat_id)
    if chat_status['is_disabled']:
        await message.reply_text(f'Chat {chat_id} is already disabled.\nReason: {chat_status["reason"]}')
        return

    await db.disable_chat(chat_id, reason)
    await message.reply_text(f'Successfully disabled chat {chat_id}.')

@Client.on_message(filters.command('enable') & filters.user(ADMINS))
async def enable_chat(client, message):
    if len(message.command) < 2:
        await message.reply_text('Please provide the chat ID to enable.\nUsage: `/enable chat_id`')
        return

    try:
        chat_id = int(message.command[1])
    except ValueError:
        await message.reply_text('Invalid chat ID. Please provide a numeric ID.')
        return

    chat_status = await db.get_chat_status(chat_id)
    if not chat_status['is_disabled']:
        await message.reply_text(f'Chat {chat_id} is not disabled.')
        return

    await db.enable_chat(chat_id)
    await message.reply_text(f'Successfully enabled chat {chat_id}.')

@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def connected_channels(client, message):
    # This function needs to interact with the database to get connected channels
    # Assuming there's a function in db.py to get all connected channels.
    # For now, let's just send a placeholder message.
    await message.reply_text("This feature is under development.")

@Client.on_message(filters.command('request'))
async def movie_request(client, message):
    if REQST_CHANNEL:
        if len(message.command) < 2:
            await message.reply_text("Please provide the movie/series name to request.\nUsage: `/request movie_name`")
            return
        
        movie_name = ' '.join(message.command[1:])
        try:
            await client.send_message(
                chat_id=REQST_CHANNEL,
                text=f"**New Movie Request:**\n\n**Requested by:** {message.from_user.mention} (ID: `{message.from_user.id}`)\n**Movie/Series Name:** `{movie_name}`\n**Requested from chat:** {message.chat.title} (ID: `{message.chat.id}`)",
                parse_mode=enums.ParseMode.MARKDOWN
            )
            await message.reply_text("Your request has been sent to the admins!")
        except Exception as e:
            logger.error(f"Error sending request to REQST_CHANNEL: {e}")
            await message.reply_text("Failed to send your request. Please try again later.")
    else:
        await message.reply_text("Movie request channel is not configured.")

@Client.on_message(filters.command('deletefiles') & filters.user(ADMINS))
async def delete_files_by_query(client, message):
    if len(message.command) < 2:
        await message.reply_text("Please provide a query to delete files.\nUsage: `/deletefiles <query>`")
        return
    
    query_text = ' '.join(message.command[1:])
    
    btn = [[
        InlineKeyboardButton("Yes", callback_data=f"killfilesdq#{query_text}"),
        InlineKeyboardButton("No", callback_data="delallcancel")
    ]]
    await message.reply_text(
        f"Are you sure you want to delete all files matching `{query_text}` from the database? This action cannot be undone.",
        reply_markup=InlineKeyboardMarkup(btn),
        parse_mode=enums.ParseMode.MARKDOWN
    )

@Client.on_message(filters.command('plan') & filters.private & filters.user(PREMIUM_AND_REFERAL_MODE))
async def plan(client, message):
    if await db.has_premium_access(message.from_user.id):
        user_data = await db.get_user_data(message.from_user.id)
        expiry_time = user_data.get("expiry_time")
        if expiry_time:
            time_left = expiry_time - datetime.datetime.now()
            days = time_left.days
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            await message.reply_text(f"**You have premium access!\n\nTime remaining: {days} days, {hours} hours, {minutes} minutes, {seconds} seconds.**")
        else:
            await message.reply_text("**You have premium access, but no expiry time is set.**")
    else:
        btn = [ 
            [InlineKeyboardButton("ɢᴇᴛ ғʀᴇᴇ ᴛʀᴀɪʟ ғᴏʀ 𝟻 ᴍɪɴᴜᴛᴇꜱ ☺️", callback_data="get_trail")],
            [InlineKeyboardButton("ʙᴜʏ sᴜʙsᴄʀɪᴘᴛɪᴏɴ : ʀᴇᴍᴏᴠᴇ ᴀᴅs", callback_data="buy_premium")],
            [InlineKeyboardButton("⚠️ ᴄʟᴏsᴇ / ᴅᴇʟᴇᴛᴇ ⚠️", callback_data="close_data")]
        ]
        reply_markup = InlineKeyboardMarkup(btn)
        m=await message.reply_sticker("CAACAgIAAxkBAAIBTGVjQbHuhOiboQsDm35brLGyLQ28AAJ-GgACglXYSXgCrotQHjibHgQ")         
        await message.reply_text(f"**😢 You Don't Have Any Premium Subscription.\n\n Check Out Our Premium /plan**",reply_markup=reply_markup)
        await asyncio.sleep(2)
        await m.delete()

@Client.on_message(filters.command("totalrequests") & filters.private & filters.user(ADMINS))
async def total_requests(client, message):
    if join_db().isActive():
        total = await join_db().get_all_users_count()
        await message.reply_text(
            text=f"Total Requests: {total}",
            parse_mode=enums.ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    else:
        await message.reply_text("Join Requests database is not active.")
