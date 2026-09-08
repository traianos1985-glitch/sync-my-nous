from flask import Flask, request, jsonify
from executor.document_chat_bridge import format_document_answer

from executor.core import safe_execute_patch
from executor.evolution import suggest_improvements
from executor.self_improver import SelfImprover

app = Flask(__name__)

improver = SelfImprover()


@app.route("/")
def home():
    return """
    <h2>ΝΟΥΣ AI OS ACTIVE</h2>
    <p>Status: RUNNING</p>
    <p>Endpoints: /chat /patch</p>
    """


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        msg = (
            data.get("message")
            or data.get("prompt")
            or data.get("text")
            or data.get("command")
            or ""
        )
        doc_answer = format_document_answer(str(msg))
        if doc_answer:
            return jsonify({
                "ok": True,
                "source": "document_chat_bridge",
                "mode": "document_recall",
                "answer": doc_answer,
                "response": doc_answer,
                "text": doc_answer
            })
    except Exception as e:
        pass

    data = request.json
    msg = data.get("message", "")

    reply = f"Νοῦς: Έλαβα -> {msg}"

    return jsonify({"reply": reply})


@app.route("/patch", methods=["POST"])
def patch():
    data = request.json

    file = data.get("file")
    content = data.get("content")

    ok = safe_execute_patch(file, content)

    return jsonify({"success": ok})


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json

    file = data.get("file", "")
    content = data.get("content", "")

    return jsonify({
        "suggestions": suggest_improvements(content, file)
    })


@app.route("/self-improve", methods=["POST"])
def self_improve():
    data = request.json
    file = data.get("file")

    def read(f):
        with open(f, "r", encoding="utf-8") as x:
            return x.read()

    improver.improve_loop(file, read, 1)

    return jsonify({"status": "started"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
