from django.db import models

class ExpenseCategory(models.Model):
    category_name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Expense Categories"
        ordering = ['category_name']

    def __str__(self):
        return self.category_name
