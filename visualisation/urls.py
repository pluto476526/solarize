## onboarding/urls/py
## pkibuka@milky-way.space


from django.urls import path

from visualisation import views

urlpatterns = [
    path("", views.index_view, name="dash"),
    path("energy-forecasts/", views.energy_forecasts_view, name="energy_forecasts"),
    path("energy-forecasts-report/", views.energy_forecasts_report_view, name="energy_forecast_report"),
]
