from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.utils import timezone

# Create your models here.

class Borrower(models.Model):
    name = models.CharField(max_length=100)
    account_no = models.CharField(max_length=12,unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True) 

    # simple running balance for approved loans – repayments reduce this
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.name} ({self.account_no})"

# to generate Loan Id
def next_loan_id():
    last = Loan.objects.order_by("-created_at").first()
    if not last or not last.loan_id:
        n = 1
    else:
        n = int(last.loan_id.replace("LN", "")) + 1
    return f"LN{n:05d}"

#receipt gener
def next_receipt_no():
    #timestamp based unique receipt number
    return f"LR-{timezone.now().strftime('%y%m%d%H%M%S%f')[:12]}"    

class Loan(models.Model):
    Loan_Status = [
        ('PENDING', 'Pending'), 
        ('APPROVED', 'Approved'), 
        ('REJECTED', 'Rejected'),
        ('REPAID', 'Repaid')
        ]
    loan_id = models.CharField(max_length=10, unique=True, editable=False, default=next_loan_id)
    borrower = models.ForeignKey(Borrower, on_delete=models.PROTECT, related_name='loans')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    months = models.PositiveIntegerField(default=12)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=Loan_Status, default='PENDING')

    def save(self, *args, **kwargs):
        if not self.loan_id:
            self.loan_id = next_loan_id()
        super().save(*args, **kwargs)

    @property
    def total_paid(self):
        agg = self.repayments.aggregate(total = models.Sum('amount')) 
        return agg['total'] or Decimal('0.00')

    @property
    def balance(self):
        return (self.amount - self.total_paid).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def __str__(self):
        return f"{self.loan_id} - {self.borrower.name}"

class RepaymentSchedule(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="schedule")
    due_date = models.DateField()
    due_amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.loan.loan_id} - {self.due_date} ({self.due_amount})"

# Repayments model
class Repayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.PROTECT, related_name='repayments')
    receipt_no = models.CharField(max_length=15, unique=True, editable=False, default=next_receipt_no)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_on = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.receipt_no:
            self.receipt_no = next_receipt_no()
        super().save(*args, **kwargs)
    
        self._apply_to_schedule()
        self.loan.borrower.current_balance = self.loan.balance
        self.loan.borrower.save(update_fields=["current_balance"])
        # close loan if fully paid
        if self.loan.balance <= Decimal("0.00") and self.loan.status == "APPROVED":
            self.loan.status = 'REPAID'
            self.loan.save(update_fields=["status"])

    def _apply_to_schedule(self):
        """Greedy fill upcoming unpaid schedule rows."""
        remain = self.amount
        for row in self.loan.schedule.filter(is_paid=False).order_by("due_date"):
            if remain <= 0:
                break
            needed = (row.due_amount - row.paid_amount).quantize(Decimal("0.01"))
            take = needed if remain >= needed else remain
            row.paid_amount = (row.paid_amount + take).quantize(Decimal("0.01"))
            row.is_paid = row.paid_amount >= row.due_amount
            row.save(update_fields=["paid_amount", "is_paid"])
            remain = (remain - take).quantize(Decimal("0.01"))

    def __str__(self):
        return f"{self.receipt_no} - {self.loan.loan_id}"
