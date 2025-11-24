from django.contrib import admin
from .models import Transformer,Customer,Connector,Task,Connections,Chatbot,Prompts,Running_Jobs,ChatHistory

# Register your models here.

admin.site.register(Transformer)
admin.site.register(Connector)
admin.site.register(Customer)
admin.site.register(Task)
admin.site.register(Connections)
admin.site.register(Chatbot)
admin.site.register(Prompts)
admin.site.register(Running_Jobs)
admin.site.register(ChatHistory)
