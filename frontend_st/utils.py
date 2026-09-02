import requests
import streamlit as st

# Update this to your Vercel URL once deployed
# BASE_URL = "http://127.0.0.1:8000" 
BASE_URL = "https://ask-me-anything-from-pdf.onrender.com" 

def check_backend_health():
    """Wakes up the Vercel serverless function."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def upload_pdf(file):
    """Sends the PDF file to the FastAPI /upload endpoint."""
    try:
        files = {"file": (file.name, file.getvalue(), "application/pdf")}
        response = requests.post(f"{BASE_URL}/upload", files=files)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error uploading file: {e}")
        return None

def ask_question(message, file_id):
    """Sends the user's question to the FastAPI /chat endpoint."""
    try:
        payload = {
            "message": message,
            "file_id": str(file_id)
        }
        response = requests.post(f"{BASE_URL}/chat", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error getting response: {e}")
        return None
    
    
def delete_context(file_id):
    """This funtion helps to delete the context from the pinecone vector store
    """
    try:
        requests.delete(f"{BASE_URL}/clear-session/{file_id}")
        return True
    except Exception as e:
        st.error(f"Error getting response: {e}")
        return None
    