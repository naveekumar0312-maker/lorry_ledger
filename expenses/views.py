from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ExpenseCategory
from trips.models import TripExpenseEntry

@login_required
def category_list(request):
    if request.method == 'POST':
        category_name = request.POST.get('category_name', '').strip()
        if category_name:
            category, created = ExpenseCategory.objects.get_or_create(category_name=category_name, user=request.user)
            if created:
                messages.success(request, f"Category '{category_name}' created.")
            else:
                messages.warning(request, f"Category '{category_name}' already exists.")
        return redirect('expenses:category_list')
        
    categories = ExpenseCategory.objects.filter(user=request.user)
    return render(request, 'expenses/categories.html', {'categories': categories})

@login_required
def category_toggle(request, pk):
    category = get_object_or_404(ExpenseCategory, pk=pk, user=request.user)
    category.is_active = not category.is_active
    category.save()
    status_str = "activated" if category.is_active else "disabled"
    messages.info(request, f"Category '{category.category_name}' {status_str}.")
    return redirect('expenses:category_list')

@login_required
def category_edit(request, pk):
    category = get_object_or_404(ExpenseCategory, pk=pk, user=request.user)
    if request.method == 'POST':
        new_name = request.POST.get('category_name', '').strip()
        if new_name and new_name != category.category_name:
            if ExpenseCategory.objects.filter(category_name=new_name, user=request.user).exists():
                messages.error(request, f"Category '{new_name}' already exists.")
                return redirect('expenses:category_list')
            category.category_name = new_name
        category.save()
        messages.success(request, f"Category updated to '{category.category_name}'.")
    return redirect('expenses:category_list')

@login_required
def category_delete(request, pk):
    category = get_object_or_404(ExpenseCategory, pk=pk, user=request.user)
    if request.method == 'POST':
        # Check if any expense entries use this category
        usage_count = TripExpenseEntry.objects.filter(category=category).count()
        if usage_count > 0:
            # Archive instead of delete
            category.is_active = False
            category.save()
            messages.warning(
                request,
                f"Category '{category.category_name}' is used in {usage_count} expense record(s). "
                f"It has been disabled/archived instead of deleted to preserve accounting history."
            )
        else:
            name = category.category_name
            category.delete()
            messages.success(request, f"Category '{name}' deleted successfully.")
    return redirect('expenses:category_list')
