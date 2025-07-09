# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re, base64, json
from struct import pack
from pyrogram.file_id import FileId
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from info import FILE_DB_URI, SEC_FILE_DB_URI, DATABASE_NAME, COLLECTION_NAME, MULTIPLE_DATABASE, USE_CAPTION_FILTER, MAX_BTN

# First Database For File Saving 
client = MongoClient(FILE_DB_URI)
db = client[DATABASE_NAME]
col = db[COLLECTION_NAME]

# Second Database For File Saving
sec_client = MongoClient(SEC_FILE_DB_URI)
sec_db = sec_client[DATABASE_NAME]
sec_col = sec_db[COLLECTION_NAME]


async def save_file(media):
    """Save file in the database."""
    
    file_id = unpack_new_file_id(media.file_id)
    file_name = clean_file_name(media.file_name)
    
    file = {
        'file_id': file_id,
        'file_name': file_name,
        'file_size': media.file_size,
        'caption': media.caption.html if media.caption else None
    }

    if is_file_already_saved(file_id, file_name):
        return False, 0

    try:
        col.insert_one(file)
        print(f"{file_name} is successfully saved.")
        return True, 1
    except DuplicateKeyError:
        print(f"{file_name} is already saved.")
        return False, 0
    except Exception as e: # Catch general exceptions
        print(f"Error saving file to primary DB: {e}")
        if MULTIPLE_DATABASE:
            try:
                sec_col.insert_one(file)
                print(f"{file_name} is successfully saved to secondary DB.")
                return True, 1
            except DuplicateKeyError:
                print(f"{file_name} is already saved in secondary DB.")
                return False, 0
            except Exception as e_sec:
                print(f"Error saving file to secondary DB: {e_sec}")
                print("Your Current File Database Is Full, Turn On Multiple Database Feature And Add Second File Mongodb To Save File.")
                return False, 0
        else:
            print("Your Current File Database Is Full, Turn On Multiple Database Feature And Add Second File Mongodb To Save File.")
            return False, 0

def clean_file_name(file_name):
    """Clean and format the file name."""
    file_name = re.sub(r"(_|\-|\.|\+)", " ", str(file_name)) 
    unwanted_chars = ['[', ']', '(', ')', '{', '}']
    
    for char in unwanted_chars:
        file_name = file_name.replace(char, '')
        
    return ' '.join(filter(lambda x: not x.startswith('@') and not x.startswith('http') and not x.startswith('www.') and not x.startswith('t.me'), file_name.split()))

def is_file_already_saved(file_id, file_name):
    """Check if the file is already saved in either collection."""
    # Use regex for file_name to account for minor variations
    regex_file_name = re.compile(re.escape(file_name), re.IGNORECASE)

    # Check by file_id (exact match)
    if col.find_one({'file_id': file_id}) or (MULTIPLE_DATABASE and sec_col.find_one({'file_id': file_id})):
        print(f"File with ID {file_id} is already saved.")
        return True
    
    # Check by file_name (regex match)
    if col.find_one({'file_name': regex_file_name}) or (MULTIPLE_DATABASE and sec_col.find_one({'file_name': regex_file_name})):
        print(f"File with name '{file_name}' is already saved (fuzzy match).")
        return True
            
    return False

async def get_search_results(chat_id, query, offset=0, max_results=MAX_BTN, filter=False):
    """
    For given query return (results, next_offset, total_results).
    Uses regex for flexible, case-insensitive search across file_name and caption.
    """
    query = query.strip()
    if not query:
        # If query is empty, match any document
        regex_pattern = re.compile(".*", re.IGNORECASE)
    else:
        # Escape special characters in the query for regex safety
        escaped_query = re.escape(query)
        # Create a regex pattern for case-insensitive substring match
        regex_pattern = re.compile(f".*{escaped_query}.*", re.IGNORECASE)

    # Build the MongoDB query to search in file_name and caption
    mongo_query = {
        "$or": [
            {"file_name": {"$regex": regex_pattern}},
            {"caption": {"$regex": regex_pattern}}
        ]
    }

    files = []
    total_results = 0

    # Fetch results from primary collection
    primary_cursor = col.find(mongo_query).skip(offset).limit(max_results)
    primary_files = await primary_cursor.to_list(length=None)
    files.extend(primary_files)
    total_results += await col.count_documents(mongo_query)

    # Fetch results from secondary collection if MULTIPLE_DATABASE is enabled
    if MULTIPLE_DATABASE:
        secondary_cursor = sec_col.find(mongo_query).skip(offset).limit(max_results)
        secondary_files = await secondary_cursor.to_list(length=None)
        files.extend(secondary_files)
        total_results += await sec_col.count_documents(mongo_query)
    
    # Deduplicate files if they came from both collections (optional, depends on your data)
    # For simplicity, if a file is in both, it might appear twice.
    # If strict deduplication is needed, you'd process `files` list here.

    # Calculate next_offset
    next_offset = offset + len(files)
    if next_offset >= total_results:
        next_offset = 0 # Indicate no more pages if all results are fetched or less than limit

    return files, next_offset, total_results

async def get_bad_files(query):
    """
    For given query return (results, total_results) for files to be deleted.
    Uses regex for flexible, case-insensitive search across file_name and caption.
    """
    query = query.strip()
    
    if not query:
        raw_pattern = '.'
    else:
        # Escape special characters in the query for regex safety
        raw_pattern = re.escape(query)
    
    try:
        # Create a regex pattern for case-insensitive substring match
        regex = re.compile(f".*{raw_pattern}.*", re.IGNORECASE)
    except re.error:
        return [], 0

    filter_criteria = {'file_name': regex}
    if USE_CAPTION_FILTER:
        filter_criteria = {'$or': [filter_criteria, {'caption': regex}]}

    files = []
    total_results = 0

    # Find documents in primary collection
    primary_files = await col.find(filter_criteria).to_list(length=None)
    files.extend(primary_files)
    total_results += await col.count_documents(filter_criteria)

    # Find documents in secondary collection if MULTIPLE_DATABASE is enabled
    if MULTIPLE_DATABASE:
        secondary_files = await sec_col.find(filter_criteria).to_list(length=None)
        files.extend(secondary_files)
        total_results += await sec_col.count_documents(filter_criteria)

    return files, total_results

async def get_file_details(query_or_file_id):
    """
    Fetches a single file's details by its file_id.
    This function is intended for direct file_id lookup, not general search.
    """
    # This function is specifically for looking up by file_id,
    # as indicated by its original usage and name.
    # For general text search, get_search_results should be used.
    file = await col.find_one({'file_id': query_or_file_id})
    if not file and MULTIPLE_DATABASE:
        file = await sec_col.find_one({'file_id': query_or_file_id})
    return [file] if file else [] # Return as a list for consistency with other functions that return lists


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
    """Return file_id"""
    decoded = FileId.decode(new_file_id)
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
