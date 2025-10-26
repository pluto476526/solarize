## analytics/urls/py
## pkibuka@milky-way.space


from django.urls import path

from analytics import views

urlpatterns = [
    path("", views.index_view, name="dash"),
    path("PVWatts-energy-modelling/", views.pvwatts_modelling_view, name="pvwatts_modelling"),
    path("PVWatts-report/", views.pvwatts_report_view, name="pvwatts_report"),
    path("fixed-mount-system/", views.fixed_mount_system_view, name="fixed_mount_system"),
    path("single-axis-tracking/", views.single_axis_tracking_view, name="single_axis_tracking"),
    path("dual-axis-tracking/", views.dual_axis_tracking_view, name="dual_axis_tracking"),
    path("spec-sheet-modelling/", views.spec_sheet_modelling_view, name="spec_sheet_modelling"),
    path("bifacial-system/", views.bifacial_system_view, name="bifacial_system"),
    path("spectral-response/", views.spectral_response_view, name="spectral_response"),
    path("modelchain-result/", views.modelchain_result_view, name="modelchain_result"),
    path("NASA-climate-modelling/", views.climate_modelling_view, name="climate_modelling"),
    path("weather/", views.weather_view, name="weather"),
    path("astronomy/", views.astronomy_view, name="astronomy"),
    path("air-quality/", views.air_quality_view, name="air_quality"),
    path("module_search/", views.module_search, name="module_search"),
    path("inverter_search/", views.inverter_search, name="inverter_search"),
]
