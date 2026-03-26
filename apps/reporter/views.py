from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from apps.news.models import Article, Category
from apps.news.services import GroqAIService
from .models import ReporterProfile, ArticleSubmission
from .forms import ArticleForm


def reporter_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.conf import settings
            return redirect(settings.LOGIN_URL + f'?next={request.path}')
        if not (request.user.is_reporter() or request.user.is_staff):
            messages.error(request, 'Reporter access required.')
            return redirect('news:home')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@reporter_required
def dashboard(request):
    user = request.user
    my_articles = Article.objects.filter(author=user).order_by('-created_at')

    stats = {
        'total': my_articles.count(),
        'published': my_articles.filter(status='published').count(),
        'draft': my_articles.filter(status='draft').count(),
        'pending': my_articles.filter(status='pending').count(),
        'views': sum(a.view_count for a in my_articles),
    }

    recent = my_articles[:10]
    profile, _ = ReporterProfile.objects.get_or_create(user=user)

    return render(request, 'reporter/dashboard.html', {
        'stats': stats,
        'recent_articles': recent,
        'profile': profile,
        'categories': Category.objects.all(),
    })


@login_required
@reporter_required
def article_list(request):
    articles = Article.objects.filter(author=request.user)
    status_filter = request.GET.get('status', '')
    if status_filter:
        articles = articles.filter(status=status_filter)
    q = request.GET.get('q', '')
    if q:
        articles = articles.filter(Q(title__icontains=q) | Q(summary__icontains=q))

    from django.core.paginator import Paginator
    paginator = Paginator(articles.order_by('-created_at'), 15)
    page = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'reporter/article_list.html', {
        'articles': page,
        'status_filter': status_filter,
        'query': q,
    })


@login_required
@reporter_required
def article_create(request):
    form = ArticleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        article = form.save(commit=False)
        article.author = request.user
        article.source_type = 'manual'
        action = request.POST.get('action', 'draft')
        if action == 'publish':
            article.status = 'published'
        elif action == 'submit':
            article.status = 'pending'
        else:
            article.status = 'draft'
        article.save()
        form.save()  # triggers tag M2M
        messages.success(request, f'Article {"published" if article.status == "published" else "saved"}!')
        return redirect('reporter:article_edit', pk=article.pk)

    return render(request, 'reporter/article_editor.html', {
        'form': form,
        'article': None,
        'categories': Category.objects.all(),
    })


@login_required
@reporter_required
def article_edit(request, pk):
    article = get_object_or_404(Article, pk=pk, author=request.user)
    form = ArticleForm(request.POST or None, instance=article)

    if request.method == 'POST' and form.is_valid():
        article = form.save(commit=False)
        action = request.POST.get('action', 'draft')
        if action == 'publish':
            article.status = 'published'
        elif action == 'submit':
            article.status = 'pending'
        else:
            article.status = 'draft'
        article.save()
        form.save()
        messages.success(request, 'Article updated!')
        return redirect('reporter:article_edit', pk=article.pk)

    return render(request, 'reporter/article_editor.html', {
        'form': form,
        'article': article,
        'categories': Category.objects.all(),
    })


@login_required
@reporter_required
def article_delete(request, pk):
    article = get_object_or_404(Article, pk=pk, author=request.user)
    if request.method == 'POST':
        article.delete()
        messages.success(request, 'Article deleted.')
        return redirect('reporter:article_list')
    return render(request, 'reporter/article_confirm_delete.html', {'article': article})


@login_required
@reporter_required
def ai_assist(request, pk):
    """AJAX: AI summarize/rephrase for reporter's own article"""
    article = get_object_or_404(Article, pk=pk, author=request.user)
    action = request.GET.get('action', 'summarize')
    ai = GroqAIService()
    content = article.content or article.summary or article.title

    if action == 'summarize':
        result = ai.summarize(article.title, content)
        if result:
            article.summary = result
            article.save(update_fields=['summary', 'ai_processed'])
            article.ai_processed = True
            article.save(update_fields=['ai_processed'])
        return JsonResponse({'status': 'ok', 'result': result})

    elif action == 'rephrase':
        result = ai.rephrase(article.title, content)
        if result:
            article.rephrased_content = result
            article.ai_processed = True
            article.save(update_fields=['rephrased_content', 'ai_processed'])
        return JsonResponse({'status': 'ok', 'result': result})

    elif action == 'tags':
        tags = ai.generate_tags(article.title, content)
        from apps.news.models import Tag
        from django.utils.text import slugify
        for t in tags:
            tag, _ = Tag.objects.get_or_create(name=t, defaults={'slug': slugify(t)})
            article.tags.add(tag)
        return JsonResponse({'status': 'ok', 'tags': tags})

    return JsonResponse({'status': 'error', 'message': 'Unknown action'})
