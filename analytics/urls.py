## analytics/urls/py
## pkibuka@milky-way.space


from django.urls import path

from analytics import views

urlpatterns = [
    path("", views.index_view, name="dash"),
    path("PVWatts-energy-modelling/", views.pvwatts_modelling_view, name="pvwatts_modelling"),
    path("PVWatts-report/", views.pvwatts_report_view, name="pvwatts_report"),
    path("pvlib-energy-modelling/", views.pvlib_modelling_view, name="pvlib_modelling"),
    path("NASA-climate-modelling/", views.climate_modelling_view, name="climate_modelling"),
    path("weather/", views.weather_view, name="weather"),
    path("astronomy/", views.astronomy_view, name="astronomy"),
    path("air-quality/", views.air_quality_view, name="air_quality"),
    path("machine-learning/", views.machine_learning_view, name="machine_learning_dash"),
]
