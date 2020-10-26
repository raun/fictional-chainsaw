import json
import logging

from .channels import new_messages, users_changed, online, offline, check_online, is_typing, read_unread

logger = logging.getLogger(__name__)


class MessageRouter(object):
    MESSAGE_QUEUE = {
        'new-message': new_messages,
        'new-user': users_changed,
        'online': online,
        'offline': offline,
        'check-online': check_online,
        'is-typing': is_typing,
        'read_message': read_unread
    }

    def __init__(self, data):
        try:
            self.packet = json.loads(data)
        except Exception as e:
            logger.debug('could not load json : {}'.format(e))

    def get_packet_type(self):
        return self.packet['type']

    async def put_packet(self):
        send_queue = self.get_queue()
        await send_queue.put(self.packet)

    def get_queue(self):
        return self.MESSAGE_QUEUE.get(self.get_packet_type())
