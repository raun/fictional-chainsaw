from django.db import models
from django.db.models import Q


class ConversationManager(models.Manager):
    def get_all_conversations(self, user):
        return super(ConversationManager, self).get_queryset(Q(owner=user) | Q(opponent=user))
