import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

load_dotenv()

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

index_name = os.getenv("PINECONE_INDEX_NAME")

# Create index if it doesn't exist
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=3072, # Specific to models/gemini-embedding-001
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws', 
            region='us-east-1' # Match this to your Vercel deployment region if possible
        )
    )
    print(f"Index '{index_name}' created successfully.")
else:
    print(f"Index '{index_name}' already exists.")
    
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

def get_retriever():
    """Returns the LangChain retriever for the RAG chain."""
    vectorstore = PineconeVectorStore(
        index_name=index_name, 
        embedding=embeddings
    )
    return vectorstore.as_retriever(search_kwargs={"k": 3})
