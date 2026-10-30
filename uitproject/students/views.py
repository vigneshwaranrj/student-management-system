import csv

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import StudentForm
from .models import Student
from .staff_forms import StaffAccountCreationForm


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = "students:login"

    def test_func(self):
        return self.request.user.is_staff


class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = "students:login"

    def test_func(self):
        return self.request.user.is_superuser


def filtered_students(params):
    queryset = Student.objects.all()
    query = params.get("q", "").strip()
    status = params.get("status", "")
    course = params.get("course", "").strip()
    sort = params.get("sort", "name")

    if query:
        queryset = queryset.filter(
            Q(name__icontains=query)
            | Q(email__icontains=query)
            | Q(course__icontains=query)
        )
    if status == "active":
        queryset = queryset.filter(is_active=True)
    elif status == "inactive":
        queryset = queryset.filter(is_active=False)
    if course:
        queryset = queryset.filter(course=course)

    sort_fields = {
        "name": "name",
        "-name": "-name",
        "enrollment_date": "enrollment_date",
        "-enrollment_date": "-enrollment_date",
        "course": "course",
    }
    return queryset.order_by(sort_fields.get(sort, "name"), "pk")


class DashboardView(StaffRequiredMixin, ListView):
    model = Student
    template_name = "students/dashboard.html"
    context_object_name = "recent_students"

    def get_queryset(self):
        return Student.objects.order_by("-created_at", "-pk")[:5]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_students"] = Student.objects.count()
        context["active_students"] = Student.objects.filter(is_active=True).count()
        context["inactive_students"] = Student.objects.filter(is_active=False).count()
        context["course_stats"] = list(
            Student.objects.values("course")
            .annotate(total=Count("pk"))
            .order_by("-total", "course")[:5]
        )
        return context


class StudentListView(StaffRequiredMixin, ListView):
    model = Student
    template_name = "students/student_list.html"
    context_object_name = "students"
    paginate_by = 10

    def get_queryset(self):
        return filtered_students(self.request.GET)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "").strip()
        context["status_filter"] = self.request.GET.get("status", "")
        context["course_filter"] = self.request.GET.get("course", "")
        context["sort_order"] = self.request.GET.get("sort", "name")
        context["courses"] = (
            Student.objects.order_by("course")
            .values_list("course", flat=True)
            .distinct()
        )
        context["filtered_count"] = self.object_list.count()
        context["query_string"] = self.request.GET.copy()
        context["query_string"].pop("page", None)
        context["query_string"] = context["query_string"].urlencode()
        return context


class StudentExportView(StaffRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="students.csv"'
        response.write("\ufeff")
        writer = csv.writer(response)
        writer.writerow(
            ["Name", "Email", "Phone", "Course", "Status", "Enrollment date"]
        )
        for student in filtered_students(request.GET):
            writer.writerow(
                [
                    student.name,
                    student.email,
                    student.phone,
                    student.course,
                    "Active" if student.is_active else "Inactive",
                    student.enrollment_date.isoformat(),
                ]
            )
        return response


class StudentDetailView(StaffRequiredMixin, DetailView):
    model = Student
    template_name = "students/student_detail.html"
    context_object_name = "student"


class StudentCreateView(StaffRequiredMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = "students/student_form.html"
    success_url = reverse_lazy("students:list")

    def form_valid(self, form):
        messages.success(self.request, "Student added successfully.")
        return super().form_valid(form)


class StudentUpdateView(StaffRequiredMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = "students/student_form.html"
    success_url = reverse_lazy("students:list")

    def form_valid(self, form):
        messages.success(self.request, "Student details updated.")
        return super().form_valid(form)


class StudentDeleteView(StaffRequiredMixin, DeleteView):
    model = Student
    template_name = "students/student_confirm_delete.html"
    context_object_name = "student"
    success_url = reverse_lazy("students:list")

    def form_valid(self, form):
        messages.success(self.request, "Student deleted.")
        return super().form_valid(form)


class StaffAccountListView(SuperuserRequiredMixin, ListView):
    template_name = "students/staff_list.html"
    context_object_name = "staff_accounts"

    def get_queryset(self):
        return get_user_model().objects.filter(is_staff=True).order_by(
            "-is_superuser", "username"
        )


class StaffAccountCreateView(SuperuserRequiredMixin, CreateView):
    form_class = StaffAccountCreationForm
    template_name = "students/staff_form.html"
    success_url = reverse_lazy("students:staff-list")

    def form_valid(self, form):
        messages.success(
            self.request,
            f"Staff account for {form.cleaned_data['username']} created.",
        )
        return super().form_valid(form)


class StaffAccountStatusView(SuperuserRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        account = get_object_or_404(
            get_user_model(),
            pk=pk,
            is_staff=True,
            is_superuser=False,
        )
        account.is_active = not account.is_active
        account.save(update_fields=["is_active"])
        status = "activated" if account.is_active else "deactivated"
        messages.success(request, f"{account.username} was {status}.")
        return redirect("students:staff-list")
