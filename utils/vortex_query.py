from dotenv import load_dotenv
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema import AIMessage, HumanMessage,SystemMessage
from langchain.vectorstores.chroma import Chroma
import json
import jsonpickle
import threading
import os
# from settings import COLLECTION_NAME, PERSIST_DIRECTORY
import re

from langchain.prompts import HumanMessagePromptTemplate,SystemMessagePromptTemplate,ChatPromptTemplate
from utils.vortex_ingester import VortexIngester,GeminiEmbeddingFunction
import chromadb
import google.generativeai as genai
from customer.models import ChatHistory
# from django.contrib.auth.models import User
from django.db import connection

load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
gemini_api_version = os.getenv("GEMINI_API_VERSION")
genai.configure(api_key=gemini_api_key)


CHAT_HISTORY_LEN = -2




def save_chat_history(uuid, content, role, connector,question=""):
    connection.ensure_connection()
    print("Saving ",role)
    ChatHistory.objects.create(uuid=uuid, content=content, role=role, connector=connector,question=question)
    print("Saved")
    connection.close()


class VortexQuery:
	def __init__(self,collection,prompt="You are a Personal AI assistant",uuid=None,save_history=False,chat_history_len=10):
		
		self.model = genai.GenerativeModel(str(gemini_api_version ) )#gemini-1.5-flash  / gemini-1.0-pro

		self.collection = collection
		self.connector = self.collection.connector if hasattr(self.collection,'connector') else self.collection.connection.connector
		
		self.chat_history =  []
		print('save_history',save_history)
		self.uuid = uuid
		if save_history:
			self.chat_history =  [ {"role": hist.role,"parts": [ { "text": hist.content}]}  for hist in ChatHistory.objects.filter(uuid=self.uuid,connector=self.connector).order_by('-pk')[:chat_history_len]]
		self.collection_name = self.clean_str(f"{self.connector.name}_{str(self.connector.created_by)}" )
		self.persist_directory = "./data/chroma"
		self.prompt = prompt


	
	def clean_str(self,string):
		pattern = re.compile(r'\s+')
		return re.sub(pattern, '', string)


	def ask_question(self, question=""):

		chroma_client = chromadb.PersistentClient(path=self.persist_directory)
		dbc = chroma_client.get_collection(name=self.collection_name, embedding_function=GeminiEmbeddingFunction()) 
		relevant_text = ", ".join(dbc.query(query_texts=[question], n_results=5)['documents'][0])
		# relevant_text  = [doc[0] for doc in results['documents']]

		escaped_passage = relevant_text.replace("'", "").replace('"', "").replace("\n", " ")
		prompt = f"""{self.prompt}

		QUESTION: '{question}'
		PASSAGE: '{escaped_passage}'

		ANSWER:
		"""
		# print("PROMPT",prompt)

		thread = threading.Thread(target=save_chat_history, args=(self.uuid, prompt, 'user', self.connector,question))
		thread.start()
		
	
		chat = self.model.start_chat(history = self.chat_history)
		
		chat.send_message(prompt)

		answers = [message.parts[0].text for message in chat.history if message.role =='model']
		thread = threading.Thread(target=save_chat_history, args=(self.uuid, answers[-1], 'model', self.connector,""))
		thread.start()

		

		
		return answers[-1]


