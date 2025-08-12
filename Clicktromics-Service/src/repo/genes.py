
from motor.motor_asyncio import AsyncIOMotorCollection
from src.mongo_client import Mongo
from src.documents.genes import GeneDocument
from src.logger import Logger

log = Logger.get_logger()

class GeneRepo:
    _collection: AsyncIOMotorCollection = None

    def __init__(self):
        self._collection = Mongo.get_genes_collection()

    async def find_by_aliases(self, aliases: str) -> GeneDocument:
        """Fetch a gene from MongoDB by aliases and return a GeneDocument instance."""
        try:
            result = await self._collection.find_one({"aliases": {"$in": [aliases.upper()]}})
            return GeneDocument(**result)
        except Exception as e:
            # Log the error or handle it appropriately
            return None

    async def find_by_id(self, id: str) -> GeneDocument:
        """Fetch a gene from MongoDB by id and return a GeneDocument instance."""
        try:
            result = await self._collection.find_one({"id": id})
            return GeneDocument(**result)
        except Exception as e:
            # Log the error or handle it appropriately
            return None

    async def find_by_name(self, name: str) -> GeneDocument:
        """Fetch a gene from MongoDB by name and return a GeneDocument instance."""
        try:
            result = await self._collection.find_one({"geneName": name})
            return GeneDocument(**result)
        except Exception as e:
            # Log the error or handle it appropriately
            return None

    async def find(self, gene: str) -> GeneDocument:
        """Fetch a gene from MongoDB by gene and return a GeneDocument instance."""
        try:
            result = await self._collection.find_one(
                    { "$text": { "$search": gene.upper() } },
                    { "score": { "$meta": "textScore" } }
                ).sort({ "score": { "$meta": "textScore" } })
            
            return GeneDocument(**result)
        except Exception as e:
            return None