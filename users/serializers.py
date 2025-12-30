"""
User Serializers
================
Serializers convert complex data types (like Django models) into Python 
data types that can be easily rendered into JSON, XML, or other content types.

They also handle deserialization - converting parsed data back into complex types
after validating the incoming data.

Think of serializers as translators between:
- Database models (Python objects) ←→ JSON (API data)
"""

from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    User Serializer
    ===============
    Handles serialization and deserialization of User model instances.
    
    This serializer:
    1. Converts User objects to JSON for API responses (serialization)
    2. Validates and converts JSON to User objects for API requests (deserialization)
    3. Provides automatic validation based on model field definitions
    
    ModelSerializer automatically:
    - Creates fields based on the model
    - Implements create() and update() methods
    - Provides default validation
    """
    
    # Read-only field that combines first_name and last_name
    # This field is computed and not stored in the database
    full_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        """
        Serializer Metadata
        ===================
        Configures which model and fields to use.
        """
        # The model this serializer is based on
        model = User
        
        # Fields to include in the serialized output
        # '__all__' includes all model fields
        # Alternative: specify fields explicitly like ['id', 'username', 'email']
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',      # Custom computed field
            'is_active',
            'created_at',
            'updated_at',
        ]
        
        # Read-only fields - cannot be modified through the API
        # These fields are automatically set by the system
        read_only_fields = ['id', 'created_at', 'updated_at']
        
        # Extra keyword arguments for fields
        # Provides additional validation and behavior
        extra_kwargs = {
            'email': {
                'required': True,  # Email is mandatory
                'allow_blank': False,  # Cannot be empty string
            },
            'username': {
                'required': True,  # Username is mandatory
                'allow_blank': False,  # Cannot be empty string
                'min_length': 3,  # Minimum 3 characters
                'max_length': 150,  # Maximum 150 characters
            },
            'first_name': {
                'required': False,  # Optional field
                'allow_blank': True,
            },
            'last_name': {
                'required': False,  # Optional field
                'allow_blank': True,
            },
        }
    
    def get_full_name(self, obj):
        """
        Custom method for the 'full_name' SerializerMethodField.
        
        SerializerMethodField requires a method named 'get_<field_name>'.
        This method is called to compute the field value.
        
        Parameters:
        -----------
        obj : User
            The User instance being serialized
        
        Returns:
        --------
        str: The user's full name
        """
        return obj.get_full_name()
    
    def validate_email(self, value):
        """
        Field-level validation for email.
        
        This method is automatically called when validating the email field.
        Method name pattern: validate_<field_name>
        
        Parameters:
        -----------
        value : str
            The email value to validate
        
        Returns:
        --------
        str: The validated (and possibly modified) email value
        
        Raises:
        -------
        serializers.ValidationError: If validation fails
        """
        # Convert email to lowercase for consistency
        value = value.lower()
        
        # Check if email already exists (for create operations)
        # self.instance is None for create, and the existing object for update
        if self.instance is None:  # Creating new user
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError(
                    "A user with this email already exists."
                )
        else:  # Updating existing user
            # Check if another user has this email
            if User.objects.filter(email=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "A user with this email already exists."
                )
        
        return value
    
    def validate_username(self, value):
        """
        Field-level validation for username.
        
        Parameters:
        -----------
        value : str
            The username value to validate
        
        Returns:
        --------
        str: The validated username value
        
        Raises:
        -------
        serializers.ValidationError: If validation fails
        """
        # Check if username already exists (for create operations)
        if self.instance is None:  # Creating new user
            if User.objects.filter(username=value).exists():
                raise serializers.ValidationError(
                    "A user with this username already exists."
                )
        else:  # Updating existing user
            # Check if another user has this username
            if User.objects.filter(username=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "A user with this username already exists."
                )
        
        return value
    
    def validate(self, data):
        """
        Object-level validation.
        
        This method is called after all field-level validations pass.
        Use it for validation that requires multiple fields.
        
        Parameters:
        -----------
        data : dict
            Dictionary of validated field data
        
        Returns:
        --------
        dict: The validated data
        
        Raises:
        -------
        serializers.ValidationError: If validation fails
        """
        # Example: You could add cross-field validation here
        # For instance, checking if first_name and last_name are both provided
        # or neither is provided
        
        return data
    
    def create(self, validated_data):
        """
        Create and return a new User instance.
        
        This method is called when saving a new user (POST request).
        ModelSerializer provides a default implementation, but you can
        override it for custom behavior.
        
        Parameters:
        -----------
        validated_data : dict
            Dictionary of validated data from the request
        
        Returns:
        --------
        User: The newly created User instance
        """
        # Create and return a new user instance
        user = User.objects.create(**validated_data)
        return user
    
    def update(self, instance, validated_data):
        """
        Update and return an existing User instance.
        
        This method is called when updating a user (PUT/PATCH request).
        
        Parameters:
        -----------
        instance : User
            The existing User instance to update
        validated_data : dict
            Dictionary of validated data from the request
        
        Returns:
        --------
        User: The updated User instance
        """
        # Update instance fields with validated data
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        
        # Save the updated instance to the database
        instance.save()
        return instance


class UserListSerializer(serializers.ModelSerializer):
    """
    Lightweight User Serializer for List Views
    ===========================================
    A simplified serializer for listing users.
    
    This serializer includes fewer fields for better performance
    when returning lists of users. Use this for GET /api/users/
    and use UserSerializer for detailed views.
    """
    
    class Meta:
        model = User
        # Only include essential fields for list view
        fields = ['id', 'username', 'email', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

