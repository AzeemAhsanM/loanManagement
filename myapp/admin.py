from django.contrib import admin
from .models import Borrower, Loan, Repayment, RepaymentSchedule

@admin.register(Borrower)
class BorrowerAdmin(admin.ModelAdmin):
    list_display = ("name", "account_no", "is_active", "current_balance")
    list_filter = ("is_active",)

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ("loan_id", "borrower", "amount", "months", "status", "created_at")
    list_filter = ("status",)

admin.site.register(Repayment)
admin.site.register(RepaymentSchedule)
