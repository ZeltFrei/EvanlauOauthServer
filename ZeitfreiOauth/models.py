from datetime import datetime
from typing import Optional

from aiohttp import ClientSession

from ZeitfreiOauth.utils import parse_datetime


class ResultResponse:
    """
    Represents a result response from the API.
    """

    def __init__(self,
                 status: Optional[str] = None,
                 message: Optional[str] = None,
                 error: Optional[str] = None,
                 *args, **kwargs):
        """
        Initialize the ResultResponse object.
        :param message: The message.
        :param error: The error.
        """
        if message is None and error is None:
            raise ValueError("message or error must be provided")

        self.status: Optional[str] = status
        self.message: Optional[str] = message
        self.error: Optional[str] = error

    def is_success(self) -> bool:
        return self.error is None

    @classmethod
    def from_dict(cls, data: dict) -> 'ResultResponse':
        """
        Create a ResultResponse object from a dictionary.
        :param data: The dictionary to create the ResultResponse object from.
        :return: The ResultResponse object.
        """
        return cls(
            status=data.get('status'),
            message=data.get('message'),
            error=data.get('error') or data.get('ERROR')
        )

    def to_dict(self) -> dict:
        """
        Convert the ResultResponse object to a dictionary.
        :return: The dictionary representation of the ResultResponse object.
        """
        data = {}

        if self.message is not None:
            data['message'] = self.message

        if self.error is not None:
            data['error'] = self.error

        if self.status is not None:
            data['status'] = self.status

        return data


class Guild:
    """
    Represents a guild.
    """

    def __init__(self,
                 guild_id: int,
                 authorized_role_id: int,
                 unauthorized_role_id: int,
                 reauthorize_delay: int):
        """
        Initialize the Guild object.
        :param guild_id: The guild ID.
        :param authorized_role_id: The authorized role ID.
        :param unauthorized_role_id: The unauthorized role ID.
        :param reauthorize_delay: The reauthorize delay.
        """
        self.guild_id: int = guild_id
        self.authorized_role_id: int = authorized_role_id
        self.unauthorized_role_id: int = unauthorized_role_id
        self.reauthorize_delay: int = reauthorize_delay

    async def register(self, client_session: ClientSession) -> ResultResponse:
        """
        Registers the guild with the API.
        :param client_session: The client session to use to register the guild.
        :return: The response from the API.
        """
        response = await client_session.post("/add_guild", json=self.to_dict())

        response.raise_for_status()

        return ResultResponse.from_dict(await response.json())

    async def remove(self, client_session: ClientSession) -> ResultResponse:
        """
        Removes the guild from the API.
        :param client_session: The client session to use to remove the guild.
        :return: The response from the API.
        """
        response = await client_session.delete("/delete_guild_data", json=self.to_dict())

        response.raise_for_status()

        return ResultResponse.from_dict(await response.json())

    @classmethod
    def from_dict(cls, data: dict) -> 'Guild':
        """
        Create a Guild object from a dictionary.
        :param data: The dictionary to create the Guild object from.
        :return: The Guild object.
        """
        return cls(
            guild_id=data['guild_id'],
            authorized_role_id=data['auth_role_id'],
            unauthorized_role_id=data['unauth_role_id'],
            reauthorize_delay=data['reauth_day']
        )

    def to_dict(self) -> dict:
        """
        Convert the Guild object to a dictionary.
        :return: The dictionary representation of the Guild object.
        """
        return {
            'guild_id': self.guild_id,
            'auth_role_id': self.authorized_role_id,
            'unauth_role_id': self.unauthorized_role_id,
            'reauth_day': self.reauthorize_delay
        }


class User:
    """
    Represents a authorized user.
    """

    def __init__(self,
                 user_id: int,
                 username: str,
                 discriminator: str,
                 access_token: str,
                 refresh_token: str,
                 expires_at: datetime):
        """
        Initialize the User object.
        :param user_id: The user ID.
        :param username: The username.
        :param discriminator: The discriminator.
        :param access_token: The access token.
        :param refresh_token: The refresh token.
        :param expires_at: The expiration date of the access token.
        """
        self.id: int = user_id
        self.username: str = username
        self.discriminator: str = discriminator
        self.access_token: str = access_token
        self.refresh_token: str = refresh_token
        self.expires_at: datetime = expires_at

    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """
        Create a User object from a dictionary
        :param data: The dictionary to create the User object from
        :return: The User object
        """
        return cls(
            user_id=data['id'],
            username=data['username'],
            discriminator=data['discriminator'],
            access_token=data['access_token'],
            refresh_token=data['refresh_token'],
            expires_at=parse_datetime(data['expires_at'])
        )

    def to_dict(self) -> dict:
        """
        Convert the User object to a dictionary
        :return: The dictionary representation of the User object
        """
        return {
            'id': self.id,
            'username': self.username,
            'discriminator': self.discriminator,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_at': self.expires_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }
