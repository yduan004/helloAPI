"""
User Models
===========
This module defines the User model that maps to the existing 'users' table 
in the PostgreSQL database.

The model uses Django's ORM (Object-Relational Mapping) to interact with 
the database without writing raw SQL queries.
"""

from django.db import models  # type: ignore
from django.utils import timezone  # type: ignore


class User(models.Model):
    """
    User Model
    ==========
    Represents a user in the system. This model maps to the 'users' table
    in your PostgreSQL database.
    
    Fields:
    -------
    - id: Primary key (auto-generated)
    - name: User's name
    - email: User's email address (unique)
    
    Meta:
    -----
    - db_table: 'users' - explicitly maps to your existing 'users' table
    - managed: False - tells Django not to create/modify this table
                       (since it already exists in your database)
    """
    
    # Primary key field (auto-incrementing integer)
    # If your existing table has 'id', Django will use it automatically
    id = models.AutoField(primary_key=True)
    
    # Name field - user's full name
    # max_length: maximum character length
    name = models.CharField(
        max_length=255,
        help_text="User's full name"
    )
    
    # Email field - for user communication
    # unique: ensures no two users can have the same email
    email = models.EmailField(
        max_length=254,
        unique=True,
        help_text="User's email address"
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
        
        # Default ordering for queries (by id)
        ordering = ['id']
        
        # Human-readable names for the model
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        """
        String representation of the User object.
        This is what you'll see in the Django admin and when printing the object.
        
        Returns:
        --------
        str: The name of the user
        """
        return self.name
    
    def save(self, *args, **kwargs):
        """
        Override the save method to add custom logic before saving.
        
        This is called every time a User object is saved to the database.
        You can add validation or data transformation here.
        """
        # Convert email to lowercase for consistency
        if self.email:
            self.email = self.email.lower()
        
        # Trim whitespace from name
        if self.name:
            self.name = self.name.strip()
        
        # Call the parent class's save method to actually save to database
        super().save(*args, **kwargs)
