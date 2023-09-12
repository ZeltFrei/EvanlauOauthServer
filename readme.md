# ZeitFrei Discord OAuth API 函式庫使用指南

## 概覽

這是一個用於與ZeitFrei Discord OAuth授權API互動的Python函式庫。

## 安裝

```
pip install git+https://github.com/ZeltFrei/EvanlauOauthServer.git
```

## 初始化

首先，你需要創建一個`DiscordOAuthClient`的實例，並提供你的API金鑰。

```python
from oauth import DiscordOAuthClient

client = DiscordOAuthClient(api_key="YOUR_API_KEY_HERE")
```

## 方法

### 1. 取得使用者

使用`get_user`方法，你可以根據指定的user_id獲得使用者資訊。

```python
user = client.get_user(1234567890)
print(user)
```

### 2. 刪除使用者

使用`delete_user`方法，你可以根據指定的user_id刪除使用者。

```python
response = client.delete_user(1234567890)
print(response)
```

### 3. 添加伺服器資訊

使用`add_guild`方法，你可以添加伺服器的資訊，包括伺服器ID、未授權角色ID和已授權角色ID。

```python
response = client.add_guild(1234567890, "unauth_role_id", "auth_role_id")
print(response)
```

### 4. 將使用者添加到伺服器

使用`add_user_to_server`方法，你可以根據指定的user_id將使用者添加到伺服器中。

```python
response = client.add_user_to_server(1234567890)
print(response)
```

## 注意

- 這份函式庫中的API基底URL設定為`http://localhost:2094`，僅供ZeitFrei開發人員專用VPS內部使用。
