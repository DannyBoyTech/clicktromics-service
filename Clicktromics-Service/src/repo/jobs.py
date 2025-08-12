from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.collection import Collection
from typing import List, Optional
from typing import List
from src.documents.jobs import JobDocument
from src.mongo_client import Mongo

class JobRepo:
    _collection: AsyncIOMotorCollection = None
    _sync_collection: Collection = None  # Add a synchronous collection

    def __init__(self):
        # Ensure MongoDB client is initialized
        try:
            self._collection = Mongo.get_jobs_collection()
        except:
            pass
        self._sync_collection = Mongo.get_sync_jobs_collection()
        

    async def save(self, job: JobDocument) -> None:
        """Save the job in MongoDB."""
        await self._collection.insert_one(job.model_dump(by_alias=True))

    async def update(self, job: JobDocument) -> bool:
        result = await self._collection.replace_one({"job_id": job.job_id}, job.model_dump())
        return result.matched_count > 0

    def update_sync(self, job: JobDocument) -> bool:
        result = self._sync_collection.replace_one({"job_id": job.job_id}, job.model_dump())
        return result.matched_count > 0

    async def find_by_job_id(self, job_id: str, ) -> Optional['JobDocument']:
        """Fetch a job from MongoDB by job_id and return a JobDocument instance."""
        job_data = await self._collection.find_one({"job_id": job_id})
        if job_data:
            return JobDocument(**job_data)
        return None

    def find_by_job_id_sync(self, job_id: str) -> Optional['JobDocument']:
        """Fetch a job from MongoDB by job_id and return a JobDocument instance."""
        job_data = self._sync_collection.find_one({"job_id": job_id})
        if job_data:
            return JobDocument(**job_data)
        return None

    async def get(self, query, sort_order, skip, limit) -> List[JobDocument]:
        """Fetch jobs from MongoDB based on a query and return a list of JobDocument instances."""
        cursor = self._collection.find(query).sort("updated_at", sort_order).skip(skip).limit(limit)
        results = await cursor.to_list(length=limit)
        return [JobDocument(**doc) for doc in results]