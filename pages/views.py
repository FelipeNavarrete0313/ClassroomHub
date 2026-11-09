from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse
from django.shortcuts import redirect, render

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
