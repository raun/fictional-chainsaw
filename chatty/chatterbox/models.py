from django.db import models
from django.template.defaultfilters import date
from django.utils.timezone import localtime
from model_utils.models import TimeStampedModel, SoftDeletableModel
from django.conf import settings

from .managers import ConversationManager


class Conversation(TimeStampedModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Conversation Owner", related_name="dialogs",
                              on_delete=models.CASCADE)
    opponent = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Conversation Opponent",
                                 on_delete=models.CASCADE)

    objects = ConversationManager()

    def __str__(self):
        return "Chat with {}".format(self.opponent.username)


class Message(TimeStampedModel, SoftDeletableModel):
    conversation = models.ForeignKey(Conversation, verbose_name="Conversation", related_name="messages", on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Author", related_name="messages", on_delete=models.CASCADE)
    text = models.TextField(verbose_name="Message Text")
    read = models.BooleanField(verbose_name="Read", default=False)

    @property
    def created_at(self):
        return date(localtime(self.created), settings.DATETIME_FORMAT)

    def __str__(self):
        return "{} ({}) - {}".format(self.author.username, self.created_at, self.text)
