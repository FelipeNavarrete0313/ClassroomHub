from django.db.models.deletion import ProtectedError
from django.test import TestCase
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
