from django.db import models
from apps.accounts.models import User
from apps.news.models import Article, Category


class ReporterProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='reporter_profile')
    desk = models.CharField(max_length=100, blank=True, help_text='e.g. Politics, Sports')
    articles_published = models.PositiveIntegerField(default=0)
    articles_pending = models.PositiveIntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reporter: {self.user.username}"


class ArticleSubmission(models.Model):
    """Tracks reporter-submitted articles through workflow"""
    article = models.OneToOneField(Article, on_delete=models.CASCADE, related_name='submission')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    notes = models.TextField(blank=True, help_text='Reporter notes for editor')
    editor_feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_submissions')

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.reporter.username} → {self.article.title[:60]}"
