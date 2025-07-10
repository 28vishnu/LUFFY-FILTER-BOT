# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re
from pymongo.errors import DuplicateKeyError
import motor.motor_asyncio
from pymongo import MongoClient
from info import DATABASE_NAME, USER_DB_URI, OTHER_DB_URI, CUSTOM_FILE_CAPTION, IMDB, IMDB_TEMPLATE, MELCOW_NEW_USERS, BUTTON_MODE, SPELL_CHECK_REPLY, PROTECT_CONTENT, AUTO_DELETE, MAX_BTN, AUTO_FFILTER, SHORTLINK_API, SHORTLINK_URL, SHORTLINK_MODE, TUTORIAL, IS_TUTORIAL
import time
import datetime

my_client = MongoClient(OTHER_DB_URI)
mydb = my_client["referal_user"]

async def referal_add_user(user_id, ref_user_id):
    user_db = mydb[str(user_id)]
    user = {'_id': ref_user_id}
    try:
        user_db.insert_one(user)
        return True
    except DuplicateKeyError:
        return False
    

async def get_referal_all_users(user_id):
    user_db = mydb[str(user_id)]
    return user_db.find()
    
async def get_referal_users_count(user_id):
    user_db = mydb[str(user_id)]
    count = user_db.count_documents({})
    return count
    

async def delete_all_referal_users(user_id):
    user_db = mydb[str(user_id)]
    user_db.drop()


class UsersChatsDb(object):
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.users = self.db.users
        self.chats = self.db.chats
        self.premium_users = self.db.premium_users # New collection for premium users
        self.banned_users = self.db.banned_users # New collection for banned users

    async def add_user(self, id, name):
        user = {"id": id, "name": name, "join_date": datetime.datetime.now()}
        try:
            await self.users.insert_one(user)
        except DuplicateKeyError:
            pass

    async def is_user_exist(self, id):
        user = await self.users.find_one({"id": id})
        return True if user else False

    async def total_users_count(self):
        count = await self.users.count_documents({})
        return count

    async def get_all_users(self):
        all_users = self.users.find({})
        return all_users

    async def delete_user(self, user_id):
        await self.users.delete_many({"id": user_id})

    async def add_chat(self, id, title):
        chat = {"id": id, "title": title, "join_date": datetime.datetime.now()}
        try:
            await self.chats.insert_one(chat)
        except DuplicateKeyError:
            pass

    async def is_chat_exist(self, id):
        chat = await self.chats.find_one({"id": id})
        return True if chat else False

    async def total_chat_count(self):
        count = await self.chats.count_documents({})
        return count

    async def get_all_chats(self):
        all_chats = self.chats.find({})
        return all_chats

    async def delete_chat(self, chat_id):
        await self.chats.delete_many({"id": chat_id})
    
    async def get_chat(self, chat_id):
        chat = await self.chats.find_one({"id": chat_id})
        return chat

    async def update_chat_settings(self, chat_id, settings):
        await self.chats.update_one({"id": chat_id}, {"$set": settings}, upsert=True)

    async def get_settings(self, id):
        # Default settings for a user or chat
        default_settings = {
            "button": BUTTON_MODE,
            "file_secure": PROTECT_CONTENT,
            "imdb": IMDB,
            "spell_check": SPELL_CHECK_REPLY,
            "welcome": MELCOW_NEW_USERS,
            "auto_delete": AUTO_DELETE,
            "max_btn": MAX_BTN,
            "auto_ffilter": AUTO_FFILTER,
            "is_shortlink": SHORTLINK_MODE,
            "tutorial": IS_TUTORIAL,
            "is_verified": False, # For user verification status
            "token": None, # For user verification token
            "last_verified_time": None # For user verification timestamp
        }
        
        # Check if settings exist for the given ID
        settings = await self.users.find_one({"id": id}, {"settings": 1})
        if settings and "settings" in settings:
            # Merge existing settings with defaults to ensure all keys are present
            merged_settings = {**default_settings, **settings["settings"]}
            return merged_settings
        
        # If no settings exist, return default settings
        return default_settings

    async def update_settings(self, id, settings):
        await self.users.update_one({"id": id}, {"$set": {"settings": settings}}, upsert=True)

    # Premium User Management
    async def add_premium_user(self, user_id, expiry_time):
        user_data = {"id": user_id, "expiry_time": expiry_time, "has_free_trial": False}
        await self.premium_users.update_one({"id": user_id}, {"$set": user_data}, upsert=True)

    async def has_premium_access(self, user_id):
        user = await self.premium_users.find_one({"id": user_id})
        if user and user["expiry_time"] > datetime.datetime.now():
            return True
        # Check for free trial if premium expired or not present
        user_settings = await self.get_settings(user_id)
        if user_settings.get("has_free_trial") and user_settings.get("expiry_time") > datetime.datetime.now():
            return True
        return False

    async def check_remaining_uasge(self, user_id):
        user = await self.premium_users.find_one({"id": user_id})
        if user and user["expiry_time"] > datetime.datetime.now():
            return user["expiry_time"] - datetime.datetime.now()
        
        user_settings = await self.get_settings(user_id)
        if user_settings.get("has_free_trial") and user_settings.get("expiry_time") > datetime.datetime.now():
            return user_settings["expiry_time"] - datetime.datetime.now()
        return datetime.timedelta(seconds=0)

    async def add_free_trial_user(self, user_id, seconds):
        expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        user_data = {"id": user_id, "expiry_time": expiry_time, "has_free_trial": True}
        await self.users.update_one({"id": user_id}, {"$set": user_data}, upsert=True)
    
    
    async def all_premium_users(self):
        count = await self.users.count_documents({
        "expiry_time": {"$gt": datetime.datetime.now()}
        })
        return count

    async def set_thumbnail(self, id, file_id):
        await self.col.update_one({'id': int(id)}, {'$set': {'file_id': file_id}})

    async def get_thumbnail(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('file_id', None)

    async def set_caption(self, id, caption):
        await self.col.update_one({'id': int(id)}, {'$set': {'caption': caption}})

    async def get_caption(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('caption', None)

    async def set_msg_command(self, id, com):
        await self.col.update_one({'id': int(id)}, {'$set': {'message_command': com}})

    async def get_msg_command(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('message_command', None)

    # Ban Management
    async def add_ban_status(self, user_id, reason="No reason provided"):
        ban_data = {"id": user_id, "is_banned": True, "reason": reason, "ban_time": datetime.datetime.now()}
        await self.banned_users.update_one({"id": user_id}, {"$set": ban_data}, upsert=True)

    async def remove_ban_status(self, user_id):
        await self.banned_users.delete_one({"id": user_id})

    async def get_ban_status(self, user_id):
        user = await self.banned_users.find_one({"id": user_id})
        return user if user else {"is_banned": False, "reason": None}

db = UsersChatsDb(USER_DB_URI, DATABASE_NAME)
