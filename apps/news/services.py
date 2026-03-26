import requests
import json
import re
from django.conf import settings
from django.utils import timezone
from datetime import datetime


class NewsAPIService:
    """Service to fetch news from NewsAPI.org"""

    BASE_URL = settings.NEWS_API_BASE_URL
    API_KEY = settings.NEWS_API_KEY

    def fetch_top_headlines(self, category='general', country='in', page_size=20):
        """Fetch top headlines from India by category"""
        try:
            resp = requests.get(
                f"{self.BASE_URL}/top-headlines",
                params={
                    'apiKey': self.API_KEY,
                    'category': category,
                    'country': country,
                    'pageSize': page_size,
                },
                timeout=10
            )
            data = resp.json()
            if data.get('status') == 'ok':
                return data.get('articles', [])
            return []
        except Exception as e:
            print(f"NewsAPI error: {e}")
            return []

    def fetch_everything(self, query, page_size=20, sort_by='publishedAt'):
        """Search all news"""
        try:
            resp = requests.get(
                f"{self.BASE_URL}/everything",
                params={
                    'apiKey': self.API_KEY,
                    'q': query,
                    'pageSize': page_size,
                    'sortBy': sort_by,
                    'language': 'en',
                },
                timeout=10
            )
            data = resp.json()
            if data.get('status') == 'ok':
                return data.get('articles', [])
            return []
        except Exception as e:
            print(f"NewsAPI error: {e}")
            return []

    def save_articles(self, api_articles, category_obj=None, source_type='api'):
        """Save fetched articles to database, auto-scrape full content and auto-run AI"""
        from apps.news.models import Article, Tag
        scraper = ArticleScraper()
        ai = GroqAIService()
        saved = 0

        for item in api_articles:
            if not item.get('url') or not item.get('title') or item['title'] == '[Removed]':
                continue

            api_id = item.get('url', '')[:499]
            if Article.objects.filter(api_id=api_id).exists():
                continue

            published_at = None
            if item.get('publishedAt'):
                try:
                    published_at = datetime.fromisoformat(item['publishedAt'].replace('Z', '+00:00'))
                except Exception:
                    published_at = timezone.now()

            # Auto-scrape full article content
            source_url = item.get('url', '')
            full_content = ''
            if source_url:
                try:
                    scraped = scraper.scrape(source_url)
                    if scraped.get('success') and scraped.get('text'):
                        full_content = scraped['text']
                except Exception as e:
                    print(f"Auto-scrape failed for {source_url}: {e}")

            content = full_content or item.get('content') or item.get('description') or ''

            article = Article(
                title=item.get('title', '')[:499],
                original_title=item.get('title', '')[:499],
                summary=item.get('description') or '',
                content=content,
                image_url=item.get('urlToImage') or '',
                source_url=source_url,
                source_name=item.get('source', {}).get('name', ''),
                category=category_obj,
                status='published',
                source_type=source_type,
                published_at=published_at or timezone.now(),
                api_id=api_id,
            )
            try:
                article.save()

                # Auto-run AI summarization and rephrasing
                if content:
                    try:
                        summary = ai.summarize(article.title, content)
                        rephrased = ai.rephrase(article.title, content)
                        tags = ai.generate_tags(article.title, content)
                        if summary:
                            article.summary = summary
                        if rephrased:
                            article.rephrased_content = rephrased
                        article.ai_processed = True
                        article.save(update_fields=['summary', 'rephrased_content', 'ai_processed'])
                        for tag_name in (tags or []):
                            tag, _ = Tag.objects.get_or_create(
                                name=tag_name,
                                defaults={'slug': tag_name.replace(' ', '-')}
                            )
                            article.tags.add(tag)
                    except Exception as e:
                        print(f"Auto-AI failed for {article.title[:60]}: {e}")

                saved += 1
            except Exception as e:
                print(f"Error saving article: {e}")

        return saved


class ArticleScraper:
    """Scrape full article content from URL using newspaper3k"""

    def scrape(self, url):
        """Attempt to scrape article content. Returns dict with title, text, image."""
        try:
            import newspaper
            art = newspaper.Article(url)
            art.download()
            art.parse()
            return {
                'title': art.title,
                'text': art.text,
                'image': art.top_image,
                'authors': art.authors,
                'success': True,
            }
        except ImportError:
            return self._basic_scrape(url)
        except Exception as e:
            print(f"Scrape error for {url}: {e}")
            return {'success': False, 'text': '', 'title': ''}

    def _basic_scrape(self, url):
        """Fallback scraper using requests + basic HTML parsing"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; NewsBot/1.0)'
            }
            resp = requests.get(url, headers=headers, timeout=8)
            from html.parser import HTMLParser

            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text_parts = []
                    self.skip_tags = {'script', 'style', 'nav', 'header', 'footer', 'aside'}
                    self._skip = False

                def handle_starttag(self, tag, attrs):
                    if tag in self.skip_tags:
                        self._skip = True

                def handle_endtag(self, tag):
                    if tag in self.skip_tags:
                        self._skip = False

                def handle_data(self, data):
                    if not self._skip and data.strip():
                        self.text_parts.append(data.strip())

            parser = TextExtractor()
            parser.feed(resp.text)
            text = ' '.join(parser.text_parts)
            return {'success': True, 'text': text[:5000], 'title': ''}
        except Exception as e:
            return {'success': False, 'text': '', 'title': ''}


class GroqAIService:
    """Free AI summarization and rephrasing via Groq API"""

    API_URL = settings.GROQ_API_URL
    API_KEY = settings.GROQ_API_KEY
    MODEL = settings.GROQ_MODEL

    def _call(self, messages, max_tokens=1000):
        try:
            resp = requests.post(
                self.API_URL,
                headers={
                    'Authorization': f'Bearer {self.API_KEY}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': self.MODEL,
                    'messages': messages,
                    'max_tokens': max_tokens,
                    'temperature': 0.7,
                },
                timeout=30
            )
            data = resp.json()
            if 'choices' in data:
                return data['choices'][0]['message']['content'].strip()
            print(f"Groq error: {data}")
            return None
        except Exception as e:
            print(f"Groq API error: {e}")
            return None

    def summarize(self, title, content, length='medium'):
        """Generate a journalistic summary of the article"""
        length_map = {
            'short': '2-3 sentences',
            'medium': '4-5 sentences',
            'long': '2 short paragraphs'
        }
        prompt = f"""You are a professional news editor. Write a clear, engaging {length_map.get(length, '4-5 sentences')} summary of this article.
Write in active voice, present the most important facts first. Sound like a real journalist, not AI.

Title: {title}

Content: {content[:3000]}

Write ONLY the summary, no preamble."""

        return self._call([{'role': 'user', 'content': prompt}], max_tokens=400)

    def rephrase(self, title, content):
        """Rephrase article content in reporter's voice"""
        prompt = f"""You are a skilled news reporter. Rewrite the following news article in a professional, engaging journalistic style.
- Use clear paragraphs (4-6 sentences each)
- Start with the most important facts (inverted pyramid)
- Use active voice and concrete details
- Sound like a real journalist writing for a major publication
- DO NOT copy sentences verbatim from the original
- Keep all facts accurate

Title: {title}

Original content: {content[:3000]}

Write ONLY the rephrased article with 3-4 paragraphs. No headline, no intro label."""

        return self._call([{'role': 'user', 'content': prompt}], max_tokens=800)

    def generate_tags(self, title, content):
        """Generate relevant tags for an article"""
        prompt = f"""Extract 5-8 relevant topic tags from this news article.
Return ONLY a comma-separated list of tags, lowercase, no hashtags.
Example: technology, artificial intelligence, openai, chatgpt, silicon valley

Title: {title}
Content: {content[:1000]}"""
        result = self._call([{'role': 'user', 'content': prompt}], max_tokens=100)
        if result:
            return [t.strip() for t in result.split(',') if t.strip()]
        return []
