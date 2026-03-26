from django import forms
from apps.news.models import Article, Category, Tag


class ArticleForm(forms.ModelForm):
    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. technology, AI, startup (comma separated)',
        }),
        help_text='Enter tags separated by commas'
    )

    class Meta:
        model = Article
        fields = ['title', 'summary', 'content', 'category', 'image_url', 'is_featured', 'is_breaking']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Article headline...'}),
            'summary': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Brief summary...'}),
            'content': forms.Textarea(attrs={'class': 'form-input editor-textarea', 'rows': 15, 'placeholder': 'Write your full article here...'}),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'image_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'is_breaking': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        if self.instance and self.instance.pk:
            self.fields['tags_input'].initial = ', '.join(
                self.instance.tags.values_list('name', flat=True)
            )

    def save(self, commit=True):
        article = super().save(commit=False)
        if commit:
            article.save()
            # Handle tags
            tags_raw = self.cleaned_data.get('tags_input', '')
            article.tags.clear()
            for t in tags_raw.split(','):
                t = t.strip().lower()
                if t:
                    from django.utils.text import slugify
                    tag, _ = Tag.objects.get_or_create(name=t, defaults={'slug': slugify(t)})
                    article.tags.add(tag)
        return article
