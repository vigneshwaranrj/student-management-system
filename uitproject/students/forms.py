from django import forms

from .models import Student


class StudentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and not self.is_bound:
            self.fields["is_active"].initial = True

    class Meta:
        model = Student
        fields = [
            "name",
            "email",
            "phone",
            "course",
            "enrollment_date",
            "is_active",
        ]
        labels = {"is_active": "Active student"}
        help_texts = {
            "is_active": "Inactive students remain in the directory but are marked separately."
        }
        widgets = {
            "enrollment_date": forms.DateInput(attrs={"type": "date"}),
        }
