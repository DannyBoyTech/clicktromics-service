from motor.motor_asyncio import AsyncIOMotorCollection
from src.mongo_client import Mongo
from src.documents.organs import OrganDocument
from src.logger import Logger
from src.request_model import PaginatedResponse

log = Logger.get_logger()

class OrganRepo:
    _collection: AsyncIOMotorCollection = None

    def __init__(self):
        self._collection = Mongo.get_organs_collection()

    async def find_by_name(self, name: str, page: int = 1, page_size: int = 10) -> PaginatedResponse[OrganDocument]:
        """Fetch genes from MongoDB by organs name and return a OrganDocument instance."""

        skip = (page - 1) * page_size
        query = {"name": name}
    
        total = await self._collection.count_documents(query)
        doc = await self._collection.find_one(query)

        return PaginatedResponse(
            total=total,
            page=page,
            page_size=page_size,
            results=[OrganDocument(name=doc["name"], genes= doc["genes"][skip:skip+page_size])]
        )