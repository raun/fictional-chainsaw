from django.conf.urls import url

from .views import ConversationListView

urlpatterns = [
    url(
        regex=r'^conversations/(?P<username>[\w.A+-]+)$',
        view=ConversationListView.as_view(),
        name='conversations_detail'
    ),
    url(
        regex=r'^conversations/$',
        view=ConversationListView.as_view(),
        name='conversations'
    ),
]
