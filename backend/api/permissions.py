from rest_framework import permissions


class AuthorOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )


# class RecipeAuthorOrReadOnly(AuthorOrReadOnly):
#     def has_permission(self, request, view):
#         return (
#             request.method in permissions.SAFE_METHODS
#             and 'is_favorited' not in request.query_params
#             and 'is_in_shopping_cart' not in request.query_params
#             or request.user.is_authenticated
#         )
