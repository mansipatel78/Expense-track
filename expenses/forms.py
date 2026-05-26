"""
Forms handle data input validation in Django.

Django Forms:
- Define what fields to show
- Validate user input automatically
- Can be linked to models (ModelForm) to save data directly

ModelForm automatically creates form fields from a model's fields.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Expense, Category


class UserRegisterForm(UserCreationForm):

    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to every field
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'amount', 'category', 'date', 'description']
        widgets = {
            # Use a date picker for the date field
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Grocery shopping'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional description...'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, user, *args, **kwargs):

        super().__init__(*args, **kwargs)
        # Filter categories to only show the current user's categories
        self.fields['category'].queryset = Category.objects.filter(user=user)
        self.fields['category'].empty_label = "-- Select Category --"


class CategoryForm(forms.ModelForm):
    
    class Meta:
        model = Category
        fields = ['name', 'icon', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category name'}),
            'icon': forms.Select(attrs={'class': 'form-select'}),
            'color': forms.Select(attrs={'class': 'form-select'}),
        }


class ExpenseFilterForm(forms.Form):
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search expenses...'})
    )
    category = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    month = forms.IntegerField(
        required=False,
        widget=forms.Select(
            choices=[('', 'All Months')] + [(i, __import__('calendar').month_name[i]) for i in range(1, 13)],
            attrs={'class': 'form-select'}
        )
    )
    year = forms.IntegerField(
        required=False,
        widget=forms.Select(
            choices=[('', 'All Years')] + [(y, y) for y in range(2020, 2030)],
            attrs={'class': 'form-select'}
        )
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user)
