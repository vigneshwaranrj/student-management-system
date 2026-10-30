from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .views import (
    DashboardView,
    StaffAccountCreateView,
    StaffAccountListView,
    StaffAccountStatusView,
    StudentCreateView,
    StudentDeleteView,
    StudentDetailView,
    StudentExportView,
    StudentListView,
    StudentUpdateView,
)

app_name = "students"

urlpatterns = [
    path("login/", LoginView.as_view(template_name="students/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("", DashboardView.as_view(), name="dashboard"),
    path("students/", StudentListView.as_view(), name="list"),
    path("students/export/", StudentExportView.as_view(), name="export"),
    path("students/add/", StudentCreateView.as_view(), name="create"),
    path("students/<int:pk>/", StudentDetailView.as_view(), name="detail"),
    path("students/<int:pk>/edit/", StudentUpdateView.as_view(), name="update"),
    path("students/<int:pk>/delete/", StudentDeleteView.as_view(), name="delete"),
    path("team/", StaffAccountListView.as_view(), name="staff-list"),
    path("team/add/", StaffAccountCreateView.as_view(), name="staff-create"),
    path(
        "team/<int:pk>/toggle-active/",
        StaffAccountStatusView.as_view(),
        name="staff-toggle-active",
    ),
]
