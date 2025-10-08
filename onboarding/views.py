## onboarding/views.py
## pkibuka@milky-way.space

from django.shortcuts import render, redirect
from django.contrib.auth import models, authenticate, login, logout
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

def home_view(request):
    context = {}
    return render(request, "onboarding/nav.html", context)

def profile_view(request):
    context = {}
    return render(request, "visualisation/profile.html", context)


def features_view(request):
    context = {}
    return render(request, "onboarding/features.html", context)

def data_sources_view(request):
    context = {}
    return render(request, "onboarding/data_sources.html", context)

def solutions_view(request):
    context = {}
    return render(request, "onboarding/solutions.html", context)

def machine_learning_view(request):
    context = {}
    return render(request, "onboarding/machine_learning.html", context)


def signin_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Please check your credentials and try again")
    
    context = {}
    return render(request, "onboarding/signin.html", context)

def signup_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 == password2:
            models.User.objects.create_user(username, email, password1)
            messages.success(request, "Account succesfully created. You can now log in.")
            return redirect("signin")

    
    context = {}
    return render(request, "onboarding/signup.html", context)

def signout_view(request):
    logout(request)
    return redirect("home")


