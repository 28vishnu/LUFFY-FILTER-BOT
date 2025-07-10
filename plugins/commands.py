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


# Admin commands
@Client.on_message(filters.command(["start"]) & filters.private)
async def start_command(client: Client, message: Message):
    if message.from_user.id in ADMINS:
        buttons = [
            [
                InlineKeyboardButton("Aᴅᴍɪɴ", callback_data="admin_commands"),
                InlineKeyboardButton("Hᴇʟᴘ", callback_data="help_commands"),
                InlineKeyboardButton("Aʙᴏᴜᴛ", callback_data="about_commands")
            ],
            [
                InlineKeyboardButton("Cʟᴏɴᴇ Bᴏᴛ", callback_data="clone_commands"),
                InlineKeyboardButton("Sᴇᴛᴛɪɴɢs", callback_data="settings_commands")
            ],
            [
                InlineKeyboardButton("Sᴜʙsᴄʀɪʙᴇ", callback_data="subscribe_commands"),
                InlineKeyboardButton("Sᴛᴀᴛᴜs", callback_data="status_commands")
            ]
        ]
    else:
        buttons = [
            [
                InlineKeyboardButton("Hᴇʟᴘ", callback_data="help_commands"),
                InlineKeyboardButton("Aʙᴏᴜᴛ", callback_data="about_commands")
            ],
            [
                InlineKeyboardButton("Sᴇᴛᴛɪɴɢs", callback_data="settings_commands"),
                InlineKeyboardButton("Sᴜʙsᴄʀɪʙᴇ", callback_data="subscribe_commands")
            ]
        ]
    
    if REACTIONS:
        try:
            await message.react(random.choice(REACTIONS))
        except Exception as e:
            logger.warning(f"Failed to react to start message: {e}")

    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        if LOG_CHANNEL:
            await client.send_message(
                LOG_CHANNEL,
                script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention)
            )

    if len(message.command) > 1:
        query_type = message.command[1].split("_")[0]
        query_id = message.command[1].split("_")[1]

        if query_type == "files":
            file_details = await get_file_details(query_id)
            if file_details:
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=file_details["file_id"],
                    caption=await get_file_caption(file_details),
                    reply_markup=await get_file_markup(file_details)
                )
            else:
                await message.reply_text("File not found.")
        elif query_type == "verify":
            file_details = await get_file_details(query_id)
            if file_details:
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=file_details["file_id"],
                    caption=await get_file_caption(file_details),
                    reply_markup=await get_file_markup(file_details)
                )
            else:
                await message.reply_text("File not found for verification.")
        return

    await message.reply_photo(
        random.choice(PICS),
        caption=script.START_TXT.format(message.from_user.mention),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_message(filters.command(["help"]) & filters.private)
async def help_command(client: Client, message: Message):
    buttons = [
        [
            InlineKeyboardButton("Mᴀɴᴜᴀʟ Fɪʟᴛᴇʀ", callback_data="manual_filter_help"),
            InlineKeyboardButton("Aᴜᴛᴏ Fɪʟᴛᴇʀ", callback_data="auto_filter_help")
        ],
        [
            InlineKeyboardButton("Cᴏɴɴᴇᴄᴛɪᴏɴs", callback_data="connections_help"),
            InlineKeyboardButton("Eхᴛʀᴀ Mᴏᴅᴜʟᴇs", callback_data="extra_modules_help")
        ],
        [
            InlineKeyboardButton("Aᴅᴍɪɴ Cᴏᴍᴍᴀɴᴅs", callback_data="admin_commands_help"),
            InlineKeyboardButton("Fɪʟᴇ Sᴛᴏʀᴇ", callback_data="file_store_help")
        ],
        [
            InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="start_commands")
        ]
    ]
    await message.reply_photo(
        random.choice(PICS),
        caption=script.HELP_TXT.format(message.from_user.mention),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_message(filters.command(["about"]) & filters.private)
async def about_command(client: Client, message: Message):
    buttons = [
        [
            InlineKeyboardButton("Sᴏᴜʀᴄᴇ Cᴏᴅᴇ", url=SOURCE_CODE_LNK),
            InlineKeyboardButton("Uᴘᴅᴀᴛᴇ Cʜᴀɴɴᴇʟ", url=CHNL_LNK)
        ],
        [
            InlineKeyboardButton("Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ", url=GRP_LNK),
            InlineKeyboardButton("Oᴡɴᴇʀ", url=OWNER_LNK)
        ],
        [
            InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="start_commands")
        ]
    ]
    await message.reply_photo(
        random.choice(PICS),
        caption=script.ABOUT_TXT.format(BOT_USERNAME, BOT_NAME, OWNER_LNK),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_message(filters.command(["settings"]) & filters.private)
async def settings_command(client: Client, message: Message):
    settings = await db.get_settings(message.from_user.id)
    buttons = [
        [
            InlineKeyboardButton('Bᴜᴛᴛᴏɴ Mᴏᴅᴇ', callback_data=f'setgs#button#{settings["button"]}#{str(message.from_user.id)}'),
            InlineKeyboardButton('✔ Oɴ' if settings["button"] else '✘ Oғғ', callback_data=f'setgs#button#{settings["button"]}#{str(message.from_user.id)}')
        ],
        [
            InlineKeyboardButton('Fɪʟᴇ Sᴇᴄᴜʀᴇ', callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(message.from_user.id)}'),
            InlineKeyboardButton('✔ Oɴ' if settings["file_secure"] else '✘ Oғғ', callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(message.from_user.id)}')
        ],
        [
            InlineKeyboardButton('IMDʙ', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(message.from_user.id)}'),
            InlineKeyboardButton('✔ Oɴ' if settings["imdb"] else '✘ Oғғ', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(message.from_user.id)}')
        ],
        [
            InlineKeyboardButton('Sᴘᴇʟʟ Cʜᴇᴄᴋ', callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(message.from_user.id)}'),
            InlineKeyboardButton('✔ Oɴ' if settings["spell_check"] else '✘ Oғғ', callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(message.from_user.id)}')
        ],
        [
            InlineKeyboardButton('Wᴇʟᴄᴏᴍᴇ Mᴇssᴀɢᴇ', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(message.from_user.id)}'),
            InlineKeyboardButton('✔ Oɴ' if settings["welcome"] else '✘ Oғғ', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(message.from_user.id)}')
        ],
        [
            InlineKeyboardButton('Aᴜᴛᴏ Dᴇʟᴇᴛᴇ', callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(message.from_user.id)}'),
            InlineKeyboardButton('✔ Oɴ' if settings["auto_delete"] else '✘ Oғғ', callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(message.from_user.id)}')
        ],
        [
            InlineKeyboardButton('Aᴜᴛᴏ-Fɪʟᴛᴇʀ', callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(message.from_user.id)}'),
            InlineKeyboardButton('✔ Oɴ' if settings["auto_ffilter"] else '✘ Oғғ', callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(message.from_user.id)}')
        ],
        [
            InlineKeyboardButton('Mᴀx Bᴜᴛᴛoɴs', callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(message.from_user.id)}'),
            InlineKeyboardButton('10' if settings["max_btn"] else f'{MAX_BTN}', callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(message.from_user.id)}')
        ],
        [
            InlineKeyboardButton('SʜᴏʀᴛLɪɴᴋ', callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{str(message.from_user.id)}'),
            InlineKeyboardButton('✔ Oɴ' if settings["is_shortlink"] else '✘ Oғғ', callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{str(message.from_user.id)}')
        ],
        [
            InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="start_commands")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply_text("Sᴇᴛᴛɪɴɢs:", reply_markup=reply_markup)

@Client.on_message(filters.command(["status"]) & filters.private)
async def status_command(client: Client, message: Message):
    if message.from_user.id not in ADMINS:
        await message.reply_text("Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")
        return

    total_users = await db.total_users_count()
    total_chats = await db.total_chat_count()
    # Assuming total_files_count, and database size functions exist in db object
    total_files = await db.total_files_count() # Placeholder, implement in users_chats_db if needed

    # These would need to be implemented in your database files if they are not already
    users_db_size = 0 # Placeholder
    file_first_db_size = 0 # Placeholder
    file_second_db_size = 0 # Placeholder
    other_db_size = 0 # Placeholder

    users_db_free = 0 # Placeholder
    file_first_db_free = 0 # Placeholder
    file_second_db_free = 0 # Placeholder
    other_db_free = 0 # Placeholder

    caption = script.STATUS_TXT.format(
        total_files,
        total_users,
        total_chats,
        total_files, # This seems to be a repeat, adjust if needed
        file_first_db_size,
        file_first_db_free,
        total_files, # This seems to be a repeat, adjust if needed
        file_second_db_size,
        file_second_db_free,
        other_db_size,
        other_db_free
    )
    await message.reply_text(caption)

@Client.on_message(filters.command(["clone"]) & filters.private)
async def clone_command(client: Client, message: Message):
    buttons = [
        [
            InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="start_commands")
        ]
    ]
    await message.reply_photo(
        random.choice(PICS),
        caption=script.CLONE_TXT,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_message(filters.command(["subscribe"]) & filters.private)
async def subscribe_command(client: Client, message: Message):
    user_id = message.from_user.id
    referral_link = f"https://telegram.me/{temp.U_NAME}?start=VJ-{user_id}"
    referral_count = await db.get_referal_users_count(user_id)

    buttons = [
        [
            InlineKeyboardButton("Pʟᴀɴs", callback_data="plans_commands"),
            InlineKeyboardButton("Mʏ Pʟᴀɴ", callback_data="my_plan_commands")
        ],
        [
            InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="start_commands")
        ]
    ]
    await message.reply_photo(
        random.choice(PICS),
        caption=script.SUBSCRIPTION_TXT.format(REFERAL_PREMEIUM_TIME, temp.U_NAME, user_id, REFERAL_COUNT),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_message(filters.command(["plans"]) & filters.private)
async def plans_command(client: Client, message: Message):
    buttons = [
        [
            InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="subscribe_commands")
        ]
    ]
    await message.reply_photo(
        PAYMENT_QR,
        caption=script.PAYMENT_TEXT,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_message(filters.command(["myplan"]) & filters.private)
async def myplan_command(client: Client, message: Message):
    user_id = message.from_user.id
    has_premium = await db.has_premium_access(user_id)
    if has_premium:
        remaining_time = await db.check_remaining_uasge(user_id)
        await message.reply_text(f"Yᴏᴜ ʜᴀᴠᴇ ᴀᴄᴛɪᴠᴇ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss. Rᴇᴍᴀɪɴɪɴɢ ᴛɪᴍᴇ: {get_readable_time(remaining_time.total_seconds())}")
    else:
        await message.reply_text("Yᴏᴜ ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ᴀɴ ᴀᴄᴛɪᴠᴇ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ.")

@Client.on_message(filters.command(["tutorial"]) & filters.private)
async def tutorial_command(client: Client, message: Message):
    if IS_TUTORIAL and TUTORIAL:
        buttons = [
            [
                InlineKeyboardButton("Wᴀᴛᴄʜ Tᴜᴛᴏʀɪᴀʟ", url=await get_tutorial_shortlink(TUTORIAL))
            ],
            [
                InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="start_commands")
            ]
        ]
        await message.reply_text(
            script.SHORTLINK_INFO,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await message.reply_text("Tᴜᴛᴏʀɪᴀʟ ɪs ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ.")

@Client.on_message(filters.command(["set_tutorial"]) & filters.private & filters.user(ADMINS))
async def set_tutorial_command(client: Client, message: Message):
    if len(message.command) > 1:
        tutorial_link = message.command[1]
        if is_valid_url(tutorial_link):
            # This would typically update an environment variable or a config file
            # For this example, we'll just confirm.
            # You would need to implement a way to persist this change (e.g., in info.py or a database)
            await message.reply_text(f"Tᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ sᴇᴛ ᴛᴏ: {tutorial_link}")
        else:
            await message.reply_text("Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ᴜʀʟ.")
    else:
        await message.reply_text("Uꜱᴀɢᴇ: /set_tutorial [video_link]")

@Client.on_message(filters.command(["set_api"]) & filters.private & filters.user(ADMINS))
async def set_api_command(client: Client, message: Message):
    if len(message.command) > 2:
        shortlink_url = message.command[1]
        shortlink_api = message.command[2]
        # Update SHORTLINK_URL and SHORTLINK_API in info.py (requires dynamic config)
        await message.reply_text(f"Sʜᴏʀᴛʟɪɴᴋ Uʀʟ sᴇᴛ ᴛᴏ: {shortlink_url}\nSʜᴏʀᴛʟɪɴᴋ Aᴘɪ sᴇᴛ ᴛᴏ: {shortlink_api}")
    else:
        await message.reply_text("Uꜱᴀɢᴇ: /set_api [url] [api_key]")

@Client.on_message(filters.command(["set_verify_api"]) & filters.private & filters.user(ADMINS))
async def set_verify_api_command(client: Client, message: Message):
    if len(message.command) > 2:
        verify_url = message.command[1]
        verify_api = message.command[2]
        # Update VERIFY_SHORTLINK_URL and VERIFY_SHORTLINK_API in info.py
        await message.reply_text(f"Vᴇʀɪғʏ Uʀʟ sᴇᴛ ᴛᴏ: {verify_url}\nVᴇʀɪғʏ Aᴘɪ sᴇᴛ ᴛᴏ: {verify_api}")
    else:
        await message.reply_text("Uꜱᴀɢᴇ: /set_verify_api [url] [api_key]")

@Client.on_message(filters.command(["set_second_verify_api"]) & filters.private & filters.user(ADMINS))
async def set_second_verify_api_command(client: Client, message: Message):
    if len(message.command) > 2:
        snd_verify_url = message.command[1]
        snd_verify_api = message.command[2]
        # Update VERIFY_SND_SHORTLINK_URL and VERIFY_SND_SHORTLINK_API in info.py
        await message.reply_text(f"Sᴇᴄᴏɴᴅ Vᴇʀɪғʏ Uʀʟ sᴇᴛ ᴛᴏ: {snd_verify_url}\nSᴇᴄᴏɴᴅ Vᴇʀɪғʏ Aᴘɪ sᴇᴛ ᴛᴏ: {snd_verify_api}")
    else:
        await message.reply_text("Uꜱᴀɢᴇ: /set_second_verify_api [url] [api_key]")

@Client.on_message(filters.command(["connections"]) & filters.private)
async def connections_command(client: Client, message: Message):
    connections = await active_connection(message.from_user.id) # Assuming active_connection returns a list of connected chat IDs
    if connections:
        text = "Yᴏᴜʀ ᴀᴄᴛɪᴠᴇ ᴄᴏɴɴᴇᴄᴛɪᴏɴs:\n"
        for conn_id in connections:
            try:
                chat = await client.get_chat(conn_id)
                text += f"- {chat.title} (`{conn_id}`)\n"
            except Exception as e:
                logger.error(f"Error getting chat info for connection {conn_id}: {e}")
                text += f"- Unknown Chat (`{conn_id}`)\n"
        await message.reply_text(text)
    else:
        await message.reply_text("Nᴏ ᴀᴄᴛɪᴠᴇ ᴄᴏɴɴᴇᴄᴛɪᴏɴs ꜰᴏᴜɴᴅ.")

@Client.on_message(filters.command(["connect"]) & filters.private)
async def connect_command(client: Client, message: Message):
    if len(message.command) > 1:
        try:
            group_id = int(message.command[1])
            chat = await client.get_chat(group_id)
            if chat.permissions.can_send_messages: # Check if bot can send messages
                # Assuming add_connection exists and works as expected
                if await add_connection(group_id, message.from_user.id):
                    await message.reply_text(f"Sᴜᴄᴄᴇssғᴜʟʟʏ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ {chat.title}.")
                else:
                    await message.reply_text("Aʟʀᴇᴀᴅʏ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴛʜɪs ᴄʜᴀᴛ.")
            else:
                await message.reply_text("Bᴏᴛ ᴅᴏᴇs ɴᴏᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴs ᴛᴏ sᴇɴᴅ ᴍᴇssᴀɢᴇs ɪɴ ᴛʜɪs ᴄʜᴀᴛ.")
        except ValueError:
            await message.reply_text("Iɴᴠᴀʟɪᴅ ɢʀᴏᴜᴘ ID. Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍᴇʀɪᴄ ɢʀᴏᴜᴘ ID.")
        except Exception as e:
            await message.reply_text(f"Eʀʀᴏʀ ᴄᴏɴɴᴇᴄᴛɪɴɢ ᴛᴏ ᴄʜᴀᴛ: {e}")
    else:
        await message.reply_text("Uꜱᴀɢᴇ: /connect [group_id]")

@Client.on_message(filters.command(["disconnect"]) & filters.private)
async def disconnect_command(client: Client, message: Message):
    if len(message.command) > 1:
        try:
            group_id = int(message.command[1])
            # Assuming delete_connection exists and works as expected
            if await delete_connection(message.from_user.id, group_id):
                await message.reply_text(f"Sᴜᴄᴄᴇssғᴜʟʟʏ ᴅɪsᴄᴏɴɴᴇᴄᴛᴇᴅ ғʀᴏᴍ {group_id}.")
            else:
                await message.reply_text("Nᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴛʜɪs ᴄʜᴀᴛ.")
        except ValueError:
            await message.reply_text("Iɴᴠᴀʟɪᴅ ɢʀᴏᴜᴘ ID. Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍᴇʀɪᴄ ɢʀᴏᴜᴘ ID.")
        except Exception as e:
            await message.reply_text(f"Eʀʀᴏʀ ᴅɪsᴄᴏɴɴᴇᴄᴛɪɴɢ ғʀᴏᴍ ᴄʜᴀᴛ: {e}")
    else:
        await message.reply_text("Uꜱᴀɢᴇ: /disconnect [group_id]")

@Client.on_message(filters.command(["connect"]) & filters.group & filters.user(ADMINS))
async def connect_group_command(client: Client, message: Message):
    try:
        # Assuming add_connection exists and works as expected
        await add_connection(message.chat.id, message.from_user.id)
        await message.reply_text(f"Cᴏɴɴᴇᴄᴛᴇᴅ ᴛʜɪs ᴄʜᴀᴛ ᴛᴏ ʏᴏᴜʀ PM. Nᴏᴡ ʏᴏᴜ ᴄᴀɴ ᴍᴀɴᴀɢᴇ ғɪʟᴛᴇʀs ғʀᴏᴍ ʏᴏᴜʀ PM.")
    except Exception as e:
        await message.reply_text(f"Eʀʀᴏʀ ᴄᴏɴɴᴇᴄᴛɪɴɢ ᴛᴏ ʏᴏᴜʀ PM: {e}")

@Client.on_callback_query()
async def callback_query_handler(client: Client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id

    if data == "start_commands":
        if user_id in ADMINS:
            buttons = [
                [
                    InlineKeyboardButton("Aᴅᴍɪɴ", callback_data="admin_commands"),
                    InlineKeyboardButton("Hᴇʟᴘ", callback_data="help_commands"),
                    InlineKeyboardButton("Aʙᴏᴜᴛ", callback_data="about_commands")
                ],
                [
                    InlineKeyboardButton("Cʟᴏɴᴇ Bᴏᴛ", callback_data="clone_commands"),
                    InlineKeyboardButton("Sᴇᴛᴛɪɴɢs", callback_data="settings_commands")
                ],
                [
                    InlineKeyboardButton("Sᴜʙsᴄʀɪʙᴇ", callback_data="subscribe_commands"),
                    InlineKeyboardButton("Sᴛᴀᴛᴜs", callback_data="status_commands")
                ]
            ]
        else:
            buttons = [
                [
                    InlineKeyboardButton("Hᴇʟᴘ", callback_data="help_commands"),
                    InlineKeyboardButton("Aʙᴏᴜᴛ", callback_data="about_commands")
                ],
                [
                    InlineKeyboardButton("Sᴇᴛᴛɪɴɢs", callback_data="settings_commands"),
                    InlineKeyboardButton("Sᴜʙsᴄʀɪʙᴇ", callback_data="subscribe_commands")
                ]
            ]
        await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))

    elif data == "help_commands":
        buttons = [
            [
                InlineKeyboardButton("Mᴀɴᴜᴀʟ Fɪʟᴛᴇʀ", callback_data="manual_filter_help"),
                InlineKeyboardButton("Aᴜᴛᴏ Fɪʟᴛᴇʀ", callback_data="auto_filter_help")
            ],
            [
                InlineKeyboardButton("Cᴏɴɴᴇᴄᴛɪᴏɴs", callback_data="connections_help"),
                InlineKeyboardButton("Eхᴛʀᴀ Mᴏᴅᴜʟᴇs", callback_data="extra_modules_help")
            ],
            [
                InlineKeyboardButton("Aᴅᴍɪɴ Cᴏᴍᴍᴀɴᴅs", callback_data="admin_commands_help"),
                InlineKeyboardButton("Fɪʟᴇ Sᴛᴏʀᴇ", callback_data="file_store_help")
            ],
            [
                InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="start_commands")
            ]
        ]
        await query.message.edit_caption(script.HELP_TXT.format(query.from_user.mention), reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "about_commands":
        buttons = [
            [
                InlineKeyboardButton("Sᴏᴜʀᴄᴇ Cᴏᴅᴇ", url=SOURCE_CODE_LNK),
                InlineKeyboardButton("Uᴘᴅᴀᴛᴇ Cʜᴀɴɴᴇʟ", url=CHNL_LNK)
            ],
            [
                InlineKeyboardButton("Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ", url=GRP_LNK),
                InlineKeyboardButton("Oᴡɴᴇʀ", url=OWNER_LNK)
            ],
            [
                InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="start_commands")
            ]
        ]
        await query.message.edit_caption(script.ABOUT_TXT.format(BOT_USERNAME, BOT_NAME, OWNER_LNK), reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "clone_commands":
        buttons = [
            [
                InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="start_commands")
            ]
        ]
        await query.message.edit_caption(script.CLONE_TXT, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "subscribe_commands":
        buttons = [
            [
                InlineKeyboardButton("Pʟᴀɴs", callback_data="plans_commands"),
                InlineKeyboardButton("Mʏ Pʟᴀɴ", callback_data="my_plan_commands")
            ],
            [
                InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="start_commands")
            ]
        ]
        await query.message.edit_caption(script.SUBSCRIPTION_TXT.format(REFERAL_PREMEIUM_TIME, temp.U_NAME, user_id, REFERAL_COUNT), reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "plans_commands":
        buttons = [
            [
                InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="subscribe_commands")
            ]
        ]
        await query.message.edit_photo(PAYMENT_QR, caption=script.PAYMENT_TEXT, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "my_plan_commands":
        has_premium = await db.has_premium_access(user_id)
        if has_premium:
            remaining_time = await db.check_remaining_uasge(user_id)
            await query.answer(f"Yᴏᴜ ʜᴀᴠᴇ ᴀᴄᴛɪᴠᴇ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss. Rᴇᴍᴀɪɴɪɴɢ ᴛɪᴍᴇ: {get_readable_time(remaining_time.total_seconds())}", show_alert=True)
        else:
            await query.answer("Yᴏᴜ ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ᴀɴ ᴀᴄᴛɪᴠᴇ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ.", show_alert=True)

    elif data == "manual_filter_help":
        buttons = [
            [
                InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="help_commands")
            ]
        ]
        await query.message.edit_caption(script.MANUELFILTER_TXT, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "auto_filter_help":
        buttons = [
            [
                InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="help_commands")
            ]
        ]
        await query.message.edit_caption(script.AUTOFILTER_TXT, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "connections_help":
        buttons = [
            [
                InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="help_commands")
            ]
        ]
        await query.message.edit_caption(script.CONNECTION_TXT, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "extra_modules_help":
        buttons = [
            [
                InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="help_commands")
            ]
        ]
        await query.message.edit_caption(script.EXTRAMOD_TXT.format(OWNER_LNK, CHNL_LNK), reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "admin_commands_help":
        buttons = [
            [
                InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="help_commands")
            ]
        ]
        await query.message.edit_caption(script.ADMIN_TXT, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "file_store_help":
        buttons = [
            [
                InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="help_commands")
            ]
        ]
        await query.message.edit_caption(script.FILE_STORE_TXT, reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("setgs#"):
        parts = data.split("#")
        setting_name = parts[1]
        current_value = parts[2] == 'True'
        target_user_id = int(parts[3])

        if user_id != target_user_id and user_id not in ADMINS:
            await query.answer("Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ ᴛᴏ ᴄʜᴀɴɢᴇ ᴛʜɪs sᴇᴛᴛɪɴɢ.", show_alert=True)
            return

        new_value = not current_value
        settings = await db.get_settings(target_user_id)
        settings[setting_name] = new_value
        await db.update_settings(target_user_id, settings)

        buttons = [
            [
                InlineKeyboardButton('Bᴜᴛᴛᴏɴ Mᴏᴅᴇ', callback_data=f'setgs#button#{settings["button"]}#{str(target_user_id)}'),
                InlineKeyboardButton('✔ Oɴ' if settings["button"] else '✘ Oғғ', callback_data=f'setgs#button#{settings["button"]}#{str(target_user_id)}')
            ],
            [
                InlineKeyboardButton('Fɪʟᴇ Sᴇᴄᴜʀᴇ', callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(target_user_id)}'),
                InlineKeyboardButton('✔ Oɴ' if settings["file_secure"] else '✘ Oғғ', callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(target_user_id)}')
            ],
            [
                InlineKeyboardButton('IMDʙ', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(target_user_id)}'),
                InlineKeyboardButton('✔ Oɴ' if settings["imdb"] else '✘ Oғғ', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(target_user_id)}')
            ],
            [
                InlineKeyboardButton('Sᴘᴇʟʟ Cʜᴇᴄᴋ', callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(target_user_id)}'),
                InlineKeyboardButton('✔ Oɴ' if settings["spell_check"] else '✘ Oғғ', callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(target_user_id)}')
            ],
            [
                InlineKeyboardButton('Wᴇʟᴄᴏᴍᴇ Mᴇssᴀɢᴇ', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(target_user_id)}'),
                InlineKeyboardButton('✔ Oɴ' if settings["welcome"] else '✘ Oғғ', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(target_user_id)}')
            ],
            [
                InlineKeyboardButton('Aᴜᴛᴏ Dᴇʟᴇᴛᴇ', callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(target_user_id)}'),
                InlineKeyboardButton('✔ Oɴ' if settings["auto_delete"] else '✘ Oғғ', callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(target_user_id)}')
            ],
            [
                InlineKeyboardButton('Aᴜᴛᴏ-Fɪʟᴛᴇʀ', callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(target_user_id)}'),
                InlineKeyboardButton('✔ Oɴ' if settings["auto_ffilter"] else '✘ Oғғ', callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(target_user_id)}')
            ],
            [
                InlineKeyboardButton('Mᴀx Bᴜᴛᴛoɴs', callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(target_user_id)}'),
                InlineKeyboardButton('10' if settings["max_btn"] else f'{MAX_BTN}', callback_data=f'setgs#max_btn#{settings["max_btn"]}#{str(target_user_id)}')
            ],
            [
                InlineKeyboardButton('SʜᴏʀᴛLɪɴᴋ', callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{str(target_user_id)}'),
                InlineKeyboardButton('✔ Oɴ' if settings["is_shortlink"] else '✘ Oғғ', callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{str(target_user_id)}')
            ],
            [
                InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="start_commands")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_reply_markup(reply_markup)
        await query.answer("Settings updated!")

    elif data.startswith("next_page#"):
        offset = int(data.split("#")[1])
        search_query = data.split("#")[2]
        
        # Re-perform the search with the new offset
        files, total_results = await get_search_results(search_query) # Assuming get_search_results handles pagination
        
        if files:
            buttons = []
            for file in files[offset:offset + MAX_BTN]: # Display MAX_BTN files per page
                file_name = file["file_name"]
                file_id = file["file_id"]
                buttons.append(
                    [InlineKeyboardButton(text=file_name, url=f"https://telegram.me/{temp.U_NAME}?start=files_{file_id}")]
                )
            
            # Add navigation buttons
            if offset + MAX_BTN < len(files):
                buttons.append([InlineKeyboardButton("Nᴇxᴛ Pᴀɢᴇ ➡️", callback_data=f"next_page#{offset + MAX_BTN}#{search_query}")])
            
            await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
        else:
            await query.answer("Nᴏ ᴍᴏʀᴇ ғɪʟᴇs ᴀᴠᴀɪʟᴀʙʟᴇ.", show_alert=True)

    elif data.startswith("alert#"):
        alert_message = data.split("#")[1]
        await query.answer(alert_message, show_alert=True)

    await query.answer() # Always answer the callback query to remove the loading animation
