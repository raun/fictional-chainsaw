from django.contrib import admin

from .models import Conversation, Message


class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'opponent', 'created', 'modified', )
    search_fields = ('owner__username', 'opponent__username')


class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'author', 'text', 'read', )
    list_filter = ('read', )
    search_fields = ('author__username', )


admin.site.register(Conversation, ConversationAdmin)
admin.site.register(Message, MessageAdmin)
