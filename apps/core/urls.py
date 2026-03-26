from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('articles/', views.manage_articles, name='manage_articles'),
    path('articles/<uuid:pk>/action/', views.article_action, name='article_action'),
    path('users/', views.manage_users, name='manage_users'),
    path('users/<int:pk>/action/', views.user_action, name='user_action'),
    path('categories/', views.manage_categories, name='manage_categories'),
    path('comments/', views.manage_comments, name='manage_comments'),
    path('comments/<int:pk>/action/', views.comment_action, name='comment_action'),
    path('fetch/', views.fetch_news_trigger, name='fetch_news_trigger'),
    path('bulk-ai/', views.bulk_ai_process, name='bulk_ai_process'),
]
