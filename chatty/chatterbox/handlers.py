import json
import logging

import websockets
from django.contrib.auth import get_user_model

from . import models, router
from .utils import get_user_from_session, get_conversation_between_users

logger = logging.getLogger(__name__)
ws_connections = {}


async def target_message(conn, payload):
    """
    Args:
        conn:
        payload:

    Returns:

    """
    try:
        await conn.send(json.dumps(payload))
    except Exception as e:
        logger.debug('could not send {}'.format(e))


async def fanout_message(connections, payload):
    """
    Args:
        connections:
        payload:

    Returns:

    """
    for conn in connections:
        try:
            await conn.send(json.dumps(payload))
        except Exception as e:
            logger.debug('could not send {}'.format(e))


async def mark_online(stream):
    """
    Args:
        stream:

    Returns:

    """
    while True:
        packet = await stream.get()
        session_id = packet.get('session_key')
        if session_id:
            user_owner = get_user_from_session(session_id)
            if user_owner:
                logger.debug('User ' + user_owner.username + ' gone online')
                # find all connections including user_owner as opponent,
                # send them a message that the user has gone online
                online_opponents = list(filter(lambda x: x[1] == user_owner.username, ws_connections))
                online_opponents_sockets = [ws_connections[i] for i in online_opponents]
                await fanout_message(online_opponents_sockets,
                                     {'type': 'mark-online', 'usernames': [user_owner.username]})
            else:
                pass
        else:
            pass


async def check_online(stream):
    """
    Args:
        stream:

    Returns:

    """
    while True:
        packet = await stream.get()
        session_id = packet.get('session_key')
        opponent_username = packet.get('username')
        if session_id and opponent_username:
            user_owner = get_user_from_session(session_id)
            if user_owner:
                # Find all connections including user_owner as opponent
                online_opponents = list(filter(lambda x: x[1] == user_owner.username, ws_connections))
                logger.debug('User ' + user_owner.username + ' has ' + str(len(online_opponents)) + ' opponents online')
                # Send user online statuses of his opponents
                socket = ws_connections.get((user_owner.username, opponent_username))
                if socket:
                    online_opponents_usernames = [i[0] for i in online_opponents]
                    await target_message(socket, {'type': 'mark-online', 'usernames': online_opponents_usernames})
                else:
                    pass
            else:
                pass
        else:
            pass


async def mark_offline(stream):
    """
    Args:
        stream:

    Returns:

    """
    while True:
        packet = await stream.get()
        session_id = packet.get('session_key')
        if session_id:
            user_owner = get_user_from_session(session_id)
            if user_owner:
                logger.debug('User ' + user_owner.username + ' gone offline')
                # find all connections including user_owner as opponent,
                #  send them a message that the user has gone offline
                online_opponents = list(filter(lambda x: x[1] == user_owner.username, ws_connections))
                online_opponents_sockets = [ws_connections[i] for i in online_opponents]
                await fanout_message(online_opponents_sockets, {'type': 'mark-offline', 'username': user_owner.username})
            else:
                pass
        else:
            pass


async def new_message_handler(stream):
    """
    Args:
        stream:

    Returns:

    """
    while True:
        packet = await stream.get()
        session_id = packet.get('session_key')
        msg_text = packet.get('message')
        username_opponent = packet.get('username')
        if session_id and msg_text and username_opponent:
            user_owner = get_user_from_session(session_id)
            if user_owner:
                user_opponent = get_user_model().objects.get(username=username_opponent)
                conversation = get_conversation_between_users(user_owner, user_opponent)
                if conversation.exists():
                    # Persist the message on database
                    msg = models.Message.objects.create(conversation=conversation.first(), author=user_owner, text=msg_text)
                    packet['created'] = msg.created_at()
                    packet['sender_name'] = msg.author.username
                    packet['message_id'] = msg.id

                    # Send the message
                    connections = []
                    if (user_owner.username, user_opponent.username) in ws_connections:
                        connections.append(ws_connections[(user_owner.username, user_opponent.username)])

                    if (user_opponent.username, user_owner.username) in ws_connections:
                        connections.append(ws_connections[(user_opponent.username, user_owner.username)])

                    else:
                        opponent_connections = list(filter(lambda x: x[0] == user_opponent.username, ws_connections))
                        opponent_connections_sockets = [ws_connections[i] for i in opponent_connections]
                        connections.extend(opponent_connections_sockets)

                    await fanout_message(connections, packet)
                else:
                    pass
            else:
                pass
        else:
            pass


async def users_changed_handler(stream):
    """
    Args:
        stream:

    Returns:

    """
    while True:
        await stream.get()
        users = [{'username': username, 'uuid': uuid_str} for username, uuid_str in ws_connections.values()]
        packet = {
            'type': 'users-changed',
            'value': sorted(users, key=lambda i: i['username'])
        }
        await fanout_message(ws_connections.keys(), packet)


async def is_typing_handler(stream):
    """
    Args:
        stream:

    Returns:

    """
    while True:
        packet = await stream.get()
        session_id = packet.get('session_key')
        user_opponent = packet.get('username')
        typing = packet.get('typing')
        if session_id and user_opponent and typing is not None:
            user_owner = get_user_from_session(session_id)
            if user_owner:
                opponent_socket = ws_connections.get((user_opponent, user_owner.username))
                if typing and opponent_socket:
                    await target_message(opponent_socket, {'type': 'opponent-typing', 'username': user_opponent})
            else:
                pass
        else:
            pass


async def read_message_handler(stream):
    """
    Args:
        stream:

    Returns:

    """
    while True:
        packet = await stream.get()
        session_id = packet.get('session_key')
        user_opponent = packet.get('username')
        message_id = packet.get('message_id')
        if session_id and user_opponent and message_id is not None:
            user_owner = get_user_from_session(session_id)
            if user_owner:
                message = models.Message.objects.filter(id=message_id)
                if message.exists():
                    message.update(read=True)
                    opponent_socket = ws_connections.get((user_opponent, user_owner.username))
                    if opponent_socket:
                        await target_message(opponent_socket, {'type': 'opponent-read-message', 'username': user_opponent, 'message_id': message_id})
                else:
                    pass
            else:
                pass
        else:
            pass


async def main_handler(websocket, path):
    """
    Args:
        websocket:
        path:

    Returns:

    """
    path = path.split('/')
    username = path[2]
    session_id = path[1]
    user_owner = get_user_from_session(session_id)
    if user_owner:
        user_owner = user_owner.username
        ws_connections[(user_owner, username)] = websocket
        try:
            while websocket.open:
                data = await websocket.recv()
                if not data:
                    continue
                try:
                    await router.MessageRouter(data).put_packet()
                except Exception as e:
                    logger.error('could not route message {}'.format(e))
        except websockets.exceptions.InvalidState:
            pass
        finally:
            del ws_connections[(user_owner, username)]
    else:
        logger.info("Got invalid session_id attempt to connect : {}".format(session_id))
