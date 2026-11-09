from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    UpdateView,
)

from .forms import ResourceForm
from .models import Resource


def home(request):
    context = {
        "welcome_message": "Explore learning resources and project ideas.",
    }
    return render(request, "pages/home.html", context)


def resources(request):
    context = {
        "resources": Resource.objects.select_related("category").all(),
    }
    return render(request, "pages/resources.html", context)


def available_resources(request):
    context = {
        "resources": Resource.objects.select_related("category").filter(
            available=True,
        ),
    }
    return render(request, "pages/resources.html", context)


def about(request):
    context = {
        "purpose": "Practice URL routing, views, and templates.",
    }
    return render(request, "pages/about.html", context)


def contact(request):
    return HttpResponse("Información de contacto")


def topic_detail(request, slug):
    return HttpResponse(f"Requested topic: {slug}")


def signup(request):
    if request.user.is_authenticated:
        return redirect("pages:dashboard")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("pages:login")
    else:
        form = UserCreationForm()

    return render(request, "pages/signup.html", {"form": form})


@login_required
def dashboard(request):
    visit_count = request.session.get("dashboard_visits", 0) + 1
    request.session["dashboard_visits"] = visit_count

    return render(
        request,
        "pages/dashboard.html",
        {"visit_count": visit_count},
    )


@login_required
def dashboard_summary(request):
    context = {
        "total_resources": Resource.objects.count(),
        "available_resources": Resource.objects.filter(available=True).count(),
    }
    return render(request, "pages/summary.html", context)


@login_required
@permission_required("pages.view_resource", raise_exception=True)
def resource_review(request):
    context = {
        "resources": Resource.objects.select_related("category").all(),
    }
    return render(request, "pages/review.html", context)


class ResourceDetailView(DetailView):
    model = Resource
    template_name = "pages/resource_detail.html"
    context_object_name = "resource"


class ResourceCreateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    CreateView,
):
    model = Resource
    form_class = ResourceForm
    template_name = "pages/resource_form.html"
    permission_required = "pages.add_resource"
    success_url = reverse_lazy("pages:resources")
