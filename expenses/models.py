"""
Models define the database structure.
Each model class = one database table.
Each attribute = one column in the table.

Django ORM (Object Relational Mapper) lets you work with the database
using Python code instead of writing raw SQL queries.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    # Predefined icon choices for categories (Bootstrap Icons)
    ICON_CHOICES = [
        ('bi-cart', 'Shopping Cart'),
        ('bi-airplane', 'Travel'),
        ('bi-house', 'Home'),
        ('bi-lightning', 'Bills'),
        ('bi-cup-straw', 'Food & Drink'),
        ('bi-heart-pulse', 'Health'),
        ('bi-controller', 'Entertainment'),
        ('bi-book', 'Education'),
        ('bi-three-dots', 'Other'),
    ]
    
    COLOR_CHOICES = [
        ('#FF6384', 'Red'),
        ('#36A2EB', 'Blue'),
        ('#FFCE56', 'Yellow'),
        ('#4BC0C0', 'Teal'),
        ('#9966FF', 'Purple'),
        ('#FF9F40', 'Orange'),
        ('#FF6384', 'Pink'),
        ('#C9CBCF', 'Grey'),
    ]

    name = models.CharField(max_length=100)                  # Category name
    icon = models.CharField(max_length=50, choices=ICON_CHOICES, default='bi-three-dots')
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='#36A2EB')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,    # Delete categories when user is deleted
        related_name='categories'
    )
    created_at = models.DateTimeField(auto_now_add=True)     

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
        unique_together = ['name', 'user']   # Each user can't have duplicate category names

    def __str__(self):
        return self.name



class Expense(models.Model):
    
    title = models.CharField(max_length=200)                  
    amount = models.DecimalField(max_digits=10, decimal_places=2)  
    description = models.TextField(blank=True, null=True)     
    date = models.DateField(default=timezone.now)             
    
    # ForeignKey = Many-to-One relationship
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,   
        null=True,
        related_name='expenses'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,    # Delete expenses when user is deleted
        related_name='expenses'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)     
    updated_at = models.DateTimeField(auto_now=True)          

    class Meta:
        ordering = ['-date', '-created_at']   

    def __str__(self):
        return f"{self.title} - ${self.amount}"
