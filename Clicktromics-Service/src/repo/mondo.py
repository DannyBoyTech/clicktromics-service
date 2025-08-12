from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.collection import Collection
from typing import List, Optional
import re

from src.documents.primekg import MondoTermDocument
from src.mongo_client import Mongo
from src.request_model import PaginatedResponse

class MondoRepo:
    _collection: AsyncIOMotorCollection = None
    _sync_collection: Collection = None

    def __init__(self):
        try:
            self._collection = Mongo.get_mondo_terms_collection()
        except:
            pass

    def chunkify(self, data, chunk_size):
        """Split a list into smaller chunks."""
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]

    def normalize(self, name : str):
        return re.sub(r'\W+', '', name.lower())

    async def search(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
        fuzzy: bool = False
    ) -> PaginatedResponse[MondoTermDocument]:
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
            results=[MondoTermDocument(**doc) for doc in docs]
        )

    async def find_by_ids(self, ids: List[str], limit: Optional[int] = None, chunk_size: int = 500) -> List[MondoTermDocument]:
        if not ids:
            return []

        results = []
        for chunk in self.chunkify(ids, chunk_size):
            cursor = self._collection.find({"id": {"$in": chunk}})
            docs = await cursor.to_list(length=chunk_size)

            if limit is None:
                results.extend([MondoTermDocument(**doc) for doc in docs])
            else:
                for doc in docs:
                    results.append(MondoTermDocument(**doc))
                    if len(results) >= limit:
                        return results
        return results

    async def find_by_name(self, name_substring: str) -> List[MondoTermDocument]:
        cursor = await self._collection.find({
            "name": {"$regex": name_substring, "$options": "i"}
        })
        return [MondoTermDocument(**doc) async for doc in cursor]

    async def search_by_name_fragment(self, name_fragment: str) -> List[MondoTermDocument]:
        """
        Search MONDO terms by a partial name using case-insensitive regex.
        """
        if not name_fragment:
            return []

        all_docs = await self._collection.find({}).to_list(length=57000)
        return [MondoTermDocument(**doc) for doc in all_docs]


