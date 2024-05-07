"""
一個用於與ZeitFrei Discord OAuth授權API互動的Python函式庫。
"""

from .async_client import AsyncDiscordOAuthClient
from ZeitfreiOauth.old.client import DiscordOAuthClient
from .exceptions import UserIsUnauthorized, UserIsAlreadyIn
from .models import User, Guild, ResultResponse
from .utils import parse_datetime
