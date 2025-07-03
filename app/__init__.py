from flask import Flask
from app.extensions import mongo
from app.webhook.routes import webhook

def create_app():
    app = Flask(__name__)

    app.config["MONGO_URI"] = "mongodb://localhost:27017/github_webhooks"
    mongo.init_app(app)

    app.register_blueprint(webhook)

    return app
