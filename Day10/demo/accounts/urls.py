from django.urls import path
from . import views
urlpatterns = [path("signup/", views.signup), path("login/", views.signin), path("logout/", views.signout), path("password-help/", views.password_help)]

