"""
URL Configuration for the expenses app.

Each path() maps a URL pattern to a view function.
The name= parameter lets us reference URLs in templates with {% url 'name' %}
instead of hardcoding paths.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),           # Root URL shows login
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Expense CRUD
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.add_expense, name='add_expense'),
    path('expenses/<int:pk>/edit/', views.edit_expense, name='edit_expense'),
    path('expenses/<int:pk>/delete/', views.delete_expense, name='delete_expense'),

    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/<int:pk>/delete/', views.delete_category, name='delete_category'),

    # Export
    path('expenses/export/csv/', views.export_csv, name='export_csv'),
]
