from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://postgres:17f50679ca9121420a9c@easypanel.idealconnecta.com.br:5432/n8n"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id = db.Column(db.Integer, primary_key=True)
    instancia = db.Column(db.String(255), nullable=False)
    remotejid = db.Column(db.String(255), nullable=False)
    sender = db.Column(db.String(255), nullable=True)
    message = db.Column(db.Text, nullable=False)
    date_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@app.route("/")
def index():
    instances = db.session.query(ChatSession.instancia).distinct().all()
    instances = [i[0] for i in instances]
    return render_template("chat.html", instances=instances, conversations=[], messages=[])

@app.route("/chat")
def chat():
    instance = request.args.get("instance")
    remoteJid = request.args.get("remoteJid")

    instances = db.session.query(ChatSession.instancia).distinct().all()
    instances = [i[0] for i in instances]

    conversations_query = (
        db.session.query(ChatSession.remotejid, db.func.max(ChatSession.date_time))
        .filter(ChatSession.instancia == instance if instance else True)
        .group_by(ChatSession.remotejid)
        .order_by(db.func.max(ChatSession.date_time).desc())
        .all()
    )
    conversations = [{"remotejid": c[0], "last_date": c[1]} for c in conversations_query]

    messages = []
    if remoteJid:
        messages = (
            ChatSession.query.filter_by(instancia=instance, remotejid=remoteJid)
            .order_by(ChatSession.date_time.asc())
            .all()
        )

    return render_template(
        "chat.html",
        instances=instances,
        conversations=conversations,
        messages=messages,
        instance=instance,
        remoteJid=remoteJid,
    )

@app.route("/messages")
def get_messages():
    instance = request.args.get("instance")
    remoteJid = request.args.get("remoteJid")
    messages = (
        ChatSession.query.filter_by(instancia=instance, remotejid=remoteJid)
        .order_by(ChatSession.date_time.asc())
        .all()
    )
    return jsonify([
        {
            "sender": m.sender,
            "message": m.message,
            "date_time": m.date_time.strftime("%d/%m/%Y %H:%M"),
        }
        for m in messages
    ])

if __name__ == "__main__":
    app.run(debug=True)
