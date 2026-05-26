"""
Register models with the Django admin site.
This gives you a free admin panel at /admin/ to manage data.
"""

from django.contrib import admin
from .models import Expense, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'icon', 'color']
    list_filter = ['user']
    search_fields = ['name']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'amount', 'category', 'user', 'date']
    list_filter = ['category', 'user', 'date']
    search_fields = ['title', 'description']
    date_hierarchy = 'date'
