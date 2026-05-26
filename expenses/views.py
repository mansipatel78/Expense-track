"""
Views handle the logic between models and templates.

Each view function:
1. Receives an HTTP request
2. Processes data (read/write from database)
3. Returns an HTTP response (usually renders a template)

@login_required decorator ensures only logged-in users can access a view.
"""

import csv
import json
import calendar
from datetime import datetime, date
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from decimal import Decimal

from .models import Expense, Category
from .forms import UserRegisterForm, ExpenseForm, CategoryForm, ExpenseFilterForm


def register_view(request):

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create default categories for the new user
            _create_default_categories(user)
            login(request, user)  # Log them in immediately after registration
            messages.success(request, f'Welcome, {user.first_name}! Your account has been created.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = UserRegisterForm()

    return render(request, 'expenses/register.html', {'form': form})


def login_view(request):
   
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                # Redirect to the page they were trying to visit, or dashboard
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    return render(request, 'expenses/login.html', {'form': form})


def logout_view(request):
    """Log the user out and redirect to login page."""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')



@login_required
def dashboard(request):

    today = date.today()
    current_month = today.month
    current_year = today.year

    # Get all expenses for the logged-in user
    user_expenses = Expense.objects.filter(user=request.user)

    # This month's expenses
    monthly_expenses = user_expenses.filter(
        date__month=current_month,
        date__year=current_year
    )

    # Calculate totals using Django ORM aggregation
    # aggregate() performs SQL SUM/COUNT on the queryset
    total_this_month = monthly_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    monthly_budget = Decimal('10000')
    budget_exceeded = total_this_month >= monthly_budget

    total_all_time = user_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    expense_count = user_expenses.count()

    # Recent 5 expenses for the dashboard feed
    recent_expenses = user_expenses.select_related('category')[:5]

    # Category breakdown for pie chart
    # values() groups by category, annotate() adds the sum
    category_data = monthly_expenses.values(
        'category__name', 'category__color'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')

    # Prepare chart data as JSON (Chart.js needs this format)
    chart_labels = [item['category__name'] or 'Uncategorized' for item in category_data]
    chart_amounts = [float(item['total']) for item in category_data]
    chart_colors = [item['category__color'] or '#36A2EB' for item in category_data]

    # Monthly trend for the last 6 months (bar chart)
    monthly_trend = []
    for i in range(5, -1, -1):
        month_offset = (current_month - i - 1) % 12 + 1
        year_offset = current_year - ((current_month - i - 1) // 12)
        month_total = user_expenses.filter(
            date__month=month_offset,
            date__year=year_offset
        ).aggregate(total=Sum('amount'))['total'] or 0
        monthly_trend.append({
            'month': calendar.month_abbr[month_offset],
            'total': float(month_total)
        })

    context = {
        'total_this_month': total_this_month,
        'total_all_time': total_all_time,
        'expense_count': expense_count,
        'recent_expenses': recent_expenses,
        'current_month_name': calendar.month_name[current_month],
        'chart_labels': json.dumps(chart_labels),
        'chart_amounts': json.dumps(chart_amounts),
        'chart_colors': json.dumps(chart_colors),
        'monthly_trend_labels': json.dumps([m['month'] for m in monthly_trend]),
        'monthly_trend_data': json.dumps([m['total'] for m in monthly_trend]),
        'category_data': category_data,
        'monthly_budget': monthly_budget,
        'budget_exceeded': budget_exceeded,
    }

    return render(request, 'expenses/dashboard.html', context)


@login_required
def expense_list(request):

    filter_form = ExpenseFilterForm(request.user, request.GET)
    
    # Start with all user's expenses
    expenses = Expense.objects.filter(user=request.user).select_related('category')

    # Apply filters if the form is valid
    if filter_form.is_valid():
        data = filter_form.cleaned_data

        # Search in title and description
        if data.get('search'):
            expenses = expenses.filter(
                Q(title__icontains=data['search']) |
                Q(description__icontains=data['search'])
            )

        # Filter by category
        if data.get('category'):
            expenses = expenses.filter(category=data['category'])

        # Filter by date range
        if data.get('date_from'):
            expenses = expenses.filter(date__gte=data['date_from'])
        if data.get('date_to'):
            expenses = expenses.filter(date__lte=data['date_to'])

        # Filter by month and year
        if data.get('month'):
            expenses = expenses.filter(date__month=data['month'])
        if data.get('year'):
            expenses = expenses.filter(date__year=data['year'])

    # Calculate total for the filtered results
    filtered_total = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Pagination: show 10 expenses per page
    paginator = Paginator(expenses, 10)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)

    context = {
        'expenses': page_obj,
        'filter_form': filter_form,
        'filtered_total': filtered_total,
        'total_count': expenses.count(),
    }

    return render(request, 'expenses/expense_list.html', context)


@login_required
def add_expense(request):

    if request.method == 'POST':
        form = ExpenseForm(request.user, request.POST)
        if form.is_valid():
            expense = form.save(commit=False)  # Don't save to DB yet
            expense.user = request.user         # Set the user first
            expense.save()                      # Now save to DB
            messages.success(request, f'Expense "{expense.title}" added successfully!')
            return redirect('expense_list')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = ExpenseForm(request.user)

    return render(request, 'expenses/expense_form.html', {
        'form': form,
        'title': 'Add Expense',
        'button_text': 'Add Expense'
    })


@login_required
def edit_expense(request, pk):

    expense = get_object_or_404(Expense, pk=pk, user=request.user)

    if request.method == 'POST':
        form = ExpenseForm(request.user, request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, f'Expense "{expense.title}" updated successfully!')
            return redirect('expense_list')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = ExpenseForm(request.user, instance=expense)

    return render(request, 'expenses/expense_form.html', {
        'form': form,
        'title': 'Edit Expense',
        'button_text': 'Save Changes',
        'expense': expense
    })


@login_required
def delete_expense(request, pk):

    expense = get_object_or_404(Expense, pk=pk, user=request.user)

    if request.method == 'POST':
        title = expense.title
        expense.delete()
        messages.success(request, f'Expense "{title}" deleted successfully.')
        return redirect('expense_list')

    return render(request, 'expenses/expense_confirm_delete.html', {'expense': expense})


# ─────────────────────────────────────────────
# Category Views
# ─────────────────────────────────────────────

@login_required
def category_list(request):
    """Show all categories for the user with their expense totals."""
    categories = Category.objects.filter(user=request.user).annotate(
        expense_count=Count('expenses'),
        total_spent=Sum('expenses__amount')
    )
    return render(request, 'expenses/category_list.html', {'categories': categories})


@login_required
def add_category(request):
    """Add a new expense category."""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, f'Category "{category.name}" created!')
            return redirect('category_list')
    else:
        form = CategoryForm()

    return render(request, 'expenses/category_form.html', {
        'form': form,
        'title': 'Add Category'
    })


@login_required
def delete_category(request, pk):
    """Delete a category."""
    category = get_object_or_404(Category, pk=pk, user=request.user)

    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted.')
        return redirect('category_list')

    return render(request, 'expenses/category_confirm_delete.html', {'category': category})


# ─────────────────────────────────────────────
# Export View
# ─────────────────────────────────────────────

@login_required
def export_csv(request):

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses.csv"'

    writer = csv.writer(response)
    
    # Write header row
    writer.writerow(['Date', 'Title', 'Category', 'Amount', 'Description'])

    # Write expense data rows
    expenses = Expense.objects.filter(user=request.user).select_related('category')
    for expense in expenses:
        writer.writerow([
            expense.date,
            expense.title,
            expense.category.name if expense.category else 'Uncategorized',
            expense.amount,
            expense.description or ''
        ])

    return response


# ─────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────

def _create_default_categories(user):
    """
    Creates default expense categories for a new user.
    Called automatically after registration.
    """
    defaults = [
        {'name': 'Shopping', 'icon': 'bi-cart', 'color': '#FFCE56'},
        {'name': 'Health & Fitness', 'icon': 'bi-heart-pulse', 'color': '#9966FF'},
        {'name': 'Tea & Snacks', 'icon': 'bi-cup-hot', 'color': '#FF6384'},
        {'name': 'Petrol', 'icon': 'bi-fuel-pump', 'color': '#FFCE56'},
        {'name': 'College Expense', 'icon': 'bi-book', 'color': '#4BC0C0'},
        {'name': 'Recharge', 'icon': 'bi-wifi', 'color': '#9966FF'},
        {'name': 'Friends Outing', 'icon': 'bi-people', 'color': '#FF9F40'},
        {'name': 'Bills', 'icon': 'bi-lightning', 'color': '#36A2EB'},
        {'name': 'Other', 'icon': 'bi-three-dots', 'color': '#C9CBCF'},
    ]
    
    for cat_data in defaults:
        Category.objects.get_or_create(
            name=cat_data['name'],
            user=user,
            defaults={'icon': cat_data['icon'], 'color': cat_data['color']}
        )
