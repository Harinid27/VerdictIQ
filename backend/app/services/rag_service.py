import os
import logging
import math
from typing import List, Dict, Any
from datetime import datetime
import google.generativeai as genai

from app.database import get_collection

logger = logging.getLogger(__name__)

# Config
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
IS_MOCK_GEMINI = not GEMINI_API_KEY or GEMINI_API_KEY == "placeholder_key"

if GEMINI_API_KEY and not IS_MOCK_GEMINI:
    genai.configure(api_key=GEMINI_API_KEY)

class RAGService:
    """
    Production RAG Service for VerdictIQ.
    Supports Parent-Child Hierarchical Chunking, Text Embeddings,
    Vector Indexing in MongoDB, and Hybrid Semantic Retrieval.
    """

    @staticmethod
    def chunk_document(text: str, parent_size: int = 2000, parent_overlap: int = 400,
                       child_size: int = 400, child_overlap: int = 100) -> List[Dict[str, str]]:
        """
        Performs Parent-Child Hierarchical Chunking.
        Returns a list of dicts: {"parent": str, "child": str}
        """
        if not text:
            return []

        chunks = []
        text_len = len(text)
        
        # 1. Create Parent Chunks
        parent_start = 0
        while parent_start < text_len:
            parent_end = min(parent_start + parent_size, text_len)
            parent_text = text[parent_start:parent_end]
            
            # 2. Slice Parent Chunk into Child Chunks
            child_start = 0
            parent_len = len(parent_text)
            while child_start < parent_len:
                child_end = min(child_start + child_size, parent_len)
                child_text = parent_text[child_start:child_end]
                
                chunks.append({
                    "parent": parent_text,
                    "child": child_text
                })
                
                child_start += child_size - child_overlap
                
            parent_start += parent_size - parent_overlap
            
        return chunks

    @staticmethod
    def get_embeddings(texts: List[str]) -> List[List[float]]:
        """
        Generates embedding vectors for list of texts using Google text-embedding-004 model.
        Falls back to dummy zero-vectors on mock or error.
        """
        if IS_MOCK_GEMINI or not texts:
            logger.info("RAG: Using dummy embeddings (mock engine active).")
            return [[0.0] * 768 for _ in texts]

        # Configure pipeline API key dynamically for embeddings
        pipeline_key = os.getenv("PIPELINE_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if pipeline_key:
            genai.configure(api_key=pipeline_key)

        try:
            # Clean empty elements
            cleaned_texts = [t if t.strip() else "[empty]" for t in texts]
            result = genai.embed_content(
                model="models/text-embedding-004",
                contents=cleaned_texts,
                task_type="retrieval_document"
            )
            # The API returns dict containing a list under 'embedding'
            embeddings = result.get('embedding')
            if embeddings:
                return embeddings
            else:
                raise ValueError("No embeddings returned in response dict.")
        except Exception as e:
            logger.error(f"Failed to generate Gemini embeddings: {e}. Falling back to zeros.")
            return [[0.0] * 768 for _ in texts]

    @staticmethod
    def get_query_embedding(query: str) -> List[float]:
        """
        Generates embedding vector for search query.
        """
        if IS_MOCK_GEMINI or not query:
            return [0.0] * 768

        # Configure pipeline API key dynamically for embeddings
        pipeline_key = os.getenv("PIPELINE_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if pipeline_key:
            genai.configure(api_key=pipeline_key)

        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                contents=query,
                task_type="retrieval_query"
            )
            embeddings = result.get('embedding')
            if embeddings and len(embeddings) > 0:
                # Returns single list if contents was a single string
                return embeddings[0] if isinstance(embeddings[0], list) else embeddings
            return [0.0] * 768
        except Exception as e:
            logger.error(f"Failed to generate Gemini query embedding: {e}.")
            return [0.0] * 768

    @staticmethod
    async def index_document(file_id: str, text: str, workspace_id: str, file_name: str, 
                             evidence_type: str = "Document", importance_level: str = "Important") -> bool:
        """
        Processes document: chunking, embedding generation, and saving into evidence_chunks collection.
        """
        logger.info(f"RAG: Indexing document {file_id} ({file_name}) for workspace {workspace_id}...")
        
        # 1. Clear existing chunks for this file to prevent duplicates
        chunks_col = get_collection("evidence_chunks")
        await chunks_col.delete_many({"file_id": file_id, "workspace_id": workspace_id})

        # 2. Chunk the text
        hierarchical_chunks = RAGService.chunk_document(text)
        if not hierarchical_chunks:
            logger.info("RAG: Document text is empty, nothing to index.")
            return True

        # Extract child texts to generate batch embeddings
        child_texts = [c["child"] for c in hierarchical_chunks]
        
        # Batch embeddings in chunks of 50 to avoid payload limits
        batch_size = 50
        embeddings = []
        for i in range(0, len(child_texts), batch_size):
            batch = child_texts[i:i+batch_size]
            batch_embs = RAGService.get_embeddings(batch)
            embeddings.extend(batch_embs)

        # 3. Create database records
        db_records = []
        for idx, item in enumerate(hierarchical_chunks):
            db_records.append({
                "workspace_id": workspace_id,
                "file_id": file_id,
                "file_name": file_name,
                "evidence_type": evidence_type,
                "importance_level": importance_level,
                "parent_chunk": item["parent"],
                "child_chunk": item["child"],
                "embedding": embeddings[idx],
                "created_at": datetime.utcnow()
            })

        if db_records:
            await chunks_col.insert_many(db_records)
            logger.info(f"RAG: Successfully indexed {len(db_records)} child-parent chunks for file {file_name}")
            return True
        return False

    @staticmethod
    def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        mag1 = math.sqrt(sum(a * a for a in v1))
        mag2 = math.sqrt(sum(b * b for b in v2))
        if mag1 * mag2 == 0:
            return 0.0
        return dot / (mag1 * mag2)

    @staticmethod
    async def retrieve_relevant_context(query: str, workspace_id: str, top_k: int = 5) -> str:
        """
        Retrieves relevant parent chunks based on query-to-child similarity, prioritizing important files.
        Resilient: works via Python similarity computation if MongoDB Vector Search index is not present.
        """
        logger.info(f"RAG: Querying context for: {query[:60]} in workspace {workspace_id}...")
        
        chunks_col = get_collection("evidence_chunks")
        
        # Fetch all chunks in this workspace
        cursor = chunks_col.find({"workspace_id": workspace_id})
        all_chunks = await cursor.to_list(length=1000)
        
        if not all_chunks:
            logger.info("RAG: No chunks indexed for this workspace. Returning empty context.")
            return ""

        # Generate query embedding
        query_emb = RAGService.get_query_embedding(query)
        
        scored_chunks = []
        for c in all_chunks:
            emb = c.get("embedding")
            if not emb or all(x == 0.0 for x in emb):
                # Fallback to keyword matching if no embeddings
                similarity = 0.1
                if query.lower() in c.get("child_chunk", "").lower():
                    similarity = 0.5
            else:
                similarity = RAGService._cosine_similarity(query_emb, emb)

            # Metadata priorities
            importance = c.get("importance_level", "Important")
            importance_weight = 1.0
            if importance == "Critical":
                importance_weight = 1.5
            elif importance == "Important":
                importance_weight = 1.0
            elif importance == "Reference":
                importance_weight = 0.5
                
            # Score formula: similarity * importance_weight
            score = similarity * importance_weight
            scored_chunks.append((score, c))

        # Sort by score desc
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = scored_chunks[:top_k]
        
        # Assemble deduplicated parent chunks
        assembled_parents = []
        seen_parents = set()
        for score, c in top_chunks:
            parent = c.get("parent_chunk", "")
            if parent and parent not in seen_parents:
                seen_parents.add(parent)
                file_name = c.get("file_name", "Unknown File")
                imp = c.get("importance_level", "Important")
                assembled_parents.append(f"--- Exhibit ({file_name}), Importance: {imp} ---\n{parent}")

        retrieved_context = "\n\n".join(assembled_parents)
        logger.info(f"RAG: Retrieved {len(assembled_parents)} parent context chunks.")
        return retrieved_context
