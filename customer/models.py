from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

class Customer(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    profile_pic= models.ImageField(upload_to='profile_pic/Customer/',null=True,blank=True)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20,null=False)
    email = models.CharField(max_length=100,null=False,default='')
    profession = models.CharField(max_length=100,null=False,default='')
    rate = models.FloatField(default=30,null=False)
    hrs = models.IntegerField(default=40,null=False)
    email_notifications = models.BooleanField(default=False)
    sms_notifications = models.BooleanField(default=False)
    call_notifications = models.BooleanField(default=False)
    whatsapp_notifications = models.BooleanField(default=False)
    fb = models.CharField(max_length=100,null=False,default='')
    ig = models.CharField(max_length=100,null=False,default='')
    twitter = models.CharField(max_length=100,null=False,default='')
    product_version = models.CharField(max_length=100,null=False,default='free')
   
    @property
    def get_name(self):
        return self.user.first_name+" "+self.user.last_name
    @property
    def get_instance(self):
        return self
    def __str__(self):
        return self.user.first_name


class BotFileUploads(models.Model):
    chatbot = models.CharField(max_length=200, null=True, blank=True)
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name + " : "+ self.chatbot


class FileModels(models.Model): 
    connector_id = models.CharField(max_length=200, null=True, blank=True)
    filetype = models.CharField(max_length=50, null=True, blank=True)
    file = models.FileField(upload_to='uploads/')
    ingest = models.CharField(max_length=10,default=False)


class Connector(models.Model):
    name = models.CharField(max_length=200,null=False,default='01')
    description = models.TextField(null=True,blank=True)
    connector_type = models.CharField(max_length=150,null=True,blank=True)
    can_source = models.CharField(max_length=20,null=True,blank=True)
    can_target = models.CharField(max_length=20,null=True,blank=True)
    type_name = models.CharField(max_length=150,null=True,blank=True)
    parameters = models.TextField(null=True,blank=True)
    created_by=models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    date_created = models.DateField(default=timezone.now)
    time_created = models.TimeField(default=timezone.now)


    def __str__(self):
        return self.name + " : "+ str(self.connector_type)+" user: "+self.created_by.username

    
 
class Transformer(models.Model):
    name = models.CharField(max_length=200,null=False,default='')
    transformer_type = models.CharField(max_length=200,null=True,blank=True,default="Python")
    description = models.TextField(null=True,blank=True)
    created_by=models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    last_modified = models.DateTimeField(default=timezone.now)
    is_public = models.CharField(max_length=20,null=True,blank=True,default='False')
    views = models.IntegerField(default=0,null=True,blank=True)
    code = models.TextField(null=True,blank=True,default='')

    def __str__(self):
        return   self.name+"-"+self.description

    def save(self, *args, **kwargs):
        self.views = self.views + 1
        super().save(*args, **kwargs)
 





class Task(models.Model):
    name = models.CharField(max_length=200,null=False,default='')
    description = models.TextField(null=True,blank=True)
    created_by=models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    date_created = models.DateField(default=timezone.now)
    time_created = models.TimeField(default=timezone.now)  
    source=models.ManyToManyField(Connector,  null=True, blank=True,related_name="connector_source")
    targets=models.ManyToManyField(Connector, null=True, blank=True)
    transformers=models.ManyToManyField(Transformer, null=True, blank=True)

    schedule_time = models.CharField(max_length=100,null=True,blank=True)
    minute_time = models.IntegerField(null=True,blank=True)
    daily_time = models.TimeField(null=True,blank=True)
    sun = models.CharField(max_length=100,null=True,blank=True)
    mon = models.CharField(max_length=100,null=True,blank=True)
    tue = models.CharField(max_length=100,null=True,blank=True)
    wed = models.CharField(max_length=100,null=True,blank=True)
    thu = models.CharField(max_length=100,null=True,blank=True)
    fri = models.CharField(max_length=100,null=True,blank=True)
    sat = models.CharField(max_length=100,null=True,blank=True) 
    weekly_time = models.TimeField(null=True,blank=True)
    status = models.CharField(max_length=50,blank=True,null=True,default='stopped')
    job_id = models.CharField(max_length=50,blank=True,null=True)
    last_run_date = models.DateField(default=timezone.now)
    last_run_time = models.TimeField(default=timezone.now )
    error = models.TextField(null=True,blank=True)

    def save(self, *args, **kwargs):
        # Update last_run_date and last_run_time fields to current date and time
        self.last_run_date = timezone.now().date()
        self.last_run_time = timezone.now().time()
        super().save(*args, **kwargs)
 

    def __str__(self):
        return self.status + " : "+ self.name

    def weekly_day(self):
        return ','.join(day for day in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'] if getattr(self, day))

    def get_transformers(self):
        return ', '.join( [x.name for x in self.transformers.all()])

    def get_targets(self):
        return ', '.join([ x.name + ' ('+x.type_name+')' for x in self.targets.all()])

    def get_sources(self):
        return ', '.join([ x.name + ' ('+x.type_name+')' for x in self.source.all()])

    weekly_day = property(weekly_day)
    get_transformers = property(get_transformers)
    get_targets = property(get_targets)
    get_sources = property(get_sources)




class ChatHistory(models.Model):
    content = models.TextField(null=True,blank=True) 
    question = models.TextField(null=True,blank=True) 
    role = models.CharField(max_length=20,null=False,default='')
    # user =  models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    connector =  models.ForeignKey(Connector, on_delete=models.CASCADE, null=True, blank=True)
    uuid = models.CharField(max_length=200,null=True,blank=True)

    def __str__(self):
        return   "uuid: "+self.uuid + ", Project: "+str(self.connector)


class Connections(models.Model):
    name = models.CharField(max_length=200,null=False,default='')
    description = models.TextField(null=True,blank=True) 
    chat_history = models.TextField(null=True,blank=True) 
    connector =  models.ForeignKey(Connector, on_delete=models.CASCADE, null=True, blank=True)
    pipelines =  models.ManyToManyField(Task,  null=True, blank=True,related_name="pipelines_task")
    last_date_update = models.DateField(default=timezone.now)
    last_time_update = models.TimeField(default=timezone.now )

    def __str__(self):
        return   self.name+"-"+self.connector.name+"-"+str(self.pk)

    def save(self, *args, **kwargs):
        self.last_date_update = timezone.now().date()
        self.last_time_update = timezone.now().time()
        super().save(*args, **kwargs)

    def get_prompts(self):
        prompt_len =  Chatbot.objects.filter(connection=self).count()
        return prompt_len


    def running_data_import(self):
        pipelines =  self.pipelines.filter(status='running').count()
        return True if pipelines > 0 else False

    get_prompts = property(get_prompts)
    running_data_import = property(running_data_import)


def merge_key(config={}):
    new_config = {}
    for key in config.keys():
        new_config[str(key).replace("-","_")] = config[key]
    return new_config

class Chatbot(models.Model):
    api_id = models.CharField(max_length=200,primary_key=True)
    name = models.CharField(max_length=200,null=False,default='')
    share_count = models.IntegerField(max_length=200,null=False,default=0)
    configs = models.TextField(null=True,blank=True) 
    connection =  models.ForeignKey(Connections, on_delete=models.CASCADE, null=True, blank=True) 
    created_by=models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    chat_history = models.TextField(null=True,blank=True) 
    last_update = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return self.name  + " - "+self.api_id

    def save(self, *args, **kwargs):
        self.last_update = timezone.now() 
        super().save(*args, **kwargs)

    def get_image(self):
        try:
            file_upload = BotFileUploads.objects.filter(chatbot=self.pk).last()
            return file_upload.file.url 
        except Exception as e:
            return None


    def get_chat_users(self):
        chat_history = json.loads(self.chat_history) if self.chat_history else []
        users = {}
        for entry in chat_history:
            if not users.get(entry.get('user')):
                users[entry.get('user')] = True

        return len(list(users.keys()))

    get_chat_users = property(get_chat_users)


    def get_chat_history(self):
        chat_history = json.loads(self.chat_history) if self.chat_history else []
        chat_history  = [ entry for entry in chat_history if entry.get('type') == 'HumanMessage'    ]
        return len(chat_history)

    get_chat_history = property(get_chat_history)


    def get_configs(self):
        configs = merge_key(json.loads(self.configs)  )
        return configs

    get_configs = property(get_configs)




class Prompts(models.Model):
    name = models.CharField(max_length=200,null=False,default='')
    description = models.TextField(null=True,blank=True) 
    api_id = models.CharField(max_length=200,null=False,default='')
    share_count = models.IntegerField(max_length=200,null=False,default=0)
    like = models.IntegerField(max_length=200,null=False,default=0)
    content = models.TextField(null=True,blank=True) 
    connection =  models.ForeignKey(Connections, on_delete=models.CASCADE, null=True, blank=True) 
    created_by=models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    last_update = models.DateTimeField(default=timezone.now)
    is_public = models.CharField(max_length=20,null=True,blank=True,default='False')


    def __str__(self):
        return self.name  + " - "+self.api_id

    def save(self, *args, **kwargs):
        self.last_update = timezone.now() 
        super().save(*args, **kwargs)

 




class Logs(models.Model):
    name = models.CharField(max_length=200,null=False,default='') 
    task = models.CharField(max_length=200,null=False,default='')
    text = models.TextField(null=True,blank=True)

    def __str__(self):
        return self.task + " : "+ self.name

class Running_Jobs(models.Model):
    job = models.TextField(null=False,default='') 
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    last_run_date = models.DateField(default=timezone.now)
    last_run_time = models.TimeField(default=timezone.now)
    next_run_date = models.DateField(default=timezone.now)
    next_run_time = models.TimeField(default=timezone.now )

    def __str__(self):
        return self.id + " : "+ self.last_run_date

 




class TaskConnectorData(models.Model):
    task_id = models.CharField(max_length=200,primary_key=True)
    data = models.TextField(null=True,blank=True) 
    date_created = models.DateField(default=timezone.now)
    time_created = models.TimeField(default=timezone.now)  

    def __str__(self):
        return self.task_id + " : "+ self.date_created




class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user=models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)


    def __str__(self):
        return self.email