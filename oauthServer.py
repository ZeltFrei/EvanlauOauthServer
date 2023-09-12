from flask import Flask, redirect, request, jsonify, session, make_response
import sqlite3
import requests
import os 
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

@app.route('/')
def index():
    return redirect(
        f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&&response_type=code&scope=guilds%20email%20guilds.join%20identify")

@app.route('/callback')
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
def get_user(user_id):
    if not check_api_key(request):
        return jsonify({"error": "Invalid API key"}), 403

    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        user = cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if user:
            return jsonify({
                'id': user[0],
                'username': user[1],
                'discriminator': user[2],
                'access_token': user[3],
                'refresh_token': user[4]
            })
        else:
            return make_response(jsonify({"error": "User not found"}), 404)

@app.route('/delete_user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    if not check_api_key(request):
        return jsonify({"error": "Invalid API key"}), 403

    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        guilds = cursor.execute("SELECT * FROM guild").fetchall()
        for guild in guilds:
            guild_id = guild[0]
            response = requests.delete(f"https://discord.com/api/guilds/{guild_id}/members/{user_id}", headers={
                'Authorization': f"Bot {BOT_TOKEN}"
            })
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

    return jsonify({"message": f"User {user_id} deleted successfully"})

@app.route('/add_guild', methods=['POST'])
def add_guild():
    if not check_api_key(request):
        return jsonify({"error": "Invalid API key"}), 403
    
    data = request.json
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO guild (guild_id, unauth_role_id, auth_role_id) VALUES (?, ?, ?)",
                       (data['guild_id'], data['unauth_role'], data['auth_role']))
        conn.commit()
    return jsonify({"message": "Guild data added successfully!"})

@app.route('/add_user_to_server/<user_id>', methods=['POST'])
def call_add_user(user_id):
    if not check_api_key(request):
        return jsonify({"ERROR": "Invalid API key"}), 403
    response = add_user_to_server(user_id=user_id)
    return jsonify({"status": response.text}), response.status_code

def check_api_key(request):
    provided_key = request.headers.get('X-API-KEY')
    return provided_key == API_KEY

def save_user_to_db(user, token_info):
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT,
                discriminator TEXT,
                access_token TEXT,
                refresh_token TEXT
            )
        """)
        cursor.execute(
            "INSERT OR REPLACE INTO users (id, username, discriminator, access_token, refresh_token) VALUES (?, ?, ?, ?, ?)",
            (user['id'], user['username'], user['discriminator'], token_info['access_token'], token_info['refresh_token'])
        )
        conn.commit()

def add_user_to_server(user_id:int):
    with sqlite3.connect("users.db") as conn:
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

    #response = requests.put(f"https://discord.com/api/guilds/969732954572075008/members/{user_id}", headers=headers, json=data) 正式程式
    response = requests.put(f"https://discord.com/api/guilds/1090311734050426960/members/{user_id}", headers=headers, json=data) #測試用
    
    if response.status_code == 201:
        print(f"{user_data[1]}已加入伺服器")
    for data in guild_data:
        guild_id = data[0]
        auth_role_id = data[2]
        requests.put(f"https://discord.com/api/guilds/{guild_id}/members/{user_id}/roles/{auth_role_id}", headers=headers)
    return response

if __name__ == "__main__":
    app.run(port=2094)
