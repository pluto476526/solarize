## onboarding/urls/py
## pkibuka@milky-way.space


from django.urls import path

from onboarding import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("accounts/profile/", views.profile_view, name="profile"),
    path("accounts/log-in/", views.signin_view, name="signin"),
    path("accounts/register/", views.signup_view, name="signup"),
    path("photovoltaic-simulation/", views.pv_modelling_view, name="pv_modelling"),
    path("features/", views.features_view, name="features"),
    path("data-sources/", views.data_sources_view, name="data_sources"),
    path("solutions/", views.solutions_view, name="solutions"),
]
