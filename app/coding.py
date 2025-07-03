from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client.github_webhooks
collection = db.events

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/github_webhook", methods=['POST'])
def github_webhook():
    if request.headers.get('Content-Type') == 'application/json':
        payload = request.json
        print("Received payload:", payload)

        # ✅ Store timestamp in UTC
        event = {
            "author": payload.get('sender', {}).get('login'),
            "repository": payload.get('repository', {}).get('name'),
            "timestamp": datetime.utcnow().isoformat(),  # UTC
            "action": None,
            "from_branch": None,
            "to_branch": None
        }

        # Detect PUSH
        if payload.get('ref'):
            event['action'] = 'PUSH'
            event['to_branch'] = payload['ref'].split('/')[-1]

        # Detect PULL_REQUEST
        elif payload.get('pull_request'):
            pr = payload['pull_request']
            event['action'] = 'PULL_REQUEST'
            event['from_branch'] = pr['head']['ref']
            event['to_branch'] = pr['base']['ref']

        # Detect MERGE
        elif payload.get('action') == 'closed' and payload.get('pull_request', {}).get('merged'):
            pr = payload['pull_request']
            event['action'] = 'MERGE'
            event['from_branch'] = pr['head']['ref']
            event['to_branch'] = pr['base']['ref']

        else:
            return jsonify({"error": "Unsupported event"}), 400

        result = collection.insert_one(event)
        print("Inserted ID:", result.inserted_id)

        return jsonify({"status": "success", "id": str(result.inserted_id)})

    else:
        return jsonify({"error": "Invalid content type"}), 400

@app.route("/events", methods=['GET'])
def get_events():
    events = list(collection.find().sort("timestamp", -1))
    for e in events:
        e['_id'] = str(e['_id'])
    return jsonify(events)

if __name__ == '__main__':
    app.run(debug=True)
