"""
User Admin Configuration
=========================
This module configures how the User model appears in the Django admin interface.

Django Admin is a built-in web interface for managing your database.
Access it at: http://localhost:8000/admin/

To create an admin user, run:
    python manage.py createsuperuser
"""

from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Admin configuration for User model.
    
    This class customizes how users are displayed and managed in the admin interface.
    """
    
    # Fields to display in the list view
    list_display = [
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'is_active',
        'created_at',
        'updated_at',
    ]
    
    # Fields that are clickable links to the detail page
    list_display_links = ['id', 'username']
    
    # Fields that can be edited directly in the list view
    list_editable = ['is_active']
    
    # Filters in the right sidebar
    list_filter = [
        'is_active',
        'created_at',
        'updated_at',
    ]
    
    # Search functionality
    search_fields = [
        'username',
        'email',
        'first_name',
        'last_name',
    ]
    
    # Default ordering (newest first)
    ordering = ['-created_at']
    
    # Number of items per page
    list_per_page = 25
    
    # Fields to display in the detail/edit form
    fields = [
        'username',
        'email',
        'first_name',
        'last_name',
        'is_active',
        'created_at',
        'updated_at',
    ]
    
    # Read-only fields (cannot be edited)
    readonly_fields = ['created_at', 'updated_at']
    
    # Group fields into sections (optional)
    fieldsets = (
        ('Basic Information', {
            'fields': ('username', 'email')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),  # Collapsible section
        }),
    )
    
    def get_queryset(self, request):
        """
        Customize the queryset used in the admin.
        
        This method is called to get the list of objects to display.
        """
        queryset = super().get_queryset(request)
        return queryset
    
    def has_delete_permission(self, request, obj=None):
        """
        Determine if the user has permission to delete objects.
        
        You can customize this to prevent deletion of certain users.
        """
        return True  # Allow deletion
    
    def save_model(self, request, obj, form, change):
        """
        Custom save logic when saving through admin.
        
        Parameters:
        -----------
        request : HttpRequest
            The current request
        obj : User
            The user instance being saved
        form : ModelForm
            The form instance
        change : bool
            True if updating existing object, False if creating new
        """
        # You can add custom logic here before saving
        # For example, logging who made the change
        super().save_model(request, obj, form, change)
