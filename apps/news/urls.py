from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('article/<slug:slug>/', views.article_detail, name='article_detail'),
    path('article/<slug:slug>/comment/', views.add_comment, name='add_comment'),
    path('api/fetch/', views.fetch_news_api, name='fetch_news_api'),
    path('api/ai-process/<uuid:pk>/', views.ai_process_article, name='ai_process_article'),
    path('api/scrape/<uuid:pk>/', views.scrape_article, name='scrape_article'),
]
