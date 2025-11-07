from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.calendar_page, name="calendar"),
    path("feed/", views.events_feed, name="feed"),
    path("create/", views.create_event, name="create"),
    path("<int:pk>/update/", views.update_event, name="update"),
    path("<int:pk>/delete/", views.delete_event, name="delete"),
]
