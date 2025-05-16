# app.py
from dotenv import load_dotenv
load_dotenv()

import os
from flask import Flask, jsonify, send_from_directory, redirect, session
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token

# ─── App & Middleware ─────────────────────────────────────────────────────────
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.urandom(24)
CORS(app)

# ─── OIDC / Dex Setup ─────────────────────────────────────────────────────────
oauth = OAuth(app)
nonce = generate_token()

oauth.register(
    name=os.getenv("OIDC_CLIENT_NAME"),
    client_id=os.getenv("OIDC_CLIENT_ID"),
    client_secret=os.getenv("OIDC_CLIENT_SECRET"),
    authorization_endpoint="http://dex:5556/auth",
    token_endpoint="http://dex:5556/token",
    jwks_uri="http://dex:5556/keys",
    userinfo_endpoint="http://dex:5556/userinfo",
    device_authorization_endpoint="http://dex:5556/device/code",
    client_kwargs={"scope": "openid email profile"},
)

# ─── API ROUTES ────────────────────────────────────────────────────────────────
@app.route("/api/key")
def get_key():
    """Expose the NYT API key to the frontend."""
    return jsonify({"apiKey": os.getenv("NYT_API_KEY")})

# ─── AUTH ROUTES ───────────────────────────────────────────────────────────────
@app.route("/login")
def login():
    session["nonce"] = nonce
    redirect_uri = "http://localhost:8000/authorize"
    return oauth.flask_app.authorize_redirect(redirect_uri, nonce=nonce)

@app.route("/authorize")
def authorize():
    token = oauth.flask_app.authorize_access_token()
    user_info = oauth.flask_app.parse_id_token(token, nonce=session.get("nonce"))
    session["user"] = user_info
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ─── FRONTEND & ASSET SERVING ──────────────────────────────────────────────────
@app.route("/")
def home():
    user = session.get("user")
    if user:
        return (
            f"<h2>Logged in as {user['email']}</h2>"
            "<a href='/logout'>Logout</a>"
        )
    return '<a href="/login">Login with Dex</a>'

@app.route("/<path:path>")
def serve_frontend(path):
    """Serve static assets or fallback to index.html for the SPA."""
    full_path = os.path.join(app.static_folder, path)
    if os.path.exists(full_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.template_folder, "index.html")

# ─── RUN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=True)


# from flask import Flask, redirect, url_for, session
# from authlib.integrations.flask_client import OAuth
# from authlib.common.security import generate_token
# import os

# app = Flask(__name__)
# app.secret_key = os.urandom(24)


# oauth = OAuth(app)

# nonce = generate_token()


# oauth.register(
#     name=os.getenv('OIDC_CLIENT_NAME'),
#     client_id=os.getenv('OIDC_CLIENT_ID'),
#     client_secret=os.getenv('OIDC_CLIENT_SECRET'),
#     #server_metadata_url='http://dex:5556/.well-known/openid-configuration',
#     authorization_endpoint="http://localhost:5556/auth",
#     token_endpoint="http://dex:5556/token",
#     jwks_uri="http://dex:5556/keys",
#     userinfo_endpoint="http://dex:5556/userinfo",
#     device_authorization_endpoint="http://dex:5556/device/code",
#     client_kwargs={'scope': 'openid email profile'}
# )

# @app.route('/')
# def home():
#     user = session.get('user')
#     if user:
#         return f"<h2>Logged in as {user['email']}</h2><a href='/logout'>Logout</a>"
#     return '<a href="/login">Login with Dex</a>'

# @app.route('/login')
# def login():
#     session['nonce'] = nonce
#     redirect_uri = 'http://localhost:8000/authorize'
#     return oauth.flask_app.authorize_redirect(redirect_uri, nonce=nonce)

# @app.route('/authorize')
# def authorize():
#     token = oauth.flask_app.authorize_access_token()
#     nonce = session.get('nonce')

#     user_info = oauth.flask_app.parse_id_token(token, nonce=nonce)  # or use .get('userinfo').json()
#     session['user'] = user_info
#     return redirect('/')

# @app.route('/logout')
# def logout():
#     session.clear()
#     return redirect('/')

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=8000)
