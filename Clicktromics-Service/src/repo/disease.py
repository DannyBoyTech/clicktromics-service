from motor.motor_asyncio import AsyncIOMotorCollection
from typing import List, Optional
import re
from typing import Generic, List, TypeVar
from src.documents.disease import DiseaseDocument
from src.mongo_client import Mongo
from pymongo.collection import Collection
from pydantic.generics import GenericModel
from src.logger import Logger

log = Logger.get_logger()

T = TypeVar("T")

class PaginatedResponse(GenericModel, Generic[T]):
    total: int
    page: int
    page_size: int
    results: List[T]

class DiseaseRepo:
    _collection: AsyncIOMotorCollection = None
    _sync_collection: Collection = None  # Add a synchronous collection

    def __init__(self):
        # Ensure MongoDB client is initialized
        try:
            self._collection = Mongo.get_diseases_collection()
        except:
            pass
        self._sync_collection = None

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
    ) -> PaginatedResponse[DiseaseDocument]:
        if not keyword:
            return PaginatedResponse(total=0, page=page, page_size=page_size, results=[])

        skip = (page - 1) * page_size
        regex = re.escape(keyword) if not fuzzy else f".*{re.escape(keyword)}.*"

        query = {
            "$or": [
                {"name": {"$regex": regex, "$options": "i"}},
                {"category": {"$regex": regex, "$options": "i"}}
            ]
        }

        total = await self._collection.count_documents(query)
        cursor = self._collection.find(query).skip(skip).limit(page_size)
        docs = await cursor.to_list(length=page_size)

        return PaginatedResponse(
            total=total,
            page=page,
            page_size=page_size,
            results=[DiseaseDocument(**doc) for doc in docs]
        )

    def find_category_by_search_name_list(self, names: List[str], chunk_size: int = 500) -> List[DiseaseDocument]:
        """
        Find all diseases documents matching any name in the provided list.
        """
        if not names:
            return []

        results = []
        for chunk in self.chunkify(names, chunk_size):
            query = {"search_name": {"$in": chunk}}

            cursor = self._sync_collection.find(query)
            docs = cursor.to_list(length=chunk_size)
           
            for doc in docs:
                if "category" in doc and not isinstance(doc["category"], list):
                    doc["category"] = [doc["category"]]
                results.append(DiseaseDocument(**doc))
                    
        return results
    
    async def find_category_by_query_list(self, query: str) -> List[DiseaseDocument]:
        """
        Find all diseases documents matching any name in the provided list.
        """
        if not query:
            return []

        results = []
        cursor =  self._collection.find({ "category": query }, {'name', 'category'})
        docs = await cursor.to_list(length=None)
        
        for doc in docs:
            if "category" in doc and not isinstance(doc["category"], list):
                doc["category"] = [doc["category"]]
            results.append(DiseaseDocument(**doc))
                    
        return results