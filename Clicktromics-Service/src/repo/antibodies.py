from motor.motor_asyncio import AsyncIOMotorCollection
from src.mongo_client import Mongo
from src.documents.antibodies import AntibodyDocument
from typing import List
from src.request_model import PaginatedResponse

class AntibodyRepo:
    _collection: AsyncIOMotorCollection = None

    def __init__(self):
        self._collection = Mongo.get_antibodies_collection()

    async def find_by_disease_name(self, disease_name: str, limit: int) -> List[AntibodyDocument]:
        """Fetch an antibody from MongoDB by disease_name and return a AntibodyDocument instance."""
        try:
            cursor = self._collection.find({"disease_name": { "$regex": disease_name, "$options": "i" }}).limit(limit)
            results = await cursor.to_list(length=limit)
            return [AntibodyDocument(**doc) for doc in results]
        except Exception as e:
            # Log the error or handle it appropriately
            return []


    async def count_by_target(self, target: str) -> int:
        query = {"targets": {"$in": [target]}}
        total = await self._collection.count_documents(query)
        if total == 0:
            query = {"targets": {"$in": [target.upper()]}}
            total = await self._collection.count_documents(query)

        return total
    
    async def find_by_target(self, target: str, page: int, page_size: int) -> PaginatedResponse[AntibodyDocument]:
        """Fetch an antibody from MongoDB by target and return a AntibodyDocument instance."""

        skip = (page - 1) * page_size
        query = {"targets": {"$in": [target]}}

        total = await self._collection.count_documents(query)
        if total == 0:
            query = {"targets": {"$in": [target.upper()]}}
            total = await self._collection.count_documents(query)

        cursor = self._collection.find(query).skip(skip).limit(page_size)
        docs = await cursor.to_list(length=page_size)

        return PaginatedResponse(
            total=total,
            page=page,
            page_size=page_size,
            results=[AntibodyDocument(**doc) for doc in docs]
        )

    async def find(self, input: str, page: int, page_size: int) -> PaginatedResponse[AntibodyDocument]:
        """Fetch an antibody from MongoDB by disease_name and return a AntibodyDocument instance."""
        skip = (page - 1) * page_size
        query =  { "$text": { "$search": input.upper() } }

        total = await self._collection.count_documents(query)
        cursor = self._collection.find(
                query,
                { "score": { "$meta": "textScore" } }
        ).sort({ "score": { "$meta": "textScore" } }
        ).skip(skip).limit(page_size)
            
        docs = await cursor.to_list(length=page_size)

        return PaginatedResponse(
            total=total,
            page=page,
            page_size=page_size,
            results=[AntibodyDocument(**doc) for doc in docs]
        )

    async def find_by_id(self, id: int) -> AntibodyDocument:
        """Fetch an antibody from MongoDB by ID and return a AntibodyDocument instance."""
        try:
            result = self._collection.find_one({ "ID": id})
            return AntibodyDocument(**result)
        except Exception as e:
            return None