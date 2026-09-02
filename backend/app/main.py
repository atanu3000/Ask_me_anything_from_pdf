import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import ChatRequest, ChatResponse, UploadResponse
from app.services import get_gemini_response, process_and_index_pdf
from app.services.vector_store import pc, index_name
import uuid
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="LuminaPDF API")

# --- CORS SETUP ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with your streamlit URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PORT = os.getenv("PORT", 8000)

# --- HEALTH CHECK ---
@app.get("/health")
async def health_check():
    return {"status": "online", "message": "LuminaPDF Engine is warm", "port": PORT}

# --- API ENDPOINTS ---
# Upload endpoint to receive PDF files
@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    print(file)
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    # Generate a unique ID for this document session
    file_id = str(uuid.uuid4())
    
    # Save file temporarily and process it
    # Note: In a real app, you'd stream this to S3 or a temp folder
    content = await file.read()
    
    # Trigger the LangChain indexing process
    success = await process_and_index_pdf(content, file.filename, file_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to process PDF.")

    return {
        "filename": file.filename,
        "file_id": file_id,
        "status": "success",
        "message": "PDF indexed and ready for chat!"
    }


# Chat endpoint to interact with the PDF content
@app.post("/chat", response_model=ChatResponse)
async def chat_with_pdf(request: ChatRequest):
    try:
        # Get answer from Gemini using our RAG service
        print(f"Received question: {request.message} for file_id: {request.file_id}")
        response = await get_gemini_response(request.message, request.file_id)
        return response
        
    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str("Error occurred in Gemini response: " + str(e)))


@app.delete("/clear-session/{file_id}")
async def clear_session(file_id: str):
    # This wipes every chunk belonging to that specific PDF/User session
    index = pc.Index(index_name)
    index.delete(filter={"file_id": {"$eq": file_id}})        
    return {"status": "success", "message": "Context successfully wiped from cloud storage."}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)

# To run the app, use the following command in your terminal:
# ...\LuminaPDF\backend> uvicorn app.main:app --reload