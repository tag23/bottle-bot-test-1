"""
This script runs the application using a development server.
"""
import os
import sys
import bottle
from http import HTTPStatus

from aiohttp import web
from aiohttp.web import Request, Response, json_response

from botbuilder.core.integration import aiohttp_error_middleware
# routes contains the HTTP handlers for our server and must be imported.
# import routes
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, ConversationState, MemoryStorage, TurnContext, UserState


from config import DefaultConfig
from botbuilder.schema import Activity

from bots import CustomPromptBot

CONFIG = DefaultConfig()

# Create adapter.
# See https://aka.ms/about-bot-adapter to learn more about how bots work.
SETTINGS = BotFrameworkAdapterSettings(CONFIG.APP_ID, CONFIG.APP_PASSWORD, channel_auth_tenant=CONFIG.CHANNEL_SERVICE,
                                       open_id_metadata=CONFIG.OPEN_ID_META_DATA)
ADAPTER = BotFrameworkAdapter(SETTINGS)
MEMORY = MemoryStorage()
USER_STATE = UserState(MEMORY)
CONVERSATION_STATE = ConversationState(MEMORY)

# Create Bot
BOT = CustomPromptBot(CONVERSATION_STATE, USER_STATE)

HOST = CONFIG.HOST
try:
    PORT = CONFIG.PORT
except ValueError:
    PORT = 3978

if '--debug' in sys.argv[1:] or 'SERVER_DEBUG' in os.environ:
    # Debug mode will enable more verbose output in the console window.
    # It must be set at the beginning of the script.
    bottle.debug(True)

def wsgi_app():
    """Returns the application to make available through wfastcgi. This is used
    when the site is published to Microsoft Azure."""
    return bottle.default_app()


async def messages(req: Request) -> Response:
    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
    else:
        return Response(status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

    activity = Activity().deserialize(body)
    auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""

    response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
    if response:
        return json_response(data=response.body, status=response.status)
    return Response(status=HTTPStatus.OK)


APP = web.Application(middlewares=[aiohttp_error_middleware])
APP.router.add_post("/api/messages", messages)

# Starts a local test server.
# bottle.run(APP, host=HOST, port=PORT, reloader=True)
web.run_app(APP, host=HOST, port=PORT)
