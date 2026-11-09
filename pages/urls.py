from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("", views.home, name="home"),
    path("resources/", views.resources, name="resources"),
    path(
        "resources/review/",
        views.resource_review,
        name="resource-review",
    ),
    path(
        "resources/new/",
        views.ResourceCreateView.as_view(),
        name="resource-create",
    ),
    path(
        "resources/<int:pk>/",
        views.ResourceDetailView.as_view(),
        name="resource-detail",
    ),
    path(
        "resources/<int:pk>/edit/",
        views.ResourceUpdateView.as_view(),
        name="resource-update",
    ),
    path(
        "resources/<int:pk>/delete/",
        views.ResourceDeleteView.as_view(),
        name="resource-delete",
    ),
    path(
        "resources/available/",
        views.available_resources,
        name="available-resources",
    ),
    path("about/", views.about, name="about"),
    path("accounts/signup/", views.signup, name="signup"),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="pages/login.html"),
        name="login",
    ),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "dashboard/summary/",
        views.dashboard_summary,
        name="dashboard-summary",
    ),
    path("contact/", views.contact, name="contact"),
    path("topics/<slug:slug>/", views.topic_detail, name="topic-detail"),
]
