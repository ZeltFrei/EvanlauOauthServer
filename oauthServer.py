import sqlite3, requests, os, hmac, datetime
from flask import Flask, redirect, request, jsonify, session, make_response, current_app
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(20)
app.config['SESSION_COOKIE_NAME'] = 'discord-login-session'

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
REDIRECT_URI = 'https://oauth.zeitfrei.tw/callback'
DATABASE = "users.db"

@app.route('/')
#將預設網址重新導向到discord授權頁面
def index():
    return redirect(
        f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&&response_type=code&scope=guilds%20email%20guilds.join%20identify")

@app.route('/callback')
#接收discord API返回資料
def callback():
    code = request.args.get('code')
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
    response = requests.post('https://discord.com/api/oauth2/token', data=data, headers=headers)
    response.raise_for_status()
    session['token'] = response.json()
    token = session['token']['access_token']
    response = requests.get('https://discord.com/api/users/@me', headers={
        'Authorization': f"Bearer {token}"
    })
    response.raise_for_status()
    user = response.json()

    save_user_to_db(user, session['token'])    
    add_user_to_server(user_id=user['id'])
    current_app.logger.info(f"User {user['id']} authenticated successfully.")
    return redirect('/close')

@app.route('/close')
def close():
    return '''
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

@app.route('/user/<user_id>')
#使用者資料查詢
def get_user(user_id):
    if not check_api_key(request):
        return jsonify({"error": "Invalid API key"}), 403

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        user = cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if user:
            return jsonify({
                'id': user[0],
                'username': user[1],
                'discriminator': user[2],
                'access_token': user[3],
                'refresh_token': user[4],
                'expires_at': user[5]
            })
        else:
            return make_response(jsonify({"error": "User not found"}), 404)

@app.route('/delete_user/<user_id>', methods=['DELETE']) 
#根據指定的使用者ID刪除使用者
#這僅會將使用者從所有擁有此系統的伺服器中踢除該成員
#並將已授權的身分組撤回
#使用者可以重新進行授權
def delete_user(user_id):
    if not check_api_key(request):
        return jsonify({"error": "Invalid API key"}), 403

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
            requests.delete(f"https://discord.com/api/guilds/{guild_id}/members/{user_id}", headers=headers)
            requests.delete(f"https://discord.com/api/guilds/{guild_id}/members/{user_id}/roles/{auth_role_id}", headers=headers)
            if guild_id != unauth_role_id: #判斷是否為everyone身分組
                requests.put(f"https://discord.com/api/guilds/{guild_id}/members/{user_id}/roles/{unauth_role_id}", headers=headers)
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

    current_app.logger.info(f"User {user_id} deleted successfully.")
    return jsonify({"message": f"User {user_id} deleted successfully"})

@app.route('/add_guild', methods=['POST']) 
#新增認證伺服器未驗證/已驗證設定資料
def add_guild():
    if not check_api_key(request):
        return jsonify({"error": "Invalid API key"}), 403
    
    data = request.json
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        #檢查是否有重複資料
        if cursor.execute(f"SELECT * FROM guild WHERE guild_id = ? AND unauth_role_id = ? AND auth_role_id = ?",(data['guild_id'],data['unauth_role'],data['auth_role'],)).fetchone() is not None:
            return jsonify({"ERROR":"Role data already exists."}),403

        cursor.execute("INSERT OR REPLACE INTO guild (guild_id, unauth_role_id, auth_role_id) VALUES (?, ?, ?)",
                       (data['guild_id'], data['unauth_role'], data['auth_role']))
        conn.commit()
    
    current_app.logger.info(f"Guild {data['guild_id']} added successfully.")
    return jsonify({"message": "Guild data added successfully!"})

@app.route('/add_user_to_server/<user_id>', methods=['POST']) 
#以使用者ID新增使用者到Zeitfrei主伺服器中
def call_add_user(user_id):
    if not check_api_key(request):
        return jsonify({"ERROR": "Invalid API key"}), 403
    response = add_user_to_server(user_id=user_id)
    current_app.logger.info(f"User {user_id} join successfully.")
    return jsonify({"status": response.text}), response.status_code

@app.route('/get_guild_auth_role_data/<guild_id>')
#獲取伺服器登記之未授權/已授權身分組資料
def get_guild_auth_role_data(guild_id):
    if not check_api_key(request):
        return jsonify({"ERROR": "Invalid API key"}), 403
    
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        data_list = cursor.execute("SELECT * FROM guild WHERE guild_id = ?",(guild_id,)).fetchall()
        output = {}
        for data in enumerate(data_list,0):
            temp_list = {
                "guild_id": data[1][0],
                "unauth_role_id": data[1][1],
                "auth_role_id": data[1][2]
            }
            output.update({data[0]:temp_list})
        return jsonify(output)

def check_api_key(request): #檢查API_KEY是否符合
    provided_key = request.headers.get('X-API-KEY')
    return hmac.compare_digest(provided_key, API_KEY)

def save_user_to_db(user, token_info): #儲存使用者授權資料
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

def refresh_token_if_expired(user_id): #將過期的access_token刷新
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        user_data = cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        
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
            response.raise_for_status()
            new_token_info = response.json()

            # 更新資料庫中的 tokens 並計算新的過期時間
            expires_in = new_token_info.get('expires_in', 0)
            expires_at = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
            
            cursor.execute(
                "UPDATE users SET access_token=?, refresh_token=?, expires_at=? WHERE id=?",
                (new_token_info['access_token'], new_token_info['refresh_token'], expires_at, user_id)
            )
            conn.commit()

def add_user_to_server(user_id:int): #根據使用者ID將使用者加入伺服器中
    refresh_token_if_expired(user_id)
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

    response = requests.put(f"https://discord.com/api/guilds/969732954572075008/members/{user_id}", headers=headers, json=data) #正式程式
    #response = requests.put(f"https://discord.com/api/guilds/1090311734050426960/members/{user_id}", headers=headers, json=data) #測試用
    
    if response.status_code == 201:
        print(f"{user_data[1]}已加入伺服器")
    for data in guild_data:
        guild_id = data[0]
        unauth_role_id = data[1]
        auth_role_id = data[2]
        requests.put(f"https://discord.com/api/guilds/{guild_id}/members/{user_id}/roles/{auth_role_id}", headers=headers)
        if guild_id != unauth_role_id: #判斷是否為everyone身分組
            requests.delete(f"https://discord.com/api/guilds/{guild_id}/members/{user_id}/roles/{unauth_role_id}", headers=headers)
    return response

if __name__ == "__main__":
    app.run(port=2094)
