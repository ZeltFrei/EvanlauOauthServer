# ZeitFrei Discord OAuth API 函式庫使用指南

## 概覽

這是一個用於與ZeitFrei Discord OAuth授權API互動的Python函式庫。

## 安裝

```
pip install git+https://github.com/ZeltFrei/EvanlauOauthServer.git
```

## 更新

```
pip install -U git+https://github.com/ZeltFrei/EvanlauOauthServer.git
```

## 初始化

首先，你需要創建一個`DiscordOAuthClient`的實例，並提供你的API金鑰。

```python
from ZeitfreiOauth import DiscordOAuthClient

client = DiscordOAuthClient(api_key="YOUR_API_KEY_HERE")
```

若需要於其他VPS或其他位置使用該API，請在創建實例時定義`api_base_url`以修改伺服器API位置
```python
client = DiscordOAuthClient(api_key="YOUR_API_KEY_HERE",api_base_url="YOUR_API_BASE_URL")
```

## 方法

### 1. 取得使用者

使用`get_user`方法，你可以根據指定的使用者ID獲得使用者資訊，若尋找失敗會返回None。

```python
user = client.get_user(1234567890)
print(user)
```

### 2. 取得伺服器登記之身分組資料

使用`get_guild_auth_role_data`方法，你可以根據指定的伺服器ID獲得未授權/已授權的身分組ID，若尋找失敗會返回None。

```python
guild_data = client.get_guild_auth_role_data(1234567890)
print(guild_data)
```

### 3. 刪除使用者

使用`delete_user`方法，你可以根據指定的使用者ID刪除使用者。
這僅會將使用者從所有擁有此系統的伺服器中踢除該成員，使用者可以重新進行授權。

```python
response = client.delete_user(1234567890)
print(response)
```

### 4. 添加伺服器認證身分組資訊

使用`add_guild`方法，你可以添加未認證/已認證身分組的設定資料，資料為伺服器ID、未授權身分組ID和已授權身分組ID。

```python
response = client.add_guild(1234567890, "unauth_role_id", "auth_role_id")
print(response)
```

### 5. 將使用者添加到伺服器

使用`add_user_to_server`方法，你可以根據指定的user_id將使用者添加到ZeitFrei Discord主伺服器中。
該使用者必須存在於至少一個擁有Qlipoth認證機器人的伺服器中。

```python
response = client.add_user_to_server(1234567890)
print(response)
```

## 注意

- 這份函式庫中的API基底URL設定為`http://localhost:2094`，僅供ZeitFrei開發人員專用VPS內部使用。
