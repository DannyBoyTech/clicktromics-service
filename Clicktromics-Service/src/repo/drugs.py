from motor.motor_asyncio import AsyncIOMotorCollection
from src.mongo_client import Mongo
from src.documents.drugs import DrugDocument
from src.logger import Logger

log = Logger.get_logger()

class DrugRepo:
    _collection: AsyncIOMotorCollection = None

    def __init__(self):
        self._collection = Mongo.get_drugs_collection()

    async def find_by_name(self, name: str) -> DrugDocument:
        """Fetch drugs from MongoDB by drugs name and return a DrugDocument instance."""
        try:
            result = await self._collection.find_one({"drug_name": name})
            return DrugDocument(**result)
        except Exception as e:
            log.error(f"Error in find_by_name for name '{name}': {str(e)}")
            return None