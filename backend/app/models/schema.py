from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    file_id: Optional[str] = None  # To chat with a specific PDF if needed

class Source(BaseModel):
    page: Optional[int] = None
    content: str
    metadata: Optional[dict] = None

class ChatResponse(BaseModel):
    answer: str
    # sources: List[Source]
    file_id: str
    
class UploadResponse(BaseModel):
    filename: str
    file_id: str
    status: str
    message: str