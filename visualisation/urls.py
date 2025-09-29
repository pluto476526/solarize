## onboarding/urls/py
## pkibuka@milky-way.space


from django.urls import path

from visualisation import views

urlpatterns = [
    path("", views.index_view, name="dash"),
]
