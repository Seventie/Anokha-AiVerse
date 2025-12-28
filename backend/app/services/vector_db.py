# backend/app/services/vector_db.py

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class VectorDBService:
    def __init__(self):
        """Initialize ChromaDB and embedding model"""
        self.client = None
        self.embedding_model = None
        self.collection = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization of vector DB"""
        if self._initialized:
            return
        
        try:
            self.client = chromadb.Client(
                ChromaSettings(
                    persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
                    anonymized_telemetry=False
                )
            )
            
            # Load embedding model from Hugging Face
            self.embedding_model = SentenceTransformer(settings.HUGGINGFACE_MODEL)
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"description": "Career memory context store"}
            )
            
            self._initialized = True
            logger.info(f"Initialized VectorDB with collection: {settings.CHROMA_COLLECTION_NAME}")
        except Exception as e:
            logger.warning(f"VectorDB initialization failed: {e}. Vector features will be disabled.")
            self._initialized = False
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Hugging Face model"""
        self._ensure_initialized()
        if not self.embedding_model:
            raise RuntimeError("VectorDB not initialized")
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def add_context(
        self,
        user_id: str,
        text: str,
        metadata: Dict[str, Any],
        doc_id: Optional[str] = None
    ) -> str:
        """
        Add contextual text to vector database
        
        Args:
            user_id: User identifier
            text: Context text to embed
            metadata: Additional metadata (source, confidence, timestamp, etc.)
            doc_id: Optional document ID, generated if not provided
        
        Returns:
            Document ID
        """
        if not doc_id:
            import uuid
            doc_id = f"{user_id}_{metadata.get('source', 'unknown')}_{uuid.uuid4().hex[:8]}"
        
        # Add user_id to metadata
        metadata["user_id"] = user_id
        
        # Generate embedding
        embedding = self.generate_embedding(text)
        
        # Add to collection
        self._ensure_initialized()
        if not self.collection:
            raise RuntimeError("VectorDB not initialized")
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )
        
        logger.info(f"Added context for user {user_id}: {doc_id}")
        return doc_id
    
    def add_resume_context(self, user_id: str, resume_text: str):
        """Add raw resume text to vector store"""
        self.add_context(
            user_id=user_id,
            text=resume_text,
            metadata={
                "source": "resume_raw",
                "type": "resume",
                "generated": False,
                "confidence": 1.0
            }
        )
    
    def add_project_context(self, user_id: str, project_id: int, description: str):
        """Add project description to vector store"""
        self.add_context(
            user_id=user_id,
            text=description,
            metadata={
                "source": "project",
                "type": "project",
                "project_id": project_id,
                "generated": False,
                "confidence": 1.0
            }
        )
    
    def add_experience_context(self, user_id: str, exp_id: int, description: str):
        """Add experience description to vector store"""
        self.add_context(
            user_id=user_id,
            text=description,
            metadata={
                "source": "experience",
                "type": "experience",
                "experience_id": exp_id,
                "generated": False,
                "confidence": 1.0
            }
        )
    
    def add_career_intent(self, user_id: str, intent_text: str):
        """Add career intent/vision statement - HIGH PRIORITY for semantic matching"""
        self.add_context(
            user_id=user_id,
            text=intent_text,
            metadata={
                "source": "career_intent",
                "type": "career_goal",
                "generated": False,
                "confidence": 1.0,
                "priority": "high"
            }
        )
    
    def add_generated_context(
        self,
        user_id: str,
        text: str,
        source: str,
        confidence: float = 0.7
    ):
        """Add AI-generated context (flagged as generated)"""
        self.add_context(
            user_id=user_id,
            text=text,
            metadata={
                "source": source,
                "type": "generated_summary",
                "generated": True,
                "confidence": confidence
            }
        )
    
    def semantic_search(
        self,
        query: str,
        user_id: Optional[str] = None,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search across vector database
        
        Args:
            query: Search query text
            user_id: Optional filter by user
            n_results: Number of results to return
            filter_metadata: Additional metadata filters
        
        Returns:
            List of matching documents with metadata
        """
        # Generate query embedding
        query_embedding = self.generate_embedding(query)
        
        # Build filter
        where_filter = {}
        if user_id:
            where_filter["user_id"] = user_id
        if filter_metadata:
            where_filter.update(filter_metadata)
        
        # Search
        self._ensure_initialized()
        if not self.collection:
            raise RuntimeError("VectorDB not initialized")
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter if where_filter else None
        )
        
        # Format results
        formatted_results = []
        if results and results["ids"]:
            for i, doc_id in enumerate(results["ids"][0]):
                formatted_results.append({
                    "id": doc_id,
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None
                })
        
        return formatted_results
    
    def match_job_description(
        self,
        user_id: str,
        job_description: str,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Match job description against user's career memory
        Returns most relevant context from resume, projects, experience, and career intent
        """
        return self.semantic_search(
            query=job_description,
            user_id=user_id,
            n_results=n_results
        )
    
    def delete_user_contexts(self, user_id: str):
        """Delete all contexts for a user"""
        self._ensure_initialized()
        if not self.collection:
            logger.warning("VectorDB not initialized, skipping delete")
            return
        # ChromaDB delete by metadata filter
        results = self.collection.get(where={"user_id": user_id})
        if results and results["ids"]:
            self.collection.delete(ids=results["ids"])
            logger.info(f"Deleted {len(results['ids'])} contexts for user {user_id}")
    
    def update_context(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        """Update existing context"""
        self._ensure_initialized()
        if not self.collection:
            raise RuntimeError("VectorDB not initialized")
        embedding = self.generate_embedding(text)
        self.collection.update(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )
        logger.info(f"Updated context: {doc_id}")

# =========================
# LAZY SINGLETON (SAFE)
# =========================
_vector_db: Optional[VectorDBService] = None


def get_vector_db() -> VectorDBService:
    """Lazy-load vector database instance"""
    global _vector_db
    if _vector_db is None:
        _vector_db = VectorDBService()
    return _vector_db

# Export both function and instance for compatibility
vector_db = get_vector_db()