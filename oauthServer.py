import sqlite3, requests, os, hmac, datetime, asyncio, logging, time, zipfile
from logging import WARN, WARNING, ERROR, DEBUG, INFO
from aiohttp import web, ClientSession
from dotenv import load_dotenv
from discord_webhook import DiscordWebhook, DiscordEmbed

load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_WEBHOOK_URL = os.getenv("LOG_WEBHOOK_URL")
REDIRECT_URI = 'https://oauth.zeitfrei.tw/callback'
DATABASE = "users.db"
AUTH_BOTS_DATABASE = "bot.db"

logging.basicConfig(filename='oauth_server.log', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
webhook = DiscordWebhook(url=LOG_WEBHOOK_URL)

def logger(request:web.Request, bot_name:str, level:logging = INFO):
    method = request.method
    path = request.path
    log_message = f"[{bot_name}] - {method} {path}"
    logging.log(level=level, msg=log_message)

async def logger_updater():
    log_file_path = 'oauth_server.log'
    server_log_dir = './serverLog'
    while True:
        current_time = datetime.datetime.now().astimezone()
        hour = current_time.hour
        minute = current_time.minute
        second = current_time.second
        set_time = 86400
        wait_time = (set_time - (hour * 3600 + minute * 60 + second) + 86400) % 86400
        print(f"換日剩餘時間 : {wait_time}")
        await asyncio.sleep(wait_time)
        date_string = datetime.datetime.now().strftime('%Y-%m-%d')
        with zipfile.ZipFile(f'{server_log_dir}/log_{date_string}.zip', 'w') as zipf:
            zipf.write(log_file_path, arcname=os.path.join(server_log_dir, 'oauth_server.log'))
        open(log_file_path, 'w').close()
        await asyncio.sleep(1)

def set_route():
    app.router.add_get('/', index)
    app.router.add_get('/callback', callback)
    app.router.add_get('/close', close)
    app.router.add_get('/web_auth_error', web_auth_error)
    app.router.add_get('/user/{user_id}', get_user)
    app.router.add_get('/all_user', get_all_user)
    app.router.add_delete('/delete_user/{user_id}', delete_user)
    app.router.add_post('/add_guild', add_guild)
    app.router.add_delete('/delete_guild_data', delete_guild_data)
    app.router.add_post('/add_user_to_server/{user_id}', add_user_to_server)
    app.router.add_get('/get_guild_auth_role_data/{guild_id}', get_guild_auth_role_data)
    app.router.add_get('/get_auth_role_data/{role_data}', get_auth_role_data)

def check_api_key(request): #檢查API_KEY是否符合
    provided_key = request.headers.get('X-API-KEY')
    with sqlite3.connect(AUTH_BOTS_DATABASE) as conn:
        cursor = conn.cursor()
        bot = cursor.execute("SELECT * FROM bot WHERE botKey = ?", (provided_key,)).fetchone()
        if bot:
            bot_name = bot[0]
            api_key = bot[2]
            logger(request, bot_name)
            return hmac.compare_digest(provided_key, api_key)
        else:
            bot_name = "Anonymous"
            logger(request, bot_name, WARN)
            return False

async def index(request):
    return web.HTTPFound(
        location=f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&&response_type=code&scope=guilds%20email%20guilds.join%20identify"
    )

async def callback(request):
    start_time = time.time()
    logger(request,bot_name="Oauth Callback")
    code = request.query.get('code')
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'scope': 'identify'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    async with ClientSession() as session:
        #print(f"1. 執行時間: {time.time() - start_time}")
        async with session.post('https://discord.com/api/oauth2/token', data=data, headers=headers) as response:
            try:
                #print(f"2. 執行時間: {time.time() - start_time}")
                response.raise_for_status()

                token_info = await response.json()
                token = token_info['access_token']
                async with session.get('https://discord.com/api/users/@me', headers={
                    'Authorization': f"Bearer {token}"
                }) as response:
                    #print(f"3. 執行時間: {time.time() - start_time}")
                    response.raise_for_status()
                    user = await response.json()
            except Exception as e:
                logger(request = request, bot_name = "Oauth Callback", level = WARN)
                raise web.HTTPFound('/web_auth_error')

    await save_user_to_db(user, token_info)

    #print(f"4. 執行時間: {time.time() - start_time}")

    await AddUserToServer(user_id=user['id'],start_time = start_time)

    #print(f"8. 執行時間: {time.time() - start_time}")
    #print(f"{user['id']} 已成功授權")
    await send_webhook_msg(user=user)    

    raise web.HTTPFound('/close')

async def send_webhook_msg(user:dict):
    user_id = user['id']
    email = user['email']
    user_name = user['username']
    user_avatar = "[{}](https://cdn.discordapp.com/avatars/{}/{}.png?size=480&quot)".format(user['avatar'], user_id, user['avatar']) if user['avatar'] else "無"
    user_banner = "[{}](https://cdn.discordapp.com/banners/{}/{}.png?size=480&quot)".format(user['banner'], user_id, user['banner']) if user['banner'] else "無"
    user_global_id = user['global_name'] if user['global_name'] else user['id']
    embed = ZeitfreiEmbedMsg(title="使用者驗證成功")
    embed.add_embed_field(name="帳號", value=f"<@{user_id}>")
    embed.add_embed_field(name="使用者名稱", value=user_name)
    embed.add_embed_field(name="帳號名稱", value=user_global_id)
    embed.add_embed_field(name="使用者ID", value=user_id)
    embed.add_embed_field(name="電子郵件", value=email)
    embed.add_embed_field(name="頭像",value=user_avatar, inline=False)
    embed.add_embed_field(name="橫幅", value=user_banner)
    embed.set_thumbnail("https://cdn.discordapp.com/avatars/{}/{}.png?size=480&quot".format(user_id, user['avatar']))
    webhook.add_embed(embed)
    webhook.execute()

async def close(request):
    return web.Response(text='''
        <html>
            <body>
                <script>
                    alert("授權完成! 你現在可以返回Discord.");
                    window.opener=null;
                    window.close();
                </script>
            </body>
        </html>
        '''
        , content_type='text/html')

async def web_auth_error(request):
    return web.Response(text='''
        <html>
            <body>
                <script>
                    alert("授權失敗 授權過程中出現錯誤");
                    window.opener=null;
                    window.close();
                </script>
            </body>
        </html>
        '''
        , content_type='text/html')

async def get_user(request):
    user_id = request.match_info['user_id']
    ensure = bool(request.query.get('ensure', 'False') == 'True')
    if not check_api_key(request):
        return web.json_response({"error": "Invalid API key"}, status=403)
    
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        user = cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if user: 
            try:
                if ensure:
                    access_token = user[3]
                    expires_at = user[5]
                    if datetime.datetime.now() >= datetime.datetime.strptime(expires_at,"%Y-%m-%d %H:%M:%S.%f"):
                        await refresh_token_if_expired(user_id)
                    async with ClientSession() as session:
                        async with session.get('https://discord.com/api/users/@me', headers={
                            'Authorization': f"Bearer {access_token}"
                        }) as response:
                            response.raise_for_status()
                else:
                    await refresh_token_if_expired(user_id)
            except Exception as e:
                await delete_user(user_id)
                return web.json_response({"message": "Found user authorization data, but the user has manually revoked authorization."}, status=403)

            return web.json_response({
                'id': user[0],
                'username': user[1],
                'discriminator': user[2],
                'access_token': user[3],
                'refresh_token': user[4],
                'expires_at': user[5]
            })
        else:
            return web.json_response({"error": "User not found"}, status=410)

async def get_all_user(request):
    if not check_api_key(request):
        return web.json_response({"error": "Invalid API key"}, status=403)

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        users = cursor.execute("SELECT * FROM users").fetchall()
        return web.json_response(users, status=200)

async def delete_user(request):
#根據指定的使用者ID刪除使用者
#這僅會將使用者從所有擁有此系統的伺服器中踢除該成員
#並將已授權的身分組撤回
#使用者可以重新進行授權
    user_id = request.match_info['user_id']
    if not check_api_key(request):
        return web.json_response({"error": "Invalid API key"}, status=403)
    await execute_user_deletion(user_id)
    return web.json_response({"message": f"User {user_id} deleted successfully"})

async def execute_user_deletion(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        guilds = cursor.execute("SELECT * FROM guild").fetchall()
        headers = {
            'Authorization': f"Bot {BOT_TOKEN}"
        }
        for guild in guilds:
            guild_id = guild[0]
            unauth_role_id = guild[1]
            auth_role_id = guild[2]
            async with ClientSession() as session:
                #await session.delete(f"https://discord.com/api/guilds/{guild_id}/members/{user_id}", headers=headers)
                await session.delete(f"https://discord.com/api/guilds/{guild_id}/members/{user_id}/roles/{auth_role_id}", headers=headers)
                if guild_id != unauth_role_id: #判斷是否為everyone身分組
                    await session.put(f"https://discord.com/api/guilds/{guild_id}/members/{user_id}/roles/{unauth_role_id}", headers=headers)
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()

async def add_guild(request):
#新增認證伺服器未驗證/已驗證設定資料
    if not check_api_key(request):
        return web.json_response({"error": "Invalid API key"}, status=403)

    data = await request.json()
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        if cursor.execute(f"SELECT * FROM guild WHERE guild_id = ? AND unauth_role_id = ? AND auth_role_id = ?",
                            (data['guild_id'], data['unauth_role'], data['auth_role'],)).fetchone() is not None:
            return web.json_response({"ERROR": "Role data already exists."}, status=403)

        cursor.execute("INSERT OR REPLACE INTO guild (guild_id, unauth_role_id, auth_role_id, reauth_day) VALUES (?, ?, ?, ?)",
                    (data['guild_id'], data['unauth_role'], data['auth_role'], data['reauth_day']))
        conn.commit()

    return web.json_response({"message": "Guild data added successfully!"})

async def delete_guild_data(request):
    if not check_api_key(request):
        return web.json_response({"error": "Invalid API key"}, status=403)

    data = await request.json()
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        if cursor.execute(f"SELECT * FROM guild WHERE guild_id = ? AND unauth_role_id = ? AND auth_role_id = ?",
                            (data['guild_id'], data['unauth_role'], data['auth_role'],)).fetchone() is None:
            return web.json_response({"ERROR": "Role data not exists."}, status=403)

        cursor.execute("DELETE FROM guild WHERE guild_id = ? AND unauth_role_id = ? AND auth_role_id = ?",
                    (data['guild_id'], data['unauth_role'], data['auth_role']))
        conn.commit()

    return web.json_response({"message": "Guild data delete successfully!"})

async def add_user_to_server(request):
    user_id = request.match_info['user_id']
    if not check_api_key(request):
        return web.json_response({"ERROR": "Invalid API key"}), 403
    response = await AddUserToServer(user_id=user_id)
    return web.json_response({"status": response.text}), response.status_code

async def get_guild_auth_role_data(request): #獲取伺服器登記之未授權/已授權身分組資料
    guild_id = request.match_info['guild_id']
    if not check_api_key(request):
        return web.json_response({"ERROR": "Invalid API key"}), 403
    
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        data_list = cursor.execute("SELECT * FROM guild WHERE guild_id = ?", (guild_id,)).fetchall()
        output = []
        for data in data_list:
            temp_list = {
                "guild_id": data[0],
                "unauth_role_id": data[1],
                "auth_role_id": data[2],
                "reauth_day": data[3]
            }
            output.append(temp_list)
    return web.json_response(output)

async def get_auth_role_data(request):
    role_data = request.match_info['role_data']
    if not check_api_key(request):
        return web.json_response({"ERROR": "Invalid API key"}), 403
    
    unauth_role_id, auth_role_id = role_data.split("+")
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        data = cursor.execute("SELECT * FROM guild WHERE unauth_role_id = ? AND auth_role_id = ?", (unauth_role_id, auth_role_id)).fetchone()
    return web.json_response(data)

async def save_user_to_db(user, token_info): #儲存使用者授權資料
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT,
                discriminator TEXT,
                access_token TEXT,
                refresh_token TEXT,
                expires_at TIMESTAMP
            )
        """)
        # 計算 access_token 的過期時間
        expires_in = token_info.get('expires_in', 0)
        expires_at = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
        
        cursor.execute(
            "INSERT OR REPLACE INTO users (id, username, discriminator, access_token, refresh_token, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user['id'], user['username'], user['discriminator'], token_info['access_token'], token_info['refresh_token'], expires_at)
        )
        conn.commit()

async def refresh_token_if_expired(user_id): #將過期的access_token刷新
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        user_data = cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user_data:
            return
        
        expires_at = user_data[5]
        # 檢查 access_token 是否已過期
        if datetime.datetime.now() >= datetime.datetime.strptime(expires_at,"%Y-%m-%d %H:%M:%S.%f"):
            data = {
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'grant_type': 'refresh_token',
                'refresh_token': user_data[4]
            }
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            response = requests.post('https://discord.com/api/oauth2/token', data=data, headers=headers)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 400:
                    embed = ZeitfreiEmbedMsg(title="使用者主動移除了授權", description=f"- 帳號: <@{user_id}>")
                    webhook.add_embed(embed)
                    webhook.execute()
                    raise "Authorization data error: The user has manually revoked authorization "
                raise e
            new_token_info = response.json()

            # 更新資料庫中的 tokens 並計算新的過期時間
            expires_in = new_token_info.get('expires_in', 0)
            expires_at = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
            
            cursor.execute(
                "UPDATE users SET access_token=?, refresh_token=?, expires_at=? WHERE id=?",
                (new_token_info['access_token'], new_token_info['refresh_token'], expires_at, user_id)
            )
            conn.commit()

async def AddUserToServer(user_id:int, start_time): #根據使用者ID將使用者加入Zeitfrei主伺服器中
    try:
        await refresh_token_if_expired(user_id)
    except Exception as e:
        return web.json_response({"error": e}, status=403)

    #print(f"5. 執行時間: {time.time() - start_time}")

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        user_data = cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        guild_data = cursor.execute("SELECT * FROM guild").fetchall()

    headers = {
        'Authorization': f"Bot {BOT_TOKEN}",
        'Content-Type': 'application/json'
    }

    data = {
        'access_token': user_data[3]
    }

    response = requests.put(f"https://discord.com/api/guilds/308120017201922048/members/{user_id}", headers=headers, json=data)
    
    #print(f"6. 執行時間: {time.time() - start_time}")

    if response.status_code == 201:
        print(f"{user_data[1]}已加入伺服器")
    for data in guild_data:
        guild_id = data[0]
        unauth_role_id = data[1]
        auth_role_id = data[2]
        requests.put(f"https://discord.com/api/guilds/{guild_id}/members/{user_id}/roles/{auth_role_id}", headers=headers)
        if guild_id != unauth_role_id: #判斷是否為everyone身分組
            requests.delete(f"https://discord.com/api/guilds/{guild_id}/members/{user_id}/roles/{unauth_role_id}", headers=headers)

    #print(f"7. 執行時間: {time.time() - start_time}")

    return response

#==================Zeitfrei專用 Webhook Embed 訊息==================
class ZeitfreiEmbedMsg(DiscordEmbed):
    def __init__(self, title:str = None, description:str = None):
        super().__init__(title=title, description=description, color="2b2d31")
        self.set_footer(text=f"ZeiFrei × Qlipoth bot ∣ 社群安全系統",icon_url="https://cdn.discordapp.com/attachments/1050082973891956799/1052222704582922301/BirthUploadPic.png")
        self.set_timestamp()

async def run_app():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 2094)
    await site.start()
    asyncio.create_task(logger_updater())

if __name__ == "__main__":
    app = web.Application()
    app.secret_key = os.urandom(20)
    app['SESSION_COOKIE_NAME'] = 'discord-login-session'
    set_route()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_app())
    loop.run_forever()