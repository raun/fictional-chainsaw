import asyncio
import ssl
import sys

import websockets
from django.conf import settings
from django.core.management import BaseCommand

from ... import handlers, channels


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('ssl_cert', nargs='?', type=str)

    def handle(self, *args, **options):
        ssl_cert = options.get('ssl_cert', None)
        if ssl_cert is not None:
            if sys.version_info >= (3, 6):
                protocol = ssl.PROTOCOL_TLS_SERVER
            elif sys.version_info >= (3, 4):
                protocol = ssl.PROTOCOL_TLSv1
            else:
                version = "{}.{}".format(sys.version_info.major, sys.version_info.minor)
                raise Exception('Version {} is not supported for wss!'.format(version))
            ssl_context = ssl.SSLContext(protocol)
            ssl_context.load_cert_chain(ssl_cert)
        else:
            ssl_context = None

        if hasattr(asyncio, "ensure_future"):
            ensure_future = asyncio.ensure_future
        else:
            ensure_future = getattr(asyncio, 'async')

        ensure_future(
            websockets.serve(
                handlers.main_handler,
                settings.CHAT_WS_HOST,
                settings.CHAT_WS_PORT,
                ssl=ssl_context
            )
        )
        ensure_future(handlers.new_message_handler(channels.new_messages))
        ensure_future(handlers.users_changed_handler(channels.users_changed))
        ensure_future(handlers.mark_online(channels.online))
        ensure_future(handlers.check_online(channels.check_online))
        ensure_future(handlers.mark_offline(channels.offline))
        ensure_future(handlers.is_typing_handler(channels.is_typing))
        ensure_future(handlers.read_message_handler(channels.read_unread))
        loop = asyncio.get_event_loop()
        loop.run_forever()
