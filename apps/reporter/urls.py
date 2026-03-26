from django.urls import path
from . import views

app_name = 'reporter'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('articles/', views.article_list, name='article_list'),
    path('articles/new/', views.article_create, name='article_create'),
    path('articles/<uuid:pk>/edit/', views.article_edit, name='article_edit'),
    path('articles/<uuid:pk>/delete/', views.article_delete, name='article_delete'),
    path('articles/<uuid:pk>/ai/', views.ai_assist, name='ai_assist'),
]
