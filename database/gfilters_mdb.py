# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01


import motor.motor_asyncio # Changed to motor.motor_asyncio
from info import OTHER_DB_URI, DATABASE_NAME
from pyrogram import enums
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

myclient = motor.motor_asyncio.AsyncIOMotorClient(OTHER_DB_URI) # Changed to AsyncIOMotorClient
mydb = myclient[DATABASE_NAME]


async def add_gfilter(gfilters, text, reply_text, btn, file, alert):
    mycol = mydb[str(gfilters)]
    # mycol.create_index([('text', 'text')]) # Index creation should ideally be handled at startup for efficiency

    data = {
        'text':str(text),
        'reply':str(reply_text),
        'btn':str(btn),
        'file':str(file),
        'alert':str(alert)
    }

    try:
        await mycol.update_one({'text': str(text)},  {"$set": data}, upsert=True) # Added await
    except Exception as e: # Catch specific exception
        logger.exception(f'Some error occured! {e}', exc_info=True)
             
     
async def find_gfilter(gfilters, name):
    mycol = mydb[str(gfilters)]
    
    query = mycol.find( {"text":name})
    # query = mycol.find( { "$text": {"$search": name}})
    try:
        # Use to_list(length=1) to get the first matching document
        file = await query.to_list(length=1)
        if file:
            file = file[0] # Get the first document
            reply_text = file['reply']
            btn = file['btn']
            fileid = file['file']
            try:
                alert = file['alert']
            except:
                alert = None
            return reply_text, btn, alert, fileid
        else:
            return None, None, None, None
    except Exception as e: # Catch specific exception
        logger.exception(f'Error in find_gfilter: {e}', exc_info=True)
        return None, None, None, None


async def get_gfilters(gfilters):
    mycol = mydb[str(gfilters)]

    texts = []
    query = mycol.find()
    try:
        # Use to_list(length=None) to get all documents
        async for file in query: # Iterate asynchronously
            text = file['text']
            texts.append(text)
    except Exception as e: # Catch specific exception
        logger.exception(f'Error in get_gfilters: {e}', exc_info=True)
        pass
    return texts


async def delete_gfilter(message, text, gfilters):
    mycol = mydb[str(gfilters)]
    
    myquery = {'text':text }
    query_count = await mycol.count_documents(myquery) # Added await
    if query_count == 1:
        await mycol.delete_one(myquery) # Added await
        await message.reply_text(
            f"'`{text}`'  deleted. I'll not respond to that gfilter anymore.",
            quote=True,
            parse_mode=enums.ParseMode.MARKDOWN
        )
    else:
        await message.reply_text("Couldn't find that gfilter!", quote=True)

async def del_allg(message, gfilters):
    # Use list_collection_names() with await
    collection_names = await mydb.list_collection_names()
    if str(gfilters) not in collection_names:
        await message.edit_text("Nothing to Remove !")
        return

    mycol = mydb[str(gfilters)]
    try:
        await mycol.drop() # Added await
        await message.edit_text(f"All gfilters has been removed !")
    except Exception as e: # Catch specific exception
        logger.exception(f'Error in del_allg: {e}', exc_info=True)
        await message.edit_text("Couldn't remove all gfilters !")
        return

async def count_gfilters(gfilters):
    mycol = mydb[str(gfilters)]

    count = await mycol.count_documents({}) # Changed to count_documents and added await
    return False if count == 0 else count


async def gfilter_stats():
    collections = await mydb.list_collection_names() # Added await

    if "CONNECTION" in collections:
        collections.remove("CONNECTION")

    totalcount = 0
    for collection in collections:
        mycol = mydb[collection]
        count = await mycol.count_documents({}) # Changed to count_documents and added await
        totalcount += count

    totalcollections = len(collections)

    return totalcollections, totalcount

