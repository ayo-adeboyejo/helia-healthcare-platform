from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

client: AsyncIOMotorClient = None
database: AsyncIOMotorDatabase = None


async def init_mongodb():
    global client, database
    client = AsyncIOMotorClient(settings.mongo_url)
    database = client[settings.mongo_db]
    # Create indexes
    await database.documents.create_index("patient_id")
    await database.prescriptions.create_index("patient_id")
    await database.consultation_notes.create_index("patient_id")
    await database.patients_history.create_index("patient_id", unique=True)


async def close_mongodb():
    if client:
        client.close()


async def get_db() -> AsyncIOMotorDatabase:
    return database
