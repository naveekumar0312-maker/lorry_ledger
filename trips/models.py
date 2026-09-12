from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models


class Trip(models.Model):
    # =====================================================
    # BASIC TRIP INFORMATION
    # =====================================================

    trip_ref_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True
    )

    entry_date = models.DateField(db_index=True)
    period_from = models.DateField(db_index=True)
    period_to = models.DateField(db_index=True)

    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.PROTECT,
        related_name='trips'
    )

    primary_driver = models.ForeignKey(
        'drivers.Driver',
        on_delete=models.PROTECT,
        related_name='primary_trips'
    )

    secondary_driver = models.ForeignKey(
        'drivers.Driver',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='secondary_trips'
    )

    notes = models.TextField(
        blank=True,
        null=True
    )

    # =====================================================
    # MANUAL ACCOUNTING EXPENSES
    # =====================================================

    cleaner_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    workshop_expense = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    toll_gate_expense = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    # =====================================================
    # ARCHIVE / AUDIT
    # =====================================================

    is_archived = models.BooleanField(
        default=False,
        db_index=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_trips'
    )

    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_trips'
    )

    class Meta:
        ordering = ['-entry_date', '-id']

    def __str__(self):
        return (
            f"Trip #{self.trip_ref_no} "
            f"({self.vehicle.vehicle_number})"
        )

    # =====================================================
    # OVERALL INCOME
    # =====================================================

    @property
    def total_income(self):
        """
        Overall Income is calculated from
        active TripLoadRevenueEntry records.
        """

        entries = self.load_revenue_entries.filter(
            is_archived=False
        )

        return sum(
            (
                entry.income_amount or Decimal('0.00')
                for entry in entries
            ),
            Decimal('0.00')
        )

    # =====================================================
    # LEGACY INCOME COMPATIBILITY
    # =====================================================

    @property
    def total_freight(self):
        incomes = self.income_entries.all()

        return sum(
            (
                income.freight_amount or Decimal('0.00')
                for income in incomes
            ),
            Decimal('0.00')
        )

    @property
    def total_advance(self):
        incomes = self.income_entries.all()

        return sum(
            (
                income.advance_amount or Decimal('0.00')
                for income in incomes
            ),
            Decimal('0.00')
        )

    @property
    def total_balance(self):
        incomes = self.income_entries.all()

        return sum(
            (
                income.balance_amount or Decimal('0.00')
                for income in incomes
            ),
            Decimal('0.00')
        )

    # =====================================================
    # FUEL
    # =====================================================

    @property
    def total_fuel_quantity(self):
        """
        Total quantity of Diesel + AdBlue.
        """

        fuels = self.fuel_entries.all()

        return sum(
            (
                fuel.quantity or Decimal('0.000')
                for fuel in fuels
            ),
            Decimal('0.000')
        )

    @property
    def total_diesel_quantity(self):
        """
        Diesel quantity only.
        Used for mileage calculation.
        """

        fuels = self.fuel_entries.filter(
            fuel_type='Diesel'
        )

        return sum(
            (
                fuel.quantity or Decimal('0.000')
                for fuel in fuels
            ),
            Decimal('0.000')
        )

    @property
    def total_adblue_quantity(self):
        """
        AdBlue quantity only.
        """

        fuels = self.fuel_entries.filter(
            fuel_type='AdBlue'
        )

        return sum(
            (
                fuel.quantity or Decimal('0.000')
                for fuel in fuels
            ),
            Decimal('0.000')
        )

    @property
    def total_diesel_cost(self):
        """
        Diesel cost only.
        """

        fuels = self.fuel_entries.filter(
            fuel_type='Diesel'
        )

        return sum(
            (
                fuel.total_cost or Decimal('0.00')
                for fuel in fuels
            ),
            Decimal('0.00')
        )

    @property
    def total_adblue_cost(self):
        """
        AdBlue cost only.
        """

        fuels = self.fuel_entries.filter(
            fuel_type='AdBlue'
        )

        return sum(
            (
                fuel.total_cost or Decimal('0.00')
                for fuel in fuels
            ),
            Decimal('0.00')
        )

    @property
    def total_fuel_cost(self):
        """
        Diesel + AdBlue total fuel cost.
        """

        return (
            self.total_diesel_cost
            + self.total_adblue_cost
        )

    # =====================================================
    # COMMISSION
    # =====================================================

    @property
    def total_commission(self):
        """
        Commission is tracked separately.

        IMPORTANT:
        Commission is NOT included in Overall Expense.
        """

        if hasattr(self, 'commission') and self.commission:
            return self.commission.amount or Decimal('0.00')

        return Decimal('0.00')

    # =====================================================
    # LOADING / UNLOADING
    # =====================================================

    @property
    def total_loading_charges(self):
        entries = self.load_revenue_entries.filter(
            is_archived=False
        )

        return sum(
            (
                entry.loading_charges or Decimal('0.00')
                for entry in entries
            ),
            Decimal('0.00')
        )

    @property
    def total_unloading_charges(self):
        entries = self.load_revenue_entries.filter(
            is_archived=False
        )

        return sum(
            (
                entry.unloading_charges or Decimal('0.00')
                for entry in entries
            ),
            Decimal('0.00')
        )

    # =====================================================
    # SECTION 4 - OTHER EXPENSES
    # =====================================================

    @property
    def total_other_expenses(self):
        """
        Total Section 4 Other Expenses.

        IMPORTANT:
        This IS included in Overall Expense.
        """

        expenses = self.expense_entries.all()

        return sum(
            (
                expense.amount or Decimal('0.00')
                for expense in expenses
            ),
            Decimal('0.00')
        )

    # =====================================================
    # DRIVER SALARY
    # =====================================================

    @property
    def driver_salary(self):
        """
        Driver Salary = 13% of Overall Income.
        """

        return (
            self.total_income
            * Decimal('13.00')
            / Decimal('100.00')
        ).quantize(
            Decimal('0.01')
        )

    # =====================================================
    # RTO
    # =====================================================

    @property
    def total_rto_expense(self):
        entries = self.rto_pc_entries.filter(
            expense_type='RTO'
        )

        return sum(
            (
                entry.total_amount or Decimal('0.00')
                for entry in entries
            ),
            Decimal('0.00')
        )

    # =====================================================
    # PC
    # =====================================================

    @property
    def total_pc_expense(self):
        entries = self.rto_pc_entries.filter(
            expense_type='PC'
        )

        return sum(
            (
                entry.total_amount or Decimal('0.00')
                for entry in entries
            ),
            Decimal('0.00')
        )

    # =====================================================
    # RTO + PC
    # =====================================================

    @property
    def total_rto_pc_expense(self):
        return (
            self.total_rto_expense
            + self.total_pc_expense
        )

    # =====================================================
    # OTHER TOLL EXPENSES
    # =====================================================

    @property
    def total_other_toll_expense(self):
        """
        Total of all dynamic Other Toll Expense rows.
        """

        entries = self.other_toll_expenses.all()

        return sum(
            (
                entry.amount or Decimal('0.00')
                for entry in entries
            ),
            Decimal('0.00')
        )

    # =====================================================
    # FINAL OVERALL EXPENSE
    # =====================================================

    @property
    def overall_expense(self):
        """
        FINAL AUTHORITATIVE EXPENSE FORMULA.

        Included:
        - Diesel
        - AdBlue
        - Loading
        - Unloading
        - Driver Salary (13%)
        - Cleaner Salary
        - Workshop Expense
        - RTO
        - PC
        - Toll Gate Expense
        - Other Toll Expenses
        - Section 4 Other Expenses
        - Commission
        """

        return (
            self.total_diesel_cost
            + self.total_adblue_cost
            + self.total_loading_charges
            + self.total_unloading_charges
            + self.driver_salary
            + (self.cleaner_salary or Decimal('0.00'))
            + (self.workshop_expense or Decimal('0.00'))
            + self.total_rto_expense
            + self.total_pc_expense
            + (self.toll_gate_expense or Decimal('0.00'))
            + self.total_other_toll_expense
            + self.total_other_expenses
            + self.total_revenue_commission
        )

    # =====================================================
    # FINAL BALANCE
    # =====================================================

    @property
    def balance(self):
        return (
            self.total_income
            - self.overall_expense
        )

    # =====================================================
    # BACKWARD COMPATIBILITY
    # =====================================================

    @property
    def total_expenses(self):
        """
        Backward-compatible alias.

        Use overall_expense for new code.
        """

        return self.overall_expense

    @property
    def net_income(self):
        return self.balance

    # =====================================================
    # KM
    # =====================================================

    @property
    def total_km(self):
        """
        Total distance travelled.

        Total KM = Ending KM - Starting KM.

        TripKMDetail.save() performs the actual calculation.
        """

        if hasattr(self, 'km_detail') and self.km_detail:
            return (
                self.km_detail.total_km
                or Decimal('0.00')
            )

        return Decimal('0.00')

    @property
    def mileage(self):
        """
        Mileage = Total KM / Diesel Quantity.

        AdBlue is NOT included.
        """

        km = self.total_km
        diesel_qty = self.total_diesel_quantity

        if diesel_qty > Decimal('0.000'):
            return round(
                km / diesel_qty,
                2
            )

        return Decimal('0.00')

    @property
    def fuel_cost_per_km(self):
        km = self.total_km
        fuel_cost = self.total_fuel_cost

        if km > Decimal('0.00'):
            return round(
                fuel_cost / km,
                2
            )

        return Decimal('0.00')

    # =====================================================
    # LOAD / REVENUE SUMMARY
    # =====================================================

    @property
    def total_revenue_ton(self):
        entries = self.load_revenue_entries.filter(
            is_archived=False
        )

        return sum(
            (
                entry.ton or Decimal('0.00')
                for entry in entries
            ),
            Decimal('0.00')
        )

    @property
    def total_revenue_income(self):
        entries = self.load_revenue_entries.filter(
            is_archived=False
        )

        return sum(
            (
                entry.income_amount or Decimal('0.00')
                for entry in entries
            ),
            Decimal('0.00')
        )

    @property
    def total_revenue_commission(self):
        entries = self.load_revenue_entries.filter(
            is_archived=False
        )

        load_commission = sum(
            (
                entry.commission_amount or Decimal('0.00')
                for entry in entries
            ),
            Decimal('0.00')
        )

        if load_commission > Decimal('0.00'):
            return load_commission

        # Fallback to legacy TripCommission for older trips to prevent commission missing from Overall Expense
        if hasattr(self, 'commission') and self.commission:
            return self.commission.amount or Decimal('0.00')

        return Decimal('0.00')

    @property
    def total_revenue_loading(self):
        return self.total_loading_charges

    @property
    def total_revenue_unloading(self):
        return self.total_unloading_charges


# =========================================================
# KM DETAIL
# =========================================================

class TripKMDetail(models.Model):
    trip = models.OneToOneField(
        Trip,
        on_delete=models.CASCADE,
        related_name='km_detail'
    )

    start_km = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    end_km = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    # Kept in DB for backward compatibility.
    # Current UI does not use this field.
    km_adjustment = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00')
    )

    total_km = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    # Kept in DB for backward compatibility.
    # Current UI does not use this field.
    km_notes = models.TextField(
        blank=True,
        null=True
    )

    def save(self, *args, **kwargs):
        calculated = (
            self.end_km
            - self.start_km
            + self.km_adjustment
        )

        self.total_km = (
            calculated
            if calculated >= Decimal('0.00')
            else Decimal('0.00')
        )

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"KM Detail for Trip #{self.trip.trip_ref_no}: "
            f"{self.start_km} -> {self.end_km} "
            f"({self.total_km} KM)"
        )


# =========================================================
# FUEL ENTRY
# =========================================================

class TripFuelEntry(models.Model):
    FUEL_TYPES = (
        ('Diesel', 'Diesel'),
        ('AdBlue', 'AdBlue'),
    )

    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name='fuel_entries'
    )

    fuel_type = models.CharField(
        max_length=30,
        choices=FUEL_TYPES,
        default='Diesel'
    )

    quantity = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        help_text='Quantity in liters'
    )

    rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text='Rate per liter in ₹'
    )

    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    station_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    fuel_date = models.DateField()

    # Kept for existing data compatibility.
    # Current UI does not show Receipt.
    receipt_number = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    notes = models.TextField(
        blank=True,
        null=True
    )

    def save(self, *args, **kwargs):
        self.total_cost = round(
            self.quantity * self.rate,
            2
        )

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.fuel_type} "
            f"{self.quantity}L @ ₹{self.rate} "
            f"= ₹{self.total_cost}"
        )


# =========================================================
# LEGACY INCOME ENTRY
# =========================================================

class TripIncomeEntry(models.Model):
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name='income_entries'
    )

    income_type = models.CharField(
        max_length=50,
        default='Freight'
    )

    custom_income_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    freight_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    advance_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    balance_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    other_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    total_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        null=True
    )

    def save(self, *args, **kwargs):
        self.balance_amount = (
            self.freight_amount
            - self.advance_amount
        )

        self.total_income = (
            self.freight_amount
            + self.other_income
        )

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"Income Trip #{self.trip.trip_ref_no}: "
            f"Freight ₹{self.freight_amount}, "
            f"Total ₹{self.total_income}"
        )


# =========================================================
# LEGACY COMMISSION
# =========================================================

class TripCommission(models.Model):
    COMMISSION_TYPES = (
        ('FIXED', 'Fixed Amount'),
        ('PERCENTAGE', 'Percentage of Freight'),
    )

    trip = models.OneToOneField(
        Trip,
        on_delete=models.CASCADE,
        related_name='commission'
    )

    commission_type = models.CharField(
        max_length=20,
        choices=COMMISSION_TYPES,
        default='FIXED'
    )

    rate_or_percentage = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00')
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    commission_date = models.DateField(
        blank=True,
        null=True
    )

    notes = models.TextField(
        blank=True,
        null=True
    )

    def save(self, *args, **kwargs):
        if self.commission_type == 'PERCENTAGE':
            freight = self.trip.total_freight

            self.amount = round(
                freight
                * (
                    self.rate_or_percentage
                    / Decimal('100.00')
                ),
                2
            )
        else:
            self.amount = self.rate_or_percentage

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"Commission for Trip "
            f"#{self.trip.trip_ref_no}: "
            f"₹{self.amount}"
        )


# =========================================================
# LEGACY LOADING ENTRY
# =========================================================

class TripLoadingEntry(models.Model):
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name='loading_entries'
    )

    loading_date = models.DateField()

    location = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    weight_tons = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    notes = models.TextField(
        blank=True,
        null=True
    )

    def __str__(self):
        return (
            f"Loading Charge ₹{self.amount} "
            f"({self.location})"
        )


# =========================================================
# LEGACY UNLOADING ENTRY
# =========================================================

class TripUnloadingEntry(models.Model):
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name='unloading_entries'
    )

    unloading_date = models.DateField()

    location = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    weight_tons = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True
    )

    shortage_penalty = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    notes = models.TextField(
        blank=True,
        null=True
    )

    def __str__(self):
        return (
            f"Unloading Charge ₹{self.amount} "
            f"({self.location})"
        )


# =========================================================
# SECTION 4 - OTHER EXPENSE ENTRY
# =========================================================

class TripExpenseEntry(models.Model):
    PAYMENT_METHODS = (
        ('CASH', 'Cash'),
        ('FASTAG', 'FASTag'),
        ('UPI', 'UPI / GPay / PhonePe'),
        ('CARD', 'Fuel Card / Debit Card'),
        ('BANK', 'Bank Transfer'),
    )

    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name='expense_entries'
    )

    category = models.ForeignKey(
        'expenses.ExpenseCategory',
        on_delete=models.SET_NULL,
        related_name='trip_expenses',
        blank=True,
        null=True
    )

    expense_name = models.CharField(
        max_length=150
    )

    expense_date = models.DateField(
        blank=True,
        null=True
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHODS,
        default='CASH',
        blank=True,
        null=True
    )

    receipt_number = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    def __str__(self):
        category_name = (
            self.category.category_name
            if self.category
            else 'Uncategorized'
        )

        return (
            f"{category_name} - "
            f"{self.expense_name}: "
            f"₹{self.amount}"
        )


# =========================================================
# SECTION 2 - LOAD & REVENUE
# =========================================================

class TripLoadRevenueEntry(models.Model):
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name='load_revenue_entries'
    )

    date = models.DateField()

    from_location = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    to_location = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    load_place = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    ton = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    income_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    commission_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    loading_charges = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    unloading_charges = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_load_entries'
    )

    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_load_entries'
    )

    is_archived = models.BooleanField(
        default=False,
        db_index=True
    )

    def __str__(self):
        return (
            f"Load Revenue Entry for Trip "
            f"#{self.trip.trip_ref_no}: "
            f"₹{self.income_amount}"
        )


# =========================================================
# SECTION 5 - RTO / PC
# =========================================================

class TripRtoPcEntry(models.Model):
    EXPENSE_TYPES = (
        ('RTO', 'RTO'),
        ('PC', 'PC'),
    )

    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name='rto_pc_entries'
    )

    place = models.CharField(
        max_length=150
    )

    expense_type = models.CharField(
        max_length=10,
        choices=EXPENSE_TYPES,
        default='RTO'
    )

    onward_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    return_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    @property
    def total_amount(self):
        return (
            (self.onward_amount or Decimal('0.00'))
            + (self.return_amount or Decimal('0.00'))
        )

    def __str__(self):
        return (
            f"{self.expense_type} - "
            f"{self.place} - "
            f"₹{self.total_amount}"
        )


# =========================================================
# SECTION 6 - OTHER TOLL EXPENSE
# =========================================================

class TripOtherTollExpense(models.Model):
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name='other_toll_expenses'
    )

    toll_name = models.CharField(
        max_length=150
    )

    toll_date = models.DateField(
        blank=True,
        null=True
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    notes = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return (
            f"{self.toll_name} - "
            f"₹{self.amount}"
        )