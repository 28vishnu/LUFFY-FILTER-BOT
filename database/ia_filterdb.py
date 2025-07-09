# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re, base64, json
from struct import pack
from pyrogram.file_id import FileId, FileType
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId # Import ObjectId for querying by _id
from info import FILE_DB_URI, SEC_FILE_DB_URI, DATABASE_NAME, COLLECTION_NAME, MULTIPLE_DATABASE, USE_CAPTION_FILTER, MAX_BTN

# First Database For File Saving 
client = MongoClient(FILE_DB_URI)
db = client[DATABASE_NAME]
col = db[COLLECTION_NAME]
col.create_index([("file_name", "text")], name="file_name_text_index") # For text search
col.create_index([("file_id", 1)], unique=True) # Ensure file_id is unique for primary DB

# Second Database For File Saving (if enabled)
sec_client = None
sec_db = None
sec_col = None
if MULTIPLE_DATABASE:
    sec_client = MongoClient(SEC_FILE_DB_URI)
    sec_db = sec_client[DATABASE_NAME]
    sec_col = sec_db[COLLECTION_NAME]
    sec_col.create_index([("file_name", "text")], name="sec_file_name_text_index")
    sec_col.create_index([("file_id", 1)], unique=True) # Ensure file_id is unique for secondary DB


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
        # Check if file with same file_id already exists to prevent duplicates
        existing_file = await col.find_one({'file_id': file_id})
        if existing_file:
            return False, "File already exists."

        result = await col.insert_one(file_data)
        print(f"Successfully saved: {file_name} with MongoDB _id: {result.inserted_id}")
        return True, str(result.inserted_id) # Return the MongoDB _id
    except DuplicateKeyError:
        print(f"Duplicate file detected (file_id: {file_id}). Not saving.")
        return False, "Duplicate file."
    except Exception as e:
        print(f"Error saving file {file_name}: {e}")
        return False, str(e)


async def get_search_results(query: str, limit: int = 20) -> list:
    """
    Searches for files in the database based on the query.
    Uses text index for efficient searching.
    """
    search_query = clean_file_name(query)
    
    # Use text search on the 'cleaned_file_name' field
    # The $text operator requires a text index on the collection
    filter_criteria = {"$text": {"$search": search_query}}

    files = []
    # Search in primary collection
    primary_files = await col.find(filter_criteria).limit(limit).to_list(length=None)
    files.extend(primary_files)

    # If MULTIPLE_DATABASE is enabled, search in secondary collection as well
    if MULTIPLE_DATABASE and sec_col:
        remaining_limit = limit - len(files)
        if remaining_limit > 0:
            secondary_files = await sec_col.find(filter_criteria).limit(remaining_limit).to_list(length=None)
            files.extend(secondary_files)
    
    # Sort results by relevance if possible (text search provides score)
    # Or by date, or file_name alphabetically if no score
    files.sort(key=lambda x: x.get('date', 0), reverse=True) # Sort by date descending

    return files


async def get_file_details(file_db_id: str) -> dict:
    """
    Fetches a single file's details by its MongoDB _id.
    """
    try:
        obj_id = ObjectId(file_db_id)
    except Exception:
        return None # Invalid ObjectId format

    file = await col.find_one({'_id': obj_id})
    if not file and MULTIPLE_DATABASE and sec_col:
        file = await sec_col.find_one({'_id': obj_id})
    return file


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

