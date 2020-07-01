"""
Routes and views for the bottle application.
"""

from bottle import route, view
from datetime import datetime
import sys
import traceback
from datetime import datetime
from http import HTTPStatus
from app import ADAPTER
from aiohttp import web
from aiohttp.web import Request, Response, json_response
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    ConversationState,
    MemoryStorage,
    TurnContext,
    UserState,
)
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity, ActivityTypes

from bots import CustomPromptBot



# Catch-all for errors.
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")
    await context.send_activity(
        "To continue to run this bot, please fix the bot source code."
    )
    # Send a trace activity if we're talking to the Bot Framework Emulator
    if context.activity.channel_id == "emulator":
        # Create a trace activity that contains the error object
        trace_activity = Activity(
            label="TurnError",
            name="on_turn_error Trace",
            timestamp=datetime.utcnow(),
            type=ActivityTypes.trace,
            value=f"{error}",
            value_type="https://www.botframework.com/schemas/error",
        )
        # Send a trace activity, which will be displayed in Bot Framework Emulator
        await context.send_activity(trace_activity)

    # Clear out state
    await CONVERSATION_STATE.delete(context)


# Set the error handler on the Adapter.
# In this case, we want an unbound method, so MethodType is not needed.
ADAPTER.on_turn_error = on_error

# Create MemoryStorage and state
MEMORY = MemoryStorage()
USER_STATE = UserState(MEMORY)
CONVERSATION_STATE = ConversationState(MEMORY)

# Create Bot
BOT = CustomPromptBot(CONVERSATION_STATE, USER_STATE)


@route('/api/messages')
def messages(req: Request) -> Response:
    print('MESSAGES')
    """Renders the home page."""
    # if "application/json" in req.headers["Content-Type"]:
    #     body = await req.json()
    # else:
    #     return Response(status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
    #
    # activity = Activity().deserialize(body)
    # auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""
    #
    # response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
    # if response:
    #     return json_response(data=response.body, status=response.status)
    return Response(status=HTTPStatus.OK)
