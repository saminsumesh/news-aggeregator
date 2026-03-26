from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from apps.accounts.models import User
import uuid


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, default='📰')
    color = models.CharField(max_length=20, default='#3B82F6')
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Article(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Review'),
        ('published', 'Published'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived'),
    ]
    SOURCE_CHOICES = [
        ('api', 'NewsAPI'),
        ('manual', 'Reporter Written'),
        ('scraped', 'Scraped'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=500, unique=True, blank=True)
    original_title = models.CharField(max_length=500, blank=True)
    summary = models.TextField(blank=True, help_text='AI-generated or manual summary')
    content = models.TextField(blank=True, help_text='Full article content (scraped or written)')
    rephrased_content = models.TextField(blank=True, help_text='AI-rephrased content')
    image_url = models.URLField(blank=True)
    source_url = models.URLField(blank=True)
    source_name = models.CharField(max_length=200, blank=True)
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='articles')
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='articles')
    tags = models.ManyToManyField(Tag, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='api')
    is_featured = models.BooleanField(default=False)
    is_breaking = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    api_id = models.CharField(max_length=500, blank=True, unique=True, null=True)
    ai_processed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:480]
            slug = base_slug
            counter = 1
            while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def increment_views(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def get_display_content(self):
        """Returns best available content for display"""
        if self.rephrased_content:
            return self.rephrased_content
        if self.content:
            return self.content
        return self.summary

    def __str__(self):
        return self.title[:80]


class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} on {self.article.title[:40]}"


class NewsAPIFetchLog(models.Model):
    fetched_at = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=100)
    articles_fetched = models.IntegerField(default=0)
    articles_saved = models.IntegerField(default=0)
    error = models.TextField(blank=True)
    success = models.BooleanField(default=True)

    class Meta:
        ordering = ['-fetched_at']
