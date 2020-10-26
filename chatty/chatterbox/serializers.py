from rest_framework import serializers

from . import models


class MessageSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username')

    class Meta:
        model = models.Message
        fields = (
            'pk',
            'author_username',
            'text',
            'read',
            'created_at'
        )


class ConversationSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username')
    opponent_username = serializers.CharField(source='opponent.username')
    messages = MessageSerializer(many=True)

    class Meta:
        model = models.Conversation
        fields = (
            'pk',
            'owner_username',
            'opponent_username',
            'messages'
        )
