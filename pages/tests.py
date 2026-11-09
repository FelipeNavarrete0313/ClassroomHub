from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase
from django.urls import reverse

from .models import Category, Resource


class ClassroomHubTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name="Programming",
            description="Core programming topics",
        )
        cls.resource = Resource.objects.create(
            title="Python basics",
            description="Variables and functions",
            available=True,
            category=cls.category,
        )
        Resource.objects.create(
            title="Django models",
            description="Database fundamentals",
            available=False,
            category=cls.category,
        )

    def test_home_page_renders(self):
        response = self.client.get(reverse("pages:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/home.html")
        self.assertContains(response, "Welcome")

    def test_resources_page_displays_database_records(self):
        response = self.client.get(reverse("pages:resources"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/resources.html")
        self.assertContains(response, "Python basics")
        self.assertContains(response, "Django models")
        self.assertContains(response, "Coming soon")

    def test_resource_displays_related_category(self):
        response = self.client.get(reverse("pages:resources"))

        self.assertContains(response, "Category: Programming")

    def test_about_page_renders(self):
        response = self.client.get(reverse("pages:about"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/about.html")

    def test_home_navigation_links_to_resources(self):
        response = self.client.get(reverse("pages:home"))

        self.assertContains(
            response,
            f'href="{reverse("pages:resources")}"',
        )

    def test_unknown_page_returns_not_found(self):
        response = self.client.get("/not-found/")

        self.assertEqual(response.status_code, 404)

    def test_resource_updates_are_persisted(self):
        self.resource.available = False
        self.resource.save(update_fields=["available"])
        self.resource.refresh_from_db()

        self.assertFalse(self.resource.available)

    def test_category_protects_related_resources(self):
        with self.assertRaises(ProtectedError):
            self.category.delete()

        self.assertTrue(
            Category.objects.filter(pk=self.category.pk).exists()
        )

    def test_empty_catalog_shows_message(self):
        Resource.objects.all().delete()

        response = self.client.get(reverse("pages:resources"))

        self.assertContains(response, "No resources are available.")

    def test_category_reverse_relation_contains_resources(self):
        titles = set(
            self.category.resources.values_list("title", flat=True)
        )

        self.assertEqual(titles, {"Python basics", "Django models"})


class AvailableResourcesTests(TestCase):
    def test_only_available_resources_are_listed(self):
        category = Category.objects.create(name="Programming")
        Resource.objects.create(
            title="Open resource",
            available=True,
            category=category,
        )
        Resource.objects.create(
            title="Hidden resource",
            available=False,
            category=category,
        )

        response = self.client.get(reverse("pages:available-resources"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Open resource")
        self.assertNotContains(response, "Hidden resource")


class AuthenticationTests(TestCase):
    def setUp(self):
        self.password = "ExampleTestPassword!2026"
        self.user = get_user_model().objects.create_user(
            username="reader",
            password=self.password,
        )

    def test_signup_page_renders(self):
        response = self.client.get(reverse("pages:signup"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/signup.html")

    def test_signup_creates_regular_user(self):
        response = self.client.post(
            reverse("pages:signup"),
            {
                "username": "new_reader",
                "password1": "NewExamplePassword!2026",
                "password2": "NewExamplePassword!2026",
            },
        )

        self.assertRedirects(response, reverse("pages:login"))
        account = get_user_model().objects.get(username="new_reader")
        self.assertFalse(account.is_staff)
        self.assertFalse(account.is_superuser)
        self.assertTrue(account.check_password("NewExamplePassword!2026"))

    def test_signup_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse("pages:signup"),
            {
                "username": "invalid_reader",
                "password1": "ExamplePassword!2026",
                "password2": "DifferentPassword!2026",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            get_user_model().objects.filter(
                username="invalid_reader"
            ).exists()
        )

    def test_signup_rejects_existing_username(self):
        response = self.client.post(
            reverse("pages:signup"),
            {
                "username": "reader",
                "password1": "ExamplePassword!2026",
                "password2": "ExamplePassword!2026",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            get_user_model().objects.filter(username="reader").count(),
            1,
        )

    def test_login_rejects_wrong_password(self):
        response = self.client.post(
            reverse("pages:login"),
            {"username": "reader", "password": "wrong"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_redirects_to_dashboard(self):
        response = self.client.post(
            reverse("pages:login"),
            {"username": "reader", "password": self.password},
        )

        self.assertRedirects(response, reverse("pages:dashboard"))
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_respects_safe_next(self):
        destination = reverse("pages:dashboard")
        response = self.client.post(
            reverse("pages:login") + f"?next={destination}",
            {
                "username": "reader",
                "password": self.password,
                "next": destination,
            },
        )

        self.assertRedirects(response, destination)

    def test_anonymous_dashboard_redirects_to_login(self):
        response = self.client.get(reverse("pages:dashboard"))

        self.assertRedirects(
            response,
            reverse("pages:login") + "?next=/dashboard/",
        )

    def test_dashboard_session_counter_increments(self):
        self.client.force_login(self.user)

        first = self.client.get(reverse("pages:dashboard"))
        second = self.client.get(reverse("pages:dashboard"))

        self.assertEqual(first.context["visit_count"], 1)
        self.assertEqual(second.context["visit_count"], 2)

    def test_logout_get_is_not_allowed(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("pages:logout"))

        self.assertEqual(response.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

    def test_logout_post_ends_session(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("pages:logout"))

        self.assertRedirects(response, reverse("pages:home"))
        self.assertNotIn("_auth_user_id", self.client.session)
        protected = self.client.get(reverse("pages:dashboard"))
        self.assertEqual(protected.status_code, 302)

    def test_login_post_without_csrf_is_rejected(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.get(reverse("pages:login"))

        response = csrf_client.post(
            reverse("pages:login"),
            {"username": "reader", "password": self.password},
        )

        self.assertEqual(response.status_code, 403)


class ResourceReviewPermissionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="review_candidate",
            password="ExampleTestPassword!2026",
        )
        category = Category.objects.create(name="Programming")
        Resource.objects.create(
            title="Python basics",
            category=category,
        )

        content_type = ContentType.objects.get_for_model(Resource)
        permission = Permission.objects.get(
            content_type=content_type,
            codename="view_resource",
        )

        self.reviewers = Group.objects.create(
            name="Catalog reviewers",
        )
        self.reviewers.permissions.add(permission)

    def test_anonymous_review_redirects_to_login(self):
        response = self.client.get(reverse("pages:resource-review"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("pages:login"), response.url)

    def test_regular_user_cannot_open_review(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("pages:resource-review"))

        self.assertEqual(response.status_code, 403)

    def test_reviewer_can_open_review(self):
        self.user.groups.add(self.reviewers)
        self.client.force_login(self.user)

        response = self.client.get(reverse("pages:resource-review"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python basics")
        self.assertTemplateUsed(response, "pages/review.html")

    def test_reviewer_does_not_become_staff(self):
        self.user.groups.add(self.reviewers)
        self.user.refresh_from_db()

        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_public_catalog_remains_available(self):
        response = self.client.get(reverse("pages:resources"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python basics")

    def test_typing_review_url_cannot_bypass_permission(self):
        self.client.force_login(self.user)

        response = self.client.get("/resources/review/")

        self.assertEqual(response.status_code, 403)



class DashboardSummaryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name="Programming")
        Resource.objects.create(
            title="Python basics",
            available=True,
            category=category,
        )
        Resource.objects.create(
            title="Django models",
            available=False,
            category=category,
        )
        cls.user = get_user_model().objects.create_user(
            username="summary_reader",
            password="ExampleTestPassword!2026",
        )

    def test_anonymous_summary_redirects_to_login(self):
        url = reverse("pages:dashboard-summary")

        response = self.client.get(url)

        self.assertRedirects(
            response,
            reverse("pages:login") + f"?next={url}",
        )

    def test_authenticated_user_sees_resource_counts(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("pages:dashboard-summary"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/summary.html")
        self.assertEqual(response.context["total_resources"], 2)
        self.assertEqual(response.context["available_resources"], 1)


class ResourceCrudTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name="Programming",
            description="Programming resources",
        )
        cls.resource = Resource.objects.create(
            title="Python basics",
            description="Variables and functions",
            category=cls.category,
            available=True,
        )

        User = get_user_model()
        cls.reader = User.objects.create_user(
            username="crud_reader",
            password="ExampleTestPassword!2026",
        )
        cls.editor = User.objects.create_user(
            username="crud_editor",
            password="ExampleTestPassword!2026",
        )
        cls.reviewer = User.objects.create_user(
            username="crud_reviewer",
            password="ExampleTestPassword!2026",
        )

        content_type = ContentType.objects.get_for_model(Resource)
        all_permissions = Permission.objects.filter(
            content_type=content_type,
            codename__in=[
                "view_resource",
                "add_resource",
                "change_resource",
                "delete_resource",
            ],
        )
        editors = Group.objects.create(name="Catalog editors")
        editors.permissions.add(*all_permissions)
        cls.editor.groups.add(editors)

        review_permission = Permission.objects.get(
            content_type=content_type,
            codename="view_resource",
        )
        reviewers = Group.objects.create(name="Catalog reviewers")
        reviewers.permissions.add(review_permission)
        cls.reviewer.groups.add(reviewers)

    def resource_data(self, **overrides):
        values = {
            "title": "Database testing",
            "description": "Database integration practice",
            "resource_type": "Guide",
            "category": self.category.pk,
            "available": "on",
        }
        values.update(overrides)
        return values

    def test_resource_detail_is_public(self):
        url = reverse("pages:resource-detail", args=[self.resource.pk])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python basics")
        self.assertContains(response, "Programming")

    def test_unknown_resource_detail_returns_404(self):
        url = reverse("pages:resource-detail", args=[999999])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_public_catalog_links_to_resource_detail(self):
        response = self.client.get(reverse("pages:resources"))
        detail_url = reverse(
            "pages:resource-detail", args=[self.resource.pk]
        )

        self.assertContains(response, f'href="{detail_url}"')

    def test_create_redirects_anonymous_user_to_login(self):
        url = reverse("pages:resource-create")

        response = self.client.get(url)

        expected = reverse("pages:login") + f"?next={url}"
        self.assertRedirects(response, expected)

    def test_create_denies_authenticated_reader(self):
        self.client.force_login(self.reader)

        response = self.client.get(reverse("pages:resource-create"))

        self.assertEqual(response.status_code, 403)

    def test_reviewer_cannot_create_resource(self):
        self.client.force_login(self.reviewer)

        response = self.client.get(reverse("pages:resource-create"))

        self.assertEqual(response.status_code, 403)

    def test_editor_can_open_create_form(self):
        self.client.force_login(self.editor)

        response = self.client.get(reverse("pages:resource-create"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/resource_form.html")

    def test_reader_cannot_create_resource_via_post(self):
        self.client.force_login(self.reader)

        response = self.client.post(
            reverse("pages:resource-create"),
            self.resource_data(),
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            Resource.objects.filter(title="Database testing").exists()
        )

    def test_editor_can_create_resource(self):
        self.client.force_login(self.editor)

        response = self.client.post(
            reverse("pages:resource-create"),
            self.resource_data(),
        )

        self.assertRedirects(response, reverse("pages:resources"))
        self.assertTrue(
            Resource.objects.filter(title="Database testing").exists()
        )

    def test_create_rejects_short_title(self):
        self.client.force_login(self.editor)

        response = self.client.post(
            reverse("pages:resource-create"),
            self.resource_data(title="ab"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "title",
            "Title must contain at least 3 characters.",
        )
        self.assertFalse(Resource.objects.filter(title="ab").exists())

    def test_create_rejects_unknown_category(self):
        self.client.force_login(self.editor)

        response = self.client.post(
            reverse("pages:resource-create"),
            self.resource_data(category=999999),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("category", response.context["form"].errors)
        self.assertFalse(
            Resource.objects.filter(title="Database testing").exists()
        )

    def test_form_exposes_only_expected_fields(self):
        self.client.force_login(self.editor)

        response = self.client.get(reverse("pages:resource-create"))
        field_names = list(response.context["form"].fields)

        self.assertEqual(
            field_names,
            [
                "title",
                "description",
                "resource_type",
                "category",
                "available",
            ],
        )
        self.assertNotIn("created_at", field_names)

    def test_update_redirects_anonymous_user_to_login(self):
        url = reverse("pages:resource-update", args=[self.resource.pk])

        response = self.client.get(url)

        self.assertRedirects(
            response,
            reverse("pages:login") + f"?next={url}",
        )

    def test_update_denies_authenticated_reader(self):
        self.client.force_login(self.reader)
        url = reverse("pages:resource-update", args=[self.resource.pk])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)

    def test_reader_cannot_update_resource_via_post(self):
        self.client.force_login(self.reader)
        url = reverse(
            "pages:resource-update", args=[self.resource.pk]
        )

        response = self.client.post(
            url,
            self.resource_data(title="Forbidden update"),
        )

        self.assertEqual(response.status_code, 403)
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.title, "Python basics")

    def test_editor_can_open_update_form(self):
        self.client.force_login(self.editor)
        url = reverse("pages:resource-update", args=[self.resource.pk])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/resource_form.html")
        self.assertContains(response, "Python basics")

    def test_editor_can_update_existing_resource(self):
        self.client.force_login(self.editor)
        old_id = self.resource.pk
        url = reverse("pages:resource-update", args=[old_id])

        response = self.client.post(
            url,
            self.resource_data(
                title="Updated Python resource",
                available="",
            ),
        )

        self.assertRedirects(response, reverse("pages:resources"))
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.pk, old_id)
        self.assertEqual(self.resource.title, "Updated Python resource")
        self.assertFalse(self.resource.available)

    def test_invalid_update_keeps_existing_values(self):
        self.client.force_login(self.editor)
        old_title = self.resource.title
        url = reverse(
            "pages:resource-update", args=[self.resource.pk]
        )

        response = self.client.post(
            url,
            self.resource_data(title="ab"),
        )

        self.assertEqual(response.status_code, 200)
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.title, old_title)

    def test_delete_redirects_anonymous_user_to_login(self):
        url = reverse(
            "pages:resource-delete", args=[self.resource.pk]
        )

        response = self.client.get(url)

        self.assertRedirects(
            response,
            reverse("pages:login") + f"?next={url}",
        )

    def test_delete_denies_authenticated_reader(self):
        self.client.force_login(self.reader)
        url = reverse(
            "pages:resource-delete", args=[self.resource.pk]
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)

    def test_reviewer_cannot_delete_resource(self):
        self.client.force_login(self.reviewer)
        url = reverse(
            "pages:resource-delete", args=[self.resource.pk]
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            Resource.objects.filter(pk=self.resource.pk).exists()
        )

    def test_delete_get_only_shows_confirmation(self):
        self.client.force_login(self.editor)
        url = reverse(
            "pages:resource-delete", args=[self.resource.pk]
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "pages/resource_confirm_delete.html"
        )
        self.assertTrue(
            Resource.objects.filter(pk=self.resource.pk).exists()
        )

    def test_delete_post_removes_resource(self):
        self.client.force_login(self.editor)
        url = reverse(
            "pages:resource-delete", args=[self.resource.pk]
        )

        response = self.client.post(url)

        self.assertRedirects(response, reverse("pages:resources"))
        self.assertFalse(
            Resource.objects.filter(pk=self.resource.pk).exists()
        )

    def test_unknown_resource_update_returns_404_for_editor(self):
        self.client.force_login(self.editor)
        url = reverse("pages:resource-update", args=[999999])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_unknown_resource_delete_returns_404_for_editor(self):
        self.client.force_login(self.editor)
        url = reverse("pages:resource-delete", args=[999999])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_reader_does_not_see_edit_or_delete_links(self):
        self.client.force_login(self.reader)
        url = reverse(
            "pages:resource-detail", args=[self.resource.pk]
        )

        response = self.client.get(url)

        self.assertNotContains(response, "Edit resource")
        self.assertNotContains(response, "Delete resource")

    def test_editor_can_manage_without_staff_status(self):
        self.client.force_login(self.editor)

        self.assertFalse(self.editor.is_staff)
        self.assertFalse(self.editor.is_superuser)
        self.assertTrue(self.editor.has_perm("pages.add_resource"))
        self.assertTrue(self.editor.has_perm("pages.change_resource"))
        self.assertTrue(self.editor.has_perm("pages.delete_resource"))

    def test_editor_can_still_open_review_page(self):
        self.client.force_login(self.editor)

        response = self.client.get(reverse("pages:resource-review"))

        self.assertEqual(response.status_code, 200)

    def test_public_catalog_reflects_new_resource(self):
        Resource.objects.create(
            title="New catalog resource",
            category=self.category,
        )

        response = self.client.get(reverse("pages:resources"))

        self.assertContains(response, "New catalog resource")

    def test_post_without_csrf_is_rejected(self):
        from django.test import Client

        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.editor)

        response = csrf_client.post(
            reverse("pages:resource-create"),
            self.resource_data(),
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            Resource.objects.filter(title="Database testing").exists()
        )
