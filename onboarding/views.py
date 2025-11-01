## onboarding/views.py
## pkibuka@milky-way.space

from django.shortcuts import render, redirect
from django.contrib.auth import models, authenticate, login, logout
from django.contrib import messages
from onboarding.models import Profile
import logging

logger = logging.getLogger(__name__)


def home_view(request):
    context = {}
    return render(request, "onboarding/index.html", context)


def profile_view(request):
    try:
        profile = Profile.objects.get(user=request.user)
    except Exception as e:
        return redirect("signup")

    if request.method == "POST":
        source = request.POST.get("source")

        if source == "update_profile_form":
            profile.full_name = request.POST.get("full_name")
            profile.bio = request.POST.get("bio")
            profile.phone = request.POST.get("phone")
            profile.job_title = request.POST.get("job_title")
            profile.department = request.POST.get("department")
            profile.avatar = request.FILES.get("avatar")
            profile.save()
            messages.success(request, "Profile details updated.")
            return redirect("profile")

    context = {"profile": profile}
    return render(request, "analytics/profile.html", context)


def features_view(request):
    context = {}
    return render(request, "onboarding/features.html", context)


def data_sources_view(request):
    context = {}
    return render(request, "onboarding/data_sources.html", context)


def solutions_view(request):
    context = {}
    return render(request, "onboarding/solutions.html", context)


def pv_modelling_view(request):
    context = {}
    return render(request, "onboarding/pv_modelling.html", context)


def climate_projection_view(request):
    context = {}
    return render(request, "onboarding/climate_projection.html", context)


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
            user = models.User.objects.create_user(username, email, password1)
            Profile.objects.create(user=user)
            messages.success(
                request, "Account succesfully created. You can now log in."
            )
            return redirect("signin")

    context = {}
    return render(request, "onboarding/signup.html", context)


def signout_view(request):
    logout(request)
    return redirect("home")
