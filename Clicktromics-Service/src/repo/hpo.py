from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.collection import Collection
from typing import List, Optional
import re

from src.documents.primekg import HPOTermDocument, HPOAnnotationDocument
from src.mongo_client import Mongo
from src.request_model import PaginatedResponse
from src.logger import Logger

log = Logger.get_logger()

class HpoRepo:
    _collection: AsyncIOMotorCollection = None
    _sync_collection: Collection = None

    def __init__(self):
        try:
            self._collection = Mongo.get_hpo_terms_collection()
        except:
            pass

    def chunkify(self, data, chunk_size):
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]

    async def search(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
        fuzzy: bool = False
    ) -> PaginatedResponse[HPOTermDocument]:
        if not keyword:
            return PaginatedResponse(total=0, page=page, page_size=page_size, results=[])

        skip = (page - 1) * page_size
        regex = re.escape(keyword) if not fuzzy else f".*{re.escape(keyword)}.*"

        query = {
            "$or": [
                {"id": {"$regex": regex, "$options": "i"}},
                {"name": {"$regex": regex, "$options": "i"}},
                {"synonyms": {"$elemMatch": {"$regex": regex, "$options": "i"}}}
            ]
        }

        total = await self._collection.count_documents(query)
        cursor = self._collection.find(query).skip(skip).limit(page_size)
        docs = await cursor.to_list(length=page_size)

        return PaginatedResponse(
            total=total,
            page=page,
            page_size=page_size,
            results=[HPOTermDocument(**doc) for doc in docs]
        )

    async def find_by_ids(self, ids: List[str]) -> List[HPOTermDocument]:
        log.info(ids)
        cursor = self._collection.find({"_id":  {"$in": ids}})
        return [HPOTermDocument(**doc) async for doc in cursor]


class HpoAnnotationRepo:
    _collection: AsyncIOMotorCollection = None
    _sync_collection: Collection = None

    def __init__(self):
        self._collection = Mongo.get_hpo_annotations_collection()

    async def search_by_disease_id(
        self,
        disease_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedResponse[HPOAnnotationDocument]:
        skip = (page - 1) * page_size
        query = {"database_id": disease_id}

        total = await self._collection.count_documents(query)
        cursor = self._collection.find(query).skip(skip).limit(page_size)
        docs = await cursor.to_list(length=page_size)

        return PaginatedResponse(
            total=total,
            page=page,
            page_size=page_size,
            results=[HPOAnnotationDocument(**doc) for doc in docs]
        )

    async def find_by_hpo_id(
        self,
        hpo_id: str,
        limit: Optional[int] = None
    ) -> List[HPOAnnotationDocument]:
        query = {"hpo_id": hpo_id}
        cursor = await self._collection.find(query)
        docs = await cursor.limit(limit) if limit else cursor
        return [HPOAnnotationDocument(**doc) for doc in docs]

