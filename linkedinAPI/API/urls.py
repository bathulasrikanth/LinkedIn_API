from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('linkedin/login/', views.linkedin_login, name='linkedin_login'),
    path('linkedin/callback/', views.linkedin_callback, name='linkedin_callback'),
    path('linkedin/posts/', views.linkedin_posts, name='linkedin_posts'),
    path('linkedin/create_post/', views.create_post, name='create_post'),
    path('linkedin/comment/<str:post_id>/', views.comment_on_post, name='comment_on_post'),
]
