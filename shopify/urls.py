from django.urls import path, include
from . import views
from django.contrib.auth.views import LoginView

urlpatterns = [
   
    path('submit', views.submit,name='submit'),
    path('themes', views.themes,name='themes'),
    path('select-theme', views.select_theme,name='select-theme'),
    path('training-data', views.training_data ,name='training-data '),
    path('train-status', views.training_status ,name='training-status '),
   

]