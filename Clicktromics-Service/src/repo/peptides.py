
from motor.motor_asyncio import AsyncIOMotorCollection
from src.mongo_client import Mongo
from src.documents.peptides import PeptideDocument
from src.logger import Logger
from typing import List

log = Logger.get_logger()

class PeptideRepo:
    _collection: AsyncIOMotorCollection = None

    def __init__(self):
        self._collection = Mongo.get_peptides_collection()

    async def save(self,conversation: PeptideDocument) -> None:
        """Save PeptideDocument in MongoDB."""
        await self._collection.insert_one(conversation.model_dump())

    async def find_by_targets(self, gene: str) -> List[PeptideDocument]:
        """Fetch a peptide from MongoDB by aliases and return a PeptideDocument instance."""
        cursor =  self._collection.find({"targets": {"$in": [gene.upper()]}})
        results = await cursor.to_list(length=None)  
        return [PeptideDocument(**doc) for doc in results]

    async def find_by_name(self, name: str) -> PeptideDocument:
        """Fetch a peptide from MongoDB by name and return a PeptideDocument instance."""
        result = await self._collection.find_one({"name": name})
        return PeptideDocument(**result)

    async def find(self, query: str) -> PeptideDocument:
        """Fetch a peptide from MongoDB by gene and return a PeptideDocument instance."""
        result = await self._collection.find_one(
                { "$text": { "$search": query } },
                { "score": { "$meta": "textScore" } }
            ).sort({ "score": { "$meta": "textScore" } })
        
        return PeptideDocument(**result)
        