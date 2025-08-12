from motor.motor_asyncio import AsyncIOMotorCollection
from typing import List, Optional
import re
from src.documents.rsid import RsidDocument
from src.mongo_client import Mongo
from pymongo.collection import Collection

from src.request_model import PaginatedResponse


class RsidRepo:
    _collection: AsyncIOMotorCollection = None
    _sync_collection: Collection = None  # Add a synchronous collection

    def __init__(self):
        # Ensure MongoDB client is initialized
        try:
            self._collection = Mongo.get_rsids_collection()
        except:
            pass
        self._sync_collection = Mongo.get_sync_rsids_collection()

    def chunkify(self, data, chunk_size):
        """Split a list into smaller chunks."""
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]

    async def search(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
        fuzzy: bool = False
    ) -> PaginatedResponse[RsidDocument]:
        if not keyword:
            return PaginatedResponse(total=0, page=page, page_size=page_size, results=[])

        skip = (page - 1) * page_size
        regex = re.escape(keyword) if not fuzzy else f".*{re.escape(keyword)}.*"

        query = {
            "$or": [
                {"rsid": {"$regex": regex, "$options": "i"}},
                {"genes": {"$elemMatch": {"$regex": regex, "$options": "i"}}},
                {f"aliases.{keyword.upper()}": {"$exists": True}}
            ]
        }

        total = await self._collection.count_documents(query)
        cursor = self._collection.find(query).skip(skip).limit(page_size)
        docs = await cursor.to_list(length=page_size)

        return PaginatedResponse(
            total=total,
            page=page,
            page_size=page_size,
            results=[RsidDocument(**doc) for doc in docs]
        )

    def find_by_rsid_list_async(self, rsids: List[str], limit: Optional[int] = None, chunk_size: int = 500) -> List[RsidDocument]:
        """
        Find all rsid documents matching any RSID in the provided list.
        Efficient if `SNPS` is indexed.
        """
        if not rsids:
            return []

        results = []
        for chunk in self.chunkify(rsids, chunk_size):
            query = {
                "$and": [
                    {"rsid": {"$in": chunk}},
                    {
                        "$or": [
                            {"disease": {"$exists": True, "$ne": None}}
                        ]
                    }
                ]
            }
            cursor = self._sync_collection.find(query)
            docs = cursor.to_list(length=chunk_size)

            if limit is None:
                results.extend([RsidDocument(**doc) for doc in docs])
            else:
                for doc in docs:
                    results.append(RsidDocument(**doc))
                    if len(results) >= limit:
                        return results


        return results

    async def find_by_rsid_list(self, rsids: List[str], limit: Optional[int] = None, chunk_size: int = 500) -> List[RsidDocument]:
        """
        Find all rsid documents matching any RSID in the provided list.
        Efficient if `SNPS` is indexed.
        """
        if not rsids:
            return []

        results = []

        for chunk in self.chunkify(rsids, chunk_size):
            cursor = self._collection.find({"rsid": {"$in": chunk}})
            docs = await cursor.to_list(length=chunk_size)

            if limit is None:
                results.extend([RsidDocument(**doc) for doc in docs])
            else:
                for doc in docs:
                    results.append(RsidDocument(**doc))
                    if len(results) >= limit:
                        return results


        return results
