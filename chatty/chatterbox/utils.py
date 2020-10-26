from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.db.models import Q
from .models import Conversation


def get_conversation_between_users(user_1, user_2):
    """
    Args:
        user_1:
        user_2:

    Returns:

    """
    return Conversation.objects.filter(Q(owner=user_1, opponent=user_2) | Q(opponent=user_1, owner=user_2))


def get_user_from_session(session_key):
    """
    Args:
        session_key:

    Returns:

    """
    session = Session.objects.get(session_key=session_key)
    session_data = session.get_decoded()
    uid = session_data.get('_auth_user_id')
    user = get_user_model().objects.filter(id=uid).first()
    return user
