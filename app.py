import streamlit
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import streamlit as st
from langchain_chroma import Chroma
import logging
from assistant import Assistant
from prompts import SYSTEM_PROMPT, WELCOME_MESSAGE
from langchain_groq import ChatGroq
from gui import AssistantGUI

from data.employees import generate_employee_data
import json
from data.employees import generate_employee_data
import json

if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(level=logging.INFO)

    streamlit.set_page_config(page_title="Umbrella Onboarding", page_icon="" ,layout="wide")

    @st.cache_data(ttl=3600, show_spinner="Loading Employee Data...")
    def get_user_data():
        return generate_employee_data(1)[0]


    @st.cache_resource(ttl=3600, show_spinner="Loading Vector Store...")
    def init_vector_store(pdf_path):
        try:
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200
            )
            splits = text_splitter.split_documents(docs)

            embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            persistent_path = "./data/vectorstore"

            vectorstore = Chroma.from_documents(
                documents=splits,
                embedding=embedding_function,
                persist_directory=persistent_path
            )

            return vectorstore
        except Exception as e:
            logging.error(f"Error initializing vector store: {str(e)}")
            st.error(f"Failed to initialize vector store: {str(e)}")
            return None

    customer_data = get_user_data()
    vector_store = init_vector_store("data/umbrella_corp_policies.pdf")
    llm = ChatGroq(model="llama-3.3-70b-versatile")

    if "customer" not in st.session_state:
        st.session_state.customer = customer_data
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "ai", "content": WELCOME_MESSAGE}]

    assistant = Assistant(
        system_prompt=SYSTEM_PROMPT,
        llm=llm,
        message_history=st.session_state.messages,
        employee_information=st.session_state.customer,
        vector_store=vector_store
    )

    gui = AssistantGUI(assistant)
    gui.render()


