from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("", views.home, name="home"),
    path("resources/", views.resources, name="resources"),
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
    path("contact/", views.contact, name="contact"),
    path("topics/<slug:slug>/", views.topic_detail, name="topic-detail"),
]
