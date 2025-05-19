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

# loading the environment variables
load_dotenv()

# APP AND MIDDLEWARE
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.urandom(24)
# allow only your dev frontend to use credentials
from flask_cors import CORS
CORS(
    app,
    supports_credentials=True,
    resources={r"/api/*": {"origins": "http://localhost:5173"}}
)
# CORS(app) allow the browser to send and receive cookies
# CORS(app, supports_credentials=True)


# OIDC / DEX SETUP
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

# MONGO CONNECTION
MONGO_HOST = os.getenv("MONGO_HOST", "mongo")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USER = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
MONGO_PASS = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "rootpassword")

mongo_uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"
client = MongoClient(mongo_uri)
db = client["mydatabase"]
comments = db["comments"]

# API ROUTES
@app.route("/api/key")
def get_key():
    return jsonify({"apiKey": os.getenv("NYT_API_KEY")}) # expose the NYT API key to the frontend

@app.route("/api/user")
def get_user():
    user = session.get("user")
    if not user:
        return {}, 401
    return jsonify(user)

@app.route("/api/search")
def search_articles():
    # search NYT articles
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Missing 'q' parameter"}), 400

    # pull our key from env
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
    # returning all the comments
    docs = list(comments.find({}, {"_id": 0}))
    return jsonify(docs)

@app.route("/api/comments", methods=["POST"])  # new code
def add_comment():
    # adding a new comment
    data = request.get_json()
    result = comments.insert_one(data)
    return jsonify({"inserted_id": str(result.inserted_id)}), 201

# RETRIEVING COMMENTS PER ARTICLE
@app.route("/api/comments/<path:article_id>", methods=["GET"])
def get_comments(article_id):
    # returning comments for 1 article, and sorting them oldest -> newest
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

# POSTING NEW COMMENT
@app.route("/api/comments/<path:article_id>", methods=["POST"])
def post_comment(article_id):
    # whoever is posting a comment needs to be logged in aka authenticated
    user = session.get("user")
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    body = request.get_json() or {}
    text = body.get("text", "").strip()
    parent_id = body.get("parentId")
    if not text:
        return jsonify({"error": "Empty comment"}), 400
    # creating the comment
    doc = {
        "articleId": article_id,
        "user": user["email"],
        "text": text,
        "createdAt": datetime.utcnow()
    }
    # if the comment has a parent, add the parentId to the comment
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

# REMOVING A COMMENT
@app.route("/api/comments/<comment_id>", methods=["PATCH"])
def remove_comment(comment_id):
    user = session.get("user")
    if not user or user.get("email") != "moderator@hw3.com":
        return jsonify({"error": "Moderator access required"}), 403
    # updating the comment to set the removed flag to true
    result = comments.update_one(
        {"_id": ObjectId(comment_id)},
        {"$set": {"removed": True}}
    )
    if result.matched_count == 0:
        return jsonify({"error": "Comment not found"}), 404
    return jsonify({"success": True})

# AUTH ROUTES
@app.route("/login")
def login():
    session["nonce"] = nonce
    redirect_uri = "http://localhost:8000/authorize"
    client = oauth.create_client(os.getenv("OIDC_CLIENT_NAME"))
    return client.authorize_redirect(redirect_uri, nonce=nonce)
# authorizing the user to access the app
@app.route("/authorize")
def authorize():
    client = oauth.create_client(os.getenv("OIDC_CLIENT_NAME"))
    token = client.authorize_access_token()
    user_info = client.parse_id_token(token, nonce=session.get("nonce"))
    session["user"] = user_info
    return redirect("http://localhost:5173/")
# logging out the user
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# FRONTEND ROUTES
@app.route("/")
# if user logged in -> shows their email and a logout link
# if no user logged in -> shows a login link that redirects to Dex authentication
def home():
    user = session.get("user")
    if user:
        return (
            f"<h2>Logged in as {user['email']}</h2>"
            "<a href='/logout'>Logout</a>"
        )
    return '<a href="/login">Login with Dex</a>'
# serving frontend assets - this route serves static files
@app.route("/<path:path>")
def serve_frontend(path):
    full_path = os.path.join(app.static_folder, path)
    if os.path.exists(full_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.template_folder, "index.html")

# RUN
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        debug=True
    )
