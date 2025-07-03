from flask import Blueprint, request, jsonify, send_from_directory, current_app, render_template
import os
from datetime import datetime
from app.extensions import mongo

webhook = Blueprint('Webhook', __name__, url_prefix='/webhook')

# Serve static frontend
@webhook.route('/', methods=['GET'])
def index():
    return render_template('index.html')


# Receive GitHub Webhook
@webhook.route('/receiver', methods=["POST"])
def receiver():
    if request.headers.get('Content-Type') == 'application/json':
        payload = request.json
        print("Received payload:", payload)

        event = {
            "author": payload.get('sender', {}).get('login'),
            "repository": payload.get('repository', {}).get('name'),
            "timestamp": datetime.utcnow().isoformat(),
            "action": None,
            "from_branch": None,
            "to_branch": None
        }

        if payload.get('ref'):
            event['action'] = 'PUSH'
            event['to_branch'] = payload['ref'].split('/')[-1]
        elif payload.get('pull_request'):
            pr = payload['pull_request']
            event['action'] = 'PULL_REQUEST'
            event['from_branch'] = pr['head']['ref']
            event['to_branch'] = pr['base']['ref']
        elif payload.get('action') == 'closed' and payload.get('pull_request', {}).get('merged'):
            pr = payload['pull_request']
            event['action'] = 'MERGE'
            event['from_branch'] = pr['head']['ref']
            event['to_branch'] = pr['base']['ref']
        else:
            return jsonify({"error": "Unsupported event"}), 400

        mongo.db.events.insert_one(event)
        return jsonify({"status": "success"}), 200

    return jsonify({"error": "Invalid content type"}), 400


# Get events
@webhook.route('/events', methods=["GET"])
def get_events():
    events = list(mongo.db.events.find().sort("timestamp", -1))
    for e in events:
        e['_id'] = str(e['_id'])
    return jsonify(events)
