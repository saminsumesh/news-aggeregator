from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.conf import settings
from .models import Article, Category, Tag, Comment
from .services import NewsAPIService, GroqAIService, ArticleScraper


def home(request):
    """Main news feed"""
    category_slug = request.GET.get('category', '')
    articles = Article.objects.filter(status='published').select_related('category', 'author')

    if category_slug:
        articles = articles.filter(category__slug=category_slug)

    featured = articles.filter(is_featured=True).first()
    breaking = articles.filter(is_breaking=True).order_by('-published_at')[:5]

    paginator = Paginator(articles, settings.ARTICLES_PER_PAGE)
    page = paginator.get_page(request.GET.get('page', 1))

    categories = Category.objects.all()
    trending = Article.objects.filter(status='published').order_by('-view_count')[:5]

    ctx = {
        'articles': page,
        'featured': featured,
        'breaking_news': breaking,
        'categories': categories,
        'trending': trending,
        'current_category': category_slug,
    }
    return render(request, 'news/home.html', ctx)


def article_detail(request, slug):
    """Full article reader - content shown inline, no redirect"""
    article = get_object_or_404(Article, slug=slug, status='published')
    article.increment_views()

    # If content is empty, try to scrape it
    if not article.content and article.source_url:
        scraper = ArticleScraper()
        result = scraper.scrape(article.source_url)
        if result.get('success') and result.get('text'):
            article.content = result['text']
            article.save(update_fields=['content'])

    comments = article.comments.filter(is_approved=True)
    related = Article.objects.filter(
        status='published', category=article.category
    ).exclude(pk=article.pk).order_by('-published_at')[:4]

    ctx = {
        'article': article,
        'comments': comments,
        'related': related,
        'categories': Category.objects.all(),
    }
    return render(request, 'news/article_detail.html', ctx)


def search(request):
    q = request.GET.get('q', '').strip()
    articles = Article.objects.none()
    if q:
        articles = Article.objects.filter(
            status='published'
        ).filter(
            Q(title__icontains=q) | Q(summary__icontains=q) | Q(content__icontains=q)
        )
    paginator = Paginator(articles, settings.ARTICLES_PER_PAGE)
    page = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'news/search.html', {
        'articles': page,
        'query': q,
        'categories': Category.objects.all(),
    })


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    articles = Article.objects.filter(status='published', category=category)
    paginator = Paginator(articles, settings.ARTICLES_PER_PAGE)
    page = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'news/category.html', {
        'category': category,
        'articles': page,
        'categories': Category.objects.all(),
    })


@login_required
@require_POST
def add_comment(request, slug):
    article = get_object_or_404(Article, slug=slug, status='published')
    content = request.POST.get('content', '').strip()
    if content:
        Comment.objects.create(article=article, user=request.user, content=content)
        messages.success(request, 'Comment posted!')
    return redirect('news:article_detail', slug=slug)


# ─── Admin / Reporter AJAX actions ─────────────────────────────────────────

def is_reporter(user):
    return user.is_authenticated and (user.is_reporter() or user.is_staff)


@login_required
@user_passes_test(is_reporter)
def fetch_news_api(request):
    """Trigger NewsAPI fetch for India news (AJAX or GET)"""
    category = request.GET.get('category', 'general')
    service = NewsAPIService()
    cat_obj = (
        Category.objects.filter(slug=category).first() or
        Category.objects.filter(name__iexact=category).first()
    )

    # Map category to India-focused search queries
    # (free NewsAPI plan doesn't support country filter on /everything,
    #  so we embed India keywords directly in the query)
    category_queries = {
        'technology': 'India technology OR tech OR startup OR AI',
        'business':   'India business OR economy OR market OR finance',
        'sports':     'India sports OR cricket OR IPL OR football',
        'health':     'India health OR medicine OR hospital OR healthcare',
        'science':    'India science OR research OR ISRO OR space',
        'entertainment': 'India entertainment OR Bollywood OR OTT OR cinema',
        'politics':   'India politics OR government OR parliament OR election',
        'general':    'India news latest',
    }
    query = category_queries.get(category, f'India {category}')
    raw = service.fetch_everything(query=query, page_size=20)

    saved = service.save_articles(raw, category_obj=cat_obj)
    from .models import NewsAPIFetchLog
    NewsAPIFetchLog.objects.create(
        category=category,
        articles_fetched=len(raw),
        articles_saved=saved,
        success=True,
    )
    return JsonResponse({'status': 'ok', 'fetched': len(raw), 'saved': saved})


@login_required
@user_passes_test(is_reporter)
def ai_process_article(request, pk):
    """Run AI summarization + rephrasing on an article"""
    from .models import Article
    article = get_object_or_404(Article, pk=pk)
    ai = GroqAIService()

    content = article.content or article.summary or article.title
    summary = ai.summarize(article.title, content)
    rephrased = ai.rephrase(article.title, content)
    tags = ai.generate_tags(article.title, content)

    if summary:
        article.summary = summary
    if rephrased:
        article.rephrased_content = rephrased
    article.ai_processed = True
    article.save()

    # Save tags
    for tag_name in tags:
        tag, _ = Tag.objects.get_or_create(name=tag_name, defaults={'slug': tag_name.replace(' ', '-')})
        article.tags.add(tag)

    return JsonResponse({'status': 'ok', 'summary': summary, 'rephrased': rephrased, 'tags': tags})


@login_required
@user_passes_test(is_reporter)
def scrape_article(request, pk):
    """Scrape full content for an article"""
    from .models import Article
    article = get_object_or_404(Article, pk=pk)
    if not article.source_url:
        return JsonResponse({'status': 'error', 'message': 'No source URL'})
    scraper = ArticleScraper()
    result = scraper.scrape(article.source_url)
    if result.get('success') and result.get('text'):
        article.content = result['text']
        article.save(update_fields=['content'])
        return JsonResponse({'status': 'ok', 'length': len(result['text'])})
    return JsonResponse({'status': 'error', 'message': 'Scrape failed'})
