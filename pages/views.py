from django.http import HttpResponse


from django.http import HttpResponse
from django.shortcuts import render


def home(request):
    context = {
        "welcome_message": "Explore learning resources and project ideas.",
    }
    return render(request, "pages/home.html", context)

def resources(request):
    context = {
        "resources": [
            {
                "title": "Python basics",
                "category": "Programming",
                "available": True,
            },
            {
                "title": "Git and GitHub",
                "category": "Collaboration",
                "available": True,
            },
            {
                "title": "Django models",
                "category": "Web development",
                "available": False,
            },
        ],
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