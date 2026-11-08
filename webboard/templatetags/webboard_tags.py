"""Custom template filters and tags for webboard emoticons and rendering."""

from django import template
from webboard.emoticons import get_msn_emoticons_list, render_webboard_content

register = template.Library()


@register.filter(name="format_webboard")
def format_webboard(value: str) -> str:
    """Format and render webboard text with safe emoticons and GIF embeds."""
    return render_webboard_content(value or "")


@register.simple_tag(name="get_msn_emoticons")
def get_msn_emoticons():
    """Return the curated list of MSN emoticons for toolbar palette."""
    return get_msn_emoticons_list()
