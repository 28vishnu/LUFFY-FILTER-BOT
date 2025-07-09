# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re, base64, json
from struct import pack
from pyrogram.file_id import FileId, FileType
from motor.motor_asyncio import AsyncIOMotorClient # Import AsyncIOMotorClient
from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError, OperationFailure
from bson.objectid import ObjectId # Import ObjectId for querying by _id
import asyncio
import logging

from info import FILE_DB_URI, SEC_FILE_DB_URI, DATABASE_NAME, COLLECTION_NAME, MULTIPLE_DATABASE, USE_CAPTION_FILTER, MAX_BTN

logger = logging.getLogger(__name__)

# First Database For File Saving 
# Use AsyncIOMotorClient for asynchronous operations
client = AsyncIOMotorClient(FILE_DB_URI)
db = client[DATABASE_NAME]
col = db[COLLECTION_NAME]

# Second Database For File Saving (if enabled)
sec_client = None
sec_db = None
sec_col = None
if MULTIPLE_DATABASE:
    sec_client = AsyncIOMotorClient(SEC_FILE_DB_URI)
    sec_db = sec_client[DATABASE_NAME]
    sec_col = sec_db[COLLECTION_NAME]


async def ensure_indexes():
    """Ensures necessary indexes are created on the collections."""
    try:
        # Create text index for file_name for search functionality
        await col.create_index([("file_name", "text")], name="file_name_text_index", background=True)
        logger.info("Text index 'file_name_text_index' created on primary collection.")
    except OperationFailure as e:
        logger.warning(f"Failed to create text index on primary collection: {e}")
    except Exception as e:
        logger.error(f"Unexpected error creating text index on primary collection: {e}")

    try:
        # Create unique index on file_id to prevent duplicates
        # Use background=True to build in the background without blocking
        # Use sparse=True so that documents without 'file_id' field are not indexed
        await col.create_index([("file_id", ASCENDING)], unique=True, background=True, sparse=True)
        logger.info("Unique index 'file_id_1' created on primary collection.")
    except OperationFailure as e:
        # This will catch if the index already exists or if there are duplicates preventing creation
        logger.warning(f"Failed to create unique index on primary collection 'file_id_1': {e}. "
                       "This might mean duplicates exist or index already present.")
    except Exception as e:
        logger.error(f"Unexpected error creating unique index on primary collection: {e}")

    if MULTIPLE_DATABASE and sec_col:
        try:
            await sec_col.create_index([("file_name", "text")], name="sec_file_name_text_index", background=True)
            logger.info("Text index 'sec_file_name_text_index' created on secondary collection.")
        except OperationFailure as e:
            logger.warning(f"Failed to create text index on secondary collection: {e}")
        except Exception as e:
            logger.error(f"Unexpected error creating text index on secondary collection: {e}")

        try:
            await sec_col.create_index([("file_id", ASCENDING)], unique=True, background=True, sparse=True)
            logger.info("Unique index 'file_id_1' created on secondary collection.")
        except OperationFailure as e:
            logger.warning(f"Failed to create unique index on secondary collection 'file_id_1': {e}. "
                           "This might mean duplicates exist or index already present.")
        except Exception as e:
            logger.error(f"Unexpected error creating unique index on secondary collection: {e}")


async def remove_duplicate_files():
    """Removes duplicate files based on 'file_id' from the primary collection."""
    logger.info("Starting duplicate file cleanup on primary collection...")
    pipeline = [
        {"$group": {
            "_id": "$file_id",
            "dups": {"$addToSet": "$_id"},
            "count": {"$sum": 1}
        }},
        {"$match": {"count": {"$gt": 1}}}
    ]

    duplicates = []
    try:
        # Use .to_list(length=None) to fetch all results from the async cursor
        duplicates = await col.aggregate(pipeline).to_list(length=None)
    except Exception as e:
        logger.error(f"Error during aggregation to find duplicates: {e}")
        return

    deleted_count = 0
    for doc in duplicates:
        file_id = doc["_id"]
        # Keep the first occurrence, delete the rest
        ids_to_delete = doc["dups"][1:]
        
        if ids_to_delete:
            try:
                result = await col.delete_many({"_id": {"$in": ids_to_delete}})
                deleted_count += result.deleted_count
                logger.info(f"Removed {result.deleted_count} duplicates for file_id: {file_id}")
            except Exception as e:
                logger.error(f"Error deleting duplicates for file_id {file_id}: {e}")
    
    logger.info(f"Finished duplicate file cleanup on primary collection. Total duplicates removed: {deleted_count}")

    if MULTIPLE_DATABASE and sec_col:
        logger.info("Starting duplicate file cleanup on secondary collection...")
        duplicates_sec = []
        try:
            duplicates_sec = await sec_col.aggregate(pipeline).to_list(length=None)
        except Exception as e:
            logger.error(f"Error during aggregation to find duplicates in secondary collection: {e}")
            return

        deleted_count_sec = 0
        for doc in duplicates_sec:
            file_id = doc["_id"]
            ids_to_delete = doc["dups"][1:]
            if ids_to_delete:
                try:
                    result = await sec_col.delete_many({"_id": {"$in": ids_to_delete}})
                    deleted_count_sec += result.deleted_count
                    logger.info(f"Removed {result.deleted_count} duplicates from secondary for file_id: {file_id}")
                except Exception as e:
                    logger.error(f"Error deleting duplicates from secondary for file_id {file_id}: {e}")
        logger.info(f"Finished duplicate file cleanup on secondary collection. Total duplicates removed: {deleted_count_sec}")


def clean_file_name(name: str) -> str:
    """Cleans a file name for better searchability."""
    # Remove common file extensions, years in parentheses, etc.
    name = re.sub(r'\.\w+$', '', name) # Remove extension
    name = re.sub(r'\(\d{4}\)', '', name) # Remove (YYYY)
    name = re.sub(r'\[.*?\]', '', name) # Remove [text in brackets]
    name = re.sub(r'\{.*?\}', '', name) # Remove {text in braces}
    name = re.sub(r'\s+', ' ', name).strip() # Replace multiple spaces with single
    return name.lower() # Convert to lowercase for consistent search


async def save_file(media) -> (bool, str):
    """Save file in the database. Returns (success, file_id_or_error_message)."""
    
    # Ensure media object has file_id attribute
    if not hasattr(media, 'file_id') or not media.file_id:
        return False, "Media object has no file_id."

    # Extract Pyrogram's FileId object for detailed info
    file_id_obj = media.file_id
    
    # Get the actual Telegram file_id string
    file_id = file_id_obj.file_id
    
    # Get file_ref bytes and convert to hex string for storage
    file_ref = file_id_obj.file_ref.hex() if file_id_obj.file_ref else None

    file_name = media.file_name or "Untitled"
    file_size = media.file_size
    caption = media.caption.html if media.caption else None
    
    # Determine file type
    file_type = None
    if media.document:
        file_type = 'document'
    elif media.video:
        file_type = 'video'
    elif media.photo:
        file_type = 'photo'
    elif media.audio:
        file_type = 'audio'
    elif media.sticker:
        file_type = 'sticker'
    elif media.animation:
        file_type = 'animation'
    elif media.voice:
        file_type = 'voice'
    elif media.contact:
        file_type = 'contact'
    elif media.location:
        file_type = 'location'
    elif media.venue:
        file_type = 'venue'
    elif media.game:
        file_type = 'game'
    elif media.invoice:
        file_type = 'invoice'
    elif media.poll:
        file_type = 'poll'
    elif media.web_page:
        file_type = 'web_page'
    
    # Clean the file name for better search indexing
    cleaned_file_name = clean_file_name(file_name)

    file_data = {
        'file_id': file_id,
        'file_ref': file_ref, # Store file_ref as hex string
        'file_name': file_name,
        'cleaned_file_name': cleaned_file_name, # Store cleaned name for search
        'file_size': file_size,
        'caption': caption,
        'file_type': file_type,
        'date': media.date # Store the date the message was sent
    }

    try:
        # Attempt to insert. DuplicateKeyError will be raised if file_id already exists
        result = await col.insert_one(file_data)
        logger.info(f"Successfully saved: {file_name} with MongoDB _id: {result.inserted_id}")
        return True, str(result.inserted_id) # Return the MongoDB _id
    except DuplicateKeyError:
        logger.warning(f"Duplicate file detected (file_id: {file_id}). Not saving.")
        return False, "Duplicate file."
    except Exception as e:
        logger.error(f"Error saving file {file_name}: {e}")
        return False, str(e)


async def get_search_results(chat_id: int, query: str, offset: int = 0, limit: int = 10, filter: bool = False) -> (list, int, int):
    """
    Searches for files in the database based on the query.
    Uses text index for efficient searching.
    Returns (files, next_offset, total_results).
    """
    search_query = clean_file_name(query)
    
    # Use text search on the 'cleaned_file_name' field
    # The $text operator requires a text index on the collection
    filter_criteria = {"$text": {"$search": search_query}}

    # Get total count first for pagination
    total_results = await col.count_documents(filter_criteria)
    if MULTIPLE_DATABASE and sec_col:
        total_results += await sec_col.count_documents(filter_criteria)

    files = []
    # Search in primary collection
    primary_files_cursor = col.find(filter_criteria).skip(offset).limit(limit)
    primary_files = await primary_files_cursor.to_list(length=limit)
    files.extend(primary_files)

    # If MULTIPLE_DATABASE is enabled, search in secondary collection as well
    if MULTIPLE_DATABASE and sec_col:
        remaining_limit = limit - len(files)
        if remaining_limit > 0:
            secondary_files_cursor = sec_col.find(filter_criteria).skip(max(0, offset - len(primary_files))).limit(remaining_limit)
            secondary_files = await secondary_files_cursor.to_list(length=remaining_limit)
            files.extend(secondary_files)
    
    # Sort results by relevance if possible (text search provides score)
    # Or by date, or file_name alphabetically if no score
    files.sort(key=lambda x: x.get('date', 0), reverse=True) # Sort by date descending

    next_offset = offset + len(files) if len(files) == limit else 0

    return files, next_offset, total_results


async def get_file_details(file_db_id: str) -> dict:
    """
    Fetches a single file's details by its MongoDB _id.
    """
    try:
        obj_id = ObjectId(file_db_id)
    except Exception:
        logger.error(f"Invalid ObjectId format: {file_db_id}")
        return None # Invalid ObjectId format

    file = await col.find_one({'_id': obj_id})
    if not file and MULTIPLE_DATABASE and sec_col:
        file = await sec_col.find_one({'_id': obj_id})
    return file

async def get_bad_files(keyword: str = None):
    """
    Retrieves blacklisted/bad files. If a keyword is provided, filters by that keyword.
    """
    logger.info(f"Retrieving bad files for keyword: {keyword}")
    if keyword:
        filter_criteria = {"$text": {"$search": clean_file_name(keyword)}}
    else:
        filter_criteria = {"is_bad": True} # Assuming a field 'is_bad' marks bad files

    files = await col.find(filter_criteria).to_list(length=None)
    total_count = await col.count_documents(filter_criteria)

    if MULTIPLE_DATABASE and sec_col:
        sec_files = await sec_col.find(filter_criteria).to_list(length=None)
        files.extend(sec_files)
        total_count += await sec_col.count_documents(filter_criteria)
        
    return files, total_count


# Helper functions for file_id encoding/decoding (if still needed for old file_ids)
# These are typically for Pyrogram's internal file_id handling, not for MongoDB _id
def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0
    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0
            r += bytes([i])
    return base64.urlsafe_b64encode(r).decode().rstrip("=")
    
def unpack_new_file_id(new_file_id):
    """Return file_id object from new_file_id string."""
    # This function is for decoding Pyrogram's new file_id format
    # It's not directly used for MongoDB _id lookups, but kept for completeness
    decoded = FileId.decode(new_file_id)
    # Example of how you might re-encode it if needed, but usually you'd just use decoded.file_id
    # and decoded.file_ref directly.
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    return file_id

