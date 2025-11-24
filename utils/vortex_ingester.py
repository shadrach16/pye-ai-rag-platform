# from typing import List
from loguru import logger
import os
from dotenv import load_dotenv
import re

load_dotenv()



import textwrap
import chromadb 

import google.generativeai as genai
from chromadb import Documents, EmbeddingFunction, Embeddings

genai.configure(api_key=os.getenv('GEMINI_API_KEY') )
gemini_api_embedding_model = os.getenv("GEMINI_API_EMBEDDING_MODEL")

        


class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        model = f'models/{gemini_api_embedding_model}'
        title = "Custom query"
        return genai.embed_content(model=model,content=input,task_type="retrieval_document",title=title)["embedding"]



class VortexIngester:

        def __init__(self, data_text,collection_name:str):
            print('data_text_check',type(data_text))
            self.documents =   [i for i in re.split('\n\n', data_text) if i.strip()] if type(data_text) ==str else data_text
            self.collection_name = self.clean_str(collection_name)
            self.persist_directory = "./data/chroma"


        def clean_str(self,string):
            pattern = re.compile(r'\s+')
            return re.sub(pattern, '', string)



        def ingest(self) -> None:

            chroma_client = chromadb.PersistentClient(path=self.persist_directory)
            try:
                db = chroma_client.create_collection(name=self.collection_name, embedding_function=GeminiEmbeddingFunction())
                print("Creating new collection")
            except Exception as e:
                print("Already has collection")
                db = chroma_client.get_collection(name=self.collection_name, embedding_function=GeminiEmbeddingFunction()) 
            print(': ',self.collection_name )

            for i, d in enumerate(self.documents):
                print("emebedding: ==> ",i, d,'\n\n')
                db.add(documents=d,ids=str(hash(d)))  

            logger.info("Created Chroma vector store sync")
            # db.persist(persist_directory=self.persist_directory)
            logger.info(f"Persisted Chroma vector store to: {self.collection_name}")
