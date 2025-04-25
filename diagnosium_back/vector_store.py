import json
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import numpy as np

class Document:
    def __init__(self, content: str, metadata: Dict[str, Any] = None):
        self.content = content
        self.metadata = metadata or {}
        self.embedding = None

class VectorStore:
    """Vector database for efficient document retrieval."""

    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        """Initialize the vector store with a specific embedding model."""
        self.documents: List[Document] = []
        self.embedding_model = SentenceTransformer(embedding_model)
        self.index = None
        self.is_index_built = False
    
    def add_document(self, content: str, metadata: Dict[str, Any] = None) -> int:
        """Add a document to the vector store."""
        doc = Document(content, metadata)
        self.documents.append(doc)
        self.is_index_built = False
        return len(self.documents) - 1
    
    def add_documents(self, contents: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> List[int]:
        """Add multiple documents to the vector store."""
        if metadatas is None:
            metadatas = [{} for _ in contents]
        
        indices = []
        for content, metadata in zip(contents, metadatas):
            idx = self.add_document(content, metadata)
            indices.append(idx)
        
        return indices
    
    def embed_documents(self):
        """Embed all documents in the store."""
        texts = [doc.content for doc in self.documents]
        if texts:
            embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
            for doc, emb in zip(self.documents, embeddings):
                doc.embedding = emb
            self.is_index_built = True

    def build_index(self):
        """Build a simple index (matrix of embeddings)."""
        if not self.is_index_built:
            self.embed_documents()
        self.index = np.stack([doc.embedding for doc in self.documents])
        self.is_index_built = True

    def load_medications_from_json(self, json_path: str):
        """Load medications from a JSON file and add them as documents."""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for letter, meds in data.items():
            for med in meds:
                conditioning = med.get("conditioning", "")
                self.add_document(conditioning, metadata={"letter": letter})
        self.embed_documents()
        self.build_index()

    def query(self, case_description: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve top_k relevant medications for a patient case."""
        if not self.is_index_built:
            self.build_index()
        query_emb = self.embedding_model.encode([case_description], convert_to_numpy=True)[0]
        similarities = np.dot(self.index, query_emb) / (
            np.linalg.norm(self.index, axis=1) * np.linalg.norm(query_emb) + 1e-10
        )
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        results = []
        for idx in top_indices:
            doc = self.documents[idx]
            results.append({
                "conditioning": doc.content,
                "metadata": doc.metadata,
                "score": float(similarities[idx])
            })
        return results
