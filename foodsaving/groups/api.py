from rest_framework import filters
from rest_framework import mixins
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, BasePermission
from rest_framework.schemas import is_custom_action
from rest_framework.viewsets import GenericViewSet

from foodsaving.groups.filters import GroupsFilter
from foodsaving.groups.serializers import GroupDetailSerializer, GroupPreviewSerializer, GroupJoinSerializer, \
    GroupLeaveSerializer
from foodsaving.groups.models import Group as GroupModel
from foodsaving.utils.mixins import PartialUpdateModelMixin


class IsMember(BasePermission):
    message = 'You are not a member.'

    def has_object_permission(self, request, view, obj):
        return request.user in obj.members.all()


class IsNotMember(BasePermission):
    message = 'You are a member.'

    def has_object_permission(self, request, view, obj):
        return request.user not in obj.members.all()


class GroupViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    PartialUpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    """
    Groups

    # Query parameters
    - `?members` - filter by member user id
    - `?search` - search in name and public description
    - `?include_empty` - set to False to exclude empty groups without members
    """
    queryset = GroupModel.objects
    filter_backends = (filters.SearchFilter, filters.DjangoFilterBackend)
    filter_class = GroupsFilter
    search_fields = ('name', 'public_description')

    def get_serializer_class(self):
        if self.action == 'create':
            self.serializer_class = GroupDetailSerializer
        elif self.action in ('retrieve', 'update', 'partial_update'):
            self.serializer_class = GroupPreviewSerializer
            try:
                if self.request.user in self.get_object().members.all():
                    self.serializer_class = GroupDetailSerializer
            except AssertionError:
                # Swagger (using OpenAPI) does not give a pk, therefore
                # we can't determine if it's legit to return the Detail serializer
                pass
        elif is_custom_action(self.action):
            pass
        else:
            self.serializer_class = GroupPreviewSerializer
        return self.serializer_class

    def get_permissions(self):
        if self.action in ('update', 'partial_update'):
            self.permission_classes = (IsMember,)
        elif is_custom_action(self.action):
            pass
        else:
            self.permission_classes = (IsAuthenticatedOrReadOnly,)

        return super().get_permissions()

    @detail_route(
        methods=['POST'],
        permission_classes=(IsAuthenticated, IsNotMember),
        serializer_class=GroupJoinSerializer
    )
    def join(self, request, pk=None):
        return self.partial_update(request)

    @detail_route(
        methods=['POST'],
        permission_classes=(IsAuthenticated, IsMember),
        serializer_class=GroupLeaveSerializer
    )
    def leave(self, request, pk=None):
        return self.partial_update(request)
