## Zeitfrei OAuth授權 API 說明文件

本文件描述 Zeitfrei 用於機器人驗證的 REST API 使用方法，目前由 Evanlau 開發與維護。

### 連線方法
API 網址為 oauth.zeitfrei.uk ，向此端點發送請求以開始使用 API 。

### 安全金鑰

- 所有金鑰都是唯一的，每個在 Zeitfrei 旗下的機器人都需要申請金鑰。
- 機器人開發者使用了本 API 後，伺服器會留下 log 紀錄以利追查使用紀錄與陌生使用者。
- 所有 API 請求都需要在請求標頭中包含 `X-API-KEY` ，其值為 API 金鑰。

```
{
    X-API-KEY: YOUR_API_KEY
}
```

### API 端點


#### `/` (GET)

- **描述**: 將使用者重定向至 Discord OAuth2 授權頁面。
- **參數**: 無
- **連結**: [https://oauth.zeitfrei.uk](oauth.zeitfrei.uk)
- **用途**:
    - 萬用的網址，會重新導向到 `Qlipoth` 的 OAuth 授權頁面
    - 也可以用以下連結在 Discord 內直接完成授權：
      [Discord OAuth2 授權連結](https://discord.com/api/oauth2/authorize?client_id=1092062648784404550&redirect_uri=https://oauth.zeitfrei.uk/callback&&response_type=code&scope=guilds%20email%20guilds.join%20identify)


#### `/user/{user_id}` (GET)

- **描述**: 獲取指定使用者的資料。
- **參數**:
    - `user_id`: Discord 使用者 ID
    - `ensure` (選填, 預設為 False): 若設為 True，則會檢查 access token 是否過期，若過期則會刷新 access token。
- **回應**:
    - 200 OK：成功找到使用者資料，回傳 JSON 格式的使用者資料：
        ```json
        {
            'id': '使用者 ID',
            'username': '使用者名稱',
            'discriminator': '使用者標籤',
            'access_token': '存取權杖',
            'refresh_token': '刷新權杖',
            'expires_at': '權杖到期時間'
        }
        ```
    - 403 Forbidden: 
        - API 金鑰無效。
        - 發現使用者授權資料，但使用者已手動撤銷授權：此時會回傳訊息 `"message": "Found user authorization data, but the user has manually revoked authorization."`
    - 410 Gone: 使用者不存在，可能已被刪除。此時會回傳訊息 `"error": "User not found"`

#### `/all_user` (GET)

- **描述**: 獲取所有已授權使用者的資料。
- **參數**: 無
- **回應**:
    - 200 OK JSON 格式的所有使用者資料列表
    - 403 Forbidden API 金鑰無效

#### `/delete_user/{user_id}` (DELETE)

- **描述**: 刪除指定使用者的資料，並將使用者從所有已設定的伺服器中移除。
- **參數**:
    - `user_id`: Discord 使用者 ID
- **回應**:
    - 200 OK JSON 格式的訊息，表示使用者已成功刪除
    - 403 Forbidden API 金鑰無效

#### `/add_guild` (POST)

- **描述**: 新增伺服器的未驗證/已驗證身分組設定資料。
- **參數**:
    - JSON 格式的請求主體，包含以下欄位：
        ```json
        {
            'guild_id': '伺服器 ID',
            'unauth_role': '未驗證身分組 ID',
            'auth_role': '已驗證身分組 ID',
            'reauth_day': '重新驗證天數'
        }
        ```
- **回應**:
    - 200 OK JSON 格式的訊息，表示伺服器資料已成功新增
    - 403 Forbidden API 金鑰無效或身分組資料已存在

#### `/delete_guild_data` (DELETE)

- **描述**: 刪除伺服器的未驗證/已驗證身分組設定資料。
- **參數**:
    - JSON 格式的請求主體，包含以下欄位：
        ```json
        {
            'guild_id': '伺服器 ID',
            'unauth_role': '未驗證身分組 ID',
            'auth_role': '已驗證身分組 ID'
        }
        ```
- **回應**:
    - 200 OK JSON 格式的訊息，表示伺服器資料已成功刪除
    - 403 Forbidden API 金鑰無效或身分組資料不存在

#### `/add_user_to_server/{user_id}` (POST)

- **描述**: 將指定使用者加入所有已設定的伺服器，並設定對應的身分組。
- **參數**:
    - `user_id`: Discord 使用者 ID
- **回應**:
    - 200 OK JSON 格式的訊息，表示使用者已成功加入伺服器
    - 403 Forbidden API 金鑰無效

#### `/get_guild_auth_role_data/{guild_id}` (GET)

- **描述**: 獲取指定伺服器已設定的未驗證/已驗證身分組資料。
- **參數**:
    - `guild_id`: Discord 伺服器 ID
- **回應**:
    - 200 OK JSON 格式的伺服器身分組資料列表
    - 403 Forbidden API 金鑰無效

#### `/get_auth_role_data/{role_data}` (GET)

- **描述**: 獲取指定未驗證/已驗證身分組組合的伺服器設定資料。
- **參數**:
    - `role_data`: 未驗證身分組 ID 與已驗證身分組 ID，以 `+` 連接，例如 `1234567890+9876543210`
- **回應**:
    - 200 OK JSON 格式的伺服器設定資料
    - 403 Forbidden API 金鑰無效


### 錯誤代碼

- 403 Forbidden: API 金鑰無效
- 404 Not Found: 使用者不存在
