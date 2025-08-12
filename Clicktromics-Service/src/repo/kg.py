from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.collection import Collection
from typing import List, Optional

from src.documents.primekg import KGEdgeDocument
from src.mongo_client import Mongo
from src.request_model import PaginatedResponse

from src.logger import Logger

log = Logger.get_logger()

class KgEdgeRepo:
    _collection: AsyncIOMotorCollection = None
    _sync_collection: Collection = None

    def __init__(self):
        self._collection = Mongo.get_kg_edges_collection()

    async def find_edges_by_node_id(
        self,
        node_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedResponse[KGEdgeDocument]:
        skip = (page - 1) * page_size
        query = {
            "$or": [
                {"source.id": node_id},
                {"target.id": node_id}
            ]
        }

        total = await self._collection.count_documents(query)
        cursor = self._collection.find(query).skip(skip).limit(page_size)
        docs = await cursor.to_list(length=page_size)

        return PaginatedResponse(
            total=total,
            page=page,
            page_size=page_size,
            results=[KGEdgeDocument(**doc) for doc in docs]
        )

    async def find_edges_by_relation(
        self,
        relation: str,
        limit: Optional[int] = None
    ) -> List[KGEdgeDocument]:
        query = {"relation": relation}
        cursor = await self._collection.find(query)
        docs = await cursor.limit(limit) if limit else cursor
        return [KGEdgeDocument(**doc) for doc in docs]


    async def find_by_relation(self, source_id, source_type, target_type, relation) -> List[KGEdgeDocument]:
       
        cursor = self._collection.find({
            "$or":[
                {
                    "source.id": str(source_id),
                    "source.type": source_type,
                    "target.type": target_type,
                    "relation": relation
                },
                {
                    "target.id": str(source_id),
                    "target.type": source_type,
                    "source.type": target_type,
                    "relation": relation
                }
            ]
        })
        return [KGEdgeDocument(**doc) async for doc in cursor]
    

    async def find_by_relation_multi_source(self, source_ids: List[str], source_type: str, target_type: str, relation: str) -> List[KGEdgeDocument]:
        cursor = self._collection.find({
            "$or": [
                    {
                        "source.id": {"$in": source_ids},
                        "source.type": source_type,
                        "target.type": target_type,
                        "relation": relation
                    },
                    {
                        "target.id": {"$in": source_ids},
                        "target.type": source_type,
                        "source.type": target_type,
                        "relation": relation
                    }
            ]
        })
        return [KGEdgeDocument(**doc) async for doc in cursor]

    async def find_by_target_name_and_relation(self, name_contains: str, target_type: str, relation: str) -> List[KGEdgeDocument]:
        cursor = self._collection.find({
            "target.type": target_type,
            "relation": relation,
            "target.name": {"$regex": name_contains, "$options": "i"}
        })
        return [KGEdgeDocument(**doc) async for doc in cursor]


    async def rank_drug_by_targets(self, drug_ids: List[str]) -> List[KGEdgeDocument]:
        pipeline = [
            {
                "$match": {
                    "source.id": {"$in": drug_ids},
                    "source.type": "drug",
                    "target.type": "gene/protein",
                    "relation": "drug_protein"
                }
            },
            {
                "$group": {
                    "_id": "$source.id",
                    "target_count": {"$sum": 1},
                    "drug_name": {"$first": "$source.name"}
                }
            },
            {
                "$sort": {"target_count": -1}
            }
        ]

        cursor = self._collection.aggregate(pipeline)
        return [KGEdgeDocument(**doc) async for doc in cursor]