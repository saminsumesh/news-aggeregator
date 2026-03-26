#!/usr/bin/env python
"""
PulseNews Setup Script
Run: python setup.py
This seeds the database with default categories and creates a superuser.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsagg.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.news.models import Category
from apps.accounts.models import User

# ── Seed Categories ────────────────────────────────
CATEGORIES = [
    {'name': 'Technology', 'slug': 'technology', 'icon': '💻', 'color': '#3B82F6'},
    {'name': 'Business',   'slug': 'business',   'icon': '💼', 'color': '#10B981'},
    {'name': 'Sports',     'slug': 'sports',     'icon': '⚽', 'color': '#F59E0B'},
    {'name': 'Health',     'slug': 'health',     'icon': '🏥', 'color': '#EC4899'},
    {'name': 'Science',    'slug': 'science',    'icon': '🔬', 'color': '#8B5CF6'},
    {'name': 'Entertainment','slug':'entertainment','icon':'🎬','color': '#EF4444'},
    {'name': 'General',    'slug': 'general',    'icon': '📰', 'color': '#6B7280'},
    {'name': 'Politics',   'slug': 'politics',   'icon': '🏛️', 'color': '#1E40AF'},
]

print("📂 Creating categories...")
for cat_data in CATEGORIES:
    obj, created = Category.objects.get_or_create(
        slug=cat_data['slug'],
        defaults=cat_data
    )
    status = '✓ Created' if created else '→ Already exists'
    print(f"   {status}: {cat_data['name']}")

# ── Create Superuser ───────────────────────────────
print("\n👤 Creating superuser...")
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@pulsenews.com',
        password='admin123',
        role='admin',
    )
    print("   ✓ Superuser created: admin / admin123")
    print("   ⚠️  CHANGE THE PASSWORD before going live!")
else:
    print("   → Superuser 'admin' already exists")

# ── Create Demo Reporter ───────────────────────────
print("\n✏️  Creating demo reporter...")
if not User.objects.filter(username='reporter1').exists():
    User.objects.create_user(
        username='reporter1',
        email='reporter@pulsenews.com',
        password='reporter123',
        role='reporter',
        is_staff=True,
    )
    print("   ✓ Reporter created: reporter1 / reporter123")
else:
    print("   → Reporter 'reporter1' already exists")

print("\n🎉 Setup complete!")
print("   Run the server: python manage.py runserver")
print("   Visit: http://127.0.0.1:8000")
print("   Admin panel: http://127.0.0.1:8000/admin-panel/")
print("   Django admin: http://127.0.0.1:8000/django-admin/")
