from src.config import MONGO_URL,MONGO_DATABASE
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo.server_api import ServerApi
from pymongo import MongoClient  # Import for synchronous MongoDB client

class Mongo:
    _mongo_client = None
    _sync_mongo_client = None  # Add a synchronous MongoDB client

    @classmethod
    def is_initialized(cls):
        if cls._mongo_client is None or cls._sync_mongo_client is None:
            return False

        return True
    
    @classmethod
    async def get_client(cls) -> AsyncIOMotorClient:
        """Get the MongoDB client, initializing it if necessary."""
        if cls._mongo_client is None:
            await cls._initialize_client()
        return cls._mongo_client
    
    @classmethod
    def get_client_sync(cls):
        """Get the synchronous MongoDB client, initializing it if necessary."""
        if cls._sync_mongo_client is None:
            cls._initialize_sync_client()
        return cls._sync_mongo_client

    @classmethod
    def get_conversations_collection(cls) -> AsyncIOMotorCollection:
        if cls._mongo_client is None:
            raise ValueError("MongoDB client is not initialized. Call Mongo.initialize() first.")
        db = cls._mongo_client[MONGO_DATABASE]  
        return db['conversations']

    @classmethod
    def get_experiments_collection(cls) -> AsyncIOMotorCollection:
        if cls._mongo_client is None:
            raise ValueError("MongoDB client is not initialized. Call Mongo.initialize() first.")
        db = cls._mongo_client[MONGO_DATABASE]  
        return db['experiments']

    @classmethod
    def get_profiles_collection(cls) -> AsyncIOMotorCollection:
        if cls._mongo_client is None:
            raise ValueError("MongoDB client is not initialized. Call Mongo.initialize() first.")
        db = cls._mongo_client[MONGO_DATABASE]  
        return db['profiles']

    @classmethod
    def get_antibodies_collection(cls) -> AsyncIOMotorCollection:
        if cls._mongo_client is None:
            raise ValueError("MongoDB client is not initialized. Call Mongo.initialize() first.")
        db = cls._mongo_client[MONGO_DATABASE]  
        return db['antibodies']
    
    @classmethod
    def get_diseases_collection(cls) -> AsyncIOMotorCollection:
        if cls._mongo_client is None:
            raise ValueError("MongoDB client is not initialized. Call Mongo.initialize() first.")
        db = cls._mongo_client[MONGO_DATABASE]  
        return db['diseases']
    
    @classmethod
    def get_malacards_collection(cls) -> AsyncIOMotorCollection:
        if cls._mongo_client is None:
            raise ValueError("MongoDB client is not initialized. Call Mongo.initialize() first.")
        db = cls._mongo_client[MONGO_DATABASE]  
        return db['malacards']
    
    @classmethod
    def get_genes_collection(cls) -> AsyncIOMotorCollection:
        if cls._mongo_client is None:
            raise ValueError("MongoDB client is not initialized. Call Mongo.initialize() first.")
        db = cls._mongo_client[MONGO_DATABASE]  
        return db['genes']
    
    @classmethod
    def get_drugs_collection(cls) -> AsyncIOMotorCollection:
        if cls._mongo_client is None:
            raise ValueError("MongoDB client is not initialized. Call Mongo.initialize() first.")
        db = cls._mongo_client[MONGO_DATABASE]  
        return db['drugs']
    
    @classmethod
    def get_rsids_collection(cls) -> AsyncIOMotorCollection:
        if cls._mongo_client is None:
            raise ValueError("MongoDB client is not initialized. Call Mongo.initialize() first.")
        db = cls._mongo_client[MONGO_DATABASE]  
        return db['rsid']

    @classmethod
    def get_jobs_collection(cls) -> AsyncIOMotorCollection:
        if cls._mongo_client is None:
            raise ValueError("MongoDB client is not initialized. Call Mongo.initialize() first.")
        db = cls._mongo_client[MONGO_DATABASE]  
        return db['jobs']

    @classmethod
    def get_organs_collection(cls) -> AsyncIOMotorCollection:
        if cls._mongo_client is None:
            raise ValueError("MongoDB client is not initialized. Call Mongo.initialize() first.")
        db = cls._mongo_client[MONGO_DATABASE]  
        return db['organs']

    @classmethod
    def get_kg_edges_collection(cls) -> AsyncIOMotorCollection:
        if cls._mongo_client is None:
            raise ValueError("MongoDB client is not initialized. Call Mongo.initialize() first.")
        db = cls._mongo_client[MONGO_DATABASE]  
        return db['kg_edges']

    @classmethod
    def get_hpo_terms_collection(cls) -> AsyncIOMotorCollection:
        if cls._mongo_client is None:
            raise ValueError("MongoDB client is not initialized. Call Mongo.initialize() first.")
        db = cls._mongo_client[MONGO_DATABASE]  
        return db['hpo_terms']

    @classmethod
    def get_hpo_annotations_collection(cls) -> AsyncIOMotorCollection:
        if cls._mongo_client is None:
            raise ValueError("MongoDB client is not initialized. Call Mongo.initialize() first.")
        db = cls._mongo_client[MONGO_DATABASE]  
        return db['hpo_annotations']

    @classmethod
    def get_mondo_terms_collection(cls) -> AsyncIOMotorCollection:
        if cls._mongo_client is None:
            raise ValueError("MongoDB client is not initialized. Call Mongo.initialize() first.")
        db = cls._mongo_client[MONGO_DATABASE]  
        return db['mondo_terms']

    @classmethod
    def get_peptides_collection(cls) -> AsyncIOMotorCollection:
        if cls._mongo_client is None:
            raise ValueError("MongoDB client is not initialized. Call Mongo.initialize() first.")
        db = cls._mongo_client[MONGO_DATABASE]  
        return db['peptides']
    
    @classmethod
    def get_users_collection(cls) -> AsyncIOMotorCollection:
        if cls._mongo_client is None:
            raise ValueError("MongoDB client is not initialized. Call Mongo.initialize() first.")
        db = cls._mongo_client[MONGO_DATABASE]  
        return db['users']
    
    @classmethod
    def get_password_reset_collection(cls) -> AsyncIOMotorCollection:
        if cls._mongo_client is None:
            raise ValueError("MongoDB client is not initialized. Call Mongo.initialize() first.")
        db = cls._mongo_client[MONGO_DATABASE]  
        return db['password_reset_tokens']
    
    @classmethod
    def get_refresh_tokens_collection(cls) -> AsyncIOMotorCollection:
        if cls._mongo_client is None:
            raise ValueError("MongoDB client is not initialized. Call Mongo.initialize() first.")
        db = cls._mongo_client[MONGO_DATABASE]  
        return db['refresh_tokens']
    
    @classmethod
    async def _initialize_client(cls):
        """Initialize the MongoDB client with a standard configuration."""
        cls._mongo_client = AsyncIOMotorClient(
            MONGO_URL,
            server_api=ServerApi('1')
        )
        cls._mongo_client[MONGO_DATABASE] 
        try:
            await cls._mongo_client.admin.command('ping')
            print("Pinged Mongo. You successfully connected to MongoDB!")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")

    @classmethod
    def _initialize_sync_client(cls):
        """Initialize the synchronous MongoDB client."""
        cls._sync_mongo_client = MongoClient(
            MONGO_URL,
            server_api=ServerApi('1')
        )
        cls._sync_mongo_client[MONGO_DATABASE]
        try:
            cls._sync_mongo_client.admin.command('ping')
            print("Pinged Mongo. Synchronous client successfully connected to MongoDB!")
        except Exception as e:
            print(f"Failed to connect to MongoDB (sync): {e}")

    @classmethod
    def get_sync_experiments_collection(cls):
        """Get the experiments collection using the synchronous client."""
        if cls._sync_mongo_client is None:
            raise ValueError("Synchronous MongoDB client is not initialized. Call Mongo.get_client_sync() first.")
        db = cls._sync_mongo_client[MONGO_DATABASE]
        return db['experiments']

    @classmethod
    def get_sync_rsids_collection(cls):
        """Get the rsid collection using the synchronous client."""
        if cls._sync_mongo_client is None:
            raise ValueError("Synchronous MongoDB client is not initialized. Call Mongo.get_client_sync() first.")
        db = cls._sync_mongo_client[MONGO_DATABASE]
        return db['rsid']

    @classmethod
    def get_sync_jobs_collection(cls):
        """Get the rsid collection using the synchronous client."""
        if cls._sync_mongo_client is None:
            raise ValueError("Synchronous MongoDB client is not initialized. Call Mongo.get_client_sync() first.")
        db = cls._sync_mongo_client[MONGO_DATABASE]
        return db['jobs']


    @classmethod
    async def close_client(cls):
        """Close the MongoDB client."""
        if cls._mongo_client is not None:
            cls._mongo_client.close()
            cls._mongo_client = None
            print("MongoDB client closed.")