"""
Main URL configuration for expense_tracker project.
This file routes incoming URLs to the correct app.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # All URLs from the expenses app
    path('', include('expenses.urls')),
]
