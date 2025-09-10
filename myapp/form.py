from django import forms
from django.core.exceptions import ValidationError
from .models import Borrower, Loan, Repayment   

class BorrowerForm(forms.ModelForm):
    class Meta:
        model = Borrower
        fields = ['name', 'account_no', 'is_active']

    def clean_account_no(self):
        val = (self.cleaned_data.get("account_no") or "").strip()
        if not val.isdigit() or len(val) != 12:
            raise ValidationError("Account number must be exactly 12 digits.")
        return val

class LoanForm(forms.ModelForm):
    class Meta:
        model  = Loan
        fields = ['borrower', 'amount', 'months']

class RepaymentForm(forms.ModelForm):
    borrower = forms.ModelChoiceField(
        queryset=Borrower.objects.all(),
        required=True,
        label="Borrower"
    )

    class Meta:
        model = Repayment
        fields = ["borrower", "loan", "amount", "paid_on"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["loan"].queryset = Loan.objects.none()

        if "borrower" in self.data:
            try:
                borrower_id = int(self.data.get("borrower"))
                self.fields["loan"].queryset = Loan.objects.filter(borrower_id=borrower_id, status="APPROVED")
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields["loan"].queryset = self.instance.borrower.loans.all()