#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

""" Bot Configuration """


class DefaultConfig:
    """ Bot Configuration """
    HOST = os.environ.get("SERVER_HOST", "localhost")
    PORT = os.environ.get("SERVER_PORT") or os.environ.get("port") or os.environ.get("PORT") or 3978
    APP_ID = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", ""),
    CHANNEL_SERVICE = os.environ.get("ChannelService", ""),
    OPEN_ID_META_DATA = os.environ.get("BotOpenIdMetadata", "")
