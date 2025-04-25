import os
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
# import PyPDF2  # Add this import for PDF processing

class Document:
    """Document class to store text and metadata."""
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
    
    # def extract_text_from_pdf(self, pdf_path: str) -> str:
    #     """Extract text content from a PDF file."""
    #     try:
    #         text = ""
    #         with open(pdf_path, 'rb') as file:
    #             reader = PyPDF2.PdfReader(file)
    #             for page_num in range(len(reader.pages)):
    #                 page = reader.pages[page_num]
    #                 text += page.extract_text() + "\n\n"
    #         return text
    #     except Exception as e:
    #         print(f"Error extracting text from PDF {pdf_path}: {e}")
    #         return ""
    
    def add_documents_from_folder(self, folder_path: str, file_extensions: List[str] = ['.txt', '.md', '.pdf']) -> int:
        """Load documents from text files and PDFs in a folder."""
        added_count = 0
        try:
            for filename in os.listdir(folder_path):
                filepath = os.path.join(folder_path, filename)
                
                try:
                    content = ""
                    if filename.lower().endswith('.pdf'):
                        content = self.extract_text_from_pdf(filepath)
                    elif any(filename.endswith(ext) for ext in [ext for ext in file_extensions if ext != '.pdf']):
                        with open(filepath, 'r', encoding='utf-8') as file:
                            content = file.read()
                    else:
                        continue  # Skip files with unsupported extensions
                    
                    if content.strip():  # Only add if content is not empty
                        self.add_document(content, {"source": filepath, "filename": filename})
                        added_count += 1
                except Exception as e:
                    print(f"Error processing file {filepath}: {e}")
        except Exception as e:
            print(f"Error accessing folder {folder_path}: {e}")
        
        print(f"Added {added_count} documents to vector store")
        return added_count
    
    def build_index(self):
        """Compute embeddings and build the FAISS index."""
        if not self.documents:
            print("No documents to index")
            return
        
        # Compute embeddings for all documents
        contents = [doc.content for doc in self.documents]
        embeddings = self.embedding_model.encode(contents)
        
        # Store embeddings in documents
        for i, doc in enumerate(self.documents):
            doc.embedding = embeddings[i]
        
        # Build FAISS index
        vector_dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(vector_dimension)
        self.index.add(np.array(embeddings).astype('float32'))
        self.is_index_built = True
        print(f"Built index with {len(self.documents)} documents")
    
    def retrieve_relevant_documents(self, query: str, top_k: int = 3) -> List[Document]:
        """Retrieve the most relevant documents for a query using vector similarity."""
        if not self.is_index_built:
            self.build_index()
        
        if not self.documents:
            return []
        
        # Compute query embedding
        query_embedding = self.embedding_model.encode([query])[0]
        
        # Search for similar documents
        distances, indices = self.index.search(
            np.array([query_embedding]).astype('float32'), 
            min(top_k, len(self.documents))
        )
        
        # Return the relevant documents
        return [self.documents[idx] for idx in indices[0]]
    
    def retrieve_relevant_context(self, query: str, top_k: int = 3) -> str:
        """Retrieve and format relevant documents as context string."""
        relevant_docs = self.retrieve_relevant_documents(query, top_k)
        
        if not relevant_docs:
            return ""
        
        # Combine content from relevant documents
        context_parts = []
        for doc in relevant_docs:
            metadata_str = ""
            if doc.metadata:
                metadata_str = " (" + ", ".join(f"{k}: {v}" for k, v in doc.metadata.items()) + ")"
            context_parts.append(f"{doc.content}{metadata_str}")
        
        return "\n\n---\n\n".join(context_parts)
