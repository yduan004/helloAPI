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

from rest_framework import serializers  # type: ignore
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
    
    class Meta:
        """
        Serializer Metadata
        ===================
        Configures which model and fields to use.
        """
        # The model this serializer is based on
        model = User
        
        # Fields to include in the serialized output
        # Using '__all__' to include all model fields (id, name, email)
        fields = '__all__'
        
        # Alternatively, specify fields explicitly:
        # fields = ['id', 'name', 'email']
        
        # Read-only fields - cannot be modified through the API
        # ID is automatically set by the database
        read_only_fields = ['id']
        
        # Extra keyword arguments for fields
        # Provides additional validation and behavior
        extra_kwargs = {
            'email': {
                'required': True,  # Email is mandatory
                'allow_blank': False,  # Cannot be empty string
            },
            'name': {
                'required': True,  # Name is mandatory
                'allow_blank': False,  # Cannot be empty string
                'min_length': 1,  # Minimum 1 character
                'max_length': 255,  # Maximum 255 characters
            },
        }
    
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
    
    def validate_name(self, value):
        """
        Field-level validation for name.
        
        Parameters:
        -----------
        value : str
            The name value to validate
        
        Returns:
        --------
        str: The validated name value (trimmed)
        
        Raises:
        -------
        serializers.ValidationError: If validation fails
        """
        # Trim whitespace
        value = value.strip()
        
        # Ensure name is not empty after trimming
        if not value:
            raise serializers.ValidationError(
                "Name cannot be empty or just whitespace."
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
        instance.name = validated_data.get('name', instance.name)
        instance.email = validated_data.get('email', instance.email)
        
        # Save the updated instance to the database
        instance.save()
        return instance


class UserListSerializer(serializers.ModelSerializer):
    """
    Lightweight User Serializer for List Views
    ===========================================
    A simplified serializer for listing users.
    
    Since the User model is already simple (id, name, email),
    this serializer is the same as UserSerializer.
    You can customize this if you want to show fewer fields in list views.
    """
    
    class Meta:
        model = User
        # Include all fields (already minimal)
        fields = '__all__'
        read_only_fields = ['id']

