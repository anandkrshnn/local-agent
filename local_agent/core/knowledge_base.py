"""
Advanced RAG Knowledge Base with ChromaDB
Enables document ingestion and semantic search
"""

import os
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid
from collections import OrderedDict

try:
    import chromadb
    from chromadb.utils import embedding_functions
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()

    def __getitem__(self, key):
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]

    def __setitem__(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    def __contains__(self, key):
        return key in self.cache

class KnowledgeBase:
    """
    Hybrid Knowledge Base for RAG (Retrieval-Augmented Generation)
    Combines Vector Search (ChromaDB) with Keyword Search (BM25) using RRF.
    """
    
    def __init__(self, persist_directory: str = "./knowledge_base"):
        self.persist_directory = persist_directory
        self.collection_name = "documents"
        self.query_cache = LRUCache(capacity=100)
        
        if HAS_CHROMADB:
            self.client = chromadb.PersistentClient(path=persist_directory)
            self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
            
            try:
                self.collection = self.client.get_collection(self.collection_name)
            except:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_fn
                )
        else:
            self.client = None
            self.collection = None
            print("⚠️ Knowledge base disabled - ChromaDB not installed")
        
        # Initialize BM25
        self.bm25 = None
        self.bm25_docs = []
        self._refresh_bm25()
    
    def ingest_text(self, text: str, metadata: Dict = None, doc_id: str = None) -> str:
        """
        Ingest a text document into the knowledge base
        
        Args:
            text: Document text content
            metadata: Additional metadata (source, date, etc.)
            doc_id: Optional document ID (auto-generated if not provided)
        
        Returns:
            Document ID
        """
        if not self.collection:
            return None
        
        doc_id = doc_id or str(uuid.uuid4())
        metadata = metadata or {}
        metadata['source_type'] = 'text'
        
        # Split into chunks for better retrieval
        chunks = self._chunk_text(text)
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            chunk_metadata = metadata.copy()
            chunk_metadata['chunk_index'] = i
            chunk_metadata['total_chunks'] = len(chunks)
            
            self.collection.add(
                documents=[chunk],
                metadatas=[chunk_metadata],
                ids=[chunk_id]
            )
        
        self._refresh_bm25()
        return doc_id
    
    def ingest_file(self, file_path: str, metadata: Dict = None) -> str:
        """
        Ingest a file into the knowledge base
        
        Supported formats: .txt, .md, .json, .csv, .pdf (requires extra deps)
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read file based on extension
        if file_path.suffix in ['.txt', '.md', '.py', '.js', '.html', '.css']:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif file_path.suffix == '.json':
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                content = json.dumps(data, indent=2)
        else:
            # For unsupported formats, try reading as text
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        metadata = metadata or {}
        metadata['source'] = str(file_path)
        metadata['filename'] = file_path.name
        metadata['source_type'] = 'file'
        
        return self.ingest_text(content, metadata)
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Wraps hybrid search with caching"""
        cache_key = f"{query}:{n_results}"
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]
        
        results = self.search_hybrid(query, n_results)
        self.query_cache[cache_key] = results
        return results

    def search_hybrid(self, query: str, n_results: int = 5, k: int = 60) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF) for Vector + BM25 search
        score = sum(1 / (k + rank))
        """
        # 1. Vector Search
        vector_results = []
        if self.collection:
            try:
                v_res = self.collection.query(query_texts=[query], n_results=n_results)
                if v_res['documents'] and v_res['documents'][0]:
                    for i, doc in enumerate(v_res['documents'][0]):
                        vector_results.append({
                            'content': doc,
                            'metadata': v_res['metadatas'][0][i] if v_res['metadatas'] else {},
                            'id': v_res['ids'][0][i]
                        })
            except Exception as e:
                print(f"Vector search error: {e}")

        # 2. BM25 Search
        bm25_results = []
        if HAS_BM25 and self.bm25:
            try:
                tokenized_query = query.lower().split()
                scores = self.bm25.get_scores(tokenized_query)
                # Get top indices
                top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n_results]
                for idx in top_indices:
                    if scores[idx] > 0:
                        bm25_results.append(self.bm25_docs[idx])
            except Exception as e:
                print(f"BM25 search error: {e}")

        # 3. Reciprocal Rank Fusion
        rrf_scores = {}
        for rank, res in enumerate(vector_results):
            doc_id = res['id']
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        
        for rank, res in enumerate(bm25_results):
            doc_id = res['id']
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (k + rank + 1)

        # 4. Sort and return
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:n_results]
        
        # Combine data
        final_results = []
        all_res = {res['id']: res for res in vector_results + bm25_results}
        for doc_id in sorted_ids:
            final_results.append(all_res[doc_id])
            
        return final_results

    def _refresh_bm25(self):
        """Rebuild the BM25 index from all documents in ChromaDB"""
        if not HAS_BM25 or not self.collection:
            return
            
        try:
            db_res = self.collection.get()
            self.bm25_docs = []
            corpus = []
            
            for i, doc in enumerate(db_res['documents']):
                self.bm25_docs.append({
                    'id': db_res['ids'][i],
                    'content': doc,
                    'metadata': db_res['metadatas'][i]
                })
                corpus.append(doc.lower().split())
            
            if corpus:
                self.bm25 = BM25Okapi(corpus)
        except Exception as e:
            print(f"BM25 refresh error: {e}")
    
    def get_context_for_prompt(self, query: str, max_chunks: int = 3) -> str:
        """
        Get relevant context to inject into a prompt
        
        Returns:
            Formatted context string for RAG
        """
        results = self.search(query, n_results=max_chunks)
        
        if not results:
            return ""
        
        context = "## Relevant Context from Knowledge Base:\n\n"
        for i, result in enumerate(results):
            context += f"[{i+1}] {result['content'][:500]}\n\n"
        
        return context
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks for better retrieval"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk = ' '.join(chunk_words)
            chunks.append(chunk)
            
            if i + chunk_size >= len(words):
                break
        
        return chunks
    
    def list_documents(self) -> List[Dict]:
        """List all documents in the knowledge base"""
        if not self.collection:
            return []
        
        # Get unique documents by their root ID
        all_docs = self.collection.get()
        documents = {}
        
        for i, doc_id in enumerate(all_docs['ids']):
            root_id = doc_id.split('_chunk_')[0]
            if root_id not in documents:
                documents[root_id] = {
                    'id': root_id,
                    'chunks': 1,
                    'metadata': all_docs['metadatas'][i] if all_docs['metadatas'] else {}
                }
            else:
                documents[root_id]['chunks'] += 1
        
        return list(documents.values())
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the knowledge base"""
        if not self.collection:
            return False
        
        # Delete all chunks with this prefix
        all_docs = self.collection.get()
        to_delete = [id for id in all_docs['ids'] if id.startswith(doc_id)]
        
        if to_delete:
            self.collection.delete(ids=to_delete)
            return True
        
        return False
    
    def get_stats(self) -> Dict:
        """Get knowledge base statistics"""
        if not self.collection:
            return {"enabled": False}
        
        try:
            count = self.collection.count()
            return {
                "enabled": True,
                "total_chunks": count,
                "total_documents": len(self.list_documents()),
                "persist_directory": self.persist_directory
            }
        except:
            return {"enabled": False, "error": "Unable to fetch stats"}

# Singleton instance
knowledge_base = KnowledgeBase()
