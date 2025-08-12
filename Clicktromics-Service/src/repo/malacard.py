from motor.motor_asyncio import AsyncIOMotorCollection
from typing import List, Optional, Tuple
import re
from typing import Generic, List, TypeVar
from src.documents.malacard import DiseaseDocument
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

class MalacardRepo:
    _collection: AsyncIOMotorCollection = None
    _sync_collection: Collection = None  # Add a synchronous collection

    def __init__(self):
        # Ensure MongoDB client is initialized
        try:
            self._collection = Mongo.get_malacards_collection()
        except:
            pass
        self._sync_collection = NotImplemented

    def chunkify(self, data, chunk_size):
        """Split a list into smaller chunks."""
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]

    async def find_disease_by_name(self, name: str) -> DiseaseDocument:
        if not name:
            return None
        
        try:
            result = await self._collection.find_one({
                "main_name": name
            })

            return DiseaseDocument(**result)
        except:
            return None

    def find_disease_by_rsid_list(self, ids: List[str], chunk_size: int = 500) -> List[DiseaseDocument]:
        """
        Find all disease documents that contain at least one matching rsid in their variants.
        Only include the matching variants in the result.
        """
        if not ids:
            return []

        results = []

        for chunk in self.chunkify(ids, chunk_size):
            # Limit fields returned by MongoDB using projection
            cursor = self._sync_collection.find(
                {"variants.rsid": {"$in": chunk}},
                {
                    "main_name": 1,
                    "description": 1,
                    "genes": 1,
                    "phenotypes": 1,
                    "drugs": 1,
                    "variants": 1
                }
            )
            docs = cursor.to_list(length=chunk_size)

            for doc in docs:
                # Filter variants to only keep those with rsid in chunk
                matching_variants = [
                    variant for variant in doc.get("variants", [])
                    if variant.get("rsid") in chunk
                ]

                doc["variants"] = matching_variants

                doc.setdefault("aliases", [])
                results.append(DiseaseDocument(**doc))

        return results

    def find_disease_by_clinvarid_list(self, ids: List[str], chunk_size: int = 500) -> List[DiseaseDocument]:
        """
        Find all diseases documents matching any clinvarid_ in the provided list.
        """
        if not ids:
            return []

        results = []

        for chunk in self.chunkify(ids, chunk_size):
            cursor = self._sync_collection.find({"variants.clinvar_id": {"$in": chunk}},{
                "main_name": 1,
                "description": 1,
                "genes": 1,
                "phenotypes": 1,
                "drugs": 1,
                "variants": 1
            }
        )
            docs =  cursor.to_list(length=chunk_size)

            for doc in docs:
                matching_variants = [
                    variant for variant in doc.get("variants", [])
                    if variant.get("clinvar_id") in chunk
                ]

                doc["variants"] = matching_variants

                # Fill in missing fields so Pydantic doesn't raise an error
                doc.setdefault("aliases", [])
                results.append(DiseaseDocument(**doc))

        return results
