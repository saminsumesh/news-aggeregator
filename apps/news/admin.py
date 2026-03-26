from django.contrib import admin
from .models import Article, Category, Tag, Comment, NewsAPIFetchLog


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'color']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'status', 'source_type', 'ai_processed', 'view_count', 'published_at']
    list_filter = ['status', 'source_type', 'ai_processed', 'category']
    search_fields = ['title', 'summary', 'content']
    readonly_fields = ['id', 'view_count', 'created_at', 'updated_at', 'api_id']
    list_per_page = 30


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'article', 'is_approved', 'created_at']
    list_filter = ['is_approved']


@admin.register(NewsAPIFetchLog)
class FetchLogAdmin(admin.ModelAdmin):
    list_display = ['fetched_at', 'category', 'articles_fetched', 'articles_saved', 'success']
    readonly_fields = ['fetched_at']
