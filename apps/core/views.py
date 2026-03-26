from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Sum, Q
from apps.news.models import Article, Category, Comment, NewsAPIFetchLog
from apps.accounts.models import User
from apps.news.services import NewsAPIService, GroqAIService


def admin_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.conf import settings
            return redirect(settings.LOGIN_URL + f'?next={request.path}')
        if not (request.user.is_admin_user() or request.user.is_staff):
            messages.error(request, 'Admin access required.')
            return redirect('news:home')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@admin_required
def admin_dashboard(request):
    # Stats
    total_articles = Article.objects.count()
    published = Article.objects.filter(status='published').count()
    pending = Article.objects.filter(status='pending').count()
    total_users = User.objects.count()
    reporters = User.objects.filter(role='reporter').count()
    total_views = Article.objects.aggregate(v=Sum('view_count'))['v'] or 0
    recent_articles = Article.objects.order_by('-created_at')[:10]
    recent_users = User.objects.order_by('-date_joined')[:5]
    fetch_logs = NewsAPIFetchLog.objects.order_by('-fetched_at')[:5]
    categories = Category.objects.annotate(article_count=Count('articles')).order_by('-article_count')

    ctx = {
        'stats': {
            'total_articles': total_articles,
            'published': published,
            'pending': pending,
            'total_users': total_users,
            'reporters': reporters,
            'total_views': total_views,
        },
        'recent_articles': recent_articles,
        'recent_users': recent_users,
        'fetch_logs': fetch_logs,
        'categories': categories,
    }
    return render(request, 'admin_panel/dashboard.html', ctx)


@login_required
@admin_required
def manage_articles(request):
    articles = Article.objects.select_related('author', 'category').order_by('-created_at')
    status_filter = request.GET.get('status', '')
    source_filter = request.GET.get('source', '')
    q = request.GET.get('q', '')

    if status_filter:
        articles = articles.filter(status=status_filter)
    if source_filter:
        articles = articles.filter(source_type=source_filter)
    if q:
        articles = articles.filter(Q(title__icontains=q) | Q(source_name__icontains=q))

    from django.core.paginator import Paginator
    paginator = Paginator(articles, 20)
    page = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'admin_panel/articles.html', {
        'articles': page,
        'status_filter': status_filter,
        'source_filter': source_filter,
        'query': q,
    })


@login_required
@admin_required
def article_action(request, pk):
    """Approve, reject, feature, publish, delete"""
    article = get_object_or_404(Article, pk=pk)
    action = request.POST.get('action', '')

    if action == 'publish':
        article.status = 'published'
        article.published_at = timezone.now()
        article.save()
        messages.success(request, 'Article published.')
    elif action == 'reject':
        article.status = 'rejected'
        article.save()
        messages.warning(request, 'Article rejected.')
    elif action == 'feature':
        article.is_featured = not article.is_featured
        article.save()
        messages.success(request, f'Article {"featured" if article.is_featured else "unfeatured"}.')
    elif action == 'breaking':
        article.is_breaking = not article.is_breaking
        article.save()
        messages.success(request, f'Article {"marked as breaking" if article.is_breaking else "removed from breaking"}.')
    elif action == 'delete':
        article.delete()
        messages.success(request, 'Article deleted.')
        return redirect('core:manage_articles')
    elif action == 'archive':
        article.status = 'archived'
        article.save()
        messages.info(request, 'Article archived.')

    return redirect(request.META.get('HTTP_REFERER', 'core:manage_articles'))


@login_required
@admin_required
def manage_users(request):
    users = User.objects.order_by('-date_joined')
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)

    from django.core.paginator import Paginator
    paginator = Paginator(users, 20)
    page = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'admin_panel/users.html', {
        'users': page,
        'role_filter': role_filter,
    })


@login_required
@admin_required
def user_action(request, pk):
    user = get_object_or_404(User, pk=pk)
    action = request.POST.get('action', '')

    if action == 'make_reporter':
        user.role = 'reporter'
        user.save()
        messages.success(request, f'{user.username} is now a Reporter.')
    elif action == 'make_admin':
        user.role = 'admin'
        user.is_staff = True
        user.save()
        messages.success(request, f'{user.username} is now an Admin.')
    elif action == 'make_reader':
        user.role = 'reader'
        user.is_staff = False
        user.save()
        messages.info(request, f'{user.username} set to Reader.')
    elif action == 'toggle_active':
        user.is_active = not user.is_active
        user.save()
        messages.info(request, f'{user.username} {"activated" if user.is_active else "deactivated"}.')

    return redirect('core:manage_users')


@login_required
@admin_required
def manage_categories(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            name = request.POST.get('name', '').strip()
            icon = request.POST.get('icon', '📰')
            color = request.POST.get('color', '#3B82F6')
            if name:
                from django.utils.text import slugify
                Category.objects.get_or_create(
                    slug=slugify(name),
                    defaults={'name': name, 'icon': icon, 'color': color}
                )
                messages.success(request, f'Category "{name}" created.')
        elif action == 'delete':
            cat_id = request.POST.get('cat_id')
            Category.objects.filter(pk=cat_id).delete()
            messages.success(request, 'Category deleted.')
        return redirect('core:manage_categories')

    categories = Category.objects.annotate(article_count=Count('articles'))
    return render(request, 'admin_panel/categories.html', {'categories': categories})


@login_required
@admin_required
def fetch_news_trigger(request):
    """Admin trigger to fetch news for all or specific categories"""
    from django.conf import settings
    category = request.GET.get('category', 'general')
    service = NewsAPIService()
    cat_obj = Category.objects.filter(slug=category).first()
    raw = service.fetch_top_headlines(category=category, page_size=20)
    saved = service.save_articles(raw, category_obj=cat_obj)
    NewsAPIFetchLog.objects.create(
        category=category,
        articles_fetched=len(raw),
        articles_saved=saved,
        success=True,
    )
    messages.success(request, f'Fetched {len(raw)} articles, saved {saved} new for "{category}".')
    return redirect(request.META.get('HTTP_REFERER', 'core:admin_dashboard'))


@login_required
@admin_required
def bulk_ai_process(request):
    """Run AI on all unprocessed published articles"""
    articles = Article.objects.filter(ai_processed=False, status='published')[:10]
    ai = GroqAIService()
    processed = 0
    for article in articles:
        content = article.content or article.summary or article.title
        summary = ai.summarize(article.title, content)
        if summary:
            article.summary = summary
            article.ai_processed = True
            article.save(update_fields=['summary', 'ai_processed'])
            processed += 1
    messages.success(request, f'AI processed {processed} articles.')
    return redirect(request.META.get('HTTP_REFERER', 'core:admin_dashboard'))


@login_required
@admin_required
def manage_comments(request):
    comments = Comment.objects.select_related('user', 'article').order_by('-created_at')
    from django.core.paginator import Paginator
    paginator = Paginator(comments, 30)
    page = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'admin_panel/comments.html', {'comments': page})


@login_required
@admin_required
def comment_action(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    action = request.POST.get('action', '')
    if action == 'approve':
        comment.is_approved = True
        comment.save()
    elif action == 'delete':
        comment.delete()
        messages.success(request, 'Comment deleted.')
    return redirect(request.META.get('HTTP_REFERER', 'core:manage_comments'))
