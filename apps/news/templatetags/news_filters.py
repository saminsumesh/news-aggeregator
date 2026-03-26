from django import template

register = template.Library()

@register.filter(name='linebreak_paras')
def linebreak_paras(value):
    """Split text into a list of paragraphs on blank lines."""
    if not value:
        return []
    paragraphs = [p.strip() for p in value.split('\n\n') if p.strip()]
    if not paragraphs:
        paragraphs = [p.strip() for p in value.split('\n') if p.strip()]
    return paragraphs