from django.apps import AppConfig
from sqlalchemy import create_engine
from apscheduler.schedulers.background import BackgroundScheduler
import logging

logging.basicConfig(filename='etl.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')




class CustomerConfig(AppConfig):
    name = 'customer'

    def ready(self):
        pass
        # from django.conf import settings

        # # create database connection
        # engine = create_engine('sqlite:///' + str(settings.DATABASES['default']['NAME']))
        # from .models import Task
        # tasks = Task.objects.filter(status='running')
        # for task in tasks:    
        #     query = f"UPDATE apscheduler_jobs SET next_run_time = 'next_run_time', job_state = 'running' WHERE id = '{task.job_id}'"
        #     with engine.connect() as conn:
        #         result = conn.execute(query)

        #     logging.info(f"Job with ID {task.job_id} resumed")
