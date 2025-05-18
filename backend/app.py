# app.py
from dotenv import load_dotenv
import os
from flask import Flask, jsonify, send_from_directory, redirect, session, request, abort
import requests
from flask_cors import CORS
from pymongo import MongoClient
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token
from bson import ObjectId
from datetime import datetime

# ─── Load environment variables ────────────────────────────────────────────────
load_dotenv()

# ─── App & Middleware ─────────────────────────────────────────────────────────
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.urandom(24)
# allow only your dev frontend to use credentials
from flask_cors import CORS
CORS(
    app,
    supports_credentials=True,
    resources={r"/api/*": {"origins": "http://localhost:5173"}}
)
# CORS(app)
# allow the browser to send and receive cookies
# CORS(app, supports_credentials=True)


# ─── OIDC / Dex Setup ─────────────────────────────────────────────────────────
oauth = OAuth(app)
nonce = generate_token()

oauth.register(
    name=os.getenv("OIDC_CLIENT_NAME"),
    client_id=os.getenv("OIDC_CLIENT_ID"),
    client_secret=os.getenv("OIDC_CLIENT_SECRET"),
    authorization_endpoint="http://localhost:5556/auth",
    token_endpoint="http://dex:5556/token",
    jwks_uri="http://dex:5556/keys",
    userinfo_endpoint="http://dex:5556/userinfo",
    device_authorization_endpoint="http://dex:5556/device/code",
    client_kwargs={"scope": "openid email profile"},
)

# ─── MongoDB Connection ───────────────────────────────────────────────────────
MONGO_HOST = os.getenv("MONGO_HOST", "mongo")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USER = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
MONGO_PASS = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "rootpassword")

mongo_uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"
client = MongoClient(mongo_uri)
db = client["mydatabase"]
comments = db["comments"]

# ─── API ROUTES ────────────────────────────────────────────────────────────────
@app.route("/api/key")
def get_key():
    """Expose the NYT API key to the frontend."""
    return jsonify({"apiKey": os.getenv("NYT_API_KEY")})

@app.route("/api/user")
def get_user():
    user = session.get("user")
    if not user:
        return {}, 401
    return jsonify(user)

@app.route("/api/search")
def search_articles():
    """Proxy NYT article search through our backend."""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Missing 'q' parameter"}), 400

    # pull your key from env
    api_key = os.getenv("NYT_API_KEY")
    resp = requests.get(
        "https://api.nytimes.com/svc/search/v2/articlesearch.json",
        params={"q": q, "api-key": api_key},
        timeout=5
    )

    if resp.status_code != 200:
        return jsonify({
            "error": "NYT API error",
            "status": resp.status_code,
            "detail": resp.text[:200]
        }), resp.status_code

    return jsonify(resp.json())

@app.route("/api/comments", methods=["GET"])
def list_comments():
    """Return all comments."""
    docs = list(comments.find({}, {"_id": 0}))
    return jsonify(docs)

@app.route("/api/comments", methods=["POST"])  # new code
def add_comment():
    """Add a new comment."""
    data = request.get_json()
    result = comments.insert_one(data)
    return jsonify({"inserted_id": str(result.inserted_id)}), 201

# ─── NEW: Get all comments for one article ────────────────────────────────────
@app.route("/api/comments/<path:article_id>", methods=["GET"])
def get_comments(article_id):
    """Return all comments for a single article, sorted oldest→newest."""
    docs = list(
        comments.find(
        {"articleId": article_id},
        {"_id": 1, "user": 1, "text": 1, "createdAt": 1, "parentId": 1, "removed": 1}
        ).sort("createdAt", 1)
    )
    for d in docs:
        d["id"] = str(d.pop("_id"))
        d["createdAt"] = d["createdAt"].isoformat()
    return jsonify(docs)

# ─── NEW: Post a new comment to an article ────────────────────────────────────
@app.route("/api/comments/<path:article_id>", methods=["POST"])
def post_comment(article_id):
    """
    Body: { text: string, parentId?: string }
    Requires authenticated user (session['user']).
    """
    user = session.get("user")
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    body = request.get_json() or {}
    text = body.get("text", "").strip()
    parent_id = body.get("parentId")
    if not text:
        return jsonify({"error": "Empty comment"}), 400

    doc = {
        "articleId": article_id,
        "user": user["email"],
        "text": text,
        "createdAt": datetime.utcnow()
    }
    if parent_id:
        doc["parentId"] = parent_id
    res = comments.insert_one(doc)
    response_doc = {
        "id": str(res.inserted_id),
        "user": doc["user"],
        "text": doc["text"],
        "createdAt": doc["createdAt"].isoformat()
    }
    if parent_id:
        response_doc["parentId"] = parent_id
    return jsonify(response_doc), 201

# ─── NEW: Remove a comment ─────────────────────────────────────────────────────
@app.route("/api/comments/<comment_id>", methods=["PATCH"])
def remove_comment(comment_id):
    user = session.get("user")
    if not user or user.get("email") != "moderator@hw3.com":
        return jsonify({"error": "Moderator access required"}), 403
    # Update the comment: set text and removed flag
    result = comments.update_one(
        {"_id": ObjectId(comment_id)},
        {"$set": {"text": "COMMENT REMOVED BY MODERATOR!", "removed": True}}
    )
    if result.matched_count == 0:
        return jsonify({"error": "Comment not found"}), 404
    return jsonify({"success": True})

# ─── AUTH ROUTES ───────────────────────────────────────────────────────────────
@app.route("/login")
def login():
    session["nonce"] = nonce
    redirect_uri = "http://localhost:8000/authorize"
    # return oauth.flask_app.authorize_redirect(redirect_uri, nonce=nonce)
    client = oauth.create_client(os.getenv("OIDC_CLIENT_NAME"))
    return client.authorize_redirect(redirect_uri, nonce=nonce)

@app.route("/authorize")
def authorize():
    # token = oauth.flask_app.authorize_access_token()
    # user_info = oauth.flask_app.parse_id_token(token, nonce=session.get("nonce"))
    client = oauth.create_client(os.getenv("OIDC_CLIENT_NAME"))
    token = client.authorize_access_token()
    user_info = client.parse_id_token(token, nonce=session.get("nonce"))
    session["user"] = user_info
    # return redirect("/")
    return redirect("http://localhost:5173/")

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
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        debug=True
    )


# NEWISH BUT OLD

# from dotenv import load_dotenv
# from flask import Flask
# from pymongo import MongoClient

# load_dotenv()

# import os
# from flask import Flask, jsonify, send_from_directory, redirect, session
# from flask_cors import CORS
# from authlib.integrations.flask_client import OAuth
# from authlib.common.security import generate_token

# # ─── App & Middleware ─────────────────────────────────────────────────────────
# app = Flask(__name__, static_folder="static", template_folder="templates")
# app.secret_key = os.urandom(24)
# CORS(app)

# # ─── OIDC / Dex Setup ─────────────────────────────────────────────────────────
# oauth = OAuth(app)
# nonce = generate_token()

# oauth.register(
#     name=os.getenv("OIDC_CLIENT_NAME"),
#     client_id=os.getenv("OIDC_CLIENT_ID"),
#     client_secret=os.getenv("OIDC_CLIENT_SECRET"),
#     authorization_endpoint="http://dex:5556/auth",
#     token_endpoint="http://dex:5556/token",
#     jwks_uri="http://dex:5556/keys",
#     userinfo_endpoint="http://dex:5556/userinfo",
#     device_authorization_endpoint="http://dex:5556/device/code",
#     client_kwargs={"scope": "openid email profile"},
# )

# # ─── API ROUTES ────────────────────────────────────────────────────────────────
# @app.route("/api/key")
# def get_key():
#     """Expose the NYT API key to the frontend."""
#     return jsonify({"apiKey": os.getenv("NYT_API_KEY")})

# # ─── AUTH ROUTES ───────────────────────────────────────────────────────────────
# @app.route("/login")
# def login():
#     session["nonce"] = nonce
#     redirect_uri = "http://localhost:8000/authorize"
#     return oauth.flask_app.authorize_redirect(redirect_uri, nonce=nonce)

# @app.route("/authorize")
# def authorize():
#     token = oauth.flask_app.authorize_access_token()
#     user_info = oauth.flask_app.parse_id_token(token, nonce=session.get("nonce"))
#     session["user"] = user_info
#     return redirect("/")

# @app.route("/logout")
# def logout():
#     session.clear()
#     return redirect("/")

# # ─── FRONTEND & ASSET SERVING ──────────────────────────────────────────────────
# @app.route("/")
# def home():
#     user = session.get("user")
#     if user:
#         return (
#             f"<h2>Logged in as {user['email']}</h2>"
#             "<a href='/logout'>Logout</a>"
#         )
#     return '<a href="/login">Login with Dex</a>'

# @app.route("/<path:path>")
# def serve_frontend(path):
#     """Serve static assets or fallback to index.html for the SPA."""
#     full_path = os.path.join(app.static_folder, path)
#     if os.path.exists(full_path):
#         return send_from_directory(app.static_folder, path)
#     return send_from_directory(app.template_folder, "index.html")

# client = MongoClient('localhost', 27017)

# db = client.flask_db
# todos = db.todos

# # ─── RUN ───────────────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=True)


# OLDDDDDDDD

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