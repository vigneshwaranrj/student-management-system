from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "course", "is_active", "enrollment_date")
    list_filter = ("is_active", "course", "enrollment_date")
    search_fields = ("name", "email", "course")
    list_editable = ("is_active",)
