from datetime import date
from dateutil.relativedelta import relativedelta 
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.http import JsonResponse
from django.db.models import Count, Q
from decimal import Decimal, ROUND_HALF_UP


from .models import Borrower, Loan, Repayment, RepaymentSchedule
from .form import BorrowerForm, LoanForm, RepaymentForm

# Borrower Views

def borrower_list(request):
    q = Borrower.objects.all().order_by('name')
    return render(request, 'myapp/borrower_list.html', {'borrowers': q})

def borrower_create(request):
    form = BorrowerForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('borrower_list')
    return render(request, 'myapp/form.html', {'form': form, 'title': 'Create Borrower'})

def borrower_edit(request, pk):
    obj = get_object_or_404(Borrower, pk=pk)
    form = BorrowerForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        return redirect('borrower_list')
    return render(request, 'myapp/form.html', {'form': form, 'title': 'Edit Borrower'})

# Loan Views

def loan_create(request):
    form = LoanForm(request.POST or None)
    if form.is_valid():
        loan = form.save(commit=False)
        loan.status = 'PENDING'
        loan.save()
        messages.success(request, f"Loan {loan.loan_id} created (Pending).")
        return redirect('borrower_list')    
    return render(request, 'myapp/loan_form.html', {'form': form, 'title': 'Create Loan'})

def loan_details(request, loan_id):
    loan = get_object_or_404(Loan, loan_id=loan_id)
    repayments = loan.repayments.all().order_by('-paid_on')
    return render(request, 'myapp/loan_details.html', {
        'loan': loan,
        'schedule': loan.schedule.order_by('due_date'),  
        'repayments': repayments
    })

def load_loans(request):
    borrower_id = request.GET.get("borrower_id")
    loans = Loan.objects.filter(borrower_id=borrower_id).values("id", "loan_id", "status")
    return JsonResponse(list(loans), safe=False)


def loan_lookup(request):
    borrowers = Borrower.objects.all().order_by('name')
    return render(request, 'myapp/loan_lookup.html', {'borrowers': borrowers})


@transaction.atomic
def loan_approve(request, loan_id):
    loan = get_object_or_404(Loan, loan_id=loan_id)
    if loan.status != "PENDING":  
        messages.warning(request, "Loan already processed.")
        return redirect("loan_details", loan_id=loan.loan_id)

    loan.status = "APPROVED"  
    loan.save(update_fields=["status"])

    # Generate equal no-interest EMIs
    per = (loan.amount / loan.months).quantize(Decimal("0.01"))
    total = Decimal("0.00")
    for i in range(loan.months):
        due_date = (date.today() + relativedelta(months=+i+1))
        amount = per if i < loan.months - 1 else (loan.amount - total).quantize(Decimal("0.01"))
        total += amount
        RepaymentSchedule.objects.create(loan=loan, due_date=due_date, due_amount=amount)

    b = loan.borrower
    b.current_balance += loan.amount
    b.save(update_fields=["current_balance"])

    messages.success(request, f"Loan {loan.loan_id} approved and schedule generated.")
    return redirect("loan_details", loan_id=loan.loan_id)  

def loan_reject(request, loan_id):
    loan = get_object_or_404(Loan, loan_id=loan_id)
    loan.status = "REJECTED"
    loan.save(update_fields=["status"])
    messages.info(request, "Loan rejected.")
    return redirect("loan_details", loan_id=loan.loan_id)  

def repayment_create(request):
    form = RepaymentForm(request.POST or None)
    if form.is_valid():
        rep = form.save()
        messages.success(request, f"Repayment recorded, receipt {rep.receipt_no}.")
        return redirect("loan_details", loan_id=rep.loan.loan_id) 
    return render(request, "myapp/repayment_form.html", {"form": form, "title": "Record Repayment"})
