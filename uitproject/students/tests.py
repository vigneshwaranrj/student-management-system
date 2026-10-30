from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import StudentForm
from .models import Student


class StudentPagesTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username="staff",
            password="test-password-123",
            is_staff=True,
        )
        self.client.force_login(self.staff)
        self.student = Student.objects.create(
            name="Alex Morgan",
            email="alex@example.com",
            course="Computer Science",
        )

    def test_student_list_displays_records(self):
        response = self.client.get(reverse("students:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alex Morgan")

    def test_search_filters_by_course(self):
        response = self.client.get(reverse("students:list"), {"q": "Computer"})

        self.assertContains(response, "Alex Morgan")
        self.assertEqual(len(response.context["students"]), 1)

    def test_create_student(self):
        response = self.client.post(
            reverse("students:create"),
            {
                "name": "Taylor Lee",
                "email": "taylor@example.com",
                "phone": "",
                "course": "Mathematics",
                "enrollment_date": "2026-01-15",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("students:list"))
        self.assertTrue(Student.objects.filter(email="taylor@example.com").exists())

    def test_new_student_form_defaults_to_active(self):
        form = StudentForm()

        self.assertTrue(form.fields["is_active"].initial)

    def test_student_detail_displays_contact_information(self):
        response = self.client.get(
            reverse("students:detail", args=[self.student.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.student.email)

    def test_update_student(self):
        response = self.client.post(
            reverse("students:update", args=[self.student.pk]),
            {
                "name": "Alex Morgan",
                "email": "alex@example.com",
                "phone": "555-0100",
                "course": "Physics",
                "enrollment_date": "2026-01-15",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("students:list"))
        self.student.refresh_from_db()
        self.assertEqual(self.student.course, "Physics")

    def test_delete_student(self):
        response = self.client.post(
            reverse("students:delete", args=[self.student.pk])
        )

        self.assertRedirects(response, reverse("students:list"))
        self.assertFalse(Student.objects.filter(pk=self.student.pk).exists())

    def test_duplicate_email_is_rejected(self):
        response = self.client.post(
            reverse("students:create"),
            {
                "name": "Another Alex",
                "email": "alex@example.com",
                "phone": "",
                "course": "Physics",
                "enrollment_date": "2026-01-15",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Student.objects.count(), 1)

    def test_dashboard_shows_student_summary(self):
        response = self.client.get(reverse("students:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_students"], 1)
        self.assertEqual(response.context["active_students"], 1)
        self.assertContains(response, "Alex Morgan")

    def test_student_list_filters_by_status_and_course(self):
        Student.objects.create(
            name="Sam Rivera",
            email="sam@example.com",
            course="Physics",
            is_active=False,
        )

        response = self.client.get(
            reverse("students:list"),
            {"status": "active", "course": "Computer Science"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["filtered_count"], 1)
        self.assertContains(response, "Alex Morgan")
        self.assertNotContains(response, "Sam Rivera")

    def test_csv_export_uses_selected_filters(self):
        Student.objects.create(
            name="Sam Rivera",
            email="sam@example.com",
            course="Physics",
            is_active=False,
        )

        response = self.client.get(
            reverse("students:export"),
            {"status": "active"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("Alex Morgan", response.content.decode("utf-8-sig"))
        self.assertNotIn("Sam Rivera", response.content.decode("utf-8-sig"))

    def test_management_pages_require_staff_login(self):
        self.client.logout()

        response = self.client.get(reverse("students:dashboard"))

        self.assertRedirects(
            response,
            f"{reverse('students:login')}?next={reverse('students:dashboard')}",
        )

    def test_non_staff_users_cannot_access_management_pages(self):
        self.client.logout()
        user = get_user_model().objects.create_user(
            username="student-user",
            password="test-password-123",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("students:list"))

        self.assertEqual(response.status_code, 403)


class StaffAccountManagementTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.superuser = user_model.objects.create_superuser(
            username="owner",
            email="owner@example.com",
            password="Owner-account!3482",
        )
        self.staff = user_model.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="Manager-account!3482",
            is_staff=True,
        )

    def test_superuser_can_view_staff_accounts(self):
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("students:staff-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "manager")

    def test_superuser_can_create_limited_staff_account(self):
        self.client.force_login(self.superuser)

        response = self.client.post(
            reverse("students:staff-create"),
            {
                "username": "new-manager",
                "first_name": "New",
                "last_name": "Manager",
                "email": "new-manager@example.com",
                "password1": "A-different-long-passphrase!3482",
                "password2": "A-different-long-passphrase!3482",
            },
        )

        self.assertRedirects(response, reverse("students:staff-list"))
        user = get_user_model().objects.get(username="new-manager")
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password("A-different-long-passphrase!3482"))

    def test_superuser_can_deactivate_and_reactivate_staff(self):
        self.client.force_login(self.superuser)
        url = reverse("students:staff-toggle-active", args=[self.staff.pk])

        response = self.client.post(url)

        self.assertRedirects(response, reverse("students:staff-list"))
        self.staff.refresh_from_db()
        self.assertFalse(self.staff.is_active)

        self.client.post(url)
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.is_active)

    def test_staff_cannot_manage_staff_accounts(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("students:staff-list"))

        self.assertEqual(response.status_code, 403)

    def test_regular_user_cannot_manage_staff_accounts(self):
        user = get_user_model().objects.create_user(
            username="regular",
            password="Regular-account!3482",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("students:staff-list"))

        self.assertEqual(response.status_code, 403)

    def test_staff_creation_rejects_duplicate_email(self):
        self.client.force_login(self.superuser)

        response = self.client.post(
            reverse("students:staff-create"),
            {
                "username": "another-manager",
                "first_name": "Another",
                "last_name": "Manager",
                "email": "manager@example.com",
                "password1": "A-different-long-passphrase!3482",
                "password2": "A-different-long-passphrase!3482",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            get_user_model().objects.filter(username="another-manager").exists()
        )

    def test_staff_toggle_requires_post(self):
        self.client.force_login(self.superuser)

        response = self.client.get(
            reverse("students:staff-toggle-active", args=[self.staff.pk])
        )

        self.assertEqual(response.status_code, 405)
