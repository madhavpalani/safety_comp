from django.contrib import admin
from django.urls import path

from webcam import views

urlpatterns = [
    path('', views.index, name='index'),
    path('video_feed', views.video_feed, name='video_feed'),
    path('alert_history', views.alert_history, name='alert_history'),
    path('web', views.web, name='web'),
    path('video_feed1', views.video_feed1, name='video_feed1'),
    path('web1', views.web1, name='web1'),
    path('history', views.history, name='history'),
    path('visualize', views.visualize, name='visualize')

]
