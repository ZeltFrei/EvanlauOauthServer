from typing import AsyncIterable

from aiohttp import ClientSession, ClientResponseError

from ZeitfreiOauth.exceptions import UserIsUnauthorized, UserIsAlreadyIn
from ZeitfreiOauth.models import User, Guild, ResultResponse


class AsyncDiscordOAuthClient:
    def __init__(self, api_key: str, api_base_url: str = "http://localhost:2094"):
        """
        Initialize the API Client.
        """
        self.api_base_url: str = api_base_url
        self.api_key: str = api_key

        self.session = ClientSession(
            base_url=self.api_base_url,
            headers={
                "X-API-KEY": self.api_key
            }
        )

    async def get_user(self, user_id: int) -> User:
        """
        Get a authorized user by user ID.
        :param user_id: The user ID to get the user for.
        :return: The User object.
        """
        response = await self.session.get(f"/user/{user_id}")

        response.raise_for_status()

        return User.from_dict(await response.json())

    async def get_all_user(self) -> AsyncIterable[User]:
        """
        Get all the authorized user.
        :return: A dictionary containing all authorized user data
        """
        response = await self.session.get("/all_user")

        response.raise_for_status()

        for user_data in await response.json():
            yield User.from_dict(user_data)

    async def get_auth_role_data(self, unauthorized_role_id: int, authorized_role_id: int) -> AsyncIterable[Guild]:
        """
        Get specific unauthorized/authorized role data.
        :param unauthorized_role_id: The unauthorized role ID to get the data for.
        :param authorized_role_id: The authorized role ID to get the data for.
        """
        response = await self.session.get(f"/get_auth_role_data/{unauthorized_role_id}+{authorized_role_id}")

        response.raise_for_status()

        for guild_data in await response.json():
            yield Guild.from_dict(guild_data)

    async def get_guild_auth_role_data(self, guild_id: int) -> Guild:
        """
        Get the unauthorized/authorized role data for a guild.
        :param guild_id: The guild ID to get the data for.
        :return: The Guild object.
        """
        response = await self.session.get(f"/get_guild_auth_role_data/{guild_id}")

        response.raise_for_status()

        return Guild.from_dict(await response.json())

    async def delete_user(self, user_id: int) -> bool:
        """
        Delete a user by user ID.
        :param user_id: The user ID to delete the user for.
        :return: always True
        """
        response = await self.session.delete(f"/delete_user/{user_id}")

        response.raise_for_status()

        return True

    async def add_guild(self, guild: Guild) -> ResultResponse:
        """
        Register a guild with the API.
        :param guild: The guild to register.
        :return: The response from the API.
        """
        return await guild.register(self.session)

    async def delete_guild_data(self, guild: Guild) -> ResultResponse:
        """
        Remove a guild from the API.
        :param guild: The guild to remove.
        :return: The response from the API.
        """
        return await guild.remove(self.session)

    async def add_user_to_server(self, user_id: int) -> ResultResponse:
        """
        Add a user to a server.
        :param user_id: The user ID to add to the server.
        """
        response = await self.session.post(f"/add_user_to_server/{user_id}")

        try:
            response.raise_for_status()

        except ClientResponseError as error:
            if error.status == 403:
                raise UserIsUnauthorized()
            elif error.status == 204:
                raise UserIsAlreadyIn()
            else:
                raise error

        return ResultResponse.from_dict(await response.json())
