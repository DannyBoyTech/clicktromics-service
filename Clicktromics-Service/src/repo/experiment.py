from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.collection import Collection
from src.mongo_client import Mongo
from src.documents.experiment import ExperimentDocument, DrugDocument
from typing import List, Optional
import datetime

class ExperimentRepo:
    _collection: AsyncIOMotorCollection = None
    _sync_collection: Collection = None  # Add a synchronous collection

    def __init__(self):
        # Ensure MongoDB client is initialized
        try:
            self._collection = Mongo.get_experiments_collection()
        except:
            pass
        self._sync_collection = Mongo.get_sync_experiments_collection()
        

    async def save(self,experiment: ExperimentDocument) -> None:
        """Save the experiment in MongoDB."""
        await self._collection.insert_one(experiment.model_dump(by_alias=True))

    async def update(self, experiment: ExperimentDocument) -> bool:
        result = await self._collection.replace_one({"experiment_id": experiment.experiment_id}, experiment.model_dump())
        return result.matched_count > 0

    def update_sync(self, experiment: ExperimentDocument) -> bool:
        result = self._sync_collection.replace_one({"experiment_id": experiment.experiment_id}, experiment.model_dump())
        return result.matched_count > 0

    def update_job_sync(self, experiment_id: str, job_id: str, user_email: str, new_status: str) -> None:
        """Synchronously update the experiment in MongoDB."""
        experiment = self.find_by_job_id_sync(experiment_id, job_id, user_email)
        if not experiment:
            raise ValueError(f"Experiment with ID {experiment_id} and job ID {job_id} not found for user {user_email}")

        for i in range(len(experiment.jobs)):
            if experiment.jobs[i].job_id == job_id:
                experiment.jobs[i].status = new_status
                experiment.jobs[i].updated_at = datetime.datetime.now(datetime.timezone.utc)   
                if experiment.stage and experiment.stage.job_id == job_id:
                    experiment.stage = experiment.jobs[i]
                self.update_sync(experiment)
                break 

    async def update_job(self, experiment_id: str, job_id: str, user_email: str, new_status: str) -> None:
        """Synchronously update the experiment in MongoDB."""
        experiment = await self.find_by_job_id(experiment_id, job_id, user_email)
        if not experiment:
            raise ValueError(f"Experiment with ID {experiment_id} and job ID {job_id} not found for user {user_email}")

        for i in range(len(experiment.jobs)):
            if experiment.jobs[i].job_id == job_id:
                experiment.jobs[i].status = new_status
                experiment.jobs[i].updated_at = datetime.datetime.now(datetime.timezone.utc)   
                if experiment.stage and experiment.stage.job_id == job_id:
                    experiment.stage = experiment.jobs[i]
                await self.update(experiment)
                break 

    def update_job_output_files_sync(self, experiment_id: str, job_id: str, user_email: str, files: List[str]) -> None:
        """Synchronously append files to the outputs.files of a specific job in MongoDB."""
        experiment = self.find_by_job_id_sync(experiment_id, job_id, user_email)
        if not experiment:
            raise ValueError(f"Experiment with ID {experiment_id} and job ID {job_id} not found for user {user_email}")

        for i in range(len(experiment.jobs)):
            if experiment.jobs[i].job_id == job_id:
                experiment.jobs[i].outputs["files"].extend(files)  # Extend the files array
                if experiment.stage and experiment.stage.job_id == job_id:
                    experiment.stage = experiment.jobs[i]
                self.update_sync(experiment)
                break 

    async def find_by_experiment_id(self, experiment_id: str, user_email: str) -> Optional['ExperimentDocument']:
        """Fetch a experiment from MongoDB by experiment_id and return a ExperimentDocument instance."""
        experiment_data = await self._collection.find_one({"experiment_id": experiment_id, "user_email":user_email})
        if experiment_data:
            return ExperimentDocument(**experiment_data)
        return None

    def find_by_experiment_id_sync(self, experiment_id: str, user_email: str) -> Optional['ExperimentDocument']:
        """Fetch a experiment from MongoDB by experiment_id and return a ExperimentDocument instance."""
        experiment_data =  self._sync_collection.find_one({"experiment_id": experiment_id, "user_email":user_email})
        if experiment_data:
            return ExperimentDocument(**experiment_data)
        return None

    async def find_by_job_id(self, experiment_id: str, job_id: str, user_email: str) -> Optional['ExperimentDocument']:
        """Fetch a experiment from MongoDB by job_id and return a ExperimentDocument instance."""
        experiment_data = await self._collection.find_one({"jobs.job_id": job_id, "experiment_id": experiment_id, "user_email":user_email})
        if experiment_data:
            return ExperimentDocument(**experiment_data)
        return None

    def find_by_job_id_sync(self, experiment_id: str, job_id: str, user_email: str) -> Optional['ExperimentDocument']:
        """Fetch a experiment from MongoDB by job_id and return a ExperimentDocument instance."""
        experiment_data =  self._sync_collection.find_one({"jobs.job_id": job_id, "experiment_id": experiment_id, "user_email":user_email})
        if experiment_data:
            return ExperimentDocument(**experiment_data)
        return None

    async def get(self, query, sort_order, skip, limit) -> List[ExperimentDocument]:
        """Fetch a experiment from MongoDB by experiment_id and return a ExperimentDocument instance."""
        cursor = self._collection.find(query).sort("updated_at", sort_order).skip(skip).limit(limit)
        results = await cursor.to_list(length=limit)
        return [ExperimentDocument(**doc) for doc in results]



class DrugRepo:
    _collection: AsyncIOMotorCollection = None

    def __init__(self):
        self._collection = Mongo.get_drugs_collection()

    async def find_by_id(self, id: str) -> DrugDocument:
        """Fetch a drug from MongoDB by drugbank_id and return a DrugDocument instance."""
        result = await self._collection.find_one({"drugbank_id": id})
        if result:
            return DrugDocument(**result)
        return None

    async def find_by_organ(self, organ: str) -> list[DrugDocument]:
        """Fetch all drugs that target a given organ."""
        cursor = self._collection.find({"targets.organs": organ})
        results = await cursor.to_list(length=10)
        return [DrugDocument(**doc) for doc in results]

    async def find_by_gene(self, gene: str) -> list[DrugDocument]:
        """Fetch all drugs that target a given gene."""
        print({"targets.gene_names": gene})
        cursor = self._collection.find({"targets.gene_names": gene.upper()})
        results = await cursor.to_list(length=10)
        return [DrugDocument(**doc) for doc in results]
