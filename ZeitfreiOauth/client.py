import requests

class DiscordOAuthClient:
    def __init__(self, api_key:str):
        self.api_base_url = "http://localhost:2094"
        self.api_key = api_key
        self.headers = {
            "X-API-KEY": self.api_key
        }

    def get_user(self, user_id:int):
        """
        使用方法:
        user = client.get_user("1234567890")
        print(user)
        """
        response = requests.get(f"{self.api_base_url}/user/{user_id}", headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to get user {user_id}: {response.text}")
        return response.json()

    def delete_user(self, user_id:int):
        """
        使用方法:
        response = client.delete_user("1234567890")
        print(response)
        """
        response = requests.delete(f"{self.api_base_url}/delete_user/{user_id}", headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to delete user {user_id}: {response.text}")
        return response.json()

    def add_guild(self, guild_id:int, unauth_role:int, auth_role:int):
        """
        使用方法:
        response = client.add_guild("1234567890", "unauth_role_id", "auth_role_id")
        print(response)
        """
        data = {
            "guild_id": guild_id,
            "unauth_role": unauth_role,
            "auth_role": auth_role
        }
        response = requests.post(f"{self.api_base_url}/add_guild", headers=self.headers, json=data)
        if response.status_code != 200:
            raise Exception(f"Failed to add guild data: {response.text}")
        return response.json()

    def add_user_to_server(self, user_id:int):
        """
        使用方法:
        response = client.add_user_to_server("1234567890")
        print(response)
        """
        response = requests.post(f"{self.api_base_url}/add_user_to_server/{user_id}", headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to add user {user_id} to server: {response.text}")
        return response.json()