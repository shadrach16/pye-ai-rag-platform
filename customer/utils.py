from django.core.serializers.json import DjangoJSONEncoder
from utils.connectors import pick_connector
from customer.models import Running_Jobs
import sys
import os
import random
import string
import datetime as dt
from datetime import datetime 
import time
from apscheduler.schedulers.background import BackgroundScheduler
import io
import json
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from django.conf import settings
from sqlalchemy import create_engine
import logging
import traceback
import threading

logging.basicConfig(filename='etl.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

 
jobstores = {
	'default': SQLAlchemyJobStore(url='sqlite:///' + str(settings.DATABASES['default']['NAME']))
}


# create database connection
engine = create_engine('sqlite:///' + str(settings.DATABASES['default']['NAME']))

class PyeScheduler():
	def __init__(self):
		self.scheduler = BackgroundScheduler(jobstores=jobstores) 

	# define a function to pause a job
	def pause_job(self,task):
		# query = f"UPDATE apscheduler_jobs SET next_run_time = NULL WHERE id = '{task.job_id}'"
		# with engine.connect() as conn:
		# 	result = conn.execute(query)
		logging.info(f"Job with ID {task.job_id} paused")
		task.status = "paused"
		task.save()
		return
		logging.exception(f"Nos job found with ID {task.job_id}")	 # define a function to pause a job

	# define a function to remove a job
	def remove_job(self,task):
		# query = f"DELETE FROM apscheduler_jobs WHERE id ='{task.job_id}'"
		# with engine.connect() as conn:
		# 	result = conn.execute(query)
		logging.info(f"Job with ID {task.job_id} removed")
		task.status = "stopped"
		task.save()
		return
		logging.exception(f"Nos job found with ID {task.job_id}") 

	# define a function to resume a job
	def resume_job(self,task):

		# query = f"UPDATE apscheduler_jobs SET next_run_time = 'next_run_time', job_state = 'running' WHERE id = '{task.job_id}'"
		# with engine.connect() as conn:
		# 	result = conn.execute(query)
		logging.info(f"Job with ID {task.job_id} resumed")
		task.status = "running"
		task.save()
		return
		logging.exception(f"No job found with ID {task.job_id}")  

	# define a function to stop a job
	def stop_job(self,task):
		# query = f"UPDATE apscheduler_jobs SET next_run_time = NULL, job_state = 'stopped' WHERE id = '{task.job_id}'"
		# with engine.connect() as conn:
		# 	result = conn.execute(query)
		logging.info(f"Job with ID {task.job_id} stopped")
		task.status = "stopped"
		task.save()
		return
		logging.exception(f"No job found with ID {task.job_id}") 

	

	# define the job scheduling function
	def schedule_job(self,task):	
		# print(task)
		# try:
		# 	get_run = Running_Jobs.objects.get(task=task)
		# except ObjectDoesNotExist:
		# 	create_run = Running_Jobs.objects.create(task)
		task.status='running'
		task.save()

		if task.schedule_time == 'hourly':
			new_job = self.scheduler.add_job(transformer_function, 'interval', minutes=int(task.minute_time), args=[task], jobstore='default')
		elif task.schedule_time == 'daily':
			new_job = self.scheduler.add_job(transformer_function, 'cron', hour=task.daily_time.hour, minute=task.daily_time.minute, args=[task], jobstore='default')
		elif task.schedule_time == 'weekly':
			new_job = self.scheduler.add_job(
				transformer_function,
				'cron',
				hour=task.weekly_time.hour,
				minute=task.weekly_time.minute,
				day_of_week=task.weekly_day,
				day="*", args=[task], jobstore='default'
			)
		else:
			logging.info(f"Instant Job Created, Running...")
			task.status = "running"
			task.save()
			thread = threading.Thread(target=transformer_function, args=(task,))
			thread.start()
			print('dfdf current')

		if task.schedule_time in ["hourly",'daily','weekly']:
			logging.info(f"Job with ID: {new_job.id} scheduled")
			task.job_id = new_job.id
			task.status = "running"
			task.save()
			jobs = self.scheduler.get_jobs(jobstore='default')
			self.scheduler.start()
			print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

			try:
				 # This is here to simulate application activity (which keeps the main thread alive).
				 while True:
					 time.sleep(2)
			except (KeyboardInterrupt, SystemExit):
				 # Not strictly necessary if daemonic mode is enabled but should be done if possible
				 self.scheduler.shutdown()



def transformer_function(task):
	try:
		setup_job(task)
		task.status='stopped'
		task.save()
	except Exception as e:
		logging.exception(e)
		task.status='error'
		task.save()

def my_setup_function(task):
	try:
		setup_job(task)
	except Exception as e:
		logging.exception(e)

def run_transform_code(transformer, transform_data, initial_data={}):
	code_str = transformer.code
	result = transform_data
	global source_data
	source_data = initial_data
	# compile the code string
	compiled = compile(code_str, '<string>', 'exec')
	# execute the code in a new namespace
	namespace = {}
	exec(compiled, namespace)
	# check if main function exists in namespace
	if 'main' in namespace:
		# call main function with data argument
		try:
			result = namespace['main'](transform_data)
			return result
		except Exception as e:
			traceback.print_exc()
			raise Exception(e)
	else:
		raise ValueError('No main function found in code') 


def setup_job(task):
	data = {}
	# get all source connection and data 
	source = task.source.all()

	for connector in source:
		con = pick_connector(connector,task)
		source_data = con.get()

		targets = task.targets.all()
		for target in targets:
			con = pick_connector(target,task)
			con.post(source_data)

			


	# logging.info(f'source_data: {str(data)}')

	# send source_data to transformer for modification
	# transform_data = data
	# transformers = task.transformers.all() 
	# # logging.exception(f"Transformer Data: {transform_data}")
	# for transformer in transformers:   
	# 	try:
	# 		transform_data = run_transform_code(transformer,transform_data,initial_data=data)
	# 	except Exception as e:
	# 		logging.exception(f"Transformer Error: {e}")
	# 		task.status='error'
	# 		task.error = str(e)
	# 		task.save()
	# 		query = f"UPDATE apscheduler_jobs SET next_run_time = NULL, job_state = 'stopped' WHERE id = '{task.job_id}'"
	# 		with engine.connect() as conn:
	# 			result = conn.execute(query)

	# 		raise Exception(e)


	# print('transform_data',transform_data)
	# post transform data to targets for update
	# targets = task.targets.all()
	# if isinstance(data, dict ):
	# 	data_keys = list(transform_data.keys())
	# 	targets_in_data = targets.filter(name__in=data_keys)
	# 	if len(targets_in_data):
	# 		# Data key Name must equal target connector Name
	# 		for key_name in data_keys:
	# 			target_model = targets.objects.get(name=key_name)
	# 			con = pick_connector(target_model,task)
	# 			con.post(transform_data[key_name])

	# 	else:
	# 		for target in targets:
	# 			con = pick_connector(target,task)
	# 			con.post(transform_data)
	# 		# print('dfdf12ferws')
 
	# else:
	# 	for target in targets:
	# 		con = pick_connector(target,task)
	# 		# print('train con',con)
	# 		con.post(transform_data)
 
 




class MyJsonEncoder(DjangoJSONEncoder):
	def default(self, o):
		if isinstance(o, InMemoryUploadedFile):
		   return o.read()
		return str(o)


def get_day(day):
	days = {'sun':0,'mon':1,'tue':2,"wed":3,"thu":4,"fri":5,"sat":6}
	return days[day]


class Connector():
	name =  ""
	description = ""
	connector_type = ""
	parameters = "" 
	pk = "test"
	def __str__(self):
		return self.name + " : "+ str(self.connector_type)

class Task():
	name = 'Test Task'
	pk = '2023-02-23'
	last_run_date = '2023-02-23'
	last_run_time = '01:23:02'

transformers_type = [{"type":"Python","description":""}]
train_model = [{"name":"gpt-3.5-turbo","description":"Text Embedding"}]
embedding_model = [{"name":"OpenAIEmbedding","description":""},{"name":"clip-vit-base-patch32","description":"Image & Text Embedding"}]




connector_list = {	
"pye":[
{"name":'blank','alias':'blank','source':True,'target':False,'disabled':False ,'icon':'https://img.icons8.com/?size=512&id=54748&format=png'},
{"name":'links','source':True,'target':True,'disabled':False ,'icon':'https://img.icons8.com/?size=512&id=12312&format=png'} ,
{"name":'pipeline','source':True,'target':True,'disabled':False ,'icon':'https://img.icons8.com/?size=512&id=13255&format=png'},
{"name":'email','source':True,'target':True,'disabled':True ,'icon':'https://img.icons8.com/?size=512&id=13826&format=png'} ,
{"name":'datasets','source':True,'target':False,'disabled':True ,'icon':'https://img.icons8.com/?size=512&id=48299&format=png'},
{"name":'ai model','alias':'pye_train' ,'source':False,'target':True,'disabled':False ,'icon':'https://img.icons8.com/?size=512&id=31128&format=png'} ,
# {"name":'pye da','source':True,'target':False,'disabled':True ,'icon':'https://img.icons8.com/?size=512&id=13551&format=png'}
]  ,
"flatfile":[
{"name":'CSV','alias':'CSV','source':True,'target':True,'disabled':False ,'icon':'https://img.icons8.com/?size=512&id=32516&format=png'},
{"name":'TXT','source':True,'target':True,'disabled':False ,'icon':'https://img.icons8.com/?size=512&id=2290&format=png'},
{"name":'Excel','source':True,'target':True,'disabled':False ,'icon':'https://img.icons8.com/?size=512&id=13654&format=png'},
{"name":'JSON','source':True,'target':True,'disabled':False ,'icon':'https://img.icons8.com/?size=512&id=22547&format=png'},
{"name":'XML','source':True,'target':True,'disabled':False ,'icon':'https://img.icons8.com/?size=512&id=112042&format=png'},
{"name":'PDF','source':True,'target':False,'disabled':False ,'icon':'https://img.icons8.com/?size=512&id=53585&format=png'},
{"name":'DOCX','source':True,'target':False,'disabled':False ,'icon':'https://img.icons8.com/?size=512&id=13674&format=png'},
{"name":'Parquet','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Fixed Width File','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Apache Kafka','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Apache NiFi','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Apache Flume','source':True,'target':True,'disabled':True ,'icon':''},
 ],
"database":[
{"name":'MySQL','alias':'MySQL','source':True,'target':True,'disabled':False ,'icon':'https://img.icons8.com/?size=512&id=31359&format=png'},
{"name":'PostgreSQL','source':True,'target':True,'disabled':False ,'icon':'https://img.icons8.com/?size=512&id=38561&format=png'},
{"name":'Oracle Db','source':True,'target':True,'disabled':False ,'icon':'https://img.icons8.com/?size=512&id=39913&format=png'},
{"name":'MSSQL Server','source':True,'target':True,'disabled':False ,'icon':'https://img.icons8.com/?size=512&id=23045&format=png'},
{"name":'MongoDB','source':True,'target':True,'disabled':True ,'icon':'https://webimages.mongodb.com/_com_assets/cms/kuyjf3vea2hg34taa-horizontal_default_slate_blue.svg?auto=format%252Ccompress'},
{"name":'Amazon Redshift','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Google BigQuery','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Snowflake','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Apache Cassandra','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Apache Hadoop','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Teradata','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'IBM DB2','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'SQLite','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Informix','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'SAP HANA','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Vertica','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'MariaDB','source':True,'target':True,'disabled':True ,'icon':''},
],
 "directory service":[
{"name":'Active Directory','alias':'Active_Directory','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'File Transfer Protocol','source':True,'target':True,'disabled':True ,'icon':'https://img.icons8.com/?size=512&id=17983&format=png'},
{"name":'Lightweight Directory','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'OpenLDAP','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Azure Active Directory','source':True,'target':True,'disabled':True ,'icon':''},
],	
"api":[
{"name":'REST','alias':'REST','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'SOAP','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'GraphQL','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Google Analytics','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'RadarPro','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Twitter','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Facebook','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'LinkedIn','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'YouTube','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Pinterest','source':True,'target':True,'disabled':True ,'icon':''},
 ],
"application":[
{"name":'SAP','alias':'SAP_only','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Salesforce','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Microsoft Dynamics','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'ServiceNow','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'SharePoint','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Jira','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Zendesk','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'QuickBooks','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Shopify','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Magento','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'WooCommerce','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'MailChimp','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Slack','source':True,'target':True,'disabled':True ,'icon':''},
 ], 
"cloud":[
{"name":'Amazon S3','alias':'Amazon_S3','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Azure Blob Storage','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Amazon RDS','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Azure SQL Database','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Amazon DynamoDB','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Azure Cosmos DB','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Google Cloud Storage','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Google Cloud SQL','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Google Cloud Firestore','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'SAP','source':True,'target':True,'disabled':True ,'icon':''},
], 
"iot": [
{"name":'MQTT','alias':'MQTT','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Apache Kafka IoT','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Azure IoT','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'AWS IoT ','source':True,'target':True,'disabled':True ,'icon':''},
{"name":'Google Cloud IoT','source':True,'target':True,'disabled':True ,'icon':''}, 
]
	}





def replace_with_char(input_string):
    input_string = str(input_string).replace(" ","").replace("-","")
    positions = random.sample(range(len(input_string)), 5)
    char_replacements = [random.choice(string.ascii_letters) for _ in range(5)]
    output_string = list(input_string)
    for pos, char in zip(positions, char_replacements):
        output_string[pos] = char
    return ''.join(output_string).upper()[0:15]