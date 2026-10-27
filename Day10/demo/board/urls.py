from django.urls import path
from . import views
urlpatterns = [path("posts/", views.post_list), path("posts/new/", views.edit), path("posts/<int:pk>/", views.detail),
 path("posts/<int:pk>/edit/", views.edit), path("posts/<int:pk>/delete/", views.delete_post),
 path("posts/<int:pk>/comments/", views.add_comment), path("comments/<int:pk>/delete/", views.delete_comment)]

