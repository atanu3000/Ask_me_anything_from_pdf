import os
import io
import tempfile
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv

load_dotenv()

# 1. Setup Embeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", dimensions=32)
index_name = os.getenv("PINECONE_INDEX_NAME")

def verify_pdf_serious(file_content: bytes):
    """Deep verification: checks for encryption, corruption, and malicious JS."""
    try:
        reader = PdfReader(io.BytesIO(file_content))
        if reader.is_encrypted:
            return False, "Encrypted PDFs are blocked for security."
        
        # Check for common PDF malware vectors (JavaScript/Auto-actions)
        catalog = reader.trailer.get("/Root", {})
        if any(key in catalog for key in ["/OpenAction", "/JS", "/JavaScript"]):
            return False, "Security Alert: Embedded scripts detected."
            
        if len(reader.pages) == 0:
            return False, "The PDF appears to be empty."
            
        return True, "Valid"
    except PdfReadError:
        return False, "Corrupted PDF structure."

async def process_and_index_pdf(file_content: bytes, filename: str, file_id: str):
    """The full pipeline: Verify -> Split -> Pinecone Index."""
    
    # --- STEP 1: SERIOUS VERIFICATION ---
    # is_valid, message = verify_pdf_serious(file_content)
    # if not is_valid:
    #     print(f"Security Block: {message}")
    #     return False, message

    # --- STEP 2: LOAD & SPLIT ---
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        loader = PyPDFLoader(tmp_path)
        docs = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(docs)

        # --- STEP 3: METADATA TAGGING (Crucial for Deletion) ---
        for chunk in chunks:
            chunk.metadata.update({
                "file_id": file_id, # Used to delete everything for this session later
                "filename": filename
            })

        # --- STEP 4: PINECONE LOGIC ---
        PineconeVectorStore.from_documents(
            chunks, 
            embeddings, 
            index_name=index_name
        )

        os.remove(tmp_path)
        return True, "Success"
    except Exception as e:
        print(f"Indexing Error: {e}")
        return False, str(e)