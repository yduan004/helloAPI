"""
User Views
==========
Views handle the business logic for API endpoints. They receive HTTP requests,
process them, and return HTTP responses.

This module implements CRUD (Create, Read, Update, Delete) operations for users
using Django REST Framework's ViewSets.

API Workflow:
-------------
1. Client sends HTTP request (GET, POST, PUT, PATCH, DELETE)
2. Django routes the request to the appropriate view based on URL
3. View processes the request:
   - Validates data using serializers
   - Performs database operations using models
   - Handles business logic
4. View returns HTTP response (usually JSON)
"""

from rest_framework import viewsets, status  # type: ignore
from rest_framework.response import Response  # type: ignore

from .models import User
from .serializers import UserSerializer, UserListSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    User ViewSet
    ============
    A ViewSet that provides complete CRUD operations for User model.
    
    ModelViewSet automatically provides:
    - list()    : GET    /api/users/          - List all users
    - create()  : POST   /api/users/          - Create a new user
    - retrieve(): GET    /api/users/{id}/     - Get a specific user
    - update()  : PUT    /api/users/{id}/     - Update a user (full update)
    - partial_update(): PATCH /api/users/{id}/ - Update a user (partial update)
    - destroy() : DELETE /api/users/{id}/     - Delete a user
    
    HTTP Methods Explained:
    -----------------------
    - GET: Retrieve data (read-only, no side effects)
    - POST: Create new resource
    - PUT: Replace entire resource (all fields required)
    - PATCH: Update specific fields (partial update)
    - DELETE: Remove resource
    
    Attributes:
    -----------
    queryset : QuerySet
        The base queryset for all operations
    serializer_class : Serializer
        The default serializer class to use
    """
    
    # Base queryset - retrieves all users from database
    # This is the starting point for all queries
    queryset = User.objects.all()
    
    # Default serializer class for this viewset
    serializer_class = UserSerializer
    
    def get_queryset(self):
        """
        Get the queryset for this view.
        
        This method is called to get the list of objects for this view.
        You can customize it to filter, search, or order results.
        
        Returns:
        --------
        QuerySet: Filtered and ordered queryset
        """
        queryset = User.objects.all()
        
        # Optional: Add search functionality
        # Example: /api/users/?search=john
        search = self.request.query_params.get('search', None)
        if search:
            # Search in name and email fields
            queryset = queryset.filter(
                name__icontains=search
            ) | queryset.filter(
                email__icontains=search
            )
        
        # Order by id
        return queryset.order_by('id')
    
    def get_serializer_class(self):
        """
        Return the serializer class to use.
        
        This method allows using different serializers for different actions.
        For example, use a lightweight serializer for list views and a
        detailed serializer for detail views.
        
        Returns:
        --------
        Serializer: The serializer class to use
        """
        # Use lightweight serializer for list action
        if self.action == 'list':
            return UserListSerializer
        # Use full serializer for all other actions
        return UserSerializer
    
    def list(self, request, *args, **kwargs):
        """
        List all users.
        
        Endpoint: GET /api/users/
        
        Query Parameters:
        -----------------
        - search: Search in name and email fields
        - page: Page number for pagination
        
        Response:
        ---------
        200 OK: List of users with pagination
        {
            "count": 100,
            "next": "http://api.example.org/users/?page=2",
            "previous": null,
            "results": [
                {
                    "id": 1,
                    "name": "John Doe",
                    "email": "john@example.com"
                },
                ...
            ]
        }
        """
        # Get the filtered queryset
        queryset = self.get_queryset()
        
        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        # If pagination is disabled, return all results
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """
        Create a new user.
        
        Endpoint: POST /api/users/
        
        Request Body:
        -------------
        {
            "name": "John Doe",
            "email": "john@example.com"
        }
        
        Response:
        ---------
        201 Created: User created successfully
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com"
        }
        
        400 Bad Request: Validation error
        {
            "name": ["This field is required."],
            "email": ["This field is required."]
        }
        """
        # Get serializer with request data
        serializer = self.get_serializer(data=request.data)
        
        # Validate the data
        # raise_exception=True will return 400 Bad Request if validation fails
        serializer.is_valid(raise_exception=True)
        
        # Save the new user to database
        self.perform_create(serializer)
        
        # Return response with created user data
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def perform_create(self, serializer):
        """
        Perform the actual creation of the user.
        
        Override this method to add custom logic before saving.
        For example, you could set the user who created this record.
        
        Parameters:
        -----------
        serializer : Serializer
            The validated serializer instance
        """
        serializer.save()
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a specific user by ID.
        
        Endpoint: GET /api/users/{id}/
        
        Response:
        ---------
        200 OK: User found
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com"
        }
        
        404 Not Found: User doesn't exist
        {
            "detail": "Not found."
        }
        """
        # Get the user instance
        instance = self.get_object()
        
        # Serialize the user
        serializer = self.get_serializer(instance)
        
        # Return the serialized data
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """
        Update a user (full update - all fields required).
        
        Endpoint: PUT /api/users/{id}/
        
        Request Body:
        -------------
        {
            "name": "John Doe Updated",
            "email": "john.updated@example.com"
        }
        
        Response:
        ---------
        200 OK: User updated successfully
        {
            "id": 1,
            "name": "John Doe Updated",
            "email": "john.updated@example.com"
        }
        
        400 Bad Request: Validation error
        404 Not Found: User doesn't exist
        """
        # partial=False means all fields are required (PUT)
        partial = kwargs.pop('partial', False)
        
        # Get the user instance
        instance = self.get_object()
        
        # Get serializer with instance and new data
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        # Validate the data
        serializer.is_valid(raise_exception=True)
        
        # Save the updated user
        self.perform_update(serializer)
        
        # Return updated data
        return Response(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """
        Partially update a user (only provided fields are updated).
        
        Endpoint: PATCH /api/users/{id}/
        
        Request Body (only include fields you want to update):
        -------------------------------------------------------
        {
            "name": "Johnny Doe"
        }
        
        Response:
        ---------
        200 OK: User updated successfully
        {
            "id": 1,
            "name": "Johnny Doe",  // updated
            "email": "john@example.com"  // unchanged
        }
        """
        # partial=True means only provided fields are required (PATCH)
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def perform_update(self, serializer):
        """
        Perform the actual update of the user.
        
        Override this method to add custom logic before saving.
        
        Parameters:
        -----------
        serializer : Serializer
            The validated serializer instance
        """
        serializer.save()
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a user.
        
        Endpoint: DELETE /api/users/{id}/
        
        Response:
        ---------
        204 No Content: User deleted successfully
        404 Not Found: User doesn't exist
        """
        # Get the user instance
        instance = self.get_object()
        
        # Delete the user
        self.perform_destroy(instance)
        
        # Return success response with no content
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def perform_destroy(self, instance):
        """
        Perform the actual deletion of the user.
        
        Parameters:
        -----------
        instance : User
            The user instance to delete
        """
        # Hard delete - actually removes from database
        instance.delete()
