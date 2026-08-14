from django import template
from datetime import date

register = template.Library()

@register.simple_tag
def make_date_tag(day, year, month):
    """Create a date object from day, month, year"""
    if day == 0:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if dictionary is None:
        return []
    return dictionary.get(key, [])

@register.filter
def multiply(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divide value by arg"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0