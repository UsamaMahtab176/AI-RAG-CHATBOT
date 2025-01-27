from langchain.tools import BaseTool, Tool
from langchain_openai import OpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
from django.conf import settings
import os

pinecone_api_key = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY=settings.OPENAI_API_KEY

class knowledgebase(BaseTool):
    name ="knowledgebase"
    description = "use this tool for specific question that you have to search from pinecone vectorstore."
    def _run(self, query: str):
      
        index_name = "test"
        embed = OpenAIEmbeddings(
        openai_api_key=OPENAI_API_KEY
        )
        docsearch = PineconeVectorStore.from_existing_index(
            index_name,embed
        )
        # Define your query
        # Initialize the language model
        llm = OpenAI(api_key=OPENAI_API_KEY, temperature=0.8)
        # Create the QA chain
        qa = RetrievalQA.from_chain_type(
            llm=llm, chain_type="stuff", retriever=docsearch.as_retriever()
        )
        # Get the answer
        return qa.invoke(query)