# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from select import select
from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    """Category Model"""
    id = models.AutoField(primary_key=True)
    name: models.CharField = models.CharField(max_length=200, null=False)

    def __str__(self) -> str:
        """String Representation of the User Expense Model"""
        return f'Category: {self.name}'


class Groups(models.Model):
    """Groups Model"""
    id = models.AutoField(primary_key=True)
    name: models.CharField = models.CharField(max_length=100, null=False)
    members: models.ManyToManyField = models.ManyToManyField(
        User, related_name='members', blank=True)

    def __str__(self) -> str:
        return f'Group: {self.name}'


class Expenses(models.Model):
    """Expenses Model"""
    id = models.AutoField(primary_key=True)
    description: models.CharField = models.CharField(max_length=200)
    total_amount: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2)
    group: models.ForeignKey = models.ForeignKey(
        Groups, null=True, on_delete=models.CASCADE)
    category: models.ForeignKey = models.ForeignKey(
        Category, default=1, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f'Description: {self.description}, \
        Total Amount: {self.total_amount}, Group: {self.group}, Category: {self.category}'


class UserExpense(models.Model):
    """User Expense Model"""
    id = models.AutoField(primary_key=True)
    expense: models.ForeignKey = models.ForeignKey(
        Expenses, default=1, on_delete=models.CASCADE, related_name="users")
    user: models.ForeignKey = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="expenses")
    amount_owed: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2)
    amount_lent: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        """String Representation of the User Expense Model"""
        return f"user: {self.user}, amount_owed: {self.amount_owed} amount_lent: {self.amount_lent}"
