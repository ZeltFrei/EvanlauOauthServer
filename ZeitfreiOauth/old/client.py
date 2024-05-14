import requests

class DiscordOAuthClient:
    def __init__(self, api_key: str, api_base_url: str = "http://localhost:2094", client_id: int = 1092062648784404550):
        """
        載入Zeitfrei Discord OAuth函式庫\n
        參數
        ------
        api_key: :class:`str`
            請私訊Evanlau以獲得api_key
        api_base_url: :class:`str`
            伺服器位於.4的VPS\n
            若需要於其他VPS或其他位置使用該API，請在創建實例時定義`oauth.zeitfrei.tw`以修改伺服器API位置
        client_id: :class:`str`
            client_id預設為使用Qlipoth之應用程式帳號ID，非必要請不要更改
        """
        self.api_base_url:str = api_base_url
        self.api_key:str = api_key
        self.auth_url: str = f"https://discord.com/api/oauth2/authorize?client_id={client_id}&redirect_uri=https://oauth.zeitfrei.tw/callback&&response_type=code&scope=guilds%20email%20guilds.join%20identify"
        self.headers:dict = {
            "X-API-KEY": self.api_key
        }

    def get_user(self, user_id:int, ensure:bool = False) -> dict:
        """
        藉由使用ID查詢使用者已授權之資料並返回JSON資料\n
        參數
        ------
        user_id: :class:`int`
            要查詢的Discord使用者ID\n
        ensure: :class:`bool`
            (可選)向discord API查詢即時授權資訊\n
        返回
        ------
        :class:`dict`
            id: 使用者ID
            username: 使用者名稱
            discriminator: 使用者判別器
            access_token: 存取token
            refresh_token: 更新token
            expires_at: token到期時間
        """
        response = requests.get(f"{self.api_base_url}/user/{user_id}?ensure={ensure}", headers=self.headers)
        if response.status_code != 200:
            return None
        return response.json()
    
        
    def get_all_user(self) -> dict:
        """
        獲取所有已授權之使用者資料

        使用方法:
        user = client.get_all_user()
        print(user)
        """
        response = requests.get(f"{self.api_base_url}/all_user", headers=self.headers)
        if response.status_code != 200:
            return None
        return response.json()
    
    def get_auth_role_data(self,unauth_role_id:int,auth_role_id:int) -> list:
        """
        獲取特定之未授權/已授權身分組資料

        使用方法:
        role_data = client.get_guild_auth_role_data(unauth_role_id,auth_role_id)
        """
        response = requests.get(f"{self.api_base_url}/get_auth_role_data/{unauth_role_id}+{auth_role_id}", headers=self.headers)
        if response.status_code != 200 or len(response.json()) == 0:
            return None
        return response.json()
    
    def get_guild_auth_role_data(self, guild_id:int) -> list:
        """
        獲取伺服器登記之未授權/已授權身分組資料

        使用方法:
        guild_data = client.get_guild_auth_role_data("guild_id")
        """
        response = requests.get(f"{self.api_base_url}/get_guild_auth_role_data/{guild_id}", headers=self.headers)
        if response.status_code != 200 or len(response.json()) == 0:
            return None
        return response.json()

    def delete_user(self, user_id:int) -> dict:
        """
        使用`delete_user`方法，你可以根據指定的使用者ID刪除使用者
        這僅會將使用者從所有擁有此系統的伺服器中踢除該成員
        並將已授權的身分組撤回
        注意:使用者可以重新進行授權

        使用方法:
        response = client.delete_user(1234567890)
        print(response)
        """
        response = requests.delete(f"{self.api_base_url}/delete_user/{user_id}", headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to delete user {user_id}: {response.text}")
        return response.json()

    def add_guild(self, guild_id:int, unauth_role:int, auth_role:int,reauth_day:int) -> dict:
        """
        添加未認證/已認證身分組的設定資料，資料為伺服器ID、未授權身分組ID和已授權身分組ID。
        
        使用方法:
        response = client.add_guild(1234567890, "unauth_role_id", "auth_role_id")
        print(response)
        """
        data = {
            "guild_id": guild_id,
            "unauth_role": unauth_role,
            "auth_role": auth_role,
            "reauth_day": reauth_day
        }
        response = requests.post(f"{self.api_base_url}/add_guild", headers=self.headers, json=data)
        if response.status_code != 200:
            raise Exception(f"Failed to add guild data: {response.text}")
        return response.json()

    def delete_guild_data(self, guild_id:int, unauth_role:int, auth_role:int):
        """
        將指定的授權自動身份組資料刪除

        使用方法：
        response = client.delete_guild_data(1234567890, "unauth_role_id", "auth_role_id")
        print(response)
        """
        data = {
            "guild_id": guild_id,
            "unauth_role": unauth_role,
            "auth_role": auth_role
        }
        response = requests.delete(f"{self.api_base_url}/delete_guild_data", headers=self.headers, json=data)
        if response.status_code != 200:
            raise Exception(f"Failed to delete guild data: {response.text}")
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
        if response.status_code == 403:  # 從資料庫移除主動取消授權之使用者
            response = requests.delete(f"{self.api_base_url}/delete_user/{user_id}", headers=self.headers)
            raise Exception(f"使用者主動取消了授權")
        elif response.status_code == 204:
            raise Exception(f"使用者已加入伺服器")
        elif response.status_code != 200:
            raise Exception(f"發生未知的錯誤(代碼:{response.status_code})")
        else:
            return response.json()