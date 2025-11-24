from email import policy
from multiprocessing.sharedctypes import Value
from typing import Type
from django.shortcuts import render,redirect,reverse
from . import forms,models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required,user_passes_test
from django.shortcuts import get_object_or_404
from django.conf import settings
from coinbase_commerce.client import Client
from decimal import Decimal
from django.core.paginator import Paginator
from datetime import date, datetime
from django.utils.datastructures import MultiValueDictKeyError
from django.core.files.uploadedfile import InMemoryUploadedFile
import mimetypes
from django.db.models import Q
from django.template import Context
from django.template.loader import render_to_string, get_template
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from backoffice import models as CMODEL
from backoffice import forms as CFORM
from django.contrib.auth.models import User
from turtle import end_fill
from django.views.decorators.csrf import csrf_exempt
from PIL import Image, ImageDraw, ImageFont
import json
import os
import random
import math
import re
from pyzbar.pyzbar import *
from glob import glob
import multiprocessing
import time
import subprocess
import string
from django.http.response import JsonResponse
from .chat import get_response, predict_class
from backoffice.models import Course
import pandas as pd
import copy
from .utils import setup_job, MyJsonEncoder,PyeScheduler,Connector,Task,transformers_type,connector_list,train_model,embedding_model,replace_with_char
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from utils.connectors import pick_connector
from utils.vortex_query import VortexQuery
from django.core.serializers.json import DjangoJSONEncoder
from customer.models import ChatHistory






def customerclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('customer-dashboard')
    return redirect('login')

@csrf_exempt
def checkout_view(request,pk):
    if request.method=='GET':
        customer = models.Customer.objects.get(user_id=request.user.id)
        policy_record = CMODEL.LeaveRecord.objects.get(customer=customer, id=pk)
        # domain_url = 'http://localhost:8030/customer/'
        # stripe.api_key = settings.STRIPE_SECRET_KEY
        #     # Create new Checkout Session for the order
        #     # Other optional params include:
        #     # [billing_address_collection] - to display billing address details on the page
        #     # [customer] - if you have an existing Stripe Customer ID
        #     # [payment_intent_data] - capture the payment later
        #     # [customer_email] - prefill the email input in the form
        #     # For full details see https://stripe.com/docs/api/checkout/sessions/create

        #     # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
        # checkout_session = stripe.checkout.Session.create(
        # success_url=domain_url + 'contracts',
        # cancel_url=domain_url + 'dashboard',
        # payment_method_types=['card'],
        # mode='payment',
        # client_reference_id=str(pk)+'_'+str(request.user.id)+'_'+"payment",
        # customer_email=customer.email,
        # line_items=[
        #             {
        #                 'name': policy_record.Vocation.policy_name,
        #                 'quantity': 1,
        #                 'currency': 'eur',
        #                 'amount': int(policy_record.Vocation.sum_assurance * 106)
        #             }
        #         ]
        #     )
        return redirect('checkout_session.url')
    return redirect('contracts')

# @csrf_exempt
# def process_payment(request,pk):
#     customer = models.Customer.objects.get(user_id=request.user.id)
#     policy_record = CMODEL.LeaveRecord.objects.get(customer=customer, id=pk)
#     order_id = request.session.get('order_id')
#     host = 'localhost:8030/customer/'
#     paypal_dict = {
#         'business': settings.PAYPAL_RECEIVER_EMAIL,
#         'amount': int(policy_record.Vocation.sum_assurance * 1.06),
#         'item_name': 'Order {}'.format(policy_record.id),
#         'invoice': str(request.user.id)+" "+str(pk),
#         'currency_code': 'USD',
#         'notify_url': 'http://{}{}'.format(host,
#                                            reverse('paypal-ipn')),
#         'return_url': 'http://{}{}'.format(host,
#                                            reverse('contracts')),
#         'cancel_return': 'http://{}{}'.format(host,
#                                               reverse('contracts')),
#     }
#     return redirect(paypal_dict['notify_url'])

@csrf_exempt
def coinbase_checkout_view(request,pk):
    if request.method=='GET':
        customer = models.Customer.objects.get(user_id=request.user.id)
        policy_record = CMODEL.LeaveRecord.objects.get(customer=customer, id=pk)
        domain_url = 'http://localhost:8030/customer/'
        client = Client(api_key=settings.COINBASE_COMMERCE_API_KEY)
        product = {
            'name': policy_record.Vocation.policy_name,
            'description': 'A really good car backoffice deal.',
            'local_price': {
                'amount': int(policy_record.Vocation.sum_assurance * 1.06),
                'currency': 'TND'
            },
            'pricing_type': 'fixed_price',
            'redirect_url': domain_url + 'contracts',
            'cancel_url': domain_url + 'dashboard',
        }
        charge = client.charge.create(**product)
        return redirect(charge.hosted_url)
    return redirect('contracts')

@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)
    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_id = session.client_reference_id.split("_")[1]
        contract_id = session.client_reference_id.split("_")[0]
        customer = models.Customer.objects.get(user_id=customer_id)
        policy_record = CMODEL.LeaveRecord.objects.get(customer=customer, id=contract_id)
        policy_record.status="Approved"
        policy_record.save()
        user_dir = os.path.join(settings.MEDIA_ROOT, "customer_{}".format(customer_id))
        invoice_path = os.path.join(user_dir,"INV-{}{}.pdf".format(customer_id,policy_record.id))
        contract_path = os.path.join(user_dir,"contrat_{}_{}.pdf".format(customer_id,policy_record.id))
        signature_path = os.path.join(settings.BASE_DIR,"signature.png")
     #   signature_add(invoice_path,signature_path,3000,950,0.6,0.9)
      #  signature_add(contract_path,signature_path,3100,1200,0.6,0.9)
        if customer.email_notifications:
            message = get_template("mail.html").render({'context':""})
            email = EmailMessage(
        'Paiement effectué avec succès',
        message,
        'keycorpsolutions@gmail.com',
        [customer.email],
    )
            #user_dir = os.path.join(settings.MEDIA_ROOT, "customer_{}".format(customer_id))
            email.content_subtype="html"
            #email.attach_file(os.path.join(user_dir,"contrat_{}_{}.png".format(customer_id,policy_record.id)))
            email.send()
        if customer.sms_notifications:
            pass
        if customer.call_notifications:
            pass
        if customer.whatsapp_notifications:
            pass
        intent = stripe.PaymentIntent.retrieve(session.payment_intent)
        used_card = intent.charges.data[0].payment_method_details.card
        if not CMODEL.Card .objects.all().filter(customer=customer,last4=used_card.last4,brand=used_card.brand):
            card = CMODEL.Card(customer=customer,holder=intent.charges.data[0].billing_details.name,brand=used_card.brand,last4=used_card.last4,exp_month=used_card.exp_month,exp_year=used_card.exp_year % 100)
            card.save()
        else:
            CMODEL.Card.objects.all().filter(customer=customer,last4=used_card.last4,brand=used_card.brand).update(holder=intent.charges.data[0].billing_details.name,exp_month=used_card.exp_month,exp_year=used_card.exp_year % 100)
    #return HttpResponse(status=200)
    return redirect('contracts')


def customer_signup_view(request):
    userForm=forms.CustomerUserForm()
    customerForm=forms.CustomerForm()
    mydict={'userForm':userForm,'customerForm':customerForm}
    if request.method=='POST':
        userForm=forms.CustomerUserForm(request.POST)
        customerForm=forms.CustomerForm(request.POST,request.FILES)
        if userForm.is_valid() and customerForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            customer=customerForm.save(commit=False)
            customer.user=user
            customer.save()
            my_customer_group = Group.objects.get_or_create(name='CUSTOMER')
            my_customer_group[0].user_set.add(user)
        return HttpResponseRedirect('login')
    return render(request,'home/sign-up.html',context=mydict)

def is_customer(user):
    return user.groups.filter(name='CUSTOMER').exists()

def chatbot_view(request):
    if request.method=='GET':
        return render(request,'base.html')
    
@csrf_exempt
def predict_view(request):
    if request.method=='POST':
        text=json.load(request)['message']
        ints=predict_class(text)
        intents = json.loads(open('intents.json').read())
        response =get_response(ints,intents)
        message={'answer':response}
        return JsonResponse(message)
    return render(request,'customer/index.html')

def presentation_view(request):
    return render(request,'presentation.html') 

def rtl_view(request):
    dict={"segment":"rtl"}
    return render(request,'home/rtl.html',context=dict) 

def virtual_reality_view(request):
    dict={"segment":"virtual"}
    return render(request,'home/virtual-reality.html',context=dict)   

@login_required(login_url='login')
def customer_dashboard_view(request):

    dict={
        'customer':models.Customer.objects.get(user_id=request.user.id),
        'chatbots':models.Chatbot.objects.filter(created_by=request.user).order_by('-pk')[0:12],
        'prompts':models.Prompts.objects.filter(created_by=request.user).order_by('-pk')[0:6],
        'connections':models.Connections.objects.filter(connector__created_by=request.user).order_by('-connector__date_created','-connector__time_created')[0:5],
        # 'available_policy':CMODEL.Vocation.objects.all().count(),
        # 'applied_policy':CMODEL.LeaveRecord.objects.all().filter(customer=models.Customer.objects.get(user_id=request.user.id)).count(),
        # 'total_category':CMODEL.Category.objects.all().count(),
        # 'total_question':CMODEL.Question.objects.all().filter(customer=models.Customer.objects.get(user_id=request.user.id)).count(),
        "segment":"customer-dashboard", 
        'user':str(request.user),
        'hide_preview':True


    }
    return render(request,'home/index.html',context=dict)

def customer_gopro_view(request):
    return render(request,'home/gopro.html')

def toggle_email_view(request):
    w = models.Customer.objects.get(id=request.POST['id'])
    w.email_notifications = request.POST['email_check'] == 'true'
    w.save()
    return HttpResponse('success')

def toggle_sms_view(request):
    w = models.Customer.objects.get(id=request.POST['id'])
    w.sms_notifications = request.POST['sms_check'] == 'true'
    w.save()
    return HttpResponse('success')

def toggle_call_view(request):
    w = models.Customer.objects.get(id=request.POST['id'])
    w.call_notifications = request.POST['call_check'] == 'true'
    w.save()
    return HttpResponse('success')

def toggle_whatsapp_view(request):
    w = models.Customer.objects.get(id=request.POST['id'])
    w.whatsapp_notifications = request.POST['whatsapp_check'] == 'true'
    w.save()
    return HttpResponse('success')


@login_required(login_url='login')
def profile_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    dict={'customer':customer,"segment":"profile"}
    return render(request,'home/profile.html',context=dict)   

@login_required(login_url='login')
def select_source_view(request,pk):
    connector= models.Connector.objects.get(pk=pk)
    dict={"segment":"connector","pk":pk,"connector":connector,"connector_list":connector_list}
    return render(request,'home/task.html',context=dict) 


@login_required(login_url='login')
def select_source_delete(request,pk):
    connector= models.Connector.objects.get(pk=pk).delete() 
    return redirect("connector-history")

@login_required(login_url='login')
def customize_bot(request):
    pk = request.GET.get('connections_pk')
    name = request.GET.get('name')
    api_id = request.GET.get('api_id')
    connections= models.Connections.objects.get(pk=pk) 
    dict={"segment":"customer-dashboard","pk":pk,"connections":connections,"name":name,"api_id":api_id,'user':request.user.username }
    return render(request,'home/chatbot_form.html',context=dict) 



    
@login_required(login_url='login')
def source_credential_view(request):    

    source_val = request.POST.get("connector_type",request.POST.get("source-val","pye"))
    type_name = request.POST.get("db_type","MySQL")
    redirect_link = request.POST.get("redirect")
    connector_name = request.POST.get("connector_name","")
    description = request.POST.get("connector_description","")
    exclude = request.POST.get("exclude",None)
    connections_pk = request.POST.get("connections_pk",None)
    # print(request.POST)



    copy_postdata = {}
    for key in request.POST:
        copy_postdata[key] = request.POST[key]

    # print(copy_postdata)
    post_data = {}
    if request.POST: 

        pk = request.POST.get("connector_pk")
        if pk:
            connector= models.Connector.objects.get(pk=pk)
        else:
            connector= models.Connector.objects.create(name=connector_name)
        connector.connector_type = source_val
        connector.type_name = type_name
        connector.created_by = request.user
        connector.description = description
        connector.save()

        print('conne',connector)

        if redirect_link == 'ai_models':
            try:
                create_connections = models.Connections.objects.get(name = connector_name,connector=connector)
            except Exception as e:
                create_connections = models.Connections.objects.create(
                name=connector_name,
                description=description,
                connector = connector
                    )
                create_connections.save()
            print('create_connections',create_connections)

            redirect_link =   reverse('ai_models_bot', args=[create_connections.pk]) 

        has_type = connector_list.get(source_val)

        if len(has_type):
            # print(has_type,type_name,list(filter(lambda x:x['name'] == type_name,has_type)))
            connector_stc =  list(filter(lambda x:x['name'] == type_name,has_type))[0]
            # print('connector_stc',connector_stc)
            connector.can_source = connector_stc.get('source')
            connector.can_target = connector_stc.get('target')

        connector.parameters = json.dumps(copy_postdata, cls=MyJsonEncoder)
        connector.save()

        if source_val=='flatfile':
            filetype = request.POST.get('filetype')
            files = request.FILES.getlist('files')

            my_file = models.FileModels.objects.filter(connector_id=connector.pk)
            my_file.delete()

            for file in files:
                try:
                    # my_file = models.FileModels.objects.get(connector_id=connector.pk)
                    # my_file.file = file
                    # my_file.filetype = filetype
                    # my_file.save()
                    my_file = models.FileModels.objects.create(file=file,filetype=filetype,connector_id=connector.pk)

                except Exception as e:
                    raise Exception("FIle Error: ",e)
            # connector.files.set(file_list)
            # connector.save()

        test_status = False
        error = ""


        try:
            data = []
            if type_name =='datasets':
                json_path = os.path.join(os.getcwd(),   'static', 'json', 'sample_data.json')
                with open(json_path,encoding="utf8") as f:
                    data = json.load(f)['sample_data'] 

            if exclude:
                print('exclude',exclude)
                task = models.Task.objects.create(name=connector.name, 
                    description=connector.description, 
                    created_by=connector.created_by,
                    schedule_time='now')

                task.source.add(connector)
                task.targets.add(models.Connections.objects.get(pk=connections_pk).connector)

                scheduler = PyeScheduler()
                try:
                    print('hererrr',connections_pk)
                    scheduler.schedule_job(task)
                    print('redirect_link',redirect_link)
                    return redirect('ai_models')
                except Exception as e:
                    print('schedule error',e)
                    task.status = "error"
                    task.error = str(e)
                task.save()

            else:
                task = Task() 
                con = pick_connector(connector,task)
                test_status = True


        except Exception as e:
            error = str(e) 
            print('error',error)
            if source_val=='task':
                data =  models.Task.objects.filter(created_by=request.user).order_by('-date_created').values("name","pk")
            if connector.parameters:
                post_data = json.loads(connector.parameters)

            # connector.delete()


            dict={"segment":"connector","source_val":connector.connector_type,"data":data,"connector":connector,
            'redirect':redirect_link,
            'post_data':post_data,'test_status':test_status,'error':error,'is_test':True,"connector_list":connector_list,
            'type_name':type_name, 'train_model':train_model,'embedding_model':embedding_model, **copy_postdata}
            return render(request,'home/credential.html',context=dict) 


        print('werhrekf',redirect_link)
        if redirect_link:
            return redirect(redirect_link)
        else:
            return redirect('connector-history')
    

    else:
        source_val = request.GET.get("source-val","pye")
        type_name = request.GET.get("type_name","MySQL")
        redirect_link = request.GET.get("redirect")
        exclude = request.GET.get("exclude")
        connections_pk = request.GET.get("connections_pk")
        pk = request.GET.get("pk")

        data = []
        if type_name =='datasets':
            json_path = os.path.join(os.getcwd(),   'static', 'json', 'sample_data.json')
            with open(json_path,encoding="utf8") as f:
                data = json.load(f)['sample_data']

        if source_val=='task':
            data =  models.Task.objects.filter(created_by=request.user).order_by('-date_created').values("name","pk")

        if pk:
            connector= models.Connector.objects.get(pk=pk)
            if connector.parameters:
                post_data = json.loads(connector.parameters)

                if source_val=='flatfile':
                    my_files = models.FileModels.objects.filter(connector_id=connector.pk) 
                    post_data['file_path'] = [ str(x.file).replace("uploads/","") for x in my_files ]
        else:
            connector = None

        type_name_icons = connector_list[source_val]
        try:
            filter_icon = list(filter(lambda e:e["name"]==type_name,type_name_icons))[0]["icon"]
        except:
            filter_icon = 'https://pbs.twimg.com/media/FyQlRbxWIAEfJ9J?format=png&name=small'


        dict={"segment":"customer-dashboard","source_val":source_val,"data":data,"connector":connector,
        'post_data':post_data,"connector_list":connector_list,"type_name":type_name,'icon':filter_icon,
        'redirect':redirect_link,
        'train_model':train_model,'embedding_model':embedding_model,"exclude":exclude,'connections_pk':connections_pk }
        return render(request,'home/credential.html',context=dict)  
    
@login_required(login_url='login')
def new_task_view(request):    

    task_pk = request.GET.get("task_pk")
    action = request.GET.get("action")

    task = {}
    if request.POST:
        name = request.POST.get('name')
        description = request.POST.get('description')
        created_by = request.user
        source_ids = request.POST.getlist('source')
        target_ids = request.POST.getlist('targets')
        transformers_ids = request.POST.getlist('transformers')
        schedule_time = request.POST.get('schedule_time')
        minute_time = request.POST.get('minute_time')
        daily_time = request.POST.get('daily_time') or None
        # weekly_day = request.POST.get('weekly_day')
        weekly_time = request.POST.get('weekly_time') or None
        
        # Get the Connector objects for source and target
        sources = models.Connector.objects.filter(id__in=source_ids)
        targets = models.Connector.objects.filter(id__in=target_ids)


        # Get the Transformer objects
        transformers = models.Transformer.objects.filter(id__in=transformers_ids)

           
        # Create the Task object

        try:
            task = models.Task.objects.get(name=name)
            task.description=description
            task.created_by=created_by
            task.schedule_time=schedule_time
            task.minute_time=minute_time
            task.daily_time=daily_time
            task.weekly_time=weekly_time 
            task.save()

        except ObjectDoesNotExist:
            task = models.Task.objects.create(name=name, description=description, created_by=created_by,
                schedule_time=schedule_time,minute_time=minute_time,daily_time=daily_time,
                weekly_time=weekly_time )


        save_days = [setattr(task, day,request.POST.get(day)) for day in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'] if request.POST.get(day)]

        # Add the Source to the Task
        for connector in sources:
            task.source.add(connector)

        # Add the Target to the Task
        for connector in targets:
            task.targets.add(connector)
        
        # Add the Transformers to the Task
        for transformer in transformers:
            task.transformers.add(transformer)
        task.save()

        return redirect('apply-policy')

    else: 
        if task_pk:
            scheduler = PyeScheduler()
            task= models.Task.objects.get(pk=task_pk)
            if action == 'delete':
                scheduler.remove_job(task)
                task.delete()
                return redirect('apply-policy')
            elif action == "play":
                try:
                    scheduler.schedule_job(task)
                except Exception as e:
                    print('schedule error',e)
                    task.status = "error"
                    task.error = str(e)
                    task.save()
                return redirect('apply-policy')
            elif action == "stop" or action == "cancel" :
                try:
                    scheduler.stop_job(task)
                except Exception as e:
                    print(e)
                    task.status = "error"
                    task.error = str(e)
                    task.save()
                return redirect('apply-policy')
            elif action == "pause":
                try:
                    scheduler.pause_job(task)
                except Exception as e:
                    print(e)
                    task.status = "error"
                    task.error = str(e)
                    task.save()
                return redirect('apply-policy')

            elif action == "resume":
                try:
                    scheduler.resume_job(task)
                except Exception as e:
                    print(e)
                    task.status = "error"
                    task.error = str(e)
                    task.save()
                return redirect('apply-policy')
            else:
                task= models.Task.objects.get(pk=task_pk)

        connectors = models.Connector.objects.filter(created_by=request.user).order_by('-date_created').values("name","description","pk",'can_source','can_target')
        transformers = models.Transformer.objects.filter(Q(is_public="True") | Q(created_by=request.user) ).order_by('-last_modified')

        dict={"segment":"apply-policy",'task':task,"connectors":connectors,"transformers":transformers}
        return render(request,'home/new_task.html',context=dict)     

@login_required(login_url='login')
def billing_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    policies = CMODEL.LeaveRecord.objects.all().filter(customer=customer)
    cards = CMODEL.Card.objects.all().filter(customer=customer)
    gross = customer.rate * customer.hrs
    net = gross * 0.9
    try:
        newest_card = CMODEL.Card.objects.filter(customer=customer).latest('creation_time')
    except:
        newest_card = None
    return render(request,'home/billing.html',{'segment':"billing",'policies':policies,'newest_card':newest_card,'cards':cards,'customer':customer,'gross':gross,'net':net})

@login_required(login_url='login')
def apply_policy_view(request): 
    # customer = models.Customer.objects.get(user_id=request.user.id)
    query = request.GET.get('q',"") 
    per_page = request.GET.get('per_page',10) 

    tasks = models.Task.objects.filter(created_by=request.user).order_by('-last_run_date','-last_run_time')
    if query:
        tasks = tasks.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )  

    paginator = Paginator(tasks, per_page) # Display 10 tasks per page
    page = request.GET.get('page')
    tasks = paginator.get_page(page)

    return render(request,'home/task_list.html',{'tasks':tasks,'segment' : "apply-policy","q":query,'per_page':per_page})


@login_required(login_url='login')
def ai_models(request): 
    # customer = models.Customer.objects.get(user_id=request.user.id)

    if request.method == 'POST': 
        bot_name = request.POST.get('name')
        connections_pk = request.POST.get('connections_pk')
        status = request.POST.get('status',"create")
        api_id = request.POST.get('api_id')

        if not bot_name:
            return JsonResponse({ "error" :f"Name is required!"})        

        print(request.POST)
        try:

            connection = models.Connections.objects.get(pk=connections_pk)
            try: 
                chatbot = models.Chatbot.objects.get(name=bot_name,created_by=request.user,connection=connection)
                # chatbot.api_id = replace_with_char(f"{bot_name}-{request.user.id}-{chatbot.pk}")
                
                if status.lower()== 'edit':
                    new_configs =  json.loads(chatbot.configs)

                    new_configs['bot-name'] = request.POST.get('bot-name')
                    new_configs['connections_pk'] = request.POST.get('connections_pk')
                    new_configs['header'] = request.POST.get('header')
                    new_configs['greeting'] = request.POST.get('greeting')
                    new_configs['task'] = request.POST.get('task')
                    new_configs['font'] = request.POST.get('font')
                    new_configs['font-size'] = request.POST.get('font-size')
                    new_configs['border-color'] = request.POST.get('border-color')
                    new_configs['border-size'] = request.POST.get('border-size')

                    new_configs['header-color'] = request.POST.get('header-color')
                    new_configs['header-title'] = request.POST.get('header-title')
                    new_configs['header-bg-color'] = request.POST.get('header-bg-color')

                    new_configs['header-font-size'] = request.POST.get('header-font-size')
                    new_configs['header-position'] = request.POST.get('header-position')
                    new_configs['header-text-transform'] = request.POST.get('header-text-transform')
                    new_configs['header-padding'] = request.POST.get('header-padding')
                    new_configs['header-margin'] = request.POST.get('header-margin')
                    new_configs['header-font-family'] = request.POST.get('header-font-family')

                    new_configs['show-icon'] = request.POST.get('show-icon')
                    new_configs['icon-margin'] = request.POST.get('icon-margin')
                    new_configs['icon-padding'] = request.POST.get('icon-padding')

                    new_configs['user-msg-color'] = request.POST.get('user-msg-color')
                    new_configs['user-msg-bg-color'] = request.POST.get('user-msg-bg-color')
                    new_configs['user-border-color'] = request.POST.get('user-border-color')
                    new_configs['user-border-size'] = request.POST.get('user-border-size')
                    new_configs['user-border-style'] = request.POST.get('user-border-style')
                    new_configs['user-border-radius'] = request.POST.get('user-border-radius')
                    new_configs['user-margin'] = request.POST.get('user-margin')
                    new_configs['user-padding'] = request.POST.get('user-padding')

                    new_configs['bot-msg-color'] = request.POST.get('bot-msg-color')
                    new_configs['bot-msg-bg-color'] = request.POST.get('bot-msg-bg-color')
                    new_configs['bot-border-color'] = request.POST.get('bot-border-color')
                    new_configs['bot-border-size'] = request.POST.get('bot-border-size')
                    new_configs['bot-border-style'] = request.POST.get('bot-border-style')
                    new_configs['bot-border-radius'] = request.POST.get('bot-border-radius')
                    new_configs['bot-margin'] = request.POST.get('bot-margin')
                    new_configs['bot-padding'] = request.POST.get('bot-padding')




                    new_configs['send-bg-color'] = request.POST.get('send-bg-color')
                    new_configs['send-color'] = request.POST.get('send-color')

                    new_configs['body-padding'] = request.POST.get('body-padding')
                    new_configs['body-margin'] = request.POST.get('body-margin')

                    new_configs['greeting-position'] =request.POST.get('greeting-position')
                    new_configs['greeting-text-transform'] = request.POST.get('greeting-text-transform')
                    new_configs['greeting-padding'] = request.POST.get('greeting-padding')
                    new_configs['greeting-margin'] = request.POST.get('greeting-margin')
                    new_configs['greeting-font-family'] = request.POST.get('greeting-font-family')


                    new_configs['greeting-bg-color'] = request.POST.get('greeting-bg-color')
                    new_configs['greeting-color'] = request.POST.get('greeting-color')
                    new_configs['greeting-border-color'] = request.POST.get('greeting-border-color')
                    new_configs['greeting-border-size'] = request.POST.get('greeting-border-size')
                    new_configs['greeting-border-radius'] = request.POST.get('greeting-border-radius')
                    new_configs['greeting-border-shadow'] = request.POST.get('greeting-border-shadow')
                    new_configs['greeting-border-style'] = request.POST.get('greeting-border-style')

                    new_configs['header-border-color'] = request.POST.get('header-border-color')
                    new_configs['header-border-size'] = request.POST.get('header-border-size')
                    new_configs['header-border-radius'] = request.POST.get('header-border-radius')
                    new_configs['header-border-style'] = request.POST.get('header-border-style')
                    new_configs['bot-greeting-message'] = request.POST.get('bot-greeting-message')




                    bot_image = request.FILES.get('bot-image')
                    if bot_image:
                        try:
                            models.BotFileUploads.objects.filter(chatbot=chatbot.pk).delete()
                        except Exception as e:
                            print("Bot Image Delete: ",e)

                        file_upload = models.BotFileUploads(chatbot=chatbot.pk, file=bot_image)
                        file_upload.save()


                    new_configs['input-position'] = request.POST.get('input-position')
                    new_configs['input-placeholder'] = request.POST.get('input-placeholder')
                    new_configs['input-width'] = request.POST.get('input-width')
                    new_configs['input-height'] = request.POST.get('input-height')
                    new_configs['input-background'] = request.POST.get('input-background')
                    new_configs['input-color'] = request.POST.get('input-color')
                    new_configs['border-radius'] = request.POST.get('border-radius')
                    new_configs['input-border-color'] = request.POST.get('input-border-color')
                    new_configs['input-border-size'] = request.POST.get('input-border-size')
                    new_configs['show-greeting'] = request.POST.get('show-greeting')
                    new_configs['show-chat-history'] = request.POST.get('show-chat-history')
                    new_configs['show-header'] = request.POST.get('show-header')
                    new_configs['show-user-icon'] = request.POST.get('show-user-icon')
                    new_configs['border-shadow'] = request.POST.get('border-shadow')
                    new_configs['task-prompt'] = request.POST.get('task-prompt')

                    chatbot.configs = json.dumps(new_configs)
                    chatbot.save()

                    return JsonResponse({ "error" :f"Bot Prompt: {bot_name} update successfully!",'status':status,'user':request.user.username,'api_id':chatbot.api_id,'pk':chatbot.pk})
                
                else:
                    return JsonResponse({ "error" :f"Bot Prompt:  {bot_name} already created by you!",'status':status,'user':request.user.username,'api_id':chatbot.api_id,'pk':chatbot.pk})

            except ObjectDoesNotExist:
                print('were er')

                chatbot = models.Chatbot.objects.create(name=bot_name,configs=json.dumps(request.POST),created_by=request.user,api_id=str(datetime.now()))
                chatbot.connection = connection
                print('heresfg')

                chatbot.api_id = replace_with_char(f"{bot_name}-{request.user.id}-{chatbot.pk}-{datetime.now()}")
                print(chatbot.api_id)
                chatbot.save()

                # Save the send_icon_color to another table (e.g., FileUploads) and get its URL
                bot_image = request.FILES.get('bot-image')
                if bot_image:
                    file_upload = models.BotFileUploads(chatbot=chatbot.pk, file=bot_image)
                    file_upload.save()


                return JsonResponse({ 'message':'Bot Prompt created successfully','status':status,'user':request.user.username,'api_id':chatbot.api_id,'pk':chatbot.pk})

        except Exception as e:
            print(e)
            return JsonResponse({ "error" :str(e)})

        

    else:
        query = request.GET.get('q',"") 
        per_page = request.GET.get('per_page',10) 

        connections = models.Connections.objects.filter(connector__created_by__username=request.user.username).order_by('-connector__date_created','-connector__time_created')
        print(connections)
        if query:
            connections = connections.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )  

        paginator = Paginator(connections, per_page) # Display 10 tasks per page
        page = request.GET.get('page')
        connections = paginator.get_page(page)

        for con in connections:
            try:
                fnd = models.Task.objects.filter(targets__pk=con.connector.pk).values('status')
                if any([x for x in fnd if x.get('status')=='error'  ]):
                    con.status = 'error'
            except ObjectDoesNotExist:
                pass
        

        return render(request,'home/ai_models.html',{'connections':connections,'segment' : "customer-dashboard","q":query,'per_page':per_page})
 


@login_required(login_url='login')
def ai_models_bot(request,pk): 
    # customer = models.Customer.objects.get(user_id=request.user.id)

    if request.method == 'POST': 
        print(request.POST)
        bot_name = request.POST.get('name')
        connections_pk = request.POST.get('connections_pk')
        status = request.POST.get('status',"create")

        if not bot_name:
            return JsonResponse({ "error" :f"Name is required!"})        

        try:

            try: 
                connection = models.Connections.objects.get(pk=connections_pk)
                chatbot = models.Chatbot.objects.get(name=bot_name,connection=connection)
                
                if status.lower()== 'edit':
                    chatbot.configs=json.dumps(request.POST)
                    chatbot.save()

                    try:
                        # Save the send_icon_color to another table (e.g., FileUploads) and get its URL
                        bot_image = request.FILES.get('bot-image')
                        print('image upload bot_image: ',bot_image)
                        if bot_image:
                            models.BotFileUploads.objects.filter(chatbot=chatbot.pk).delete()
                            file_upload = models.BotFileUploads.objects.create(chatbot=chatbot.pk, file=bot_image)
                            file_upload.save()
                    except Exception as e:
                        print('image upload err: ',e)


                    return JsonResponse({ "message" :f"Bot Prompts: {bot_name} update successfully!"})
                
                else:
                    return JsonResponse({ "message" :f"Bot Prompts: {bot_name} already created by you!"})

            except ObjectDoesNotExist:

                chatbot = models.Chatbot.objects.create(name=bot_name,configs=json.dumps(request.POST),created_by=request.user,api_id=str(datetime.now()))
                chatbot.connection = connection
                chatbot.api_id = replace_with_char(f"{bot_name}-{request.user.id}-{chatbot.pk}-{datetime.now()}")
                print(chatbot.api_id)
                chatbot.save()

                try:
                    # Save the send_icon_color to another table (e.g., FileUploads) and get its URL
                    bot_image = request.FILES.get('bot-image')
                    print('image upload bot_image: ',bot_image)
                    if bot_image:
                        models.BotFileUploads.objects.filter(chatbot=chatbot.pk).delete()
                        file_upload = models.BotFileUploads.objects.create(chatbot=chatbot.pk, file=bot_image)
                        file_upload.save()
                except Exception as e:
                    print('image upload err: ',e)

                return JsonResponse({ 'message':'Bot Prompts created successfully'})

        except Exception as e:
            print(e)
            return JsonResponse({ "error" :str(e)})

        

    else:
        query = request.GET.get('q',"") 
        per_page = request.GET.get('per_page',10) 

        connection = models.Connections.objects.get(pk=pk)

        chatbots = models.Chatbot.objects.filter(connection=connection, created_by=request.user).order_by('-pk')
        # print('pk',pk,chatbots)
        if query:
            chatbots = chatbots.filter(
                Q(name__icontains=query) |
                Q(configs__icontains=query)
            )  

        paginator = Paginator(chatbots, per_page) # Display 10 tasks per page
        page = request.GET.get('page')
        chatbots = paginator.get_page(page)

        return render(request,'home/ai_models_bot.html',{'chatbots':chatbots,'connection':connection,'segment' : "customer-dashboard","q":query,'per_page':per_page})


def merge_key(config={}):
    new_config = {}
    for key in config.keys():
        new_config[str(key).replace("-","_")] = config[key]
    return new_config


def ai_models_bot_iframe(request,api_id): 
    height = request.GET.get('height',"100%") 
    user_id = request.GET.get('user_id') 

    try:
        chatbot = models.Chatbot.objects.get(api_id=api_id)
        connection = models.Connections.objects.get(pk=chatbot.connection.pk) 
        configs = merge_key(json.loads(chatbot.configs)) 
        file_upload = models.BotFileUploads.objects.get(chatbot=chatbot.pk)
        configs['bot_image'] = file_upload.file.url
    except Exception as e:
        print('image upload err: ',e) 


    return render(request,'home/ai_models_bot_iframe.html',{'chatbot':chatbot,
        'connection':connection,'api_id':api_id,'height':height,"configs":configs,'user_id':user_id})

@login_required(login_url='login')
def chatbot_delete(request): 
    pk = request.GET.get('pk') 
    connections_pk = request.GET.get('connections_pk') 

    chatbot = models.Chatbot.objects.get(pk=pk)
    chatbot.delete()

    url = reverse('ai_models_bot', args=[connections_pk])  # Replace 'ai_models_bot' with the actual view name
    return redirect(url)


@login_required(login_url='login')
def ai_models_delete(request): 
    pk = request.GET.get('pk') 
    connection = models.Connections.objects.get(pk=pk)
    connector = models.Connector.objects.get(pk=connection.connector.pk).delete()
    chatbots = models.Chatbot.objects.filter(connection=connection).delete()
    tasks = models.Task.objects.filter(targets__pk=connection.connector.pk).delete()
    connection.delete()

    url = reverse('ai_models')
    return redirect(url)

@login_required(login_url='login')
def prompt_delete(request): 
    pk = request.GET.get('pk') 
    prompt = models.Prompts.objects.get(pk=pk)
    prompt.delete()

    url = reverse('prompt')
    return redirect(url)

# @login_required(login_url='login')
def process_message(request): 
    form_data = request.GET
    message = form_data.get('message',"")
    api_id = form_data.get('api_id')
    api_user = form_data.get('user_id')
    uuid = form_data.get('uuid')
    prompt = ""
    pk = form_data.get('pk') 
    show_chat_history = True
    greeting_message = []

    try:

        try:
            customer = models.Customer.objects.get(user__username=str(api_user if api_user else request.user) )
            if str(customer.product_version) == 'free':
                chat_history_len = 200
            elif  str(customer.product_version).lower() == 'pro':
                chat_history_len = 500
            else:
                chat_history_len = 50
        except ObjectDoesNotExist:
            chat_history_len = 50


        if api_id:
            connection = models.Chatbot.objects.get(api_id=api_id)
            configs = json.loads(connection.configs)
            if configs.get('bot-greeting-message'):
                greeting_message.append({'type':"AIMessage",'content':configs.get('bot-greeting-message')})

            prompt = configs.get("task","") 
            show_chat_history = True if configs.get("show-chat-history") == "on" else False
            # connection.connector = connection.connection.connector
        else:
            connection = models.Connections.objects.get(pk=pk)


        
        if message:
            vortex_query = VortexQuery(connection,prompt,uuid,show_chat_history,chat_history_len)
            answer = vortex_query.ask_question(message)
            return JsonResponse({'response':answer})
        else:
            print('show_chat_history',configs.get("show-chat-history"))
            
            if show_chat_history:
                connection = {"chat_history":json.dumps(greeting_message+[ {"type": 'HumanMessage' if hist.role == 'user' else "AIMessage", "content": hist.question if hist.question else hist.content}  for hist in ChatHistory.objects.filter(uuid=uuid,connector=connection.connector if hasattr(connection,'connector') else connection.connection.connector).order_by('pk')[:chat_history_len]])}
                # connection = {"chat_history":json.dumps([ entry for entry in chat_history if entry.get('user') == str(api_user if api_user else request.user)  ][chat_history_len:] )}
            else:
                connection = {"chat_history":json.dumps(greeting_message)} 

            result = json.dumps(connection, sort_keys=True,
                                    indent=1, cls=DjangoJSONEncoder)
            return JsonResponse({'response':result})
    except Exception as e:
        print("Err @ Chat",e)
        return JsonResponse({'error':str(e)})



@login_required(login_url='login')
def connector_history_view(request): 

    # customer = models.Customer.objects.get(user_id=request.user.id)
    query = request.GET.get('q',"") 
    per_page = request.GET.get('per_page',10) 
    connectors = models.Connector.objects.filter(created_by=request.user).order_by('-date_created','-time_created')
    if query:
        connectors = connectors.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )  

    paginator = Paginator(connectors, per_page) # Display 10 tasks per page
    page = request.GET.get('page')
    connectors = paginator.get_page(page)

    if request.method == 'POST': 
        try:
            code_Form=forms.Connectorform(request.POST)
            if code_Form.is_valid() :
                code_save = code_Form.save(commit=False)
                code_save.created_by = request.user
                code_save.save() 

        except Exception as e: 
            return  render(request,'home/connector.html',{'connectors':connectors,
                                                    'segment' : "connectors", "connector_list":connector_list,
                                                    "error":str(e),'per_page':per_page})

        return render(request,'home/task.html',{'connector':code_save,
                                                    'segment' : "connectors","pk":code_save.pk,
                                                    "connector_list":connector_list,'per_page':per_page
                                                    })

    return render(request,'home/connector.html',{'connectors':connectors,
                                                    'segment' : "connectors","q":query , 
                                                    "connector_list":connector_list,'per_page':per_page})
@login_required(login_url='login')
def select_connector(request):  
    exclude = request.GET.get('exclude',"")
    connections_pk = request.GET.get('connections_pk',"")
    query = request.GET.get('q',"")
    new_connector_list = {}

    if query:
        for con_type in connector_list:
            for con in connector_list[con_type]:
                if query.lower() in con['name'].lower() or query.lower() in con_type.lower() :
                    if new_connector_list.get(con_type):
                        new_connector_list[con_type].append(con)
                    else:
                        new_connector_list[con_type] = [con]


    exclude_list = exclude.rstrip(',').split(",") 
    return  render(request,'home/task.html',{'segment' : "customer-dashboard", "connector_list":new_connector_list if query else connector_list ,'exclude':exclude_list,
        'exclude_args':exclude,
        'connections_pk':connections_pk,'q':query}) 

def apply_view(request,pk):
    customer = models.Customer.objects.get(user_id=request.user.id)
    policy = CMODEL.Vocation.objects.get(id=pk)
    policyrecord = CMODEL.LeaveRecord()
    policyrecord.Policy = policy
    policyrecord.customer = customer
    policyrecord.save()
    email = EmailMessage(
        'Demande de congé en cours de traitement',
        "Votre demande de congé de numéro {}{} créée le {} a été envoyée avec succès et est en cours de traitement.".format(request.user.id,policyrecord.id,policyrecord.creation_date),
        'proxymartstore@gmail.com',
        ["driverprodigy@gmail.com",customer.email],
    )
    email.send()
    return redirect('history')

def history_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    policies = CMODEL.LeaveRecord.objects.all().filter(customer=customer)
    return render(request,'customer/history.html',{'policies':policies,'customer':customer})


def delete_contract_view(request,pk):
    customer = models.Customer.objects.get(user_id=request.user.id)
    policy_record = CMODEL.LeaveRecord.objects.get(customer=customer, id=pk)
    policy_record.delete()
    return redirect('contracts')

def delete_card_view(request,pk):
    customer = models.Customer.objects.get(user_id=request.user.id)
    card = CMODEL.Card.objects.get(customer=customer,id=pk)
    card.delete()
    return redirect('billing')

def delete_car_view(request,pk):
    customer = models.Customer.objects.get(user_id=request.user.id)
    car = CMODEL.Car.objects.get(owner=customer,id=pk)
    car.delete()
    return redirect('contracts')

@login_required(login_url='login')
def history_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    vocations = CMODEL.LeaveRecord.objects.all().filter(customer=customer)
    cars = CMODEL.Car.objects.all().filter(owner=customer)
    return render(request,'home/tables.html',{'cars':cars,'vocations':vocations,'customer':customer,'segment':"contracts"})

def delete_question_view(request,pk):
    customer = models.Customer.objects.get(user_id=request.user.id)
    question = CMODEL.Question.objects.get(customer=customer,id=pk)
    question.delete()
    return redirect('question-history')



@login_required(login_url='login')
def delete_code_editor(request,pk):
    connector= models.Transformer.objects.get(pk=pk).delete()
    return redirect("question-history")



def code_editor(request,pk=None): 

    transformers = models.Transformer.objects.filter(is_public="True").order_by('-last_modified')    

    if request.method == 'POST':  
        try:

            try:
                saved_transformer = models.Transformer.objects.get(pk=pk,created_by=request.user)
                saved_transformer.code = request.POST.get("code")
                saved_transformer.is_public = request.POST.get("is_public")
                saved_transformer.description = request.POST.get("description")
                saved_transformer.transformer_type = request.POST.get("transformer_type")
                saved_transformer.save()
                return redirect('question-history')

            except ObjectDoesNotExist:            
                code_Form=forms.CodeForm(request.POST)
                if code_Form.is_valid() :
                    code_save = code_Form.save(commit=False)
                    code_save.created_by = request.user
                    code_save.transfomer_type = request.POST.get("transfomer_type")
                    code_save.save()
                # saved_transformer = models.Transformer.objects.create(**save_data) 
                return redirect('question-history')
        except Exception as e:
            print(e)
            form = forms.CodeForm()
            return render(request,'home/code_editor.html',{'code':request.POST.get("code"),'form':form,"update":1,
                'name':request.POST.get("name"),'description':request.POST.get("description"),"error":e,
                'transformers_type':transformers_type,'segment' : "question-history",
                'transformer_type': request.POST.get("transformer_type") or "Python",

                 }) 
    else:
        form = forms.CodeForm()
        if pk:
            transformer = models.Transformer.objects.get(pk=pk)
            return render(request,'home/code_editor.html',{'code':transformer.code,'form':form,"update":1,
                'name':transformer.name,'description':transformer.description,'transformers_type':transformers_type,'is_public':transformer.is_public }) 
        return render(request,'home/code_editor.html',{'code':
            """# This Python 3 environment comes with many helpful analytics libraries installed 

    import numpy as np # linear algebra
    import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)

    def main(transform_data,source_data):
        dt = source_data['Dataset Reading']
        print(dt)
        dt.pop()
        return dt

        """,'transformers_type':transformers_type,
        'transformer_type':  "Python",'segment' : "question-history"}) 



def question_history_view(request): 
    # customer = models.Customer.objects.get(user_id=request.user.id)
    query = request.GET.get('q',"")
    per_page = request.GET.get('per_page',10)
    q_types = request.GET.get('q_types',"")
    transformers = models.Transformer.objects.filter().order_by('-last_modified')
    my_work = models.Transformer.objects.filter(created_by=request.user).count()  

    if query:
        transformers = transformers.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )  

    if q_types:
        transformers.filter(transformer_type=q_types)

    paginator = Paginator(transformers, per_page) # Display 10 transformers per page
    page = request.GET.get('page')
    transformers = paginator.get_page(page)

    return render(request,'home/my-questions.html',{'transformers':transformers,'transformers_type':transformers_type,
        'transformer_type':q_types,'segment' : "question-history","q":query,"my_work":my_work,'per_page':per_page})


def download_attendance(request):
    e = models.Customer.objects.get(user_id=request.user.id)
    employee_dir = os.path.join(settings.MEDIA_ROOT, "employee_{}".format(request.user.id))
    os.makedirs(employee_dir,exist_ok=True)
    filename = "attendance_{}.pdf".format(request.user.id)
    font = ImageFont.truetype("arial.ttf", 35, encoding="utf-8")
    font1 = ImageFont.truetype("arial.ttf", 15, encoding="utf-8")
    canvas = Image.open('attendance.png')
    canvas=canvas.convert('RGB')
    draw = ImageDraw.Draw(canvas)
    draw.text((430, 420), str(request.user.first_name)+" "+str(request.user.last_name), 'black', font)
    draw.text((530, 580), "{}    {}      {}".format(datetime.now().day,datetime.now().month,datetime.now().year), 'black', font1)
    canvas.save(os.path.join(employee_dir,filename))
    #signature_add(os.path.join(employee_dir,filename),'signature.png',3000,750,0.6,0.9)
    filepath = settings.BASE_DIR + '\\static\\' + "employee_{}\\".format(request.user.id) + filename
    fl = open(filepath, 'rb')
    mime_type, _ = mimetypes.guess_type(filename)
    response = HttpResponse(fl, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    email = EmailMessage(
    'Certificat de présence',
    "Veuillez trouver ci-joint votre certificat de présence, attribuée suite à votre demande.",
    'proxymartstore@gmail.com',
    ["driverprodigy@gmail.com",e.email],
)
    email.attach_file(os.path.join(employee_dir,filename))
    email.send()
    return response

def download_payslip(request):
    e = models.Customer.objects.get(user_id=request.user.id)
    employee_dir = os.path.join(settings.MEDIA_ROOT, "employee_{}".format(request.user.id))
    os.makedirs(employee_dir,exist_ok=True)
    filename = "payslip_{}_{}_{}.pdf".format(request.user.id,datetime.now().month,datetime.now().year)
    font2 = ImageFont.truetype("arial.ttf", 15, encoding="utf-8")
    font = ImageFont.truetype("arial.ttf", 20, encoding="utf-8")
    canvas = Image.open('payslip.png')
    canvas=canvas.convert('RGB')
    draw = ImageDraw.Draw(canvas)
    draw.text((550, 300), "{} H".format(e.hrs), 'black', font)
    draw.text((620, 305), "{} DT/H".format(e.rate), 'black', font2)
    draw.text((700, 305), "{} DT".format(e.hrs*e.rate), 'black', font2)
    draw.text((700, 340), "{} DT".format(e.hrs*e.rate), 'black', font2)
    draw.text((700, 370), "{} DT".format(e.hrs*e.rate*0.1), 'black', font2)
    draw.text((700, 400), "{} DT".format(e.hrs*e.rate*0.9), 'black', font2)
    draw.text((700, 430), "{} DT".format(e.hrs*e.rate*0.9*0.02), 'black', font2)
    draw.text((530, 200), "{}/{}/{}".format(datetime.now().day,datetime.now().month,datetime.now().year), 'black', font2)
    draw.text((40, 170), "{} {}".format(request.user.first_name,request.user.last_name), 'black', font2)
    draw.text((40, 200), "{}".format(e.address), 'black', font2)
    canvas.save(os.path.join(employee_dir,filename))
   # signature_add(os.path.join(employee_dir,filename),'signature.png',450,450,0.6,0.9)
    filepath = settings.BASE_DIR + '\\static\\' + "employee_{}\\".format(request.user.id) + filename
    fl = open(filepath, 'rb')
    mime_type, _ = mimetypes.guess_type(filename)
    response = HttpResponse(fl, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    email = EmailMessage(
    'Bulletin de paie',
    "Veuillez trouver ci-joint votre bulletin de paie pour le mois {}/{}.".format(datetime.now().month,datetime.now().year),
    'proxymartstore@gmail.com',
    ["driverprodigy@gmail.com",e.email],
)
    email.attach_file(os.path.join(employee_dir,filename))
    email.send()
    return response

def download_autorization(request,pk):
    customer = models.Customer.objects.get(user_id=request.user.id)
    leave_record = CMODEL.LeaveRecord.objects.get(customer=customer,id=pk)
    if leave_record.status != "Approved":
        return redirect('contracts')
    employee_dir = os.path.join(settings.MEDIA_ROOT, "employee_{}".format(request.user.id))
    os.makedirs(employee_dir,exist_ok=True)
    filename = "autorization_{}_{}.pdf".format(request.user.id,pk)
    font = ImageFont.truetype("arial.ttf", 35, encoding="utf-8")
    font1 = ImageFont.truetype("arial.ttf", 25, encoding="utf-8")
    canvas = Image.open('autorization.jpg')
    canvas=canvas.convert('RGB')
    draw = ImageDraw.Draw(canvas)
    draw.text((100, 410), "{} {}".format(request.user.first_name,request.user.last_name), 'black', font)
    draw.text((180, 470), "{}".format(leave_record.creation_date), 'black', font)
    draw.text((670, 570), "{}{}".format(request.user.id,pk), 'black', font)
    draw.text((335, 595), "{}".format(leave_record.creation_date), 'black', font1)
    canvas.save(os.path.join(employee_dir,filename))
  #  signature_add(os.path.join(employee_dir,filename),'signature.png',5000,600,0.6,0.9)
    filepath = settings.BASE_DIR + '\\static\\' + "employee_{}\\".format(request.user.id) + filename
    fl = open(filepath, 'rb')
    mime_type, _ = mimetypes.guess_type(filename)
    response = HttpResponse(fl, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response


def movie_recommendation_view(request):
    if request.method == "GET":
      # The context/data to be presented in the HTML template
      context = generate_movies_context()
      # Render a HTML page with specified template and context
      return render(request, 'customer/movie_list.html', context)

def generate_movies_context():
    context = {}
    # Show only movies in recommendation list
    # Sorted by vote_average in desc
    # Get recommended movie counts
    recommended_count = Course.objects.filter(
        recommended=True
    ).count()
    # If there are no recommended movies
    if recommended_count == 0:
        # Just return the top voted and unwatched movies as popular ones
        courses = Course.objects.filter(
            watched=False
        ).order_by('-vote_count')[:30]
    else:
        # Get the top voted, unwatched, and recommended movies
        courses = Course.objects.filter(
            watched=False
        ).filter(
            recommended=True
        ).order_by('-vote_count')[:30]
    context['movie_list'] = courses

    return context



 


def process_payment(request):
    # Retrieve form data
    amount = "20"
    card_cvv = request.POST.get('card_cvv')
    card_expiry_date = request.POST.get('card_expiry_date')
    card_expiry_month = request.POST.get('card_expiry_month')

    # Create payment payload
    payload = {
        'merchantId': settings.REMITA_MERCHANT_ID,
        'serviceTypeId': '123456789',
        'amount': amount,
        'cardCVV': card_cvv,
        'cardExpiryDate': card_expiry_date,
        'cardExpiryMonth': card_expiry_month,
        # Add other required parameters
    }

    # Make API request to Remita
    response = requests.post(
        f"{settings.REMITA_API_BASE_URL}/remita/exapp/api/v1/send/api/echannelsvc/echannel/initialize",
        json=payload,
        headers={'Content-Type': 'application/json', 'Authorization': f"Bearer {settings.REMITA_API_KEY}"}
    )

    # Process the response and redirect the user to the payment page
    if response.status_code == 200:
        payment_data = response.json()
        redirect_url = payment_data['paymentAuthUrl']
        return redirect(redirect_url)
    else:
        # Handle error case
        return render(request, 'home/paymenterror.html')




def custom_404(request, exception):
    return render(request, 'home/404.html', status=404)



def subscribe(request):
    if request.method == 'POST':
        print(request.POST)
        email = request.POST.get('email')
        if email:
            models.Subscriber.objects.create(email=email,user=request.user)
            return JsonResponse({'message': 'Subscribed successfully!'})
        else:
            return JsonResponse({'error': 'Invalid email.'})
    return JsonResponse({'error': 'Invalid request.'})


def get_chatbot_data(request):
    chatbot_id = request.GET.get('chatbot_id')  # Assuming you pass the chatbot ID as a parameter
    chatbot = models.Chatbot.objects.get(pk=chatbot_id)
    chatbot_data = merge_key(json.loads(chatbot.configs)) 
    try:
        file_upload = models.BotFileUploads.objects.get(chatbot=chatbot.pk)
        chatbot_data['bot_image_url'] = file_upload.file.url
    except Exception as e:
        print("imagr err: ",e)
    # print(chatbot_data)
    return JsonResponse(chatbot_data)



@login_required(login_url='login')
def prompt(request): 
    # customer = models.Customer.objects.get(user_id=request.user.id)

    if request.method == 'POST': 
        prompt_name = request.POST.get('name')
        connections_pk = request.POST.get('connections_pk')
        status = request.POST.get('status',"create")

        if not prompt_name:
            return JsonResponse({ "error" :f"Name is required!"})        

        try:

            try: 
                connection = models.Connections.objects.get(pk=connections_pk)
                prompt = models.Prompts.objects.get(name=prompt_name,created_by=request.user,connection=connection)
                
                if status.lower()== 'edit':
                    prompt.configs=json.dumps(request.POST)
                    prompt.save() 

                    return JsonResponse({ "message" :f"Prompt: {prompt_name} update successfully!"})
                
                else:
                    return JsonResponse({ "message" :f"Prompt: {prompt_name} already created by you!"})

            except ObjectDoesNotExist:

                prompt = models.Prompts.objects.create(name=prompt_name,configs=json.dumps(request.POST),created_by=request.user)
                prompt.connection = connection
                prompt.api_id = replace_with_char(f"{prompt_name}-{request.user.id}-{prompt.pk}-{datetime.now()}")
                prompt.save() 

                return JsonResponse({ 'message':'Prompts created successfully'})

        except Exception as e:
            print(e)
            return JsonResponse({ "error" :str(e)})

        

    else:
        query = request.GET.get('q',"") 
        per_page = request.GET.get('per_page',10) 

        prompts = models.Prompts.objects.filter(created_by=request.user).order_by('-pk')
        # print('pk',pk,prompts)
        if query:
            prompts = prompts.filter(
                Q(name__icontains=query) |
                Q(configs__icontains=query)
            )  

        paginator = Paginator(prompts, per_page) # Display 10 tasks per page
        page = request.GET.get('page')
        prompts = paginator.get_page(page)

        return render(request,'home/prompts_landing.html',{'prompts':prompts, 
        'segment' : "prompt","q":query,'per_page':per_page})








@login_required(login_url='login')
def prompt_writer(request): 
    # customer = models.Customer.objects.get(user_id=request.user.id)

    if request.method == 'POST': 
        prompt_name = request.POST.get('name')
        description = request.POST.get('description')
        status = request.POST.get('status',"create")
        content = request.POST.get('content',"")
        is_public = request.POST.get('is_public',"")

        if not prompt_name:
            return JsonResponse({ "error" :f"Name is required!"})        

        try: 
            prompt = models.Prompts.objects.get(name=prompt_name,description=description,created_by=request.user
                )
            
            if status.lower()== 'edit':
                prompt.content=content
                prompt.is_public=is_public or prompt.is_public
                prompt.save() 

                return JsonResponse({ "message" :f"Prompt: {prompt_name} update successfully!"})
            
            else:
                return JsonResponse({ "message" :f"Prompt: {prompt_name} already created by you!"})

        except ObjectDoesNotExist:

            prompt = models.Prompts.objects.create(name=prompt_name,content=content,created_by=request.user)
            prompt.description = description
            prompt.is_public = is_public
            prompt.api_id = replace_with_char(f"{prompt_name}-{request.user.id}-{prompt.pk}-{datetime.now()}")
            print(prompt.api_id)
            prompt.save() 

            return JsonResponse({ 'message':'Prompts created successfully'})


    else:
        status = request.GET.get('status',"create")
        pk = request.GET.get('pk')
        item = None
        if pk:
            item = models.Prompts.objects.get(pk=pk)
            prompt =  item.content
        else:
            prompt="""

Now you are Pye Gpt: A Documentation Search Engine, designed to assist users in finding information within our extensive documentation. Your goal is to help users discover relevant topics and solutions based on their search queries.

Instructions:
1. Users will enter search queries, which can be questions, keywords, or topics related to PYE.
2. Your responses should provide accurate and concise information from our documentation.
3. Prioritize offering solutions, code examples, and step-by-step guides where applicable.
4. If a query has multiple relevant results, you can provide a brief summary and offer to provide more detailed information upon request.
5. If a query has no relevant results, say I don't know and tell them which links to go, if available.
6. Your objective is to enhance the user experience by promptly connecting them with the information they need.

Example Queries:
1. How do I install PYE?
2. What features are available in PYE?
3. Provide an example of sentiment analysis using PYE.
4. How can I integrate PYE with my web application?
5. Troubleshoot common errors when using PYE.

Your responses should be informative, helpful, and presented in a language understandable to users.
            
            """
        print(item)

        return render(request,'home/prompt_editor.html',{'prompt':prompt, 
        'segment' : "prompt","status":status,'pk':pk,'item':item})




def prompt_writer_search(request): 

    query = request.GET.get('q',"") 

    connections = models.Connections.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query)
    ).order_by('-connector__date_created','-connector__time_created').values('pk','name','description','last_date_update',
    'last_time_update','connector__date_created','connector__type_name','connector__created_by__username')     

    connections = connections[0:8]
    for x in connections:
        x['get_prompts'] = models.Chatbot.objects.filter(connection__pk=x.get('pk')).count()

    res = {'results':list(connections)}

    return JsonResponse(res)


def prompt_search(request): 

    query = request.GET.get('q',"") 

    connections = models.Prompts.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query) |
        Q(content__icontains=query)
    ).order_by('-last_update').values('pk','name','description','api_id','last_update', 'created_by__username','content')     

    connections = connections[0:8]
    for x in connections:
        x['get_prompts'] = models.Chatbot.objects.filter(connection__pk=x.get('pk')).count()

    res = {'results':list(connections)}

    return JsonResponse(res)





def prompt_like(request): 

    pk = request.GET.get('pk',"") 

    prompt = models.Prompts.objects.get(pk=pk)
    prompt.like = prompt.like + 1
    prompt.save() 
    res = {'message':f"{prompt.name} Liked"}

    return JsonResponse(res)





@login_required(login_url='login')
def run_prompt(request): 
    if request.method == 'POST': 
        pk = request.POST.get('pk')
        prompt = request.POST.get('prompt')
        message = request.POST.get('message')
        uuid = request.POST.get('uuid')
        try:
            connection = models.Connections.objects.get(pk=pk)

            if message:
                vortex_query = VortexQuery(connection,prompt,str(uuid),save_history=False)
                answer = vortex_query.ask_question(message)
                # print(answer)
                return JsonResponse({'response':answer})


        except Exception as e:
            print("Err @ Chat",e)
            return JsonResponse({ 'message':"Error: "+e}) 


def oauth2_callback(request):
    return redirect('customer-dashboard')