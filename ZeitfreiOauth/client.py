import requests

class DiscordOAuthClient:
    def __init__(self, api_key: str, api_base_url: str = "http://localhost:2094", client_id: int = 1020705629360365678):
        """
        載入Zeitfrei Discord OAuth函式庫
        伺服器預設位置為「http://localhost:2094」
        client_id預設為使用Qlipoth之應用程式帳號ID
        """
        self.api_base_url:str = api_base_url
        self.api_key:str = api_key
        self.auth_url: str = f"https://discord.com/api/oauth2/authorize?client_id={client_id}&redirect_uri=https://oauth.zeitfrei.tw/callback&&response_type=code&scope=guilds%20email%20guilds.join%20identify"
        self.headers:dict = {
            "X-API-KEY": self.api_key
        }

    def get_user(self, user_id:int) -> dict:
        """
        藉由使用ID查詢使用者已授權之資料

        使用方法:
        user = client.get_user(1234567890)
        print(user)
        """
        response = requests.get(f"{self.api_base_url}/user/{user_id}", headers=self.headers)
        if response.status_code != 200:
            return None
        return response.json()
    
    def get_guild_auth_role_data(self, guild_id:int) -> dict:
        """
        獲取伺服器登記之未授權/已授權身分組資料

        使用方法:
        guild_data = client.get_guild_auth_role_data("guild_id")
        """
        response = requests.get(f"{self.api_base_url}/get_guild_auth_role_data/{guild_id}", headers=self.headers)
        if response.status_code != 200 or len(dict(response.json())) == 0:
            return None
        return response.json()

    def delete_user(self, user_id:int) -> dict:
        """
        使用`delete_user`方法，你可以根據指定的使用者ID刪除使用者。
        這僅會將使用者從所有擁有此系統的伺服器中踢除該成員，使用者可以重新進行授權。

        使用方法:
        response = client.delete_user(1234567890)
        print(response)
        """
        response = requests.delete(f"{self.api_base_url}/delete_user/{user_id}", headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to delete user {user_id}: {response.text}")
        return response.json()

    def add_guild(self, guild_id:int, unauth_role:int, auth_role:int) -> dict:
        """
        添加未認證/已認證身分組的設定資料，資料為伺服器ID、未授權身分組ID和已授權身分組ID。
        
        使用方法:
        response = client.add_guild(1234567890, "unauth_role_id", "auth_role_id")
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

    def add_user_to_server(self, user_id:int) -> dict:
        """
        根據指定的user_id將使用者添加到ZeitFrei Discord主伺服器
        該使用者必須存在於至少一個擁有Qlipoth認證機器人的伺服器中

        使用方法:
        response = client.add_user_to_server(1234567890)
        print(response)
        """
        response = requests.post(f"{self.api_base_url}/add_user_to_server/{user_id}", headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to add user {user_id} to server: {response.text}")
        return response.json()