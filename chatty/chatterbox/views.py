from django.db.models import Q
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .serializers import ConversationSerializer
from . import models


class ConversationListView(ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        queryset = models.Conversation.objects.filter(Q(owner=self.request.user) | Q(opponent=self.request.user))
        return queryset
