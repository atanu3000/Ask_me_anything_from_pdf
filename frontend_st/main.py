import streamlit as st
from utils import check_backend_health, upload_pdf, ask_question, delete_context

# Must be the first Streamlit command
st.set_page_config(page_title="LuminaPDF", layout="centered")

st.title("📄 LuminaPDF")
st.subheader("Ask Me Anything From PDF")

# --- WAKE UP BACKEND ---
if "backend_warm" not in st.session_state:
    with st.spinner("Waking up AI Engine..."):
        if check_backend_health():
            st.session_state.backend_warm = True
        else:
            st.error("Server is offline. Please try refreshing.")
            st.stop()

if st.sidebar.button("🗑️ Clear Session & Wipe Data"):
    if st.session_state.file_id:
        # 1. Call Backend to wipe Cloud & Local File
        if delete_context(st.session_state.file_id):                        
            # 2. CLEAR EVERYTHING
            # This specifically resets the file uploader widget
            if "pdf_uploader_key" in st.session_state:
                del st.session_state["pdf_uploader_key"]
                st.session_state.clear()
                st.rerun()

# Initialize Session States
if "file_id" not in st.session_state:
    st.session_state.file_id = None
if "last_uploaded" not in st.session_state:
    st.session_state.last_uploaded = None

# --- AUTO-INDEXING PDF UPLOADER ---
uploaded_file = st.file_uploader(
    "Drop your PDF here to start chatting", 
    type="pdf", 
    label_visibility="collapsed", 
    key="pdf_uploader_key"
)

# Trigger indexing automatically when a new file is detected
if uploaded_file is not None and uploaded_file.name != st.session_state.last_uploaded:
    with st.status("Indexing your PDF...", expanded=True) as status:
        st.write("Extracting text and creating vectors...")
        result = upload_pdf(uploaded_file)
        if result:
            st.session_state.file_id = result["file_id"]
            st.session_state.last_uploaded = uploaded_file.name
            status.update(label="✅ PDF Indexed Successfully!", state="complete", expanded=False)
        else:
            st.error("Failed to index PDF.")

st.divider()

# --- CHAT INTERFACE ---
# Only show chat if a file has been indexed
# if st.session_state.file_id:
if prompt := st.chat_input("What is in the PDF?"):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = ask_question(prompt, st.session_state.file_id)
            if response:
                st.markdown(response["answer"])
                with st.expander("View Sources"):
                    for src in response.get("sources", []):
                        st.caption(f"Page {src.get('page')}: {src.get('content')}...")
# else:
#     st.info("Upload a PDF above to ask something the chat.")