from django.test import SimpleTestCase
from django.urls import reverse


class PageViewsTests(SimpleTestCase):
    def test_home_page_renders(self):
        response = self.client.get(reverse("pages:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/home.html")
        self.assertContains(response, "Welcome")

    def test_resources_page_shows_example_data(self):
        response = self.client.get(reverse("pages:resources"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/resources.html")
        self.assertContains(response, "Python basics")
        self.assertContains(response, "Coming soon")

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