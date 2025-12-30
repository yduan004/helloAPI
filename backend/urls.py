"""
URL Configuration for Backend Project
======================================

This is the main URL configuration file for the Django project.
It routes incoming requests to the appropriate app-level URL configurations.

URL Structure:
--------------
http://localhost:8000/admin/          -> Django admin interface
http://localhost:8000/api/users/      -> Users API endpoints

How URL Routing Works:
----------------------
1. Request comes in: http://localhost:8000/api/users/1/
2. Django checks this file (backend/urls.py)
3. Finds pattern 'api/' and routes to users.urls
4. users/urls.py handles the rest: 'users/1/'
5. Router maps to appropriate view method
6. View processes and returns response

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django Admin Interface
    # Access at: http://localhost:8000/admin/
    path('admin/', admin.site.urls),
    
    # Users API Endpoints
    # All user-related endpoints are prefixed with 'api/'
    # Examples:
    # - http://localhost:8000/api/users/           (list/create users)
    # - http://localhost:8000/api/users/1/         (get/update/delete user)
    # - http://localhost:8000/api/users/1/activate/ (custom action)
    path('api/', include('users.urls')),
    
    # Django REST Framework's browsable API authentication
    # This adds login/logout to the browsable API interface
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
