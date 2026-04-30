from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client: AsyncIOMotorClient = None # starts as empty, gets filled on startup

async def connect_db(): # called when FastAPI starts up
    global client
    client = AsyncIOMotorClient(settings.MONGODB_URI)

async def close_db(): # called when FastAPI shuts down
    global client
    if client:
        client.close()

def get_db(): # called by every route that needs the DB
    return client[settings.MONGODB_DB]