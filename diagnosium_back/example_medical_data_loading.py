from vector_store import VectorStore

# Initialize the vector store
vector_store = VectorStore()

# Add medical documents from a folder containing PDFs
pdf_folder_path = "c:/Users/islam/Diagnosium/medical_pdfs"
vector_store.add_documents_from_folder(pdf_folder_path, ['.pdf'])

# Build the vector index
vector_store.build_index()

# Test retrieval with a medical query
medical_query = "What are the symptoms of diabetes?"
context = vector_store.retrieve_relevant_context(medical_query, top_k=3)
print(f"\nRelevant medical information for '{medical_query}':")
print(context)
