import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableLambda
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from app.services.vector_store import get_retriever
from app.models import ChatResponse

# Global store for chat history (In production, use Redis)
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


# 1. Initialize Gemini Flash (Fastest for Vercel)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)

# 2. Define the RAG Prompt
template = """Suppose you are a helpful assistant. Sometime you are a HR, Industry Expert, Successful researcher, a good advisor based on requirements. Answer the question based only on the following context:
{context}

Question: {question}
"""
prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=template
)
parser = StrOutputParser()  # Ensures we get a clean string answer without extra formatting

# 3. Helper to format retrieved documents
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

async def get_gemini_response(user_query: str, session_id: str)-> ChatResponse:
    retriever = get_retriever()
    
    # This ensures we fetch docs ONCE and use them for both the LLM and the sources list
    rag_chain = (
        # {"context": retriever | RunnableLambda(format_docs), "question": RunnablePassthrough()}
        RunnablePassthrough.assign(
            context=lambda x: "\n\n".join(d.page_content for d in retriever.invoke(x["question"]))
        )
        | prompt
        | llm
        | parser
    )

    try:
        # answer = await rag_chain.ainvoke(user_query)
        
        # # Get docs for sources
        # docs = await retriever.ainvoke(user_query)
        # sources = [{"page": d.metadata.get("page"), "content": d.page_content[:100]} for d in docs]

        # return {
        #     "answer": answer,
        #     "sources": sources
        # }
        
        with_message_history = RunnableWithMessageHistory(
            rag_chain,
            get_session_history,
            input_messages_key="question",
            history_messages_key="chat_history",
        )

        answer = await with_message_history.ainvoke(
            {"question": user_query},
            config={"configurable": {"session_id": session_id}}
        )
        
        return {"answer": answer, "file_id": session_id}
        
    except Exception as e:
        print(f"LLM Error: {e}")
        raise e