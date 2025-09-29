## onboarding/urls/py
## pkibuka@milky-way.space


from django.urls import path

from onboarding import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("profile/", views.profile_view, name="profile"),
    path("log-in/", views.signin_view, name="signin"),
    path("onboarding/", views.signup_view, name="signup"),
]
