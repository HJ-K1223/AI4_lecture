from django.urls import path
from . import views
urlpatterns = [path("terms/", views.terms), path("terms/<int:pk>/delete/", views.delete_term)]

