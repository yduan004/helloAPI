"""
User Models
===========
This module defines the User model that maps to the existing 'users' table 
in the PostgreSQL database.

The model uses Django's ORM (Object-Relational Mapping) to interact with 
the database without writing raw SQL queries.
"""

from django.db import models
from django.utils import timezone


class User(models.Model):
    """
    User Model
    ==========
    Represents a user in the system. This model maps to the 'users' table
    in your PostgreSQL database.
    
    Fields:
    -------
    - id: Primary key (auto-generated)
    - username: Unique username for the user
    - email: User's email address (unique)
    - first_name: User's first name
    - last_name: User's last name
    - is_active: Whether the user account is active
    - created_at: Timestamp when the user was created
    - updated_at: Timestamp when the user was last updated
    
    Meta:
    -----
    - db_table: 'users' - explicitly maps to your existing 'users' table
    - managed: False - tells Django not to create/modify this table
                       (since it already exists in your database)
    """
    
    # Primary key field (auto-incrementing integer)
    # If your existing table has 'id', Django will use it automatically
    id = models.AutoField(primary_key=True)
    
    # Username field - unique identifier for login
    # max_length: maximum character length
    # unique: ensures no two users can have the same username
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text="Required. 150 characters or fewer."
    )
    
    # Email field - for user communication
    # unique: ensures no two users can have the same email
    email = models.EmailField(
        max_length=254,
        unique=True,
        help_text="User's email address"
    )
    
    # First name field
    # blank=True: allows empty values in forms
    # null=True: allows NULL in database
    first_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="User's first name"
    )
    
    # Last name field
    last_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="User's last name"
    )
    
    # Active status - for soft deletes or account suspension
    # default=True: new users are active by default
    is_active = models.BooleanField(
        default=True,
        help_text="Designates whether this user should be treated as active."
    )
    
    # Timestamp fields for tracking record creation and updates
    # auto_now_add: automatically set when object is first created
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the user was created"
    )
    
    # auto_now: automatically updated every time the object is saved
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the user was last updated"
    )
    
    class Meta:
        """
        Model Metadata
        ==============
        Defines how Django should interact with the database table.
        """
        # Explicitly specify the database table name
        # This maps to your existing 'users' table
        db_table = 'users'
        
        # managed = False tells Django NOT to create/modify/delete this table
        # Set to False because the table already exists in your database
        # If you want Django to manage the table, set this to True
        managed = False
        
        # Default ordering for queries (newest first)
        ordering = ['-created_at']
        
        # Human-readable names for the model
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        """
        String representation of the User object.
        This is what you'll see in the Django admin and when printing the object.
        
        Returns:
        --------
        str: The username of the user
        """
        return self.username
    
    def get_full_name(self):
        """
        Returns the user's full name.
        
        Returns:
        --------
        str: First name and last name with a space in between,
             or just the username if names are not set.
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.username
    
    def save(self, *args, **kwargs):
        """
        Override the save method to add custom logic before saving.
        
        This is called every time a User object is saved to the database.
        You can add validation or data transformation here.
        """
        # Convert email to lowercase for consistency
        if self.email:
            self.email = self.email.lower()
        
        # Call the parent class's save method to actually save to database
        super().save(*args, **kwargs)
